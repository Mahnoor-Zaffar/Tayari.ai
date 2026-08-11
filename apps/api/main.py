from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from core.audit import auth_audit_middleware
from core.config import settings
from core.database import Base, async_session, engine
from core.errors import AppError, ErrorCode
from core.logging import get_logger, request_id
from core.secrets import validate_prod_settings
from core.security_headers import security_headers_middleware

log = get_logger("app")


# ── Lifespan ────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    from core.logging import setup_logging
    from workers.scheduler import scheduler

    setup_logging()

    if settings.SENTRY_DSN:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            release=f"tayari-api@{settings.VERSION}",
            traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
            profiles_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 0.0,
        )
        log.info("Sentry initialized for environment=%s", settings.ENVIRONMENT)

    validate_prod_settings()
    # Schema management is owned by Alembic. In production the schema must be
    # migrated explicitly (`alembic upgrade head`); create_all is a dev/test
    # convenience only, so it never silently diverges from the migration chain.
    if settings.is_development:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    scheduler.start()
    log.info("APScheduler started with PostgreSQL job store")

    from ai.usage.recorder import get_usage_recorder

    usage_recorder = get_usage_recorder()
    await usage_recorder.start_flush_loop()
    log.info("AI usage flush loop started")

    # Restore active sessions from DB (survives server restarts)
    try:
        from features.sessions.dependencies import get_session_manager
        from features.sessions.repository import SessionRepository

        manager = get_session_manager()
        async with async_session() as restore_db:
            repo = SessionRepository(restore_db)
            active = await repo.find_active_sessions()
            if active:
                count = manager.restore_sessions(active)
                log.info("Restored %d/%d active sessions from database", count, len(active))
    except Exception as exc:
        log.warning("Failed to restore active sessions: %s", exc)
    yield
    scheduler.shutdown(wait=False)
    log.info("APScheduler shut down")

    from ai.usage.recorder import get_usage_recorder

    await get_usage_recorder().stop()
    log.info("AI usage recorder stopped")

    await engine.dispose()


# ── App ─────────────────────────────────────────────────────────────────────


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    description="AI mock interview platform — live coding, system-design, and behavioral with AI evaluation.",
    terms_of_service="https://tayari.ai/terms",
    contact={"name": "Tayari AI", "email": "support@tayari.ai", "url": "https://tayari.ai"},
    license_info={"name": "MIT", "identifier": "MIT"},
    docs_url=None,
    redoc_url=None,
)

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

app.openapi_tags = [
    {"name": "auth", "description": "Registration, login, token refresh, email verification, password reset"},
    {"name": "interviews", "description": "Interview lifecycle: create, configure, upload resume/JD, validate"},
    {"name": "evaluations", "description": "Post-interview evaluation: trigger, list, retrieve scores and verdicts"},
    {"name": "health", "description": "Service health check endpoint"},
]


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
    try:
        import sentry_sdk

        sentry_sdk.capture_exception(exc)
    except ImportError:
        pass
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


from features.ai_usage.routes import router as ai_usage_router  # noqa: E402
from features.analytics.router import router as analytics_router  # noqa: E402
from features.auth.routes import router as auth_router  # noqa: E402
from features.code.routes import router as code_router  # noqa: E402
from features.dashboard.router import router as dashboard_router  # noqa: E402
from features.health.routes import router as health_router  # noqa: E402
from features.interview.routes import router as interview_router  # noqa: E402
from features.reports.routes import router as evaluations_router  # noqa: E402
from features.sessions.routes import router as sessions_router  # noqa: E402
from features.users.routes import router as users_router  # noqa: E402
from features.voice.routes import router as voice_router  # noqa: E402

app.include_router(analytics_router, prefix="/api/v1")
app.include_router(ai_usage_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(health_router, prefix="")
app.include_router(interview_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(code_router, prefix="/api/v1")
app.include_router(evaluations_router, prefix="/api/v1")

STATIC_ROOT = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


@app.get("/docs", include_in_schema=False)
async def swagger_docs():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{settings.PROJECT_NAME} - Swagger UI",
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.css",
    )


@app.get("/redirect", include_in_schema=False)
async def swagger_oauth2_redirect():
    return HTMLResponse("")


@app.get("/redoc", include_in_schema=False)
async def redoc_docs():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{settings.PROJECT_NAME} - ReDoc",
        redoc_js_url="/static/redoc/redoc.standalone.js",
    )


@app.get("/")
async def root(request: Request):
    if "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(
            f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{settings.PROJECT_NAME} API</title>
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 640px;
           margin: 80px auto; padding: 0 24px; color: #1f2937; }}
    h1 {{ font-size: 24px; }} a {{ color: #2563eb; }} .tag {{ color: #6b7280; font-size: 14px; }}
  </style>
</head>
<body>
  <h1>{settings.PROJECT_NAME}</h1>
  <p class="tag">API v{settings.VERSION} · running</p>
  <p>Interactive docs: <a href="/docs">/docs</a></p>
  <p>Health check: <a href="/health">/health</a></p>
  <p>API base: <code>/api/v1</code></p>
</body>
</html>""",
            status_code=200,
        )
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION}


@app.get("/api/v1")
async def api_v1_root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "ok",
        "docs": "/docs",
        "endpoints": [
            "/api/v1/auth",
            "/api/v1/interviews",
            "/api/v1/sessions",
            "/api/v1/evaluations",
            "/api/v1/code",
            "/api/v1/users",
            "/api/v1/dashboard",
            "/api/v1/admin/ai-usage",
            "/api/v1/analytics",
            "/api/v1/voice",
        ],
    }
