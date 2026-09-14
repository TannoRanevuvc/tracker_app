from fastapi import APIRouter

router = APIRouter(prefix="/api/finance", tags=["finance"])


@router.get("/transactions")
async def list_transactions():
    pass


@router.post("/transactions")
async def create_transaction():
    pass


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int):
    pass


@router.get("/accounts")
async def list_accounts():
    pass


@router.post("/accounts")
async def create_account():
    pass


@router.get("/categories")
async def list_categories():
    pass
