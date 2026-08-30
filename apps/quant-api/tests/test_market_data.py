from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.models.market_data import Price, Stock


def _make_stock(db, symbol: str, name: str) -> Stock:
    stock = Stock(symbol=symbol, name=name, sector="Financials", exchange="IDX", currency="IDR")
    db.add(stock)
    db.flush()
    return stock


def _make_candles(db, stock: Stock, start: datetime, count: int = 3) -> list[Price]:
    candles = [
        Price(
            stock_id=stock.id,
            time=start + timedelta(days=i),
            open=9000.0 + i,
            high=9100.0 + i,
            low=8900.0 + i,
            close=9050.0 + i,
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


def _seed(client: TestClient) -> None:
    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "BBCA", "Bank Central Asia")
        _make_candles(db, stock, datetime(2026, 1, 5, tzinfo=UTC))
        other = _make_stock(db, "TLKM", "Telkom Indonesia")
        _make_candles(db, other, datetime(2026, 1, 5, tzinfo=UTC))
        db.add(
            Stock(
                symbol="AAPL",
                name="Apple Inc.",
                sector="Technology",
                exchange="NASDAQ",
                currency="USD",
            )
        )
        db.commit()
    finally:
        db.close()


def test_list_stocks_returns_envelope_and_pagination(client: TestClient) -> None:
    _seed(client)
    response = client.get("/api/v1/stocks", headers=_auth_headers(client))

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["pagination"]["total"] == 2
    assert [item["symbol"] for item in payload["data"]["items"]] == ["BBCA", "TLKM"]
    assert "as_of" in payload["data"]


def test_list_stocks_search_filters(client: TestClient) -> None:
    _seed(client)
    response = client.get("/api/v1/stocks", params={"search": "telkom"}, headers=_auth_headers(client))

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["symbol"] for item in items] == ["TLKM"]


def test_stock_prices_return_candles_and_provenance(client: TestClient) -> None:
    _seed(client)
    response = client.get("/api/v1/stocks/BBCA/prices", headers=_auth_headers(client))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["symbol"] == "BBCA"
    assert data["data_source"] == "sample"
    assert data["pagination"]["total"] == 3
    assert data["items"][0]["time"]
    assert isinstance(data["items"][0]["close"], int | float)


def test_stock_prices_filter_by_start_date(client: TestClient) -> None:
    _seed(client)
    response = client.get(
        "/api/v1/stocks/BBCA/prices",
        params={"start_date": "2026-01-06"},
        headers=_auth_headers(client),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["pagination"]["total"] == 2
    assert all(item["time"] >= "2026-01-06" for item in data["items"])


def test_stock_prices_unknown_symbol_returns_404(client: TestClient) -> None:
    _seed(client)
    response = client.get("/api/v1/stocks/XXXX/prices", headers=_auth_headers(client))

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["code"] == "SYMBOL_NOT_FOUND"


def test_stock_prices_require_authentication(client: TestClient) -> None:
    _seed(client)
    response = client.get("/api/v1/stocks/BBCA/prices")

    assert response.status_code == 401
    assert response.json()["code"] == "ACCESS_TOKEN_MISSING"