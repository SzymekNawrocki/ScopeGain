"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  LineSeries,
  ColorType,
  CrosshairMode,
  type IChartApi,
} from "lightweight-charts";
import { PerformancePoint } from "../lib/api";

// Dwie linie od 100: portfel (neon zielony) vs rynek (cyan).
// Ta sama mechanika co PriceChart - useRef + useEffect + sprzatanie.
export function PerformanceChart({
  series,
  benchmarkLabel,
}: {
  series: PerformancePoint[];
  benchmarkLabel: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart: IChartApi = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#12121a" },
        textColor: "#9ca3af",
        fontFamily: "var(--font-jetbrains), monospace",
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: "rgba(42, 42, 58, 0.4)" },
        horzLines: { color: "rgba(42, 42, 58, 0.4)" },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: "#2a2a3a" },
      timeScale: { borderColor: "#2a2a3a" },
    });

    // Portfel - grubsza zielona linia (bohater wykresu).
    const portfel = chart.addSeries(LineSeries, {
      color: "#00ff88",
      lineWidth: 2,
      priceLineVisible: false,
      title: "portfel",
    });
    portfel.setData(series.map((p) => ({ time: p.time, value: p.portfolio })));

    // Rynek - cieńsza cyan, dla kontrastu.
    const rynek = chart.addSeries(LineSeries, {
      color: "#00d4ff",
      lineWidth: 1,
      priceLineVisible: false,
      title: benchmarkLabel,
    });
    rynek.setData(series.map((p) => ({ time: p.time, value: p.benchmark })));

    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [series, benchmarkLabel]);

  return <div ref={containerRef} className="h-[360px] w-full" />;
}
