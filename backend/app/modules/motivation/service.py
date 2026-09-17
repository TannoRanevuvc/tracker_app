import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.bus import EventBus
from app.modules.motivation.models import Achievement, UserAchievement, UserProgress

logger = logging.getLogger(__name__)

XP_RULES: dict[str, int] = {
    "habit_completed": 10,
    "task_completed_high": 10,
    "task_completed_low": 5,
    "task_completed_medium": 5,
    "food_daily_goal_reached": 15,
}

STREAK_ACHIEVEMENT_MAP: dict[int, str] = {
    7: "streak_7",
    30: "streak_30",
    100: "streak_100",
}

XP_PER_LEVEL = 100


def calculate_level(xp_total: int) -> int:
    return xp_total // XP_PER_LEVEL + 1


def calculate_xp_to_next_level(xp_total: int) -> int:
    return XP_PER_LEVEL - (xp_total % XP_PER_LEVEL)


class MotivationService:
    def __init__(self, session: AsyncSession, bus: EventBus) -> None:
        self.session = session
        self.bus = bus

    async def get_or_create_progress(self, user_id: uuid.UUID) -> UserProgress:
        result = await self.session.execute(
            select(UserProgress).where(UserProgress.user_id == user_id)
        )
        progress = result.scalars().first()
        if progress is None:
            progress = UserProgress(
                user_id=user_id,
                xp_total=0,
                level=1,
                updated_at=datetime.now(UTC),
            )
            self.session.add(progress)
            await self.session.commit()
            await self.session.refresh(progress)
        return progress

    async def award_xp(
        self, user_id: uuid.UUID, amount: int, reason: str
    ) -> UserProgress:
        progress = await self.get_or_create_progress(user_id)
        old_level = progress.level
        progress.xp_total += amount
        progress.level = calculate_level(progress.xp_total)
        progress.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(progress)

        await self.bus.publish(
            "motivation.xp_awarded",
            {"user_id": str(user_id), "amount": amount, "reason": reason},
        )

        if progress.level > old_level:
            await self.bus.publish(
                "motivation.level_up",
                {"user_id": str(user_id), "new_level": progress.level},
            )

        return progress

    async def unlock_achievement(
        self, user_id: uuid.UUID, code: str
    ) -> bool:
        result = await self.session.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_code == code,
            )
        )
        if result.scalars().first() is not None:
            return False

        ua = UserAchievement(
            user_id=user_id,
            achievement_code=code,
            unlocked_at=datetime.now(UTC),
        )
        self.session.add(ua)
        await self.session.commit()

        await self.bus.publish(
            "motivation.achievement_unlocked",
            {"user_id": str(user_id), "achievement_code": code},
        )
        return True

    async def get_user_achievements(
        self, user_id: uuid.UUID
    ) -> list[UserAchievement]:
        result = await self.session.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_summary(self, user_id: uuid.UUID) -> dict:
        progress = await self.get_or_create_progress(user_id)

        recent_result = await self.session.execute(
            select(UserAchievement, Achievement)
            .join(
                Achievement,
                UserAchievement.achievement_code == Achievement.code,
            )
            .where(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.unlocked_at.desc())
            .limit(5)
        )
        recent = [
            {
                "code": ach.code,
                "name": ach.name,
                "unlocked_at": ua.unlocked_at,
            }
            for ua, ach in recent_result.all()
        ]

        return {
            "xp_total": progress.xp_total,
            "level": progress.level,
            "xp_to_next_level": calculate_xp_to_next_level(progress.xp_total),
            "recent_achievements": recent,
        }

    async def get_achievements(self, user_id: uuid.UUID) -> list[dict]:
        all_result = await self.session.execute(select(Achievement))
        all_achievements = list(all_result.scalars().all())

        unlocked_result = await self.session.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
        unlocked_map = {
            ua.achievement_code: ua for ua in unlocked_result.scalars().all()
        }

        result = []
        for ach in all_achievements:
            ua = unlocked_map.get(ach.code)
            result.append({
                "code": ach.code,
                "name": ach.name,
                "description": ach.description,
                "unlocked": ua is not None,
                "unlocked_at": ua.unlocked_at if ua else None,
            })
        return result

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def on_habit_completed(self, payload: dict) -> None:
        try:
            user_id = uuid.UUID(payload["user_id"])
            await self.award_xp(user_id, XP_RULES["habit_completed"], "habit_completed")
            streak = int(payload.get("current_streak", 0))
            if streak in STREAK_ACHIEVEMENT_MAP:
                await self.unlock_achievement(user_id, STREAK_ACHIEVEMENT_MAP[streak])
        except Exception:
            logger.exception("motivation.on_habit_completed error")

    async def on_streak_broken(self, payload: dict) -> None:
        pass

    async def on_task_completed(self, payload: dict) -> None:
        try:
            user_id = uuid.UUID(payload["user_id"])
            priority = payload.get("priority", "medium")
            reason = f"task_completed_{priority}"
            amount = XP_RULES.get(reason, XP_RULES["task_completed_medium"])
            await self.award_xp(user_id, amount, reason)
        except Exception:
            logger.exception("motivation.on_task_completed error")

    async def on_food_daily_goal_reached(self, payload: dict) -> None:
        try:
            user_id = uuid.UUID(payload["user_id"])
            await self.award_xp(
                user_id, XP_RULES["food_daily_goal_reached"], "food_daily_goal_reached"
            )
        except Exception:
            logger.exception("motivation.on_food_daily_goal_reached error")

    async def on_budget_exceeded(self, payload: dict) -> None:
        pass
