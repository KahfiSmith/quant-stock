"use client";

import { useState } from "react";

import { StateMessage } from "@/components/common";
import { useRunBacktest } from "@/hooks/market";
import type { BacktestParams, BacktestResponse } from "@/types";

export function BacktestRunner() {
  const [params, setParams] = useState<BacktestParams>({
    symbol: "BBCA",
    strategy: "SMA_CROSSOVER",
    initial_capital: 100_000_000,
    fast_period: 20,
    slow_period: 50,
  });

  const [result, setResult] = useState<BacktestResponse | null>(null);
  const runBacktest = useRunBacktest();

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!params.symbol) return;
    const res = await runBacktest.mutateAsync(params);
    setResult(res);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Parameter Form */}
      <form onSubmit={handleRun} className="flex flex-wrap items-center gap-3 rounded-xl border bg-card p-4">
        <input
          type="text"
          placeholder="Ticker (e.g. BBCA)"
          className="w-28 rounded-md border bg-background px-3 py-1.5 text-sm"
          value={params.symbol}
          onChange={(e) => setParams((p) => ({ ...p, symbol: e.target.value.toUpperCase() }))}
        />

        <select
          className="rounded-md border bg-background px-3 py-1.5 text-sm"
          value={params.strategy}
          onChange={(e) =>
            setParams((p) => ({ ...p, strategy: e.target.value as BacktestParams["strategy"] }))
          }
        >
          <option value="SMA_CROSSOVER">SMA Crossover (Fast/Slow)</option>
          <option value="RSI_MOMENTUM">RSI Mean Reversion</option>
          <option value="BUY_AND_HOLD">Buy & Hold</option>
        </select>

        {params.strategy === "SMA_CROSSOVER" && (
          <>
            <input
              type="number"
              placeholder="Fast"
              className="w-20 rounded-md border bg-background px-3 py-1.5 text-sm"
              value={params.fast_period}
              onChange={(e) => setParams((p) => ({ ...p, fast_period: parseInt(e.target.value) || 20 }))}
            />
            <input
              type="number"
              placeholder="Slow"
              className="w-20 rounded-md border bg-background px-3 py-1.5 text-sm"
              value={params.slow_period}
              onChange={(e) => setParams((p) => ({ ...p, slow_period: parseInt(e.target.value) || 50 }))}
            />
          </>
        )}

        <input
         type="number"
         min="0"
         max="5"
         step="0.01"
         placeholder="Slippage %"
         className="w-24 rounded-md border bg-background px-3 py-1.5 text-sm"
         value={params.slippage_percent ?? 0}
         onChange={(e) => setParams((p) => ({ ...p, slippage_percent: Number(e.target.value) || 0 }))}
        />

        <button
          type="submit"
          disabled={runBacktest.isPending || !params.symbol}
          className="rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground disabled:opacity-50"
        >
          {runBacktest.isPending ? "Simulating..." : "Run Backtest"}
        </button>
      </form>

      {runBacktest.isError ? (
        <StateMessage variant="error">
          Backtest execution failed. Ensure sufficient price history is available for {params.symbol}.
        </StateMessage>
      ) : result ? (
        <div className="flex flex-col gap-6">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            <div className="rounded-xl border bg-card p-3">
              <p className="text-xs text-muted-foreground">Total Return</p>
              <p
                className={`text-lg font-semibold ${
                  result.summary.total_return_pct >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                }`}
              >
                {result.summary.total_return_pct}%
              </p>
            </div>
            <div className="rounded-xl border bg-card p-3">
              <p className="text-xs text-muted-foreground">CAGR</p>
              <p className="text-lg font-semibold">{result.summary.cagr_pct}%</p>
            </div>
            <div className="rounded-xl border bg-card p-3">
              <p className="text-xs text-muted-foreground">Sharpe Ratio</p>
              <p className="text-lg font-semibold">{result.summary.sharpe_ratio}</p>
            </div>
            <div className="rounded-xl border bg-card p-3">
              <p className="text-xs text-muted-foreground">Sortino Ratio</p>
              <p className="text-lg font-semibold">{result.summary.sortino_ratio}</p>
            </div>
            <div className="rounded-xl border bg-card p-3">
              <p className="text-xs text-muted-foreground">Max Drawdown</p>
              <p className="text-lg font-semibold text-red-600 dark:text-red-400">
                {result.summary.max_drawdown_pct}%
              </p>
            </div>
            <div className="rounded-xl border bg-card p-3">
              <p className="text-xs text-muted-foreground">Annual Volatility</p>
              <p className="text-lg font-semibold">{result.summary.annualized_volatility_pct}%</p>
            </div>
            <div className="rounded-xl border bg-card p-3">
              <p className="text-xs text-muted-foreground">Trades (Win Rate)</p>
              <p className="text-lg font-semibold">
                {result.summary.total_trades} ({result.summary.win_rate_pct}%)
              </p>
            </div>
          </div>

          <dl className="grid grid-cols-1 gap-2 rounded-xl border bg-card p-4 text-xs text-muted-foreground sm:grid-cols-2 lg:grid-cols-4">
            <div><dt>Dataset</dt><dd className="font-medium text-foreground">{result.metadata.dataset_id} / {result.metadata.dataset_version}</dd></div>
            <div><dt>Evaluation</dt><dd className="font-medium text-foreground">{result.metadata.effective_start_date} → {result.metadata.effective_end_date}</dd></div>
            <div><dt>Execution</dt><dd className="font-medium text-foreground">{result.metadata.execution_price}</dd></div>
            <div><dt>Costs</dt><dd className="font-medium text-foreground">Fee {result.metadata.fee_percent * 100}% / Slip {result.metadata.slippage_percent * 100}%</dd></div>
          </dl>

          {/* Equity Curve Data Summary Table */}
          <div className="overflow-hidden rounded-xl border bg-card shadow-sm">
            <h3 className="border-b bg-muted/20 px-4 py-3 text-sm font-semibold">
              Simulation Trajectory (Sample Points)
            </h3>
            <div className="max-h-80 overflow-y-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/40 text-left text-muted-foreground">
                    <th className="px-4 py-2 font-medium">Date</th>
                    <th className="px-4 py-2 font-medium">Portfolio Equity</th>
                    <th className="px-4 py-2 font-medium">Benchmark Equity</th>
                    <th className="px-4 py-2 font-medium">Drawdown</th>
                  </tr>
                </thead>
                <tbody>
                  {result.equity_curve
                    .filter((_, idx) => idx % Math.max(1, Math.floor(result.equity_curve.length / 20)) === 0)
                    .map((pt) => (
                      <tr key={pt.time} className="border-b last:border-0 hover:bg-muted/20">
                        <td className="px-4 py-2 text-muted-foreground">{pt.time}</td>
                        <td className="px-4 py-2 font-semibold text-primary">
                          IDR {pt.equity.toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-muted-foreground">
                          IDR {pt.benchmark.toLocaleString()}
                        </td>
                        <td
                          className={`px-4 py-2 font-medium ${
                            pt.drawdown < 0 ? "text-red-600 dark:text-red-400" : "text-muted-foreground"
                          }`}
                        >
                          {pt.drawdown}%
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
