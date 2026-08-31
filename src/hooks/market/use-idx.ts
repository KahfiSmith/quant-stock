import { useMutation, useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import type {
  BrokerSummaryResponse,
  ForeignFlowAnalysis,
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

export const useFlowAnalysis = (symbol: string) => {
  return useQuery<ForeignFlowAnalysis>({
    queryKey: ["flow-analysis", symbol],
    queryFn: async () => {
      const response = await apiClient.get<ForeignFlowAnalysis>(
        API_ENDPOINTS.IDX.FLOW_ANALYSIS(symbol)
      );
      return response as unknown as ForeignFlowAnalysis;
    },
    enabled: Boolean(symbol),
  });
};

export const useIDXBrokerSummary = (date: string | null) => {
  return useQuery<BrokerSummaryResponse>({
    queryKey: ["idx-broker-summary", date],
    queryFn: async () => {
      const response = await apiClient.get<BrokerSummaryResponse>(
        API_ENDPOINTS.IDX.BROKER_SUMMARY,
        { params: { date, limit: 50 } }
      );
      return response as unknown as BrokerSummaryResponse;
    },
    enabled: Boolean(date),
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
