from pydantic import BaseModel


class TransactionCreate(BaseModel):
    account_id: int
    category_id: int
    amount_kopecks: int
    note: str | None = None


class TransactionRead(BaseModel):
    id: int
    account_id: int
    category_id: int
    amount_kopecks: int
    note: str | None

    model_config = {"from_attributes": True}


class AccountCreate(BaseModel):
    name: str
    balance_kopecks: int = 0


class AccountRead(BaseModel):
    id: int
    name: str
    balance_kopecks: int

    model_config = {"from_attributes": True}
