from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.models.market_data import Price, Stock


def _make_stock(db, symbol: str, name: str) -> Stock:
    stock = Stock(symbol=symbol, name=name, sector="Financials", exchange="IDX", currency="IDR")
    db.add(stock)
    db.flush()
    return stock


def _make_candles(db, stock: Stock, start: datetime, count: int = 60) -> list[Price]:
    candles = [
        Price(
            stock_id=stock.id,
            time=start + timedelta(days=i),
            open=9000.0 + i * 20,
            high=9100.0 + i * 20,
            low=8900.0 + i * 20,
            close=9050.0 + i * 20,
            volume=1_000_000.0,
            interval="1d",
            source="sample",
        )
        for i in range(count)
    ]
    db.add_all(candles)
    db.flush()
    return candles


def _auth_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": "trader@example.com", "name": "Trader", "password": "password123"},
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "trader@example.com", "password": "password123"},
    ).json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_run_strategy_backtest_respects_date_range_and_warmup(client: TestClient) -> None:
    headers = _auth_headers(client)

    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "BBCA", "Bank Central Asia")
        _make_candles(db, stock, datetime(2026, 1, 1, tzinfo=UTC), count=90)
        db.commit()
    finally:
        db.close()

    res = client.post(
        "/api/v1/backtest",
        json={
            "symbol": "BBCA",
            "strategy": "BUY_AND_HOLD",
            "initial_capital": 100_000_000,
            "start_date": "2026-03-01",
            "end_date": "2026-03-20",
        },
        headers=headers,
    )
    assert res.status_code == 200
    curve = res.json()["data"]["equity_curve"]
    assert curve[0]["time"] == "2026-03-01"
    assert curve[-1]["time"] == "2026-03-20"
    assert len(curve) == 20


def test_backtest_rejects_invalid_strategy_ranges(client: TestClient) -> None:
    headers = _auth_headers(client)
    for payload in (
        {"symbol": "BBCA", "fast_period": 50, "slow_period": 20},
        {"symbol": "BBCA", "rsi_oversold": 80, "rsi_overbought": 20},
    ):
        res = client.post("/api/v1/backtest", json=payload, headers=headers)
        assert res.status_code == 422
        assert res.json()["code"] == "VALIDATION_ERROR"


def test_run_strategy_backtest_rejects_invalid_date_range(client: TestClient) -> None:
    headers = _auth_headers(client)
    res = client.post(
        "/api/v1/backtest",
        json={
            "symbol": "BBCA",
            "start_date": "2026-03-01",
            "end_date": "2026-02-01",
        },
        headers=headers,
    )
    assert res.status_code == 422
    assert res.json()["code"] == "VALIDATION_ERROR"


def test_run_strategy_backtest(client: TestClient) -> None:
    headers = _auth_headers(client)

    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "BBCA", "Bank Central Asia")
        _make_candles(db, stock, datetime(2026, 1, 1, tzinfo=UTC), count=65)
        db.commit()
    finally:
        db.close()

    res = client.post(
        "/api/v1/backtest",
        json={"symbol": "BBCA", "strategy": "BUY_AND_HOLD", "initial_capital": 100_000_000},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["symbol"] == "BBCA"
    assert data["strategy"] == "BUY_AND_HOLD"
    assert "summary" in data
    assert data["summary"]["total_return_pct"] > 0
    assert len(data["equity_curve"]) > 50
