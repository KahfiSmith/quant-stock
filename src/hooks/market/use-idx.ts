import { useMutation, useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import type {
  IDXFactorRotationParams,
  IDXFactorRotationResponse,
  IDXStockDetailResponse,
  Stock,
} from "@/types";

export interface IDXUniverseResponse {
  items: Stock[];
  total: number;
  as_of: string;
}

export const useIDXUniverse = (params?: {
  sector?: string;
  min_market_cap?: number;
  liquidity?: string;
  board?: string;
}) => {
  return useQuery<IDXUniverseResponse>({
    queryKey: ["idx-universe", params],
    queryFn: async () => {
      const response = await apiClient.get<IDXUniverseResponse>(API_ENDPOINTS.IDX.UNIVERSE, {
        params,
      });
      return response as unknown as IDXUniverseResponse;
    },
  });
};

export const useIDXStockDetail = (symbol: string) => {
  return useQuery<IDXStockDetailResponse>({
    queryKey: ["idx-stock-detail", symbol],
    queryFn: async () => {
      const response = await apiClient.get<IDXStockDetailResponse>(
        API_ENDPOINTS.IDX.STOCK_DETAIL(symbol)
      );
      return response as unknown as IDXStockDetailResponse;
    },
    enabled: Boolean(symbol),
  });
};

export const useIDXFactorRotation = () => {
  return useMutation<IDXFactorRotationResponse, Error, IDXFactorRotationParams>({
    mutationFn: async (params: IDXFactorRotationParams) => {
      const response = await apiClient.post<IDXFactorRotationResponse>(
        API_ENDPOINTS.IDX.FACTOR_ROTATION,
        params
      );
      return response as unknown as IDXFactorRotationResponse;
    },
  });
};
