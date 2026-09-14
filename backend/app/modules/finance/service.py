from sqlalchemy.ext.asyncio import AsyncSession


class FinanceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_transactions(self):
        pass

    async def create_transaction(self, data):
        pass

    async def delete_transaction(self, transaction_id: int):
        pass

    async def list_accounts(self):
        pass

    async def create_account(self, data):
        pass
