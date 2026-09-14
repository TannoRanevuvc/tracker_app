"""
Интеграционные тесты API модуля food.
httpx.AsyncClient + тестовая Postgres-схема через фикстуры conftest.py.

Покрытие критериев приёмки из specs/food.md §7:
  AC#1 — TestMealEntries (POST meal-entry → kcal=220.0, food.meal_logged)
  AC#2 — TestDailyGoalReached (1900 + 150 kcal → food.daily_goal_reached, kcal_total=2050)
  AC#3 — TestDailyGoalReached (повторный приём не дублирует событие)
  AC#4 — TestMealEntries (без price_kopecks → price_kopecks: null в событии)
  AC#5 — TestMealEntries (редактирование продукта не пересчитывает старую запись)
  AC#6 — TestGoals (две цели — возвращается та, что effective_from в прошлом)
  AC#7 — TestProducts (GET ?q=греч → находит "Гречка" без внешнего API)
"""
import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient

PRODUCTS_URL = "/api/food/products"
MEAL_ENTRIES_URL = "/api/food/meal-entries"
SUMMARY_URL = "/api/food/summary"
GOALS_URL = "/api/food/goals"
CURRENT_GOAL_URL = "/api/food/goals/current"


# ---------------------------------------------------------------------------
# Продукты
# ---------------------------------------------------------------------------

class TestProducts:
    async def test_create_product_returns_201(self, authed_client: AsyncClient):
        resp = await authed_client.post(PRODUCTS_URL, json={
            "name": "Гречка",
            "kcal_per_100g": 110,
            "protein_g_per_100g": 4.5,
            "fat_g_per_100g": 2.3,
            "carbs_g_per_100g": 21.2,
        })
        assert resp.status_code == 201

    async def test_create_product_response_fields(self, authed_client: AsyncClient):
        resp = await authed_client.post(PRODUCTS_URL, json={
            "name": "Овсянка",
            "kcal_per_100g": 68,
            "protein_g_per_100g": 2.5,
            "fat_g_per_100g": 1.4,
            "carbs_g_per_100g": 12.0,
        })
        body = resp.json()
        assert "id" in body
        assert body["name"] == "Овсянка"
        assert body["kcal_per_100g"] == 68

    async def test_list_products_returns_created(self, authed_client: AsyncClient):
        await authed_client.post(PRODUCTS_URL, json={
            "name": "Творог",
            "kcal_per_100g": 155,
            "protein_g_per_100g": 17,
            "fat_g_per_100g": 9,
            "carbs_g_per_100g": 3,
        })
        resp = await authed_client.get(PRODUCTS_URL)
        assert resp.status_code == 200
        assert any(p["name"] == "Творог" for p in resp.json())

    # AC#7: поиск по имени находит продукт без внешнего API
    async def test_search_by_name_finds_product(self, authed_client: AsyncClient):
        await authed_client.post(PRODUCTS_URL, json={
            "name": "Гречка",
            "kcal_per_100g": 110,
            "protein_g_per_100g": 4.5,
            "fat_g_per_100g": 2.3,
            "carbs_g_per_100g": 21.2,
        })
        resp = await authed_client.get(f"{PRODUCTS_URL}?q=греч")
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) >= 1
        assert any(p["name"] == "Гречка" for p in results)

    # AC#7: поиск без совпадений возвращает пустой список
    async def test_search_no_match_returns_empty(self, authed_client: AsyncClient):
        resp = await authed_client.get(f"{PRODUCTS_URL}?q=несуществующийпродукт")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_without_auth_returns_401(self, client: AsyncClient):
        resp = await client.post(PRODUCTS_URL, json={
            "name": "Тест",
            "kcal_per_100g": 100,
            "protein_g_per_100g": 10,
            "fat_g_per_100g": 5,
            "carbs_g_per_100g": 20,
        })
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# AC#1, AC#4, AC#5 — Записи приёмов пищи
# ---------------------------------------------------------------------------

class TestMealEntries:
    async def _create_product(self, client, name="Гречка", kcal=110):
        resp = await client.post(PRODUCTS_URL, json={
            "name": name,
            "kcal_per_100g": kcal,
            "protein_g_per_100g": 4.5,
            "fat_g_per_100g": 2.3,
            "carbs_g_per_100g": 21.2,
        })
        return resp.json()

    # AC#1: POST meal-entry → ответ содержит kcal = 220.0 (200г × 110/100)
    async def test_create_meal_entry_returns_201_with_kcal(
        self, authed_client: AsyncClient
    ):
        product = await self._create_product(authed_client, kcal=110)
        resp = await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": product["id"],
            "quantity_g": 200,
            "meal_type": "lunch",
        })
        assert resp.status_code == 201
        assert resp.json()["kcal"] == 220.0

    # AC#1: все четыре поля КБЖУ присутствуют в ответе
    async def test_create_meal_entry_response_has_all_macros(
        self, authed_client: AsyncClient
    ):
        product = await self._create_product(authed_client)
        resp = await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": product["id"],
            "quantity_g": 100,
            "meal_type": "breakfast",
        })
        body = resp.json()
        assert "kcal" in body
        assert "protein_g" in body
        assert "fat_g" in body
        assert "carbs_g" in body

    # AC#1: событие food.meal_logged публикуется
    async def test_create_meal_entry_publishes_event(
        self, authed_client: AsyncClient, captured_food_events
    ):
        product = await self._create_product(authed_client, kcal=110)
        await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": product["id"],
            "quantity_g": 200,
            "meal_type": "lunch",
        })
        assert len(captured_food_events["food.meal_logged"]) == 1
        payload = captured_food_events["food.meal_logged"][0]
        assert payload["kcal"] == 220.0

    # AC#4: без price_kopecks → событие содержит price_kopecks: null
    async def test_meal_entry_without_price_event_has_null(
        self, authed_client: AsyncClient, captured_food_events
    ):
        product = await self._create_product(authed_client)
        await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": product["id"],
            "quantity_g": 100,
            "meal_type": "snack",
        })
        payload = captured_food_events["food.meal_logged"][0]
        assert payload["price_kopecks"] is None

    # С price_kopecks → передаётся в событие
    async def test_meal_entry_with_price_event_has_value(
        self, authed_client: AsyncClient, captured_food_events
    ):
        product = await self._create_product(authed_client)
        await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": product["id"],
            "quantity_g": 100,
            "meal_type": "breakfast",
            "price_kopecks": 7500,
        })
        payload = captured_food_events["food.meal_logged"][0]
        assert payload["price_kopecks"] == 7500

    # GET meal-entries?date возвращает записи за день
    async def test_list_meal_entries_by_date(self, authed_client: AsyncClient):
        product = await self._create_product(authed_client)
        await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": product["id"],
            "quantity_g": 100,
            "meal_type": "breakfast",
            "logged_at": str(date.today()) + "T08:00:00",
        })
        resp = await authed_client.get(f"{MEAL_ENTRIES_URL}?date={date.today()}")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    # DELETE meal-entry → 204
    async def test_delete_meal_entry_returns_204(self, authed_client: AsyncClient):
        product = await self._create_product(authed_client)
        entry = (await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": product["id"],
            "quantity_g": 100,
            "meal_type": "dinner",
        })).json()
        resp = await authed_client.delete(f"{MEAL_ENTRIES_URL}/{entry['id']}")
        assert resp.status_code == 204

    # DELETE несуществующей записи → 404
    async def test_delete_nonexistent_entry_returns_404(
        self, authed_client: AsyncClient
    ):
        resp = await authed_client.delete(f"{MEAL_ENTRIES_URL}/{uuid.uuid4()}")
        assert resp.status_code == 404

    # POST с несуществующим product_id → 404
    async def test_create_with_unknown_product_returns_404(
        self, authed_client: AsyncClient
    ):
        resp = await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": str(uuid.uuid4()),
            "quantity_g": 100,
            "meal_type": "lunch",
        })
        assert resp.status_code == 404

    # AC#5: редактирование продукта не пересчитывает сохранённые КБЖУ записи
    async def test_product_edit_does_not_recalculate_historical_entry(
        self, authed_client: AsyncClient
    ):
        product = await self._create_product(authed_client, kcal=110)
        entry = (await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": product["id"],
            "quantity_g": 200,  # kcal=220.0 на момент создания
            "meal_type": "lunch",
        })).json()
        original_kcal = entry["kcal"]
        assert original_kcal == 220.0

        # Редактируем продукт (изменяем kcal_per_100g)
        await authed_client.patch(f"{PRODUCTS_URL}/{product['id']}", json={
            "kcal_per_100g": 999,
        })

        # GET старой записи — kcal не изменился
        resp = await authed_client.get(f"{MEAL_ENTRIES_URL}?date={date.today()}")
        entries = [e for e in resp.json() if e["id"] == entry["id"]]
        assert len(entries) == 1
        assert entries[0]["kcal"] == original_kcal


# ---------------------------------------------------------------------------
# AC#2, AC#3 — Summary и daily_goal_reached
# ---------------------------------------------------------------------------

class TestDailyGoalReached:
    async def _create_product(self, client, kcal=1000):
        resp = await client.post(PRODUCTS_URL, json={
            "name": "Тест",
            "kcal_per_100g": kcal,
            "protein_g_per_100g": 0,
            "fat_g_per_100g": 0,
            "carbs_g_per_100g": 0,
        })
        return resp.json()

    async def _set_goal(self, client, kcal_goal=2000):
        return await client.post(GOALS_URL, json={
            "kcal_goal": kcal_goal,
            "effective_from": str(date.today()),
        })

    # AC#2: 1900 kcal уже залогировано + 150 → food.daily_goal_reached, kcal_total=2050
    async def test_goal_reached_published_when_threshold_crossed(
        self, authed_client: AsyncClient, captured_food_events
    ):
        await self._set_goal(authed_client, kcal_goal=2000)
        product = await self._create_product(authed_client, kcal=1000)

        # 190г × 1000/100 = 1900 kcal (ниже цели)
        await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": product["id"],
            "quantity_g": 190,
            "meal_type": "breakfast",
        })
        assert len(captured_food_events["food.daily_goal_reached"]) == 0

        # 15г × 1000/100 = 150 kcal → итого 2050 ≥ 2000
        await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": product["id"],
            "quantity_g": 15,
            "meal_type": "lunch",
        })
        assert len(captured_food_events["food.daily_goal_reached"]) == 1
        payload = captured_food_events["food.daily_goal_reached"][0]
        assert payload["kcal_total"] == 2050.0
        assert payload["kcal_goal"] == 2000

    # AC#3: повторный приём после достижения цели не дублирует событие
    async def test_goal_reached_not_duplicated(
        self, authed_client: AsyncClient, captured_food_events
    ):
        await self._set_goal(authed_client, kcal_goal=500)
        product = await self._create_product(authed_client, kcal=1000)

        # 60г = 600 kcal → первое событие
        await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": product["id"],
            "quantity_g": 60,
            "meal_type": "breakfast",
        })
        assert len(captured_food_events["food.daily_goal_reached"]) == 1

        # Ещё один приём в тот же день — повтора нет
        await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": product["id"],
            "quantity_g": 10,
            "meal_type": "snack",
        })
        assert len(captured_food_events["food.daily_goal_reached"]) == 1


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class TestSummary:
    async def test_summary_returns_totals(self, authed_client: AsyncClient):
        product = (await authed_client.post(PRODUCTS_URL, json={
            "name": "Рис",
            "kcal_per_100g": 344,
            "protein_g_per_100g": 6.7,
            "fat_g_per_100g": 0.7,
            "carbs_g_per_100g": 78.9,
        })).json()
        await authed_client.post(MEAL_ENTRIES_URL, json={
            "product_id": product["id"],
            "quantity_g": 100,
            "meal_type": "lunch",
        })

        resp = await authed_client.get(f"{SUMMARY_URL}?date={date.today()}")
        assert resp.status_code == 200
        body = resp.json()
        assert "kcal_total" in body
        assert "protein_total" in body
        assert "fat_total" in body
        assert "carbs_total" in body
        assert "goal_reached" in body
        assert body["kcal_total"] == 344.0

    async def test_summary_without_goal_has_null_kcal_goal(
        self, authed_client: AsyncClient
    ):
        resp = await authed_client.get(f"{SUMMARY_URL}?date={date.today()}")
        assert resp.status_code == 200
        assert resp.json()["kcal_goal"] is None

    async def test_summary_empty_day_returns_zeros(self, authed_client: AsyncClient):
        yesterday = str(date.today() - timedelta(days=1))
        resp = await authed_client.get(f"{SUMMARY_URL}?date={yesterday}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["kcal_total"] == 0
        assert body["goal_reached"] is False


# ---------------------------------------------------------------------------
# AC#6 — Цели
# ---------------------------------------------------------------------------

class TestGoals:
    # POST goal → 201
    async def test_create_goal_returns_201(self, authed_client: AsyncClient):
        resp = await authed_client.post(GOALS_URL, json={
            "kcal_goal": 2000,
            "effective_from": str(date.today()),
        })
        assert resp.status_code == 201

    # GET /goals/current без цели → 404
    async def test_no_goal_returns_404(self, authed_client: AsyncClient):
        resp = await authed_client.get(CURRENT_GOAL_URL)
        assert resp.status_code == 404

    # GET /goals/current → возвращает активную цель
    async def test_get_current_goal_returns_active(self, authed_client: AsyncClient):
        await authed_client.post(GOALS_URL, json={
            "kcal_goal": 2200,
            "effective_from": str(date.today()),
        })
        resp = await authed_client.get(CURRENT_GOAL_URL)
        assert resp.status_code == 200
        assert resp.json()["kcal_goal"] == 2200

    # AC#6: две цели (прошлое + завтра) → возвращается прошлая
    async def test_current_goal_ignores_future_effective_from(
        self, authed_client: AsyncClient
    ):
        tomorrow = str(date.today() + timedelta(days=1))
        yesterday = str(date.today() - timedelta(days=1))

        await authed_client.post(GOALS_URL, json={
            "kcal_goal": 1800,
            "effective_from": yesterday,
        })
        await authed_client.post(GOALS_URL, json={
            "kcal_goal": 2500,
            "effective_from": tomorrow,
        })

        resp = await authed_client.get(CURRENT_GOAL_URL)
        assert resp.status_code == 200
        assert resp.json()["kcal_goal"] == 1800

    # Создание новой цели не удаляет старую (история сохраняется)
    async def test_multiple_goals_history_preserved(self, authed_client: AsyncClient):
        await authed_client.post(GOALS_URL, json={
            "kcal_goal": 2000,
            "effective_from": str(date.today() - timedelta(days=7)),
        })
        await authed_client.post(GOALS_URL, json={
            "kcal_goal": 2200,
            "effective_from": str(date.today()),
        })

        resp = await authed_client.get(CURRENT_GOAL_URL)
        assert resp.status_code == 200
        assert resp.json()["kcal_goal"] == 2200
