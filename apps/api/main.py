from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import engine, Base
from core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from features.auth.routes import router as auth_router
from features.interview.routes import router as interview_router
from features.reports.routes import router as reports_router
from features.billing.routes import router as billing_router
from features.users.routes import router as users_router
from features.voice.routes import router as voice_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(interview_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION}
