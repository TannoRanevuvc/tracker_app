"""
Контрактные тесты событий модуля food.

Уровень 1 — статические: PUBLISHES/SUBSCRIBES_TO соответствуют спеке.
Уровень 2 — функциональные: реальная публикация через FoodService.

Покрытие критериев приёмки:
  AC#1 (food.meal_logged публикуется при создании записи, payload содержит kcal) — TestMealLogged
  AC#2 (food.daily_goal_reached при первом превышении цели, payload содержит kcal_total) — TestDailyGoalReached
  AC#3 (food.daily_goal_reached не публикуется повторно в тот же день) — TestDailyGoalReached
  AC#4 (food.meal_logged с price_kopecks: null, когда цена не указана) — TestMealLogged
"""
from datetime import date

import pytest

from app.core.events.bus import EventBus
from app.modules.food import events as food_events


# ---------------------------------------------------------------------------
# Статический контракт
# ---------------------------------------------------------------------------

class TestEventContract:
    def test_publishes_meal_logged(self):
        assert "food.meal_logged" in food_events.PUBLISHES

    def test_publishes_daily_goal_reached(self):
        assert "food.daily_goal_reached" in food_events.PUBLISHES

    def test_no_extra_published_events(self):
        assert set(food_events.PUBLISHES) == {
            "food.meal_logged",
            "food.daily_goal_reached",
        }

    def test_no_subscriptions(self):
        assert food_events.SUBSCRIBES_TO == {}


# ---------------------------------------------------------------------------
# Вспомогательная функция
# ---------------------------------------------------------------------------

async def _make_product(svc, user_id, name="Гречка", kcal=110):
    return await svc.create_product(
        user_id=user_id,
        name=name,
        kcal_per_100g=kcal,
        protein_g_per_100g=4.5,
        fat_g_per_100g=2.3,
        carbs_g_per_100g=21.2,
    )


# ---------------------------------------------------------------------------
# AC#1, AC#4 — food.meal_logged
# ---------------------------------------------------------------------------

class TestMealLogged:
    # AC#1: создание meal_entry → food.meal_logged публикуется
    async def test_meal_logged_published(self, db_session, test_user):
        from app.modules.food.service import FoodService

        test_bus = EventBus()
        received = []
        test_bus.subscribe("food.meal_logged", lambda p: received.append(p))

        svc = FoodService(db_session, test_bus)
        product = await _make_product(svc, test_user.id)
        await svc.create_meal_entry(
            user_id=test_user.id,
            product_id=product.id,
            quantity_g=200,
            meal_type="lunch",
        )

        assert len(received) == 1

    # AC#1: payload содержит meal_entry_id, user_id, date, kcal
    async def test_meal_logged_payload_fields(self, db_session, test_user):
        from app.modules.food.service import FoodService

        test_bus = EventBus()
        received = []
        test_bus.subscribe("food.meal_logged", lambda p: received.append(p))

        svc = FoodService(db_session, test_bus)
        product = await _make_product(svc, test_user.id, kcal=110)
        await svc.create_meal_entry(
            user_id=test_user.id,
            product_id=product.id,
            quantity_g=200,  # 200/100 * 110 = 220.0
            meal_type="lunch",
        )

        payload = received[0]
        assert "meal_entry_id" in payload
        assert str(payload["user_id"]) == str(test_user.id)
        assert "date" in payload
        assert payload["kcal"] == 220.0

    # AC#4: без price_kopecks → price_kopecks: None в событии
    async def test_meal_logged_without_price_has_null(self, db_session, test_user):
        from app.modules.food.service import FoodService

        test_bus = EventBus()
        received = []
        test_bus.subscribe("food.meal_logged", lambda p: received.append(p))

        svc = FoodService(db_session, test_bus)
        product = await _make_product(svc, test_user.id)
        await svc.create_meal_entry(
            user_id=test_user.id,
            product_id=product.id,
            quantity_g=100,
            meal_type="dinner",
            price_kopecks=None,
        )

        assert received[0]["price_kopecks"] is None

    # С price_kopecks → значение передаётся
    async def test_meal_logged_with_price_in_payload(self, db_session, test_user):
        from app.modules.food.service import FoodService

        test_bus = EventBus()
        received = []
        test_bus.subscribe("food.meal_logged", lambda p: received.append(p))

        svc = FoodService(db_session, test_bus)
        product = await _make_product(svc, test_user.id)
        await svc.create_meal_entry(
            user_id=test_user.id,
            product_id=product.id,
            quantity_g=100,
            meal_type="breakfast",
            price_kopecks=8500,
        )

        assert received[0]["price_kopecks"] == 8500


# ---------------------------------------------------------------------------
# AC#2, AC#3 — food.daily_goal_reached
# ---------------------------------------------------------------------------

class TestDailyGoalReached:
    # AC#2: когда суммарный kcal за день впервые достигает цели → событие публикуется
    async def test_goal_reached_published_on_first_crossing(self, db_session, test_user):
        from app.modules.food.service import FoodService

        test_bus = EventBus()
        received = []
        test_bus.subscribe("food.daily_goal_reached", lambda p: received.append(p))

        svc = FoodService(db_session, test_bus)
        await svc.create_goal(
            user_id=test_user.id,
            kcal_goal=2000,
            effective_from=date.today(),
        )
        # product: 1000 kcal/100г
        product = await _make_product(svc, test_user.id, kcal=1000)

        # 190г → 1900 kcal (ниже цели, события нет)
        await svc.create_meal_entry(
            user_id=test_user.id,
            product_id=product.id,
            quantity_g=190,
            meal_type="breakfast",
        )
        assert len(received) == 0

        # 15г → +150 kcal → итого 2050 ≥ 2000 → событие
        await svc.create_meal_entry(
            user_id=test_user.id,
            product_id=product.id,
            quantity_g=15,
            meal_type="lunch",
        )
        assert len(received) == 1

    # AC#2: payload содержит user_id, date, kcal_total, kcal_goal
    async def test_goal_reached_payload_fields(self, db_session, test_user):
        from app.modules.food.service import FoodService

        test_bus = EventBus()
        received = []
        test_bus.subscribe("food.daily_goal_reached", lambda p: received.append(p))

        svc = FoodService(db_session, test_bus)
        await svc.create_goal(
            user_id=test_user.id,
            kcal_goal=2000,
            effective_from=date.today(),
        )
        product = await _make_product(svc, test_user.id, kcal=1000)
        await svc.create_meal_entry(
            user_id=test_user.id,
            product_id=product.id,
            quantity_g=205,  # 2050 kcal ≥ 2000
            meal_type="lunch",
        )

        payload = received[0]
        assert str(payload["user_id"]) == str(test_user.id)
        assert "date" in payload
        assert payload["kcal_goal"] == 2000
        assert payload["kcal_total"] >= 2000

    # AC#3: повторный приём после достижения цели не публикует событие снова
    async def test_goal_reached_not_published_twice_same_day(self, db_session, test_user):
        from app.modules.food.service import FoodService

        test_bus = EventBus()
        received = []
        test_bus.subscribe("food.daily_goal_reached", lambda p: received.append(p))

        svc = FoodService(db_session, test_bus)
        await svc.create_goal(
            user_id=test_user.id,
            kcal_goal=500,
            effective_from=date.today(),
        )
        product = await _make_product(svc, test_user.id, kcal=1000)

        # Первый приём: 60г = 600 kcal > 500 → первое событие
        await svc.create_meal_entry(
            user_id=test_user.id,
            product_id=product.id,
            quantity_g=60,
            meal_type="breakfast",
        )
        assert len(received) == 1

        # Второй приём в тот же день — повторного события нет
        await svc.create_meal_entry(
            user_id=test_user.id,
            product_id=product.id,
            quantity_g=10,
            meal_type="snack",
        )
        assert len(received) == 1

    # Цель не задана → daily_goal_reached никогда не публикуется
    async def test_no_goal_no_event(self, db_session, test_user):
        from app.modules.food.service import FoodService

        test_bus = EventBus()
        received = []
        test_bus.subscribe("food.daily_goal_reached", lambda p: received.append(p))

        svc = FoodService(db_session, test_bus)
        product = await _make_product(svc, test_user.id, kcal=1000)
        await svc.create_meal_entry(
            user_id=test_user.id,
            product_id=product.id,
            quantity_g=300,
            meal_type="lunch",
        )

        assert len(received) == 0
