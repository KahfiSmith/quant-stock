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

    # 1. Create Portfolio
    res = client.post(
        "/api/v1/portfolios",
        json={"name": "Main Growth", "description": "Long term growth holdings"},
        headers=headers,
    )
    assert res.status_code == 200
    portfolio_id = res.json()["data"]["id"]

    # 2. Add BUY transaction
    tx_res = client.post(
        f"/api/v1/portfolios/{portfolio_id}/transactions",
        json={"symbol": "BBCA", "transaction_type": "BUY", "quantity": 100, "price": 9000, "fee": 1500},
        headers=headers,
    )
    assert tx_res.status_code == 200

    # 3. Get portfolio detail and check holdings PnL
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
