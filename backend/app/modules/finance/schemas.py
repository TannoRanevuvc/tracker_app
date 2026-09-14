import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class AccountCreate(BaseModel):
    name: str


class AccountResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    balance_kopecks: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str
    type: str  # income | expense


class CategoryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: str

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    account_id: uuid.UUID
    amount_kopecks: int
    category_id: Optional[uuid.UUID] = None
    occurred_at: date
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    account_id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    amount_kopecks: int
    occurred_at: date
    description: Optional[str] = None
    recurring_rule_id: Optional[uuid.UUID] = None
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RecurringRuleCreate(BaseModel):
    account_id: uuid.UUID
    amount_kopecks: int
    category_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    frequency: str  # monthly | weekly
    day_of_month: Optional[int] = None
    day_of_week: Optional[int] = None
    next_due_date: Optional[date] = None


class RecurringRuleUpdate(BaseModel):
    active: Optional[bool] = None
    amount_kopecks: Optional[int] = None


class RecurringRuleResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    account_id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    amount_kopecks: int
    description: Optional[str] = None
    frequency: str
    day_of_month: Optional[int] = None
    day_of_week: Optional[int] = None
    next_due_date: date
    active: bool

    model_config = {"from_attributes": True}


class BudgetCreate(BaseModel):
    category_id: uuid.UUID
    period: str  # YYYY-MM
    limit_kopecks: int


class BudgetResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category_id: uuid.UUID
    period: str
    limit_kopecks: int

    model_config = {"from_attributes": True}


class SummaryByCategoryItem(BaseModel):
    category_id: Optional[uuid.UUID]
    category_name: Optional[str]
    amount_kopecks: int


class SummaryResponse(BaseModel):
    by_category: list[SummaryByCategoryItem]
    total_income: int
    total_expense: int
