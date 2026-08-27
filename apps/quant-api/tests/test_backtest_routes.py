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
    assert res.json()["data"]["summary"]["total_trades"] == 1
    assert curve[0]["equity"] == 99_850_000.0


def test_buy_and_hold_enters_on_middle_evaluation_date(client: TestClient) -> None:
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
            "end_date": "2026-03-10",
        },
        headers=headers,
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["equity_curve"][0]["time"] == "2026-03-01"
    assert data["summary"]["total_trades"] == 1
    assert data["equity_curve"][0]["equity"] == 99_850_000.0


def test_backtest_rejects_insufficient_evaluation_data(client: TestClient) -> None:
    headers = _auth_headers(client)

    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "BBCA", "Bank Central Asia")
        _make_candles(db, stock, datetime(2026, 1, 1, tzinfo=UTC), count=60)
        db.commit()
    finally:
        db.close()

    res = client.post(
        "/api/v1/backtest",
        json={
            "symbol": "BBCA",
            "strategy": "BUY_AND_HOLD",
            "start_date": "2026-03-10",
            "end_date": "2026-03-11",
        },
        headers=headers,
    )

    assert res.status_code == 400
    assert res.json()["code"] == "INSUFFICIENT_DATA"


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
    assert data["summary"]["sortino_ratio"] == 0.0
    assert len(data["equity_curve"]) > 50
    metadata = data["metadata"]
    assert metadata["status"] == "succeeded"
    assert metadata["status_history"] == ["queued", "running", "succeeded"]
    assert metadata["retry_policy"] == "none_synchronous_execution"
    assert metadata["dataset_id"] == "BBCA:1d"
    assert len(metadata["dataset_version"]) == 16
    assert metadata["strategy_version"] == "v1"
    assert metadata["execution_price"] == "same_candle_close_with_slippage"
    assert metadata["corporate_action_policy"] == "not_adjusted"
    assert metadata["effective_start_date"] == "2026-01-01"
    assert metadata["effective_end_date"] == "2026-03-06"


def test_backtest_future_data_does_not_change_earlier_equity(client: TestClient) -> None:
    headers = _auth_headers(client)
    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "BBCA", "Bank Central Asia")
        candles = _make_candles(db, stock, datetime(2026, 1, 1, tzinfo=UTC), count=65)
        db.commit()
        first = client.post(
            "/api/v1/backtest",
            json={"symbol": "BBCA", "strategy": "BUY_AND_HOLD"},
            headers=headers,
        )
        candles[-1].close = 100_000.0
        db.commit()
    finally:
        db.close()

    second = client.post(
        "/api/v1/backtest",
        json={"symbol": "BBCA", "strategy": "BUY_AND_HOLD"},
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    first_curve = first.json()["data"]["equity_curve"]
    second_curve = second.json()["data"]["equity_curve"]
    assert first_curve[:-1] == second_curve[:-1]


def test_backtest_slippage_changes_execution_result(client: TestClient) -> None:
    headers = _auth_headers(client)
    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "BBCA", "Bank Central Asia")
        _make_candles(db, stock, datetime(2026, 1, 1, tzinfo=UTC), count=65)
        db.commit()
    finally:
        db.close()

    base_payload = {
        "symbol": "BBCA",
        "strategy": "BUY_AND_HOLD",
        "initial_capital": 100_000_000,
    }
    no_slippage = client.post("/api/v1/backtest", json=base_payload, headers=headers)
    with_slippage = client.post(
        "/api/v1/backtest",
        json={**base_payload, "slippage_percent": 0.01},
        headers=headers,
    )

    assert no_slippage.status_code == 200
    assert with_slippage.status_code == 200
    assert (
        with_slippage.json()["data"]["summary"]["final_equity"]
        < no_slippage.json()["data"]["summary"]["final_equity"]
    )
    assert with_slippage.json()["data"]["metadata"]["slippage_percent"] == 0.01
