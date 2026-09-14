"""
Unit-тесты бизнес-логики habits. Нет БД, нет HTTP.

calculate_streak(checkin_dates, frequency_type, weekly_days, today)
    -> tuple[int, bool, int]  # (current_streak, broken, previous_streak)

is_scheduled_day(frequency_type, weekly_days, d) -> bool

Покрытие критериев приёмки:
  AC#1 (streak=0 при создании) — test_no_checkins_returns_zero
  AC#2 (streak=1 после первого чекина) — test_daily_checkin_today_streak_one
  AC#4 (3 дня подряд, сегодня нет → streak=3) — test_daily_consecutive_ending_yesterday
  AC#5 (пропуск вчера → streak=0, broken) — test_daily_gap_yesterday_*
  AC#6 (незапланированный день) — test_weekly_*, test_is_scheduled_day_*
"""

from datetime import date

import pytest

from app.modules.habits.service import calculate_streak, is_scheduled_day


# ---------------------------------------------------------------------------
# is_scheduled_day
# ---------------------------------------------------------------------------

class TestIsScheduledDay:
    def test_daily_any_weekday_is_scheduled(self):
        for d in (date(2024, 1, 1), date(2024, 1, 4), date(2024, 1, 7)):
            assert is_scheduled_day("daily", None, d) is True

    def test_weekly_days_scheduled_days_match(self):
        # weekly_days [0,2,4] = пн/ср/пт
        assert is_scheduled_day("weekly_days", [0, 2, 4], date(2024, 1, 1)) is True   # пн
        assert is_scheduled_day("weekly_days", [0, 2, 4], date(2024, 1, 3)) is True   # ср
        assert is_scheduled_day("weekly_days", [0, 2, 4], date(2024, 1, 5)) is True   # пт

    def test_weekly_days_unscheduled_days_excluded(self):
        # weekly_days [0,2,4] = пн/ср/пт; вт/чт/сб/вс — не запланированы
        assert is_scheduled_day("weekly_days", [0, 2, 4], date(2024, 1, 2)) is False  # вт
        assert is_scheduled_day("weekly_days", [0, 2, 4], date(2024, 1, 4)) is False  # чт
        assert is_scheduled_day("weekly_days", [0, 2, 4], date(2024, 1, 6)) is False  # сб
        assert is_scheduled_day("weekly_days", [0, 2, 4], date(2024, 1, 7)) is False  # вс


# ---------------------------------------------------------------------------
# calculate_streak — ежедневные привычки
# ---------------------------------------------------------------------------

class TestCalculateStreakDaily:
    # AC#1: нет чекинов → streak=0, не прерван
    def test_no_checkins_returns_zero(self):
        streak, broken, prev = calculate_streak(set(), "daily", None, date(2024, 1, 10))
        assert streak == 0
        assert broken is False

    # AC#2 (unit-часть): чекин сегодня → streak=1
    def test_checkin_today_streak_one(self):
        today = date(2024, 1, 10)
        streak, broken, _ = calculate_streak({today}, "daily", None, today)
        assert streak == 1
        assert broken is False

    # чекин вчера (сегодня ещё не отмечено) → streak=1, не прерван
    def test_checkin_yesterday_streak_one(self):
        today = date(2024, 1, 10)
        yesterday = date(2024, 1, 9)
        streak, broken, _ = calculate_streak({yesterday}, "daily", None, today)
        assert streak == 1
        assert broken is False

    # AC#4: 3 чекина подряд, последний — вчера; сегодня нет → streak=3, не прерван
    def test_three_consecutive_ending_yesterday_streak_three(self):
        today = date(2024, 1, 10)
        checkins = {date(2024, 1, 7), date(2024, 1, 8), date(2024, 1, 9)}
        streak, broken, _ = calculate_streak(checkins, "daily", None, today)
        assert streak == 3
        assert broken is False

    # сегодня добавляется к уже существующей серии → streak=4
    def test_checkin_today_extends_existing_streak(self):
        today = date(2024, 1, 10)
        checkins = {date(2024, 1, 7), date(2024, 1, 8), date(2024, 1, 9), today}
        streak, broken, _ = calculate_streak(checkins, "daily", None, today)
        assert streak == 4

    # AC#5: чекин позавчера, вчера пропущено → streak=0, broken, previous=1
    def test_gap_yesterday_streak_broken(self):
        today = date(2024, 1, 10)
        checkins = {date(2024, 1, 8)}  # позавчера
        streak, broken, prev = calculate_streak(checkins, "daily", None, today)
        assert streak == 0
        assert broken is True
        assert prev == 1

    # AC#5 точное previous_streak: 3 подряд, потом пропуск
    def test_gap_yesterday_previous_streak_correct(self):
        today = date(2024, 1, 10)
        checkins = {date(2024, 1, 5), date(2024, 1, 6), date(2024, 1, 7)}  # 3 дня, последний — 3 дня назад
        streak, broken, prev = calculate_streak(checkins, "daily", None, today)
        assert streak == 0
        assert broken is True
        assert prev == 3

    # нет чекинов вообще → не считается "прерванным" (стрик никогда не начинался)
    def test_no_checkins_not_broken(self):
        today = date(2024, 1, 10)
        streak, broken, prev = calculate_streak(set(), "daily", None, today)
        assert broken is False
        assert prev == 0


# ---------------------------------------------------------------------------
# calculate_streak — еженедельные привычки
# ---------------------------------------------------------------------------

class TestCalculateStreakWeekly:
    # AC#6 (unit-часть): чекин в незапланированный день → streak=0, не увеличивается
    def test_unscheduled_checkin_not_counted(self):
        # weekly [0,2,4]; today=ср 3 янв; чекин во вт 2 янв (незапланировано)
        today = date(2024, 1, 3)   # среда
        checkins = {date(2024, 1, 2)}  # вторник — не в [0,2,4]
        streak, broken, _ = calculate_streak(checkins, "weekly_days", [0, 2, 4], today)
        assert streak == 0

    # последовательные запланированные дни считаются нормально
    def test_consecutive_scheduled_days_streak(self):
        # weekly [0,2,4]; today=пт 5 янв; чекины пн+ср+пт → streak=3
        today = date(2024, 1, 5)   # пятница
        checkins = {date(2024, 1, 1), date(2024, 1, 3), date(2024, 1, 5)}
        streak, broken, _ = calculate_streak(checkins, "weekly_days", [0, 2, 4], today)
        assert streak == 3

    # незапланированный чекин внутри серии не прерывает и не сохраняет стрик
    def test_unscheduled_checkin_mixed_with_scheduled(self):
        # weekly [0,2,4]; today=ср 3 янв; чекин пн+вт; ср пока нет
        # пн — запланирован, вт — нет; последний completed scheduled = пн → streak=1
        today = date(2024, 1, 3)   # среда
        checkins = {date(2024, 1, 1), date(2024, 1, 2)}  # пн (✓) + вт (✗ scheduled)
        streak, broken, _ = calculate_streak(checkins, "weekly_days", [0, 2, 4], today)
        assert streak == 1

    # пропуск запланированного дня → broken
    def test_missed_scheduled_day_broken(self):
        # weekly [0,2,4]; today=пт 5 янв; чекин только пн; ср пропущена → broken
        today = date(2024, 1, 5)   # пятница
        checkins = {date(2024, 1, 1)}  # только понедельник
        streak, broken, prev = calculate_streak(checkins, "weekly_days", [0, 2, 4], today)
        assert streak == 0
        assert broken is True
        assert prev == 1
