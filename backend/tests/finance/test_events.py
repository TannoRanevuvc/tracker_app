"""
Контрактные тесты событий модуля finance.

Уровень 1 — статические: PUBLISHES/SUBSCRIBES_TO соответствуют спеке.
Уровень 2 — функциональные: реальная публикация/обработка событий через FinanceService.

Покрытие критериев приёмки:
  AC#1 (finance.transaction_added при создании транзакции) — TestTransactionAdded
  AC#2 (finance.budget_exceeded при превышении лимита) — TestBudgetExceeded
  AC#5 (food.meal_logged с price_kopecks → транзакция source=food_module) — TestFoodMealLoggedHandler
  AC#6 (food.meal_logged без price_kopecks → транзакция не создаётся) — TestFoodMealLoggedHandler
"""

import uuid
from datetime import date

import pytest

from app.core.events.bus import EventBus
from app.modules.finance import events as finance_events


# ---------------------------------------------------------------------------
# Статический контракт
# ---------------------------------------------------------------------------

class TestEventContract:
    def test_publishes_transaction_added(self):
        assert "finance.transaction_added" in finance_events.PUBLISHES

    def test_publishes_budget_exceeded(self):
        assert "finance.budget_exceeded" in finance_events.PUBLISHES

    def test_no_extra_published_events(self):
        assert set(finance_events.PUBLISHES) == {
            "finance.transaction_added",
            "finance.budget_exceeded",
        }

    def test_subscribes_to_food_meal_logged(self):
        assert "food.meal_logged" in finance_events.SUBSCRIBES_TO

    def test_no_extra_subscriptions(self):
        assert set(finance_events.SUBSCRIBES_TO.keys()) == {"food.meal_logged"}


# ---------------------------------------------------------------------------
# AC#1 — finance.transaction_added
# ---------------------------------------------------------------------------

class TestTransactionAdded:
    async def test_create_transaction_publishes_event(self, db_session, test_user):
        from app.modules.finance.service import FinanceService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("finance.transaction_added", capture)

        svc = FinanceService(db_session, test_bus)
        account = await svc.create_account(user_id=test_user.id, name="Наличные")
        await svc.create_transaction(
            user_id=test_user.id,
            account_id=account.id,
            amount_kopecks=500_000,
            occurred_at=date.today(),
        )

        assert len(received) == 1

    async def test_transaction_added_payload_fields(self, db_session, test_user):
        from app.modules.finance.service import FinanceService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("finance.transaction_added", capture)

        svc = FinanceService(db_session, test_bus)
        account = await svc.create_account(user_id=test_user.id, name="Наличные")
        await svc.create_transaction(
            user_id=test_user.id,
            account_id=account.id,
            amount_kopecks=500_000,
            occurred_at=date.today(),
        )

        payload = received[0]
        assert "transaction_id" in payload
        assert str(payload["user_id"]) == str(test_user.id)
        assert str(payload["account_id"]) == str(account.id)
        assert payload["amount_kopecks"] == 500_000
        assert "occurred_at" in payload

    async def test_transaction_added_category_id_in_payload(self, db_session, test_user):
        from app.modules.finance.service import FinanceService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("finance.transaction_added", capture)

        svc = FinanceService(db_session, test_bus)
        account = await svc.create_account(user_id=test_user.id, name="Карта")
        category = await svc.create_category(user_id=test_user.id, name="Еда", type="expense")
        await svc.create_transaction(
            user_id=test_user.id,
            account_id=account.id,
            amount_kopecks=-10_000,
            category_id=category.id,
            occurred_at=date.today(),
        )

        assert str(received[0]["category_id"]) == str(category.id)

    # Создание счёта и категории — не публикует transaction_added
    async def test_no_event_on_account_create(self, db_session, test_user):
        from app.modules.finance.service import FinanceService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("finance.transaction_added", capture)

        svc = FinanceService(db_session, test_bus)
        await svc.create_account(user_id=test_user.id, name="Наличные")

        assert len(received) == 0


# ---------------------------------------------------------------------------
# AC#2 — finance.budget_exceeded
# ---------------------------------------------------------------------------

class TestBudgetExceeded:
    async def test_publishes_budget_exceeded_when_limit_crossed(self, db_session, test_user):
        from app.modules.finance.service import FinanceService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("finance.budget_exceeded", capture)

        svc = FinanceService(db_session, test_bus)
        account = await svc.create_account(user_id=test_user.id, name="Карта")
        category = await svc.create_category(user_id=test_user.id, name="Еда", type="expense")
        period = date.today().strftime("%Y-%m")
        await svc.create_budget(
            user_id=test_user.id,
            category_id=category.id,
            period=period,
            limit_kopecks=100_000,
        )
        await svc.create_transaction(
            user_id=test_user.id,
            account_id=account.id,
            amount_kopecks=-150_000,
            category_id=category.id,
            occurred_at=date.today(),
        )

        assert len(received) == 1

    async def test_budget_exceeded_payload_fields(self, db_session, test_user):
        from app.modules.finance.service import FinanceService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("finance.budget_exceeded", capture)

        svc = FinanceService(db_session, test_bus)
        account = await svc.create_account(user_id=test_user.id, name="Карта")
        category = await svc.create_category(user_id=test_user.id, name="Еда", type="expense")
        period = date.today().strftime("%Y-%m")
        await svc.create_budget(
            user_id=test_user.id,
            category_id=category.id,
            period=period,
            limit_kopecks=100_000,
        )
        await svc.create_transaction(
            user_id=test_user.id,
            account_id=account.id,
            amount_kopecks=-150_000,
            category_id=category.id,
            occurred_at=date.today(),
        )

        payload = received[0]
        assert str(payload["user_id"]) == str(test_user.id)
        assert str(payload["category_id"]) == str(category.id)
        assert payload["period"] == period
        assert payload["limit_kopecks"] == 100_000
        assert payload["spent_kopecks"] > payload["limit_kopecks"]

    # Транзакция в рамках бюджета — событие не публикуется
    async def test_no_event_when_within_limit(self, db_session, test_user):
        from app.modules.finance.service import FinanceService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("finance.budget_exceeded", capture)

        svc = FinanceService(db_session, test_bus)
        account = await svc.create_account(user_id=test_user.id, name="Карта")
        category = await svc.create_category(user_id=test_user.id, name="Еда", type="expense")
        await svc.create_budget(
            user_id=test_user.id,
            category_id=category.id,
            period=date.today().strftime("%Y-%m"),
            limit_kopecks=1_000_000,
        )
        await svc.create_transaction(
            user_id=test_user.id,
            account_id=account.id,
            amount_kopecks=-50_000,
            category_id=category.id,
            occurred_at=date.today(),
        )

        assert len(received) == 0

    # Бюджет по income-категории — budget_exceeded никогда не публикуется
    async def test_no_event_for_income_category(self, db_session, test_user):
        from app.modules.finance.service import FinanceService

        test_bus = EventBus()
        received = []

        async def capture(payload):
            received.append(payload)

        test_bus.subscribe("finance.budget_exceeded", capture)

        svc = FinanceService(db_session, test_bus)
        account = await svc.create_account(user_id=test_user.id, name="Карта")
        income_cat = await svc.create_category(
            user_id=test_user.id, name="Зарплата", type="income"
        )
        await svc.create_budget(
            user_id=test_user.id,
            category_id=income_cat.id,
            period=date.today().strftime("%Y-%m"),
            limit_kopecks=100_000,
        )
        await svc.create_transaction(
            user_id=test_user.id,
            account_id=account.id,
            amount_kopecks=500_000,
            category_id=income_cat.id,
            occurred_at=date.today(),
        )

        assert len(received) == 0

    # Удаление транзакции не публикует "бюджет в норме"
    async def test_delete_transaction_does_not_publish_budget_ok(self, db_session, test_user):
        from app.modules.finance.service import FinanceService

        test_bus = EventBus()
        exceeded_events = []
        all_budget_events = []

        async def capture_exceeded(payload):
            exceeded_events.append(payload)

        test_bus.subscribe("finance.budget_exceeded", capture_exceeded)

        svc = FinanceService(db_session, test_bus)
        account = await svc.create_account(user_id=test_user.id, name="Карта")
        category = await svc.create_category(user_id=test_user.id, name="Еда", type="expense")
        await svc.create_budget(
            user_id=test_user.id,
            category_id=category.id,
            period=date.today().strftime("%Y-%m"),
            limit_kopecks=100_000,
        )
        txn = await svc.create_transaction(
            user_id=test_user.id,
            account_id=account.id,
            amount_kopecks=-150_000,
            category_id=category.id,
            occurred_at=date.today(),
        )

        exceeded_events.clear()
        await svc.delete_transaction(user_id=test_user.id, transaction_id=txn.id)

        assert len(exceeded_events) == 0


# ---------------------------------------------------------------------------
# AC#5, AC#6 — обработчик food.meal_logged
# ---------------------------------------------------------------------------

class TestFoodMealLoggedHandler:
    # AC#5: payload содержит price_kopecks → создаётся транзакция amount=-price, source=food_module
    async def test_with_price_creates_transaction(self, db_session, test_user):
        from app.modules.finance.service import FinanceService

        test_bus = EventBus()
        svc = FinanceService(db_session, test_bus)
        await svc.create_account(user_id=test_user.id, name="Карта")

        await svc.on_food_meal_logged({
            "user_id": str(test_user.id),
            "price_kopecks": 35_000,
        })

        txns = await svc.list_transactions(user_id=test_user.id)
        assert len(txns) == 1
        assert txns[0].amount_kopecks == -35_000
        assert txns[0].source == "food_module"

    # AC#5: категория "Еда" создаётся автоматически при первом срабатывании
    async def test_food_category_auto_created(self, db_session, test_user):
        from app.modules.finance.service import FinanceService

        test_bus = EventBus()
        svc = FinanceService(db_session, test_bus)
        await svc.create_account(user_id=test_user.id, name="Карта")

        await svc.on_food_meal_logged({
            "user_id": str(test_user.id),
            "price_kopecks": 35_000,
        })

        categories = await svc.list_categories(user_id=test_user.id)
        food_cats = [c for c in categories if c.name == "Еда"]
        assert len(food_cats) == 1
        assert food_cats[0].type == "expense"

    # AC#5: повторный вызов не создаёт вторую категорию "Еда"
    async def test_food_category_not_duplicated(self, db_session, test_user):
        from app.modules.finance.service import FinanceService

        test_bus = EventBus()
        svc = FinanceService(db_session, test_bus)
        await svc.create_account(user_id=test_user.id, name="Карта")

        await svc.on_food_meal_logged({"user_id": str(test_user.id), "price_kopecks": 10_000})
        await svc.on_food_meal_logged({"user_id": str(test_user.id), "price_kopecks": 20_000})

        categories = await svc.list_categories(user_id=test_user.id)
        food_cats = [c for c in categories if c.name == "Еда"]
        assert len(food_cats) == 1

    # AC#6: price_kopecks == None → транзакция не создаётся
    async def test_without_price_no_transaction(self, db_session, test_user):
        from app.modules.finance.service import FinanceService

        test_bus = EventBus()
        svc = FinanceService(db_session, test_bus)
        await svc.create_account(user_id=test_user.id, name="Карта")

        await svc.on_food_meal_logged({
            "user_id": str(test_user.id),
            "price_kopecks": None,
        })

        txns = await svc.list_transactions(user_id=test_user.id)
        assert len(txns) == 0
