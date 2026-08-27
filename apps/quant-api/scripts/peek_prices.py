"""Read current prices for the configured universe; print symbols >= Rp 2.000.

Usage: from apps/quant-api/, run `python -m scripts.peek_prices`.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import yfinance


def _read_symbols() -> list[str]:
    with open(".env") as f:
        for line in f:
            if line.startswith("YFINANCE_SYMBOLS="):
                return [s.strip() for s in line.split("=", 1)[1].split(",") if s.strip()]
    raise RuntimeError("YFINANCE_SYMBOLS not found in .env")


def get_price(sym: str) -> tuple[str, float | None]:
    try:
        t = yfinance.Ticker(f"{sym}.JK")
        hist = t.history(period="5d", auto_adjust=True)
        if hist is None or hist.empty:
            return sym, None
        return sym, float(hist["Close"].iloc[-1])
    except Exception:
        return sym, None


def main() -> None:
    symbols = _read_symbols()
    results: dict[str, float | None] = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for sym, price in ex.map(get_price, symbols):
            results[sym] = price

    sorted_prices = sorted(
        results.items(), key=lambda x: (x[1] is None, -(x[1] or 0))
    )

    print(f"{'Symbol':<10} {'Price (IDR)':>15}")
    print("-" * 30)
    for sym, price in sorted_prices:
        if price is None:
            print(f"{sym:<10} {'N/A':>15}")
        else:
            print(f"{sym:<10} {price:>15,.0f}")

    print("\n=== Saham >= Rp 2.000 ===")
    above = [(s, p) for s, p in sorted_prices if p is not None and p >= 2000]
    print(f"Count: {len(above)}")
    for s, p in above:
        print(f"  {s:<10} Rp {p:>10,.0f}")


if __name__ == "__main__":
    main()
