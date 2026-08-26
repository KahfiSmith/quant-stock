"use client";

import Link from "next/link";

import { StateMessage } from "@/components/common";
import { useStocks } from "@/hooks/market";

export function StockList() {
  const { data, isPending, isError } = useStocks();

  if (isPending) {
    return <StateMessage variant="loading" />;
  }

  if (isError) {
    return (
      <StateMessage variant="error">
        Failed to load the stock universe. Please try again.
      </StateMessage>
    );
  }

  const stocks = data?.items ?? [];

  if (stocks.length === 0) {
    return <StateMessage variant="empty">No stocks available yet.</StateMessage>;
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