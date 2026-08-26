import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { QUERY_KEYS } from "@/lib/api/query-keys";
import type { TechnicalAnalysisResponse } from "@/types";

export const useStockTechnical = (symbol: string, interval = "1d") => {
  return useQuery({
    queryKey: [...QUERY_KEYS.MARKET.TECHNICAL(symbol), interval],
    queryFn: async () => {
      const response = await apiClient.get<TechnicalAnalysisResponse>(
        API_ENDPOINTS.MARKET.TECHNICAL(symbol),
        { params: { interval } }
      );
      return response as unknown as TechnicalAnalysisResponse;
    },
    enabled: Boolean(symbol),
  });
};
