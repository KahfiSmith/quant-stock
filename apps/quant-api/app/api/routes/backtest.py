from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.errors import success
from app.models.user import User
from app.quant.backtest import run_strategy_backtest
from app.schemas.backtest import BacktestRequest, BacktestResponse

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])


@router.post("", response_model=None)
def post_backtest(
    body: BacktestRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict[str, object]:
    result: BacktestResponse = run_strategy_backtest(db, body)
    return success(result.model_dump(mode="json"), "Backtest completed successfully")
