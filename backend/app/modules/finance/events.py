PUBLISHES = [
    "finance.transaction_added",
    "finance.budget_exceeded",
]

SUBSCRIBES_TO = {
    "food.meal_logged": "on_food_meal_logged",
}
