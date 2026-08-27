# Documentation Directory

These documents distinguish implemented behavior from planned work. Accepted
architecture and conventions live in the current sources of truth; planned
capabilities are called out explicitly rather than described as if they exist.

This repository contains the QuantLens Next.js client and active FastAPI service
(`apps/quant-api`). The architecture documentation describes the current runtime
layout and the planned expansion separately.

## Current sources of truth

- [Product PRD Specification](product/quantlens-spec.md) - QuantLens comprehensive PRD, architecture, and phase guide.
- [Architecture](architecture/overview.md) - System design, folder structure, data flow, dependency rules, and ADRs.
- [API](api/overview.md) - Backend contract, Axios clients, query config.
- [Authentication API & Errors](api/authentication.md) - Endpoints, envelope, error codes.
- [Security](security/overview.md) - Trust boundaries, authentication, authorization.
- [Secrets & Security Rules](security/secrets.md) - Env vars, secrets management, rules.
- [Coding Standards & Naming](conventions/coding.md) - TS, lint, components, imports, styling, naming.
- [Validation](conventions/validation.md) - Zod schemas and form wiring.
- [Error Handling & Logging](conventions/error-handling.md) - Error paths, logging rules.
- [Testing](conventions/testing.md) - Current status and guidance.
- [Development](development/setup.md) - Setup, commands, environment.
- [Workflow](development/workflow.md) - Implementation patterns, handoff checklist.
- [Debugging](development/debugging.md) - Common checks and failure modes.
- [Features](features/authentication.md) - Implemented feature modules (authentication and user session).
- [Market Data](features/market-data.md) - Stock universe and price-history chart feature.
- [Product Overview](product/overview.md) - Product status, business rules, terminology.
- [Roadmap](product/roadmap.md) - Planned work and build order.
- [Database](database/schema.md) - Database notes (PostgreSQL + TimescaleDB).
- [Infrastructure](infrastructure/deployment.md) - Environments, deployment, CI/CD.
- [Observability](infrastructure/observability.md) - Current signals and planned tooling.
- [Verification harness](development/workflow.md) - `verify:*` commands, risk classification, cross-repo sync.

## Planned, not yet implemented

The following are intentionally not described as implemented:

- Next.js server-side API routes (`src/app/api/**`) - none exist; FastAPI owns the active API boundary.
- Middleware-enforced page access control - `middleware.ts` is a pass-through; API authorization is enforced by FastAPI.
- Frontend test suite - Vitest covers authentication, API clients, route guards,
  and domain hooks; focused FastAPI route and quant tests exist under
  `apps/quant-api/tests`.
- Observability tooling - not configured.
- Market-data schema and read endpoints - the `stocks`/`prices` tables and
  `GET /api/v1/stocks*` endpoints exist, but real market-data ingestion is
  deferred pending a data-provider decision.

When a planned capability is shipped, promote only its durable decisions into
the current sources of truth.
