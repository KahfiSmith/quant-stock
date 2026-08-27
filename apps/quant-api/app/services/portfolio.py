from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.models.market_data import Price, Stock
from app.models.portfolio import Portfolio, Transaction
from app.schemas.portfolio import (
    CreatePortfolioRequest,
    CreateTransactionRequest,
    HoldingResponse,
    PortfolioDetailResponse,
    PortfolioSummaryResponse,
    TransactionResponse,
)


def list_user_portfolios(db: Session, user_id: int) -> list[PortfolioSummaryResponse]:
    rows = list(
        db.scalars(
            select(Portfolio).where(Portfolio.user_id == user_id).order_by(Portfolio.id.asc())
        )
    )
    return [
        PortfolioSummaryResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            currency=p.currency,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in rows
    ]


def create_user_portfolio(
    db: Session, user_id: int, req: CreatePortfolioRequest
) -> PortfolioSummaryResponse:
    existing = db.scalar(
        select(Portfolio).where(Portfolio.user_id == user_id, Portfolio.name == req.name.strip())
    )
    if existing:
        raise ApiError(409, "PORTFOLIO_EXISTS", f"Portfolio '{req.name}' already exists")

    portfolio = Portfolio(
        user_id=user_id,
        name=req.name.strip(),
        description=req.description.strip() if req.description else None,
        currency=req.currency.upper(),
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return PortfolioSummaryResponse(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        currency=portfolio.currency,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
    )


def get_portfolio_detail(db: Session, user_id: int, portfolio_id: int) -> PortfolioDetailResponse:
    portfolio = db.scalar(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
    )
    if not portfolio:
        raise ApiError(404, "PORTFOLIO_NOT_FOUND", "Portfolio not found")

    transactions = list(
        db.scalars(
            select(Transaction)
            .where(Transaction.portfolio_id == portfolio.id)
            .order_by(Transaction.transacted_at.asc())
        )
    )

    # Compute holdings via FIFO / weighted average cost
    stock_shares: dict[int, float] = defaultdict(float)
    stock_cost: dict[int, float] = defaultdict(float)

    for tx in transactions:
        qty = float(tx.quantity)
        price = float(tx.price)
        if tx.transaction_type == "BUY":
            stock_shares[tx.stock_id] += qty
            stock_cost[tx.stock_id] += qty * price + float(tx.fee)
        elif tx.transaction_type == "SELL":
            curr_shares = stock_shares[tx.stock_id]
            if curr_shares > 0:
                avg_cost = stock_cost[tx.stock_id] / curr_shares
                stock_shares[tx.stock_id] -= qty
                stock_cost[tx.stock_id] -= qty * avg_cost

    holdings: list[HoldingResponse] = []
    total_cost = 0.0
    current_value = 0.0

    for stock_id, shares in stock_shares.items():
        if shares <= 0:
            continue
        stock = db.scalar(select(Stock).where(Stock.id == stock_id))
        if not stock:
            continue

        latest_price_rec = db.scalar(
            select(Price)
            .where(Price.stock_id == stock.id, Price.interval == "1d")
            .order_by(Price.time.desc())
            .limit(1)
        )
        curr_price = float(latest_price_rec.close) if latest_price_rec else None

        cost = stock_cost[stock_id]
        avg_buy = cost / shares if shares > 0 else 0.0
        val = curr_price * shares if curr_price is not None else None
        pnl = (val - cost) if val is not None else None
        pnl_pct = (pnl / cost * 100.0) if pnl is not None and cost > 0 else None

        total_cost += cost
        if val is not None:
            current_value += val

        holdings.append(
            HoldingResponse(
                stock_id=stock.id,
                symbol=stock.symbol,
                name=stock.name,
                quantity=round(shares, 4),
                avg_buy_price=round(avg_buy, 2),
                current_price=round(curr_price, 2) if curr_price is not None else None,
                current_value=round(val, 2) if val is not None else None,
                unrealized_pnl=round(pnl, 2) if pnl is not None else None,
                unrealized_pnl_percent=round(pnl_pct, 2) if pnl_pct is not None else None,
            )
        )

    total_pnl = current_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100.0) if total_cost > 0 else 0.0

    return PortfolioDetailResponse(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        currency=portfolio.currency,
        total_cost=round(total_cost, 2),
        current_value=round(current_value, 2),
        total_unrealized_pnl=round(total_pnl, 2),
        total_unrealized_pnl_percent=round(total_pnl_pct, 2),
        holdings=holdings,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
    )


def add_portfolio_transaction(
    db: Session, user_id: int, portfolio_id: int, req: CreateTransactionRequest
) -> TransactionResponse:
    portfolio = db.scalar(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
    )
    if not portfolio:
        raise ApiError(404, "PORTFOLIO_NOT_FOUND", "Portfolio not found")

    stock = db.scalar(select(Stock).where(Stock.symbol == req.symbol.upper()))
    if not stock:
        raise ApiError(404, "SYMBOL_NOT_FOUND", f"Unknown symbol: {req.symbol.upper()}")

    tx = Transaction(
        portfolio_id=portfolio.id,
        stock_id=stock.id,
        transaction_type=req.transaction_type,
        quantity=req.quantity,
        price=req.price,
        fee=req.fee,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    return TransactionResponse(
        id=tx.id,
        portfolio_id=tx.portfolio_id,
        stock_id=tx.stock_id,
        symbol=stock.symbol,
        transaction_type=tx.transaction_type,
        quantity=float(tx.quantity),
        price=float(tx.price),
        fee=float(tx.fee),
        transacted_at=tx.transacted_at,
    )
