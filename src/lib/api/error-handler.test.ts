import { describe, expect, it } from "vitest";

import { ApiError, toApiErrorMessage } from "@/lib/api/error-handler";

describe("toApiErrorMessage", () => {
  it("returns the message from an ApiError", () => {
    const error = new ApiError("Invalid credentials", 401, { code: "INVALID_CREDENTIALS" });
    expect(toApiErrorMessage(error)).toBe("Invalid credentials");
  });

  it("returns the message from a generic Error", () => {
    expect(toApiErrorMessage(new Error("Network failed"))).toBe("Network failed");
  });

  it("returns a safe fallback for unknown errors", () => {
    expect(toApiErrorMessage({ some: "object" })).toBe("Unexpected API error.");
    expect(toApiErrorMessage(null)).toBe("Unexpected API error.");
  });
});

describe("ApiError", () => {
  it("carries the HTTP status and payload", () => {
    const payload = { code: "RATE_LIMITED" };
    const error = new ApiError("Too many requests", 429, payload);
    expect(error.status).toBe(429);
    expect(error.payload).toEqual(payload);
    expect(error.name).toBe("ApiError");
  });
});