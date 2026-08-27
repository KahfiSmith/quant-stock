# Secrets Management & Security Rules

## Secrets

### Rules

- Secrets must never be prefixed with `NEXT_PUBLIC_`.
- Public configurations live in `.env.example`.
- Sensitive local credentials are stored in `.env.local` (git-ignored).
- Never commit secrets.

### Environment variables

| Variable | Public | Default | Notes |
|---|---|---|---|
| `NEXT_PUBLIC_BACKEND_API_URL` | yes | `http://localhost:8000` | Backend base URL; read by the Axios clients |
| `AI_ANALYST_API_KEY` | no | _(unset)_ | Optional API key for the LLM provider. Empty = no LLM call (rule-based). Currently unused for actual LLM calls; the AI Analyst code path is deterministic. |
| `YFINANCE_PROXY` | no | _(unset)_ | Optional HTTP proxy URL for the yfinance collector. yfinance itself does not require a key, but a proxy may be needed in restricted networks. |

When additional server-only secrets are added, they must be non-prefixed
variables and must never appear in client bundles. The market data
provider (yfinance) does not require a key, so no new credential is
introduced by the yfinance integration (see ADR-005).

## Security rules and enforcement

1. Never commit secrets.
2. Never log credentials or tokens.
3. Validate user input with Zod prior to API call.

| Rule | Where it lives |
|---|---|
| Never commit secrets | `.gitignore` for `.env.local`; `.env.example` holds only public vars |
| Never log credentials/tokens | `eslint.config.mjs` `no-console` warn; `handleQueryError` logs only in development |
| Validate input with Zod | `src/lib/schemas/auth.schema.ts` + `@hookform/resolvers/zod` in forms |
