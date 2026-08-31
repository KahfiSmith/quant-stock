# Developer Setup and Commands

## Prerequisites

- Node.js 20+ and pnpm 10.x
- Python 3.12 for host-mode FastAPI development, or Docker with Compose

## Local stack

```bash
cp .env.example .env.local
docker compose up --build
```

This starts the Next.js frontend at `http://localhost:3000`, FastAPI at `http://localhost:8000`, and PostgreSQL with TimescaleDB at `localhost:5432`. The API applies Alembic migrations before starting.

For frontend-only development, run `pnpm dev` and ensure `NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000` is configured.

For API host-mode development:

```bash
cd apps/quant-api
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --port 8000
```

## Verification

- Frontend: `pnpm lint`, `pnpm type-check`, `pnpm docs:check`
- API: `.venv/bin/ruff check .`, `.venv/bin/pytest -q`
- Service endpoints: `GET /health`, `GET /ready`

## Ingesting real market data

After a fresh stack start, the `stocks` table is empty and the screener will
show no data. The platform has two data sources that complement each other:

| Source | Data | Script |
|---|---|---|
| **yfinance** (Yahoo Finance) | OHLCV harian, fundamentals (PE, ROE, etc) | `backfill_market_data` |
| **idx.co.id** (BEI resmi) | Foreign buy/sell per saham, broker summary | `backfill_idx_data` |

### Step 1 — Apply database migrations

```bash
# Via Docker (recommended)
docker compose exec quant-api alembic upgrade head

# Atau host-mode
cd apps/quant-api
.venv/bin/alembic upgrade head
```

### Step 2 — Backfill OHLCV + Fundamentals (yfinance)

Mengambil 2 tahun data harga harian dan rasio fundamental dari Yahoo Finance
untuk ~90 saham IDX liquid. Dibutuhkan untuk chart, technical indicators,
quant score, dan backtest.

```bash
# Via Docker
docker compose exec quant-api python -m scripts.backfill_market_data

# Atau host-mode
cd apps/quant-api
.venv/bin/python -m scripts.backfill_market_data
```

Opsi:
```bash
# Hanya saham tertentu
docker compose exec quant-api python -m scripts.backfill_market_data --symbols BBCA,BMRI,TLKM

# Period lebih panjang
docker compose exec quant-api python -m scripts.backfill_market_data --period 5y

# Skip fundamentals (hanya harga)
docker compose exec quant-api python -m scripts.backfill_market_data --skip-fundamentals

# Rate limit lebih lambat (default 1 detik)
docker compose exec quant-api python -m scripts.backfill_market_data --rate-limit-seconds 8.0
```

#### Troubleshooting: Yahoo Finance 429 (Too Many Requests)

Yahoo Finance gratis memiliki batas rate limit yang ketat. Kalau muncul error
`429 Client Error: Too Many Requests`:

1. **Stop script** (Ctrl+C).
2. **Tunggu 30 menit** — biarkan Yahoo reset throttle IP kamu.
3. **Jalankan ulang dengan batch kecil dan rate limit lambat**:
   ```bash
   docker compose exec quant-api python -m scripts.backfill_market_data \
     --symbols BBCA,BMRI,BBRI,TLKM,ASII,UNVR,BBNI,SIDO,ICBP,KLBF \
     --rate-limit-seconds 8.0
   ```
4. Setelah batch pertama sukses, tambahkan symbol lainnya di batch berikutnya.

Data yang sudah ter-ingest sebelum error **tetap tersimpan** — script bersifat
idempotent, jadi aman dijalankan ulang.

> **Tip**: Error `Permission denied: '/nonexistent/.cache/py-yfinance'` di Docker
> bisa diabaikan — ini hanya warning cache folder, tidak mempengaruhi data.

### Step 3 — Backfill Foreign Flow + Broker Summary (idx.co.id)

Mengambil data dari website resmi BEI. Dibutuhkan untuk foreign flow analysis
dan broker activity monitoring. **Script ini menggunakan sumber berbeda dari
yfinance**, jadi tidak terpengaruh oleh Yahoo 429 rate limit.

- **Stock summary**: Foreign buy/sell per saham per hari (masuk ke tabel `market_flows_idx`)
- **Broker summary**: Aktivitas trading per broker per hari (masuk ke tabel `broker_summary_idx`)

```bash
# Via Docker — 30 hari terakhir (recommended untuk mulai)
docker compose exec quant-api python -m scripts.backfill_idx_data --range 30

# Atau host-mode
cd apps/quant-api
.venv/bin/python -m scripts.backfill_idx_data --range 30
```

Opsi:
```bash
# Tanggal spesifik
docker compose exec quant-api python -m scripts.backfill_idx_data --date 20260828

# Hanya foreign flow (skip broker)
docker compose exec quant-api python -m scripts.backfill_idx_data --range 30 --skip-broker

# Hanya broker summary (skip foreign flow)
docker compose exec quant-api python -m scripts.backfill_idx_data --range 30 --skip-stock

# Perlambat request kalau kena rate limit
docker compose exec quant-api python -m scripts.backfill_idx_data --range 30 --rate-limit 3.0
```

### Daily update (setelah market tutup)

Jalankan kedua script untuk update data hari ini:

```bash
docker compose exec quant-api python -m scripts.backfill_market_data
docker compose exec quant-api python -m scripts.backfill_idx_data
```

Semua script bersifat **idempotent** — aman dijalankan berkali-kali tanpa
duplikasi data.

### Urutan yang disarankan

Kedua script **saling melengkapi**, bukan duplikasi:

| Script | Data | Dipakai oleh |
|---|---|---|
| `backfill_market_data` | Harga OHLCV, fundamentals (PE, ROE) | Chart, technical indicators, quant score, screener, backtest |
| `backfill_idx_data` | Foreign buy/sell, broker activity | Foreign flow tab di stock detail, broker summary endpoint |

Kalau yfinance kena 429, **jalankan `backfill_idx_data` duluan** — data foreign
flow dan broker summary akan langsung tersedia. Lalu retry yfinance setelah
30 menit.

### Catatan

- Data yfinance bersifat EOD (end-of-day) dengan lag ~1 hari perdagangan.
- Data idx.co.id hanya tersedia untuk tanggal yang sudah lewat, bukan real-time.
- Weekend dan hari libur bursa otomatis di-skip oleh kedua script.
- Request pertama ke idx.co.id butuh bootstrap session cookie (~3 detik).
- Kedua script bersifat **idempotent** — aman dijalankan berkali-kali.
- Untuk development tanpa koneksi internet, gunakan `MARKET_DATA_PROVIDER=sample`
  dan jalankan `python -m scripts.seed_market_data` untuk data sintetis.
