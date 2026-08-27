import type { Metadata } from "next";

import { PortfolioManager } from "@/components/features/market";

export const metadata: Metadata = {
  title: "Portfolio Tracker",
  description: "Track equity holdings, transactions, and live unrealized PnL.",
};

export default function PortfolioPage() {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-6">
      <header>
        <p className="text-sm font-medium text-primary">Investments</p>
        <h1 className="text-2xl font-semibold tracking-tight">Portfolio Tracker</h1>
      </header>

      <PortfolioManager />
    </div>
  );
}
