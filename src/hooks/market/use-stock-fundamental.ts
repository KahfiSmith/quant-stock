import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { QUERY_KEYS } from "@/lib/api/query-keys";
import type { FundamentalResponse } from "@/types";

export const useStockFundamental = (symbol: string) => {
  return useQuery({
    queryKey: QUERY_KEYS.MARKET.FUNDAMENTAL(symbol),
    queryFn: async () => {
      const response = await apiClient.get<FundamentalResponse>(
        API_ENDPOINTS.MARKET.FUNDAMENTAL(symbol)
      );
      return response as unknown as FundamentalResponse;
    },
    enabled: Boolean(symbol),
  });
};
