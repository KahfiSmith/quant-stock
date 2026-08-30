"use client";

import Link from "next/link";
import { ArrowRight, BarChart3, Binary, Sparkles, TrendingUp } from "lucide-react";

import { ROUTES } from "@/config/routes";
import { Footer, Header } from "@/components/common";
import { Button } from "@/components/ui";

export default function HomePage() {

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />

      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-12 px-6 py-16">
        {}
        <section className="space-y-6 text-center sm:text-left">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-semibold text-primary">
            <Sparkles className="h-3.5 w-3.5" />
            IDX Quant Research & Factor Rotation Platform
          </div>

          <h1 className="max-w-3xl text-4xl sm:text-5xl font-extrabold tracking-tight">
            Indonesia Stock Exchange (IDX) Quant Research & Factor Rotation
          </h1>

          <p className="max-w-2xl text-base sm:text-lg text-muted-foreground leading-relaxed">
            Eliminate emotional bias on Bursa Efek Indonesia with Point-in-Time financial statements, IDX-IC sector classifications, pre-ranking liquidity filters, and monthly factor rotation backtested against IHSG.
          </p>

          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-4 pt-2">
            <Button asChild size="lg">
              <Link href={ROUTES.QUANT_RANKING} className="flex items-center gap-2 font-semibold">
                Explore IDX Quant Leaderboard
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href={ROUTES.BACKTEST}>Run IDX Factor Rotation</Link>
            </Button>
          </div>
        </section>

        {}
        <section className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          <div className="rounded-xl border bg-card p-5 shadow-sm space-y-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Binary className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-foreground">Multi-Factor Scoring</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Objective 0–100 asset ranking based on normalized Piotroski Quality, 12-Month Momentum, P/E Valuations, and Volatility Risk.
            </p>
          </div>

          <div className="rounded-xl border bg-card p-5 shadow-sm space-y-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <TrendingUp className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-foreground">Quantitative Signals</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Transparent Buy/Hold/Sell decision matrices with empirical reason codes, confidence scoring, and risk levels.
            </p>
          </div>

          <div className="rounded-xl border bg-card p-5 shadow-sm space-y-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
              <BarChart3 className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-foreground">Strategy Backtesting</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Historical equity curve simulations with anti-lookahead protections, slippage, CAGR, Sharpe, and Sortino ratios.
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
