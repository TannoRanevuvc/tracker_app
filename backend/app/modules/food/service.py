from sqlalchemy.ext.asyncio import AsyncSession


class FoodService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_products(self):
        pass

    async def create_product(self, data):
        pass

    async def search_products(self, query: str):
        pass

    async def log_meal(self, data):
        pass

    async def delete_meal(self, meal_id: int):
        pass

    async def daily_summary(self, date):
        pass
