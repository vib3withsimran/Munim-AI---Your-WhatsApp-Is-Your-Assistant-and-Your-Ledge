class RepositoryError(Exception):
    """Base exception for all repository data-access failures."""
    def __init__(self, message: str, details: str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(RepositoryError):
    """Raised when a requested database record is not found."""
    pass


class DuplicateRecordError(RepositoryError):
    """Raised when an insert/update violates a unique constraint (e.g. duplicate customer phone)."""
    pass


class ForeignKeyViolationError(RepositoryError):
    """Raised when an operation references a non-existent foreign key (e.g. invalid product_id)."""
    pass


class PermissionDeniedError(RepositoryError):
    """Raised when RLS or permission check prevents the operation."""
    pass


class ConstraintViolationError(RepositoryError):
    """Raised when a database check constraint or NOT NULL constraint is violated."""
    pass


class DatabaseConnectionError(RepositoryError):
    """Raised when communication with Supabase fails or times out."""
    pass


def map_supabase_error(e: Exception, entity: str = "Record") -> RepositoryError:
    """Translates raw Supabase/PostgREST exceptions into typed repository exceptions."""
    err_msg = str(e)
    code = getattr(e, "code", None)
    if not code and hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
        code = e.args[0].get("code")

    if code == "42501" or "violates row-level security policy" in err_msg:
        return PermissionDeniedError(f"Access denied for {entity}: RLS policy violation", details=err_msg)
    if code == "23505" or "duplicate key" in err_msg or "already exists" in err_msg:
        return DuplicateRecordError(f"A duplicate {entity} already exists", details=err_msg)
    if code == "23503" or "foreign key constraint" in err_msg:
        return ForeignKeyViolationError(f"Referenced foreign key for {entity} does not exist", details=err_msg)
    if code == "23502" or "null value in column" in err_msg or "violates not-null constraint" in err_msg:
        return ConstraintViolationError(f"Required field constraint violated for {entity}", details=err_msg)
    if "Connection" in err_msg or "timeout" in err_msg.lower() or "network" in err_msg.lower():
        return DatabaseConnectionError(f"Database connection failure while operating on {entity}", details=err_msg)

    return RepositoryError(f"Unexpected database error on {entity}: {err_msg}", details=err_msg)

