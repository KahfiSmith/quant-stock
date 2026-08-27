import { describe, expect, it } from "vitest";

import { usePortfolios } from "@/hooks/market";

describe("usePortfolios hook", () => {
  it("is defined and exports expected hook", () => {
    expect(typeof usePortfolios).toBe("function");
  });
});
