import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.app.repositories.exceptions import (
    NotFoundError,
    DuplicateRecordError,
    PermissionDeniedError,
    ForeignKeyViolationError,
    ConstraintViolationError,
    RepositoryError,
)
from backend.app.services.exceptions import (
    BusinessRuleError,
    InsufficientStockError,
    InvalidOrderTransitionError,
    InvalidPaymentTransitionError,
    AmbiguousPaymentMatchError,
    CustomerPrivacyViolationError,
)
from backend.app.utils.file_validation import FileValidationError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Registers global exception handlers to map typed repository and service errors to HTTP responses."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": exc.message or str(exc)},
        )

    @app.exception_handler(DuplicateRecordError)
    async def duplicate_record_handler(request: Request, exc: DuplicateRecordError):
        return JSONResponse(
            status_code=409,
            content={"detail": exc.message or str(exc)},
        )

    @app.exception_handler(PermissionDeniedError)
    async def permission_denied_handler(request: Request, exc: PermissionDeniedError):
        return JSONResponse(
            status_code=403,
            content={"detail": exc.message or str(exc)},
        )

    @app.exception_handler(CustomerPrivacyViolationError)
    async def privacy_violation_handler(request: Request, exc: CustomerPrivacyViolationError):
        return JSONResponse(
            status_code=403,
            content={"detail": exc.message or str(exc)},
        )

    @app.exception_handler(InsufficientStockError)
    async def insufficient_stock_handler(request: Request, exc: InsufficientStockError):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message or str(exc)},
        )

    @app.exception_handler(InvalidOrderTransitionError)
    async def invalid_order_transition_handler(request: Request, exc: InvalidOrderTransitionError):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message or str(exc)},
        )

    @app.exception_handler(InvalidPaymentTransitionError)
    async def invalid_payment_transition_handler(request: Request, exc: InvalidPaymentTransitionError):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message or str(exc)},
        )

    @app.exception_handler(AmbiguousPaymentMatchError)
    async def ambiguous_payment_handler(request: Request, exc: AmbiguousPaymentMatchError):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message or str(exc)},
        )

    @app.exception_handler(ForeignKeyViolationError)
    async def foreign_key_handler(request: Request, exc: ForeignKeyViolationError):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message or str(exc)},
        )

    @app.exception_handler(ConstraintViolationError)
    async def constraint_violation_handler(request: Request, exc: ConstraintViolationError):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message or str(exc)},
        )

    @app.exception_handler(BusinessRuleError)
    async def business_rule_handler(request: Request, exc: BusinessRuleError):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message or str(exc)},
        )

    @app.exception_handler(FileValidationError)
    async def file_validation_handler(request: Request, exc: FileValidationError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(RepositoryError)
    async def repository_error_handler(request: Request, exc: RepositoryError):
        logger.error(f"Repository exception on {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Database operation failed."},
        )

