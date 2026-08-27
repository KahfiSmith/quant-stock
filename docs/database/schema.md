# Database Schema

QuantLens uses PostgreSQL with the TimescaleDB extension. FastAPI owns migrations through Alembic in `apps/quant-api/alembic`.

## Authentication tables

- `users`: numeric auto-increment `id`, unique email, Argon2 password hash, profile fields, active/verification flags, timestamps.
- `sessions`: numeric ID, numeric `user_id`, refresh-token family ID, client metadata, expiry, and revocation timestamp.
- `refresh_tokens`: numeric ID, session ID, unique HMAC token hash, expiry, and `used_at` rotation marker.

The first migration is `0001_authentication`. Refresh tokens are never stored in raw form. A reused token revokes the related session.

## Market data & fundamentals tables

Migration `0002_market_data` and `0003_fundamentals` add market data and fundamental records:

- `stocks`: numeric `id`, unique indexed `symbol`, `name`, optional `sector`,
  `market_cap`, `exchange`, `currency`, `timezone`, and timestamps.
- `prices`: numeric `id`, `stock_id` (FK to `stocks`), `time`
  (`TIMESTAMPTZ`), OHLC `open/high/low/close`, `volume`, `interval`, `source`,
  and `created_at`. A unique constraint on `(stock_id, time, interval, source)`
  is the canonical idempotency key. On PostgreSQL the table is created as a
  TimescaleDB hypertable partitioned on `time`; on other dialects (SQLite
  tests) it is a plain table.
- `fundamentals`: numeric `id`, `stock_id` (FK to `stocks`), `period_end` (Date),
  `period_type` (e.g. `TTM`), valuation/profitability/growth ratios (`pe_ratio`, `pb_ratio`,
  `roe`, `roa`, `debt_to_equity`, `revenue_growth`, `eps_growth`), composite `score`,
  `source`, and `created_at`. Unique on `(stock_id, period_end, period_type)`.

The `prices.source` field carries data provenance (`sample` for seeded
placeholder rows). Real ingestion is deferred pending a data-provider decision.

## Portfolio & transaction tables

Migration `0004_portfolios` adds portfolio management:

- `portfolios`: numeric `id`, `user_id` (FK to `users`), unique per user `name`, `currency`, and timestamps.
- `transactions`: numeric `id`, `portfolio_id` (FK to `portfolios`), `stock_id` (FK to `stocks`), `transaction_type` (`BUY` or `SELL`), `quantity`, `price`, `fee`, `transacted_at`, and `created_at`.

1. Change SQLAlchemy models in `apps/quant-api/app/models`.
2. Create and review an Alembic migration.
3. Update Pydantic schemas and frontend types when the API contract changes.
4. Apply migrations with `alembic upgrade head`.
5. Test upgrade and rollback behavior before shared deployment.
