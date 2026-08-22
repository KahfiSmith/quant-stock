# Deployment and Environments

## Active local topology

| Service | URL or port | Responsibility |
| --- | --- | --- |
| Next.js web | `http://localhost:3000` | UI and browser API client |
| FastAPI | `http://localhost:8000` | `/api/v1`, auth, future quant services |
| PostgreSQL/TimescaleDB | `localhost:5432` | relational and future time-series data |

`docker-compose.yml` is the local source of truth. The browser-facing API URL is `NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000`.

## Production requirements

- Run FastAPI behind HTTPS and configure `COOKIE_SECURE=true`.
- Set a single trusted `FRONTEND_ORIGIN` and use the deployment API URL in `NEXT_PUBLIC_BACKEND_API_URL`.
- Replace development JWT and refresh HMAC secrets through a secret manager.
- Apply Alembic migrations as an explicit deployment step.
- Use managed PostgreSQL/TimescaleDB backups and a shared rate limiter before multi-instance deployment.
