"""Timestamp policy helpers.

The QuantLens API persists all timestamps as UTC. The `Price.time` and
`Fundamental.published_at` columns are declared `DateTime(timezone=True)`,
which on PostgreSQL stores the timezone alongside the value.

On SQLite (used in tests), SQLAlchemy strips tzinfo on read by default. This
module provides a normalization helper so application code and tests can rely
on `datetime.tzinfo == UTC` for any timestamp read from the database.

Production policy:
- All writes go through `datetime.now(UTC)` or `.astimezone(UTC)`.
- The collector sets `time` to UTC explicitly via `CollectedPrice.normalized()`.
- The persistence layer never mutates timestamps.
- Reads should be re-attached to UTC when tz is missing (SQLite tests only).
"""
from __future__ import annotations

from datetime import UTC, datetime


def ensure_utc(value: datetime) -> datetime:
    """Return `value` with tzinfo set to UTC. Naive datetimes are tagged UTC.

    Use this at test/UI boundaries when reading timestamps from SQLite, which
    strips tzinfo on read. PostgreSQL preserves tzinfo, so the helper is a
    no-op in production.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
