import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { QUERY_KEYS } from "@/lib/api/query-keys";
import type {
  CreatePortfolioInput,
  CreateTransactionInput,
  UpdatePortfolioInput,
  PortfolioDetail,
  PortfolioSummary,
} from "@/types";

export const usePortfolios = () => {
  return useQuery({
    queryKey: QUERY_KEYS.PORTFOLIO.LIST,
    queryFn: async () => {
      const response = await apiClient.get<PortfolioSummary[]>(API_ENDPOINTS.PORTFOLIO.LIST);
      return response as unknown as PortfolioSummary[];
    },
  });
};

export const usePortfolioDetail = (id: number | string) => {
  return useQuery({
    queryKey: QUERY_KEYS.PORTFOLIO.DETAIL(id),
    queryFn: async () => {
      const response = await apiClient.get<PortfolioDetail>(API_ENDPOINTS.PORTFOLIO.DETAIL(id));
      return response as unknown as PortfolioDetail;
    },
    enabled: Boolean(id),
  });
};

export const useCreatePortfolio = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreatePortfolioInput) => {
      const response = await apiClient.post<PortfolioSummary>(
        API_ENDPOINTS.PORTFOLIO.CREATE,
        input
      );
      return response as unknown as PortfolioSummary;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.PORTFOLIO.LIST });
    },
  });
};

export const useUpdatePortfolio = (portfolioId: number | string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: UpdatePortfolioInput) => {
      const response = await apiClient.patch<PortfolioSummary>(
        API_ENDPOINTS.PORTFOLIO.UPDATE(portfolioId),
        input
      );
      return response as unknown as PortfolioSummary;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.PORTFOLIO.LIST });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.PORTFOLIO.DETAIL(portfolioId) });
    },
  });
};

export const useAddTransaction = (portfolioId: number | string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: CreateTransactionInput) => {
      const response = await apiClient.post(
        API_ENDPOINTS.PORTFOLIO.ADD_TRANSACTION(portfolioId),
        input
      );
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.PORTFOLIO.DETAIL(portfolioId) });
    },
  });
};

export const useDeletePortfolio = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (portfolioId: number | string) => {
      await apiClient.delete(API_ENDPOINTS.PORTFOLIO.DELETE(portfolioId));
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.PORTFOLIO.LIST });
    },
  });
};

export const useDeleteTransaction = (portfolioId: number | string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (transactionId: number | string) => {
      await apiClient.delete(
        API_ENDPOINTS.PORTFOLIO.DELETE_TRANSACTION(portfolioId, transactionId)
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.PORTFOLIO.DETAIL(portfolioId) });
    },
  });
};
