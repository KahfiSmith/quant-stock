"use client";

import { Activity, Flame, TrendingDown, TrendingUp } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { StateMessage } from "@/components/common";
import { Button } from "@/components/ui/button";
import { useScanner } from "@/hooks/market";
import type { ScreenerItem } from "@/types";

type ScannerMode = "swing" | "scalping" | "accumulation" | "oversold-bounce";

const SCANNER_MODES: { id: ScannerMode; label: string; description: string; icon: React.ReactNode }[] = [
  {
    id: "swing",
    label: "Swing Breakout",
    description: "Volume spike + momentum kuat. Saham yang siap rally 2-5 hari.",
    icon: <TrendingUp className="h-4 w-4" />,
  },
  {
    id: "scalping",
    label: "Scalping / Gorengan",
    description: "Volume extreme + momentum agresif. Saham gorengan yang lagi digerakkan.",
    icon: <Flame className="h-4 w-4" />,
  },
  {
    id: "accumulation",
    label: "Foreign Accumulation",
    description: "Asing diam-diam nampung. Harga belum naik tapi smart money sudah masuk.",
    icon: <Activity className="h-4 w-4" />,
  },
  {
    id: "oversold-bounce",
    label: "Oversold Bounce",
    description: "RSI/MFI oversold + volume mulai masuk. Siap mantul dari bawah.",
    icon: <TrendingDown className="h-4 w-4" />,
  },
];

const getFlowBadge = (signal?: string | null) => {
  if (!signal) return null;
  const config: Record<string, string> = {
    STRONG_ACCUMULATION: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    ACCUMULATION: "bg-green-500/10 text-green-600 dark:text-green-400",
    DISTRIBUTION: "bg-rose-500/10 text-rose-600 dark:text-rose-400",
    STRONG_DISTRIBUTION: "bg-red-500/10 text-red-600 dark:text-red-400",
    NEUTRAL: "bg-muted text-muted-foreground",
  };
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-semibold ${config[signal] ?? config.NEUTRAL}`}>
      {signal.replace(/_/g, " ")}
    </span>
  );
};

const getRecBadge = (rec?: string | null) => {
  if (!rec) return "—";
  const config: Record<string, string> = {
    STRONG_BUY_HIGH_CONVICTION: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    BUY_ACCUMULATE: "bg-green-500/10 text-green-600 dark:text-green-400",
    BUY_WATCHLIST: "bg-sky-500/10 text-sky-600 dark:text-sky-400",
    HOLD_NEUTRAL: "bg-muted text-muted-foreground",
    REDUCE_POSITION: "bg-rose-500/10 text-rose-600 dark:text-rose-400",
    SELL_EXIT: "bg-red-500/10 text-red-600 dark:text-red-400",
  };
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-bold ${config[rec] ?? "bg-muted text-muted-foreground"}`}>
      {rec.replace(/_/g, " ")}
    </span>
  );
};

export default function ScannerPage() {
  const [mode, setMode] = useState<ScannerMode>("swing");
  const [page, setPage] = useState(1);
  const { data, isPending, isError, refetch } = useScanner(mode, { page });
  const items = data?.items ?? [];
  const totalPages = data?.pagination?.total_pages ?? 1;

  const handleModeChange = (newMode: ScannerMode) => {
    setMode(newMode);
    setPage(1);
  };

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 p-6">
      <div className="flex flex-col gap-2 rounded-2xl border bg-gradient-to-r from-amber-500/10 via-background to-background p-6">
        <span className="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">
          Swing & Scalping Scanner
        </span>
        <h1 className="text-3xl font-bold tracking-tight">IDX Stock Scanner</h1>
        <p className="text-sm text-muted-foreground max-w-3xl">
          Real-time scanner for swing trading and scalping opportunities. Filters stocks by volume spikes,
          momentum breakouts, foreign accumulation, and oversold bounce setups.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {SCANNER_MODES.map((m) => (
          <button
            key={m.id}
            type="button"
            onClick={() => handleModeChange(m.id)}
            className={`flex flex-col gap-2 rounded-xl border p-4 text-left transition-colors ${
              mode === m.id
                ? "border-primary bg-primary/5"
                : "bg-card hover:bg-muted/50"
            }`}
          >
            <div className="flex items-center gap-2">
              <span className={mode === m.id ? "text-primary" : "text-muted-foreground"}>
                {m.icon}
              </span>
              <span className={`text-sm font-semibold ${mode === m.id ? "text-primary" : ""}`}>
                {m.label}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">{m.description}</p>
          </button>
        ))}
      </div>

      <div className="rounded-xl border bg-card overflow-hidden shadow-sm">
        <div className="flex items-center justify-between border-b bg-muted/20 px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold">
              {SCANNER_MODES.find((m) => m.id === mode)?.label} Results
            </span>
            <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-mono font-bold text-primary">
              {items.length} found
            </span>
          </div>
        </div>

        {isPending ? (
          <div className="p-8"><StateMessage variant="loading" /></div>
        ) : isError ? (
          <div className="p-8 space-y-3">
            <StateMessage variant="error">Scanner failed. Please retry.</StateMessage>
            <Button size="sm" variant="outline" onClick={() => refetch()}>Retry</Button>
          </div>
        ) : items.length === 0 ? (
          <div className="p-8">
            <StateMessage variant="empty">No stocks match this scanner&apos;s criteria right now.</StateMessage>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b bg-muted/40 font-semibold text-muted-foreground">
                  <tr>
                    <th className="py-3 px-4">Ticker</th>
                    <th className="py-3 px-4">Company</th>
                    <th className="py-3 px-4 text-center">Conviction</th>
                    <th className="py-3 px-4 text-center">Recommendation</th>
                    <th className="py-3 px-4 text-center">Vol Z-Score</th>
                    <th className="py-3 px-4 text-center">Flow Signal</th>
                    <th className="py-3 px-4 text-right">1M Mom</th>
                    <th className="py-3 px-4 text-right">RSI</th>
                    <th className="py-3 px-4 text-right">Support</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {items.map((item: ScreenerItem) => (
                    <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-4">
                        <Link href={`/stocks/${item.symbol}`} className="font-bold text-primary hover:underline">
                          {item.symbol}
                        </Link>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-medium text-foreground truncate max-w-[160px]">{item.name}</div>
                        <div className="text-[10px] text-muted-foreground">{item.sector ?? "General"}</div>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`font-mono text-sm font-bold ${
                          (item.conviction_score ?? 0) >= 70 ? "text-emerald-600 dark:text-emerald-400"
                            : (item.conviction_score ?? 0) >= 50 ? "text-primary"
                            : "text-rose-600 dark:text-rose-400"
                        }`}>
                          {item.conviction_score?.toFixed(0) ?? "—"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">{getRecBadge(item.recommendation)}</td>
                      <td className="py-3 px-4 text-center">
                        <span className={`font-mono font-bold ${
                          (item.volume_zscore ?? 0) >= 3 ? "text-amber-600 dark:text-amber-400"
                            : (item.volume_zscore ?? 0) >= 1.5 ? "text-emerald-600 dark:text-emerald-400"
                            : ""
                        }`}>
                          {item.volume_zscore != null ? `${item.volume_zscore.toFixed(1)}σ` : "—"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">{getFlowBadge(item.flow_signal)}</td>
                      <td className={`py-3 px-4 text-right font-mono ${
                        (item.momentum_1m ?? 0) >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
                      }`}>
                        {item.momentum_1m != null ? `${item.momentum_1m >= 0 ? "+" : ""}${item.momentum_1m.toFixed(1)}%` : "—"}
                      </td>
                      <td className={`py-3 px-4 text-right font-mono ${
                        (item.rsi ?? 50) < 30 ? "text-emerald-600 dark:text-emerald-400"
                          : (item.rsi ?? 50) > 70 ? "text-rose-600 dark:text-rose-400"
                          : ""
                      }`}>
                        {item.rsi?.toFixed(0) ?? "—"}
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-muted-foreground">
                        {item.close_price?.toLocaleString() ?? "—"}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Button asChild size="sm" variant="outline" className="h-7 text-xs">
                          <Link href={`/stocks/${item.symbol}`}>Analyze</Link>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-between border-t px-4 py-3 text-xs">
                <span className="text-muted-foreground">Page {page} of {totalPages}</span>
                <div className="flex gap-1">
                  <Button size="sm" variant="outline" className="h-7 text-xs" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Prev</Button>
                  <Button size="sm" variant="outline" className="h-7 text-xs" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
