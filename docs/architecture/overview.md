# Architecture Overview

QuantLens system architecture: Next.js 16 App Router frontend connected to FastAPI Python Quant Engine and PostgreSQL + TimescaleDB.

## Target Architecture

The target architecture follows a monorepo setup containing the frontend web app, the Python quant API engine, shared database schemas, and shared config:

```text
quantlens/
├── apps/
│   ├── web/               # Next.js 16+ App Router (React 19, TypeScript)
│   └── quant-api/         # FastAPI Python 3.12 Quant Engine & REST API
├── packages/
│   ├── database/          # PostgreSQL + TimescaleDB schemas & migrations
│   ├── ui/                # Shared UI primitives & design tokens
│   └── config/            # Shared configuration & constants
└── docker-compose.yml     # Local orchestration
```

```text
browser
  -> Next.js App Router (React 19, client components, TradingView charts)
     -> feature components (src/components/features)
        -> hooks (src/hooks)
           -> Axios clients (src/lib/api)
              -> Zustand stores (src/store)
                 -> FastAPI Quant Engine backend (/api/v1)
                    -> PostgreSQL (relational) + TimescaleDB (OHLCV time-series)
```

## Core stack

| Concern      | Choice                          | Purpose / Role                                     |
| ------------ | ------------------------------- | -------------------------------------------------- |
| Frontend App | Next.js 16 (App Router)         | Web UI, routing, SSR/client views                  |
| UI / Styling | React 19, Tailwind CSS 4        | Interactive UI & design tokens                     |
| UI Components| shadcn/ui                       | Reusable UI primitives (`src/components/ui`)       |
| Charts       | TradingView Lightweight Charts  | Interactive candlestick & technical indicator plots|
| State & Cache| Zustand 5 + TanStack Query 5    | In-memory state, session, and server cache         |
| Backend API  | FastAPI (Python 3.12)           | REST API, asynchronous service layer               |
| Quant Engine | pandas, numpy, scipy, pandas-ta | Statistical analysis, indicators, quant scoring    |
| Database     | PostgreSQL + TimescaleDB        | Users, portfolios, fundamentals, OHLCV time-series |
| Container    | Docker + Docker Compose         | Unified local and deployment environment           |

## Implemented routes

| Route      | Segment           | Component(s)                              | Guard                        |
| ---------- | ----------------- | ----------------------------------------- | ---------------------------- |
| `/`        | `(public)`        | `HomePage` + `Header`/`Footer`            | none (public)                |
| `/login`   | `(auth)`          | `LoginPage` → `LoginForm`                 | redirects if authenticated   |
| `/register`| `(auth)`          | `RegisterPage` → `RegisterForm`           | none                         |
| `/profile` | `(dashboard)`     | `ProfilePage` + `LogoutButton`            | redirects if unauthenticated |

All interactive pages are client components (`"use client"`). Layouts and
`register/page.tsx` remain server components.

## Backend & Engine Integration

The backend is structured as a FastAPI service (`apps/quant-api`) serving `/api/v1` REST endpoints, with background workers/engines for market data processing, technical calculations, quant scoring, and backtesting. See [QuantLens PRD](../product/quantlens-spec.md) for full phase plans.

## Current vs Planned Features

- **Current Frontend**: Auth & user profile, session bootstrap, Axios client with single-flight refresh.
- **Planned Backend**: FastAPI quant engine with PostgreSQL & TimescaleDB hypertables.
- **Planned Frontend Routes**: `/stocks` (screener), `/stocks/[symbol]` (details/chart), `/portfolio` (tracking), `/backtest` (strategy testing).
