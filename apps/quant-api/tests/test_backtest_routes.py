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


def test_backtest_job_lifecycle_persistence_and_unauthorized_isolation(client: TestClient) -> None:

    client.post(
        "/api/v1/auth/register",
        json={"email": "u1@example.com", "name": "U1", "password": "password123"},
    )
    t1 = client.post(
        "/api/v1/auth/login",
        json={"email": "u1@example.com", "password": "password123"},
    ).json()["data"]["access_token"]
    h1 = {"Authorization": f"Bearer {t1}"}

    client.post(
        "/api/v1/auth/register",
        json={"email": "u2@example.com", "name": "U2", "password": "password123"},
    )
    t2 = client.post(
        "/api/v1/auth/login",
        json={"email": "u2@example.com", "password": "password123"},
    ).json()["data"]["access_token"]
    h2 = {"Authorization": f"Bearer {t2}"}

    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "TLKM", "Telkom Indonesia")
        _make_candles(db, stock, datetime(2026, 1, 1, tzinfo=UTC), count=65)
        db.commit()
    finally:
        db.close()


    res = client.post(
        "/api/v1/backtest",
        json={"symbol": "TLKM", "strategy": "BUY_AND_HOLD"},
        headers=h1,
    )
    assert res.status_code == 200
    job_id = res.json()["data"]["job_id"]
    assert job_id is not None


    jobs_res = client.get("/api/v1/backtest/jobs", headers=h1)
    assert jobs_res.status_code == 200
    jobs_data = jobs_res.json()["data"]
    assert jobs_data["total"] >= 1
    assert any(j["id"] == job_id for j in jobs_data["items"])
    target_job = next(j for j in jobs_data["items"] if j["id"] == job_id)
    assert target_job["status"] == "succeeded"
    assert target_job["symbol"] == "TLKM"
    assert target_job["summary"]["total_trades"] == 1


    single_res = client.get(f"/api/v1/backtest/jobs/{job_id}", headers=h1)
    assert single_res.status_code == 200
    assert single_res.json()["data"]["id"] == job_id
    assert len(single_res.json()["data"]["equity_curve"]) > 50


    u2_single = client.get(f"/api/v1/backtest/jobs/{job_id}", headers=h2)
    assert u2_single.status_code == 404
    assert u2_single.json()["code"] == "JOB_NOT_FOUND"

    u2_list = client.get("/api/v1/backtest/jobs", headers=h2)
    assert u2_list.status_code == 200
    assert not any(j["id"] == job_id for j in u2_list.json()["data"]["items"])


def test_backtest_job_records_failure_lifecycle(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "fail@example.com", "name": "FailUser", "password": "password123"},
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "fail@example.com", "password": "password123"},
    ).json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}


    res = client.post(
        "/api/v1/backtest",
        json={"symbol": "NONEXISTENT", "strategy": "BUY_AND_HOLD"},
        headers=headers,
    )
    assert res.status_code == 404


    jobs_res = client.get("/api/v1/backtest/jobs", headers=headers)
    assert jobs_res.status_code == 200
    items = jobs_res.json()["data"]["items"]
    assert len(items) == 1
    failed_job = items[0]
    assert failed_job["symbol"] == "NONEXISTENT"
    assert failed_job["status"] == "failed"
    assert "Unknown symbol" in failed_job["error_message"]
    assert failed_job["finished_at"] is not None
