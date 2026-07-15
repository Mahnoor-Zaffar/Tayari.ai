from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from core.audit import auth_audit_middleware
from core.config import settings
from core.database import Base, engine
from core.errors import AppError, ErrorCode
from core.logging import get_logger, request_id
from core.secrets import validate_prod_settings
from core.security_headers import security_headers_middleware

log = get_logger("app")


# ── Lifespan ────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    from core.logging import setup_logging

    setup_logging()
    validate_prod_settings()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


# ── App ─────────────────────────────────────────────────────────────────────


app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


# ── Middleware order: outermost runs first (i.e. last to wrap) ──────────────

#  1. Security headers (outermost — sets headers on every response)
app.middleware("http")(security_headers_middleware)


#  2. Request‑ID
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    rid = str(uuid4())
    request_id.set(rid)
    response = await call_next(request)
    return response


#  3. Auth audit (innermost — runs after request_id is set)
app.middleware("http")(auth_audit_middleware)


# ── OpenAPI security scheme ─────────────────────────────────────────────────


def _custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste your access token (no 'Bearer ' prefix needed)",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = _custom_openapi  # type: ignore[method-assign]


# ── Exception handlers ──────────────────────────────────────────────────────


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    detail = exc.detail
    rid = request_id.get()
    if rid and isinstance(detail, dict):
        detail["request_id"] = rid
    return JSONResponse(status_code=exc.status_code, content=detail)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    rid = request_id.get()
    raw_errors = exc.errors()
    log.warning("request validation failed", extra={"request_id": rid, "errors": raw_errors})
    details = []
    for err in raw_errors:
        clean = {k: v for k, v in err.items() if k != "ctx"}
        if "ctx" in err and isinstance(err["ctx"], dict):
            clean["ctx"] = {k: str(v) for k, v in err["ctx"].items()}
        details.append(clean)
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "Request validation failed",
                "details": details,
            },
            "request_id": rid,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard FastAPI HTTPExceptions that aren't AppErrors (e.g. 405)."""
    rid = request_id.get()
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": exc.detail if isinstance(exc.detail, str) else "HTTP error",
            },
            "request_id": rid,
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    rid = request_id.get()
    log.warning("database integrity error", extra={"request_id": rid})
    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.CONFLICT,
                "message": "Resource conflict",
            },
            "request_id": rid,
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    rid = request_id.get()
    log.error("database error", exc_info=exc, extra={"request_id": rid})
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.DATABASE_ERROR,
                "message": "A database error occurred",
            },
            "request_id": rid,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    rid = request_id.get()
    log.exception("unhandled exception", extra={"request_id": rid})
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "An internal error occurred",
            },
            "request_id": rid,
        },
    )


# ── Route imports (late to avoid circular imports) ─────────────────────────


from features.analytics.router import router as analytics_router  # noqa: E402
from features.auth.routes import router as auth_router  # noqa: E402
from features.billing.routes import router as billing_router  # noqa: E402
from features.dashboard.router import router as dashboard_router  # noqa: E402
from features.health.routes import router as health_router  # noqa: E402
from features.interview.routes import router as interview_router  # noqa: E402
from features.reports.routes import router as reports_router  # noqa: E402
from features.users.routes import router as users_router  # noqa: E402
from features.voice.routes import router as voice_router  # noqa: E402
from features.sessions.routes import router as sessions_router  # noqa: E402
from features.code.routes import router as code_router  # noqa: E402

app.include_router(analytics_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(health_router, prefix="")
app.include_router(interview_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(code_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION}
