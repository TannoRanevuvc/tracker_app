import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.bus import EventBus
from app.modules.food import off_client as _off_client
from app.modules.food.models import DailyGoal, MealEntry, Product


# ---------------------------------------------------------------------------
# Чистые функции (unit-тестируемы без БД)
# ---------------------------------------------------------------------------

def calculate_macros(
    kcal_per_100g,
    protein_per_100g,
    fat_per_100g,
    carbs_per_100g,
    quantity_g,
) -> tuple[float, float, float, float]:
    factor = float(quantity_g) / 100
    return (
        round(float(kcal_per_100g) * factor, 1),
        round(float(protein_per_100g) * factor, 1),
        round(float(fat_per_100g) * factor, 1),
        round(float(carbs_per_100g) * factor, 1),
    )


def select_active_goal(goals, today: date):
    past = [g for g in goals if g.effective_from <= today]
    if not past:
        return None
    return max(past, key=lambda g: g.effective_from)


# ---------------------------------------------------------------------------
# Сервис
# ---------------------------------------------------------------------------

class FoodService:
    def __init__(self, session: AsyncSession, bus: EventBus) -> None:
        self.session = session
        self.bus = bus

    async def _save(self, obj):
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------

    async def create_product(
        self,
        user_id: Optional[uuid.UUID],
        name: str,
        kcal_per_100g: float,
        protein_g_per_100g: float,
        fat_g_per_100g: float,
        carbs_g_per_100g: float,
        external_id: Optional[str] = None,
    ) -> Product:
        product = Product(
            user_id=user_id,
            name=name,
            kcal_per_100g=kcal_per_100g,
            protein_g_per_100g=protein_g_per_100g,
            fat_g_per_100g=fat_g_per_100g,
            carbs_g_per_100g=carbs_g_per_100g,
            external_id=external_id,
        )
        self.session.add(product)
        return await self._save(product)

    async def list_products(self, q: Optional[str] = None) -> list[Product]:
        stmt = select(Product)
        if q:
            stmt = stmt.where(Product.name.ilike(f"%{q}%"))
        stmt = stmt.order_by(Product.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_external(self, q: str) -> list[dict]:
        return await _off_client.search_products(q)

    async def import_external(self, external_id: str) -> tuple[Product, bool]:
        result = await self.session.execute(
            select(Product).where(Product.external_id == external_id)
        )
        existing = result.scalars().first()
        if existing is not None:
            return existing, False

        data = await _off_client.get_product(external_id)
        if data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found in Open Food Facts",
            )

        product = await self.create_product(
            user_id=None,
            name=data["name"],
            kcal_per_100g=data["kcal_per_100g"],
            protein_g_per_100g=data["protein_g_per_100g"],
            fat_g_per_100g=data["fat_g_per_100g"],
            carbs_g_per_100g=data["carbs_g_per_100g"],
            external_id=external_id,
        )
        return product, True

    async def update_product(
        self,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        **fields,
    ) -> Product:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id, Product.user_id == user_id)
        )
        product = result.scalars().first()
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        for key, value in fields.items():
            if value is not None:
                setattr(product, key, value)
        return await self._save(product)

    async def _get_product(self, product_id: uuid.UUID) -> Product:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalars().first()
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    # ------------------------------------------------------------------
    # Meal entries
    # ------------------------------------------------------------------

    async def create_meal_entry(
        self,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        quantity_g: float,
        meal_type: str,
        logged_at: Optional[datetime] = None,
        price_kopecks: Optional[int] = None,
    ) -> MealEntry:
        product = await self._get_product(product_id)

        kcal, protein_g, fat_g, carbs_g = calculate_macros(
            product.kcal_per_100g,
            product.protein_g_per_100g,
            product.fat_g_per_100g,
            product.carbs_g_per_100g,
            quantity_g,
        )

        ts = logged_at or datetime.now(timezone.utc)
        entry_date = ts.date()

        # Считаем итог ДО добавления новой записи для дедупликации daily_goal_reached
        total_before = await self._get_daily_kcal_total(user_id, entry_date)
        goal = await self._get_active_goal(user_id, today=entry_date)

        entry = MealEntry(
            user_id=user_id,
            product_id=product_id,
            quantity_g=quantity_g,
            meal_type=meal_type,
            logged_at=ts,
            price_kopecks=price_kopecks,
            kcal=kcal,
            protein_g=protein_g,
            fat_g=fat_g,
            carbs_g=carbs_g,
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)

        await self.bus.publish(
            "food.meal_logged",
            {
                "meal_entry_id": str(entry.id),
                "user_id": str(user_id),
                "date": str(entry_date),
                "kcal": kcal,
                "price_kopecks": price_kopecks,
            },
        )

        # Публикуем daily_goal_reached ровно один раз: когда порог впервые пересекается
        if goal is not None and total_before < goal.kcal_goal:
            total_after = total_before + kcal
            if total_after >= goal.kcal_goal:
                await self.bus.publish(
                    "food.daily_goal_reached",
                    {
                        "user_id": str(user_id),
                        "date": str(entry_date),
                        "kcal_total": round(total_after, 1),
                        "kcal_goal": goal.kcal_goal,
                    },
                )

        return entry

    async def list_meal_entries(
        self, user_id: uuid.UUID, entry_date: date
    ) -> list[MealEntry]:
        stmt = (
            select(MealEntry)
            .where(
                MealEntry.user_id == user_id,
                cast(MealEntry.logged_at, Date) == entry_date,
            )
            .order_by(MealEntry.logged_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_meal_entry(
        self, user_id: uuid.UUID, entry_id: uuid.UUID
    ) -> None:
        result = await self.session.execute(
            select(MealEntry).where(
                MealEntry.id == entry_id, MealEntry.user_id == user_id
            )
        )
        entry = result.scalars().first()
        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal entry not found")
        await self.session.delete(entry)
        await self.session.commit()

    async def _get_daily_kcal_total(
        self, user_id: uuid.UUID, entry_date: date
    ) -> float:
        result = await self.session.execute(
            select(func.coalesce(func.sum(MealEntry.kcal), 0)).where(
                MealEntry.user_id == user_id,
                cast(MealEntry.logged_at, Date) == entry_date,
            )
        )
        return float(result.scalar())

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    async def get_summary(self, user_id: uuid.UUID, entry_date: date) -> dict:
        entries = await self.list_meal_entries(user_id, entry_date)
        kcal_total = round(sum(float(e.kcal) for e in entries), 1)
        protein_total = round(sum(float(e.protein_g) for e in entries), 1)
        fat_total = round(sum(float(e.fat_g) for e in entries), 1)
        carbs_total = round(sum(float(e.carbs_g) for e in entries), 1)

        goal = await self._get_active_goal(user_id, today=entry_date)
        kcal_goal = goal.kcal_goal if goal is not None else None
        goal_reached = (kcal_total >= kcal_goal) if kcal_goal is not None else False

        return {
            "kcal_total": kcal_total,
            "protein_total": protein_total,
            "fat_total": fat_total,
            "carbs_total": carbs_total,
            "kcal_goal": kcal_goal,
            "goal_reached": goal_reached,
        }

    # ------------------------------------------------------------------
    # Daily goals
    # ------------------------------------------------------------------

    async def create_goal(
        self,
        user_id: uuid.UUID,
        kcal_goal: int,
        effective_from: date,
        protein_goal_g: Optional[int] = None,
        fat_goal_g: Optional[int] = None,
        carbs_goal_g: Optional[int] = None,
    ) -> DailyGoal:
        goal = DailyGoal(
            user_id=user_id,
            kcal_goal=kcal_goal,
            protein_goal_g=protein_goal_g,
            fat_goal_g=fat_goal_g,
            carbs_goal_g=carbs_goal_g,
            effective_from=effective_from,
        )
        self.session.add(goal)
        return await self._save(goal)

    async def get_current_goal(self, user_id: uuid.UUID) -> Optional[DailyGoal]:
        return await self._get_active_goal(user_id, today=date.today())

    async def _get_active_goal(
        self, user_id: uuid.UUID, today: date
    ) -> Optional[DailyGoal]:
        result = await self.session.execute(
            select(DailyGoal)
            .where(DailyGoal.user_id == user_id, DailyGoal.effective_from <= today)
            .order_by(DailyGoal.effective_from.desc())
            .limit(1)
        )
        return result.scalars().first()
