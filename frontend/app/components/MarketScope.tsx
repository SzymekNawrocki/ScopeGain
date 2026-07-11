"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  getStockHistory,
  getStockMetrics,
  PERIODS,
  Period,
  StockHistory,
  StockMetrics,
} from "../lib/api";
import { PriceChart } from "./PriceChart";
import { TerminalWindow } from "./ui/TerminalWindow";
import { StatTile } from "./ui/StatTile";
import { StatusPanel } from "./ui/StatusPanel";
import { pnlColor, withSign } from "../lib/format";

// Sekcja "market scope": pole na ticker + wybor zakresu + wykres swiecowy.
// Cala logika (fetch, stany) zyje tu; PriceChart tylko maluje wynik.
export function MarketScope() {
  const [query, setQuery] = useState("AAPL"); // to, co user wpisuje
  const [ticker, setTicker] = useState("AAPL"); // aktywnie pobrana spolka
  const [period, setPeriod] = useState<Period>("6mo");

  const [data, setData] = useState<StockHistory | null>(null);
  const [metrics, setMetrics] = useState<StockMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Pobierz historie ORAZ metryki za kazdym razem, gdy zmieni sie spolka/zakres.
  // Dwa niezalezne strzaly - wykres i statystyki moga dojsc w innym tempie.
  useEffect(() => {
    let aktualne = true; // straznik: ignoruj odpowiedz starego zapytania
    setLoading(true);
    setError(null);

    getStockHistory(ticker, period)
      .then((h) => {
        if (aktualne) setData(h);
      })
      .catch((e) => {
        if (aktualne) {
          setError(e.message ?? "Blad pobierania");
          setData(null);
        }
      })
      .finally(() => {
        if (aktualne) setLoading(false);
      });

    getStockMetrics(ticker, period)
      .then((m) => aktualne && setMetrics(m))
      .catch(() => aktualne && setMetrics(null));

    return () => {
      aktualne = false; // odpowiedz przyjdzie za pozno -> odrzuc ja
    };
  }, [ticker, period]);

  // Enter w polu -> ustaw nowa spolke (effect wyzej sam dociagnie dane).
  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const t = query.trim().toUpperCase();
    if (t) setTicker(t);
  }

  return (
    <div className="mb-12">
      <TerminalWindow title={`~/market/${ticker}`}>
        {/* Sterowanie: pole na ticker + przyciski zakresu */}
        <div className="mb-5 flex flex-wrap items-center gap-4">
          <form onSubmit={onSubmit} className="relative">
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 font-mono text-accent">
              &gt;
            </span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              spellCheck={false}
              aria-label="Symbol spolki"
              placeholder="AAPL"
              className="cyber-chamfer-sm w-40 border border-border bg-[#12121a] py-2 pl-8 pr-3 font-mono text-sm uppercase text-accent outline-none transition-all placeholder:text-muted-foreground focus:border-accent focus:shadow-glow"
            />
          </form>

          <div className="flex gap-1">
            {PERIODS.map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`cyber-chamfer-sm border px-3 py-1.5 font-mono text-sm uppercase tracking-wider transition-all ${
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

        {/* Naglowek wykresu: spolka + ostatnie zamkniecie */}
        <div className="mb-3 flex items-baseline gap-3">
          <h2 className="font-display text-2xl font-bold uppercase tracking-wide text-foreground">
            {ticker}
          </h2>
          {data && data.candles.length > 0 && (
            <span className="font-mono text-sm text-accent">
              ${data.candles[data.candles.length - 1].close.toFixed(2)}
            </span>
          )}
        </div>

        {/* Panel metryk quant (warstwa 6): zwrot, ryzyko, ja vs rynek */}
        {metrics && metrics.ticker === ticker && (
          <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatTile
              label={`Zwrot ${period}`}
              value={`${withSign(metrics.return_pct)}%`}
              className={pnlColor(metrics.return_pct)}
            />
            <StatTile
              label="Zmiennosc (rok)"
              value={`${metrics.volatility_pct.toFixed(2)}%`}
              className="text-accent-tertiary"
            />
            <StatTile
              label="Max drawdown"
              value={`${metrics.max_drawdown_pct.toFixed(2)}%`}
              className="text-destructive"
            />
            <StatTile
              label={`vs ${metrics.benchmark.ticker}`}
              value={metrics.alpha_pct != null ? `${withSign(metrics.alpha_pct)}%` : "—"}
              className={pnlColor(metrics.alpha_pct)}
              hint={
                metrics.benchmark.return_pct != null
                  ? `rynek ${withSign(metrics.benchmark.return_pct)}%`
                  : undefined
              }
            />
          </div>
        )}

        {/* Stany: blad / ladowanie / wykres */}
        {error ? (
          <StatusPanel variant="error">
            <p className="mb-1 uppercase tracking-[0.2em]">// signal lost</p>
            <p className="text-foreground">{error}</p>
          </StatusPanel>
        ) : (
          <div className="relative">
            {loading && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-card/70 font-mono text-sm text-accent">
                <span className="cursor-blink">&gt; pobieranie swiec</span>
              </div>
            )}
            {data && <PriceChart candles={data.candles} />}
          </div>
        )}
      </TerminalWindow>
    </div>
  );
}
