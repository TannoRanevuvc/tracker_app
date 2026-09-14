from fastapi import APIRouter

router = APIRouter(prefix="/api/habits", tags=["habits"])


@router.get("/")
async def list_habits():
    pass


@router.post("/")
async def create_habit():
    pass


@router.patch("/{habit_id}")
async def update_habit(habit_id: int):
    pass


@router.delete("/{habit_id}")
async def delete_habit(habit_id: int):
    pass


@router.post("/{habit_id}/check")
async def check_habit(habit_id: int):
    pass
