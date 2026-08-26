import { describe, expect, it } from "vitest";

import { useStockFundamental } from "@/hooks/market";

describe("useStockFundamental hook", () => {
  it("is defined and exports expected hook", () => {
    expect(typeof useStockFundamental).toBe("function");
  });
});
