PUBLISHES = [
    "task.completed",
    "task.overdue",
]

SUBSCRIBES_TO = {
    "habit.completed": "app.modules.tasks.service.on_habit_completed",
}
