import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { QUERY_KEYS } from "@/lib/api/query-keys";
import type { ScreenerFilterParams, ScreenerResponse } from "@/types";

export const useStockScreener = (filters: ScreenerFilterParams = {}) => {
  return useQuery({
    queryKey: QUERY_KEYS.MARKET.SCREENER(filters as Record<string, unknown>),
    queryFn: async () => {
      const response = await apiClient.post<ScreenerResponse>(
        API_ENDPOINTS.MARKET.SCREENER,
        filters
      );
      return response as unknown as ScreenerResponse;
    },
  });
};
