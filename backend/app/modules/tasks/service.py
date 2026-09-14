from sqlalchemy.ext.asyncio import AsyncSession


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_tasks(self):
        pass

    async def create_task(self, data):
        pass

    async def update_task(self, task_id: int, data):
        pass

    async def delete_task(self, task_id: int):
        pass

    async def complete_task(self, task_id: int):
        pass
