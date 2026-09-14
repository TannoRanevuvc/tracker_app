from datetime import date, datetime
from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    calories_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float


class ProductRead(BaseModel):
    id: int
    name: str
    calories_per_100g: float
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float

    model_config = {"from_attributes": True}


class MealCreate(BaseModel):
    product_id: int
    grams: float
    eaten_at: datetime


class MealRead(BaseModel):
    id: int
    product_id: int
    grams: float
    eaten_at: datetime

    model_config = {"from_attributes": True}


class DailySummary(BaseModel):
    date: date
    calories: float
    protein: float
    fat: float
    carbs: float
