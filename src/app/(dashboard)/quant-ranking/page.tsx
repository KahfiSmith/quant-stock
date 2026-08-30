"use client";

import { SlidersHorizontal, TrendingUp } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { StateMessage } from "@/components/common";
import { VolumeAnomalyBadge, VolatilityRegimeBadge } from "@/components/features/market/quant-badges";
import { Button } from "@/components/ui/button";
import { useStockScreener } from "@/hooks/market";
import type { CustomFactorWeights, ScreenerFilterParams, ScreenerItem } from "@/types";

const IDX_IC_SECTORS = [
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

const PRESET_OPTIONS = [
  { id: "none", label: "Standard IDX Quant (Balanced)", weights: { momentum: 0.30, quality: 0.25, value: 0.20, risk: 0.15, growth: 0.10 } },
  { id: "quality_momentum", label: "IDX Bluechip Momentum", weights: { momentum: 0.40, quality: 0.40, value: 0.10, risk: 0.05, growth: 0.05 } },
  { id: "deep_value", label: "IDX Deep Value", weights: { value: 0.50, quality: 0.25, momentum: 0.10, risk: 0.10, growth: 0.05 } },
  { id: "garp", label: "IDX GARP Rotation", weights: { growth: 0.35, quality: 0.25, value: 0.25, momentum: 0.10, risk: 0.05 } },
  { id: "defensive_income", label: "IDX High Dividend & Defensive", weights: { momentum: 0.05, quality: 0.35, value: 0.20, risk: 0.35, growth: 0.05 } },
  { id: "volume_momentum", label: "IDX Volume Momentum", weights: { momentum: 0.45, quality: 0.20, value: 0.15, risk: 0.10, growth: 0.10 } },
];

export default function QuantRankingPage() {
  const [preset, setPreset] = useState<string>("none");
  const [weights, setWeights] = useState<CustomFactorWeights>({
    momentum: 0.30,
    quality: 0.25,
    value: 0.20,
    risk: 0.15,
    growth: 0.10,
  });
  const [sectorFilter, setSectorFilter] = useState<string>("");
  const [sortBy] = useState<ScreenerFilterParams["sort_by"]>("score");
  const [sortOrder] = useState<"asc" | "desc">("desc");

  const filterParams: ScreenerFilterParams = useMemo(() => ({
    exchange: "IDX",
    sector: sectorFilter || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
    custom_weights: weights,
    strategy_preset: preset as ScreenerFilterParams["strategy_preset"],
    page: 1,
    page_size: 50,
  }), [sectorFilter, sortBy, sortOrder, weights, preset]);

  const { data, isPending, isError, refetch } = useStockScreener(filterParams);
  const rankingItems = useMemo(
    () => (data?.items ?? []).filter((item) => item.currency === "IDR"),
    [data?.items]
  );

  const handlePresetChange = (presetId: string) => {
    setPreset(presetId);
    const target = PRESET_OPTIONS.find((p) => p.id === presetId);
    if (target) {
      setWeights(target.weights);
    }
  };

  const handleWeightChange = (factor: keyof CustomFactorWeights, value: number) => {
    setPreset("custom");
    setWeights((prev) => ({ ...prev, [factor]: value }));
  };

  const getSignalBadge = (signal?: string) => {
    switch (signal) {
      case "STRONG_BUY":
        return <span className="inline-flex items-center rounded-md bg-emerald-500/10 px-2 py-0.5 text-xs font-bold text-emerald-600 dark:text-emerald-400">STRONG BUY</span>;
      case "BUY":
        return <span className="inline-flex items-center rounded-md bg-green-500/10 px-2 py-0.5 text-xs font-semibold text-green-600 dark:text-green-400">BUY</span>;
      case "SELL":
        return <span className="inline-flex items-center rounded-md bg-rose-500/10 px-2 py-0.5 text-xs font-semibold text-rose-600 dark:text-rose-400">SELL</span>;
      case "STRONG_SELL":
        return <span className="inline-flex items-center rounded-md bg-red-500/10 px-2 py-0.5 text-xs font-bold text-red-600 dark:text-red-400">STRONG SELL</span>;
      default:
        return <span className="inline-flex items-center rounded-md bg-amber-500/10 px-2 py-0.5 text-xs font-semibold text-amber-600 dark:text-amber-400">HOLD</span>;
    }
  };

  const getRiskBadge = (risk?: string) => {
    switch (risk) {
      case "LOW":
        return <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">Low Risk</span>;
      case "HIGH":
        return <span className="text-xs text-red-600 dark:text-red-400 font-medium">High Risk</span>;
      default:
        return <span className="text-xs text-muted-foreground font-medium">Moderate</span>;
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 p-6">
      {}
      <div className="flex flex-col gap-2 rounded-2xl border bg-gradient-to-r from-primary/10 via-background to-background p-6">
        <div className="flex items-center gap-2 text-primary">
          <span className="text-xs font-bold uppercase tracking-wider">BEI / IDX Quantitative Decision Engine</span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">IDX Cross-Sectional Quant Leaderboard</h1>
        <p className="text-sm text-muted-foreground max-w-3xl">
          Multi-factor composite scoring & ranking across Indonesian listed stocks (IDX). Powered by Point-in-Time financial statements, liquidity filters, and factor models: Value, Quality (Piotroski), Momentum (12M), Growth, and Risk Penalty.
        </p>
      </div>

      {}
      <div className="rounded-xl border bg-card p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b pb-4">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold">Factor Strategy & Weighting Model</h2>
          </div>

          <div className="flex flex-wrap gap-2">
            {PRESET_OPTIONS.map((opt) => (
              <Button
                key={opt.id}
                size="sm"
                variant={preset === opt.id ? "default" : "outline"}
                className="text-xs"
                onClick={() => handlePresetChange(opt.id)}
              >
                {opt.label}
              </Button>
            ))}
          </div>
        </div>

        {}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5 text-xs">
          <div>
            <div className="flex justify-between font-medium mb-1">
              <span>Quality ({Math.round(weights.quality * 100)}%)</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={weights.quality}
              onChange={(e) => handleWeightChange("quality", parseFloat(e.target.value))}
              className="w-full accent-primary"
            />
          </div>
          <div>
            <div className="flex justify-between font-medium mb-1">
              <span>Momentum ({Math.round(weights.momentum * 100)}%)</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={weights.momentum}
              onChange={(e) => handleWeightChange("momentum", parseFloat(e.target.value))}
              className="w-full accent-primary"
            />
          </div>
          <div>
            <div className="flex justify-between font-medium mb-1">
              <span>Value ({Math.round(weights.value * 100)}%)</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={weights.value}
              onChange={(e) => handleWeightChange("value", parseFloat(e.target.value))}
              className="w-full accent-primary"
            />
          </div>
          <div>
            <div className="flex justify-between font-medium mb-1">
              <span>Risk Penalty ({Math.round(weights.risk * 100)}%)</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={weights.risk}
              onChange={(e) => handleWeightChange("risk", parseFloat(e.target.value))}
              className="w-full accent-primary"
            />
          </div>
          <div>
            <div className="flex justify-between font-medium mb-1">
              <span>Growth ({Math.round(weights.growth * 100)}%)</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={weights.growth}
              onChange={(e) => handleWeightChange("growth", parseFloat(e.target.value))}
              className="w-full accent-primary"
            />
          </div>
        </div>
      </div>

      {}
      <div className="rounded-xl border bg-card overflow-hidden shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 border-b bg-muted/20">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold">Universe Ranking Table</h3>
            <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary font-mono font-bold">
              {rankingItems.length} IDX Assets shown
            </span>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={sectorFilter}
              onChange={(e) => setSectorFilter(e.target.value)}
              className="h-8 rounded-md border bg-background px-2 text-xs"
            >
              {IDX_IC_SECTORS.map((sec) => (
                <option key={sec} value={sec === "All Sectors" ? "" : sec}>
                  {sec}
                </option>
              ))}
            </select>
          </div>
        </div>

        {isPending ? (
          <div className="p-8">
            <StateMessage variant="loading" />
          </div>
        ) : isError ? (
          <div className="p-8 space-y-3">
            <StateMessage variant="error">
              Failed to load quant ranking data. Please try again.
            </StateMessage>
            <Button size="sm" variant="outline" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        ) : !rankingItems.length ? (
          <div className="p-8">
            <StateMessage variant="empty">
              No assets matching the selected criteria.
            </StateMessage>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b bg-muted/40 font-semibold text-muted-foreground">
                <tr>
                  <th className="py-3 px-4">Rank</th>
                  <th className="py-3 px-4">Ticker</th>
                  <th className="py-3 px-4">Company</th>
                  <th className="py-3 px-4 text-center">Quant Score</th>
                  <th className="py-3 px-4 text-center">Decision Signal</th>
                  <th className="py-3 px-4 text-right">Value</th>
                  <th className="py-3 px-4 text-right">Quality</th>
                  <th className="py-3 px-4 text-right">Momentum</th>
                  <th className="py-3 px-4 text-center">Volume</th>
                  <th className="py-3 px-4 text-center">Volatility</th>
                  <th className="py-3 px-4 text-center">Risk Level</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {rankingItems.map((item: ScreenerItem) => (
                  <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-foreground">
                      #{item.composite_rank ?? "—"}
                    </td>
                    <td className="py-3 px-4">
                      <Link
                        href={`/stocks/${item.symbol}`}
                        className="font-bold text-primary hover:underline"
                      >
                        {item.symbol}
                      </Link>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-foreground truncate max-w-[180px]">{item.name}</div>
                      <div className="text-[10px] text-muted-foreground">{item.sector ?? "General"}</div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="font-mono text-sm font-bold text-primary">
                        {item.quant_score !== null ? item.quant_score.toFixed(1) : "—"}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex flex-col items-center gap-1">
                        {getSignalBadge(item.signal)}
                        {item.signal_confidence_pct && (
                          <span className="text-[9px] text-muted-foreground">{item.signal_confidence_pct}% conf.</span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right font-mono">{item.value_score ?? "—"}</td>
                    <td className="py-3 px-4 text-right font-mono">{item.quality_score ?? "—"}</td>
                    <td className="py-3 px-4 text-right font-mono">{item.momentum_score ?? "—"}</td>
                    <td className="py-3 px-4 text-center">
                      <VolumeAnomalyBadge zscore={item.volume_zscore} />
                    </td>
                    <td className="py-3 px-4 text-center">
                      <VolatilityRegimeBadge regime={item.volatility_regime} atrPercent={item.atr_percent} />
                    </td>
                    <td className="py-3 px-4 text-center">{getRiskBadge(item.risk_level)}</td>
                    <td className="py-3 px-4 text-right">
                      <Button asChild size="sm" variant="outline" className="h-7 text-xs">
                        <Link href={`/stocks/${item.symbol}`}>Research</Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

