"use client";

import { useParams } from "next/navigation";

import { RequireAuth } from "@/components/features/auth";
import { StockDetail } from "@/components/features/market";

export default function StockDetailPage() {
  const { symbol } = useParams<{ symbol: string }>();

  return (
    <RequireAuth>
      <StockDetail symbol={symbol} />
    </RequireAuth>
  );
}