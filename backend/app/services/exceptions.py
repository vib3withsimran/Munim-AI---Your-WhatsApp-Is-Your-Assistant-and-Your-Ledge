from backend.app.repositories.exceptions import RepositoryError, NotFoundError


class BusinessRuleError(Exception):
    """Base exception for business logic rule violations."""
    def __init__(self, message: str, code: str = "BUSINESS_RULE_VIOLATION"):
        super().__init__(message)
        self.message = message
        self.code = code


class InsufficientStockError(BusinessRuleError):
    """Raised when sellable stock is less than the requested order quantity."""
    def __init__(self, message: str = "Insufficient sellable stock for requested item"):
        super().__init__(message, code="INSUFFICIENT_STOCK")


class InvalidOrderTransitionError(BusinessRuleError):
    """Raised when an order status transition violates the lifecycle state machine."""
    def __init__(self, from_status: str = "unknown", to_status: str = "unknown", message: str | None = None):
        msg = message or f"Invalid order status transition from '{from_status}' to '{to_status}'"
        super().__init__(msg, code="INVALID_ORDER_TRANSITION")
        self.from_status = from_status
        self.to_status = to_status


class InvalidPaymentTransitionError(BusinessRuleError):
    """Raised when a payment status transition violates the payment lifecycle."""
    def __init__(self, from_status: str, to_status: str):
        super().__init__(
            f"Invalid payment status transition from '{from_status}' to '{to_status}'",
            code="INVALID_PAYMENT_TRANSITION"
        )
        self.from_status = from_status
        self.to_status = to_status


class AmbiguousPaymentMatchError(BusinessRuleError):
    """Raised when an incoming payment matches multiple pending orders equally."""
    def __init__(self, message: str = "Multiple orders match payment amount; human review required"):
        super().__init__(message, code="AMBIGUOUS_PAYMENT_MATCH")


class CustomerPrivacyViolationError(BusinessRuleError):
    """Raised when an operation violates customer privacy restrictions."""
    def __init__(self, message: str = "Customer has privacy enabled; operations restricted"):
        super().__init__(message, code="CUSTOMER_PRIVACY_VIOLATION")

