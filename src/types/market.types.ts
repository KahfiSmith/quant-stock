export interface Stock {
  id: number;
  symbol: string;
  name: string;
  sector: string | null; // IDX-IC Sector
  sub_sector?: string | null; // IDX-IC Sub-Sector
  listing_date?: string | null;
  liquidity_status?: "liquid" | "watchlist" | "illiquid" | string;
  is_active?: boolean;
  board?: string | null;
  avg_daily_turnover_20d?: number | null;
  avg_daily_frequency_20d?: number | null;
  exchange: string | null;
  currency: string;
  timezone: string | null;
  market_cap: number | null;
  updated_at: string | null;
  close_price?: number | null;
  pe_ratio?: number | null;
  pb_ratio?: number | null;
  roe?: number | null;
  roa?: number | null;
  quant_score?: number | null;
  composite_rank?: number | null;
  percentile?: number | null;
}

export interface IDXMarketFlow {
  date: string;
  foreign_buy_value: number;
  foreign_sell_value: number;
  net_foreign_value: number;
  foreign_buy_volume: number;
  foreign_sell_volume: number;
  top3_buyer_broker_val?: number | null;
  top3_seller_broker_val?: number | null;
}

export interface IDXCorporateAction {
  action_type: "DIVIDEND" | "STOCK_SPLIT" | "RIGHT_ISSUE" | string;
  cum_date?: string | null;
  ex_date: string;
  recording_date?: string | null;
  payment_date?: string | null;
  ratio_from?: number | null;
  ratio_to?: number | null;
  cash_amount?: number | null;
  exercise_price?: number | null;
}

export interface IDXStockDetailResponse {
  stock: Stock;
  market_flows: IDXMarketFlow[];
  corporate_actions: IDXCorporateAction[];
  as_of: string;
}

export interface IDXRotationEquityPoint {
  date: string;
  equity: number;
  benchmark: number; // IHSG (^JKSE)
  drawdown: number;
}

export interface IDXRotationRebalanceEvent {
  date: string;
  selected_symbols: string[];
  portfolio_value: number;
  cash_reserve: number;
}

export interface IDXRotationSummary {
  total_return_pct: number;
  cagr_pct: number;
  benchmark_return_pct: number;
  alpha_pct: number;
  beta: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  annualized_volatility_pct: number;
  final_equity: number;
  rebalance_count: number;
}

export interface IDXFactorRotationResponse {
  run_id: string;
  strategy_name: string;
  initial_capital: number;
  start_date: string;
  end_date: string;
  summary: IDXRotationSummary;
  equity_curve: IDXRotationEquityPoint[];
  rebalance_history: IDXRotationRebalanceEvent[];
  benchmark_name: string;
  as_of: string;
}

export interface IDXFactorRotationParams {
  strategy_name: string;
  initial_capital: number;
  top_n: number;
  rebalance_frequency: "monthly" | "quarterly";
  start_date?: string | null;
  end_date?: string | null;
  min_market_cap?: number;
  min_adv_turnover?: number;
  min_frequency?: number;
  sector_filter?: string | null;
  factor_weights?: CustomFactorWeights;
  fee_percent?: number;
  slippage_percent?: number;
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
  source_record_id?: string | null;
  retrieved_at?: string | null;
  payload_checksum?: string | null;
  validation_state?: string;
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

export interface AiEvidence {
  category: string;
  metric: string;
  value: number | string | null;
  source: string | null;
  as_of: string | null;
  period_end: string | null;
  score_version: string | null;
}

export interface AiAnalystResponse {
  symbol: string;
  strengths: string[];
  risks: string[];
  unknowns: string[];
  conclusion: string;
  disclaimer: string;
  as_of: string;
  analysis_version: string;
  data_quality: string;
  data_used: string[];
  data_unavailable: string[];
  evidence: AiEvidence[];
}

export interface EquityPoint {
  time: string;
  equity: number;
  benchmark: number;
  drawdown: number;
}

export interface BacktestSummary {
  total_return_pct: number;
  cagr_pct: number;
  annualized_volatility_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown_pct: number;
  total_trades: number;
  win_rate_pct: number;
  final_equity: number;
}

export interface BacktestMetadata {
  run_id: string;
  status: "succeeded";
  status_history: ("queued" | "running" | "succeeded" | "failed")[];
  retry_policy: string;
  dataset_id: string;
  dataset_version: string;
  strategy_id: string;
  strategy_version: string;
  requested_start_date: string | null;
  requested_end_date: string | null;
  effective_start_date: string;
  effective_end_date: string;
  warmup_bars: number;
  evaluation_bars: number;
  universe: string[];
  execution_price: string;
  fee_percent: number;
  slippage_percent: number;
  initial_cash: number;
  cash_policy: string;
  lot_rounding: string;
  corporate_action_policy: string;
  benchmark: string;
  risk_free_rate: number;
  last_data_timestamp: string;
}

export interface BacktestResponse {
  symbol: string;
  strategy: string;
  initial_capital: number;
  summary: BacktestSummary;
  equity_curve: EquityPoint[];
  metadata: BacktestMetadata;
  as_of: string;
}

export interface BacktestParams {
  symbol: string;
  strategy: "SMA_CROSSOVER" | "RSI_MOMENTUM" | "BUY_AND_HOLD";
  initial_capital?: number;
  fast_period?: number;
  slow_period?: number;
  rsi_oversold?: number;
  rsi_overbought?: number;
  fee_percent?: number;
  slippage_percent?: number;
}

export interface PortfolioSummary {
  id: number;
  name: string;
  description: string | null;
  currency: string;
  created_at: string;
  updated_at: string;
}

export interface PortfolioHolding {
  stock_id: number;
  symbol: string;
  name: string;
  quantity: number;
  avg_buy_price: number;
  current_price: number | null;
  current_value: number | null;
  unrealized_pnl: number | null;
  unrealized_pnl_percent: number | null;
}

export interface PortfolioRisk {
  annualized_volatility_percent: number;
  max_holding_concentration_percent: number;
  observations: number;
}

export interface PortfolioDetail {
  id: number;
  name: string;
  description: string | null;
  currency: string;
  total_cost: number;
  current_value: number;
  total_realized_pnl: number;
  total_unrealized_pnl: number;
  total_unrealized_pnl_percent: number;
  holdings: PortfolioHolding[];
  risk: PortfolioRisk;
  created_at: string;
  updated_at: string;
}

export interface CreatePortfolioInput {
  name: string;
  description?: string;
  currency?: string;
}

export interface UpdatePortfolioInput {
  name?: string;
  description?: string | null;
  currency?: string;
}

export interface CreateTransactionInput {
  symbol: string;
  transaction_type: "BUY" | "SELL";
  quantity: number;
  price: number;
  fee?: number;
}

export interface ScreenerItem {
  id: number;
  symbol: string;
  name: string;
  sector: string | null;
  market_cap: number | null;
  currency: string;
  close_price: number | null;
  quant_score: number | null;
  score_version: string | null;
  data_source: string | null;
  price_as_of?: string | null;
  as_of: string | null;
  pe_ratio: number | null;
  pb_ratio: number | null;
  roe: number | null;
  rsi: number | null;
  trend: string;
  signal?: "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL";
  risk_level?: "LOW" | "MEDIUM" | "HIGH";
  signal_confidence_pct?: number | null;
  signal_reasons?: string[];
  value_score?: number | null;
  quality_score?: number | null;
  momentum_score?: number | null;
  growth_score?: number | null;
  risk_score?: number | null;
  composite_rank?: number | null;
  percentile?: number | null;
}

export interface CustomFactorWeights {
  momentum: number;
  quality: number;
  value: number;
  risk: number;
  growth: number;
}

export interface ScreenerFilterParams {
  search?: string;
  exchange?: string;
  sector?: string;
  min_market_cap?: number;
  max_market_cap?: number;
  min_score?: number;
  max_score?: number;
  min_pe?: number;
  max_pe?: number;
  min_pb?: number;
  max_pb?: number;
  min_roe?: number;
  min_rsi?: number;
  max_rsi?: number;
  strategy_preset?: "none" | "quality_momentum" | "deep_value" | "garp" | "defensive_income";
  custom_weights?: CustomFactorWeights;
  sort_by?: "score" | "symbol" | "market_cap" | "pe_ratio" | "pb_ratio" | "roe" | "rsi" | "value_score" | "quality_score" | "momentum_score" | "composite_rank";
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export interface ScreenerResponse {
  items: ScreenerItem[];
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

export interface QuantUniverse {
  identifier: string;
  size: number;
  sector?: string | null;
  sector_rank?: number | null;
  sector_total?: number | null;
  percentile?: number | null;
}

export interface QuantMetadata {
  model_version: string;
  methodology_version: string;
  raw_inputs: Record<string, number | null>;
  missing_inputs: string[];
  weights: Record<string, number>;
  normalization: Record<string, string>;
  reason_codes: string[];
  comparison_universe: QuantUniverse;
  technical_as_of: string | null;
  fundamental_period_end: string | null;
  fundamental_published_at: string | null;
  price_as_of: string | null;
  sector_relative?: Record<string, number | null> | null;
}

export interface QuantScoreResponse {
  symbol: string;
  as_of: string;
  score_version: string;
  total_score: number;
  factors: QuantFactors;
  data_quality: "complete" | "partial" | "insufficient" | string;
  metadata: QuantMetadata;
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
  currency: string | null;
  period_type: string;
  score: number | null;
  ratios: FundamentalRatios;
  source: string;
  source_record_id: string | null;
  retrieved_at: string | null;
  payload_checksum: string | null;
  validation_state: string;
  units: Record<string, string>;
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