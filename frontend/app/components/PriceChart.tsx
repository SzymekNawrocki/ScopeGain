"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  type IChartApi,
} from "lightweight-charts";
import { Candle } from "../lib/api";

// Czysty "malarz" wykresu: dostaje gotowe swiece i rysuje je na canvasie.
// Fetch/stany zyja wyzej (MarketScope) - ten komponent tylko renderuje.
export function PriceChart({ candles }: { candles: Candle[] }) {
  // ref = uchwyt do prawdziwego <div> w DOM. Lightweight Charts nie jest
  // Reactem - potrzebuje fizycznego elementu, w ktorym namaluje canvas.
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Tworzymy wykres w naszym divie. autoSize -> biblioteka sama pilnuje
    // szerokosci przy zmianie rozmiaru okna (wlasny ResizeObserver w srodku).
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

    // Seria swiecowa. Wzrost = neonowa zielen, spadek = czerwien "destructive".
    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#00ff88",
      downColor: "#ff3366",
      borderVisible: false,
      wickUpColor: "#00ff88",
      wickDownColor: "#ff3366",
    });
    series.setData(candles);
    chart.timeScale().fitContent(); // dopasuj zoom, zeby zmiescic caly zakres

    // Sprzatanie: gdy komponent znika lub dane sie zmieniaja, niszczymy stary
    // wykres. Bez tego zostawialibysmy wiszace canvasy i wycieki pamieci.
    return () => chart.remove();
  }, [candles]);

  return <div ref={containerRef} className="h-[420px] w-full" />;
}
