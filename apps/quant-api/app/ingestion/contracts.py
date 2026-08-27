from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class CollectionRequest:
    symbols: Sequence[str]
    start_date: date | None
    end_date: date | None
    interval: str = "1d"


@dataclass(frozen=True)
class CollectedPrice:
    symbol: str
    time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    interval: str
    source: str
    source_record_id: str | None = None
    retrieved_at: datetime | None = None
    payload_checksum: str | None = None

    def normalized(self) -> "CollectedPrice":
        return CollectedPrice(
            symbol=self.symbol.upper(),
            time=self.time.astimezone(UTC) if self.time.tzinfo else self.time.replace(tzinfo=UTC),
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
            interval=self.interval,
            source=self.source,
            source_record_id=self.source_record_id,
            retrieved_at=self.retrieved_at,
            payload_checksum=self.payload_checksum,
        )


@dataclass(frozen=True)
class CollectedFundamental:
    symbol: str
    period_end: date
    published_at: datetime
    currency: str
    period_type: str
    metrics: dict[str, Decimal | None]
    source: str
    source_record_id: str
    retrieved_at: datetime
    payload_checksum: str | None = None


class MarketDataCollector(Protocol):
    name: str

    def collect_prices(self, request: CollectionRequest) -> Iterable[CollectedPrice]: ...

    def collect_fundamentals(
        self, request: CollectionRequest
    ) -> Iterable[CollectedFundamental]: ...
