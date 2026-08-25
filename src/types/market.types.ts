export interface Stock {
  id: number;
  symbol: string;
  name: string;
  sector: string | null;
  exchange: string | null;
  currency: string;
  timezone: string | null;
  market_cap: number | null;
  updated_at: string | null;
}

export interface PriceCandle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  interval: string;
  source: string;
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface StocksPage {
  items: Stock[];
  pagination: PaginationMeta;
  as_of: string;
}

export interface PricesResponse {
  symbol: string;
  data_source: string;
  items: PriceCandle[];
  pagination: PaginationMeta;
  as_of: string;
}

/** Candle shape consumed by TradingView Lightweight Charts. */
export interface ChartCandle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

/**
 * Maps backend price candles to chart-ready candles, converting the ISO
 * timestamp to a `YYYY-MM-DD` date string (a native Lightweight Charts `Time`)
 * and ensuring numeric price fields.
 */
export function toChartCandles(candles: PriceCandle[]): ChartCandle[] {
  return candles.map((candle) => ({
    time: candle.time.slice(0, 10),
    open: Number(candle.open),
    high: Number(candle.high),
    low: Number(candle.low),
    close: Number(candle.close),
  }));
}