import { useMutation } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import type { BacktestParams, BacktestResponse } from "@/types";

export const useRunBacktest = () => {
  return useMutation({
    mutationFn: async (params: BacktestParams) => {
      const response = await apiClient.post<BacktestResponse>(
        API_ENDPOINTS.BACKTEST.RUN,
        params
      );
      return response as unknown as BacktestResponse;
    },
  });
};
