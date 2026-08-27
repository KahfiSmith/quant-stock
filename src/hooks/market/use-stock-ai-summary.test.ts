import { describe, expect, it } from "vitest";

import { useStockAiSummary } from "@/hooks/market";

describe("useStockAiSummary hook", () => {
  it("is defined and exports expected hook", () => {
    expect(typeof useStockAiSummary).toBe("function");
  });
});
