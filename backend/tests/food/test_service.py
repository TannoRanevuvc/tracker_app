"""
Unit-тесты бизнес-логики food. Нет БД, нет HTTP.

Покрытие критериев приёмки:
  AC#1 (расчёт КБЖУ: quantity_g / 100 * per_100g, округление до 1 знака) — TestCalculateMacros
  AC#6 (активная цель — последняя из тех, у которых effective_from <= today) — TestSelectActiveGoal

Этап 2 (Open Food Facts):
  parse_off_product — TestParseOffProduct (§4 + §6; явных Given/When/Then в §7 нет,
  тесты покрывают контракт из §4 и бизнес-правила из §6)
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


# ---------------------------------------------------------------------------
# Этап 2: парсинг ответа Open Food Facts
# ---------------------------------------------------------------------------

class TestParseOffProduct:
    """
    parse_off_product(raw: dict) -> dict
    Принимает один элемент из ответа OFF API и возвращает dict, совместимый
    с ExternalProductPreview: {external_id, name, kcal_per_100g, protein_g_per_100g,
    fat_g_per_100g, carbs_g_per_100g}.

    Тесты покрывают контракт §4 и правила §6 (defaults для отсутствующих нутриентов).
    Явных Given/When/Then в §7 для этапа 2 нет — пишем по §4+§6.
    """

    def _parse(self):
        from app.modules.food.off_client import parse_off_product
        return parse_off_product

    def _raw(
        self,
        code="3017620422003",
        name="Nutella",
        kcal=539.0,
        protein=6.3,
        fat=30.9,
        carbs=57.5,
    ) -> dict:
        return {
            "code": code,
            "product_name": name,
            "nutriments": {
                "energy-kcal_100g": kcal,
                "proteins_100g": protein,
                "fat_100g": fat,
                "carbohydrates_100g": carbs,
            },
        }

    def test_external_id_equals_barcode_code(self):
        result = self._parse()(self._raw(code="3017620422003"))
        assert result["external_id"] == "3017620422003"

    def test_name_extracted(self):
        result = self._parse()(self._raw(name="Nutella"))
        assert result["name"] == "Nutella"

    def test_kcal_per_100g_extracted(self):
        result = self._parse()(self._raw(kcal=539.0))
        assert result["kcal_per_100g"] == 539.0

    def test_protein_g_per_100g_extracted(self):
        result = self._parse()(self._raw(protein=6.3))
        assert result["protein_g_per_100g"] == 6.3

    def test_fat_g_per_100g_extracted(self):
        result = self._parse()(self._raw(fat=30.9))
        assert result["fat_g_per_100g"] == 30.9

    def test_carbs_g_per_100g_extracted(self):
        result = self._parse()(self._raw(carbs=57.5))
        assert result["carbs_g_per_100g"] == 57.5

    # §6: при отсутствии нутриента в OFF-данных — default 0.0, не исключение
    def test_missing_kcal_defaults_to_zero(self):
        data = {"code": "123", "product_name": "Test", "nutriments": {}}
        result = self._parse()(data)
        assert result["kcal_per_100g"] == 0.0

    def test_missing_all_nutrients_default_to_zero(self):
        data = {"code": "123", "product_name": "Test", "nutriments": {}}
        result = self._parse()(data)
        assert result["protein_g_per_100g"] == 0.0
        assert result["fat_g_per_100g"] == 0.0
        assert result["carbs_g_per_100g"] == 0.0

    # Нет поля `id` (UUID PK) — только external_id (штрихкод/OFF-id)
    def test_no_uuid_id_in_result(self):
        result = self._parse()(self._raw())
        assert "id" not in result
        assert "external_id" in result
