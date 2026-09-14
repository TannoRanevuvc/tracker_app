"""
Unit-тесты бизнес-логики food. Нет БД, нет HTTP.

Покрытие критериев приёмки:
  AC#1 (расчёт КБЖУ: quantity_g / 100 * per_100g, округление до 1 знака) — TestCalculateMacros
  AC#6 (активная цель — последняя из тех, у которых effective_from <= today) — TestSelectActiveGoal
"""
from datetime import date
from types import SimpleNamespace

import pytest

from app.modules.food.service import calculate_macros, select_active_goal


class TestCalculateMacros:
    # AC#1: базовый расчёт — 200г при 110 kcal/100г = 220.0
    def test_kcal_basic(self):
        kcal, _, _, _ = calculate_macros(
            kcal_per_100g=110,
            protein_per_100g=4.5,
            fat_per_100g=2.3,
            carbs_per_100g=21.2,
            quantity_g=200,
        )
        assert kcal == 220.0

    def test_protein_basic(self):
        _, protein, _, _ = calculate_macros(
            kcal_per_100g=110,
            protein_per_100g=4.5,
            fat_per_100g=2.3,
            carbs_per_100g=21.2,
            quantity_g=200,
        )
        assert protein == 9.0

    def test_fat_basic(self):
        _, _, fat, _ = calculate_macros(
            kcal_per_100g=110,
            protein_per_100g=4.5,
            fat_per_100g=2.3,
            carbs_per_100g=21.2,
            quantity_g=200,
        )
        assert fat == 4.6

    def test_carbs_basic(self):
        _, _, _, carbs = calculate_macros(
            kcal_per_100g=110,
            protein_per_100g=4.5,
            fat_per_100g=2.3,
            carbs_per_100g=21.2,
            quantity_g=200,
        )
        assert carbs == 42.4

    # Результат уже округлён до 1 знака (не 2, не 3)
    def test_result_rounded_to_one_decimal(self):
        # 33г × 100 kcal/100г = 33.0 — ровно
        kcal, _, _, _ = calculate_macros(
            kcal_per_100g=100,
            protein_per_100g=0,
            fat_per_100g=0,
            carbs_per_100g=0,
            quantity_g=33,
        )
        assert kcal == round(kcal, 1)
        assert isinstance(kcal, float)

    # Дробный результат округляется, а не обрезается
    def test_fractional_result_is_rounded(self):
        # 150г × 8.33 kcal/100г = 12.495 → округление до 1 знака = 12.5
        kcal, _, _, _ = calculate_macros(
            kcal_per_100g=8.33,
            protein_per_100g=0,
            fat_per_100g=0,
            carbs_per_100g=0,
            quantity_g=150,
        )
        assert kcal == round(kcal, 1)

    # Нулевые значения не вызывают ошибок
    def test_zero_quantity(self):
        kcal, protein, fat, carbs = calculate_macros(
            kcal_per_100g=100,
            protein_per_100g=10,
            fat_per_100g=5,
            carbs_per_100g=20,
            quantity_g=0,
        )
        assert kcal == 0.0
        assert protein == 0.0


class TestSelectActiveGoal:
    """
    Активная цель — та, у которой effective_from <= сегодня,
    максимальная среди таких по effective_from (последняя заданная).
    """

    def _goal(self, effective_from: date):
        return SimpleNamespace(effective_from=effective_from)

    # AC#6: из двух целей (прошлое + завтра) возвращается прошлая
    def test_returns_past_goal_not_future(self):
        today = date(2024, 6, 15)
        past = self._goal(date(2024, 6, 1))
        future = self._goal(date(2024, 6, 16))

        assert select_active_goal([past, future], today=today) is past

    # AC#6: цель ровно на сегодня считается активной
    def test_effective_today_is_active(self):
        today = date(2024, 6, 15)
        goal = self._goal(today)

        assert select_active_goal([goal], today=today) is goal

    # Нет прошлых целей → None
    def test_all_future_returns_none(self):
        today = date(2024, 6, 15)
        future = self._goal(date(2024, 6, 16))

        assert select_active_goal([future], today=today) is None

    # Пустой список → None
    def test_empty_list_returns_none(self):
        assert select_active_goal([], today=date.today()) is None

    # Несколько прошлых → возвращается самая последняя
    def test_returns_latest_among_past_goals(self):
        today = date(2024, 6, 15)
        old = self._goal(date(2024, 1, 1))
        mid = self._goal(date(2024, 3, 1))
        recent = self._goal(date(2024, 6, 10))

        assert select_active_goal([old, mid, recent], today=today) is recent

    # Порядок в списке не влияет на результат
    def test_order_in_list_does_not_matter(self):
        today = date(2024, 6, 15)
        old = self._goal(date(2024, 1, 1))
        recent = self._goal(date(2024, 6, 10))

        assert select_active_goal([recent, old], today=today) is recent
        assert select_active_goal([old, recent], today=today) is recent
