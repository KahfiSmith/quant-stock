"""HTTP client for the Indonesia Stock Exchange (idx.co.id) public data API.

The IDX website requires a session cookie obtained by visiting the homepage.
This client handles cookie bootstrapping, exponential retry on transient errors,
and per-request rate limiting to avoid overwhelming the public endpoints.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from base64 import b64encode
from datetime import date, datetime
from typing import Any

import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

_BASE = "https://www.idx.co.id"
_BROWSER_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
    "Referer": f"{_BASE}/",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
}


class IDXClient:
    """Thin HTTP wrapper around idx.co.id public JSON endpoints."""

    def __init__(
        self,
        *,
        max_retries: int = 4,
        rate_limit_seconds: float = 1.5,
        timeout: int = 30,
    ) -> None:
        self._max_retries = max_retries
        self._rate_limit = rate_limit_seconds
        self._timeout = timeout
        self._cookie: str = ""
        self._last_request_at: float = 0.0

    def _ensure_session(self) -> None:
        if self._cookie:
            return
        logger.info("IDX: bootstrapping session cookie …")
        req = urllib.request.Request(f"{_BASE}/id", headers=_BROWSER_HEADERS)
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            cookies = resp.headers.get_all("Set-Cookie") or []
            self._cookie = "; ".join(
                c.split(";")[0] for c in cookies if c
            )
        time.sleep(1.0)

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        remaining = self._rate_limit - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_request_at = time.monotonic()

    def _fetch_json(self, url: str) -> Any | None:
        self._ensure_session()
        self._throttle()
        headers = {**_BROWSER_HEADERS, "Cookie": self._cookie}
        for attempt in range(1, self._max_retries + 1):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    return json.loads(resp.read().decode())
            except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
                status = getattr(exc, "code", None)
                if status == 429:
                    delay = min(5.0 * attempt, 30.0)
                    logger.warning("IDX: 429 rate-limited, sleeping %.1fs (attempt %d)", delay, attempt)
                elif status and 400 <= status < 500 and status != 429:
                    logger.warning("IDX: client error %d for %s — skipping", status, url)
                    return None
                else:
                    delay = min(2.0 ** attempt, 20.0)
                    logger.warning("IDX: request error for %s (attempt %d): %s", url, attempt, exc)
                time.sleep(delay if "delay" in dir() else min(2.0 ** attempt, 20.0))
            except json.JSONDecodeError:
                logger.warning("IDX: invalid JSON from %s", url)
                return None
        logger.error("IDX: exhausted retries for %s", url)
        return None

    def get_stock_summary(self, trade_date: date) -> list[dict[str, Any]]:
        """Fetch daily trading summary for all stocks on a given date.

        Returns per-stock OHLCV, foreign buy/sell, bid/ask, trading frequency.
        """
        date_str = trade_date.strftime("%Y%m%d")
        raw = self._fetch_json(
            f"{_BASE}/primary/TradingSummary/GetStockSummary?date={date_str}"
        )
        if not raw or not isinstance(raw.get("data"), list):
            return []
        return raw["data"]

    def get_broker_summary(
        self,
        trade_date: date,
        start: int = 0,
        length: int = 9999,
    ) -> list[dict[str, Any]]:
        """Fetch broker-level trading summary for a given date."""
        date_str = trade_date.strftime("%Y%m%d")
        raw = self._fetch_json(
            f"{_BASE}/primary/TradingSummary/GetBrokerSummary"
            f"?length={length}&start={start}&date={date_str}"
        )
        if not raw or not isinstance(raw.get("data"), list):
            return []
        return raw["data"]

    def get_foreign_trading_summary(
        self, year: int, month: int
    ) -> list[dict[str, Any]]:
        """Fetch monthly foreign investor daily trading metrics."""
        query = json.dumps(
            {"year": str(year), "month": str(month), "quarter": 0, "type": "monthly"}
        )
        q_b64 = b64encode(query.encode()).decode()
        raw = self._fetch_json(
            f"{_BASE}/primary/DigitalStatistic/GetApiData"
            f"?urlName=LINK_TABLE_DAILY_TRADING_INVESTOR_FOREIGN"
            f"&query={q_b64}&isPrint=False&cumulative=false"
        )
        if not raw or not isinstance(raw.get("data"), list):
            return []
        return raw["data"]


def checksum_for_record(data: dict[str, Any]) -> str:
    raw = json.dumps(data, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()[:16]
