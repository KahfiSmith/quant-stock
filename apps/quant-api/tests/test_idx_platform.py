"""Tests for IDX Universe Master, Point-in-Time Fundamentals, Market Flows, and Factor Rotation Engine."""

from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.idx_models import (
    BenchmarkPrice,
    CorporateActionIDX,
    FinancialStatementPIT,
    MarketFlowIDX,
)
from app.models.market_data import Price, Stock


def _setup_idx_test_data(db: Session) -> list[Stock]:
    today = date.today()
    stocks = []


    for offset in range(30, -1, -1):
        day = today - timedelta(days=offset)
        t_dt = datetime.combine(day, datetime.min.time(), tzinfo=UTC)
        db.add(
            BenchmarkPrice(
                symbol="^JKSE",
                time=t_dt,
                open=7100.0,
                high=7250.0,
                low=7050.0,
                close=7200.0 + (30 - offset) * 5.0,
                volume=15_000_000_000.0,
            )
        )


    specs = [
        {"symbol": "BBCA", "name": "Bank Central Asia", "sector": "Financials", "sub": "Banks", "cap": 1_200_000_000_000_000.0, "price": 9500.0, "roe": 0.21, "eps": 450.0, "bvps": 2200.0},
        {"symbol": "TLKM", "name": "Telkom Indonesia", "sector": "Infrastructures", "sub": "Telecom", "cap": 280_000_000_000_000.0, "price": 3000.0, "roe": 0.16, "eps": 220.0, "bvps": 1200.0},
        {"symbol": "ADRO", "name": "Adaro Energy", "sector": "Energy", "sub": "Coal", "cap": 110_000_000_000_000.0, "price": 3600.0, "roe": 0.28, "eps": 600.0, "bvps": 2500.0},
    ]

    for sp in specs:
        st = Stock(
            symbol=sp["symbol"],
            name=sp["name"],
            sector=sp["sector"],
            sub_sector=sp["sub"],
            listing_date=date(2000, 1, 1),
            market_cap=sp["cap"],
            liquidity_status="liquid",
            is_active=True,
            board="MAIN",
            avg_daily_turnover_20d=100_000_000_000.0,
            avg_daily_frequency_20d=10_000.0,
            exchange="IDX",
            currency="IDR",
        )
        db.add(st)
        db.flush()
        stocks.append(st)


        for offset in range(30, -1, -1):
            day = today - timedelta(days=offset)
            t_dt = datetime.combine(day, datetime.min.time(), tzinfo=UTC)
            db.add(
                Price(
                    stock_id=st.id,
                    time=t_dt,
                    open=sp["price"] * 0.99,
                    high=sp["price"] * 1.02,
                    low=sp["price"] * 0.98,
                    close=sp["price"] + (30 - offset) * 10.0,
                    volume=5_000_000.0,
                    interval="1d",
                    source="idx_feed",
                )
            )

            db.add(
                MarketFlowIDX(
                    stock_id=st.id,
                    date=day,
                    foreign_buy_value=25_000_000_000.0,
                    foreign_sell_value=18_000_000_000.0,
                    net_foreign_value=7_000_000_000.0,
                    foreign_buy_volume=2_500_000.0,
                    foreign_sell_volume=1_800_000.0,
                )
            )


        db.add(
            FinancialStatementPIT(
                stock_id=st.id,
                fiscal_year=2024,
                fiscal_quarter="FY",
                period_end=date(2024, 12, 31),
                filing_date=date(2025, 3, 25),
                currency="IDR",
                eps=sp["eps"],
                bvps=sp["bvps"],
                roe=sp["roe"],
                roa=0.04,
                debt_to_equity=0.5,
                net_profit_margin=0.25,
                is_audited=True,
            )
        )


        db.add(
            CorporateActionIDX(
                stock_id=st.id,
                action_type="DIVIDEND",
                cum_date=date(2025, 4, 10),
                ex_date=date(2025, 4, 11),
                cash_amount=150.0,
            )
        )

    db.commit()
    return stocks


def test_idx_universe_endpoint(client: TestClient) -> None:
    db = client.app.state.database.session()
    try:
        _setup_idx_test_data(db)
        db.add(
            Stock(
                symbol="NVDA",
                name="NVIDIA Corporation",
                is_active=True,
                exchange="NASDAQ",
                currency="USD",
            )
        )
        db.commit()
    finally:
        db.close()

    res = client.get("/api/v1/idx/universe")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "items" in data["data"]
    assert len(data["data"]["items"]) >= 3
    assert all(item["exchange"] == "IDX" for item in data["data"]["items"])
    assert all(item["symbol"] != "NVDA" for item in data["data"]["items"])
    bbca = next(item for item in data["data"]["items"] if item["symbol"] == "BBCA")
    assert bbca["sector"] == "Financials"
    assert bbca["sub_sector"] == "Banks"
    assert bbca["composite_rank"] is not None


def test_idx_stock_detail_with_flows_and_corporate_actions(client: TestClient) -> None:
    db = client.app.state.database.session()
    try:
        _setup_idx_test_data(db)
    finally:
        db.close()

    res = client.get("/api/v1/idx/stocks/BBCA")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    payload = data["data"]
    assert payload["stock"]["symbol"] == "BBCA"
    assert len(payload["market_flows"]) > 0
    assert payload["market_flows"][0]["net_foreign_value"] == 7_000_000_000.0
    assert len(payload["corporate_actions"]) > 0
    assert payload["corporate_actions"][0]["action_type"] == "DIVIDEND"


def test_idx_factor_rotation_backtest(client: TestClient) -> None:
    db = client.app.state.database.session()
    try:
        _setup_idx_test_data(db)
    finally:
        db.close()

    payload = {
        "strategy_name": "IDX Multi-Factor Top 10",
        "initial_capital": 500_000_000.0,
        "top_n": 2,
        "rebalance_frequency": "monthly",
        "min_market_cap": 100_000_000_000.0,
        "min_adv_turnover": 1_000_000_000.0,
        "min_frequency": 500.0,
        "factor_weights": {
            "momentum": 0.30,
            "quality": 0.30,
            "value": 0.20,
            "risk": 0.10,
            "growth": 0.10,
        },
    }
    res = client.post("/api/v1/idx/factor-rotation/backtest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    bt = data["data"]
    assert bt["strategy_name"] == "IDX Multi-Factor Top 10"
    assert bt["benchmark_name"] == "IHSG (^JKSE)"
    assert len(bt["equity_curve"]) > 0
    assert len(bt["rebalance_history"]) > 0
    assert "alpha_pct" in bt["summary"]
    assert "benchmark_return_pct" in bt["summary"]
