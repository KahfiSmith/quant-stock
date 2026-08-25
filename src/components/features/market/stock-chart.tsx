"use client";

import {
  CandlestickSeries,
  createChart,
  type CandlestickData,
  type IChartApi,
  type ISeriesApi,
  type Time,
} from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { ChartCandle } from "@/types";

type StockChartProps = {
  data: ChartCandle[];
};

export function StockChart({ data }: StockChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }
    const chart = createChart(container, {
      width: container.clientWidth,
      height: 380,
      layout: { background: { color: "transparent" } },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#16a34a",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#16a34a",
      wickDownColor: "#ef4444",
    });
    chartRef.current = chart;
    seriesRef.current = series as ISeriesApi<"Candlestick">;

    const resizeObserver = new ResizeObserver(() => {
      chart.applyOptions({ width: container.clientWidth });
    });
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    const series = seriesRef.current;
    const chart = chartRef.current;
    if (!series || !chart) {
      return;
    }
    series.setData(data as unknown as CandlestickData<Time>[]);
    chart.timeScale().fitContent();
  }, [data]);

  if (data.length === 0) {
    return (
      <div className="flex h-[380px] w-full items-center justify-center rounded-lg border bg-muted/40 text-sm text-muted-foreground">
        No price data available for this symbol yet.
      </div>
    );
  }

  return <div ref={containerRef} className="h-[380px] w-full" />;
}