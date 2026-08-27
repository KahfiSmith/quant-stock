from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient

from app.models.fundamental import Fundamental
from app.models.market_data import Price, Stock


def _make_stock(db, symbol: str, name: str, sector: str = "Financials") -> Stock:
    stock = Stock(symbol=symbol, name=name, sector=sector, exchange="IDX", currency="IDR")
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


def test_screener_filters_and_sorts(client: TestClient) -> None:
    db = client.app.state.database.session()
    try:
        bbca = _make_stock(db, "BBCA", "Bank Central Asia", "Financials")
        _make_candles(db, bbca, datetime(2026, 1, 1, tzinfo=UTC), count=35)
        fund_bbca = Fundamental(
            stock_id=bbca.id,
            period_end=date(2025, 12, 31),
            published_at=datetime(2026, 2, 1, tzinfo=UTC),
            period_type="TTM",
            pe_ratio=18.5,
            pb_ratio=4.2,
            roe=0.21,
            debt_to_equity=0.8,
            revenue_growth=0.12,
            eps_growth=0.15,
            score=82.5,
            source="sample",
        )
        db.add(fund_bbca)

        tlkm = _make_stock(db, "TLKM", "Telkom Indonesia", "Infrastructure")
        _make_candles(db, tlkm, datetime(2026, 1, 1, tzinfo=UTC), count=35)
        fund_tlkm = Fundamental(
            stock_id=tlkm.id,
            period_end=date(2025, 12, 31),
            published_at=datetime(2026, 2, 1, tzinfo=UTC),
            period_type="TTM",
            pe_ratio=14.0,
            pb_ratio=2.5,
            roe=0.18,
            debt_to_equity=0.9,
            revenue_growth=0.05,
            eps_growth=0.08,
            score=75.0,
            source="sample",
        )
        db.add(fund_tlkm)
        db.commit()
    finally:
        db.close()

    # 1. Test sector filter
    resp = client.post(
        "/api/v1/screener",
        json={"sector": "Financials", "sort_by": "score", "sort_order": "desc"},
        headers=_auth_headers(client),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 1
    assert data["items"][0]["symbol"] == "BBCA"

    # 2. Test min_roe filter
    resp2 = client.post(
        "/api/v1/screener",
        json={"min_roe": 0.20},
        headers=_auth_headers(client),
    )
    assert resp2.status_code == 200
    data2 = resp2.json()["data"]
    assert len(data2["items"]) == 1
    assert data2["items"][0]["symbol"] == "BBCA"
    assert data2["items"][0]["close_price"] == 9390.0


def test_screener_rejects_reversed_ranges(client: TestClient) -> None:
    headers = _auth_headers(client)
    res = client.post(
        "/api/v1/screener",
        json={"min_score": 90, "max_score": 10},
        headers=headers,
    )
    assert res.status_code == 422
    assert res.json()["code"] == "VALIDATION_ERROR"


def test_screener_close_price_is_latest_close_without_ma20(client: TestClient) -> None:
    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "BBRI", "Bank Rakyat Indonesia")
        _make_candles(db, stock, datetime(2026, 1, 1, tzinfo=UTC), count=30)
        db.commit()
    finally:
        db.close()

    resp = client.post(
        "/api/v1/screener",
        json={},
        headers=_auth_headers(client),
    )
    assert resp.status_code == 200
    item = next(item for item in resp.json()["data"]["items"] if item["symbol"] == "BBRI")
    assert item["close_price"] == 9340.0
