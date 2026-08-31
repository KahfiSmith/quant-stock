# QuantLens

Quantitative analytics platform for Indonesian Stock Exchange (IDX/BEI). Analyzes
78+ IDX stocks using 34 technical indicators, foreign flow analysis, and a composite
conviction score to generate data-driven buy/sell recommendations.

## Features

### 📊 Quant Ranking (`/quant-ranking`)

Leaderboard ranking IDX stocks by **Conviction Score** — a composite 0-100 score
that combines all analytical signals into a single actionable metric.

**Strategy Presets** — select an investment strategy that matches your style:

| Preset | Focus | Best For |
|---|---|---|
| Standard IDX Quant | Balanced across all factors | Default, all investor types |
| IDX Bluechip Momentum | Blue chip stocks with strong trends | Trend followers |
| IDX Deep Value | Cheap stocks (low PE/PB) | Value investors |
| IDX GARP Rotation | Growth at Reasonable Price | Growth seekers with valuation discipline |
| IDX High Dividend & Defensive | Defensive, low-risk stocks | Conservative investors |
| IDX Volume Momentum | Stocks with high volume momentum | Short-term traders |
| IDX Mean Reversion | Oversold stocks ready to bounce | Contrarian investors |

**Weight Slider** — customize the weighting of 5 scoring factors:

| Factor | What It Measures | Default |
|---|---|---|
| **Momentum** | RSI, MA trend, ADX, 12-month return | 30% |
| **Quality** | ROE, ROA, Debt/Equity (company health) | 25% |
| **Value** | P/E, P/B (cheap or expensive) | 20% |
| **Risk** | Sharpe, Sortino, drawdown, volatility | 15% |
| **Growth** | Revenue growth, EPS growth | 10% |

Drag a slider right to increase that factor's importance. For example, to focus
on finding cheap stocks, increase Value to 50% and reduce the others.

**Table Columns:**

| Column | Meaning |
|---|---|
| **Conviction** | Composite score 0-100 blending quant + foreign flow + risk-adjusted returns. Higher is better |
| **Recommendation** | STRONG BUY HIGH CONVICTION → SELL EXIT. Action based on conviction score |
| **Quant Score** | 5-factor score (momentum, quality, value, risk, growth) |
| **Flow Signal** | Foreign institutional buying (ACCUMULATION) or selling (DISTRIBUTION) |
| **Decision Signal** | STRONG BUY / BUY / HOLD / SELL / STRONG SELL |
| **1M Mom** | 1-month price return |
| **Sharpe** | Risk-adjusted return. >1 = good, >2 = excellent |
| **Risk Level** | LOW / MEDIUM / HIGH |

Click column headers to sort. Pagination at 20 items per page.

### 📈 Stock Detail (`/stocks/[symbol]`)

Per-stock analysis page with 6 tabs:

- **Overview** — 8 cards: Technical (ADX, MFI, Stochastic RSI, OBV, Support Distance), Fundamental (PE, PB, ROE), Volume Analysis, Volatility Regime, Momentum (1M/3M/6M/12M), Drawdown, Risk-Adjusted Returns (Sharpe/Sortino/Calmar)
- **Candlestick Chart** — Price chart with range 1M/3M/6M/1Y/All
- **Financial Fundamentals** — PE, PB, ROE, ROA, D/E, Revenue Growth, EPS Growth
- **Quant Score Breakdown** — Detailed 5-factor breakdown + sector comparison
- **IDX Foreign Flow** — Foreign Flow Analysis (signal, rolling 5D/20D, streak, divergence) + daily foreign buy/sell table + corporate actions
- **AI Analyst** — Automated strengths, risks, conclusion analysis

### 💼 Portfolio (`/portfolio`)

Track your investments:
- Create portfolios, add BUY/SELL transactions
- View holdings, unrealized PnL, realized PnL
- Risk metrics: annualized volatility, max concentration
- Transaction history with delete capability
- Click any symbol to navigate directly to its stock detail page

### 🔬 IDX Factor Rotation (`/backtest`)

Backtest factor rotation strategies across the IDX universe:
- Select top-N stocks, rebalance frequency, factor weights
- Benchmark against IHSG (^JKSE)
- Results: equity curve, Sharpe, CAGR, max drawdown, alpha/beta

### 🎯 Scanner (`/scanner`)

Real-time scanner for swing trading and scalping opportunities with 4 modes:

| Scanner Mode | What It Finds | Filter |
|---|---|---|
| **Swing Breakout** | Volume spike + strong momentum — stocks ready to rally 2-5 days | Volume Z ≥ 1.5 |
| **Scalping / Gorengan** | Extreme volume + aggressive momentum — stocks being moved | Volume Z ≥ 2.0 |
| **Foreign Accumulation** | Smart money quietly buying — price hasn't moved yet | Flow = ACCUMULATION |
| **Oversold Bounce** | RSI/MFI oversold + volume entering — ready to bounce | RSI ≤ 35 |

Results table shows Conviction, Recommendation, Volume Z-Score, Flow Signal,
1M Momentum, RSI, and Price with color-coded signals.

### 🔍 Stock List (`/stocks`)

Browse all IDX stocks with real market data:
- Filter by IDX-IC sector (12 sectors)
- Search by ticker or company name
- Sort by Quant Score, Market Cap, PE, PB, ROE
- Pagination at 20 per page

## Quick Start

```bash
# 1. Start all services (frontend + backend + database)
docker compose up -d

# 2. Apply database migrations
docker compose exec quant-api alembic upgrade head

# 3. Backfill foreign flow + broker summary from idx.co.id (~5-10 minutes)
docker compose exec quant-api python -m scripts.backfill_idx_data --range 30

# 4. Backfill OHLCV + fundamentals from Yahoo Finance (~2-5 minutes)
docker compose exec quant-api python -m scripts.backfill_market_data
```

Frontend: `http://localhost:3000` | Backend API: `http://localhost:8000`

> **Tip**: If step 4 hits `429 Too Many Requests`, wait 30 minutes then retry
> with a smaller batch: `--symbols BBCA,BMRI,BBRI,TLKM,ASII --rate-limit-seconds 8.0`.
> Step 3 (idx.co.id) is not affected. See [setup docs](docs/development/setup.md)
> for detailed troubleshooting.

### Daily Update (after market close)

```bash
docker compose exec quant-api python -m scripts.backfill_market_data
docker compose exec quant-api python -m scripts.backfill_idx_data
```

### Frontend-Only Development

```bash
pnpm install
cp .env.example .env.local
pnpm dev
```

## Data Sources

| Source | Data | Price |
|---|---|---|
| **Yahoo Finance** (yfinance) | Daily OHLCV, fundamentals (PE, ROE, etc) | Free |
| **idx.co.id** (IDX official) | Foreign buy/sell per stock, broker summary | Free |

## Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS v4, shadcn/ui
- **Backend**: FastAPI (Python), SQLAlchemy, Alembic
- **Database**: PostgreSQL + TimescaleDB
- **State**: Zustand, TanStack React Query
- **Charts**: TradingView Lightweight Charts

## Security & Auth Architecture

- **Access Token**: In-memory only via non-persisted Zustand store (`useAuthStore`).
- **Refresh Token**: Managed via `HttpOnly` secure cookies set by the FastAPI backend.
- **Session Bootstrap**: On mount, `SessionProvider` triggers `POST /api/v1/auth/refresh` to restore session.
- **Single-Flight Refresh**: Concurrent 401s merged into a single shared refresh promise.

## Quality Checks

```bash
pnpm lint
pnpm type-check
pnpm docs:check
pnpm build

pnpm verify:all   
```

## Documentation

- [Documentation index](docs/README.md) - Architecture, API, security, conventions, development, and more.
- A pre-commit hook runs `pnpm verify:fast` (lint + type-check + docs:check) automatically on commit.
- GitHub Actions CI runs lint, type-check, docs, build, and risk classification on every push/PR.
