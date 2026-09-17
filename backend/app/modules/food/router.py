import uuid
from datetime import date
from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user_id
from app.core.db import get_session
from app.core.events.bus import bus
from app.modules.food.schemas import (
    DailyGoalCreate,
    DailyGoalResponse,
    ExternalProductPreview,
    ImportExternalRequest,
    MealEntryCreate,
    MealEntryResponse,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    SummaryResponse,
)
from app.modules.food.service import FoodService

router = APIRouter(prefix="/api/food", tags=["food"])

_UserId = Annotated[uuid.UUID, Depends(get_current_user_id)]


async def _call_off(coro):
    """Translates httpx.TimeoutException → HTTP 502 for Open Food Facts calls."""
    try:
        return await coro
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Open Food Facts unavailable",
        )


def _svc(session: AsyncSession = Depends(get_session)) -> FoodService:
    return FoodService(session, bus)


_Svc = Annotated[FoodService, Depends(_svc)]


# ------------------------------------------------------------------
# Products
# ------------------------------------------------------------------

@router.post("/products", status_code=status.HTTP_201_CREATED, response_model=ProductResponse)
async def create_product(body: ProductCreate, user_id: _UserId, svc: _Svc):
    return await svc.create_product(
        user_id=user_id,
        name=body.name,
        kcal_per_100g=body.kcal_per_100g,
        protein_g_per_100g=body.protein_g_per_100g,
        fat_g_per_100g=body.fat_g_per_100g,
        carbs_g_per_100g=body.carbs_g_per_100g,
    )


@router.get("/products", response_model=list[ProductResponse])
async def list_products(
    user_id: _UserId,
    svc: _Svc,
    q: Optional[str] = Query(default=None),
):
    return await svc.list_products(q=q)


@router.get("/products/search-external", response_model=list[ExternalProductPreview])
async def search_external_products(
    user_id: _UserId,
    svc: _Svc,
    q: str = Query(...),
):
    return await _call_off(svc.search_external(q))


@router.post("/products/import-external", response_model=ProductResponse)
async def import_external_product(
    body: ImportExternalRequest,
    user_id: _UserId,
    svc: _Svc,
    response: Response,
):
    product, created = await _call_off(svc.import_external(body.external_id))
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return product


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    user_id: _UserId,
    svc: _Svc,
):
    return await svc.update_product(
        user_id=user_id,
        product_id=product_id,
        **body.model_dump(exclude_none=True),
    )


# ------------------------------------------------------------------
# Meal entries
# ------------------------------------------------------------------

@router.post(
    "/meal-entries", status_code=status.HTTP_201_CREATED, response_model=MealEntryResponse
)
async def create_meal_entry(body: MealEntryCreate, user_id: _UserId, svc: _Svc):
    return await svc.create_meal_entry(
        user_id=user_id,
        product_id=body.product_id,
        quantity_g=body.quantity_g,
        meal_type=body.meal_type,
        logged_at=body.logged_at,
        price_kopecks=body.price_kopecks,
    )


@router.get("/meal-entries", response_model=list[MealEntryResponse])
async def list_meal_entries(
    user_id: _UserId,
    svc: _Svc,
    date: date = Query(...),
):
    return await svc.list_meal_entries(user_id=user_id, entry_date=date)


@router.delete("/meal-entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_entry(entry_id: uuid.UUID, user_id: _UserId, svc: _Svc):
    await svc.delete_meal_entry(user_id=user_id, entry_id=entry_id)


# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------

@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    user_id: _UserId,
    svc: _Svc,
    date: date = Query(...),
):
    return await svc.get_summary(user_id=user_id, entry_date=date)


# ------------------------------------------------------------------
# Daily goals
# ------------------------------------------------------------------

@router.post("/goals", status_code=status.HTTP_201_CREATED, response_model=DailyGoalResponse)
async def create_goal(body: DailyGoalCreate, user_id: _UserId, svc: _Svc):
    return await svc.create_goal(
        user_id=user_id,
        kcal_goal=body.kcal_goal,
        effective_from=body.effective_from,
        protein_goal_g=body.protein_goal_g,
        fat_goal_g=body.fat_goal_g,
        carbs_goal_g=body.carbs_goal_g,
    )


@router.get("/goals/current", response_model=DailyGoalResponse)
async def get_current_goal(user_id: _UserId, svc: _Svc):
    goal = await svc.get_current_goal(user_id=user_id)
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active goal")
    return goal
