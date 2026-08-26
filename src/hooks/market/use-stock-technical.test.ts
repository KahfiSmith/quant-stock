import { describe, expect, it } from "vitest";

import { useStockTechnical } from "@/hooks/market";

describe("useStockTechnical hook", () => {
  it("is defined and exports expected hook", () => {
    expect(typeof useStockTechnical).toBe("function");
  });
});
