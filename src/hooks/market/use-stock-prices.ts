"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { QUERY_KEYS } from "@/lib/api/query-keys";
import type { PricesResponse } from "@/types";

export type PriceRange = {
  start?: string;
  end?: string;
};

export const useStockPrices = (symbol: string, range: PriceRange = {}) => {
  return useQuery({
    queryKey: [
      ...QUERY_KEYS.MARKET.PRICES(symbol),
      range.start ?? "start:all",
      range.end ?? "end:all",
    ],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (range.start) {
        params.start_date = range.start;
      }
      if (range.end) {
        params.end_date = range.end;
      }
      // apiClient's response interceptor unwraps the envelope to the payload.
      const response = await apiClient.get<PricesResponse>(API_ENDPOINTS.MARKET.PRICES(symbol), {
        params,
      });
      return response as unknown as PricesResponse;
    },
    enabled: Boolean(symbol),
  });
};