import uuid
from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.core.db import get_session
from app.core.events.bus import bus
from app.modules.finance.schemas import (
    AccountCreate,
    AccountResponse,
    BudgetCreate,
    BudgetResponse,
    CategoryCreate,
    CategoryResponse,
    RecurringRuleCreate,
    RecurringRuleResponse,
    RecurringRuleUpdate,
    SummaryResponse,
    TransactionCreate,
    TransactionResponse,
)
from app.modules.finance.service import FinanceService

router = APIRouter(prefix="/api/finance", tags=["finance"])

_UserId = Annotated[uuid.UUID, Depends(get_current_user_id)]


def _svc(session: AsyncSession = Depends(get_session)) -> FinanceService:
    return FinanceService(session, bus)


_Svc = Annotated[FinanceService, Depends(_svc)]


# ------------------------------------------------------------------
# Accounts
# ------------------------------------------------------------------

@router.post("/accounts", status_code=status.HTTP_201_CREATED, response_model=AccountResponse)
async def create_account(body: AccountCreate, user_id: _UserId, svc: _Svc):
    return await svc.create_account(user_id=user_id, name=body.name)


@router.get("/accounts", response_model=list[AccountResponse])
async def list_accounts(user_id: _UserId, svc: _Svc):
    return await svc.list_accounts(user_id=user_id)


# ------------------------------------------------------------------
# Categories
# ------------------------------------------------------------------

@router.post(
    "/categories", status_code=status.HTTP_201_CREATED, response_model=CategoryResponse
)
async def create_category(body: CategoryCreate, user_id: _UserId, svc: _Svc):
    return await svc.create_category(user_id=user_id, name=body.name, type=body.type)


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(user_id: _UserId, svc: _Svc):
    return await svc.list_categories(user_id=user_id)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    await svc.delete_category(user_id=user_id, category_id=category_id)


# ------------------------------------------------------------------
# Transactions
# ------------------------------------------------------------------

@router.post(
    "/transactions", status_code=status.HTTP_201_CREATED, response_model=TransactionResponse
)
async def create_transaction(body: TransactionCreate, user_id: _UserId, svc: _Svc):
    return await svc.create_transaction(
        user_id=user_id,
        account_id=body.account_id,
        amount_kopecks=body.amount_kopecks,
        occurred_at=body.occurred_at,
        category_id=body.category_id,
        description=body.description,
    )


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    user_id: _UserId,
    svc: _Svc,
    account_id: Optional[uuid.UUID] = Query(default=None),
    category_id: Optional[uuid.UUID] = Query(default=None),
    from_: Optional[str] = Query(default=None, alias="from"),
    to: Optional[str] = Query(default=None),
):
    from_date = date.fromisoformat(from_) if from_ else None
    to_date = date.fromisoformat(to) if to else None
    return await svc.list_transactions(
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(transaction_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    await svc.delete_transaction(user_id=user_id, transaction_id=transaction_id)


# ------------------------------------------------------------------
# Recurring rules
# ------------------------------------------------------------------

@router.post(
    "/recurring-rules",
    status_code=status.HTTP_201_CREATED,
    response_model=RecurringRuleResponse,
)
async def create_recurring_rule(body: RecurringRuleCreate, user_id: _UserId, svc: _Svc):
    return await svc.create_recurring_rule(
        user_id=user_id,
        account_id=body.account_id,
        amount_kopecks=body.amount_kopecks,
        frequency=body.frequency,
        day_of_month=body.day_of_month,
        day_of_week=body.day_of_week,
        category_id=body.category_id,
        description=body.description,
        next_due_date=body.next_due_date,
    )


@router.get("/recurring-rules", response_model=list[RecurringRuleResponse])
async def list_recurring_rules(user_id: _UserId, svc: _Svc):
    return await svc.list_recurring_rules(user_id=user_id)


@router.patch("/recurring-rules/{rule_id}", response_model=RecurringRuleResponse)
async def update_recurring_rule(
    rule_id: uuid.UUID, body: RecurringRuleUpdate, user_id: _UserId, svc: _Svc
):
    return await svc.update_recurring_rule(
        user_id=user_id,
        rule_id=rule_id,
        active=body.active,
        amount_kopecks=body.amount_kopecks,
    )


# ------------------------------------------------------------------
# Budgets
# ------------------------------------------------------------------

@router.post(
    "/budgets", status_code=status.HTTP_201_CREATED, response_model=BudgetResponse
)
async def create_budget(body: BudgetCreate, user_id: _UserId, svc: _Svc):
    return await svc.create_budget(
        user_id=user_id,
        category_id=body.category_id,
        period=body.period,
        limit_kopecks=body.limit_kopecks,
    )


# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------

@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    user_id: _UserId,
    svc: _Svc,
    period: str = Query(...),
):
    return await svc.get_summary(user_id=user_id, period=period)
