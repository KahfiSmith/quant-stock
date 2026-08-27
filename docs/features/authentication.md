# Feature: Authentication and User Session

## Overview

QuantLens Phase 1 provides registration, login, session bootstrap, logout, account deletion, profile management, preferences settings, and protected profile/settings surfaces. The active backend is `apps/quant-api` (FastAPI).

## Flow

```text
Login -> FastAPI /auth/login -> JWT access token in Zustand
      -> opaque refresh token in HttpOnly cookie
App mount -> /auth/refresh -> token rotation -> restored session
Expired access token -> one shared refresh request -> retry
```

Users have numeric PostgreSQL IDs. Refresh tokens are HMAC-hashed in `sessions` and `refresh_tokens`; a reused rotated token revokes its session. The protected `/settings` route updates display name, theme preference (`light`, `dark`, or `system`), and timezone through `PATCH /api/v1/auth/me`.

## Frontend modules

- Forms: `src/components/features/auth/`
- Settings page: `src/app/(dashboard)/settings/page.tsx`
- Hooks: `src/hooks/auth/`
- Session state: `src/store/auth-store.ts`
- Bootstrap: `src/providers/session-provider.tsx`
- API client and endpoints: `src/lib/api/`
- Safe redirect validation: `src/lib/utils/safe-redirect.ts`

## Backend modules

- Routes: `apps/quant-api/app/api/routes/auth.py`
- Service rules: `apps/quant-api/app/services/auth.py`
- Models/migration: `apps/quant-api/app/models/`, `apps/quant-api/alembic/`
- Tests: `apps/quant-api/tests/test_authentication.py`

Google OAuth, password reset, and email verification are deferred and not presented in the active UI.
