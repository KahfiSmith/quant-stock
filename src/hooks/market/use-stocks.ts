"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { QUERY_KEYS } from "@/lib/api/query-keys";
import type { StocksPage } from "@/types";

export const useStocks = () => {
  return useQuery({
    queryKey: QUERY_KEYS.MARKET.STOCKS,
    queryFn: async () => {
      // apiClient's response interceptor unwraps the envelope to the payload.
      const response = await apiClient.get<StocksPage>(API_ENDPOINTS.MARKET.STOCKS);
      return response as unknown as StocksPage;
    },
  });
};