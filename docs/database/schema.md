# Database Architecture & Schemas

QuantLens utilizes **PostgreSQL** for relational application data and **TimescaleDB** (PostgreSQL extension) for high-frequency time-series market price data.

## Target Database Engines

- **PostgreSQL 16+**: Users, auth sessions, portfolios, transactions, company fundamentals.
- **TimescaleDB**: `prices` hypertable partitioned by time (`date`/`timestamp`) for optimized historical OHLCV queries and analytical rollups.

---

## Core Entities & Schemas

### 1. Users & Authentication (`PostgreSQL`)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL,
    user_agent TEXT,
    ip_address VARCHAR(45),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 2. Market Data (`PostgreSQL + TimescaleDB`)

#### `stocks` (Master Saham)
```sql
CREATE TABLE stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,  -- e.g. 'BBCA'
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `prices` (Time-series OHLCV Hypertable)
```sql
CREATE TABLE prices (
    time TIMESTAMPTZ NOT NULL,
    stock_id INT REFERENCES stocks(id) ON DELETE CASCADE,
    open NUMERIC(12, 4) NOT NULL,
    high NUMERIC(12, 4) NOT NULL,
    low NUMERIC(12, 4) NOT NULL,
    close NUMERIC(12, 4) NOT NULL,
    volume BIGINT NOT NULL
);

-- Convert to TimescaleDB Hypertable
SELECT create_hypertable('prices', 'time');

CREATE INDEX ix_prices_stock_time ON prices (stock_id, time DESC);
```

---

### 3. Fundamentals & Quant Scores (`PostgreSQL`)

```sql
CREATE TABLE fundamentals (
    id SERIAL PRIMARY KEY,
    stock_id INT REFERENCES stocks(id) ON DELETE CASCADE,
    period_date DATE NOT NULL,
    per NUMERIC(8, 2),
    pbv NUMERIC(8, 2),
    roe NUMERIC(8, 4),
    roa NUMERIC(8, 4),
    debt_to_equity NUMERIC(8, 4),
    revenue_growth NUMERIC(8, 4),
    eps_growth NUMERIC(8, 4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE quant_scores (
    id SERIAL PRIMARY KEY,
    stock_id INT REFERENCES stocks(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_score NUMERIC(5, 2) NOT NULL,    -- 0 - 100
    momentum_score NUMERIC(5, 2),
    quality_score NUMERIC(5, 2),
    value_score NUMERIC(5, 2),
    risk_score NUMERIC(5, 2),
    growth_score NUMERIC(5, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_stock_score_date UNIQUE (stock_id, date)
);
```

---

### 4. Portfolio Management (`PostgreSQL`)

```sql
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    stock_id INT REFERENCES stocks(id),
    type VARCHAR(10) NOT NULL,            -- 'BUY' | 'SELL'
    shares INT NOT NULL,
    price_per_share NUMERIC(12, 2) NOT NULL,
    transaction_date TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Migration Protocol

Setiap perubahan database:
1. Buat migration file terisolasi melalui Alembic di `packages/database` atau `apps/quant-api`.
2. Update SQLAlchemy ORM models.
3. Update Pydantic schemas.
4. Update TypeScript types (`src/types/`).
