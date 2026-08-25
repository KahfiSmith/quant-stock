"use client";

import Link from "next/link";
import { Loader2 } from "lucide-react";

import { useStocks } from "@/hooks/market";

export function StockList() {
  const { data, isPending, isError } = useStocks();

  if (isPending) {
    return (
      <div className="flex items-center justify-center p-6 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
        Failed to load the stock universe. Please try again.
      </div>
    );
  }

  const stocks = data?.items ?? [];

  if (stocks.length === 0) {
    return (
      <div className="rounded-lg border bg-muted/40 p-6 text-center text-sm text-muted-foreground">
        No stocks available yet.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border bg-card shadow-sm">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/40 text-left text-muted-foreground">
            <th className="px-4 py-3 font-medium">Symbol</th>
            <th className="px-4 py-3 font-medium">Name</th>
            <th className="px-4 py-3 font-medium">Sector</th>
            <th className="px-4 py-3 font-medium">Exchange</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock) => (
            <tr key={stock.id} className="border-b last:border-0 hover:bg-muted/20">
              <td className="px-4 py-3">
                <Link
                  href={`/stocks/${stock.symbol}`}
                  className="font-semibold text-primary hover:underline"
                >
                  {stock.symbol}
                </Link>
              </td>
              <td className="px-4 py-3">{stock.name}</td>
              <td className="px-4 py-3 text-muted-foreground">{stock.sector || "—"}</td>
              <td className="px-4 py-3 text-muted-foreground">{stock.exchange || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}