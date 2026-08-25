import { QueryClient, QueryClientProvider, type QueryClientConfig } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";
import MockAdapter from "axios-mock-adapter";
import type { ReactNode } from "react";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";

import { useRegister } from "@/hooks/auth/use-register";
import { authClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { useAuthStore } from "@/store";

const mocks = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mocks.push, replace: mocks.replace }),
}));

const input = {
  name: "Quant User",
  email: "user@example.com",
  password: "password123",
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

describe("useRegister", () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(authClient, { onNoMatch: "throwException" });
    mocks.push.mockReset();
    useAuthStore.setState({ status: "idle", accessToken: null, user: null });
  });

  afterEach(() => {
    mock.restore();
  });

  it("navigates to login after a successful registration", async () => {
    mock.onPost(API_ENDPOINTS.AUTH.REGISTER).reply(201, {
      success: true,
      message: "Registered",
      data: { id: 1 },
    });

    const { result } = renderHook(() => useRegister(), { wrapper: createWrapper() });
    await result.current.register(input);

    expect(mocks.push).toHaveBeenCalledWith("/login");
  });

  it("rejects when registration fails and does not navigate", async () => {
    mock.onPost(API_ENDPOINTS.AUTH.REGISTER).reply(409, {
      success: false,
      message: "Email already registered",
      code: "EMAIL_ALREADY_REGISTERED",
    });

    const { result } = renderHook(() => useRegister(), { wrapper: createWrapper() });
    await expect(result.current.register(input)).rejects.toBeTruthy();

    expect(mocks.push).not.toHaveBeenCalled();
  });
});