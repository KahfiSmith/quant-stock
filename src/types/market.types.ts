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

export interface QuantFactors {
  momentum: number;
  quality: number;
  value: number;
  risk: number;
  growth: number;
}

export interface QuantScoreResponse {
  symbol: string;
  as_of: string;
  score_version: string;
  total_score: number;
  factors: QuantFactors;
  data_quality: "complete" | "partial" | "insufficient" | string;
}

export interface FundamentalRatios {
  pe_ratio: number | null;
  pb_ratio: number | null;
  roe: number | null;
  roa: number | null;
  debt_to_equity: number | null;
  revenue_growth: number | null;
  eps_growth: number | null;
}

export interface FundamentalResponse {
  symbol: string;
  period_end: string;
  published_at: string | null;
  period_type: string;
  score: number | null;
  ratios: FundamentalRatios;
  source: string;
  as_of: string;
}

export interface BollingerBand {
  middle: number | null;
  upper: number | null;
  lower: number | null;
}

export interface MacdIndicator {
  line: number | null;
  signal: number | null;
  histogram: number | null;
}

export interface IndicatorsSummary {
  ma20: number | null;
  ma50: number | null;
  ma200: number | null;
  rsi14: number | null;
  atr14: number | null;
  macd: MacdIndicator;
  bollinger: BollingerBand;
}

export interface TechnicalAnalysisResponse {
  symbol: string;
  interval: string;
  as_of: string;
  trend: "bullish" | "bearish" | "neutral" | string;
  rsi: number | null;
  ma_signal: "positive" | "negative" | "neutral" | string;
  indicators: IndicatorsSummary;
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