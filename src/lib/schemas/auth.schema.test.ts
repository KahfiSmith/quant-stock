import { describe, expect, it } from "vitest";

import { loginSchema, registerSchema, deleteAccountSchema } from "@/lib/schemas/auth.schema";

describe("loginSchema", () => {
  it("accepts a valid email and password", () => {
    const result = loginSchema.safeParse({ email: "user@example.com", password: "password123" });
    expect(result.success).toBe(true);
  });

  it("rejects a missing email", () => {
    const result = loginSchema.safeParse({ password: "password123" });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid email format", () => {
    const result = loginSchema.safeParse({ email: "not-an-email", password: "password123" });
    expect(result.success).toBe(false);
  });

  it("rejects a password shorter than 8 characters", () => {
    const result = loginSchema.safeParse({ email: "user@example.com", password: "short" });
    expect(result.success).toBe(false);
  });

  it("allows an optional redirectTo", () => {
    const result = loginSchema.safeParse({
      email: "user@example.com",
      password: "password123",
      redirectTo: "/stocks",
    });
    expect(result.success).toBe(true);
  });
});

describe("registerSchema", () => {
  it("accepts a valid name, email, and password", () => {
    const result = registerSchema.safeParse({
      name: "Quant User",
      email: "user@example.com",
      password: "password123",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a name shorter than 2 characters", () => {
    const result = registerSchema.safeParse({
      name: "A",
      email: "user@example.com",
      password: "password123",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid email format", () => {
    const result = registerSchema.safeParse({
      name: "Quant User",
      email: "nope",
      password: "password123",
    });
    expect(result.success).toBe(false);
  });
});

describe("deleteAccountSchema", () => {
  it("accepts a non-empty password", () => {
    const result = deleteAccountSchema.safeParse({ password: "password123" });
    expect(result.success).toBe(true);
  });

  it("rejects a missing password", () => {
    const result = deleteAccountSchema.safeParse({});
    expect(result.success).toBe(false);
  });
});