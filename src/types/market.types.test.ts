import { describe, expect, it } from "vitest";

import { toChartCandles, type PriceCandle } from "@/types";

const candle: PriceCandle = {
  time: "2026-01-05T00:00:00Z",
  open: 9000,
  high: 9100,
  low: 8900,
  close: 9050,
  volume: 1000000,
  interval: "1d",
  source: "sample",
};

describe("toChartCandles", () => {
  it("maps candle fields and converts time to a YYYY-MM-DD date", () => {
    const result = toChartCandles([candle]);
    expect(result[0]).toEqual({
      time: "2026-01-05",
      open: 9000,
      high: 9100,
      low: 8900,
      close: 9050,
    });
  });

  it("returns an empty array for empty input", () => {
    expect(toChartCandles([])).toEqual([]);
  });

  it("coerces string-price numeric fields", () => {
    const stringy: PriceCandle = { ...candle, open: "9200" as unknown as number };
    expect(toChartCandles([stringy])[0].open).toBe(9200);
  });
});