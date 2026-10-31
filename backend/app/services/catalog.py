import time
import logging
from typing import List, Dict, Any, Optional

from backend.app.core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# In-memory TTL cache for store catalogs (seller_id -> {"timestamp": float, "products": list})
_CATALOG_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

DEFAULT_STORE_CATALOG = [
    {
        "id": "prod-1",
        "name": "Cotton Anarkali Kurti",
        "price": 1299.0,
        "stock": 15,
        "description": "Sizes: M, L, XL, XXL | Colors: Red, Blue, Pink",
        "is_active": True
    },
    {
        "id": "prod-2",
        "name": "Straight Fit Blue Kurti",
        "price": 799.0,
        "stock": 25,
        "description": "Sizes: S, M, L, XL | Color: Indigo Blue",
        "is_active": True
    },
    {
        "id": "prod-3",
        "name": "Embroidered Silk Kurti",
        "price": 1899.0,
        "stock": 8,
        "description": "Sizes: M, L | Colors: Maroon, Mustard",
        "is_active": True
    },
    {
        "id": "prod-4",
        "name": "Casual Black Kurti",
        "price": 649.0,
        "stock": 30,
        "description": "Sizes: S, M, L, XL, XXL | Color: Jet Black",
        "is_active": True
    }
]

async def get_active_catalog(seller_id: str = "default_seller", force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Retrieves active products from Supabase with an in-memory TTL cache.
    Prevents repeated network queries and drops latency to < 1ms on cache hits.
    """
    now = time.time()
    cached = _CATALOG_CACHE.get(seller_id)
    if not force_refresh and cached and (now - cached["timestamp"] < CACHE_TTL_SECONDS):
        return cached["products"]

    try:
        supabase = get_supabase_client()
        res = (
            supabase.table("products")
            .select("*")
            .eq("seller_id", seller_id)
            .eq("is_active", True)
            .execute()
        )
        products = res.data or []
        if not products:
            # If no products in DB yet, fallback to default catalog
            products = DEFAULT_STORE_CATALOG
    except Exception as e:
        logger.warning(f"Could not fetch catalog from Supabase ({e}), using default catalog cache.")
        products = DEFAULT_STORE_CATALOG

    _CATALOG_CACHE[seller_id] = {
        "timestamp": now,
        "products": products
    }
    return products


async def search(seller_id: str = "default_seller", query: str = "", entities: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Searches product catalog by keyword, size, or color.
    """
    catalog = await get_active_catalog(seller_id)
    if not query and not entities:
        return catalog

    search_term = query.lower().strip() if query else ""
    if entities and "name" in entities:
        search_term = str(entities["name"]).lower().strip()

    matches = []
    for p in catalog:
        name_lower = p["name"].lower()
        desc_lower = p.get("description", "").lower()
        if search_term and (search_term in name_lower or any(word in name_lower for word in search_term.split())):
            matches.append(p)
        elif search_term and search_term in desc_lower:
            matches.append(p)

    return matches if matches else catalog


async def find_variant(
    seller_id: str = "default_seller",
    item_name: str = "",
    size: Optional[str] = None,
    color: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Finds a specific product variant and returns product details including available stock.
    """
    catalog = await get_active_catalog(seller_id)
    name_clean = item_name.lower().strip()

    # Exact or substring match on product name
    matched_product = None
    for p in catalog:
        p_name = p["name"].lower()
        if name_clean and (name_clean in p_name or p_name in name_clean):
            matched_product = dict(p)
            break
        # Match single keywords like "anarkali", "blue kurti", "silk"
        keywords = [k for k in name_clean.split() if len(k) > 2]
        if any(k in p_name for k in keywords):
            matched_product = dict(p)
            break

    if not matched_product and catalog:
        # Fallback to first product if query was vague
        matched_product = dict(catalog[0])

    if matched_product:
        matched_product["requested_size"] = size
        matched_product["requested_color"] = color

    return matched_product
