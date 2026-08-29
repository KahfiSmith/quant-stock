"use client";

import Link from "next/link";
import { useState } from "react";

import { StateMessage } from "@/components/common";
import { StockChart } from "@/components/features/market/stock-chart";
import {
  useIDXStockDetail,
  useStockAiSummary,
  useStockFundamental,
  useStockPrices,
  useStockScore,
  useStockTechnical,
  type PriceRange,
} from "@/hooks/market";
import { toChartCandles } from "@/types";

type StockDetailProps = {
  symbol: string;
};

type RangeOption = {
  label: string;
  days: number;
};

type ActiveTab = "overview" | "chart" | "fundamentals" | "quant" | "flows" | "ai";

const RANGE_OPTIONS: RangeOption[] = [
  { label: "1M", days: 30 },
  { label: "3M", days: 90 },
  { label: "6M", days: 180 },
  { label: "1Y", days: 365 },
  { label: "All", days: 0 },
];

function rangeFor(days: number): PriceRange {
  if (days === 0) {
    return {};
  }
  const start = new Date();
  start.setDate(start.getDate() - days);
  return { start: start.toISOString().slice(0, 10) };
}

export function StockDetail({ symbol }: StockDetailProps) {
  const [days, setDays] = useState<number>(0);
  const [tab, setTab] = useState<ActiveTab>("overview");

  const { data, isPending, isError } = useStockPrices(symbol, rangeFor(days));
  const { data: idxDetail } = useIDXStockDetail(symbol);
  const { data: technical } = useStockTechnical(symbol);
  const { data: fundamental } = useStockFundamental(symbol);
  const { data: scoreData } = useStockScore(symbol);
  const { data: aiData, isPending: isAiPending } = useStockAiSummary(symbol);

  const latestCandle = data?.items && data.items.length > 0 ? data.items[data.items.length - 1] : null;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-6">
      {/* Header Banner */}
      <header className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-card p-6 shadow-sm">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">{symbol.toUpperCase()}</h1>
            {scoreData ? (
              <span className="rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground shadow-sm">
                Quant Score: {scoreData.total_score}/100
              </span>
            ) : null}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {latestCandle ? `Latest Close: IDR ${Number(latestCandle.close).toLocaleString()} | Volume: ${Number(latestCandle.volume).toLocaleString()}` : "Market Asset"}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/backtest"
            className="rounded-md border bg-background px-3 py-1.5 text-xs font-medium hover:bg-muted"
          >
            Backtest Strategy
          </Link>
          {technical ? (
            <span
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                technical.trend === "bullish"
                  ? "bg-green-500/10 text-green-600 dark:text-green-400"
                  : technical.trend === "bearish"
                    ? "bg-red-500/10 text-red-600 dark:text-red-400"
                    : "bg-muted text-muted-foreground"
              }`}
            >
              Trend: {technical.trend.toUpperCase()}
            </span>
          ) : null}
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="flex border-b border-border text-sm">
        <button
          type="button"
          onClick={() => setTab("overview")}
          className={`border-b-2 px-4 py-2.5 font-medium transition-colors ${
            tab === "overview"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Overview
        </button>
        <button
          type="button"
          onClick={() => setTab("chart")}
          className={`border-b-2 px-4 py-2.5 font-medium transition-colors ${
            tab === "chart"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Candlestick Chart
        </button>
        <button
          type="button"
          onClick={() => setTab("fundamentals")}
          className={`border-b-2 px-4 py-2.5 font-medium transition-colors ${
            tab === "fundamentals"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Financial Fundamentals
        </button>
        <button
          type="button"
          onClick={() => setTab("quant")}
          className={`border-b-2 px-4 py-2.5 font-medium transition-colors ${
            tab === "quant"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Quant Score Breakdown
        </button>
        <button
          type="button"
          onClick={() => setTab("flows")}
          className={`border-b-2 px-4 py-2.5 font-medium transition-colors ${
            tab === "flows"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          IDX Foreign Flow & Actions
        </button>
        <button
          type="button"
          onClick={() => setTab("ai")}
          className={`border-b-2 px-4 py-2.5 font-medium transition-colors ${
            tab === "ai"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          AI Analyst Insight
        </button>
      </div>

      {isPending ? (
        <StateMessage variant="loading" />
      ) : isError ? (
        <StateMessage variant="error">
          Failed to load price history for {symbol.toUpperCase()}.
        </StateMessage>
      ) : (
        <div className="space-y-6">
          {/* Tab 1: Overview */}
          {tab === "overview" && (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div className="flex flex-col gap-4 rounded-xl border bg-card p-5">
                <h3 className="text-base font-semibold">Technical Highlights</h3>
                {technical ? (
                  <dl className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <dt className="text-xs text-muted-foreground">RSI (14)</dt>
                      <dd className="font-semibold">{technical.rsi ?? "n/a"}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted-foreground">MA Signal</dt>
                      <dd className="font-semibold">{technical.ma_signal}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted-foreground">MA20 / MA50</dt>
                      <dd className="font-semibold">
                        {technical.indicators.ma20 ?? "—"} / {technical.indicators.ma50 ?? "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted-foreground">ATR (14)</dt>
                      <dd className="font-semibold">{technical.indicators.atr14 ?? "—"}</dd>
                    </div>
                  </dl>
                ) : (
                  <p className="text-sm text-muted-foreground">No technical summary available.</p>
                )}
              </div>

              <div className="flex flex-col gap-4 rounded-xl border bg-card p-5">
                <h3 className="text-base font-semibold">Fundamental Snapshot</h3>
                {fundamental ? (
                  <dl className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <dt className="text-xs text-muted-foreground">P/E Ratio</dt>
                      <dd className="font-semibold">{fundamental.ratios.pe_ratio ?? "—"}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted-foreground">P/B Ratio</dt>
                      <dd className="font-semibold">{fundamental.ratios.pb_ratio ?? "—"}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted-foreground">ROE</dt>
                      <dd className="font-semibold">
                        {fundamental.ratios.roe !== null ? `${(fundamental.ratios.roe * 100).toFixed(1)}%` : "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted-foreground">Revenue Growth</dt>
                      <dd className="font-semibold">
                        {fundamental.ratios.revenue_growth !== null ? `${(fundamental.ratios.revenue_growth * 100).toFixed(1)}%` : "—"}
                      </dd>
                    </div>
                  </dl>
                ) : (
                  <p className="text-sm text-muted-foreground">No fundamental ratios available.</p>
                )}
              </div>
            </div>
          )}

          {/* Tab 2: Candlestick Chart */}
          {tab === "chart" && (
            <div className="space-y-4 rounded-xl border bg-card p-5">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold">Price History (OHLCV)</h3>
                <div className="flex gap-1" role="group" aria-label="Price range">
                  {RANGE_OPTIONS.map((option) => {
                    const active = option.days === days;
                    return (
                      <button
                        key={option.label}
                        type="button"
                        onClick={() => setDays(option.days)}
                        className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                          active
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground hover:bg-muted/80"
                        }`}
                      >
                        {option.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <StockChart data={toChartCandles(data?.items ?? [])} />

              <dl className="flex flex-wrap gap-6 border-t pt-3 text-xs text-muted-foreground">
                <div>
                  <dt>Data Source</dt>
                  <dd className="font-medium text-foreground">{data?.data_source ?? "n/a"}</dd>
                </div>
                <div>
                  <dt>Total Candles</dt>
                  <dd className="font-medium text-foreground">{data?.pagination.total ?? 0}</dd>
                </div>
                <div>
                  <dt>As of</dt>
                  <dd className="font-medium text-foreground">
                    {data ? new Date(data.as_of).toLocaleDateString() : "n/a"}
                  </dd>
                </div>
              </dl>
            </div>
          )}

          {/* Tab 3: Financial Fundamentals */}
          {tab === "fundamentals" && (
            <div className="rounded-xl border bg-card p-5">
              <h3 className="mb-4 text-base font-semibold">Comprehensive Financial Health & Valuation</h3>
              {fundamental ? (
                <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-4">
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <p className="text-xs text-muted-foreground">Price / Earnings (P/E)</p>
                    <p className="mt-1 text-xl font-bold">{fundamental.ratios.pe_ratio ?? "—"}</p>
                  </div>
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <p className="text-xs text-muted-foreground">Price / Book (P/B)</p>
                    <p className="mt-1 text-xl font-bold">{fundamental.ratios.pb_ratio ?? "—"}</p>
                  </div>
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <p className="text-xs text-muted-foreground">Return on Equity (ROE)</p>
                    <p className="mt-1 text-xl font-bold">
                      {fundamental.ratios.roe !== null ? `${(fundamental.ratios.roe * 100).toFixed(2)}%` : "—"}
                    </p>
                  </div>
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <p className="text-xs text-muted-foreground">Return on Assets (ROA)</p>
                    <p className="mt-1 text-xl font-bold">
                      {fundamental.ratios.roa !== null ? `${(fundamental.ratios.roa * 100).toFixed(2)}%` : "—"}
                    </p>
                  </div>
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <p className="text-xs text-muted-foreground">Debt to Equity (D/E)</p>
                    <p className="mt-1 text-xl font-bold">{fundamental.ratios.debt_to_equity ?? "—"}</p>
                  </div>
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <p className="text-xs text-muted-foreground">Revenue Growth</p>
                    <p className="mt-1 text-xl font-bold">
                      {fundamental.ratios.revenue_growth !== null ? `${(fundamental.ratios.revenue_growth * 100).toFixed(2)}%` : "—"}
                    </p>
                  </div>
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <p className="text-xs text-muted-foreground">EPS Growth</p>
                    <p className="mt-1 text-xl font-bold">
                      {fundamental.ratios.eps_growth !== null ? `${(fundamental.ratios.eps_growth * 100).toFixed(2)}%` : "—"}
                    </p>
                  </div>
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <p className="text-xs text-muted-foreground">Period Basis</p>
                    <p className="mt-1 text-xl font-bold">{fundamental.period_type}</p>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No fundamental ratios available for this symbol.</p>
              )}
            </div>
          )}

          {/* Tab 4: Quant Score Breakdown */}
          {tab === "quant" && (
            <div className="rounded-xl border bg-card p-5">
              <h3 className="mb-4 text-base font-semibold">Multi-Factor Quantitative Model</h3>
              {scoreData ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
                    <div className="rounded-lg border bg-muted/10 p-3 text-center">
                      <p className="text-xs text-muted-foreground">Momentum (30%)</p>
                      <p className="mt-1 text-xl font-bold text-primary">{scoreData.factors.momentum}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 text-center">
                      <p className="text-xs text-muted-foreground">Quality (25%)</p>
                      <p className="mt-1 text-xl font-bold text-primary">{scoreData.factors.quality}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 text-center">
                      <p className="text-xs text-muted-foreground">Value (20%)</p>
                      <p className="mt-1 text-xl font-bold text-primary">{scoreData.factors.value}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 text-center">
                      <p className="text-xs text-muted-foreground">Risk (15%)</p>
                      <p className="mt-1 text-xl font-bold text-primary">{scoreData.factors.risk}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/10 p-3 text-center">
                      <p className="text-xs text-muted-foreground">Growth (10%)</p>
                      <p className="mt-1 text-xl font-bold text-primary">{scoreData.factors.growth}</p>
                    </div>
                  </div>

                  {/* Sector Relative Comparison */}
                  {scoreData.metadata.sector_relative ? (
                    <div className="rounded-lg border border-primary/20 bg-primary/5 p-4 text-xs space-y-2">
                      <p className="font-semibold text-primary">Sector Context ({scoreData.metadata.comparison_universe.sector ?? "General"})</p>
                      <div className="grid grid-cols-2 gap-4">
                        {scoreData.metadata.sector_relative.sector_avg_pe !== undefined ? (
                          <div>
                            <span className="text-muted-foreground">Sector Avg P/E: </span>
                            <span className="font-medium text-foreground">{scoreData.metadata.sector_relative.sector_avg_pe}</span>
                            {scoreData.metadata.sector_relative.pe_discount_pct !== null && (
                              <span className="ml-1 text-emerald-600 dark:text-emerald-400">
                                ({scoreData.metadata.sector_relative.pe_discount_pct}% discount)
                              </span>
                            )}
                          </div>
                        ) : null}
                        {scoreData.metadata.sector_relative.sector_avg_roe !== undefined ? (
                          <div>
                            <span className="text-muted-foreground">Sector Avg ROE: </span>
                            <span className="font-medium text-foreground">
                              {((scoreData.metadata.sector_relative.sector_avg_roe ?? 0) * 100).toFixed(2)}%
                            </span>
                            {scoreData.metadata.sector_relative.roe_spread_pct !== null && (
                              <span className="ml-1 text-emerald-600 dark:text-emerald-400">
                                ({scoreData.metadata.sector_relative.roe_spread_pct > 0 ? "+" : ""}
                                {scoreData.metadata.sector_relative.roe_spread_pct}%)
                              </span>
                            )}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  ) : null}

                  <div className="space-y-1 text-xs text-muted-foreground">
                    <p>
                      Model Version: {scoreData.score_version} | Completeness: {scoreData.data_quality} | Universe: {scoreData.metadata.comparison_universe.identifier} ({scoreData.metadata.comparison_universe.size})
                    </p>
                    {scoreData.metadata.missing_inputs.length > 0 ? (
                      <p>Unavailable inputs: {scoreData.metadata.missing_inputs.join(", ")}</p>
                    ) : null}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No quantitative score available for this symbol.</p>
              )}
            </div>
          )}

          {/* Tab 4.5: IDX Foreign Flow & Corporate Actions */}
          {tab === "flows" && (
            <div className="flex flex-col gap-6">
              {/* Foreign Flow History */}
              <div className="rounded-xl border bg-card overflow-hidden">
                <div className="border-b bg-muted/20 px-4 py-3">
                  <h3 className="text-sm font-semibold">Foreign Flow & Broker Concentration</h3>
                </div>
                <div className="max-h-72 overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b bg-muted/40 text-left text-muted-foreground">
                        <th className="px-4 py-2 font-medium">Date</th>
                        <th className="px-4 py-2 font-medium text-right">Foreign Buy (IDR)</th>
                        <th className="px-4 py-2 font-medium text-right">Foreign Sell (IDR)</th>
                        <th className="px-4 py-2 font-medium text-right">Net Foreign Flow</th>
                      </tr>
                    </thead>
                    <tbody>
                      {idxDetail?.market_flows?.map((flow) => (
                        <tr key={flow.date} className="border-b last:border-0 hover:bg-muted/10">
                          <td className="px-4 py-2 font-medium">{flow.date}</td>
                          <td className="px-4 py-2 text-right text-muted-foreground">
                            Rp {flow.foreign_buy_value.toLocaleString()}
                          </td>
                          <td className="px-4 py-2 text-right text-muted-foreground">
                            Rp {flow.foreign_sell_value.toLocaleString()}
                          </td>
                          <td
                            className={`px-4 py-2 text-right font-bold ${
                              flow.net_foreign_value >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                            }`}
                          >
                            {flow.net_foreign_value > 0 ? "+" : ""}
                            Rp {flow.net_foreign_value.toLocaleString()}
                          </td>
                        </tr>
                      )) || (
                        <tr>
                          <td colSpan={4} className="p-4 text-center text-muted-foreground">
                            No market flow history available.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Corporate Actions */}
              <div className="rounded-xl border bg-card p-5">
                <h3 className="mb-3 text-sm font-semibold">Corporate Actions (Dividends, Splits, Right Issues)</h3>
                {idxDetail?.corporate_actions && idxDetail.corporate_actions.length > 0 ? (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {idxDetail.corporate_actions.map((ca, idx) => (
                      <div key={idx} className="rounded-lg border bg-muted/20 p-3 text-xs">
                        <div className="flex items-center justify-between font-semibold">
                          <span className="text-primary">{ca.action_type}</span>
                          <span className="text-muted-foreground">Ex-Date: {ca.ex_date}</span>
                        </div>
                        {ca.cash_amount && (
                          <p className="mt-1 text-foreground">Cash Dividend: Rp {ca.cash_amount} / share</p>
                        )}
                        {ca.ratio_from && ca.ratio_to && (
                          <p className="mt-1 text-foreground">Ratio: {ca.ratio_from} : {ca.ratio_to}</p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">No recent corporate actions recorded.</p>
                )}
              </div>
            </div>
          )}

          {/* Tab 5: AI Analyst Insight */}
          {tab === "ai" && (
            <div className="space-y-6 rounded-xl border bg-card p-6">
              <div>
                <h3 className="text-lg font-bold">AI Analyst Synthesis</h3>
                <p className="text-xs text-muted-foreground">Automated multi-factor evaluation of {symbol.toUpperCase()}</p>
              </div>

              {isAiPending ? (
                <StateMessage variant="loading" />
              ) : aiData ? (
                <div className="space-y-6">
                  {/* Conclusion Card */}
                  <div className="rounded-lg border border-primary/30 bg-primary/5 p-4">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-primary">Executive Synthesis</h4>
                    <p className="mt-2 text-sm leading-relaxed text-foreground">{aiData.conclusion}</p>
                  </div>

                  {/* Strengths & Risks Grid */}
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="rounded-lg border border-green-500/30 bg-green-500/5 p-4">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-green-600 dark:text-green-400">
                        Key Strengths & Catalysts
                      </h4>
                      <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
                        {aiData.strengths.map((s, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-green-500">✓</span>
                            <span>{s}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-red-600 dark:text-red-400">
                        Identified Risks & Vulnerabilities
                      </h4>
                      <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
                        {aiData.risks.map((r, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-red-500">⚠</span>
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Unknowns / Macro Considerations */}
                  <div className="rounded-lg border bg-muted/20 p-4">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Unknowns & Macro Factors
                    </h4>
                    <ul className="mt-2 list-disc pl-5 text-xs text-muted-foreground">
                      {aiData.unknowns.map((u, idx) => (
                        <li key={idx}>{u}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="rounded-lg border bg-muted/20 p-4 text-xs text-muted-foreground">
                    <p className="font-semibold text-foreground">Supporting Facts</p>
                    <ul className="mt-2 space-y-1">
                      {aiData.evidence.map((fact) => (
                        <li key={`${fact.category}-${fact.metric}`}>
                          {fact.metric}: {fact.value ?? "unavailable"} ({fact.source ?? "unknown source"})
                        </li>
                      ))}
                    </ul>
                    {aiData.data_unavailable.length > 0 ? (
                      <p className="mt-2">Unavailable: {aiData.data_unavailable.join(", ")}</p>
                    ) : null}
                    <p className="mt-2">Analysis version: {aiData.analysis_version} | Quality: {aiData.data_quality}</p>
                  </div>

                  {/* Disclaimer */}
                  <p className="border-t pt-3 text-[11px] italic text-muted-foreground">
                    {aiData.disclaimer}
                  </p>
                </div>
              ) : (
                <StateMessage variant="error">Unable to synthesize AI report at this time.</StateMessage>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
