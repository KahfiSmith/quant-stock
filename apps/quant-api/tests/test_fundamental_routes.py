from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from app.models.fundamental import Fundamental
from app.models.market_data import Stock


def _make_stock(db, symbol: str, name: str) -> Stock:
    stock = Stock(symbol=symbol, name=name, sector="Financials", exchange="IDX", currency="IDR")
    db.add(stock)
    db.flush()
    return stock


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


def test_get_stock_fundamental_success(client: TestClient) -> None:
    db = client.app.state.database.session()
    try:
        stock = _make_stock(db, "BBCA", "Bank Central Asia")
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
            currency="IDR",
            source_record_id="fixture:BBCA:2025-12-31:TTM",
            retrieved_at=datetime(2026, 2, 2, tzinfo=UTC),
            payload_checksum="fixture-checksum",
            validation_state="valid",
        )
        db.add(fund)
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/stocks/BBCA/fundamental", headers=_auth_headers(client))
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["symbol"] == "BBCA"
    assert data["period_end"] == "2025-12-31"
    assert data["score"] == 82.5
    assert data["ratios"]["pe_ratio"] == 18.5
    assert data["ratios"]["roe"] == 0.21
    assert data["currency"] == "IDR"
    assert data["source"] == "sample"
    assert data["source_record_id"] == "fixture:BBCA:2025-12-31:TTM"
    assert data["retrieved_at"].startswith("2026-02-02T00:00:00")
    assert data["payload_checksum"] == "fixture-checksum"
    assert data["validation_state"] == "valid"



def test_get_stock_fundamental_not_found(client: TestClient) -> None:
    db = client.app.state.database.session()
    try:
        _make_stock(db, "TLKM", "Telkom Indonesia")
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/stocks/TLKM/fundamental", headers=_auth_headers(client))
    assert response.status_code == 404
    assert response.json()["code"] == "FUNDAMENTAL_NOT_FOUND"
