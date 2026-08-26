import { describe, expect, it } from "vitest";

import { useStockScore } from "@/hooks/market";

describe("useStockScore hook", () => {
  it("is defined and exports expected hook", () => {
    expect(typeof useStockScore).toBe("function");
  });
});
