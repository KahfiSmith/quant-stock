from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient

from app.models.fundamental import Fundamental
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


def test_get_stock_ai_summary(client: TestClient) -> None:
    headers = _auth_headers(client)

    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "BBCA", "Bank Central Asia")
        _make_candles(db, stock, datetime(2026, 1, 1, tzinfo=UTC), count=35)
        fund = Fundamental(
            stock_id=stock.id,
            period_end=date(2025, 12, 31),
            published_at=datetime(2026, 2, 1, tzinfo=UTC),
            period_type="TTM",
            pe_ratio=18.5,
            pb_ratio=4.2,
            roe=0.21,
            roa=0.035,
            debt_to_equity=0.8,
            revenue_growth=0.12,
            eps_growth=0.15,
            score=82.5,
            source="sample",
        )
        db.add(fund)
        db.commit()
    finally:
        db.close()

    res = client.get("/api/v1/stocks/BBCA/ai-summary", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["symbol"] == "BBCA"
    assert len(data["strengths"]) > 0
    assert len(data["risks"]) > 0
    assert len(data["unknowns"]) > 0
    assert "disclaimer" in data
    assert "not constitute financial" in data["disclaimer"].lower()


def test_ai_summary_does_not_claim_unavailable_data(client: TestClient) -> None:
    headers = _auth_headers(client)

    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "BBRI", "Bank Rakyat Indonesia")
        _make_candles(db, stock, datetime(2026, 1, 1, tzinfo=UTC), count=35)
        db.commit()
    finally:
        db.close()

    res = client.get("/api/v1/stocks/BBRI/ai-summary", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    statements = " ".join(data["strengths"] + data["risks"] + [data["conclusion"]]).lower()
    assert "ma50" not in statements
    assert "ma200" not in statements
    assert "sound fundamentals" not in statements
    assert any("fundamental" in unknown.lower() for unknown in data["unknowns"])
