import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { QUERY_KEYS } from "@/lib/api/query-keys";
import { useAuthStore } from "@/store";
import type { User } from "@/types";

export type UpdateProfileInput = {
  name?: string;
  theme_preference?: "light" | "dark" | "system";
  timezone?: string;
};

export const useUpdateProfile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: UpdateProfileInput) => {
      const response = await apiClient.patch<User>(API_ENDPOINTS.AUTH.UPDATE_PROFILE, input);
      return response as unknown as User;
    },
    onSuccess: (user) => {
      useAuthStore.setState({ user });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.AUTH.SESSION });
    },
  });
};
