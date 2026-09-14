PUBLISHES = [
    "finance.transaction_added",
    "finance.budget_exceeded",
]

SUBSCRIBES_TO = {
    "food.meal_logged": "app.modules.finance.service.on_meal_logged",
}
