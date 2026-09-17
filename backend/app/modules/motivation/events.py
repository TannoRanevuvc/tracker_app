PUBLISHES: list[str] = [
    "motivation.xp_awarded",
    "motivation.level_up",
    "motivation.achievement_unlocked",
]

SUBSCRIBES_TO: dict[str, str] = {
    "habit.completed": "app.modules.motivation.service.MotivationService.on_habit_completed",
    "habit.streak_broken": "app.modules.motivation.service.MotivationService.on_streak_broken",
    "task.completed": "app.modules.motivation.service.MotivationService.on_task_completed",
    "food.daily_goal_reached": "app.modules.motivation.service.MotivationService.on_food_daily_goal_reached",
    "finance.budget_exceeded": "app.modules.motivation.service.MotivationService.on_budget_exceeded",
}
