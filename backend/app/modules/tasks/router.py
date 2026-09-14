from fastapi import APIRouter

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/")
async def list_tasks():
    pass


@router.post("/")
async def create_task():
    pass


@router.patch("/{task_id}")
async def update_task(task_id: int):
    pass


@router.delete("/{task_id}")
async def delete_task(task_id: int):
    pass


@router.post("/{task_id}/complete")
async def complete_task(task_id: int):
    pass
