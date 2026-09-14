from sqlalchemy.ext.asyncio import AsyncSession


class HabitService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_habits(self):
        pass

    async def create_habit(self, data):
        pass

    async def update_habit(self, habit_id: int, data):
        pass

    async def delete_habit(self, habit_id: int):
        pass

    async def check_habit(self, habit_id: int):
        pass
