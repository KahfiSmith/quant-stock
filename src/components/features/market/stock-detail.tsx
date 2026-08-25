"use client";

import { Loader2 } from "lucide-react";

import { StockChart } from "@/components/features/market/stock-chart";
import { useStockPrices } from "@/hooks/market";
import { toChartCandles } from "@/types";

type StockDetailProps = {
  symbol: string;
};

export function StockDetail({ symbol }: StockDetailProps) {
  const { data, isPending, isError } = useStockPrices(symbol);

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 p-6">
      <header>
        <p className="text-sm font-medium text-primary">Market data</p>
        <h1 className="text-2xl font-semibold tracking-tight">{symbol.toUpperCase()}</h1>
      </header>

      {isPending ? (
        <div className="flex items-center justify-center p-6 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      ) : isError ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load price history for {symbol.toUpperCase()}.
        </div>
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
          </dl>
        </div>
      )}
    </div>
  );
}