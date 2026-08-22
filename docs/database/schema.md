# Database Schema

QuantLens uses PostgreSQL with the TimescaleDB extension. FastAPI owns migrations through Alembic in `apps/quant-api/alembic`.

## Authentication tables

- `users`: numeric auto-increment `id`, unique email, Argon2 password hash, profile fields, active/verification flags, timestamps.
- `sessions`: numeric ID, numeric `user_id`, refresh-token family ID, client metadata, expiry, and revocation timestamp.
- `refresh_tokens`: numeric ID, session ID, unique HMAC token hash, expiry, and `used_at` rotation marker.

The first migration is `0001_authentication`. Refresh tokens are never stored in raw form. A reused token revokes the related session.

## Future market-data tables

Phase 2 adds `stocks` and a TimescaleDB `prices` hypertable. Phase 1 does not yet ingest or expose market data.

## Migration workflow

1. Change SQLAlchemy models in `apps/quant-api/app/models`.
2. Create and review an Alembic migration.
3. Update Pydantic schemas and frontend types when the API contract changes.
4. Apply migrations with `alembic upgrade head`.
5. Test upgrade and rollback behavior before shared deployment.
