# Developer Setup and Commands

## Prerequisites

- Node.js 20+ and pnpm 10.x
- Python 3.12 for host-mode FastAPI development, or Docker with Compose

## Local stack

```bash
cp .env.example .env.local
docker compose up --build
```

This starts the Next.js frontend at `http://localhost:3000`, FastAPI at `http://localhost:8000`, and PostgreSQL with TimescaleDB at `localhost:5432`. The API applies Alembic migrations before starting.

For frontend-only development, run `pnpm dev` and ensure `NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000` is configured.

For API host-mode development:

```bash
cd apps/quant-api
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --port 8000
```

## Verification

- Frontend: `pnpm lint`, `pnpm type-check`, `pnpm docs:check`
- API: `.venv/bin/ruff check .`, `.venv/bin/pytest -q`
- Service endpoints: `GET /health`, `GET /ready`

## Ingesting real market data

After a fresh stack start, the `stocks` table is empty and the screener will
show no data. Populate it with real IDX data via the yfinance backfill
(see [ADR-005](../architecture/adr/ADR-005-yfinance-provider.md) for context):

```bash
# 1. Make sure the DB is up and migrations applied.
docker compose up -d db
cd apps/quant-api
.venv/bin/alembic upgrade head

# 2. Run the backfill (20 IDX stocks × ~500 daily bars, ~2 minutes with rate limit).
.venv/bin/python -m scripts.backfill_market_data

# Override the symbol list, period, or skip fundamentals:
.venv/bin/python -m scripts.backfill_market_data --symbols BBCA,BMRI,TLKM --period 5y
.venv/bin/python -m scripts.backfill_market_data --skip-fundamentals
```

To re-run safely (idempotent UPSERT), just invoke the same command again.
To temporarily fall back to synthetic 15-day data (e.g. for offline
development), set `MARKET_DATA_PROVIDER=sample` in
`apps/quant-api/.env` and run `python -m scripts.seed_market_data`.
