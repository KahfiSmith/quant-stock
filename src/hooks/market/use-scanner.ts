import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import type { ScreenerResponse } from "@/types";

type ScannerType = "swing" | "scalping" | "accumulation" | "oversold-bounce";

const ENDPOINT_MAP: Record<ScannerType, string> = {
  swing: API_ENDPOINTS.SCANNER.SWING,
  scalping: API_ENDPOINTS.SCANNER.SCALPING,
  accumulation: API_ENDPOINTS.SCANNER.ACCUMULATION,
  "oversold-bounce": API_ENDPOINTS.SCANNER.OVERSOLD_BOUNCE,
};

export const useScanner = (type: ScannerType, params?: { sector?: string; page?: number }) => {
  return useQuery<ScreenerResponse>({
    queryKey: ["scanner", type, params],
    queryFn: async () => {
      const response = await apiClient.get<ScreenerResponse>(ENDPOINT_MAP[type], { params });
      return response as unknown as ScreenerResponse;
    },
  });
};
