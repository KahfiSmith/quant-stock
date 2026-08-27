import type { Metadata } from "next";

import { BacktestRunner } from "@/components/features/market";

export const metadata: Metadata = {
  title: "Strategy Backtesting Engine",
  description: "Simulate quantitative strategies (SMA Crossover, RSI Momentum, Buy & Hold) against historical data.",
};

export default function BacktestPage() {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-6">
      <header>
        <p className="text-sm font-medium text-primary">Quantitative Simulation</p>
        <h1 className="text-2xl font-semibold tracking-tight">Strategy Backtest Engine</h1>
      </header>

      <BacktestRunner />
    </div>
  );
}
