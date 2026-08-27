"use client";

import Link from "next/link";
import { useState } from "react";

import { StateMessage } from "@/components/common";
import { useStockScreener } from "@/hooks/market";
import type { ScreenerFilterParams } from "@/types";

export function StockList() {
  const [filters, setFilters] = useState<ScreenerFilterParams>({
    sort_by: "score",
    sort_order: "desc",
    page: 1,
    page_size: 20,
  });

  const { data, isPending, isError } = useStockScreener(filters);

  return (
    <div className="flex flex-col gap-4">
      {/* Screener filter toolbar */}
      <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-card p-4 text-sm">
        <input
          type="text"
          placeholder="Search ticker or name..."
          className="rounded-md border bg-background px-3 py-1.5 text-sm"
          value={filters.search ?? ""}
          onChange={(e) =>
            setFilters((prev) => ({ ...prev, search: e.target.value || undefined, page: 1 }))
          }
        />

        <select
          className="rounded-md border bg-background px-3 py-1.5 text-sm"
          value={filters.sort_by ?? "score"}
          onChange={(e) =>
            setFilters((prev) => ({
              ...prev,
              sort_by: e.target.value as ScreenerFilterParams["sort_by"],
              page: 1,
            }))
          }
        >
          <option value="score">Sort by: Quant Score</option>
          <option value="symbol">Sort by: Symbol</option>
          <option value="pe_ratio">Sort by: P/E</option>
          <option value="pb_ratio">Sort by: P/B</option>
          <option value="roe">Sort by: ROE</option>
          <option value="rsi">Sort by: RSI</option>
        </select>

        <select
          className="rounded-md border bg-background px-3 py-1.5 text-sm"
          value={filters.sort_order ?? "desc"}
          onChange={(e) =>
            setFilters((prev) => ({
              ...prev,
              sort_order: e.target.value as ScreenerFilterParams["sort_order"],
              page: 1,
            }))
          }
        >
          <option value="desc">Order: High to Low (Desc)</option>
          <option value="asc">Order: Low to High (Asc)</option>
        </select>
      </div>

      {isPending ? (
        <StateMessage variant="loading" />
      ) : isError ? (
        <StateMessage variant="error">
          Failed to load the stock universe. Please try again.
        </StateMessage>
      ) : (data?.items ?? []).length === 0 ? (
        <StateMessage variant="empty">No stocks match your filter criteria.</StateMessage>
      ) : (
        <div className="overflow-hidden rounded-xl border bg-card shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40 text-left text-muted-foreground">
                <th className="px-4 py-3 font-medium">Symbol</th>
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Quant Score</th>
                <th className="px-4 py-3 font-medium">P/E</th>
                <th className="px-4 py-3 font-medium">P/B</th>
                <th className="px-4 py-3 font-medium">ROE</th>
                <th className="px-4 py-3 font-medium">RSI(14)</th>
                <th className="px-4 py-3 font-medium">Trend</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((stock) => (
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
                  <td className="px-4 py-3 font-semibold text-primary">
                    {stock.quant_score !== null ? stock.quant_score : "—"}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {stock.pe_ratio !== null ? stock.pe_ratio : "—"}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {stock.pb_ratio !== null ? stock.pb_ratio : "—"}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {stock.roe !== null ? `${(stock.roe * 100).toFixed(1)}%` : "—"}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {stock.rsi !== null ? stock.rsi : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        stock.trend === "bullish"
                          ? "bg-green-500/10 text-green-600 dark:text-green-400"
                          : stock.trend === "bearish"
                            ? "bg-red-500/10 text-red-600 dark:text-red-400"
                            : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {stock.trend}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}