import { describe, expect, it } from "vitest";

import { useStockScreener } from "@/hooks/market";

describe("useStockScreener hook", () => {
  it("is defined and exports expected hook", () => {
    expect(typeof useStockScreener).toBe("function");
  });
});
