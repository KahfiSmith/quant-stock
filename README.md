# QuantLens

Next.js App Router client with a FastAPI authentication service and a TimescaleDB/PostgreSQL data foundation.

## Security & Auth Architecture

- **Access Token**: In-memory only via non-persisted Zustand store (`useAuthStore`).
- **Refresh Token**: Managed via `HttpOnly` secure cookies set by the FastAPI backend. JavaScript cannot access the refresh token.
- **Session Bootstrap**: On application mount, `SessionProvider` triggers `POST /api/v1/auth/refresh` using `authClient` (`withCredentials: true`) to restore the in-memory access token.
- **Single-Flight Refresh**: Concurrent `401 ACCESS_TOKEN_EXPIRED` requests are merged into a single shared refresh promise via `refreshAccessToken()`.
- **Axios Clients**: `authClient` (for auth endpoints with credentials) and `apiClient` (for business endpoints with Bearer tokens).

## Quick Start

```bash
# 1. Start all services (frontend + backend + database)
docker compose up -d

# 2. Apply database migrations
docker compose exec quant-api alembic upgrade head

# 3. Backfill foreign flow + broker summary dari idx.co.id (~5-10 menit)
docker compose exec quant-api python -m scripts.backfill_idx_data --range 30

# 4. Backfill OHLCV + fundamentals dari Yahoo Finance (~2-5 menit)
docker compose exec quant-api python -m scripts.backfill_market_data
```

Frontend: `http://localhost:3000` | Backend API: `http://localhost:8000`

> **Tip**: Kalau step 4 kena `429 Too Many Requests`, tunggu 30 menit lalu retry
> dengan batch kecil: `--symbols BBCA,BMRI,BBRI,TLKM,ASII --rate-limit-seconds 8.0`.
> Step 3 (idx.co.id) tidak terpengaruh. Lihat [setup docs](docs/development/setup.md)
> untuk detail troubleshooting.

### Daily Update (setelah market tutup)

```bash
docker compose exec quant-api python -m scripts.backfill_market_data
docker compose exec quant-api python -m scripts.backfill_idx_data
```

### Frontend-Only Development

```bash
pnpm install
cp .env.example .env.local
pnpm dev
```

## Quality Checks

```bash
pnpm lint
pnpm type-check
pnpm docs:check
pnpm build

pnpm verify:all   
```

## Documentation

- [Documentation index](docs/README.md) - Architecture, API, security, conventions, development, and more.
- A pre-commit hook runs `pnpm verify:fast` (lint + type-check + docs:check) automatically on commit.
- GitHub Actions CI runs lint, type-check, docs, build, and risk classification on every push/PR.
