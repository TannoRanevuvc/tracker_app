"""
Unit-тесты бизнес-логики motivation. Нет БД, нет HTTP.

calculate_level(xp_total: int) -> int
calculate_xp_to_next_level(xp_total: int) -> int

Покрытие критериев приёмки:
  AC#1 (xp_total=0, habit.completed → +10 XP) — формула XP из конфига
  AC#2 (xp_total=95 + 10 XP → level 1→2) — calculate_level
  AC#5 (task high→10 XP, task low→5 XP) — XP-конфиг по приоритету
  Производная: xp_to_next_level вычисляется корректно
"""

import pytest


# ---------------------------------------------------------------------------
# calculate_level
# ---------------------------------------------------------------------------

class TestCalculateLevel:
    # AC#2 (уровень 1 при xp<100)
    def test_zero_xp_is_level_1(self):
        from app.modules.motivation.service import calculate_level
        assert calculate_level(0) == 1

    def test_99_xp_is_level_1(self):
        from app.modules.motivation.service import calculate_level
        assert calculate_level(99) == 1

    # AC#2 (xp=100 → уровень 2)
    def test_100_xp_is_level_2(self):
        from app.modules.motivation.service import calculate_level
        assert calculate_level(100) == 2

    # AC#2 (xp=105 → уровень 2, внутри диапазона)
    def test_105_xp_is_level_2(self):
        from app.modules.motivation.service import calculate_level
        assert calculate_level(105) == 2

    def test_199_xp_is_level_2(self):
        from app.modules.motivation.service import calculate_level
        assert calculate_level(199) == 2

    def test_200_xp_is_level_3(self):
        from app.modules.motivation.service import calculate_level
        assert calculate_level(200) == 3

    # граница: ровно на пороге
    def test_level_boundary_exact(self):
        from app.modules.motivation.service import calculate_level
        for xp, expected_level in [(0, 1), (100, 2), (200, 3), (500, 6), (999, 10)]:
            assert calculate_level(xp) == expected_level, f"xp={xp}"


# ---------------------------------------------------------------------------
# calculate_xp_to_next_level
# ---------------------------------------------------------------------------

class TestCalculateXpToNextLevel:
    # 0 XP — до следующего уровня ровно 100
    def test_zero_xp_needs_100(self):
        from app.modules.motivation.service import calculate_xp_to_next_level
        assert calculate_xp_to_next_level(0) == 100

    # AC#2: 95 XP → 5 до следующего уровня
    def test_95_xp_needs_5(self):
        from app.modules.motivation.service import calculate_xp_to_next_level
        assert calculate_xp_to_next_level(95) == 5

    # ровно на пороге уровня → снова 100 до следующего
    def test_at_level_boundary_needs_100(self):
        from app.modules.motivation.service import calculate_xp_to_next_level
        assert calculate_xp_to_next_level(100) == 100

    def test_150_xp_needs_50(self):
        from app.modules.motivation.service import calculate_xp_to_next_level
        assert calculate_xp_to_next_level(150) == 50

    def test_199_xp_needs_1(self):
        from app.modules.motivation.service import calculate_xp_to_next_level
        assert calculate_xp_to_next_level(199) == 1

    def test_200_xp_needs_100(self):
        from app.modules.motivation.service import calculate_xp_to_next_level
        assert calculate_xp_to_next_level(200) == 100


# ---------------------------------------------------------------------------
# XP-правила из конфига
# ---------------------------------------------------------------------------

class TestXpConfig:
    """Проверяет, что конфигурационные константы XP соответствуют спеке."""

    # AC#1: habit.completed → 10 XP
    def test_habit_completed_xp(self):
        from app.modules.motivation.service import XP_RULES
        assert XP_RULES["habit_completed"] == 10

    # AC#5: task.completed high → 10 XP
    def test_task_high_priority_xp(self):
        from app.modules.motivation.service import XP_RULES
        assert XP_RULES["task_completed_high"] == 10

    # AC#5: task.completed low/medium → 5 XP
    def test_task_low_priority_xp(self):
        from app.modules.motivation.service import XP_RULES
        assert XP_RULES["task_completed_low"] == 5

    def test_task_medium_priority_xp(self):
        from app.modules.motivation.service import XP_RULES
        assert XP_RULES["task_completed_medium"] == 5

    # food.daily_goal_reached → 15 XP
    def test_food_daily_goal_xp(self):
        from app.modules.motivation.service import XP_RULES
        assert XP_RULES["food_daily_goal_reached"] == 15


# ---------------------------------------------------------------------------
# Пороги ачивок по стрику
# ---------------------------------------------------------------------------

class TestStreakAchievementThresholds:
    """Пороги 7/30/100 стрика зафиксированы в конфиге, не хардкодом в нескольких местах."""

    def test_streak_thresholds_contain_7_30_100(self):
        from app.modules.motivation.service import STREAK_ACHIEVEMENT_MAP
        assert 7 in STREAK_ACHIEVEMENT_MAP
        assert 30 in STREAK_ACHIEVEMENT_MAP
        assert 100 in STREAK_ACHIEVEMENT_MAP

    def test_streak_7_maps_to_correct_code(self):
        from app.modules.motivation.service import STREAK_ACHIEVEMENT_MAP
        assert STREAK_ACHIEVEMENT_MAP[7] == "streak_7"

    def test_streak_30_maps_to_correct_code(self):
        from app.modules.motivation.service import STREAK_ACHIEVEMENT_MAP
        assert STREAK_ACHIEVEMENT_MAP[30] == "streak_30"

    def test_streak_100_maps_to_correct_code(self):
        from app.modules.motivation.service import STREAK_ACHIEVEMENT_MAP
        assert STREAK_ACHIEVEMENT_MAP[100] == "streak_100"
