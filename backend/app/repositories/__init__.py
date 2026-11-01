from backend.app.repositories.exceptions import (
    RepositoryError,
    NotFoundError,
    DuplicateRecordError,
    ForeignKeyViolationError,
    PermissionDeniedError,
    ConstraintViolationError,
    DatabaseConnectionError,
    map_supabase_error,
)
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.repositories.inventory_repository import InventoryRepository
from backend.app.repositories.order_repository import OrderRepository
from backend.app.repositories.payment_repository import PaymentRepository
from backend.app.repositories.media_repository import MediaRepository
from backend.app.repositories.webhook_repository import WebhookRepository
from backend.app.repositories.privacy_repository import PrivacyRepository

__all__ = [
    # Exceptions
    "RepositoryError",
    "NotFoundError",
    "DuplicateRecordError",
    "ForeignKeyViolationError",
    "PermissionDeniedError",
    "ConstraintViolationError",
    "DatabaseConnectionError",
    "map_supabase_error",
    # Repositories
    "CustomerRepository",
    "ProductRepository",
    "InventoryRepository",
    "OrderRepository",
    "PaymentRepository",
    "MediaRepository",
    "WebhookRepository",
    "PrivacyRepository",
]

