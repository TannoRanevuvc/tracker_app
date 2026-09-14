"""
Unit-тесты бизнес-логики tasks. Нет БД, нет HTTP.

is_task_overdue(due_date, status, today) -> bool

Покрытие критериев приёмки:
  AC#4 (due_date вчера + status!=done → is_overdue=True) — TestIsTaskOverdue
"""

from datetime import date, timedelta

import pytest

from app.modules.tasks.service import is_task_overdue


class TestIsTaskOverdue:
    # AC#4 — ядро логики: вчерашний дедлайн + незавершённый статус → просрочено
    def test_yesterday_todo_is_overdue(self):
        yesterday = date(2024, 6, 14)
        assert is_task_overdue(yesterday, "todo", date(2024, 6, 15)) is True

    def test_yesterday_in_progress_is_overdue(self):
        yesterday = date(2024, 6, 14)
        assert is_task_overdue(yesterday, "in_progress", date(2024, 6, 15)) is True

    # done-задача с прошедшим дедлайном — не просрочена (закрыта)
    def test_yesterday_done_not_overdue(self):
        yesterday = date(2024, 6, 14)
        assert is_task_overdue(yesterday, "done", date(2024, 6, 15)) is False

    # дедлайн сегодня — ещё не просрочено
    def test_today_due_date_not_overdue(self):
        today = date(2024, 6, 15)
        assert is_task_overdue(today, "todo", today) is False

    # дедлайн завтра — точно не просрочено
    def test_future_due_date_not_overdue(self):
        tomorrow = date(2024, 6, 16)
        assert is_task_overdue(tomorrow, "todo", date(2024, 6, 15)) is False

    # без дедлайна — никогда не просрочено
    def test_no_due_date_not_overdue(self):
        assert is_task_overdue(None, "todo", date(2024, 6, 15)) is False

    def test_no_due_date_done_not_overdue(self):
        assert is_task_overdue(None, "done", date(2024, 6, 15)) is False
