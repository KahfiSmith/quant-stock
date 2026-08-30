import math
from collections import defaultdict
from datetime import UTC, datetime
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
    PortfolioRiskResponse,
    PortfolioSummaryResponse,
    TransactionResponse,
    UpdatePortfolioRequest,
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


def update_user_portfolio(
    db: Session, user_id: int, portfolio_id: int, req: UpdatePortfolioRequest
) -> PortfolioSummaryResponse:
    portfolio = db.scalar(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
    )
    if not portfolio:
        raise ApiError(404, "PORTFOLIO_NOT_FOUND", "Portfolio not found")
    if req.name is not None:
        normalized_name = req.name.strip()
        duplicate = db.scalar(
            select(Portfolio).where(
                Portfolio.user_id == user_id,
                Portfolio.name == normalized_name,
                Portfolio.id != portfolio_id,
            )
        )
        if duplicate:
            raise ApiError(409, "PORTFOLIO_EXISTS", f"Portfolio '{normalized_name}' already exists")
        portfolio.name = normalized_name
    if req.description is not None:
        portfolio.description = req.description.strip() or None
    if req.currency is not None:
        portfolio.currency = req.currency.upper()
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


def _replay_transactions(
    transactions: list[Transaction],
) -> tuple[dict[int, Decimal], dict[int, Decimal], Decimal]:
    shares: dict[int, Decimal] = defaultdict(Decimal)
    cost: dict[int, Decimal] = defaultdict(Decimal)
    realized = Decimal(0)
    for tx in transactions:
        quantity = Decimal(str(tx.quantity))
        price = Decimal(str(tx.price))
        fee = Decimal(str(tx.fee))
        if tx.transaction_type == "BUY":
            shares[tx.stock_id] += quantity
            cost[tx.stock_id] += quantity * price + fee
        else:
            held = shares[tx.stock_id]
            if quantity > held:
                raise ApiError(
                    409,
                    "INSUFFICIENT_HOLDINGS",
                    f"Cannot sell {quantity} shares; only {held} shares are held",
                )
            average_cost = cost[tx.stock_id] / held if held else Decimal(0)
            realized += quantity * price - fee - quantity * average_cost
            shares[tx.stock_id] -= quantity
            cost[tx.stock_id] -= quantity * average_cost
    return shares, cost, realized


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

    stock_shares, stock_cost, total_realized_pnl = _replay_transactions(transactions)

    holdings: list[HoldingResponse] = []
    total_cost = Decimal(0)
    current_value = Decimal(0)
    hundred = Decimal("100")
    cents = Decimal("0.01")
    shares_precision = Decimal("0.0001")


    earliest_price_as_of: datetime | None = None
    data_lag: str | None = None

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
        price_as_of = latest_price_rec.time if latest_price_rec else None
        price_source = latest_price_rec.source if latest_price_rec else None

        holding_data_lag: str | None = None
        if price_source == "yfinance":
            holding_data_lag = "eod_1d"

        if holding_data_lag and data_lag is None:
            data_lag = holding_data_lag


        if price_as_of is not None:
            if earliest_price_as_of is None or price_as_of < earliest_price_as_of:
                earliest_price_as_of = price_as_of

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
                price_as_of=price_as_of,
                data_source=price_source,
                data_lag=holding_data_lag,
            )
        )

    total_pnl = current_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * hundred) if total_cost > 0 else Decimal(0)

    latest_values = [
        Decimal(str(holding.current_value))
        for holding in holdings
        if holding.current_value is not None
    ]
    concentration = (
        max(latest_values) / sum(latest_values) * hundred
        if latest_values and sum(latest_values) > 0
        else Decimal(0)
    )
    daily_values: dict = {}
    historical_shares: dict[int, Decimal] = defaultdict(Decimal)
    transactions_by_time = sorted(transactions, key=lambda tx: (tx.transacted_at, tx.id))
    transaction_index = 0
    all_prices = list(
        db.scalars(
            select(Price)
            .where(Price.stock_id.in_(stock_shares.keys()), Price.interval == "1d")
            .order_by(Price.time.asc())
        )
    )
    for price_record in all_prices:
        while (
            transaction_index < len(transactions_by_time)
            and transactions_by_time[transaction_index].transacted_at.date() <= price_record.time.date()
        ):
            transaction = transactions_by_time[transaction_index]
            quantity = Decimal(str(transaction.quantity))
            historical_shares[transaction.stock_id] += quantity if transaction.transaction_type == "BUY" else -quantity
            transaction_index += 1
        shares = historical_shares[price_record.stock_id]
        if shares > 0:
            day = price_record.time.date()
            daily_values[day] = daily_values.get(day, Decimal(0)) + shares * Decimal(str(price_record.close))
    ordered_values = [daily_values[day] for day in sorted(daily_values)]
    returns = [
        (current - previous) / previous
        for previous, current in zip(ordered_values, ordered_values[1:])
        if previous > 0
    ]
    volatility = Decimal(0)
    if len(returns) > 1:
        mean = sum(returns) / Decimal(len(returns))
        variance = sum((value - mean) ** 2 for value in returns) / Decimal(len(returns) - 1)
        volatility = Decimal(str(math.sqrt(float(variance)) * math.sqrt(252) * 100))

    return PortfolioDetailResponse(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        currency=portfolio.currency,
        total_cost=float(total_cost.quantize(cents)),
        current_value=float(current_value.quantize(cents)),
        total_realized_pnl=float(total_realized_pnl.quantize(cents)),
        total_unrealized_pnl=float(total_pnl.quantize(cents)),
        total_unrealized_pnl_percent=float(total_pnl_pct.quantize(cents)),
        holdings=holdings,
        risk=PortfolioRiskResponse(
            annualized_volatility_percent=float(volatility.quantize(cents)),
            max_holding_concentration_percent=float(concentration.quantize(cents)),
            observations=len(returns),
        ),
        as_of=datetime.now(UTC),
        price_as_of=earliest_price_as_of,
        data_lag=data_lag,
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
        shares, _, _ = _replay_transactions(transactions)
        requested_quantity = Decimal(str(req.quantity))
        held_quantity = shares[stock.id]
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
        transacted_at=req.transacted_at,
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
