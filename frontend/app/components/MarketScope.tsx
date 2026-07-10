"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  getStockHistory,
  PERIODS,
  Period,
  StockHistory,
} from "../lib/api";
import { PriceChart } from "./PriceChart";

// Sekcja "market scope": pole na ticker + wybor zakresu + wykres swiecowy.
// Cala logika (fetch, stany) zyje tu; PriceChart tylko maluje wynik.
export function MarketScope() {
  const [query, setQuery] = useState("AAPL"); // to, co user wpisuje
  const [ticker, setTicker] = useState("AAPL"); // aktywnie pobrana spolka
  const [period, setPeriod] = useState<Period>("6mo");

  const [data, setData] = useState<StockHistory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Pobierz historie za kazdym razem, gdy zmieni sie spolka albo zakres.
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
    <section className="mb-12">
      <div className="cyber-chamfer border border-border bg-card">
        {/* Pasek terminala */}
        <header className="flex items-center gap-2 border-b border-border bg-muted/40 px-4 py-2">
          <span className="h-2.5 w-2.5 rounded-full bg-destructive" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#ffcc00]" />
          <span className="h-2.5 w-2.5 rounded-full bg-accent" />
          <span className="ml-2 font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
            ~/market/{ticker}
          </span>
        </header>

        <div className="p-5">
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

          {/* Naglowek wykresu: spolka + ostatnie zamkniecie */}
          <div className="mb-3 flex items-baseline gap-3">
            <h2 className="font-display text-2xl font-bold uppercase tracking-wide text-foreground text-glow">
              {ticker}
            </h2>
            {data && data.candles.length > 0 && (
              <span className="font-mono text-sm text-accent">
                ${data.candles[data.candles.length - 1].close.toFixed(2)}
              </span>
            )}
          </div>

          {/* Stany: blad / ladowanie / wykres */}
          {error ? (
            <div className="cyber-chamfer border-2 border-destructive bg-card p-6 font-mono text-sm text-destructive">
              <p className="mb-1 uppercase tracking-[0.2em]">// signal lost</p>
              <p className="text-foreground">{error}</p>
            </div>
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
        </div>
      </div>
    </section>
  );
}
