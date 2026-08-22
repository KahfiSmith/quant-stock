"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { authClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import type { LoginInput } from "@/lib/schemas/auth.schema";
import { getSafeRedirect } from "@/lib/utils/safe-redirect";
import { useAuthStore } from "@/store";
import type { ApiResponse, BackendAuthPayload } from "@/types";
import { mapAuthPayload } from "@/types";

export const useLogin = () => {
  const router = useRouter();
  const queryClient = useQueryClient();

  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginInput) => {
      const response = await authClient.post<ApiResponse<BackendAuthPayload>>(
        API_ENDPOINTS.AUTH.LOGIN,
        credentials
      );
      return mapAuthPayload(response.data.data);
    },
    onSuccess: (session, variables) => {
      useAuthStore.getState().setSession(session);
      queryClient.clear();
      router.replace(getSafeRedirect(variables.redirectTo));
    },
  });

  return {
    isPending: loginMutation.isPending,
    login: loginMutation.mutateAsync,
  };
};
