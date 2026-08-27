# Database Schema

QuantLens uses PostgreSQL with the TimescaleDB extension. FastAPI owns migrations through Alembic in `apps/quant-api/alembic`.

## Authentication tables

- `users`: numeric auto-increment `id`, unique email, Argon2 password hash, profile fields, active/verification flags, timestamps.
- `sessions`: numeric ID, numeric `user_id`, refresh-token family ID, client metadata, expiry, and revocation timestamp.
- `refresh_tokens`: numeric ID, session ID, unique HMAC token hash, expiry, and `used_at` rotation marker.

The first migration is `0001_authentication`. Refresh tokens are never stored in raw form. A reused token revokes the related session.

## Market data & fundamentals tables

Migrations `0002_market_data`, `0003_fundamentals`, `0006_fundamental_provenance`, and `0007_price_provenance` add market data and fundamental records:

- `stocks`: numeric `id`, unique indexed `symbol`, `name`, optional `sector`,
  `market_cap`, `exchange`, `currency`, `timezone`, and timestamps.
- `prices`: numeric `id`, `stock_id` (FK to `stocks`), `time`
  (`TIMESTAMPTZ`), OHLC `open/high/low/close`, `volume`, `interval`, `source`,
  source-record identifier, retrieval time, payload checksum, validation state,
  and `created_at`. A unique constraint on `(stock_id, time, interval, source)`
  is the canonical idempotency key. On PostgreSQL the table is created as a
  TimescaleDB hypertable partitioned on `time`; on other dialects (SQLite
  tests) it is a plain table.
- `fundamentals`: numeric `id`, `stock_id` (FK to `stocks`), `period_end` (Date),
  `period_type` (e.g. `TTM`), valuation/profitability/growth ratios (`pe_ratio`, `pb_ratio`,
  `roe`, `roa`, `debt_to_equity`, `revenue_growth`, `eps_growth`), composite `score`,
  `source`, currency, source-record identifier, retrieval time, payload checksum,
  validation state, and `created_at`. Unique on `(stock_id, period_end, period_type)`.
  Legacy sample rows may be flagged when `published_at` is unavailable.

The `prices.source` field carries data provenance (`sample` for seeded
placeholder rows). Real ingestion is deferred pending a data-provider decision.

## Portfolio & transaction tables

Migrations `0004_portfolios`, `0005_transaction_constraints`, `0008_user_preferences`, and `0009_unique_lookup_indexes` add portfolio management and schema integrity alignment:

Portfolio detail derives weighted-average realized/unrealized PnL and a deterministic
risk summary from transactions and available daily prices; no separate holdings table
is required by the active implementation.

- `portfolios`: numeric `id`, `user_id` (FK to `users`), unique per user `name`, `currency`, and timestamps.
- `transactions`: numeric `id`, `portfolio_id` (FK to `portfolios`), `stock_id` (FK to `stocks`), `transaction_type` (`BUY` or `SELL`), `quantity`, `price`, `fee`, `transacted_at`, and `created_at`. Database checks enforce valid type, positive quantity/price, and non-negative fees.

Migration `0008_user_preferences` adds `users.theme_preference` (`light`, `dark`, or `system`) and `users.timezone`.

1. Change SQLAlchemy models in `apps/quant-api/app/models`.
2. Create and review an Alembic migration.
3. Update Pydantic schemas and frontend types when the API contract changes.
4. Apply migrations with `alembic upgrade head`.
5. Test upgrade and rollback behavior before shared deployment.
