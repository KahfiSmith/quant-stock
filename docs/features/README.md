# Features Documentation

Overview of business features implemented in this application.

## Implemented features

- [Authentication & User Session](./authentication.md) - login, register,
  logout, session bootstrap, protected profile, delete account.
- [Market Data](./market-data.md) - stock universe, chart, technical,
  fundamental, quant, screener, and AI summary surfaces.
- Portfolio tracking, transaction recording, and PnL are implemented under the
  `(dashboard)` route group; backtesting is implemented under the same group.

## Route-group coverage

Every route group under `src/app/` must be documented here. The
`docs:check` gate fails when a route group has no feature doc.

- `(auth)` - covered by [authentication.md](./authentication.md).
- `(dashboard)` - the protected profile surface is part of
  [authentication.md](./authentication.md); the stock pages (`/stocks`,
  `/stocks/[symbol]`) are covered by
  [market-data.md](./market-data.md).
- `(public)` - the landing page is a thin shell over the auth surface; see
  [product overview](../product/overview.md).

## Adding a new feature

1. Create the route group under `src/app/`.
2. Copy `docs/features/_TEMPLATE.md` to `docs/features/<group>.md`.
3. Fill in Overview, Core flow, Implementation map, Endpoints.
4. Add it to the list above.

Feature docs must describe only implemented behavior. When a feature ships,
promote its durable decisions here.
