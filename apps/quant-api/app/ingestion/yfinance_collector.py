"""yfinance-backed MarketDataCollector implementation.

Pulls daily OHLCV and TTM fundamentals from Yahoo Finance for IDX-listed
stocks (suffix `.JK`). See ADR-005-yfinance-provider.md for the design
context and trade-offs.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterable
from datetime import UTC, date, datetime
from decimal import Decimal

import yfinance

from app.ingestion.contracts import (
    CollectedFundamental,
    CollectedPrice,
    CollectionRequest,
)

logger = logging.getLogger(__name__)


def _to_decimal(value: object) -> Decimal | None:
    """Convert a yfinance numeric value to Decimal. Returns None on NaN/missing."""
    if value is None:
        return None
    try:
        as_float = float(value)
    except (TypeError, ValueError):
        return None
    if as_float != as_float:  # NaN check
        return None
    return Decimal(str(as_float))


def _normalize_debt_to_equity(value: Decimal | None) -> Decimal | None:
    """yfinance returns debtToEquity inconsistently across exchanges.

    IDX stocks typically report as a ratio (e.g. 0.8). When the value is
    suspiciously large (> 5), assume the source returned a percentage and
    normalize back to a ratio. Returns None if input is None.
    """
    if value is None:
        return None
    if value > 5:
        return (value / 100).quantize(Decimal("0.0001"))
    return value


def _checksum_for_history(rows: list[dict[str, object]]) -> str:
    """Stable SHA-256 over the canonical row representation.

    Used to detect upstream yfinance revisions on re-ingestion.
    """
    canonical = "|".join(
        f"{r['time'].isoformat()},{r['open']},{r['high']},{r['low']},{r['close']},{r['volume']}"
        for r in rows
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


class StockMetadata(dict):
    """Convenience dict for stock-level metadata fetched from yfinance."""

    @property
    def name(self) -> str | None:
        return self.get("name")  # type: ignore[return-value]

    @property
    def sector(self) -> str | None:
        return self.get("sector")  # type: ignore[return-value]

    @property
    def exchange(self) -> str | None:
        return self.get("exchange")  # type: ignore[return-value]

    @property
    def market_cap(self) -> float | None:
        return self.get("market_cap")  # type: ignore[return-value]

    @property
    def currency(self) -> str:
        return str(self.get("currency") or "IDR")

    @property
    def timezone(self) -> str:
        return str(self.get("timezone") or "Asia/Jakarta")


class YFinanceCollector:
    """Collects OHLCV prices and TTM fundamentals via the yfinance library."""

    name: str = "yfinance"

    def __init__(
        self,
        *,
        timeout: float = 15.0,
        symbol_suffix: str = ".JK",
        proxy: str | None = None,
    ) -> None:
        self.timeout = timeout
        self.symbol_suffix = symbol_suffix
        self.proxy = proxy
        self._session: object | None = None

    def _ticker(self, symbol: str) -> yfinance.Ticker:
        if self._session is None:
            import requests

            self._session = requests.Session()
            if self.proxy:
                self._session.proxies.update(
                    {"http": self.proxy, "https": self.proxy}
                )
        return yfinance.Ticker(symbol, session=self._session)

    def _suffix(self, symbol: str) -> str:
        s = symbol.upper().strip()
        if not s.endswith(self.symbol_suffix):
            s = f"{s}{self.symbol_suffix}"
        return s

    def collect_metadata(self, symbol: str) -> StockMetadata:
        """Fetch stock-level metadata (name, sector, market cap, etc.).

        Separate from collect_fundamentals because metadata is needed even
        when fundamentals are unavailable (KLBF, BRIS historically).
        """
        yf_symbol = self._suffix(symbol)
        try:
            info: dict[str, object] = dict(self._ticker(yf_symbol).info or {})
        except Exception as exc:  # noqa: BLE001
            logger.warning("yfinance info (metadata) failed for %s: %s", yf_symbol, exc)
            return StockMetadata(
                symbol=symbol.upper(),
                name=None,
                sector=None,
                exchange=None,
                market_cap=None,
                currency="IDR",
                timezone="Asia/Jakarta",
            )

        try:
            market_cap_raw = info.get("marketCap")
            market_cap = float(market_cap_raw) if market_cap_raw is not None else None
        except (TypeError, ValueError):
            market_cap = None

        return StockMetadata(
            symbol=symbol.upper(),
            name=info.get("longName") or info.get("shortName") or yf_symbol,
            sector=info.get("sector"),
            exchange=info.get("exchange"),
            market_cap=market_cap,
            currency=str(info.get("currency") or "IDR"),
            timezone=str(info.get("exchangeTimezoneShortName") or "Asia/Jakarta"),
        )

    def collect_prices(
        self, request: CollectionRequest
    ) -> Iterable[CollectedPrice]:
        for symbol in request.symbols:
            yf_symbol = self._suffix(symbol)
            try:
                ticker = self._ticker(yf_symbol)
                df = ticker.history(
                    interval="1d",
                    start=str(request.start_date) if request.start_date else None,
                    end=str(request.end_date) if request.end_date else None,
                    period=None if request.start_date or request.end_date else "2y",
                    auto_adjust=True,
                    timeout=self.timeout,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("yfinance history failed for %s: %s", yf_symbol, exc)
                continue

            if df is None or df.empty:
                logger.info("yfinance returned no rows for %s", yf_symbol)
                continue

            df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
            df = df[~df.index.duplicated(keep="last")]
            df = df.sort_index()

            rows: list[dict[str, object]] = []
            for ts, row in df.iterrows():
                ts_py: datetime = ts.to_pydatetime()
                if ts_py.tzinfo is None:
                    ts_py = ts_py.replace(tzinfo=UTC)
                open_ = _to_decimal(row.get("Open"))
                high = _to_decimal(row.get("High"))
                low = _to_decimal(row.get("Low"))
                close = _to_decimal(row.get("Close"))
                volume = _to_decimal(row.get("Volume"))
                if None in (open_, high, low, close, volume):
                    continue
                rows.append(
                    {
                        "time": ts_py.astimezone(UTC),
                        "open": open_,
                        "high": high,
                        "low": low,
                        "close": close,
                        "volume": volume,
                    }
                )

            if not rows:
                logger.info("yfinance produced no valid rows for %s", yf_symbol)
                continue

            checksum = _checksum_for_history(rows)
            retrieved_at = datetime.now(UTC)

            for r in rows:
                yield CollectedPrice(
                    symbol=symbol.upper(),
                    time=r["time"],  # type: ignore[arg-type]
                    open=r["open"],  # type: ignore[arg-type]
                    high=r["high"],  # type: ignore[arg-type]
                    low=r["low"],  # type: ignore[arg-type]
                    close=r["close"],  # type: ignore[arg-type]
                    volume=r["volume"],  # type: ignore[arg-type]
                    interval="1d",
                    source=self.name,
                    source_record_id=yf_symbol,
                    retrieved_at=retrieved_at,
                    payload_checksum=checksum,
                )

    def collect_fundamentals(
        self, request: CollectionRequest
    ) -> Iterable[CollectedFundamental]:
        today = date.today()
        retrieved_at = datetime.now(UTC)
        for symbol in request.symbols:
            yf_symbol = self._suffix(symbol)
            try:
                info: dict[str, object] = dict(self._ticker(yf_symbol).info or {})
            except Exception as exc:  # noqa: BLE001
                logger.warning("yfinance info failed for %s: %s", yf_symbol, exc)
                continue

            if not info:
                logger.info("yfinance returned empty info for %s", yf_symbol)
                continue

            pe = _to_decimal(info.get("trailingPE"))
            pb = _to_decimal(info.get("priceToBook"))
            roe = _to_decimal(info.get("returnOnEquity"))
            roa = _to_decimal(info.get("returnOnAssets"))
            de_raw = _to_decimal(info.get("debtToEquity"))
            de = _normalize_debt_to_equity(de_raw)
            rev_g = _to_decimal(info.get("revenueGrowth"))
            eps_g = _to_decimal(info.get("earningsGrowth"))

            metrics: dict[str, Decimal | None] = {
                "pe_ratio": pe,
                "pb_ratio": pb,
                "roe": roe,
                "roa": roa,
                "debt_to_equity": de,
                "revenue_growth": rev_g,
                "eps_growth": eps_g,
            }

            if all(v is None for v in metrics.values()):
                logger.info("yfinance info for %s has no usable metrics", yf_symbol)
                continue

            canonical = f"{yf_symbol}|{sorted((k, str(v)) for k, v in metrics.items() if v is not None)}"
            checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]

            yield CollectedFundamental(
                symbol=symbol.upper(),
                period_end=today,
                published_at=retrieved_at,
                currency=str(info.get("currency") or "IDR"),
                period_type="TTM",
                metrics=metrics,
                source=self.name,
                source_record_id=f"{yf_symbol}:info",
                retrieved_at=retrieved_at,
                payload_checksum=checksum,
            )
