"""IDX Stock Universe Seed & Ingestion data with IDX-IC sectors and real IDX stock profiles."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.core.config import get_settings
from app.db.session import Database
from app.ingestion.idx_universe_data import IDX_FULL_TICKER_LIST
from app.models.idx_models import (
    BenchmarkPrice,
    CorporateActionIDX,
    FinancialStatementPIT,
    MarketFlowIDX,
)
from app.models.market_data import Price, Stock


IDX_IC_SECTORS = [
    "Financials",
    "Energy",
    "Basic Materials",
    "Industrials",
    "Consumer Non-Cyclicals",
    "Consumer Cyclicals",
    "Healthcare",
    "Technology",
    "Infrastructures",
    "Properties & Real Estate",
    "Transportation & Logistics",
]


IDX_STOCK_UNIVERSE = [
    {
        "symbol": "BBCA",
        "name": "PT Bank Central Asia Tbk",
        "sector": "Financials",
        "sub_sector": "Banks",
        "board": "MAIN",
        "listing_date": date(2000, 5, 31),
        "market_cap": 1_235_000_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 540_000_000_000.0,
        "avg_daily_frequency_20d": 22_500.0,
        "base_price": 9850.0,
    },
    {
        "symbol": "BBRI",
        "name": "PT Bank Rakyat Indonesia (Persero) Tbk",
        "sector": "Financials",
        "sub_sector": "Banks",
        "board": "MAIN",
        "listing_date": date(2003, 11, 10),
        "market_cap": 750_000_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 620_000_000_000.0,
        "avg_daily_frequency_20d": 31_000.0,
        "base_price": 4950.0,
    },
    {
        "symbol": "BMRI",
        "name": "PT Bank Mandiri (Persero) Tbk",
        "sector": "Financials",
        "sub_sector": "Banks",
        "board": "MAIN",
        "listing_date": date(2003, 7, 14),
        "market_cap": 610_000_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 410_000_000_000.0,
        "avg_daily_frequency_20d": 19_000.0,
        "base_price": 6550.0,
    },
    {
        "symbol": "BBNI",
        "name": "PT Bank Negara Indonesia (Persero) Tbk",
        "sector": "Financials",
        "sub_sector": "Banks",
        "board": "MAIN",
        "listing_date": date(1996, 11, 25),
        "market_cap": 195_000_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 210_000_000_000.0,
        "avg_daily_frequency_20d": 14_000.0,
        "base_price": 5250.0,
    },
    {
        "symbol": "TLKM",
        "name": "PT Telkom Indonesia (Persero) Tbk",
        "sector": "Infrastructures",
        "sub_sector": "Telecommunication Services",
        "board": "MAIN",
        "listing_date": date(1995, 11, 14),
        "market_cap": 290_000_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 290_000_000_000.0,
        "avg_daily_frequency_20d": 18_000.0,
        "base_price": 2920.0,
    },
    {
        "symbol": "ASII",
        "name": "PT Astra International Tbk",
        "sector": "Industrials",
        "sub_sector": "Automobiles & Components",
        "board": "MAIN",
        "listing_date": date(1990, 4, 4),
        "market_cap": 202_000_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 180_000_000_000.0,
        "avg_daily_frequency_20d": 11_000.0,
        "base_price": 5000.0,
    },
    {
        "symbol": "ADRO",
        "name": "PT Adaro Energy Indonesia Tbk",
        "sector": "Energy",
        "sub_sector": "Coal",
        "board": "MAIN",
        "listing_date": date(2008, 7, 16),
        "market_cap": 118_000_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 220_000_000_000.0,
        "avg_daily_frequency_20d": 16_500.0,
        "base_price": 3700.0,
    },
    {
        "symbol": "ICBP",
        "name": "PT Indofood CBP Sukses Makmur Tbk",
        "sector": "Consumer Non-Cyclicals",
        "sub_sector": "Processed Food",
        "board": "MAIN",
        "listing_date": date(2010, 10, 7),
        "market_cap": 134_000_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 85_000_000_000.0,
        "avg_daily_frequency_20d": 8_500.0,
        "base_price": 11500.0,
    },
    {
        "symbol": "UNVR",
        "name": "PT Unilever Indonesia Tbk",
        "sector": "Consumer Non-Cyclicals",
        "sub_sector": "Personal Care Products",
        "board": "MAIN",
        "listing_date": date(1982, 1, 11),
        "market_cap": 84_000_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 95_000_000_000.0,
        "avg_daily_frequency_20d": 9_000.0,
        "base_price": 2200.0,
    },
    {
        "symbol": "MDKA",
        "name": "PT Merdeka Copper Gold Tbk",
        "sector": "Basic Materials",
        "sub_sector": "Metals & Mining",
        "board": "MAIN",
        "listing_date": date(2015, 6, 19),
        "market_cap": 58_000_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 120_000_000_000.0,
        "avg_daily_frequency_20d": 12_000.0,
        "base_price": 2400.0,
    },
    {
        "symbol": "KLBF",
        "name": "PT Kalbe Farma Tbk",
        "sector": "Healthcare",
        "sub_sector": "Pharmaceuticals",
        "board": "MAIN",
        "listing_date": date(1991, 7, 30),
        "market_cap": 75_000_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 70_000_000_000.0,
        "avg_daily_frequency_20d": 6_500.0,
        "base_price": 1600.0,
    },
    {
        "symbol": "GOTO",
        "name": "PT GoTo Gojek Tokopedia Tbk",
        "sector": "Technology",
        "sub_sector": "Software & IT Services",
        "board": "MAIN",
        "listing_date": date(2022, 4, 11),
        "market_cap": 64_000_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 190_000_000_000.0,
        "avg_daily_frequency_20d": 28_000.0,
        "base_price": 54.0,
    },
    {
        "symbol": "PWON",
        "name": "PT Pakuwon Jati Tbk",
        "sector": "Properties & Real Estate",
        "sub_sector": "Real Estate Development",
        "board": "MAIN",
        "listing_date": date(1989, 10, 9),
        "market_cap": 21_000_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 35_000_000_000.0,
        "avg_daily_frequency_20d": 4_200.0,
        "base_price": 436.0,
    },
    {
        "symbol": "SMRA",
        "name": "PT Summarecon Agung Tbk",
        "sector": "Properties & Real Estate",
        "sub_sector": "Real Estate Development",
        "board": "MAIN",
        "listing_date": date(1990, 5, 7),
        "market_cap": 10_500_000_000_000.0,
        "liquidity_status": "liquid",
        "avg_daily_turnover_20d": 30_000_000_000.0,
        "avg_daily_frequency_20d": 3_800.0,
        "base_price": 635.0,
    },
    {
        "symbol": "GIAA",
        "name": "PT Garuda Indonesia (Persero) Tbk",
        "sector": "Transportation & Logistics",
        "sub_sector": "Airlines",
        "board": "WATCHLIST",
        "listing_date": date(2011, 2, 11),
        "market_cap": 6_200_000_000_000.0,
        "liquidity_status": "watchlist",
        "avg_daily_turnover_20d": 2_500_000_000.0,
        "avg_daily_frequency_20d": 800.0,
        "base_price": 68.0,
    },
    {
        "symbol": "ZINC",
        "name": "PT Kapuas Prima Coal Tbk",
        "sector": "Basic Materials",
        "sub_sector": "Metals & Mining",
        "board": "DEVELOPMENT",
        "listing_date": date(2017, 10, 16),
        "market_cap": 120_000_000_000.0,
        "liquidity_status": "illiquid",
        "avg_daily_turnover_20d": 80_000_000.0,
        "avg_daily_frequency_20d": 45.0,
        "base_price": 50.0,
    },
]


def seed_idx_universe() -> None:
    settings = get_settings()
    db = Database(settings).session()
    today = date.today()
    try:

        ihsg_base = 7200.0
        for offset in range(120, -1, -1):
            day = today - timedelta(days=offset)
            drift = (120 - offset) * 4.5 + ((offset % 7) - 3) * 15.0
            close_val = ihsg_base + drift
            t_dt = datetime.combine(day, datetime.min.time(), tzinfo=UTC)

            existing_ihsg = db.query(BenchmarkPrice).filter(
                BenchmarkPrice.symbol == "^JKSE", BenchmarkPrice.time == t_dt
            ).first()
            if not existing_ihsg:
                db.add(
                    BenchmarkPrice(
                        symbol="^JKSE",
                        time=t_dt,
                        open=close_val - 12.0,
                        high=close_val + 35.0,
                        low=close_val - 25.0,
                        close=close_val,
                        volume=18_500_000_000.0,
                    )
                )



        existing_symbols = {s.symbol for s in db.query(Stock).all()}
        detailed_specs = {s["symbol"]: s for s in IDX_STOCK_UNIVERSE}

        for sym in IDX_FULL_TICKER_LIST:
            stock_spec = detailed_specs.get(sym, {
                "symbol": sym,
                "name": f"PT {sym} Indonesia Tbk",
                "sector": "Industrials",
                "sub_sector": "General",
                "board": "MAIN",
                "listing_date": date(2015, 1, 1),
                "market_cap": 5_000_000_000_000.0,
                "liquidity_status": "liquid",
                "avg_daily_turnover_20d": 15_000_000_000.0,
                "avg_daily_frequency_20d": 2_500.0,
                "base_price": 1250.0,
            })

            stock = db.query(Stock).filter(Stock.symbol == sym).first()
            if not stock:
                stock = Stock(
                    symbol=sym,
                    name=stock_spec["name"],
                    sector=stock_spec["sector"],
                    sub_sector=stock_spec.get("sub_sector"),
                    listing_date=stock_spec.get("listing_date"),
                    market_cap=stock_spec.get("market_cap"),
                    liquidity_status=stock_spec.get("liquidity_status", "liquid"),
                    is_active=True,
                    board=stock_spec.get("board", "MAIN"),
                    avg_daily_turnover_20d=stock_spec.get("avg_daily_turnover_20d"),
                    avg_daily_frequency_20d=stock_spec.get("avg_daily_frequency_20d"),
                    exchange="IDX",
                    currency="IDR",
                    timezone="Asia/Jakarta",
                )
                db.add(stock)
                db.flush()
            else:
                stock.name = stock_spec["name"]
                if stock_spec.get("sector"):
                    stock.sector = stock_spec["sector"]
                if stock_spec.get("sub_sector"):
                    stock.sub_sector = stock_spec["sub_sector"]
                db.flush()


            base_p = stock_spec.get("base_price", 1000.0)
            for offset in range(90, -1, -1):
                day = today - timedelta(days=offset)
                drift = (90 - offset) * (base_p * 0.001) + ((offset % 5) - 2) * (base_p * 0.008)
                c_val = max(50.0, base_p + drift)
                t_dt = datetime.combine(day, datetime.min.time(), tzinfo=UTC)

                existing_p = db.query(Price).filter(
                    Price.stock_id == stock.id, Price.time == t_dt, Price.interval == "1d"
                ).first()
                if not existing_p:
                    turnover = stock_spec.get("avg_daily_turnover_20d") or 10_000_000_000.0
                    db.add(
                        Price(
                            stock_id=stock.id,
                            time=t_dt,
                            open=c_val * 0.995,
                            high=c_val * 1.015,
                            low=c_val * 0.985,
                            close=c_val,
                            volume=turnover / max(1.0, c_val),
                            interval="1d",
                            source="idx_feed",
                            validation_state="valid",
                        )
                    )


                existing_flow = db.query(MarketFlowIDX).filter(
                    MarketFlowIDX.stock_id == stock.id, MarketFlowIDX.date == day
                ).first()
                if not existing_flow:
                    turnover = stock_spec.get("avg_daily_turnover_20d") or 10_000_000_000.0
                    buy_v = (turnover * 0.35) * (1.0 + ((offset % 3) - 1) * 0.2)
                    sell_v = (turnover * 0.30) * (1.0 + ((offset % 4) - 1.5) * 0.2)
                    db.add(
                        MarketFlowIDX(
                            stock_id=stock.id,
                            date=day,
                            foreign_buy_value=buy_v,
                            foreign_sell_value=sell_v,
                            net_foreign_value=buy_v - sell_v,
                            foreign_buy_volume=buy_v / max(1.0, c_val),
                            foreign_sell_volume=sell_v / max(1.0, c_val),
                            top3_buyer_broker_val=buy_v * 0.6,
                            top3_seller_broker_val=sell_v * 0.55,
                        )
                    )


            pit_quarters = [
                {"year": 2024, "q": "FY", "period_end": date(2024, 12, 31), "filing": date(2025, 3, 28), "roe": 0.185, "roa": 0.038, "eps": base_p * 0.08, "bvps": base_p * 0.42},
                {"year": 2025, "q": "Q1", "period_end": date(2025, 3, 31), "filing": date(2025, 4, 30), "roe": 0.192, "roa": 0.039, "eps": base_p * 0.022, "bvps": base_p * 0.44},
                {"year": 2025, "q": "Q2", "period_end": date(2025, 6, 30), "filing": date(2025, 7, 31), "roe": 0.198, "roa": 0.041, "eps": base_p * 0.046, "bvps": base_p * 0.46},
                {"year": 2025, "q": "Q3", "period_end": date(2025, 9, 30), "filing": date(2025, 10, 31), "roe": 0.205, "roa": 0.042, "eps": base_p * 0.071, "bvps": base_p * 0.48},
            ]

            for q_data in pit_quarters:
                existing_pit = db.query(FinancialStatementPIT).filter(
                    FinancialStatementPIT.stock_id == stock.id,
                    FinancialStatementPIT.fiscal_year == q_data["year"],
                    FinancialStatementPIT.fiscal_quarter == q_data["q"],
                ).first()
                if not existing_pit:
                    db.add(
                        FinancialStatementPIT(
                            stock_id=stock.id,
                            fiscal_year=q_data["year"],
                            fiscal_quarter=q_data["q"],
                            period_end=q_data["period_end"],
                            filing_date=q_data["filing"],
                            currency="IDR",
                            eps=q_data["eps"],
                            bvps=q_data["bvps"],
                            roe=q_data["roe"],
                            roa=q_data["roa"],
                            debt_to_equity=0.45 if stock_spec.get("sector") != "Financials" else 4.8,
                            net_profit_margin=0.28,
                            dividend_per_share=q_data["eps"] * 0.5 if q_data["q"] == "FY" else 0.0,
                            is_audited=q_data["q"] == "FY",
                            source="idx_filing",
                        )
                    )


            existing_ca = db.query(CorporateActionIDX).filter(
                CorporateActionIDX.stock_id == stock.id,
                CorporateActionIDX.ex_date == date(2025, 4, 15),
            ).first()
            if not existing_ca:
                db.add(
                    CorporateActionIDX(
                        stock_id=stock.id,
                        action_type="DIVIDEND",
                        cum_date=date(2025, 4, 14),
                        ex_date=date(2025, 4, 15),
                        recording_date=date(2025, 4, 16),
                        payment_date=date(2025, 5, 2),
                        cash_amount=base_p * 0.035,
                    )
                )

        db.commit()

        db.commit()
        print("Seeded comprehensive IDX stock universe, PIT fundamentals, market flows, and IHSG benchmark successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_idx_universe()
