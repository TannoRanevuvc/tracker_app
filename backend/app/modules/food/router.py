from fastapi import APIRouter

router = APIRouter(prefix="/api/food", tags=["food"])


@router.get("/products")
async def list_products():
    pass


@router.post("/products")
async def create_product():
    pass


@router.get("/products/search")
async def search_products(q: str):
    pass


@router.get("/meals")
async def list_meals():
    pass


@router.post("/meals")
async def log_meal():
    pass


@router.delete("/meals/{meal_id}")
async def delete_meal(meal_id: int):
    pass


@router.get("/daily")
async def daily_summary():
    pass
