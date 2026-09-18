import uuid
from datetime import date, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.bus import EventBus
from app.modules.finance.models import Account, Budget, Category, RecurringRule, Transaction


# ---------------------------------------------------------------------------
# Чистые функции — вычисление дат рекуррентности (unit-тестируемы без БД)
# ---------------------------------------------------------------------------

def compute_next_due_date(
    frequency: str,
    current_due_date: date,
    day_of_month: Optional[int] = None,
    day_of_week: Optional[int] = None,
) -> date:
    """Возвращает следующую дату после current_due_date для данного правила."""
    if frequency == "monthly":
        month = current_due_date.month + 1
        year = current_due_date.year
        if month > 12:
            month = 1
            year += 1
        return date(year, month, day_of_month or current_due_date.day)
    else:  # weekly
        return current_due_date + timedelta(days=7)


def get_pending_periods(
    frequency: str,
    next_due_date: date,
    day_of_month: Optional[int],
    day_of_week: Optional[int],
    today: date,
) -> list[date]:
    """Возвращает все даты, которые нужно материализовать (next_due_date <= today)."""
    periods: list[date] = []
    current = next_due_date
    while current <= today:
        periods.append(current)
        current = compute_next_due_date(
            frequency=frequency,
            current_due_date=current,
            day_of_month=day_of_month,
            day_of_week=day_of_week,
        )
    return periods


# ---------------------------------------------------------------------------
# Сервис
# ---------------------------------------------------------------------------

class FinanceService:
    def __init__(self, session: AsyncSession, bus: EventBus) -> None:
        self.session = session
        self.bus = bus

    async def _save(self, obj):
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def _publish_transaction_added(self, txn: Transaction) -> None:
        await self.bus.publish(
            "finance.transaction_added",
            {
                "transaction_id": str(txn.id),
                "user_id": str(txn.user_id),
                "account_id": str(txn.account_id),
                "category_id": str(txn.category_id) if txn.category_id else None,
                "amount_kopecks": txn.amount_kopecks,
                "occurred_at": str(txn.occurred_at),
            },
        )

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------

    async def create_account(self, user_id: uuid.UUID, name: str) -> Account:
        account = Account(user_id=user_id, name=name, balance_kopecks=0)
        self.session.add(account)
        return await self._save(account)

    async def list_accounts(self, user_id: uuid.UUID) -> list[Account]:
        result = await self.session.execute(
            select(Account).where(Account.user_id == user_id)
        )
        return list(result.scalars().all())

    async def update_account(self, user_id: uuid.UUID, account_id: uuid.UUID, name: str) -> Account:
        account = await self._get_account(user_id, account_id)
        account.name = name
        return await self._save(account)

    async def set_account_balance(
        self, user_id: uuid.UUID, account_id: uuid.UUID, balance_kopecks: int
    ) -> Account:
        account = await self._get_account(user_id, account_id)
        account.balance_kopecks = balance_kopecks
        return await self._save(account)

    async def delete_account(self, user_id: uuid.UUID, account_id: uuid.UUID) -> None:
        account = await self._get_account(user_id, account_id)
        txn_count = await self.session.execute(
            select(func.count(Transaction.id)).where(
                Transaction.account_id == account_id,
                Transaction.user_id == user_id,
            )
        )
        if txn_count.scalar() > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account has transactions; delete them first",
            )
        await self.session.delete(account)
        await self.session.commit()

    async def _get_account(self, user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
        result = await self.session.execute(
            select(Account).where(Account.id == account_id, Account.user_id == user_id)
        )
        account = result.scalars().first()
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return account

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------

    async def create_category(
        self, user_id: uuid.UUID, name: str, type: str
    ) -> Category:
        category = Category(user_id=user_id, name=name, type=type)
        self.session.add(category)
        return await self._save(category)

    async def list_categories(self, user_id: uuid.UUID) -> list[Category]:
        result = await self.session.execute(
            select(Category).where(Category.user_id == user_id)
        )
        return list(result.scalars().all())

    async def delete_category(self, user_id: uuid.UUID, category_id: uuid.UUID) -> None:
        result = await self.session.execute(
            select(Category).where(
                Category.id == category_id, Category.user_id == user_id
            )
        )
        category = result.scalars().first()
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        # Проверяем, есть ли транзакции у этой категории
        txn_count = await self.session.execute(
            select(func.count(Transaction.id)).where(
                Transaction.category_id == category_id,
                Transaction.user_id == user_id,
            )
        )
        if txn_count.scalar() > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category has transactions; reassign them first",
            )
        await self.session.delete(category)
        await self.session.commit()

    async def _get_or_create_food_category(self, user_id: uuid.UUID) -> Category:
        result = await self.session.execute(
            select(Category).where(
                Category.user_id == user_id,
                Category.name == "Еда",
                Category.type == "expense",
            )
        )
        category = result.scalars().first()
        if category is None:
            category = Category(user_id=user_id, name="Еда", type="expense")
            self.session.add(category)
            await self.session.flush()
        return category

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------

    async def create_transaction(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
        amount_kopecks: int,
        occurred_at: date,
        category_id: Optional[uuid.UUID] = None,
        description: Optional[str] = None,
        source: str = "manual",
        recurring_rule_id: Optional[uuid.UUID] = None,
    ) -> Transaction:
        # Проверяем существование счёта
        account = await self._get_account(user_id, account_id)

        txn = Transaction(
            user_id=user_id,
            account_id=account_id,
            category_id=category_id,
            amount_kopecks=amount_kopecks,
            occurred_at=occurred_at,
            description=description,
            source=source,
            recurring_rule_id=recurring_rule_id,
        )
        self.session.add(txn)

        # Атомарно обновляем баланс счёта
        account.balance_kopecks += amount_kopecks

        await self.session.commit()
        await self.session.refresh(txn)

        await self._publish_transaction_added(txn)
        await self._check_budget(user_id, category_id, occurred_at)
        return txn

    async def _check_budget(
        self,
        user_id: uuid.UUID,
        category_id: Optional[uuid.UUID],
        occurred_at: date,
    ) -> None:
        """Публикует finance.budget_exceeded если расходы по категории превышают лимит."""
        if category_id is None:
            return

        # Проверяем тип категории
        cat_result = await self.session.execute(
            select(Category).where(Category.id == category_id, Category.user_id == user_id)
        )
        category = cat_result.scalars().first()
        if category is None or category.type != "expense":
            return

        period = occurred_at.strftime("%Y-%m")

        budget_result = await self.session.execute(
            select(Budget).where(
                Budget.user_id == user_id,
                Budget.category_id == category_id,
                Budget.period == period,
            )
        )
        budget = budget_result.scalars().first()
        if budget is None:
            return

        # Считаем суммарные расходы по категории за период
        spent_result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount_kopecks), 0)).where(
                Transaction.user_id == user_id,
                Transaction.category_id == category_id,
                func.to_char(Transaction.occurred_at, "YYYY-MM") == period,
            )
        )
        spent_raw = spent_result.scalar()
        # Расходы — отрицательные числа; берём модуль
        spent_kopecks = abs(int(spent_raw))

        if spent_kopecks > budget.limit_kopecks:
            await self.bus.publish(
                "finance.budget_exceeded",
                {
                    "user_id": str(user_id),
                    "category_id": str(category_id),
                    "period": period,
                    "limit_kopecks": budget.limit_kopecks,
                    "spent_kopecks": spent_kopecks,
                },
            )

    async def list_transactions(
        self,
        user_id: uuid.UUID,
        account_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[Transaction]:
        # Сначала материализуем просроченные recurring rules для пользователя
        await self._materialize_pending_rules(user_id)

        q = select(Transaction).where(Transaction.user_id == user_id)
        if account_id is not None:
            q = q.where(Transaction.account_id == account_id)
        if category_id is not None:
            q = q.where(Transaction.category_id == category_id)
        if from_date is not None:
            q = q.where(Transaction.occurred_at >= from_date)
        if to_date is not None:
            q = q.where(Transaction.occurred_at <= to_date)
        q = q.order_by(Transaction.occurred_at.desc(), Transaction.created_at.desc())
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def delete_transaction(
        self, user_id: uuid.UUID, transaction_id: uuid.UUID
    ) -> None:
        result = await self.session.execute(
            select(Transaction).where(
                Transaction.id == transaction_id, Transaction.user_id == user_id
            )
        )
        txn = result.scalars().first()
        if txn is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        # Атомарно откатываем баланс счёта
        acc_result = await self.session.execute(
            select(Account).where(Account.id == txn.account_id)
        )
        account = acc_result.scalars().first()
        if account is not None:
            account.balance_kopecks -= txn.amount_kopecks

        await self.session.delete(txn)
        await self.session.commit()

    # ------------------------------------------------------------------
    # Recurring rules + ленивая материализация
    # ------------------------------------------------------------------

    async def create_recurring_rule(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
        amount_kopecks: int,
        frequency: str,
        day_of_month: Optional[int] = None,
        day_of_week: Optional[int] = None,
        category_id: Optional[uuid.UUID] = None,
        description: Optional[str] = None,
        next_due_date: Optional[date] = None,
    ) -> RecurringRule:
        if next_due_date is None:
            # Вычисляем первую дату срабатывания из параметров
            today = date.today()
            if frequency == "monthly" and day_of_month is not None:
                month, year = today.month, today.year
                candidate = date(year, month, day_of_month)
                if candidate <= today:
                    month += 1
                    if month > 12:
                        month = 1
                        year += 1
                    candidate = date(year, month, day_of_month)
                next_due_date = candidate
            elif frequency == "weekly" and day_of_week is not None:
                days_ahead = (day_of_week - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                next_due_date = today + timedelta(days=days_ahead)
            else:
                next_due_date = today

        rule = RecurringRule(
            user_id=user_id,
            account_id=account_id,
            category_id=category_id,
            amount_kopecks=amount_kopecks,
            description=description,
            frequency=frequency,
            day_of_month=day_of_month,
            day_of_week=day_of_week,
            next_due_date=next_due_date,
            active=True,
        )
        self.session.add(rule)
        return await self._save(rule)

    async def list_recurring_rules(self, user_id: uuid.UUID) -> list[RecurringRule]:
        result = await self.session.execute(
            select(RecurringRule).where(RecurringRule.user_id == user_id)
        )
        return list(result.scalars().all())

    async def update_recurring_rule(
        self,
        user_id: uuid.UUID,
        rule_id: uuid.UUID,
        active: Optional[bool] = None,
        amount_kopecks: Optional[int] = None,
    ) -> RecurringRule:
        result = await self.session.execute(
            select(RecurringRule).where(
                RecurringRule.id == rule_id, RecurringRule.user_id == user_id
            )
        )
        rule = result.scalars().first()
        if rule is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if active is not None:
            rule.active = active
        if amount_kopecks is not None:
            rule.amount_kopecks = amount_kopecks
        return await self._save(rule)

    async def _materialize_pending_rules(self, user_id: uuid.UUID) -> None:
        """Лениво материализует все просроченные активные правила пользователя."""
        today = date.today()
        result = await self.session.execute(
            select(RecurringRule).where(
                RecurringRule.user_id == user_id,
                RecurringRule.active.is_(True),
                RecurringRule.next_due_date <= today,
            )
        )
        rules = list(result.scalars().all())
        if not rules:
            return

        account_cache: dict[uuid.UUID, Optional[Account]] = {}
        new_txns: list[Transaction] = []

        for rule in rules:
            periods = get_pending_periods(
                frequency=rule.frequency,
                next_due_date=rule.next_due_date,
                day_of_month=rule.day_of_month,
                day_of_week=rule.day_of_week,
                today=today,
            )

            if rule.account_id not in account_cache:
                acc_result = await self.session.execute(
                    select(Account).where(Account.id == rule.account_id)
                )
                account_cache[rule.account_id] = acc_result.scalars().first()
            account = account_cache[rule.account_id]

            for period_date in periods:
                txn = Transaction(
                    user_id=user_id,
                    account_id=rule.account_id,
                    category_id=rule.category_id,
                    amount_kopecks=rule.amount_kopecks,
                    occurred_at=period_date,
                    description=rule.description,
                    source="recurring",
                    recurring_rule_id=rule.id,
                )
                self.session.add(txn)
                new_txns.append(txn)

                if account is not None:
                    account.balance_kopecks += rule.amount_kopecks

            # Сдвигаем next_due_date за все материализованные периоды
            if periods:
                rule.next_due_date = compute_next_due_date(
                    frequency=rule.frequency,
                    current_due_date=periods[-1],
                    day_of_month=rule.day_of_month,
                    day_of_week=rule.day_of_week,
                )

        await self.session.flush()
        await self.session.commit()

        # Обновляем объекты транзакций (получаем id после commit)
        for txn in new_txns:
            await self.session.refresh(txn)

        for txn in new_txns:
            await self._publish_transaction_added(txn)

    # ------------------------------------------------------------------
    # Budgets
    # ------------------------------------------------------------------

    async def create_budget(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        period: str,
        limit_kopecks: int,
    ) -> Budget:
        budget = Budget(
            user_id=user_id,
            category_id=category_id,
            period=period,
            limit_kopecks=limit_kopecks,
        )
        self.session.add(budget)
        return await self._save(budget)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    async def get_summary(self, user_id: uuid.UUID, period: str):
        # Материализуем pending rules перед подсчётом
        await self._materialize_pending_rules(user_id)

        # Транзакции за период
        result = await self.session.execute(
            select(Transaction).where(
                Transaction.user_id == user_id,
                func.to_char(Transaction.occurred_at, "YYYY-MM") == period,
            )
        )
        transactions = list(result.scalars().all())

        total_income = sum(t.amount_kopecks for t in transactions if t.amount_kopecks > 0)
        total_expense = abs(sum(t.amount_kopecks for t in transactions if t.amount_kopecks < 0))

        # Группировка по категории
        by_category_map: dict = {}
        for txn in transactions:
            key = txn.category_id
            by_category_map.setdefault(key, 0)
            by_category_map[key] += txn.amount_kopecks

        # Загружаем имена всех задействованных категорий одним запросом
        cat_ids = [cid for cid in by_category_map if cid is not None]
        cat_names: dict[uuid.UUID, str] = {}
        if cat_ids:
            cat_result = await self.session.execute(
                select(Category).where(Category.id.in_(cat_ids))
            )
            for cat in cat_result.scalars().all():
                cat_names[cat.id] = cat.name

        by_category = [
            {
                "category_id": cat_id,
                "category_name": cat_names.get(cat_id) if cat_id else None,
                "amount_kopecks": amount,
            }
            for cat_id, amount in by_category_map.items()
        ]

        return {
            "by_category": by_category,
            "total_income": total_income,
            "total_expense": total_expense,
        }

    # ------------------------------------------------------------------
    # Обработчик события food.meal_logged
    # ------------------------------------------------------------------

    async def on_food_meal_logged(self, payload: dict) -> None:
        price_kopecks = payload.get("price_kopecks")
        if price_kopecks is None:
            return

        try:
            user_id = uuid.UUID(str(payload["user_id"]))
        except (KeyError, ValueError):
            return

        # Находим первый счёт пользователя
        acc_result = await self.session.execute(
            select(Account)
            .where(Account.user_id == user_id)
            .order_by(Account.created_at)
            .limit(1)
        )
        account = acc_result.scalars().first()
        if account is None:
            return

        category = await self._get_or_create_food_category(user_id)
        await self.create_transaction(
            user_id=user_id,
            account_id=account.id,
            amount_kopecks=-int(price_kopecks),
            occurred_at=date.today(),
            category_id=category.id,
            source="food_module",
        )
