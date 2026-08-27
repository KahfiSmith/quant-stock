# Testing Conventions

## Current status

Vitest is configured with a `test` script (`pnpm test`) and a jsdom
environment. Focused tests cover the authentication flow:

- **Schemas**: Zod validation states in `src/lib/schemas/*.test.ts`.
- **Hooks**: mutation success/error paths for `useLogin`, `useLogout`,
  `useRegister`, `useDeleteAccount`.
- **API layer**: `apiClient` interceptor behavior (envelope unwrap, bearer-token
  attach, single-flight refresh, `_retry`).
- **Route guards**: `RequireAuth` / `RedirectAuthenticated` render and redirect
  behavior.
- **Domain contracts**: settings preferences, quant metadata, portfolio accounting/risk,
  backtest reproducibility/anti-bias behavior, AI evidence, and ingestion validation.
- **AI evaluation**: deterministic structured-output, evidence, unavailable-data,
  disclaimer, and safety-contract tests; no external LLM or licensed-news provider is configured.

A test script is wired into `verify` and `verify:all`. The full quality gates are:

```bash
pnpm lint
pnpm type-check
pnpm docs:check
pnpm test
pnpm build
```

## When more tests are needed

Add focused tests when new behavior requires them. Run tests via `pnpm test`
(or `pnpm test:watch` while developing):

- **Components**: render and interaction checks for feature components
  (e.g. form validation states, logout button).
- **Hooks**: mutation success/error paths for auth and future domain hooks.
- **API layer**: interceptor behavior (unwrap, single-flight refresh, `_retry`).
