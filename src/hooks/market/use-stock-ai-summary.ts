import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { QUERY_KEYS } from "@/lib/api/query-keys";
import type { AiAnalystResponse } from "@/types";

export const useStockAiSummary = (symbol: string) => {
  return useQuery({
    queryKey: QUERY_KEYS.MARKET.AI_SUMMARY(symbol),
    queryFn: async () => {
      const response = await apiClient.get<AiAnalystResponse>(
        API_ENDPOINTS.MARKET.AI_SUMMARY(symbol)
      );
      return response as unknown as AiAnalystResponse;
    },
    enabled: Boolean(symbol),
  });
};
