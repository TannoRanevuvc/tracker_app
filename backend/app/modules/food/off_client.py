"""
Клиент Open Food Facts API.

Публичные функции:
  parse_off_product(raw)  — чистый парсер одного OFF-продукта (unit-тестируем)
  search_products(q)      — поиск по названию/штрихкоду, возвращает список уже распарсенных dict
  get_product(external_id)— получение конкретного продукта, возвращает dict или None

Обе async-функции могут поднять httpx.TimeoutException при недоступности сервиса.
Вызывающий код (router) отвечает за преобразование этого в 502.
"""
import httpx

_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
_PRODUCT_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
_TIMEOUT = 5.0


def parse_off_product(raw: dict) -> dict:
    """Parse raw OFF product dict → ExternalProductPreview-compatible dict (no `id`)."""
    nutriments = raw.get("nutriments", {})
    return {
        "external_id": str(raw.get("code") or raw.get("_id") or ""),
        "name": raw.get("product_name") or raw.get("product_name_en") or "",
        "kcal_per_100g": float(nutriments.get("energy-kcal_100g") or 0.0),
        "protein_g_per_100g": float(nutriments.get("proteins_100g") or 0.0),
        "fat_g_per_100g": float(nutriments.get("fat_100g") or 0.0),
        "carbs_g_per_100g": float(nutriments.get("carbohydrates_100g") or 0.0),
    }


async def search_products(q: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(
            _SEARCH_URL,
            params={"search_terms": q, "json": "1", "page_size": "20"},
        )
        data = resp.json()
    return [parse_off_product(p) for p in data.get("products", []) if p.get("code")]


async def get_product(external_id: str) -> dict | None:
    url = _PRODUCT_URL.format(barcode=external_id)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(url)
        data = resp.json()
    if data.get("status") != 1:
        return None
    product = dict(data.get("product", {}))
    product.setdefault("code", external_id)
    return parse_off_product(product)
