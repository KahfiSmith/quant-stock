import type { Metadata } from "next";

import { IDXFactorRotationRunner } from "@/components/features/market";

export const metadata: Metadata = {
  title: "IDX Factor Rotation Backtesting Engine",
  description: "Simulate multi-asset factor rotation strategies across the IDX listed universe benchmarked against IHSG (^JKSE).",
};

export default function BacktestPage() {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-6">
      <header>
        <p className="text-sm font-medium text-primary">IDX Quantitative Simulation</p>
        <h1 className="text-2xl font-semibold tracking-tight">IDX Factor Rotation Backtesting</h1>
        <p className="text-xs text-muted-foreground mt-1">
          Monthly rebalancing simulation across active BEI stocks with liquidity filters and IHSG composite benchmark.
        </p>
      </header>

      <IDXFactorRotationRunner />
    </div>
  );
}
