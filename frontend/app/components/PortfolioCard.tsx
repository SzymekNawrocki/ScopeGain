"use client";

import { useEffect, useState } from "react";
import {
  Portfolio,
  PortfolioValuation,
  costBasis,
  getPortfolioValuation,
} from "../lib/api";

// Formatuje liczbe jako kwote (2 miejsca, separatory tysiecy).
const fmt = (n: number) =>
  n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// Zysk >= 0 -> neon zielony, strata -> czerwien. Zwraca klase Tailwinda.
const pnlColor = (n: number | null | undefined) =>
  n == null ? "text-muted-foreground" : n >= 0 ? "text-accent" : "text-destructive";

// Znak + strzalka przed liczba (▲ zysk / ▼ strata).
const sign = (n: number) => (n >= 0 ? "▲ +" : "▼ ");

export function PortfolioCard({ portfolio }: { portfolio: Portfolio }) {
  // Wycena dociagana osobno dla KAZDEJ karty - komponent sam o siebie dba.
  const [val, setVal] = useState<PortfolioValuation | null>(null);

  useEffect(() => {
    let aktualne = true;
    getPortfolioValuation(portfolio.id)
      .then((v) => aktualne && setVal(v))
      .catch(() => {}); // brak wyceny -> zostaje sam koszt wejscia (nizej)
    return () => {
      aktualne = false;
    };
  }, [portfolio.id]);

  // Mapa ticker -> policzona pozycja, zeby dokleic cene/zysk do wiersza.
  const wyceny = new Map(val?.positions.map((p) => [p.id, p]) ?? []);

  return (
    <article className="group relative">
      {/* Narozne akcenty HUD */}
      <span className="pointer-events-none absolute left-0 top-0 h-3 w-3 border-l-2 border-t-2 border-accent" />
      <span className="pointer-events-none absolute right-0 top-0 h-3 w-3 border-r-2 border-t-2 border-accent" />
      <span className="pointer-events-none absolute bottom-0 left-0 h-3 w-3 border-b-2 border-l-2 border-accent" />
      <span className="pointer-events-none absolute bottom-0 right-0 h-3 w-3 border-b-2 border-r-2 border-accent" />

      <div className="cyber-chamfer border border-border bg-card transition-all duration-300 group-hover:border-accent group-hover:shadow-glow">
        {/* Pasek terminala + odznaka calkowitego zysku */}
        <header className="flex items-center gap-2 border-b border-border bg-muted/40 px-4 py-2">
          <span className="h-2.5 w-2.5 rounded-full bg-destructive" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#ffcc00]" />
          <span className="h-2.5 w-2.5 rounded-full bg-accent" />
          <span className="ml-2 truncate font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
            ~/portfolios/{portfolio.id}
          </span>
          {val && (
            <span className={`ml-auto font-mono text-xs font-bold ${pnlColor(val.total_pnl_pct)}`}>
              {sign(val.total_pnl_pct)}
              {fmt(Math.abs(val.total_pnl_pct))}%
            </span>
          )}
        </header>

        <div className="p-5">
          <h2 className="font-display text-xl font-bold uppercase tracking-wide text-foreground text-glow">
            {portfolio.name}
          </h2>

          {/* Pozycje */}
          <div className="mt-4 space-y-1">
            {portfolio.positions.length === 0 ? (
              <p className="font-mono text-sm text-muted-foreground">
                <span className="text-accent">$</span> brak pozycji — pusty portfel
              </p>
            ) : (
              <>
                <div className="grid grid-cols-[1fr_auto_auto_auto] gap-4 border-b border-border pb-1 font-mono text-[0.65rem] uppercase tracking-[0.2em] text-muted-foreground">
                  <span>Ticker</span>
                  <span className="text-right">Ilosc</span>
                  <span className="text-right">Teraz</span>
                  <span className="text-right">Zysk</span>
                </div>
                {portfolio.positions.map((pos) => {
                  const w = wyceny.get(pos.id);
                  return (
                    <div
                      key={pos.id}
                      className="grid grid-cols-[1fr_auto_auto_auto] gap-4 py-1 font-mono text-sm"
                    >
                      <span className="font-bold text-accent-tertiary">{pos.ticker}</span>
                      <span className="text-right text-foreground">{fmt(pos.quantity)}</span>
                      {/* Dopoki wycena nie doszla - migajacy placeholder */}
                      <span className="text-right text-muted-foreground">
                        {w?.current_price != null ? fmt(w.current_price) : "···"}
                      </span>
                      <span className={`text-right font-bold ${pnlColor(w?.pnl_pct)}`}>
                        {w?.pnl_pct != null ? `${w.pnl_pct >= 0 ? "+" : ""}${fmt(w.pnl_pct)}%` : "···"}
                      </span>
                    </div>
                  );
                })}
              </>
            )}
          </div>

          {/* Podsumowanie: koszt wejscia -> wartosc dzis -> zysk/strata */}
          <footer className="mt-4 space-y-2 border-t border-border pt-3">
            <div className="flex items-baseline justify-between">
              <span className="font-mono text-[0.65rem] uppercase tracking-[0.2em] text-muted-foreground">
                Koszt wejscia
              </span>
              <span className="font-mono text-sm text-muted-foreground">
                ${fmt(val?.total_cost ?? costBasis(portfolio))}
              </span>
            </div>
            <div className="flex items-baseline justify-between">
              <span className="font-mono text-[0.65rem] uppercase tracking-[0.2em] text-muted-foreground">
                Wartosc dzis
              </span>
              <span className="font-display text-lg font-bold text-accent text-glow">
                {val ? `$${fmt(val.total_value)}` : "···"}
              </span>
            </div>
            {val && (
              <div className="flex items-baseline justify-between">
                <span className="font-mono text-[0.65rem] uppercase tracking-[0.2em] text-muted-foreground">
                  Zysk / strata
                </span>
                <span className={`font-display text-lg font-bold ${pnlColor(val.total_pnl_abs)}`}>
                  {val.total_pnl_abs >= 0 ? "+" : "−"}${fmt(Math.abs(val.total_pnl_abs))}
                </span>
              </div>
            )}
          </footer>
        </div>
      </div>
    </article>
  );
}
