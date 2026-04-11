from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.core.responses import success_response, error_response
from src.database import get_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> JSONResponse:
    """Liveness + DB connectivity probe. No auth required."""
    try:
        db = get_client()
        await db.execute_raw("SELECT 1")
        db_status = "connected"
    except Exception:
        return error_response(
            error="Database unreachable",
            code="DB_ERROR",
            status_code=503,
        )

    return success_response(data={"status": "ok", "db": db_status})
