# Architecture Overview

QuantLens consists of a Next.js 16 App Router web client, a FastAPI authentication service, and a PostgreSQL/TimescaleDB data foundation. The active web application remains at the repository root; only the API is currently located under `apps/quant-api`.

## Active topology

```text
quant-stock/
├── apps/
│   └── quant-api/          # FastAPI service, Alembic migrations, API tests
├── src/                    # Next.js application
├── docker-compose.yml      # Web, API, and TimescaleDB local orchestration
└── .env.example            # Shared local environment defaults
```

```text
browser
  -> Next.js App Router (React 19)
     -> feature components
        -> hooks
           -> Axios clients
              -> FastAPI API (/api/v1)
                 -> PostgreSQL + TimescaleDB
```

## Core stack

| Concern | Choice | Role |
| --- | --- | --- |
| Frontend | Next.js 16, React 19, TypeScript | Web UI, routing, client-side session experience |
| UI | Tailwind CSS 4 and shadcn/ui-style primitives | Tokens, layout, and reusable components |
| State and cache | Zustand 5 and TanStack Query 5 | In-memory auth state and server-state caching |
| Backend | FastAPI and SQLAlchemy | REST API, authentication, and future quant services |
| Database | PostgreSQL with TimescaleDB | Authentication records and future market time-series data |
| Local orchestration | Docker Compose | Web, API, and database services |

## Frontend structure and ownership

```text
src/
├── app/                    # App Router segments, layouts, metadata
│   ├── (auth)/             # Login and registration routes
│   ├── (dashboard)/        # Protected profile route
│   ├── (public)/           # Public landing route
│   ├── layout.tsx          # Root layout and AppProvider mount
│   └── globals.css         # Tailwind tokens and CSS variables
├── components/
│   ├── common/             # Shared shell and feedback components
│   ├── features/           # Feature-owned UI composition
│   └── ui/                 # Business-free reusable primitives
├── config/                 # Static application and route constants
├── hooks/                  # API/query and mutation wrappers
├── lib/
│   ├── api/                # Axios clients, endpoints, queries, errors
│   ├── schemas/            # Zod request and form validation
│   └── utils/              # Pure helpers
├── providers/              # App, query, and session providers
├── store/                  # Zustand stores
└── types/                  # Domain and API contracts
```

| Path | Responsibility |
| --- | --- |
| `src/app/` | Route composition, layouts, metadata, and lightweight client guards |
| `src/components/features/` | Feature-level UI and interaction composition |
| `src/components/ui/` | Reusable primitives with no domain logic |
| `src/hooks/` | Query and mutation logic that wraps API clients |
| `src/lib/api/` | Frontend HTTP boundary and endpoint constants |
| `src/lib/schemas/` | Zod validation schemas |
| `src/lib/utils/` | Pure reusable helpers |
| `src/providers/` | Root-mounted client providers and session bootstrap |
| `src/store/` | In-memory global client state |
| `src/types/` | Shared TypeScript domain and API contracts |
| `apps/quant-api/` | FastAPI routes, services, persistence models, migrations, and API tests |

## Dependency rules

```text
app -> components/features -> hooks -> lib/api -> store -> types
providers -> lib/api | store
```

- `src/components/ui` must remain independent of feature and domain logic.
- Pages compose feature components and keep guards limited to navigation UX; FastAPI is the authorization boundary.
- Feature components use hooks rather than calling Axios clients directly.
- External API access occurs only through `src/lib/api`.
- `process.env` is read only in approved configuration boundaries, including the Axios base URL.
- `src/app/api/**` has no active routes; FastAPI owns the API boundary.

## Authentication request flow

```text
User action
  -> component handler and Zod validation
     -> auth hook (useLogin / useRegister / useLogout)
        -> authClient or apiClient
           -> FastAPI endpoint (/api/v1/auth/...)
              -> API response envelope
                 -> client handling and Zustand auth-store update
                    -> UI re-render or safe internal redirect
```

- `authClient` sends credentials for authentication mutations and refresh.
- `apiClient` attaches the in-memory Bearer access token to protected business requests and coordinates a single-flight refresh after `401 ACCESS_TOKEN_EXPIRED`.
- `apiClient` unwraps successful API envelopes to `response.data.data`.
- Access tokens exist only in the non-persisted Zustand store; FastAPI manages the refresh token as an `HttpOnly` cookie.
- The root provider mounts `AppProvider` → `QueryProvider` → `SessionProvider`. On mount, `SessionProvider` calls `POST /api/v1/auth/refresh` to restore the in-memory session.

## Implemented routes

| Route | Segment | Primary UI | Protection |
| --- | --- | --- | --- |
| `/` | `(public)` | Home page with header and footer | Public |
| `/login` | `(auth)` | Login form | Redirects after an authenticated session is restored |
| `/register` | `(auth)` | Registration form | Public |
| `/profile` | `(dashboard)` | Profile page and logout action | Client guard for UX; FastAPI authorizes protected API calls |

## Current and planned scope

- **Implemented:** FastAPI authentication, numeric user IDs, refresh-token rotation and reuse detection, frontend session bootstrap, and protected profile UX.
- **Deferred:** Market-data ingestion, technical and fundamental analysis, quant scoring, portfolios, backtesting, and AI-assisted analysis.
- **Future repository structure:** Additional packages or a moved `apps/web` application require an explicit migration; they are not part of the current runtime layout.
