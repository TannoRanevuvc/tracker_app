"""
Unit-тесты бизнес-логики finance. Нет БД, нет HTTP.

Покрытие критериев приёмки:
  AC#3 (recurring monthly → next_due_date сдвигается на +1 месяц) — TestComputeNextDueDate
  AC#4 (3 пропущенных периода → get_pending_periods возвращает 3) — TestGetPendingPeriods
"""

from datetime import date

import pytest

from app.modules.finance.service import compute_next_due_date, get_pending_periods


class TestComputeNextDueDate:
    # AC#3: monthly — следующий период ровно через месяц
    def test_monthly_day_1_shifts_to_next_month(self):
        assert compute_next_due_date(
            frequency="monthly",
            current_due_date=date(2024, 1, 1),
            day_of_month=1,
        ) == date(2024, 2, 1)

    def test_monthly_day_15_shifts_to_next_month(self):
        assert compute_next_due_date(
            frequency="monthly",
            current_due_date=date(2024, 3, 15),
            day_of_month=15,
        ) == date(2024, 4, 15)

    def test_monthly_december_wraps_to_january(self):
        assert compute_next_due_date(
            frequency="monthly",
            current_due_date=date(2024, 12, 1),
            day_of_month=1,
        ) == date(2025, 1, 1)

    # weekly — сдвиг ровно на 7 дней
    def test_weekly_shifts_by_7_days(self):
        assert compute_next_due_date(
            frequency="weekly",
            current_due_date=date(2024, 1, 1),
            day_of_week=0,
        ) == date(2024, 1, 8)

    def test_weekly_wraps_across_month_boundary(self):
        assert compute_next_due_date(
            frequency="weekly",
            current_due_date=date(2024, 1, 29),
            day_of_week=0,
        ) == date(2024, 2, 5)


class TestGetPendingPeriods:
    # AC#3: одна просроченная дата → список из одного элемента
    def test_one_overdue_monthly_returns_one(self):
        # today=Jan 31: Jan 1 <= Jan 31 (YES), Feb 1 <= Jan 31 (NO) → ровно 1
        periods = get_pending_periods(
            frequency="monthly",
            next_due_date=date(2024, 1, 1),
            day_of_month=1,
            day_of_week=None,
            today=date(2024, 1, 31),
        )
        assert len(periods) == 1
        assert periods[0] == date(2024, 1, 1)

    # AC#4: три пропущенных месяца → список из трёх элементов в хронологическом порядке
    def test_three_overdue_monthly_periods(self):
        # today=Mar 31: Jan 1, Feb 1, Mar 1 <= Mar 31 (YES), Apr 1 <= Mar 31 (NO) → ровно 3
        periods = get_pending_periods(
            frequency="monthly",
            next_due_date=date(2024, 1, 1),
            day_of_month=1,
            day_of_week=None,
            today=date(2024, 3, 31),
        )
        assert len(periods) == 3
        assert periods[0] == date(2024, 1, 1)
        assert periods[1] == date(2024, 2, 1)
        assert periods[2] == date(2024, 3, 1)

    # next_due_date в будущем → пустой список
    def test_future_due_date_returns_empty(self):
        periods = get_pending_periods(
            frequency="monthly",
            next_due_date=date(2024, 5, 1),
            day_of_month=1,
            day_of_week=None,
            today=date(2024, 4, 1),
        )
        assert len(periods) == 0

    # next_due_date == сегодня → один период (срабатывает в день наступления)
    def test_due_today_returns_one_period(self):
        today = date(2024, 3, 1)
        periods = get_pending_periods(
            frequency="monthly",
            next_due_date=today,
            day_of_month=1,
            day_of_week=None,
            today=today,
        )
        assert len(periods) == 1

    # weekly: два пропущенных периода
    def test_two_overdue_weekly_periods(self):
        # today=Jan 14: Jan 1, Jan 8 <= Jan 14 (YES), Jan 15 <= Jan 14 (NO) → ровно 2
        periods = get_pending_periods(
            frequency="weekly",
            next_due_date=date(2024, 1, 1),
            day_of_month=None,
            day_of_week=0,
            today=date(2024, 1, 14),
        )
        assert len(periods) == 2
        assert periods[0] == date(2024, 1, 1)
        assert periods[1] == date(2024, 1, 8)
