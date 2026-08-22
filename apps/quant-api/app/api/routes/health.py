from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import ApiError, success

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    return success({"status": "ok"}, "Service is healthy")


@router.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as error:
        raise ApiError(503, "DEPENDENCY_UNAVAILABLE", "Database is unavailable") from error
    return success({"status": "ready"}, "Service is ready")
