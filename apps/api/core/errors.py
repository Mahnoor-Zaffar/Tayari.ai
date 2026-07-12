from fastapi import HTTPException

# ── Error codes ─────────────────────────────────────────────────────────────

class ErrorCode:
    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    # Authentication
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    UNAUTHORIZED = "UNAUTHORIZED"
    # Authorization
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_CREDITS = "INSUFFICIENT_CREDITS"
    # Resource
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    # Rate limiting
    RATE_LIMITED = "RATE_LIMITED"
    # Database
    DATABASE_ERROR = "DATABASE_ERROR"
    # External services
    AI_ERROR = "AI_ERROR"
    STRIPE_ERROR = "STRIPE_ERROR"
    # Catch-all
    INTERNAL_ERROR = "INTERNAL_ERROR"


# ── Base app exception ──────────────────────────────────────────────────────


class AppError(HTTPException):
    """Base for all application-level HTTP errors.

    Every error serialises to the standard shape::

        {
            "success": false,
            "error": {
                "code": "<ErrorCode>",
                "message": "<human-readable>",
                "details": [...]   // optional
            },
            "request_id": "<uuid>"  // set by middleware
        }
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        *,
        details: list | None = None,
        request_id: str = "",
    ) -> None:
        error: dict = {"code": code, "message": message}
        if details:
            error["details"] = details
        payload: dict = {"success": False, "error": error}
        if request_id:
            payload["request_id"] = request_id
        super().__init__(status_code=status_code, detail=payload)


# ── Specific exception classes ──────────────────────────────────────────────


class ValidationError(AppError):
    def __init__(self, message: str = "Request validation failed", *, details: list | None = None) -> None:
        super().__init__(ErrorCode.VALIDATION_ERROR, message, 422, details=details)


class AuthenticationError(AppError):
    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(ErrorCode.UNAUTHORIZED, message, 401)


class TokenError(AppError):
    """Token is invalid, expired, or revoked — distinct from generic
    ``AuthenticationError`` so clients can differentiate "no credentials"
    from "credentials exist but are bad"."""

    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(ErrorCode.INVALID_TOKEN, message, 401)


class AuthorizationError(AppError):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(ErrorCode.FORBIDDEN, message, 403)


class NotFoundError(AppError):
    def __init__(self, message: str = "") -> None:
        super().__init__(ErrorCode.NOT_FOUND, message or "Resource not found", 404)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(ErrorCode.CONFLICT, message, 409)


class RateLimitedError(AppError):
    def __init__(self, message: str = "Too many requests") -> None:
        super().__init__(ErrorCode.RATE_LIMITED, message, 429)


class DatabaseError(AppError):
    def __init__(self, message: str = "A database error occurred") -> None:
        super().__init__(ErrorCode.DATABASE_ERROR, message, 500)


class InternalError(AppError):
    def __init__(self, message: str = "An internal error occurred") -> None:
        super().__init__(ErrorCode.INTERNAL_ERROR, message, 500)


# ── Helpers ─────────────────────────────────────────────────────────────────


def success_response(data: dict) -> dict:
    return {"success": True, "data": data}
