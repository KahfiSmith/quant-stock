"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { QUERY_KEYS } from "@/lib/api/query-keys";
import type { PricesResponse } from "@/types";

export const useStockPrices = (symbol: string) => {
  return useQuery({
    queryKey: QUERY_KEYS.MARKET.PRICES(symbol),
    queryFn: async () => {
      // apiClient's response interceptor unwraps the envelope to the payload.
      const response = await apiClient.get<PricesResponse>(API_ENDPOINTS.MARKET.PRICES(symbol));
      return response as unknown as PricesResponse;
    },
    enabled: Boolean(symbol),
  });
};