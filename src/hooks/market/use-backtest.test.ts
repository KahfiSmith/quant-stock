import { describe, expect, it } from "vitest";

import { useRunBacktest } from "@/hooks/market";

describe("useRunBacktest hook", () => {
  it("is defined and exports expected hook", () => {
    expect(typeof useRunBacktest).toBe("function");
  });
});
