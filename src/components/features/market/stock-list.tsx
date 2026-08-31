"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { StateMessage } from "@/components/common";
import { useIDXUniverse } from "@/hooks/market";
import type { Stock } from "@/types";

type SortBy = "score" | "symbol" | "market_cap" | "pe_ratio" | "pb_ratio" | "roe";
type SortOrder = "asc" | "desc";

const PAGE_SIZE = 20;

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

const formatIdr = (value: number | null) =>
  value === null
    ? "—"
    : new Intl.NumberFormat("id-ID", {
        style: "currency",
        currency: "IDR",
        maximumFractionDigits: 0,
      }).format(value);

export function StockList() {
  const [search, setSearch] = useState("");
  const [sector, setSector] = useState("");
  const [sortBy, setSortBy] = useState<SortBy>("score");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [page, setPage] = useState(1);
  const { data, isPending, isError } = useIDXUniverse(
    sector ? { sector } : undefined
  );

  const stocks = useMemo(() => {
    const query = search.trim().toLowerCase();
    const filteredStocks = (data?.items ?? []).filter(
      (stock) =>
        !query ||
        stock.symbol.toLowerCase().includes(query) ||
        stock.name.toLowerCase().includes(query)
    );

    return [...filteredStocks].sort((left, right) => {
      if (sortBy === "symbol") {
        return sortOrder === "asc"
          ? left.symbol.localeCompare(right.symbol)
          : right.symbol.localeCompare(left.symbol);
      }

      const getSortValue = (stock: Stock) => {
        switch (sortBy) {
          case "score":
            return stock.quant_score ?? Number.NEGATIVE_INFINITY;
          case "market_cap":
            return stock.market_cap ?? Number.NEGATIVE_INFINITY;
          case "pe_ratio":
            return stock.pe_ratio ?? Number.NEGATIVE_INFINITY;
          case "pb_ratio":
            return stock.pb_ratio ?? Number.NEGATIVE_INFINITY;
          case "roe":
            return stock.roe ?? Number.NEGATIVE_INFINITY;
        }
      };
      const leftValue = getSortValue(left);
      const rightValue = getSortValue(right);
      return sortOrder === "asc" ? leftValue - rightValue : rightValue - leftValue;
    });
  }, [data?.items, search, sortBy, sortOrder]);

  const totalPages = Math.max(1, Math.ceil(stocks.length / PAGE_SIZE));
  const pagedStocks = stocks.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setPage(1);
  };

  const handleSectorChange = (value: string) => {
    setSector(value);
    setPage(1);
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-card p-4 text-sm">
        <span className="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary">
          BEI / IDX — Indonesia
        </span>
        <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-mono">
          {stocks.length} stocks
        </span>
        <input
          type="text"
          placeholder="Cari kode atau nama saham..."
          className="rounded-md border bg-background px-3 py-1.5 text-sm"
          value={search}
          onChange={(event) => handleSearchChange(event.target.value)}
        />

        <select
          className="rounded-md border bg-background px-3 py-1.5 text-sm"
          value={sector}
          onChange={(event) => handleSectorChange(event.target.value)}
        >
          {IDX_IC_SECTORS.map((sec) => (
            <option key={sec} value={sec === "All Sectors" ? "" : sec}>
              {sec}
            </option>
          ))}
        </select>

        <select
          className="rounded-md border bg-background px-3 py-1.5 text-sm"
          value={sortBy}
          onChange={(event) => { setSortBy(event.target.value as SortBy); setPage(1); }}
        >
          <option value="score">Urutkan: Quant Score</option>
          <option value="symbol">Urutkan: Kode Saham</option>
          <option value="market_cap">Urutkan: Market Cap</option>
          <option value="pe_ratio">Urutkan: P/E</option>
          <option value="pb_ratio">Urutkan: P/B</option>
          <option value="roe">Urutkan: ROE</option>
        </select>

        <select
          className="rounded-md border bg-background px-3 py-1.5 text-sm"
          value={sortOrder}
          onChange={(event) => { setSortOrder(event.target.value as SortOrder); setPage(1); }}
        >
          <option value="desc">Tertinggi ke Terendah</option>
          <option value="asc">Terendah ke Tertinggi</option>
        </select>
      </div>

      {isPending ? (
        <StateMessage variant="loading" />
      ) : isError ? (
        <StateMessage variant="error">
          Gagal memuat universe saham BEI. Silakan coba lagi.
        </StateMessage>
      ) : stocks.length === 0 ? (
        <StateMessage variant="empty">Tidak ada saham BEI yang sesuai dengan pencarian Anda.</StateMessage>
      ) : (
        <>
          <div className="overflow-x-auto rounded-xl border bg-card shadow-sm">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40 text-left text-muted-foreground">
                  <th className="px-4 py-3 font-medium">Kode</th>
                  <th className="px-4 py-3 font-medium">Nama</th>
                  <th className="px-4 py-3 font-medium">Sektor IDX-IC</th>
                  <th className="px-4 py-3 font-medium">Quant Score</th>
                  <th className="px-4 py-3 font-medium">Market Cap</th>
                  <th className="px-4 py-3 font-medium">P/E</th>
                  <th className="px-4 py-3 font-medium">P/B</th>
                  <th className="px-4 py-3 font-medium">ROE</th>
                </tr>
              </thead>
              <tbody>
                {pagedStocks.map((stock: Stock) => (
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
                    <td className="px-4 py-3 text-muted-foreground">{stock.sector ?? "—"}</td>
                    <td className="px-4 py-3 font-semibold text-primary">
                      {stock.quant_score ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{formatIdr(stock.market_cap)}</td>
                    <td className="px-4 py-3 text-muted-foreground">{stock.pe_ratio ?? "—"}</td>
                    <td className="px-4 py-3 text-muted-foreground">{stock.pb_ratio ?? "—"}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {stock.roe !== null && stock.roe !== undefined
                        ? `${(stock.roe * 100).toFixed(1)}%`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Page {page} of {totalPages}</span>
              <div className="flex gap-1">
                <button
                  onClick={() => setPage(1)}
                  disabled={page <= 1}
                  className="rounded border px-2 py-1 disabled:opacity-40"
                >
                  First
                </button>
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="rounded border px-2 py-1 disabled:opacity-40"
                >
                  Prev
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="rounded border px-2 py-1 disabled:opacity-40"
                >
                  Next
                </button>
                <button
                  onClick={() => setPage(totalPages)}
                  disabled={page >= totalPages}
                  className="rounded border px-2 py-1 disabled:opacity-40"
                >
                  Last
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
