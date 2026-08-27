from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.errors import success
from app.models.user import User
from app.schemas.screener import ScreenerRequest, ScreenerResponse
from app.services.screener import screen_stocks

router = APIRouter(prefix="/api/v1/screener", tags=["screener"])


@router.post("", response_model=None)
def post_screener(
    body: ScreenerRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, object]:
    result: ScreenerResponse = screen_stocks(db, body)
    return success(result.model_dump(mode="json"), "Screener results retrieved")
