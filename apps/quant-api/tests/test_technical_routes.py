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
            close=9050.0 + i * 10,
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


def test_get_stock_technical_success(client: TestClient) -> None:
    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "BBCA", "Bank Central Asia")
        _make_candles(db, stock, datetime(2026, 1, 1, tzinfo=UTC), count=35)
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/stocks/BBCA/technical", headers=_auth_headers(client))
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["symbol"] == "BBCA"
    assert data["interval"] == "1d"
    assert data["trend"] in ("bullish", "bearish", "neutral")
    assert data["ma_signal"] in ("positive", "negative", "neutral")
    assert data["rsi"] is not None
    assert "indicators" in data
    assert "ma20" in data["indicators"]
    assert "macd" in data["indicators"]
    assert "bollinger" in data["indicators"]


def test_get_stock_technical_unknown_symbol(client: TestClient) -> None:
    response = client.get("/api/v1/stocks/UNKNOWN/technical", headers=_auth_headers(client))
    assert response.status_code == 404
    assert response.json()["code"] == "SYMBOL_NOT_FOUND"
