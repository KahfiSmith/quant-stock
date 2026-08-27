from collections import defaultdict
from decimal import Decimal

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

    # Compute holdings via weighted average cost.
    stock_shares: dict[int, Decimal] = defaultdict(Decimal)
    stock_cost: dict[int, Decimal] = defaultdict(Decimal)

    for tx in transactions:
        qty = Decimal(str(tx.quantity))
        price = Decimal(str(tx.price))
        fee = Decimal(str(tx.fee))
        if tx.transaction_type == "BUY":
            stock_shares[tx.stock_id] += qty
            stock_cost[tx.stock_id] += qty * price + fee
        elif tx.transaction_type == "SELL":
            curr_shares = stock_shares[tx.stock_id]
            if qty > curr_shares:
                raise ApiError(
                    409,
                    "INSUFFICIENT_HOLDINGS",
                    f"Cannot sell {qty} shares; only {curr_shares} shares are held",
                )
            avg_cost = stock_cost[tx.stock_id] / curr_shares if curr_shares else Decimal(0)
            stock_shares[tx.stock_id] -= qty
            stock_cost[tx.stock_id] -= qty * avg_cost

    holdings: list[HoldingResponse] = []
    total_cost = Decimal(0)
    current_value = Decimal(0)
    hundred = Decimal("100")
    cents = Decimal("0.01")
    shares_precision = Decimal("0.0001")

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
        curr_price = Decimal(latest_price_rec.close) if latest_price_rec else None

        cost = stock_cost[stock_id]
        avg_buy = cost / shares if shares > 0 else Decimal(0)
        val = curr_price * shares if curr_price is not None else None
        pnl = (val - cost) if val is not None else None
        pnl_pct = (pnl / cost * hundred) if pnl is not None and cost > 0 else None

        total_cost += cost
        if val is not None:
            current_value += val

        holdings.append(
            HoldingResponse(
                stock_id=stock.id,
                symbol=stock.symbol,
                name=stock.name,
                quantity=float(shares.quantize(shares_precision)),
                avg_buy_price=float(avg_buy.quantize(cents)),
                current_price=float(curr_price.quantize(cents)) if curr_price is not None else None,
                current_value=float(val.quantize(cents)) if val is not None else None,
                unrealized_pnl=float(pnl.quantize(cents)) if pnl is not None else None,
                unrealized_pnl_percent=float(pnl_pct.quantize(cents)) if pnl_pct is not None else None,
            )
        )

    total_pnl = current_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * hundred) if total_cost > 0 else Decimal(0)

    return PortfolioDetailResponse(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        currency=portfolio.currency,
        total_cost=float(total_cost.quantize(cents)),
        current_value=float(current_value.quantize(cents)),
        total_unrealized_pnl=float(total_pnl.quantize(cents)),
        total_unrealized_pnl_percent=float(total_pnl_pct.quantize(cents)),
        holdings=holdings,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
    )


def add_portfolio_transaction(
    db: Session, user_id: int, portfolio_id: int, req: CreateTransactionRequest
) -> TransactionResponse:
    portfolio = db.scalar(
        select(Portfolio)
        .where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        .with_for_update()
    )
    if not portfolio:
        raise ApiError(404, "PORTFOLIO_NOT_FOUND", "Portfolio not found")

    stock = db.scalar(select(Stock).where(Stock.symbol == req.symbol.upper()))
    if not stock:
        raise ApiError(404, "SYMBOL_NOT_FOUND", f"Unknown symbol: {req.symbol.upper()}")

    if req.transaction_type == "SELL":
        transactions = list(
            db.scalars(
                select(Transaction)
                .where(Transaction.portfolio_id == portfolio.id)
                .order_by(Transaction.transacted_at.asc(), Transaction.id.asc())
            )
        )
        held_quantity = sum(
            (Decimal(str(tx.quantity)) if tx.transaction_type == "BUY" else -Decimal(str(tx.quantity)))
            for tx in transactions
            if tx.stock_id == stock.id
        )
        requested_quantity = Decimal(str(req.quantity))
        if requested_quantity > held_quantity:
            raise ApiError(
                409,
                "INSUFFICIENT_HOLDINGS",
                f"Cannot sell {requested_quantity} shares; only {held_quantity} shares are held",
            )

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
