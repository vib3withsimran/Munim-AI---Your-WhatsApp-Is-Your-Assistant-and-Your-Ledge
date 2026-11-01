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
    ProductWithVariantsResponse,
    ProductVariantResponse,
)
from backend.app.repositories.product_repository import ProductRepository
from backend.app.repositories.exceptions import NotFoundError, ForeignKeyViolationError

logger = logging.getLogger(__name__)


class ProductService:
    """Business logic service for catalog, products, and variant management."""

    def __init__(self, db: Client):
        self.db = db
        self.product_repo = ProductRepository(db)

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    def create_product(
        self,
        seller_id: Union[str, UUID],
        data: ProductCreateRequest
    ) -> Product:
        """Creates a new catalog product owned by the seller."""
        sid = self._normalize_id(seller_id)
        return self.product_repo.create_product(seller_id=sid, data=data)

    def get_product(
        self,
        seller_id: Union[str, UUID],
        product_id: Union[str, UUID]
    ) -> Optional[Product]:
        """Fetches product by ID with strict seller ownership verification."""
        sid = self._normalize_id(seller_id)
        pid = self._normalize_id(product_id)
        return self.product_repo.get_product_by_id(seller_id=sid, product_id=pid)

    def list_products(
        self,
        seller_id: Union[str, UUID],
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Product]:
        """Lists products owned by seller with optional active filter."""
        sid = self._normalize_id(seller_id)
        return self.product_repo.list_products(seller_id=sid, is_active=is_active, limit=limit, offset=offset)

    def update_product(
        self,
        seller_id: Union[str, UUID],
        product_id: Union[str, UUID],
        data: ProductUpdateRequest
    ) -> Product:
        """Updates product details after verifying seller ownership."""
        sid = self._normalize_id(seller_id)
        pid = self._normalize_id(product_id)

        existing = self.get_product(seller_id=sid, product_id=pid)
        if not existing:
            raise NotFoundError(f"Product '{pid}' not found or not owned by this seller.")

        updated = self.product_repo.update_product(seller_id=sid, product_id=pid, data=data)
        if not updated:
            raise NotFoundError(f"Product '{pid}' update failed.")
        return updated

    def archive_product(
        self,
        seller_id: Union[str, UUID],
        product_id: Union[str, UUID]
    ) -> bool:
        """
        Soft-deletes a product by setting is_active = False.
        Preserves product records referenced by historical order items.
        """
        sid = self._normalize_id(seller_id)
        pid = self._normalize_id(product_id)

        existing = self.get_product(seller_id=sid, product_id=pid)
        if not existing:
            raise NotFoundError(f"Product '{pid}' not found or not owned by this seller.")

        return self.product_repo.archive_product(seller_id=sid, product_id=pid)

    def create_variant(
        self,
        seller_id: Union[str, UUID],
        data: ProductVariantCreateRequest
    ) -> ProductVariant:
        """
        Creates a variant under an active parent product owned by the seller.
        Rejects creation under archived products or foreign seller products.
        """
        sid = self._normalize_id(seller_id)
        pid = self._normalize_id(data.product_id)

        parent = self.get_product(seller_id=sid, product_id=pid)
        if not parent:
            raise NotFoundError(f"Parent product '{pid}' not found or not owned by this seller.")
        if not parent.is_active:
            raise ForeignKeyViolationError(f"Cannot add variant to archived product '{pid}'.")

        return self.product_repo.create_variant(seller_id=sid, data=data)

    def update_variant(
        self,
        seller_id: Union[str, UUID],
        variant_id: Union[str, UUID],
        data: ProductVariantUpdateRequest
    ) -> ProductVariant:
        """Updates variant details after verifying seller ownership."""
        sid = self._normalize_id(seller_id)
        vid = self._normalize_id(variant_id)

        existing = self.product_repo.get_variant_by_id(seller_id=sid, variant_id=vid)
        if not existing:
            raise NotFoundError(f"Variant '{vid}' not found or not owned by this seller.")

        updated = self.product_repo.update_variant(seller_id=sid, variant_id=vid, data=data)
        if not updated:
            raise NotFoundError(f"Variant '{vid}' update failed.")
        return updated

    def get_product_catalog(
        self,
        seller_id: Union[str, UUID]
    ) -> List[ProductWithVariantsResponse]:
        """
        Retrieves active product catalog with embedded variants.
        Excludes archived products. Authoritative prices come strictly from product_variants.
        """
        sid = self._normalize_id(seller_id)
        active_products = self.list_products(seller_id=sid, is_active=True, limit=100)

        catalog: List[ProductWithVariantsResponse] = []
        for p in active_products:
            variants = self.product_repo.list_variants_by_product(seller_id=sid, product_id=p.id)
            variant_responses = [ProductVariantResponse.model_validate(v) for v in variants]
            catalog.append(
                ProductWithVariantsResponse(
                    id=p.id,
                    seller_id=p.seller_id,
                    name=p.name,
                    description=p.description,
                    category=p.category,
                    image_path=p.image_path,
                    is_active=p.is_active,
                    created_at=p.created_at,
                    variants=variant_responses
                )
            )
        return catalog

