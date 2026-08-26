import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { QUERY_KEYS } from "@/lib/api/query-keys";
import type { QuantScoreResponse } from "@/types";

export const useStockScore = (symbol: string) => {
  return useQuery({
    queryKey: QUERY_KEYS.MARKET.SCORE(symbol),
    queryFn: async () => {
      const response = await apiClient.get<QuantScoreResponse>(
        API_ENDPOINTS.MARKET.SCORE(symbol)
      );
      return response as unknown as QuantScoreResponse;
    },
    enabled: Boolean(symbol),
  });
};
