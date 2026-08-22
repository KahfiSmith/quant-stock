# QuantLens AI Development Workflow Specification (PRD)

## 1. Purpose

This document is the primary product and delivery guide for AI coding agents and developers building **QuantLens**, a quantitative stock-analysis platform.

Target architecture:

- **Frontend:** Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui, and TradingView Lightweight Charts
- **Backend:** FastAPI and a Python 3.12 quant engine
- **Database:** PostgreSQL and TimescaleDB
- **Infrastructure:** Docker, Docker Compose, and cloud deployment

---

## 2. Product Goal and Value Proposition

QuantLens enables objective, data-driven equity analysis through:

1. **Automated data ingestion:** historical and EOD/realtime market data (OHLCV) and fundamentals.
2. **Data processing:** normalized market data and financial metrics.
3. **Quant scoring:** standardized multi-factor scores for Momentum, Quality, Value, Risk, and Growth.
4. **Stock screening:** multi-criteria discovery and ranking.
5. **Interactive analysis:** technical charts and fundamental metrics.
6. **Strategy backtesting:** historical strategy simulation with performance metrics such as CAGR, Sharpe ratio, and maximum drawdown.
7. **AI-driven insights:** structured summaries of strengths, risks, unknowns, and conclusions.

**Final objective:**

> Investors can analyse stocks objectively through a tested, automated quantitative-finance workflow.

---

## 3. Target Monorepo Architecture

```text
quantlens/
├── apps/
│   ├── web/               # Next.js 16+ App Router frontend
│   └── quant-api/         # FastAPI Python 3.12 quant engine and REST API
├── packages/
│   ├── database/          # PostgreSQL/TimescaleDB schemas and migrations
│   ├── ui/                # Shared UI primitives and design tokens
│   └── config/            # Shared configuration and constants
└── docker-compose.yml     # Local orchestration
```

---

## 4. Technology Stack and Rules

### Frontend (`apps/web` / Next.js)

- Next.js App Router, React 19, and TypeScript strict mode
- Tailwind CSS v4 and shadcn/ui
- Zustand for in-memory authentication and client state
- TanStack Query for server state and caching
- TradingView Lightweight Charts for stock charts
- Axios with `authClient`, `apiClient`, and single-flight token refresh
- Zod and React Hook Form for validation

### Backend (`apps/quant-api` / FastAPI)

- Python 3.12
- FastAPI REST framework
- Pydantic v2 request and response schemas
- SQLAlchemy 2.0 and asyncpg
- Alembic database migrations

### Quant engine

- `pandas` and `numpy` for time-series processing
- `scipy` for statistical calculations
- `pandas-ta` for technical indicators
- `scikit-learn` for predictive or clustering models when a validated use case exists

### Database and storage

- **PostgreSQL:** users, sessions, portfolios, transactions, and fundamentals
- **TimescaleDB:** time-series OHLCV hypertables

### Infrastructure and development

- Docker and Docker Compose
- GitHub Actions CI/CD
- Standardized environment variables; secrets are never committed

---

## 5. Development Roadmap and Phases

### Phase 0 — Project Initialization

- Status: `TODO`
- Create the target monorepo structure: `apps/web`, `apps/quant-api`, and `packages/`.
- Integrate the existing Next.js boilerplate.
- Create the FastAPI service skeleton.
- Configure Docker Compose for the web app, API, PostgreSQL, and TimescaleDB.
- Provide `.env.example` files with dummy values only.
- **Verification:** `docker compose up` starts the required local stack from a clean clone.

### Phase 1 — Authentication and User System

- Status: `TODO`
- **Frontend:** `/login`, `/register`, `/settings`, and `/profile`.
- **Backend:** `/api/v1/auth/*` endpoints, JWT access tokens, and HttpOnly refresh cookies.
- **Database:** `users` and `sessions` tables.
- **Acceptance criteria:** users can register, log in, refresh a session, log out, and manage a profile securely.

### Phase 2 — Market Data System

- Status: `TODO`
- Build data collection, processing, and storage pipelines.
- **Database tables:**
  - `stocks`: `id`, `symbol`, `name`, `sector`, `market_cap`, `created_at`, `updated_at`
  - `prices` hypertable: `id`, `stock_id`, `date`, `open`, `high`, `low`, `close`, `volume`
- **Backend API:**
  - `GET /api/v1/stocks`
  - `GET /api/v1/stocks/{symbol}/prices`
- **Acceptance criteria:** validated stock data is stored and the frontend displays historical prices on a chart.

### Phase 3 — Technical Analysis Engine

- Status: `TODO`
- Module: `apps/quant-api/app/technical`
- Indicators: MA20, MA50, MA200, RSI, MACD, ATR, and Bollinger Bands.
- **Backend API:** `GET /api/v1/stocks/{symbol}/technical`
- Example output:

```json
{
  "symbol": "BBCA",
  "trend": "bullish",
  "rsi": 65.4,
  "ma_signal": "positive",
  "indicators": {}
}
```

### Phase 4 — Fundamental Analysis Engine

- Status: `TODO`
- Module: `apps/quant-api/app/fundamental`
- Inputs: PER, PBV, ROE, ROA, debt-to-equity ratio, revenue growth, and EPS growth.
- **Backend API:** `GET /api/v1/stocks/{symbol}/fundamental`
- Output: a 0–100 fundamental score and a traceable ratio summary.

### Phase 5 — Quant Scoring Engine

- Status: `TODO`
- Module: `apps/quant-api/app/quant/scoring.py`
- Baseline multi-factor formula:

```text
Total score = 30% Momentum + 25% Quality + 20% Value + 15% Risk + 10% Growth
```

- **Backend API:** `GET /api/v1/stocks/{symbol}/score`
- Output: a 0–100 composite score and a factor-level breakdown.

### Phase 6 — Stock Screener

- Status: `TODO`
- **Frontend:** `/stocks` interactive screener table.
- Filters: sector, market capitalization, quant score, ROE, PER, PBV, and RSI.
- Output: ranked stocks with validated sorting and pagination.

### Phase 7 — Stock Detail Page

- Status: `TODO`
- **Frontend:** `/stocks/[symbol]`
- Required sections:
  1. **Overview:** price, market capitalization, sector, and headline quant score.
  2. **Chart:** candlestick chart, volume, and technical-indicator overlays.
  3. **Fundamentals:** ratios, valuation, profitability, and growth metrics.
  4. **Quant analysis:** factor-score breakdown and risk analysis.

### Phase 8 — Portfolio System

- Status: `TODO`
- **Database:** `portfolios`, `transactions`, and `holdings`.
- Features: portfolio creation and editing, buy/sell transaction recording, realized and unrealized PnL, allocation, and portfolio-risk metrics.
- **Frontend:** `/portfolio`

### Phase 9 — Backtesting Engine

- Status: `TODO`
- Module: `apps/quant-api/app/quant/backtest.py`
- Input: strategy rules, period, starting capital, and execution assumptions. Example: buy when score is greater than 80; sell when score is below 60.
- Output:
  - total return and CAGR
  - annualized volatility
  - Sharpe and Sortino ratios
  - maximum drawdown
  - equity-curve visualization

### Phase 10 — AI Analyst

- Status: `FUTURE`
- Integrate an LLM or AI reasoning layer that reads structured quant scores, fundamentals, technical metrics, and licensed news data.
- Output: `strengths`, `risks`, `unknowns`, and `conclusion`.

---

## 6. Database Migration and Integrity Rules

Every database change must:

1. create an isolated Alembic migration;
2. update the SQLAlchemy ORM model;
3. update Pydantic request and response schemas;
4. update TypeScript interfaces under `src/types` or their future shared-package equivalent;
5. document migration, rollback, compatibility, and data-backfill requirements where applicable.

Migrations must be reviewed, ordered, reversible where practical, and executed through the application deployment workflow rather than manually against shared environments.

---

## 7. API Conventions and Contract

The API base path is `/api/v1`.

### Success response envelope

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

### Error response envelope

```json
{
  "success": false,
  "message": "Human-readable error message",
  "code": "ERROR_CODE_STRING",
  "error": null
}
```

---

## 8. Testing and Definition of Done

### Testing requirements

| Layer | Minimum coverage | Required examples |
| --- | --- | --- |
| Frontend | Component and integration tests for critical flows | loading, error and empty states; screener filters; authentication; number/date formatting |
| Backend | `pytest` unit and API tests | input validation, authorization, response envelopes, pagination, and error mapping |
| Quant engine | Deterministic unit tests using fixed fixtures | indicator formulas, score normalization, factor weights, and incomplete-data edge cases |
| Data pipeline | Integration tests against a temporary database | idempotent ingestion, deduplication, upsert behavior, and OHLCV quality validation |
| Backtest | Regression tests using versioned datasets | no look-ahead bias, transaction costs, return calculation, and drawdown calculation |

Any bug fix affecting financial outputs, scores, or backtests requires a regression test before it is complete.

### Definition of Done

A feature is `Done` only when:

- [ ] Scope, dependencies, acceptance criteria, and risks are agreed.
- [ ] Relevant database migrations, models, and indexes are complete.
- [ ] Relevant backend API, authorization, validation, and error envelopes are complete.
- [ ] Relevant frontend UI, loading/error/empty states, and data integration are complete.
- [ ] Relevant unit, integration, and regression tests pass.
- [ ] Documentation is synchronized, including affected API, schema, and feature documentation.
- [ ] `pnpm lint`, `pnpm type-check`, and `pnpm docs:check` pass for the web app; equivalent Python checks pass for the API.
- [ ] The feature runs reliably through Docker Compose after Phase 0 is available.
- [ ] No secret, personal data, or licensed provider data is committed or exposed in logs.

---

## 9. Authority, Current Baseline, and Scope Boundaries

### Document authority

This PRD is the source of truth for **product direction, phase dependencies, and QuantLens acceptance criteria**. It does not override the current implementation sources of truth:

- Active routes and runtime behavior in `src/app`.
- Frontend conventions in `AGENTS.md`, `docs/conventions/`, and `docs/architecture/`.
- Implemented endpoint contracts in `src/lib/api/endpoints.ts` and `docs/api/`.
- Applied migrations and implemented database schemas, which override illustrative schema examples in this document.

When a conflict exists, preserve current runtime compatibility, record the decision in an ADR, and update this PRD and related documentation in the same change.

### Current repository baseline

At the time of writing, this repository is a **Next.js frontend boilerplate**, not a running QuantLens monorepo. It currently contains a landing page, login, registration, profile, TanStack Query providers, Zustand session state, and Axios clients for the existing backend contract. FastAPI, TimescaleDB, QuantLens Docker Compose, market data, `/stocks`, and the quant engine are planned work.

Therefore:

1. Phase 0 is not complete merely because the frontend boilerplate exists.
2. Phase 1 has UI and session foundations, but FastAPI and database integration must be completed before the phase can be `Done`.
3. Roadmap endpoints are target contracts; they do not prove that those endpoints currently exist.

### Product boundaries and non-goals

The first QuantLens release focuses on equities supported by a legally usable data provider. The product must not:

- give personalized investment advice, guaranteed buy/sell signals, or return promises;
- claim realtime data, corporate-action handling, or exchange coverage before the relevant source and license are verified;
- execute broker orders, provide custody, or perform trading in the current scope;
- use an LLM as the source of market prices, scores, or fundamental facts.

Every analytical page and AI output must state that it is educational/analytical information, not investment advice.

---

## 10. Delivery Model and Phase Gates

### Status definitions

- `TODO`: not started; no active work has begun.
- `IN PROGRESS`: scope, owner, and active implementation work exist.
- `BLOCKED`: work cannot proceed because a dependency, data license, or product decision is missing.
- `DONE`: the phase meets its acceptance criteria and Definition of Done.
- `FUTURE`: deliberately outside the current release scope.

### Mandatory execution loop

For every task, the AI agent and developer must:

1. read this PRD, the roadmap, and relevant domain documentation;
2. inspect the actual implementation, migrations, endpoints, and tests;
3. select exactly one earliest TODO phase or sub-phase whose dependencies are satisfied;
4. state the small implementation scope, acceptance criteria, and risks before changing code;
5. implement only that scope with the necessary layers;
6. run relevant validation;
7. update the roadmap and documentation, then report changed files, completed scope, remaining work, validation, and risks.

A future-phase feature must not be implemented merely because its UI or library is available. An exception requires an approved ADR.

### Dependency map and minimum phase exit criteria

| Phase | Prerequisites | Minimum exit criteria |
| --- | --- | --- |
| 0. Initialization | None | Monorepo, web/API services, database, environment examples, and `docker compose up` work from a clean clone. |
| 1. Authentication | Phase 0 | User/session migration; protected register/login/refresh/logout; secure refresh cookie; integrated frontend; passing auth tests. |
| 2. Market data | Phase 0 and a data-provider decision | Idempotent ingestion; validated metadata and OHLCV storage; paginated endpoints; historical chart rendering. |
| 3. Technical | Phase 2 | Defined data interval and lookback; benchmark-tested indicators; timestamp and `as_of` data in responses. |
| 4. Fundamental | Phase 2 and financial-statement source | Clear reporting periods and units; ratios traceable to inputs; tested fundamental score. |
| 5. Quant scoring | Phases 3 and 4 | Persisted and displayed weights, normalization, model version, and incomplete-data reasons. |
| 6. Screener | Phase 5 | Server-side validated filters; deterministic sorting/pagination; `as_of` and model-version metadata. |
| 7. Stock detail | Phases 2–5 | Overview, chart, fundamentals, and score breakdown are consistent for one symbol and timestamp. |
| 8. Portfolio | Phases 1 and 2 | Enforced ownership; immutable/auditable transactions; tested PnL and risk calculations. |
| 9. Backtest | Phases 2 and 5 | Versioned dataset/strategy; anti-bias controls; costs and slippage; reproducible metrics. |
| 10. AI analyst | Phases 3–5 and approved AI policy | Provenance-backed structured output; no personal advice; passing quality and safety evaluation. |

### Phase 0 implementation checklist

Phase 0 must be delivered in small, reversible changes:

1. Decide whether to migrate the frontend into `apps/web` or treat this repository as `apps/web` temporarily. Do not move large source trees without an ADR and compatibility plan.
2. Add `apps/quant-api` with a health endpoint, dependency lock, format/lint/type/test commands, and a non-root Dockerfile.
3. Add a minimal Compose profile for `web`, `quant-api`, and PostgreSQL with TimescaleDB. Database health checks must block API startup until ready.
4. Separate server-only secrets from `NEXT_PUBLIC_*`; update `.env.example` with dummy values only.
5. Bootstrap the database through Alembic migrations, not one-time manual SQL.
6. Document start/stop commands, local database reset, and troubleshooting.

---

## 11. Market Data Governance and Canonical Contracts

### Source and licensing requirements

Before implementing a collector, document the chosen provider's exchange/symbol coverage, cadence (EOD or intraday), timezone, latency, corporate-action policy, rate limit, retention, attribution, cost, and redistribution rights. Do not scrape or retain data when the provider license does not permit it.

### Candidate providers for Indonesian and global coverage

The following providers are candidates for Phase 2 evaluation; none is selected,
integrated, or approved for redistribution yet. Coverage, commercial terms, API
limits, data adjustments, and permitted use must be validated against the
intended universe before implementation.

| Provider | Intended evaluation scope | Decision required before use |
| --- | --- | --- |
| IDX data provider | Indonesian exchange instruments, official reference data, and exchange-specific corporate actions | Confirm the applicable IDX data product, licensing, access method, cadence, and redistribution rights. |
| Yahoo Finance | Broad public-market historical price and reference data | Confirm Indonesian symbol coverage, terms of use, adjustment semantics, reliability, and whether automated collection is permitted. |
| Alpha Vantage | API-delivered global market data and selected fundamentals | Confirm exchange coverage, plan limits, latency, historical depth, and commercial rights for the required universe. |
| Polygon | Global-market API candidate, subject to product availability by exchange | Confirm the specific Polygon product's Indonesian and other exchange coverage, entitlements, latency, and redistribution rights. |
| Financial Modeling Prep | Fundamental statements, ratios, and market reference data | Confirm Indonesian issuer coverage, filing provenance, update timing, plan limits, and use rights. |

A provider may be used only after the product and technical owners record the
selection and satisfy the source and licensing requirements below.

### Canonical identifiers and timestamps

- `symbol` is the display ticker; `stock_id` is the stable internal identity.
- Instrument metadata must store `exchange`, `currency`, and exchange timezone.
- Use `TIMESTAMPTZ` for market events and UTC for storage/transport; render time in the exchange timezone in the UI.
- Every analytical response must include `as_of`, `data_source`, and, when relevant, `data_version` or `score_version`.
- Persistent financial calculations must not rely on JavaScript floating point. Use `NUMERIC`/`Decimal` at database and API boundaries.

### OHLCV and fundamental validation

The collector or processor must reject or flag records when:

- `high < low`, `open` or `close` falls outside the low-high range, a price or volume is negative, a timestamp is duplicated, or a symbol is unknown;
- candles are not strictly time-ordered;
- a fundamental record lacks `period_end`, `published_at`, `currency`, or period basis such as TTM, quarterly, or annual;
- incoming data overwrites published data without provenance.

Store at least the source, source-record identifier, retrieval time, payload checksum/version when available, and validation state. Ingestion must be idempotent through an appropriate unique key, such as `(stock_id, time, interval, source)` for a candle.

### Corporate actions and missing data

Adjusted and unadjusted prices must be explicit. Splits, dividends, trading suspensions, delistings, ticker changes, and exchange holidays must not be treated as ordinary candles. Missing data must never be silently filled; the processor must return a data-quality status or explain why an indicator or score is unavailable.

---

## 12. Quant Methodology and Reproducibility

### Indicator conventions

Every indicator must define its candle interval, lookback, moving-average type, warm-up policy, input price (`close` or adjusted close), and output rounding. Values without enough lookback history must not be represented as zero.

Baseline examples:

- MA20/50/200: simple moving average of daily adjusted close unless a version explicitly says otherwise.
- RSI: 14-period RSI with the documented smoothing method.
- MACD: response metadata includes fast, slow, and signal parameters.
- ATR: interval and True Range method are explicit.

### Scoring contract

The Phase 5 factor weights are a baseline model, not a formula that may change silently:

```text
score = 0.30 × momentum
      + 0.25 × quality
      + 0.20 × value
      + 0.15 × risk
      + 0.10 × growth
```

Each factor score is normalized to 0–100 with an explicit direction. For example, lower measured risk can produce a higher `risk_score`. The implementation must persist and return:

- `score_version`, effective date, and normalization parameters;
- raw and normalized factor values;
- total score, weights, data-completeness status, and reason codes for partial or unavailable scores;
- the comparison universe when percentiles or ranks are used.

A change to weights, metrics, normalization, or universe is a model change. It requires a new version, benchmark regression tests, a change record, and historical versioning rather than silent rewrites.

### Backtesting validity requirements

A backtest may use only information available at the time of each decision. The implementation must prevent look-ahead bias, survivorship bias, and data leakage. A strategy run records dataset version, universe, period, rebalance schedule, execution price, corporate-action treatment, fees, slippage, cash policy, and lot-rounding rules.

Report at least total return, CAGR/annualized return, annualized volatility, Sharpe ratio including the risk-free rate, maximum drawdown, transaction count, win rate when relevant, and a clearly identified benchmark. Backtest results must never be presented as forecasts or guarantees.

---

## 13. API Contract Detail

In addition to the response envelope in Section 7, target endpoints follow these rules:

- All endpoints use the `/api/v1` prefix. Breaking changes require a new API version or documented deprecation period.
- Python API payloads use `snake_case`. The frontend may map them at a boundary, but must not mix conventions inconsistently.
- Resource lists use documented pagination (`page` and `page_size`, or cursor), sorting allowlists, and validated filters.
- A market-data list response includes the data, pagination metadata, and `as_of` when values depend on market data.
- Private endpoints enforce identity and resource ownership on the server. Frontend route guards are not a security boundary.
- Errors must not expose stack traces, credentials, database queries, or another user's data. Use stable `code` values for UI-handled errors.
- Market, score, and detail endpoints explicitly handle unknown symbols, unavailable data, invalid periods, and provider outages.

Example target score response:

```json
{
  "success": true,
  "data": {
    "symbol": "BBCA",
    "as_of": "2026-08-21T00:00:00Z",
    "score_version": "v1",
    "total_score": 87.0,
    "factors": {
      "momentum": 90.0,
      "quality": 86.0,
      "value": 78.0,
      "risk": 82.0,
      "growth": 91.0
    },
    "data_quality": "complete"
  }
}
```

---

## 14. Security, Privacy, and Operational Requirements

### Security and privacy

- Access tokens remain short-lived and in-memory in the frontend. Refresh tokens use `HttpOnly`, `Secure`, and deployment-appropriate `SameSite` cookies.
- The API implements modern password hashing, session rotation/revocation, rate limits for authentication and expensive endpoints, input validation, CORS allowlists, and audit logs for sensitive actions.
- Secrets come only from environment variables or a secret manager. `.env.local`, provider tokens, database credentials, and personal payloads must not be committed.
- IP addresses and user agents in sessions are operational personal data; access, retention, and logging must be limited by policy.

### Reliability and observability

- Provide `/health` for liveness and `/ready` for dependency readiness.
- Ingestion and backtest jobs have an ID, status (`queued`, `running`, `succeeded`, `failed`), retry policy, and safe error reporting.
- Structured logs include request/job correlation IDs, never tokens or passwords. Metrics cover API latency, error rate, data freshness, rejected-record count, and job duration.
- Define SLOs only after data volume and provider characteristics are known. Do not claim realtime latency or availability beforehand.

### Performance baselines

Cache stock metadata and analytical results with an `as_of` value deliberately. Chart queries must constrain interval, date range, and point count; downsample or resample in the API when needed. Collectors and backtests are background workloads, not long synchronous requests.

---

## 15. AI Analyst Guardrails (Phase 10)

The AI Analyst summarizes only structured facts supplied by the quant API and licensed news sources. Its input includes timestamps, source/provenance, data quality, and score version; its output must be able to identify the supporting facts.

Output is divided into `strengths`, `risks`, `unknowns`, and `conclusion`, includes a disclaimer, and avoids certainty such as "will certainly rise" or personalized instructions to buy or sell. When data is incomplete, stale, or conflicting, the AI explains the limitation rather than filling gaps with assumptions. Run offline factuality, format, safety, and prompt-injection-resistance evaluations before release.

---

## 16. Git Workflow and Change Management

Use the branches `main`, `develop`, and `feature/<area>-<short-description>`. Use concise Conventional Commit prefixes: `feat:`, `fix:`, `refactor:`, `docs:`, and `test:`. Example: `feat: add versioned stock scoring engine`.

A pull request affecting quant logic, schema, or API contracts states the model/schema version, migration and rollback plan, provider-data change, benchmark/test result, and compatibility impact. Do not combine a broad refactor with a formula or migration change without a documented reason.

---

## 17. AI Agent Execution Prompt

Use the following instruction for QuantLens implementation work:

```text
You are the lead software engineer for QuantLens.

Use docs/product/quantlens-spec.md for product direction and phase ordering.
Treat current runtime code, migrations, endpoint definitions, and repository
conventions as the source of truth for implemented behavior.

Before coding:
1. Inspect the current repository state, roadmap, relevant docs, migrations,
   endpoints, and tests.
2. Identify the earliest TODO phase whose dependencies are complete.
3. Select one small, verifiable slice of only that phase.
4. State the acceptance criteria, data/API/UI/test impact, and risks.
5. Implement with clean boundaries; do not invent data sources or claim planned
   services are already implemented.
6. Run the relevant tests and quality checks.
7. Update docs and report files changed, completed scope, remaining work,
   validation results, and risks.

Never skip dependencies or implement future phases before the current phase is
stable. Escalate missing provider licenses, product decisions, or conflicting
contracts instead of guessing.
```

---

## 18. Decisions Required Before Phase 0 or Phase 2

Product and technical owners must make the following decisions before dependent implementation begins:

1. Initial exchange and universe (for example, IDX-only or multi-exchange), currency, UI language, and display timezone.
2. Data provider, license, EOD versus intraday scope, budget/rate limits, and corporate-action policy.
3. Repository strategy: full monorepo migration or separate frontend and API repositories with an explicit contract.
4. Hosting, secret manager, database backup/retention, and development/staging/production environments.
5. Scoring universe, factor normalization, incomplete-data handling, and backtest benchmark definition.
6. Disclaimer policy, legal/compliance review, and the boundaries of the AI Analyst.

Until these decisions are available, mark affected work as `BLOCKED`; do not replace them with hidden assumptions.
