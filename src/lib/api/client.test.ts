import MockAdapter from "axios-mock-adapter";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ROUTES } from "@/config/routes";
import { apiClient, authClient } from "@/lib/api/client";
import { API_ENDPOINTS } from "@/lib/api/endpoints";
import { useAuthStore } from "@/store";
import type { BackendAuthPayload, User } from "@/types";

const user: User = {
  id: 1,
  email: "user@example.com",
  name: "Quant User",
  role: "user",
  is_email_verified: false,
};

const authPayload = (accessToken = "access-123"): BackendAuthPayload => ({
  access_token: accessToken,
  expires_in: 900,
  user,
});

const expiredEnvelope = {
  success: false,
  message: "Access token expired",
  code: "ACCESS_TOKEN_EXPIRED",
};

const setSession = (accessToken: string) => {
  useAuthStore.getState().setSession({
    accessToken,
    expiresIn: 900,
    user,
  });
};

let apiMock: MockAdapter;
let authMock: MockAdapter;

beforeEach(() => {
  apiMock = new MockAdapter(apiClient, { onNoMatch: "throwException" });
  authMock = new MockAdapter(authClient, { onNoMatch: "throwException" });
  useAuthStore.setState({ status: "idle", accessToken: null, user: null });
});

afterEach(() => {
  apiMock.restore();
  authMock.restore();
  useAuthStore.setState({ status: "idle", accessToken: null, user: null });
});

describe("apiClient response interceptor", () => {
  it("unwraps the API envelope on success", async () => {
    apiMock.onGet("/items").reply(200, {
      success: true,
      message: "ok",
      data: { id: 1 },
    });

    const response = await apiClient.get("/items");

    expect(response).toEqual({ id: 1 });
  });

  it("passes through responses without an envelope", async () => {
    apiMock.onGet("/raw").reply(200, { hello: "world" });

    const response = await apiClient.get("/raw");

    expect(response).toEqual({ hello: "world" });
  });
});

describe("apiClient request interceptor", () => {
  it("attaches the bearer token from the store", async () => {
    setSession("token-abc");
    let authHeader: string | undefined;

    apiMock.onGet("/secure").reply((config) => {
      authHeader = config.headers?.Authorization;
      return [200, { data: { ok: true } }];
    });

    await apiClient.get("/secure");

    expect(authHeader).toBe("Bearer token-abc");
  });
});

describe("apiClient single-flight refresh", () => {
  it("refreshes once for concurrent 401s and retries both requests", async () => {
    setSession("expired-token");
    let refreshCalls = 0;
    authMock.onPost(API_ENDPOINTS.AUTH.REFRESH).reply(() => {
      refreshCalls += 1;
      return [200, { success: true, message: "ok", data: authPayload("fresh-token") }];
    });

    let apiCalls = 0;
    apiMock.onGet("/secure").reply(() => {
      apiCalls += 1;
      if (apiCalls <= 2) return [401, expiredEnvelope];
      return [200, { data: { ok: true } }];
    });

    const [a, b] = await Promise.all([apiClient.get("/secure"), apiClient.get("/secure")]);

    expect(a).toEqual({ ok: true });
    expect(b).toEqual({ ok: true });
    expect(refreshCalls).toBe(1);
    expect(useAuthStore.getState().accessToken).toBe("fresh-token");
  });

  it("does not refresh twice when the retry also fails with 401", async () => {
    setSession("expired-token");
    let refreshCalls = 0;
    authMock.onPost(API_ENDPOINTS.AUTH.REFRESH).reply(() => {
      refreshCalls += 1;
      return [200, { success: true, message: "ok", data: authPayload("fresh-token") }];
    });

    apiMock.onGet("/secure").reply(() => [401, expiredEnvelope]);

    await expect(apiClient.get("/secure")).rejects.toBeTruthy();

    expect(refreshCalls).toBe(1);
  });

  it("clears the session and redirects to login when refresh fails", async () => {
    setSession("expired-token");
    authMock.onPost(API_ENDPOINTS.AUTH.REFRESH).reply(500, {
      success: false,
      message: "Server error",
    });
    apiMock.onGet("/secure").reply(() => [401, expiredEnvelope]);

    const replace = vi.fn();
    const originalLocation = window.location;
    Object.defineProperty(window, "location", { configurable: true, value: { replace } });

    await expect(apiClient.get("/secure")).rejects.toBeTruthy();

    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().status).toBe("unauthenticated");
    expect(replace).toHaveBeenCalledWith(ROUTES.LOGIN);

    Object.defineProperty(window, "location", { configurable: true, value: originalLocation });
  });
});