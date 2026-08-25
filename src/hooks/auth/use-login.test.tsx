import { QueryClient, QueryClientProvider, type QueryClientConfig } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";
import MockAdapter from "axios-mock-adapter";
import type { ReactNode } from "react";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";

import { useLogin } from "@/hooks/auth/use-login";
import { authClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { useAuthStore } from "@/store";
import type { BackendAuthPayload, User } from "@/types";

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

const payload: BackendAuthPayload = {
  access_token: "access-123",
  expires_in: 900,
  user,
};

const credentials = { email: user.email, password: "password123" };

function createWrapper() {
  const config: QueryClientConfig = {
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  };
  const queryClient = new QueryClient(config);
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe("useLogin", () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(authClient, { onNoMatch: "throwException" });
    mocks.replace.mockReset();
    useAuthStore.setState({ status: "idle", accessToken: null, user: null });
  });

  afterEach(() => {
    mock.restore();
  });

  it("stores the session and navigates to the profile on success", async () => {
    mock.onPost(API_ENDPOINTS.AUTH.LOGIN).reply(200, {
      success: true,
      message: "Logged in",
      data: payload,
    });

    const { result } = renderHook(() => useLogin(), { wrapper: createWrapper() });
    await result.current.login(credentials);

    expect(useAuthStore.getState().accessToken).toBe("access-123");
    expect(useAuthStore.getState().status).toBe("authenticated");
    expect(mocks.replace).toHaveBeenCalledWith("/profile");
  });

  it("redirects to a safe explicit redirectTo", async () => {
    mock.onPost(API_ENDPOINTS.AUTH.LOGIN).reply(200, {
      success: true,
      message: "Logged in",
      data: payload,
    });

    const { result } = renderHook(() => useLogin(), { wrapper: createWrapper() });
    await result.current.login({ ...credentials, redirectTo: "/stocks" });

    expect(mocks.replace).toHaveBeenCalledWith("/stocks");
  });

  it("falls back to the profile for unsafe redirect targets", async () => {
    mock.onPost(API_ENDPOINTS.AUTH.LOGIN).reply(200, {
      success: true,
      message: "Logged in",
      data: payload,
    });

    const { result } = renderHook(() => useLogin(), { wrapper: createWrapper() });
    await result.current.login({ ...credentials, redirectTo: "https://evil.example" });

    expect(mocks.replace).toHaveBeenCalledWith("/profile");
  });

  it("does not mutate the store when login fails", async () => {
    mock.onPost(API_ENDPOINTS.AUTH.LOGIN).reply(401, {
      success: false,
      message: "Invalid credentials",
      code: "INVALID_CREDENTIALS",
    });

    const { result } = renderHook(() => useLogin(), { wrapper: createWrapper() });
    await expect(result.current.login(credentials)).rejects.toBeTruthy();

    expect(useAuthStore.getState().status).toBe("idle");
    expect(mocks.replace).not.toHaveBeenCalled();
  });
});