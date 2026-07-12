from fastapi import HTTPException


class ErrorCode:
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AI_ERROR = "AI_ERROR"
    STRIPE_ERROR = "STRIPE_ERROR"
    INSUFFICIENT_CREDITS = "INSUFFICIENT_CREDITS"


class AppError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400, detail: dict | None = None):
        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "error": {
                    "code": code,
                    "message": message,
                    **(detail or {}),
                },
            },
        )


def not_found(resource: str = "Resource") -> AppError:
    return AppError(ErrorCode.NOT_FOUND, f"{resource} not found", 404)


def unauthorized(msg: str = "Invalid credentials") -> AppError:
    return AppError(ErrorCode.UNAUTHORIZED, msg, 401)


def success_response(data: dict) -> dict:
    return {"success": True, "data": data}
