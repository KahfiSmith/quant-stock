"use client";

import { useState } from "react";

import { StateMessage } from "@/components/common";
import { StockChart } from "@/components/features/market/stock-chart";
import {
  useStockFundamental,
  useStockPrices,
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
  const { data, isPending, isError } = useStockPrices(symbol, rangeFor(days));
  const { data: technical } = useStockTechnical(symbol);
  const { data: fundamental } = useStockFundamental(symbol);

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 p-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-primary">Market data</p>
          <h1 className="text-2xl font-semibold tracking-tight">{symbol.toUpperCase()}</h1>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          {technical ? (
            <>
              <span
                className={`rounded-full px-2.5 py-0.5 font-medium ${
                  technical.trend === "bullish"
                    ? "bg-green-500/10 text-green-600 dark:text-green-400"
                    : technical.trend === "bearish"
                      ? "bg-red-500/10 text-red-600 dark:text-red-400"
                      : "bg-muted text-muted-foreground"
                }`}
              >
                Trend: {technical.trend}
              </span>
              {technical.rsi !== null ? (
                <span className="rounded-full bg-muted px-2.5 py-0.5 font-medium text-foreground">
                  RSI(14): {technical.rsi}
                </span>
              ) : null}
            </>
          ) : null}
          {fundamental?.score !== null && fundamental?.score !== undefined ? (
            <span className="rounded-full bg-primary/10 px-2.5 py-0.5 font-medium text-primary">
              Fundamental Score: {fundamental.score}/100
            </span>
          ) : null}
        </div>
      </header>

      <div className="flex gap-2" role="group" aria-label="Price range">
        {RANGE_OPTIONS.map((option) => {
          const active = option.days === days;
          return (
            <button
              key={option.label}
              type="button"
              onClick={() => setDays(option.days)}
              className={`rounded-md px-3 py-1 text-sm transition-colors ${
                active
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/60"
              }`}
            >
              {option.label}
            </button>
          );
        })}
      </div>

      {isPending ? (
        <StateMessage variant="loading" />
      ) : isError ? (
        <StateMessage variant="error">
          Failed to load price history for {symbol.toUpperCase()}.
        </StateMessage>
      ) : (
        <div className="space-y-4">
          <StockChart data={toChartCandles(data?.items ?? [])} />

          <dl className="flex flex-wrap gap-4 text-sm">
            <div>
              <dt className="text-muted-foreground">Data source</dt>
              <dd className="font-medium">{data?.data_source ?? "n/a"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Candles</dt>
              <dd className="font-medium">{data?.pagination.total ?? 0}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">As of</dt>
              <dd className="font-medium">
                {data ? new Date(data.as_of).toLocaleString() : "n/a"}
              </dd>
            </div>
            {technical ? (
              <>
                <div>
                  <dt className="text-muted-foreground">MA20</dt>
                  <dd className="font-medium">{technical.indicators.ma20 ?? "n/a"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">MA50</dt>
                  <dd className="font-medium">{technical.indicators.ma50 ?? "n/a"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">MA200</dt>
                  <dd className="font-medium">{technical.indicators.ma200 ?? "n/a"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">ATR(14)</dt>
                  <dd className="font-medium">{technical.indicators.atr14 ?? "n/a"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">MACD Line / Signal</dt>
                  <dd className="font-medium">
                    {technical.indicators.macd.line ?? "n/a"} / {technical.indicators.macd.signal ?? "n/a"}
                  </dd>
                </div>
              </>
            ) : null}
            {fundamental ? (
              <>
                <div>
                  <dt className="text-muted-foreground">P/E Ratio</dt>
                  <dd className="font-medium">{fundamental.ratios.pe_ratio ?? "n/a"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">P/B Ratio</dt>
                  <dd className="font-medium">{fundamental.ratios.pb_ratio ?? "n/a"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">ROE</dt>
                  <dd className="font-medium">
                    {fundamental.ratios.roe !== null ? `${(fundamental.ratios.roe * 100).toFixed(1)}%` : "n/a"}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">D/E</dt>
                  <dd className="font-medium">{fundamental.ratios.debt_to_equity ?? "n/a"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Rev Growth</dt>
                  <dd className="font-medium">
                    {fundamental.ratios.revenue_growth !== null ? `${(fundamental.ratios.revenue_growth * 100).toFixed(1)}%` : "n/a"}
                  </dd>
                </div>
              </>
            ) : null}
          </dl>
        </div>
      )}
    </div>
  );
}