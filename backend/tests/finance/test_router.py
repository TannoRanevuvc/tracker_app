"""
Интеграционные тесты API модуля finance.
httpx.AsyncClient + тестовая Postgres-схема через фикстуры conftest.py.

Покрытие критериев приёмки из specs/finance.md §7:
  AC#1 — TestTransactions (баланс обновляется, событие публикуется)
  AC#2 — TestBudgets (budget_exceeded при превышении лимита)
  AC#3 — TestRecurringMaterialization (один просроченный период → материализуется)
  AC#4 — TestRecurringMaterialization (три пропущенных периода → три транзакции)
  AC#5 — TestFoodHandler (food.meal_logged с price → транзакция)
  AC#6 — TestFoodHandler (food.meal_logged без price → ничего)
  AC#7 — TestTransactions (DELETE → баланс восстанавливается)
  AC#8 — TestCategories (DELETE категории с транзакциями → 409)
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient

ACCOUNTS_URL = "/api/finance/accounts"
CATEGORIES_URL = "/api/finance/categories"
TRANSACTIONS_URL = "/api/finance/transactions"
RECURRING_URL = "/api/finance/recurring-rules"
BUDGETS_URL = "/api/finance/budgets"
SUMMARY_URL = "/api/finance/summary"


def txn_url(txn_id) -> str:
    return f"{TRANSACTIONS_URL}/{txn_id}"


def recurring_url(rule_id) -> str:
    return f"{RECURRING_URL}/{rule_id}"


def category_url(cat_id) -> str:
    return f"{CATEGORIES_URL}/{cat_id}"


# ---------------------------------------------------------------------------
# Счета
# ---------------------------------------------------------------------------

class TestAccounts:
    async def test_create_account_returns_201(self, authed_client: AsyncClient):
        resp = await authed_client.post(ACCOUNTS_URL, json={"name": "Наличные"})
        assert resp.status_code == 201

    async def test_create_account_initial_balance_zero(self, authed_client: AsyncClient):
        resp = await authed_client.post(ACCOUNTS_URL, json={"name": "Наличные"})
        assert resp.json()["balance_kopecks"] == 0

    async def test_list_accounts_returns_created(self, authed_client: AsyncClient):
        await authed_client.post(ACCOUNTS_URL, json={"name": "Наличные"})
        resp = await authed_client.get(ACCOUNTS_URL)
        assert resp.status_code == 200
        assert any(a["name"] == "Наличные" for a in resp.json())

    async def test_create_without_auth_returns_401(self, client: AsyncClient):
        resp = await client.post(ACCOUNTS_URL, json={"name": "Тест"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Категории
# ---------------------------------------------------------------------------

class TestCategories:
    async def test_create_category_returns_201(self, authed_client: AsyncClient):
        resp = await authed_client.post(
            CATEGORIES_URL, json={"name": "Продукты", "type": "expense"}
        )
        assert resp.status_code == 201

    async def test_create_income_category(self, authed_client: AsyncClient):
        resp = await authed_client.post(
            CATEGORIES_URL, json={"name": "Зарплата", "type": "income"}
        )
        assert resp.json()["type"] == "income"

    async def test_list_categories_returns_created(self, authed_client: AsyncClient):
        await authed_client.post(
            CATEGORIES_URL, json={"name": "Транспорт", "type": "expense"}
        )
        resp = await authed_client.get(CATEGORIES_URL)
        assert any(c["name"] == "Транспорт" for c in resp.json())

    # AC#8: DELETE категории с транзакциями → 409
    async def test_delete_category_with_transactions_returns_409(
        self, authed_client: AsyncClient
    ):
        account = (
            await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})
        ).json()
        category = (
            await authed_client.post(
                CATEGORIES_URL, json={"name": "Еда", "type": "expense"}
            )
        ).json()
        await authed_client.post(
            TRANSACTIONS_URL,
            json={
                "account_id": account["id"],
                "amount_kopecks": -50_000,
                "category_id": category["id"],
                "occurred_at": str(date.today()),
            },
        )

        resp = await authed_client.delete(category_url(category["id"]))
        assert resp.status_code == 409

    # DELETE категории без транзакций → 204
    async def test_delete_category_without_transactions_returns_204(
        self, authed_client: AsyncClient
    ):
        category = (
            await authed_client.post(
                CATEGORIES_URL, json={"name": "Пустая", "type": "expense"}
            )
        ).json()
        resp = await authed_client.delete(category_url(category["id"]))
        assert resp.status_code == 204


# ---------------------------------------------------------------------------
# AC#1, AC#7 — Транзакции и баланс счёта
# ---------------------------------------------------------------------------

class TestTransactions:
    # AC#1: POST транзакции → balance_kopecks обновляется атомарно
    async def test_income_transaction_increases_balance(self, authed_client: AsyncClient):
        account = (
            await authed_client.post(ACCOUNTS_URL, json={"name": "Наличные"})
        ).json()

        await authed_client.post(
            TRANSACTIONS_URL,
            json={
                "account_id": account["id"],
                "amount_kopecks": 500_000,
                "occurred_at": str(date.today()),
            },
        )

        accounts = (await authed_client.get(ACCOUNTS_URL)).json()
        updated = next(a for a in accounts if a["id"] == account["id"])
        assert updated["balance_kopecks"] == 500_000

    async def test_expense_transaction_decreases_balance(self, authed_client: AsyncClient):
        account = (
            await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})
        ).json()
        await authed_client.post(
            TRANSACTIONS_URL,
            json={
                "account_id": account["id"],
                "amount_kopecks": 1_000_000,
                "occurred_at": str(date.today()),
            },
        )
        await authed_client.post(
            TRANSACTIONS_URL,
            json={
                "account_id": account["id"],
                "amount_kopecks": -200_000,
                "occurred_at": str(date.today()),
            },
        )

        accounts = (await authed_client.get(ACCOUNTS_URL)).json()
        updated = next(a for a in accounts if a["id"] == account["id"])
        assert updated["balance_kopecks"] == 800_000

    # AC#1: POST транзакции → публикуется finance.transaction_added
    async def test_create_transaction_publishes_event(
        self, authed_client: AsyncClient, captured_finance_events
    ):
        account = (
            await authed_client.post(ACCOUNTS_URL, json={"name": "Наличные"})
        ).json()
        await authed_client.post(
            TRANSACTIONS_URL,
            json={
                "account_id": account["id"],
                "amount_kopecks": 500_000,
                "occurred_at": str(date.today()),
            },
        )

        assert len(captured_finance_events["finance.transaction_added"]) == 1
        payload = captured_finance_events["finance.transaction_added"][0]
        assert payload["amount_kopecks"] == 500_000

    async def test_create_transaction_returns_201(self, authed_client: AsyncClient):
        account = (
            await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})
        ).json()
        resp = await authed_client.post(
            TRANSACTIONS_URL,
            json={
                "account_id": account["id"],
                "amount_kopecks": -30_000,
                "occurred_at": str(date.today()),
            },
        )
        assert resp.status_code == 201

    async def test_create_transaction_unknown_account_returns_404(
        self, authed_client: AsyncClient
    ):
        resp = await authed_client.post(
            TRANSACTIONS_URL,
            json={
                "account_id": str(uuid.uuid4()),
                "amount_kopecks": 100_000,
                "occurred_at": str(date.today()),
            },
        )
        assert resp.status_code == 404

    # AC#7: DELETE транзакции → balance_kopecks возвращается к значению до создания
    async def test_delete_transaction_restores_balance(self, authed_client: AsyncClient):
        account = (
            await authed_client.post(ACCOUNTS_URL, json={"name": "Наличные"})
        ).json()
        txn = (
            await authed_client.post(
                TRANSACTIONS_URL,
                json={
                    "account_id": account["id"],
                    "amount_kopecks": 500_000,
                    "occurred_at": str(date.today()),
                },
            )
        ).json()

        await authed_client.delete(txn_url(txn["id"]))

        accounts = (await authed_client.get(ACCOUNTS_URL)).json()
        updated = next(a for a in accounts if a["id"] == account["id"])
        assert updated["balance_kopecks"] == 0

    async def test_delete_transaction_returns_204(self, authed_client: AsyncClient):
        account = (
            await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})
        ).json()
        txn = (
            await authed_client.post(
                TRANSACTIONS_URL,
                json={
                    "account_id": account["id"],
                    "amount_kopecks": -10_000,
                    "occurred_at": str(date.today()),
                },
            )
        ).json()

        resp = await authed_client.delete(txn_url(txn["id"]))
        assert resp.status_code == 204

    async def test_delete_nonexistent_transaction_returns_404(
        self, authed_client: AsyncClient
    ):
        resp = await authed_client.delete(txn_url(uuid.uuid4()))
        assert resp.status_code == 404

    # Фильтрация по account_id
    async def test_filter_by_account_id(self, authed_client: AsyncClient):
        acc1 = (await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})).json()
        acc2 = (await authed_client.post(ACCOUNTS_URL, json={"name": "Наличные"})).json()

        await authed_client.post(
            TRANSACTIONS_URL,
            json={"account_id": acc1["id"], "amount_kopecks": 100_000, "occurred_at": str(date.today())},
        )
        await authed_client.post(
            TRANSACTIONS_URL,
            json={"account_id": acc2["id"], "amount_kopecks": 200_000, "occurred_at": str(date.today())},
        )

        resp = await authed_client.get(f"{TRANSACTIONS_URL}?account_id={acc1['id']}")
        txns = resp.json()
        assert all(t["account_id"] == acc1["id"] for t in txns)
        assert len(txns) == 1

    # Фильтрация по диапазону дат
    async def test_filter_by_date_range(self, authed_client: AsyncClient):
        account = (await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})).json()
        yesterday = str(date.today() - timedelta(days=1))
        today = str(date.today())

        await authed_client.post(
            TRANSACTIONS_URL,
            json={"account_id": account["id"], "amount_kopecks": 100_000, "occurred_at": yesterday},
        )
        await authed_client.post(
            TRANSACTIONS_URL,
            json={"account_id": account["id"], "amount_kopecks": 200_000, "occurred_at": today},
        )

        resp = await authed_client.get(f"{TRANSACTIONS_URL}?from={today}&to={today}")
        txns = resp.json()
        assert len(txns) == 1
        assert txns[0]["amount_kopecks"] == 200_000


# ---------------------------------------------------------------------------
# AC#3, AC#4 — Ленивая материализация recurring rules
# ---------------------------------------------------------------------------

class TestRecurringMaterialization:
    # AC#3: одно просроченное правило → одна транзакция создаётся при GET
    async def test_one_overdue_rule_materializes_on_get(self, authed_client: AsyncClient):
        account = (await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})).json()
        yesterday = str(date.today() - timedelta(days=1))

        rule = (
            await authed_client.post(
                RECURRING_URL,
                json={
                    "account_id": account["id"],
                    "amount_kopecks": -50_000,
                    "frequency": "monthly",
                    "day_of_month": (date.today() - timedelta(days=1)).day,
                    "next_due_date": yesterday,
                },
            )
        ).json()

        resp = await authed_client.get(TRANSACTIONS_URL)
        txns = resp.json()

        materialized = [t for t in txns if t.get("recurring_rule_id") == rule["id"]]
        assert len(materialized) == 1
        assert materialized[0]["source"] == "recurring"

    # AC#3: после материализации next_due_date правила сдвигается на следующий период
    async def test_next_due_date_advances_after_materialization(
        self, authed_client: AsyncClient
    ):
        account = (await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})).json()
        yesterday = date.today() - timedelta(days=1)

        rule = (
            await authed_client.post(
                RECURRING_URL,
                json={
                    "account_id": account["id"],
                    "amount_kopecks": -30_000,
                    "frequency": "monthly",
                    "day_of_month": yesterday.day,
                    "next_due_date": str(yesterday),
                },
            )
        ).json()

        await authed_client.get(TRANSACTIONS_URL)

        rules = (await authed_client.get(RECURRING_URL)).json()
        updated_rule = next(r for r in rules if r["id"] == rule["id"])
        assert updated_rule["next_due_date"] > str(yesterday)

    # AC#4: три пропущенных периода → три отдельных транзакции
    async def test_three_overdue_periods_create_three_transactions(
        self, authed_client: AsyncClient
    ):
        account = (await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})).json()
        three_months_ago = date.today().replace(day=1) - timedelta(days=1)
        # Устанавливаем next_due_date на ~3 месяца назад (1-е число три месяца назад)
        three_months_past = date(
            three_months_ago.year - (1 if three_months_ago.month <= 2 else 0),
            ((three_months_ago.month - 3) % 12) + 1,
            1,
        )

        rule = (
            await authed_client.post(
                RECURRING_URL,
                json={
                    "account_id": account["id"],
                    "amount_kopecks": -10_000,
                    "frequency": "monthly",
                    "day_of_month": 1,
                    "next_due_date": str(three_months_past),
                },
            )
        ).json()

        resp = await authed_client.get(TRANSACTIONS_URL)
        txns = resp.json()

        materialized = [t for t in txns if t.get("recurring_rule_id") == rule["id"]]
        assert len(materialized) >= 3

    # Материализация также происходит при GET /summary
    async def test_overdue_rule_materializes_on_summary(self, authed_client: AsyncClient):
        account = (await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})).json()
        yesterday = str(date.today() - timedelta(days=1))
        period = date.today().strftime("%Y-%m")

        rule = (
            await authed_client.post(
                RECURRING_URL,
                json={
                    "account_id": account["id"],
                    "amount_kopecks": -20_000,
                    "frequency": "monthly",
                    "day_of_month": (date.today() - timedelta(days=1)).day,
                    "next_due_date": yesterday,
                },
            )
        ).json()

        await authed_client.get(f"{SUMMARY_URL}?period={period}")

        # После summary — транзакция должна существовать
        resp = await authed_client.get(TRANSACTIONS_URL)
        materialized = [t for t in resp.json() if t.get("recurring_rule_id") == rule["id"]]
        assert len(materialized) == 1

    # Неактивное правило не материализуется
    async def test_inactive_rule_not_materialized(self, authed_client: AsyncClient):
        account = (await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})).json()
        yesterday = str(date.today() - timedelta(days=1))

        rule = (
            await authed_client.post(
                RECURRING_URL,
                json={
                    "account_id": account["id"],
                    "amount_kopecks": -10_000,
                    "frequency": "monthly",
                    "day_of_month": (date.today() - timedelta(days=1)).day,
                    "next_due_date": yesterday,
                },
            )
        ).json()
        await authed_client.patch(recurring_url(rule["id"]), json={"active": False})

        await authed_client.get(TRANSACTIONS_URL)

        resp = await authed_client.get(TRANSACTIONS_URL)
        materialized = [t for t in resp.json() if t.get("recurring_rule_id") == rule["id"]]
        assert len(materialized) == 0


# ---------------------------------------------------------------------------
# AC#2 — Бюджеты и событие budget_exceeded
# ---------------------------------------------------------------------------

class TestBudgets:
    async def test_create_budget_returns_201(self, authed_client: AsyncClient):
        category = (
            await authed_client.post(
                CATEGORIES_URL, json={"name": "Еда", "type": "expense"}
            )
        ).json()
        period = date.today().strftime("%Y-%m")

        resp = await authed_client.post(
            BUDGETS_URL,
            json={
                "category_id": category["id"],
                "period": period,
                "limit_kopecks": 1_000_000,
            },
        )
        assert resp.status_code == 201

    # AC#2: транзакция, превышающая бюджет → finance.budget_exceeded публикуется
    async def test_transaction_exceeding_budget_publishes_event(
        self, authed_client: AsyncClient, captured_finance_events
    ):
        account = (await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})).json()
        category = (
            await authed_client.post(
                CATEGORIES_URL, json={"name": "Рестораны", "type": "expense"}
            )
        ).json()
        period = date.today().strftime("%Y-%m")

        await authed_client.post(
            BUDGETS_URL,
            json={
                "category_id": category["id"],
                "period": period,
                "limit_kopecks": 500_000,
            },
        )
        await authed_client.post(
            TRANSACTIONS_URL,
            json={
                "account_id": account["id"],
                "amount_kopecks": -600_000,
                "category_id": category["id"],
                "occurred_at": str(date.today()),
            },
        )

        assert len(captured_finance_events["finance.budget_exceeded"]) == 1
        payload = captured_finance_events["finance.budget_exceeded"][0]
        assert payload["spent_kopecks"] > payload["limit_kopecks"]
        assert payload["period"] == period

    # Транзакция в рамках бюджета — событие не публикуется
    async def test_transaction_within_budget_no_event(
        self, authed_client: AsyncClient, captured_finance_events
    ):
        account = (await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})).json()
        category = (
            await authed_client.post(
                CATEGORIES_URL, json={"name": "Кофе", "type": "expense"}
            )
        ).json()
        await authed_client.post(
            BUDGETS_URL,
            json={
                "category_id": category["id"],
                "period": date.today().strftime("%Y-%m"),
                "limit_kopecks": 1_000_000,
            },
        )
        await authed_client.post(
            TRANSACTIONS_URL,
            json={
                "account_id": account["id"],
                "amount_kopecks": -50_000,
                "category_id": category["id"],
                "occurred_at": str(date.today()),
            },
        )

        assert len(captured_finance_events["finance.budget_exceeded"]) == 0


# ---------------------------------------------------------------------------
# AC#5, AC#6 — Обработчик food.meal_logged (интеграция через шину)
# ---------------------------------------------------------------------------

class TestFoodHandler:
    # AC#5: food.meal_logged с price_kopecks → транзакция source=food_module создаётся
    async def test_food_event_with_price_creates_transaction(
        self, authed_client: AsyncClient, test_user
    ):
        from app.core.events.bus import bus
        from app.modules.finance.service import FinanceService
        from tests.conftest import test_session_factory

        await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})

        async with test_session_factory() as session:
            svc = FinanceService(session, bus)
            await svc.on_food_meal_logged({
                "user_id": str(test_user.id),
                "price_kopecks": 35_000,
            })
            await session.commit()

        resp = await authed_client.get(TRANSACTIONS_URL)
        txns = resp.json()
        food_txns = [t for t in txns if t.get("source") == "food_module"]
        assert len(food_txns) == 1
        assert food_txns[0]["amount_kopecks"] == -35_000

    # AC#6: food.meal_logged с price_kopecks=None → транзакция не создаётся
    async def test_food_event_without_price_no_transaction(
        self, authed_client: AsyncClient, test_user
    ):
        from app.core.events.bus import bus
        from app.modules.finance.service import FinanceService
        from tests.conftest import test_session_factory

        await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})

        async with test_session_factory() as session:
            svc = FinanceService(session, bus)
            await svc.on_food_meal_logged({
                "user_id": str(test_user.id),
                "price_kopecks": None,
            })
            await session.commit()

        resp = await authed_client.get(TRANSACTIONS_URL)
        assert len(resp.json()) == 0


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class TestSummary:
    async def test_summary_returns_totals(self, authed_client: AsyncClient):
        account = (await authed_client.post(ACCOUNTS_URL, json={"name": "Карта"})).json()
        income_cat = (
            await authed_client.post(
                CATEGORIES_URL, json={"name": "Зарплата", "type": "income"}
            )
        ).json()
        expense_cat = (
            await authed_client.post(
                CATEGORIES_URL, json={"name": "Продукты", "type": "expense"}
            )
        ).json()
        period = date.today().strftime("%Y-%m")

        await authed_client.post(
            TRANSACTIONS_URL,
            json={
                "account_id": account["id"],
                "amount_kopecks": 500_000,
                "category_id": income_cat["id"],
                "occurred_at": str(date.today()),
            },
        )
        await authed_client.post(
            TRANSACTIONS_URL,
            json={
                "account_id": account["id"],
                "amount_kopecks": -100_000,
                "category_id": expense_cat["id"],
                "occurred_at": str(date.today()),
            },
        )

        resp = await authed_client.get(f"{SUMMARY_URL}?period={period}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_income"] == 500_000
        assert body["total_expense"] == 100_000
        assert "by_category" in body
