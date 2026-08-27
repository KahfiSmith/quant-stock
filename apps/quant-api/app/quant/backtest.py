"""Historical strategy backtesting engine."""

from __future__ import annotations

import math
from datetime import UTC, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.models.market_data import Price, Stock
from app.schemas.backtest import (
    BacktestRequest,
    BacktestResponse,
    BacktestSummary,
    EquityPoint,
)
from app.technical.indicators import rsi, sma


def run_strategy_backtest(db: Session, req: BacktestRequest) -> BacktestResponse:
    stock = db.scalar(select(Stock).where(Stock.symbol == req.symbol.upper()))
    if not stock:
        raise ApiError(404, "SYMBOL_NOT_FOUND", f"Unknown symbol: {req.symbol.upper()}")

    stmt = select(Price).where(Price.stock_id == stock.id, Price.interval == "1d")
    if req.end_date:
        end_at = datetime.combine(req.end_date, time.max, tzinfo=UTC)
        stmt = stmt.where(Price.time <= end_at)
    prices = list(db.scalars(stmt.order_by(Price.time.asc())))

    evaluation_start = 0
    if req.start_date:
        evaluation_start = next(
            (index for index, price in enumerate(prices) if price.time.date() >= req.start_date),
            len(prices),
        )

    required_history = max(req.slow_period, 30)
    if len(prices) < required_history:
        raise ApiError(400, "INSUFFICIENT_DATA", "Not enough price history to run this backtest")
    if evaluation_start == len(prices):
        raise ApiError(400, "INSUFFICIENT_DATA", "No price history exists in the requested backtest period")
    if req.start_date and evaluation_start < required_history - 1:
        raise ApiError(
            400,
            "INSUFFICIENT_DATA",
            "Not enough warm-up history exists before the requested backtest period",
        )

    dates = [p.time.strftime("%Y-%m-%d") for p in prices]
    closes = [float(p.close) for p in prices]

    # Calculate indicators
    fast_ma = sma(closes, req.fast_period)
    slow_ma = sma(closes, req.slow_period)
    rsi_vals = rsi(closes, 14)

    cash = req.initial_capital
    shares = 0.0
    trades_count = 0
    winning_trades = 0
    last_buy_price = 0.0

    equity_curve: list[EquityPoint] = []
    peak_equity = req.initial_capital
    daily_returns: list[float] = []

    initial_close = closes[evaluation_start]

    for i in range(evaluation_start, len(prices)):
        close = closes[i]
        date_str = dates[i]

        # Generate signals
        signal = 0  # 1 = BUY, -1 = SELL, 0 = HOLD

        if req.strategy == "BUY_AND_HOLD":
            if i == 0:
                signal = 1
        elif req.strategy == "SMA_CROSSOVER":
            if (
                i > 0
                and fast_ma[i] is not None
                and slow_ma[i] is not None
                and fast_ma[i - 1] is not None
                and slow_ma[i - 1] is not None
            ):
                if fast_ma[i] > slow_ma[i] and fast_ma[i - 1] <= slow_ma[i - 1]:
                    signal = 1
                elif fast_ma[i] < slow_ma[i] and fast_ma[i - 1] >= slow_ma[i - 1]:
                    signal = -1
        elif req.strategy == "RSI_MOMENTUM":
            if i > 0 and rsi_vals[i] is not None and rsi_vals[i - 1] is not None:
                if rsi_vals[i] < req.rsi_oversold and rsi_vals[i - 1] >= req.rsi_oversold:
                    signal = 1
                elif rsi_vals[i] > req.rsi_overbought and rsi_vals[i - 1] <= req.rsi_overbought:
                    signal = -1

        # Execute signals
        if signal == 1 and cash > 0:
            fee = cash * req.fee_percent
            investable = cash - fee
            bought_shares = investable / close
            shares += bought_shares
            cash = 0.0
            last_buy_price = close
            trades_count += 1
        elif signal == -1 and shares > 0:
            gross = shares * close
            fee = gross * req.fee_percent
            cash = gross - fee
            if close > last_buy_price:
                winning_trades += 1
            shares = 0.0
            trades_count += 1

        total_equity = cash + (shares * close)
        if total_equity > peak_equity:
            peak_equity = total_equity

        dd = (total_equity - peak_equity) / peak_equity * 100.0 if peak_equity > 0 else 0.0
        bench = (close / initial_close) * req.initial_capital

        if i > 0 and len(equity_curve) > 0:
            prev_eq = equity_curve[-1].equity
            daily_returns.append((total_equity - prev_eq) / prev_eq if prev_eq > 0 else 0.0)

        equity_curve.append(
            EquityPoint(
                time=date_str,
                equity=round(total_equity, 2),
                benchmark=round(bench, 2),
                drawdown=round(dd, 2),
            )
        )

    final_equity = equity_curve[-1].equity
    total_return_pct = (final_equity - req.initial_capital) / req.initial_capital * 100.0

    # CAGR calculation
    days = max(1, len(prices) - evaluation_start)
    years = days / 252.0
    cagr_pct = (
        ((final_equity / req.initial_capital) ** (1.0 / years) - 1.0) * 100.0
        if years > 0 and final_equity > 0
        else 0.0
    )

    # Volatility & Sharpe
    if len(daily_returns) > 1:
        mean_ret = sum(daily_returns) / len(daily_returns)
        var = sum((r - mean_ret) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        daily_std = math.sqrt(var)
        ann_vol = daily_std * math.sqrt(252.0) * 100.0
        # Risk free rate baseline 5%
        rf_daily = 0.05 / 252.0
        sharpe = (mean_ret - rf_daily) / daily_std * math.sqrt(252.0) if daily_std > 0 else 0.0
    else:
        ann_vol = 0.0
        sharpe = 0.0

    max_dd = min((pt.drawdown for pt in equity_curve), default=0.0)
    win_rate = (winning_trades / (trades_count / 2) * 100.0) if trades_count >= 2 else 0.0

    summary = BacktestSummary(
        total_return_pct=round(total_return_pct, 2),
        cagr_pct=round(cagr_pct, 2),
        annualized_volatility_pct=round(ann_vol, 2),
        sharpe_ratio=round(sharpe, 2),
        max_drawdown_pct=round(max_dd, 2),
        total_trades=trades_count,
        win_rate_pct=round(win_rate, 2),
        final_equity=round(final_equity, 2),
    )

    return BacktestResponse(
        symbol=stock.symbol,
        strategy=req.strategy,
        initial_capital=req.initial_capital,
        summary=summary,
        equity_curve=equity_curve,
        as_of=datetime.now(UTC),
    )
