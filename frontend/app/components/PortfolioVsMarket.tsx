"use client";

import { useEffect, useState } from "react";
import {
  getPortfolioPerformance,
  PERIODS,
  Period,
  Portfolio,
  PortfolioPerformance,
} from "../lib/api";
import { PerformanceChart } from "./PerformanceChart";

const pnlColor = (n: number | null | undefined) =>
  n == null ? "text-foreground" : n >= 0 ? "text-accent" : "text-destructive";
const withSign = (n: number) => `${n >= 0 ? "+" : ""}${n.toFixed(2)}`;

// Sekcja "portfel vs rynek": wybor portfela + zakresu, krzywa wzrostu i alpha.
export function PortfolioVsMarket({ portfolios }: { portfolios: Portfolio[] }) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [period, setPeriod] = useState<Period>("1y");
  const [perf, setPerf] = useState<PortfolioPerformance | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Domyslnie pierwszy portfel, gdy tylko lista dojdzie.
  useEffect(() => {
    if (selectedId === null && portfolios.length > 0) {
      setSelectedId(portfolios[0].id);
    }
  }, [portfolios, selectedId]);

  useEffect(() => {
    if (selectedId === null) return;
    let aktualne = true;
    setLoading(true);
    setError(null);

    getPortfolioPerformance(selectedId, period)
      .then((p) => aktualne && setPerf(p))
      .catch((e) => {
        if (aktualne) {
          setError(e.message ?? "Blad pobierania");
          setPerf(null);
        }
      })
      .finally(() => aktualne && setLoading(false));

    return () => {
      aktualne = false;
    };
  }, [selectedId, period]);

  if (portfolios.length === 0) return null; // nie ma czego porownywac

  return (
    <section className="mb-12">
      <p className="mb-4 font-mono text-xs uppercase tracking-[0.3em] text-accent-tertiary">
        <span className="text-accent">$</span> ./portfolio --vs-market
      </p>

      <div className="cyber-chamfer border border-border bg-card">
        <header className="flex items-center gap-2 border-b border-border bg-muted/40 px-4 py-2">
          <span className="h-2.5 w-2.5 rounded-full bg-destructive" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#ffcc00]" />
          <span className="h-2.5 w-2.5 rounded-full bg-accent" />
          <span className="ml-2 font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
            ~/backtest{perf ? `/${perf.name}` : ""}
          </span>
        </header>

        <div className="p-5">
          {/* Sterowanie: wybor portfela (jesli >1) + zakres */}
          <div className="mb-5 flex flex-wrap items-center gap-4">
            {portfolios.length > 1 && (
              <div className="flex flex-wrap gap-1">
                {portfolios.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setSelectedId(p.id)}
                    className={`cyber-chamfer-sm border px-3 py-1.5 font-mono text-xs uppercase tracking-wider transition-all ${
                      p.id === selectedId
                        ? "border-accent bg-accent/10 text-accent shadow-glow"
                        : "border-border text-muted-foreground hover:border-accent hover:text-accent"
                    }`}
                  >
                    {p.name}
                  </button>
                ))}
              </div>
            )}
            <div className="flex gap-1">
              {PERIODS.map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`cyber-chamfer-sm border px-3 py-1.5 font-mono text-xs uppercase tracking-wider transition-all ${
                    p === period
                      ? "border-accent bg-accent/10 text-accent shadow-glow"
                      : "border-border text-muted-foreground hover:border-accent hover:text-accent"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Podsumowanie: portfel / rynek / alpha + legenda */}
          {perf && (
            <div className="mb-4 flex flex-wrap items-center gap-x-8 gap-y-2 font-mono text-sm">
              <span className="flex items-center gap-2">
                <span className="inline-block h-0.5 w-5 bg-accent" />
                <span className="text-muted-foreground">portfel</span>
                <span className={`font-bold ${pnlColor(perf.portfolio_return_pct)}`}>
                  {withSign(perf.portfolio_return_pct)}%
                </span>
              </span>
              <span className="flex items-center gap-2">
                <span className="inline-block h-0.5 w-5 bg-accent-tertiary" />
                <span className="text-muted-foreground">{perf.benchmark_ticker}</span>
                <span className={`font-bold ${pnlColor(perf.benchmark_return_pct)}`}>
                  {withSign(perf.benchmark_return_pct)}%
                </span>
              </span>
              <span className="flex items-center gap-2">
                <span className="text-muted-foreground uppercase tracking-[0.15em] text-[0.7rem]">
                  alpha
                </span>
                <span className={`font-display text-lg font-bold ${pnlColor(perf.alpha_pct)}`}>
                  {withSign(perf.alpha_pct)}%
                </span>
              </span>
            </div>
          )}

          {/* Stany */}
          {error ? (
            <div className="cyber-chamfer border-2 border-destructive bg-card p-6 font-mono text-sm text-destructive">
              <p className="mb-1 uppercase tracking-[0.2em]">// signal lost</p>
              <p className="text-foreground">{error}</p>
            </div>
          ) : (
            <div className="relative">
              {loading && (
                <div className="absolute inset-0 z-10 flex items-center justify-center bg-card/70 font-mono text-sm text-accent">
                  <span className="cursor-blink">&gt; liczenie backtestu</span>
                </div>
              )}
              {perf && (
                <PerformanceChart series={perf.series} benchmarkLabel={perf.benchmark_ticker} />
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
