# Security Overview

## Trust boundary

```text
browser
  -> Next.js frontend (in-memory access token)
     -> FastAPI API at /api/v1
        -> PostgreSQL/TimescaleDB (users, sessions, token history)
```


## Authentication

- Access tokens are JWTs, short-lived, and stored only in the non-persisted Zustand store.
- Refresh tokens are opaque random values in an `HttpOnly` cookie; JavaScript cannot read them.
- The API persists only HMAC-SHA256 token hashes and rotates refresh tokens on every use.
- Reuse of an already-used refresh token revokes its session family.
- Passwords are hashed with Argon2 through `pwdlib`.
- Login, refresh, logout, registration, and account deletion validate browser origins. CORS uses an explicit frontend allowlist and credentials.
- Development rate limiting is in-memory; production must replace it with a shared limiter such as Redis or an edge gateway.

## Authorization

The frontend client guard is UX only. FastAPI verifies Bearer tokens on protected endpoints and must enforce resource ownership for future portfolios and market-data features.

## Route protection

`/profile` remains client-guarded while session bootstrap completes. Future server-rendered protected routes require a documented server-side session strategy; they must not trust client-only state.

## Operational rules

Set `COOKIE_SECURE=true` and use HTTPS in production. Set a specific `FRONTEND_ORIGIN`, replace development secrets, and never log passwords, access tokens, refresh tokens, or raw provider credentials.
