import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    kcal_per_100g: float
    protein_g_per_100g: float
    fat_g_per_100g: float
    carbs_g_per_100g: float


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    kcal_per_100g: Optional[float] = None
    protein_g_per_100g: Optional[float] = None
    fat_g_per_100g: Optional[float] = None
    carbs_g_per_100g: Optional[float] = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    external_id: Optional[str]
    name: str
    kcal_per_100g: float
    protein_g_per_100g: float
    fat_g_per_100g: float
    carbs_g_per_100g: float
    created_at: datetime

    model_config = {"from_attributes": True}


class MealEntryCreate(BaseModel):
    product_id: uuid.UUID
    quantity_g: float
    meal_type: str  # breakfast | lunch | dinner | snack
    logged_at: Optional[datetime] = None
    price_kopecks: Optional[int] = None


class MealEntryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    quantity_g: float
    meal_type: str
    logged_at: datetime
    price_kopecks: Optional[int]
    kcal: float
    protein_g: float
    fat_g: float
    carbs_g: float

    model_config = {"from_attributes": True}


class DailyGoalCreate(BaseModel):
    kcal_goal: int
    protein_goal_g: Optional[int] = None
    fat_goal_g: Optional[int] = None
    carbs_goal_g: Optional[int] = None
    effective_from: date


class DailyGoalResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    kcal_goal: int
    protein_goal_g: Optional[int]
    fat_goal_g: Optional[int]
    carbs_goal_g: Optional[int]
    effective_from: date

    model_config = {"from_attributes": True}


class SummaryResponse(BaseModel):
    kcal_total: float
    protein_total: float
    fat_total: float
    carbs_total: float
    kcal_goal: Optional[int]
    goal_reached: bool


class ExternalProductPreview(BaseModel):
    """Результат поиска в Open Food Facts — продукт ещё не в локальной БД, нет `id`."""
    external_id: str
    name: str
    kcal_per_100g: float
    protein_g_per_100g: float
    fat_g_per_100g: float
    carbs_g_per_100g: float


class ImportExternalRequest(BaseModel):
    external_id: str
