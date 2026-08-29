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

The `prices.source` field carries data provenance:
- `"yfinance"` for real IDX market data ingested via the
  [yfinance collector](../../apps/quant-api/app/ingestion/yfinance_collector.py)
  (see [ADR-005](../architecture/adr/ADR-005-yfinance-provider.md)).
- `"sample"` for the legacy 15-day synthetic seeder; still queryable for
  offline development but not the active data source by default.

The `fundamentals.source` column follows the same convention.

## Portfolio & transaction tables

Migrations `0004_portfolios`, `0005_transaction_constraints`, `0008_user_preferences`, and `0009_unique_lookup_indexes` add portfolio management and schema integrity alignment:

Portfolio detail derives weighted-average realized/unrealized PnL and a deterministic
risk summary from transactions and available daily prices; no separate holdings table
is required by the active implementation.

- `portfolios`: numeric `id`, `user_id` (FK to `users`), unique per user `name`, `currency`, and timestamps.
- `transactions`: numeric `id`, `portfolio_id` (FK to `portfolios`), `stock_id` (FK to `stocks`), `transaction_type` (`BUY` or `SELL`), `quantity`, `price`, `fee`, `transacted_at`, and `created_at`. Database checks enforce valid type, positive quantity/price, and non-negative fees.

Migration `0008_user_preferences` adds `users.theme_preference` (`light`, `dark`, or `system`) and `users.timezone`.

## Backtest jobs table

Migration `0010_backtest_jobs` adds persistent backtest execution tracking:

- `backtest_jobs`: string primary key `id` (UUID), `user_id` (FK to `users`), `symbol`, `strategy`, `status` (`queued`, `running`, `succeeded`, `failed`), `initial_capital`, `parameters` (JSON), `start_date`, `end_date`, `summary` (JSON), `equity_curve` (JSON), `metadata` (JSON), `error_message`, `retry_count`, `created_at`, `started_at`, and `finished_at`.

## IDX Specialized Architecture Tables

Migration `0011_idx_platform_architecture` adds specialized data structures for Indonesian listed equities (Bursa Efek Indonesia):

- `stocks` (extended): adds `sub_sector` (IDX-IC), `listing_date`, `liquidity_status` (`liquid`, `watchlist`, `illiquid`), `is_active` (`bool`), `board` (`MAIN`, `DEVELOPMENT`, `ACCELERATION`, `WATCHLIST`), `avg_daily_turnover_20d`, `avg_daily_frequency_20d`.
- `financial_statements_pit`: Point-in-Time financial statements strictly indexed by `filing_date` (release date to public) to prevent look-ahead bias in historical simulations. Stores quarterly `revenue`, `net_income`, `eps`, `bvps`, `roe`, `roa`, `debt_to_equity`, `net_profit_margin`, `dividend_per_share`, and `is_audited`.
- `market_flows_idx`: Daily Indonesian foreign fund flow & broker summary tracking (`foreign_buy_value`, `foreign_sell_value`, `net_foreign_value`, `top3_buyer_broker_val`, `top3_seller_broker_val`).
- `corporate_actions_idx`: Corporate actions on IDX (`DIVIDEND`, `STOCK_SPLIT`, `RIGHT_ISSUE`) with `cum_date`, `ex_date`, `ratio_from`, `ratio_to`, `cash_amount`, `exercise_price`.
- `benchmark_prices`: Historical daily prices for Indonesian benchmark indices (`^JKSE` / IHSG, IDX Sectoral Indices).
- `strategy_definitions`: Quantitative factor strategy catalog & preset weighting definitions.
- `idx_factor_rotation_backtests`: Historical simulation results for multi-asset monthly/periodic factor rotation across BEI universe.

1. Change SQLAlchemy models in `apps/quant-api/app/models`.
2. Create and review an Alembic migration.
3. Update Pydantic schemas and frontend types when the API contract changes.
4. Apply migrations with `alembic upgrade head`.
5. Test upgrade and rollback behavior before shared deployment.
