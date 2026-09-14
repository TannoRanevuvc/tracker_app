PUBLISHES: list = []

SUBSCRIBES_TO = {
    "habit.completed": "app.modules.motivation.handlers.on_habit_completed",
    "habit.streak_broken": "app.modules.motivation.handlers.on_streak_broken",
    "task.completed": "app.modules.motivation.handlers.on_task_completed",
}
