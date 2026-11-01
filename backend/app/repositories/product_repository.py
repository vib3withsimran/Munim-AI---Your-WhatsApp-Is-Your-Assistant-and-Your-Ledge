import logging
from typing import List, Optional, Union
from uuid import UUID
from supabase import Client

from backend.app.models.product import Product, ProductVariant
from backend.app.schemas.product import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductVariantCreateRequest,
    ProductVariantUpdateRequest,
)
from backend.app.repositories.exceptions import (
    NotFoundError,
    ForeignKeyViolationError,
    PermissionDeniedError,
    map_supabase_error,
)

logger = logging.getLogger(__name__)


class ProductRepository:
    """Data-access repository for 'products' and 'product_variants' tables."""

    def __init__(self, db: Client):
        self.db = db

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    # =========================================================================
    # Product Operations
    # =========================================================================

    def create_product(
        self,
        seller_id: Union[str, UUID],
        data: ProductCreateRequest
    ) -> Product:
        """Creates a new product record owned by seller_id."""
        sid = self._normalize_id(seller_id)
        payload = {
            "seller_id": sid,
            "name": data.name,
            "description": data.description,
            "category": data.category,
            "image_path": data.image_path,
            "is_active": data.is_active,
        }

        try:
            res = (
                self.db.table("products")
                .insert(payload)
                .execute()
            )
            if not res.data:
                raise RuntimeError("Failed to insert product record")
            row = res.data[0] if isinstance(res.data, list) else res.data
            return Product.model_validate(row)
        except Exception as e:
            raise map_supabase_error(e, entity="Product")

    def get_product_by_id(
        self,
        seller_id: Union[str, UUID],
        product_id: Union[str, UUID]
    ) -> Optional[Product]:
        """Fetches a single product by ID, strictly scoped to seller_id."""
        sid = self._normalize_id(seller_id)
        pid = self._normalize_id(product_id)

        try:
            res = (
                self.db.table("products")
                .select("*")
                .eq("seller_id", sid)
                .eq("id", pid)
                .maybe_single()
                .execute()
            )
            if not res or not res.data:
                return None
            row = res.data[0] if isinstance(res.data, list) and res.data else res.data
            if not row or not isinstance(row, dict):
                return None
            return Product.model_validate(row)
        except Exception as e:
            raise map_supabase_error(e, entity="Product")

    def list_products(
        self,
        seller_id: Union[str, UUID],
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Product]:
        """Lists products owned by the seller with optional is_active filter and pagination."""
        sid = self._normalize_id(seller_id)
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)

        try:
            query = (
                self.db.table("products")
                .select("*")
                .eq("seller_id", sid)
            )
            if is_active is not None:
                query = query.eq("is_active", is_active)

            res = (
                query
                .order("created_at", desc=True)
                .range(safe_offset, safe_offset + safe_limit - 1)
                .execute()
            )
            rows = res.data or []
            return [Product.model_validate(r) for r in rows]
        except Exception as e:
            raise map_supabase_error(e, entity="Product")

    def update_product(
        self,
        seller_id: Union[str, UUID],
        product_id: Union[str, UUID],
        data: ProductUpdateRequest
    ) -> Optional[Product]:
        """Updates product fields belonging to seller_id."""
        sid = self._normalize_id(seller_id)
        pid = self._normalize_id(product_id)

        update_dict = {}
        if data.name is not None:
            update_dict["name"] = data.name
        if data.description is not None:
            update_dict["description"] = data.description
        if data.category is not None:
            update_dict["category"] = data.category
        if data.image_path is not None:
            update_dict["image_path"] = data.image_path
        if data.is_active is not None:
            update_dict["is_active"] = data.is_active

        if not update_dict:
            return self.get_product_by_id(seller_id=sid, product_id=pid)

        try:
            res = (
                self.db.table("products")
                .update(update_dict)
                .eq("seller_id", sid)
                .eq("id", pid)
                .execute()
            )
            if not res.data:
                return None
            row = res.data[0] if isinstance(res.data, list) else res.data
            return Product.model_validate(row)
        except Exception as e:
            raise map_supabase_error(e, entity="Product")

    def archive_product(
        self,
        seller_id: Union[str, UUID],
        product_id: Union[str, UUID]
    ) -> bool:
        """Soft-deletes a product by setting is_active = False."""
        sid = self._normalize_id(seller_id)
        pid = self._normalize_id(product_id)

        try:
            res = (
                self.db.table("products")
                .update({"is_active": False})
                .eq("seller_id", sid)
                .eq("id", pid)
                .execute()
            )
            return bool(res.data)
        except Exception as e:
            raise map_supabase_error(e, entity="Product")

    # =========================================================================
    # ProductVariant Operations
    # =========================================================================

    def create_variant(
        self,
        seller_id: Union[str, UUID],
        data: ProductVariantCreateRequest
    ) -> ProductVariant:
        """
        Creates a new variant for a product.
        Verifies that the parent product belongs to the same seller.
        """
        sid = self._normalize_id(seller_id)
        pid = self._normalize_id(data.product_id)

        # Cross-seller / parent ownership verification
        parent_product = self.get_product_by_id(seller_id=sid, product_id=pid)
        if not parent_product:
            raise ForeignKeyViolationError(f"Product '{pid}' does not exist or is not owned by this seller.")

        payload = {
            "seller_id": sid,
            "product_id": pid,
            "sku": data.sku,
            "size": data.size,
            "color": data.color,
            "price": float(data.price),
        }

        try:
            res = (
                self.db.table("product_variants")
                .insert(payload)
                .execute()
            )
            if not res.data:
                raise RuntimeError("Failed to insert product variant")
            row = res.data[0] if isinstance(res.data, list) else res.data
            return ProductVariant.model_validate(row)
        except Exception as e:
            if isinstance(e, ForeignKeyViolationError):
                raise
            raise map_supabase_error(e, entity="ProductVariant")

    def get_variant_by_id(
        self,
        seller_id: Union[str, UUID],
        variant_id: Union[str, UUID]
    ) -> Optional[ProductVariant]:
        """Fetches a single product variant by ID, strictly scoped to seller_id."""
        sid = self._normalize_id(seller_id)
        vid = self._normalize_id(variant_id)

        try:
            res = (
                self.db.table("product_variants")
                .select("*")
                .eq("seller_id", sid)
                .eq("id", vid)
                .maybe_single()
                .execute()
            )
            if not res or not res.data:
                return None
            row = res.data[0] if isinstance(res.data, list) and res.data else res.data
            if not row or not isinstance(row, dict):
                return None
            return ProductVariant.model_validate(row)
        except Exception as e:
            raise map_supabase_error(e, entity="ProductVariant")

    def list_variants_by_product(
        self,
        seller_id: Union[str, UUID],
        product_id: Union[str, UUID]
    ) -> List[ProductVariant]:
        """Lists all variants belonging to a specific product owned by the seller."""
        sid = self._normalize_id(seller_id)
        pid = self._normalize_id(product_id)

        try:
            res = (
                self.db.table("product_variants")
                .select("*")
                .eq("seller_id", sid)
                .eq("product_id", pid)
                .order("created_at")
                .execute()
            )
            rows = res.data or []
            return [ProductVariant.model_validate(r) for r in rows]
        except Exception as e:
            raise map_supabase_error(e, entity="ProductVariant")

    def update_variant(
        self,
        seller_id: Union[str, UUID],
        variant_id: Union[str, UUID],
        data: ProductVariantUpdateRequest
    ) -> Optional[ProductVariant]:
        """Updates variant fields belonging to seller_id."""
        sid = self._normalize_id(seller_id)
        vid = self._normalize_id(variant_id)

        update_dict = {}
        if data.sku is not None:
            update_dict["sku"] = data.sku
        if data.size is not None:
            update_dict["size"] = data.size
        if data.color is not None:
            update_dict["color"] = data.color
        if data.price is not None:
            update_dict["price"] = float(data.price)

        if not update_dict:
            return self.get_variant_by_id(seller_id=sid, variant_id=vid)

        try:
            res = (
                self.db.table("product_variants")
                .update(update_dict)
                .eq("seller_id", sid)
                .eq("id", vid)
                .execute()
            )
            if not res.data:
                return None
            row = res.data[0] if isinstance(res.data, list) else res.data
            return ProductVariant.model_validate(row)
        except Exception as e:
            raise map_supabase_error(e, entity="ProductVariant")
