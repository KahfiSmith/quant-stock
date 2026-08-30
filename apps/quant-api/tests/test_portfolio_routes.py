from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.models.market_data import Price, Stock


def _make_stock(db, symbol: str, name: str) -> Stock:
    stock = Stock(symbol=symbol, name=name, sector="Financials", exchange="IDX", currency="IDR")
    db.add(stock)
    db.flush()
    return stock


def _make_candles(db, stock: Stock, start: datetime, count: int = 30) -> list[Price]:
    candles = [
        Price(
            stock_id=stock.id,
            time=start + timedelta(days=i),
            open=9000.0 + i * 10,
            high=9100.0 + i * 10,
            low=8900.0 + i * 10,
            close=9500.0,
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


def test_portfolio_lifecycle_and_holdings_pnl(client: TestClient) -> None:
    headers = _auth_headers(client)

    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "BBCA", "Bank Central Asia")
        _make_candles(db, stock, datetime(2026, 1, 1, tzinfo=UTC), count=30)
        db.commit()
    finally:
        db.close()


    res = client.post(
        "/api/v1/portfolios",
        json={"name": "Main Growth", "description": "Long term growth holdings"},
        headers=headers,
    )
    assert res.status_code == 200
    portfolio_id = res.json()["data"]["id"]


    tx_res = client.post(
        f"/api/v1/portfolios/{portfolio_id}/transactions",
        json={"symbol": "BBCA", "transaction_type": "BUY", "quantity": 100, "price": 9000, "fee": 1500},
        headers=headers,
    )
    assert tx_res.status_code == 200


    detail_res = client.get(f"/api/v1/portfolios/{portfolio_id}", headers=headers)
    assert detail_res.status_code == 200
    data = detail_res.json()["data"]
    assert data["name"] == "Main Growth"
    assert len(data["holdings"]) == 1
    holding = data["holdings"][0]
    assert holding["symbol"] == "BBCA"
    assert holding["quantity"] == 100
    assert holding["current_price"] == 9500.0
    assert holding["unrealized_pnl"] > 0

    sell_res = client.post(
        f"/api/v1/portfolios/{portfolio_id}/transactions",
        json={"symbol": "BBCA", "transaction_type": "SELL", "quantity": 40, "price": 9500},
        headers=headers,
    )
    assert sell_res.status_code == 200

    remaining_res = client.get(f"/api/v1/portfolios/{portfolio_id}", headers=headers)
    remaining_data = remaining_res.json()["data"]
    assert remaining_data["holdings"][0]["quantity"] == 60
    assert remaining_data["total_realized_pnl"] == 19_400.0
    assert remaining_data["risk"]["max_holding_concentration_percent"] == 100.0
    assert remaining_data["risk"]["observations"] == 0

    update_res = client.patch(
        f"/api/v1/portfolios/{portfolio_id}",
        json={"name": "Main Income", "currency": "USD"},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["name"] == "Main Income"
    assert update_res.json()["data"]["currency"] == "USD"

    oversell_res = client.post(
        f"/api/v1/portfolios/{portfolio_id}/transactions",
        json={"symbol": "BBCA", "transaction_type": "SELL", "quantity": 61, "price": 9500},
        headers=headers,
    )
    assert oversell_res.status_code == 409
    assert oversell_res.json()["code"] == "INSUFFICIENT_HOLDINGS"


def test_portfolio_risk_uses_historical_transaction_date(client: TestClient) -> None:
    headers = _auth_headers(client)

    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "BBCA", "Bank Central Asia")
        _make_candles(db, stock, datetime(2026, 1, 1, tzinfo=UTC), count=30)
        db.commit()
    finally:
        db.close()

    create_res = client.post(
        "/api/v1/portfolios",
        json={"name": "Historical Portfolio"},
        headers=headers,
    )
    portfolio_id = create_res.json()["data"]["id"]
    buy_res = client.post(
        f"/api/v1/portfolios/{portfolio_id}/transactions",
        json={
            "symbol": "BBCA",
            "transaction_type": "BUY",
            "quantity": 100,
            "price": 9000,
            "transacted_at": "2026-01-05T00:00:00Z",
        },
        headers=headers,
    )
    assert buy_res.status_code == 200

    detail = client.get(f"/api/v1/portfolios/{portfolio_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["risk"]["observations"] == 25


def test_portfolio_rejects_sell_without_holdings(client: TestClient) -> None:
    headers = _auth_headers(client)

    db = client.app.state.database.session()
    try:
        _make_stock(db, "BBCA", "Bank Central Asia")
        db.commit()
    finally:
        db.close()

    create_res = client.post(
        "/api/v1/portfolios",
        json={"name": "Empty Portfolio"},
        headers=headers,
    )
    portfolio_id = create_res.json()["data"]["id"]

    sell_res = client.post(
        f"/api/v1/portfolios/{portfolio_id}/transactions",
        json={"symbol": "BBCA", "transaction_type": "SELL", "quantity": 1, "price": 100},
        headers=headers,
    )
    assert sell_res.status_code == 409
    assert sell_res.json()["code"] == "INSUFFICIENT_HOLDINGS"
