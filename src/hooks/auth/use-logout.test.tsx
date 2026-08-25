import { QueryClient, QueryClientProvider, type QueryClientConfig } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";
import MockAdapter from "axios-mock-adapter";
import type { ReactNode } from "react";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";

import { useLogout } from "@/hooks/auth/use-logout";
import { authClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { useAuthStore } from "@/store";
import type { User } from "@/types";

const mocks = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mocks.push, replace: mocks.replace }),
}));

const user: User = {
  id: 1,
  email: "user@example.com",
  name: "Quant User",
  role: "user",
  is_email_verified: false,
};

function createWrapper() {
  const config: QueryClientConfig = {
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  };
  const queryClient = new QueryClient(config);
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe("useLogout", () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(authClient, { onNoMatch: "throwException" });
    mocks.replace.mockReset();
    useAuthStore.getState().setSession({ accessToken: "access-123", expiresIn: 900, user });
  });

  afterEach(() => {
    mock.restore();
    useAuthStore.setState({ status: "idle", accessToken: null, user: null });
  });

  it("clears the session and navigates to login on success", async () => {
    mock.onPost(API_ENDPOINTS.AUTH.LOGOUT).reply(200, {
      success: true,
      message: "Logged out",
      data: null,
    });

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() });
    await result.current.logout();

    expect(useAuthStore.getState().status).toBe("unauthenticated");
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(mocks.replace).toHaveBeenCalledWith("/login");
  });

  it("clears the session and navigates to login even when the request fails", async () => {
    mock.onPost(API_ENDPOINTS.AUTH.LOGOUT).reply(500, {
      success: false,
      message: "Server error",
    });

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() });
    await expect(result.current.logout()).rejects.toBeTruthy();

    expect(useAuthStore.getState().status).toBe("unauthenticated");
    expect(mocks.replace).toHaveBeenCalledWith("/login");
  });
});