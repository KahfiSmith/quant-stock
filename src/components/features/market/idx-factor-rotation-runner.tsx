"use client";

import { useState } from "react";
import { ArrowUpDown, Filter, Play, RefreshCw, ShieldCheck } from "lucide-react";

import { StateMessage } from "@/components/common";
import { useIDXFactorRotation } from "@/hooks/market";
import type { CustomFactorWeights, IDXFactorRotationParams, IDXFactorRotationResponse } from "@/types";

const IDX_SECTORS = [
  "All Sectors",
  "Financials",
  "Energy",
  "Basic Materials",
  "Industrials",
  "Consumer Non-Cyclicals",
  "Consumer Cyclicals",
  "Healthcare",
  "Technology",
  "Infrastructures",
  "Properties & Real Estate",
  "Transportation & Logistics",
];

export function IDXFactorRotationRunner() {
  const [params, setParams] = useState<IDXFactorRotationParams>({
    strategy_name: "IDX Top 10 Multi-Factor Rotation",
    initial_capital: 500_000_000,
    top_n: 10,
    rebalance_frequency: "monthly",
    min_market_cap: 1_000_000_000_000, // Rp 1T
    min_adv_turnover: 5_000_000_000, // Rp 5B
    min_frequency: 1000,
    sector_filter: null,
    factor_weights: {
      momentum: 0.30,
      quality: 0.25,
      value: 0.20,
      risk: 0.15,
      growth: 0.10,
    },
    fee_percent: 0.0015,
    slippage_percent: 0.001,
  });

  const [result, setResult] = useState<IDXFactorRotationResponse | null>(null);
  const runMutation = useIDXFactorRotation();

  const handleWeightChange = (key: keyof CustomFactorWeights, val: number) => {
    setParams((p) => ({
      ...p,
      factor_weights: {
        ...(p.factor_weights || {
          momentum: 0.3,
          quality: 0.25,
          value: 0.2,
          risk: 0.15,
          growth: 0.1,
        }),
        [key]: val,
      },
    }));
  };

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await runMutation.mutateAsync(params);
    setResult(res);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Strategy & Universe Filter Configuration Form */}
      <form onSubmit={handleRun} className="flex flex-col gap-4 rounded-xl border bg-card p-5">
        <div className="flex items-center justify-between border-b pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" />
            <h2 className="text-sm font-semibold">IDX Universe Liquidity & Factor Parameters</h2>
          </div>
          <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary">
            BEI / IDX Listed Universe (IHSG Benchmark)
          </span>
        </div>

        {/* Top Controls */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-muted-foreground">Strategy Name</label>
            <input
              type="text"
              className="rounded-md border bg-background px-3 py-1.5 text-xs font-medium"
              value={params.strategy_name}
              onChange={(e) => setParams((p) => ({ ...p, strategy_name: e.target.value }))}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-muted-foreground">Initial Capital (IDR)</label>
            <input
              type="number"
              step="10000000"
              className="rounded-md border bg-background px-3 py-1.5 text-xs font-medium"
              value={params.initial_capital}
              onChange={(e) => setParams((p) => ({ ...p, initial_capital: Number(e.target.value) || 0 }))}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-muted-foreground">Select Top N Quant Stocks</label>
            <input
              type="number"
              min="1"
              max="50"
              className="rounded-md border bg-background px-3 py-1.5 text-xs font-medium"
              value={params.top_n}
              onChange={(e) => setParams((p) => ({ ...p, top_n: parseInt(e.target.value) || 10 }))}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-muted-foreground">Rebalance Frequency</label>
            <select
              className="rounded-md border bg-background px-3 py-1.5 text-xs font-medium"
              value={params.rebalance_frequency}
              onChange={(e) =>
                setParams((p) => ({
                  ...p,
                  rebalance_frequency: e.target.value as "monthly" | "quarterly",
                }))
              }
            >
              <option value="monthly">Monthly (Awal Bulan)</option>
              <option value="quarterly">Quarterly (Kuartalan)</option>
            </select>
          </div>
        </div>

        {/* IDX Liquidity Filters */}
        <div className="rounded-lg border bg-muted/20 p-3">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-foreground">
            <Filter className="h-3.5 w-3.5" />
            IDX Pre-Ranking Liquidity Filters (Anti Manipulasi & Illiquid)
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="flex flex-col gap-1">
              <label className="text-[11px] text-muted-foreground">Min Market Cap (Rp)</label>
              <input
                type="number"
                step="100000000000"
                className="rounded-md border bg-background px-2.5 py-1 text-xs"
                value={params.min_market_cap}
                onChange={(e) => setParams((p) => ({ ...p, min_market_cap: Number(e.target.value) || 0 }))}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[11px] text-muted-foreground">Min 20D Avg Turnover (Rp/Hari)</label>
              <input
                type="number"
                step="500000000"
                className="rounded-md border bg-background px-2.5 py-1 text-xs"
                value={params.min_adv_turnover}
                onChange={(e) => setParams((p) => ({ ...p, min_adv_turnover: Number(e.target.value) || 0 }))}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[11px] text-muted-foreground">IDX-IC Sector Filter</label>
              <select
                className="rounded-md border bg-background px-2.5 py-1 text-xs"
                value={params.sector_filter || "All Sectors"}
                onChange={(e) =>
                  setParams((p) => ({
                    ...p,
                    sector_filter: e.target.value === "All Sectors" ? null : e.target.value,
                  }))
                }
              >
                {IDX_SECTORS.map((sec) => (
                  <option key={sec} value={sec}>
                    {sec}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Factor Weight Sliders */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {(["momentum", "quality", "value", "risk", "growth"] as (keyof CustomFactorWeights)[]).map((f) => (
            <div key={f} className="flex flex-col gap-1 rounded-md border bg-background p-2">
              <div className="flex justify-between text-[11px] font-medium capitalize">
                <span>{f}</span>
                <span className="font-semibold text-primary">
                  {Math.round(((params.factor_weights?.[f] || 0.2) * 100))}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                className="h-1.5 w-full cursor-pointer accent-primary"
                value={params.factor_weights?.[f] || 0.2}
                onChange={(e) => handleWeightChange(f, parseFloat(e.target.value))}
              />
            </div>
          ))}
        </div>

        {/* Action Button */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={runMutation.isPending}
            className="flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-xs font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50"
          >
            {runMutation.isPending ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                Simulating IDX Rotation...
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-current" />
                Execute IDX Factor Rotation Backtest
              </>
            )}
          </button>
        </div>
      </form>

      {runMutation.isError ? (
        <StateMessage variant="error">
          Execution failed. Please ensure market prices and IHSG benchmark are seeded.
        </StateMessage>
      ) : result ? (
        <div className="flex flex-col gap-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <div className="rounded-xl border bg-card p-4">
              <p className="text-xs text-muted-foreground">Total Return (Strategy)</p>
              <p
                className={`text-xl font-bold ${
                  result.summary.total_return_pct >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                }`}
              >
                {result.summary.total_return_pct}%
              </p>
            </div>
            <div className="rounded-xl border bg-card p-4">
              <p className="text-xs text-muted-foreground">IHSG Benchmark Return</p>
              <p className="text-xl font-bold text-foreground">
                {result.summary.benchmark_return_pct}%
              </p>
            </div>
            <div className="rounded-xl border bg-card p-4">
              <p className="text-xs text-muted-foreground">Alpha (vs IHSG)</p>
              <p
                className={`text-xl font-bold ${
                  result.summary.alpha_pct >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                }`}
              >
                {result.summary.alpha_pct > 0 ? `+${result.summary.alpha_pct}%` : `${result.summary.alpha_pct}%`}
              </p>
            </div>
            <div className="rounded-xl border bg-card p-4">
              <p className="text-xs text-muted-foreground">Sharpe Ratio</p>
              <p className="text-xl font-bold text-primary">{result.summary.sharpe_ratio}</p>
            </div>
            <div className="rounded-xl border bg-card p-4">
              <p className="text-xs text-muted-foreground">Max Drawdown</p>
              <p className="text-xl font-bold text-red-600 dark:text-red-400">
                {result.summary.max_drawdown_pct}%
              </p>
            </div>
            <div className="rounded-xl border bg-card p-4">
              <p className="text-xs text-muted-foreground">Final Equity (IDR)</p>
              <p className="text-xl font-bold text-foreground">
                Rp {result.summary.final_equity.toLocaleString()}
              </p>
            </div>
          </div>

          {/* Rebalance History Log */}
          <div className="overflow-hidden rounded-xl border bg-card">
            <div className="flex items-center justify-between border-b bg-muted/20 px-4 py-3">
              <div className="flex items-center gap-2">
                <ArrowUpDown className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-semibold">Monthly Rebalance History & Selected Quant Stocks</h3>
              </div>
              <span className="text-xs text-muted-foreground">
                {result.rebalance_history.length} Rebalance Events
              </span>
            </div>
            <div className="max-h-60 overflow-y-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b bg-muted/40 text-left text-muted-foreground">
                    <th className="px-4 py-2 font-medium">Rebalance Date</th>
                    <th className="px-4 py-2 font-medium">Top Ranked Quant Universe</th>
                    <th className="px-4 py-2 font-medium text-right">Portfolio Value</th>
                    <th className="px-4 py-2 font-medium text-right">Cash Reserve</th>
                  </tr>
                </thead>
                <tbody>
                  {result.rebalance_history.map((ev) => (
                    <tr key={ev.date} className="border-b last:border-0 hover:bg-muted/10">
                      <td className="px-4 py-2 font-medium">{ev.date}</td>
                      <td className="px-4 py-2">
                        <div className="flex flex-wrap gap-1">
                          {ev.selected_symbols.map((sym) => (
                            <span
                              key={sym}
                              className="rounded bg-primary/10 px-1.5 py-0.5 text-[11px] font-semibold text-primary"
                            >
                              {sym}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-2 text-right font-semibold text-foreground">
                        Rp {ev.portfolio_value.toLocaleString()}
                      </td>
                      <td className="px-4 py-2 text-right text-muted-foreground">
                        Rp {ev.cash_reserve.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Equity Curve Progression */}
          <div className="overflow-hidden rounded-xl border bg-card">
            <h3 className="border-b bg-muted/20 px-4 py-3 text-sm font-semibold">
              Equity Trajectory vs IHSG Composite Benchmark
            </h3>
            <div className="max-h-80 overflow-y-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b bg-muted/40 text-left text-muted-foreground">
                    <th className="px-4 py-2 font-medium">Date</th>
                    <th className="px-4 py-2 font-medium text-right">Factor Portfolio (IDR)</th>
                    <th className="px-4 py-2 font-medium text-right">IHSG Benchmark (IDR)</th>
                    <th className="px-4 py-2 font-medium text-right">Drawdown</th>
                  </tr>
                </thead>
                <tbody>
                  {result.equity_curve
                    .filter((_, idx) => idx % Math.max(1, Math.floor(result.equity_curve.length / 25)) === 0)
                    .map((pt) => (
                      <tr key={pt.date} className="border-b last:border-0 hover:bg-muted/10">
                        <td className="px-4 py-2 text-muted-foreground">{pt.date}</td>
                        <td className="px-4 py-2 text-right font-semibold text-primary">
                          Rp {pt.equity.toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-right text-muted-foreground">
                          Rp {pt.benchmark.toLocaleString()}
                        </td>
                        <td
                          className={`px-4 py-2 text-right font-medium ${
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
