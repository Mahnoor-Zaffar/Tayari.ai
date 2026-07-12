"""Health-check and readiness-probe endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict:
    """Readiness probe — confirms DB connectivity and returns dependency status."""
    deps: dict[str, str] = {}
    healthy = True

    # Database
    try:
        await db.execute(text("SELECT 1"))
        deps["database"] = "ok"
    except Exception:
        deps["database"] = "unreachable"
        healthy = False

    return {"status": "ok" if healthy else "degraded", "dependencies": deps}
