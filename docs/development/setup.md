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
