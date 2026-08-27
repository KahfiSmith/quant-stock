from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.errors import success
from app.models.user import User
from app.schemas.portfolio import (
    CreatePortfolioRequest,
    CreateTransactionRequest,
    PortfolioDetailResponse,
    PortfolioSummaryResponse,
    TransactionResponse,
)
from app.services.portfolio import (
    add_portfolio_transaction,
    create_user_portfolio,
    get_portfolio_detail,
    list_user_portfolios,
)

router = APIRouter(prefix="/api/v1/portfolios", tags=["portfolio"])


@router.get("", response_model=None)
def get_portfolios(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    result: list[PortfolioSummaryResponse] = list_user_portfolios(db, user.id)
    return success([p.model_dump(mode="json") for p in result], "Portfolios retrieved")


@router.post("", response_model=None)
def post_portfolio(
    body: CreatePortfolioRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    result: PortfolioSummaryResponse = create_user_portfolio(db, user.id, body)
    return success(result.model_dump(mode="json"), "Portfolio created")


@router.get("/{portfolio_id}", response_model=None)
def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    result: PortfolioDetailResponse = get_portfolio_detail(db, user.id, portfolio_id)
    return success(result.model_dump(mode="json"), "Portfolio detail retrieved")


@router.post("/{portfolio_id}/transactions", response_model=None)
def post_transaction(
    portfolio_id: int,
    body: CreateTransactionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    result: TransactionResponse = add_portfolio_transaction(db, user.id, portfolio_id, body)
    return success(result.model_dump(mode="json"), "Transaction added")
