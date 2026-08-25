# ADR-004: Frontend Stays at the Repository Root

## Context

The PRD target monorepo places the web app under `apps/web` alongside
`apps/quant-api` and a `packages/` directory. The repository currently has the
Next.js frontend at the repository root, with the FastAPI service at
`apps/quant-api`. The architecture overview and `docs/development/setup.md`
describe the root location as temporary. Moving the entire `src/` tree into
`apps/web` is a large, risky change with a real compatibility surface (path
aliases, `docker-compose.yml`, docs, CI, `.env` handling).

Before restructuring, the codebase has no shared `packages/` consumer: nothing
outside the web app needs the UI primitives, design tokens, or configuration
today. The only reason to migrate the web app is therefore a hypothesized future
need, not a current one.

## Decision

Treat the repository root as the web application for the current phase. Do not
move the frontend into `apps/web` now.

- Keep `src/`, `docker-compose.yml`, and the root Next.js configuration where
  they are.
- Keep the FastAPI service under `apps/quant-api`.
- Record the mono-app layout in the architecture overview, not the target
  `apps/web` monorepo structure.
- Revisit this decision with a new ADR when a concrete trigger appears: the
  first consumer outside the web app for a shared UI/config package, or the
  first migration that forces moving more than one app into `apps/`.

## Consequences

- No migration churn or compatibility risk in the current phase.
- Import aliases (`@/*`), docs path references, and Docker Compose stay valid.
- The repository does not yet match the PRD's target `apps/web` layout; the
  roadmap should not present the target monorepo shape as implemented.
- When the trigger condition is reached, the move is deliberately large and
  must be its own effort with a compatibility plan, not mixed into a feature
  change.

## Status

Accepted for the current phase. Superseded only by an explicit future ADR
recording the migration trigger.