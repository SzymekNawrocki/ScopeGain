"use client";

import { useEffect, useState } from "react";
import {
  getPortfolioCorrelations,
  getPortfolioPerformance,
  PERIODS,
  Period,
  Portfolio,
  PortfolioCorrelations,
  PortfolioPerformance,
} from "../lib/api";
import { PerformanceChart } from "./PerformanceChart";
import { CorrelationMatrix } from "./CorrelationMatrix";

const pnlColor = (n: number | null | undefined) =>
  n == null ? "text-foreground" : n >= 0 ? "text-accent" : "text-destructive";
const withSign = (n: number) => `${n >= 0 ? "+" : ""}${n.toFixed(2)}`;

// Slowna ocena Sharpe'a wg reguly kciuka + kolor.
function sharpeVerdict(s: number): { label: string; color: string } {
  if (s < 0.5) return { label: "slaby", color: "text-destructive" };
  if (s < 1) return { label: "przecietny", color: "text-foreground" };
  if (s < 2) return { label: "dobry", color: "text-accent" };
  return { label: "swietny", color: "text-accent" };
}

// Beta -> co to znaczy po ludzku (nie jest 'dobra' ani 'zla' sama w sobie).
function betaVerdict(b: number): string {
  if (b < 0) return "odwrotnie do rynku";
  if (b < 0.9) return "spokojniej niz rynek";
  if (b <= 1.1) return "jak rynek";
  return "mocniej niz rynek";
}

// Sekcja "portfel vs rynek": wybor portfela + zakresu, krzywa wzrostu i alpha.
export function PortfolioVsMarket({ portfolios }: { portfolios: Portfolio[] }) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [period, setPeriod] = useState<Period>("1y");
  const [perf, setPerf] = useState<PortfolioPerformance | null>(null);
  const [corr, setCorr] = useState<PortfolioCorrelations | null>(null);
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

    getPortfolioCorrelations(selectedId, period)
      .then((c) => aktualne && setCorr(c))
      .catch(() => aktualne && setCorr(null));

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

          {/* Panel ryzyko/nagroda - twarde metryki, ktorych broker nie daje */}
          {perf && <RiskPanel risk={perf.risk} />}

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

          {/* Korelacje: jak bardzo spolki chodza razem (dywersyfikacja) */}
          {corr && (
            <div className="mt-6 border-t border-border pt-5">
              <p className="mb-3 font-mono text-[0.65rem] uppercase tracking-[0.2em] text-muted-foreground">
                Korelacje — <span className="text-accent">0 = niezalezne (dobra dywersyfikacja)</span>,{" "}
                <span className="text-accent-secondary">+1 = chodza razem</span>
              </p>
              <CorrelationMatrix tickers={corr.tickers} matrix={corr.matrix} />
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

// Panel metryk ryzyko/nagroda: Sharpe + beta + zwrot/ryzyko.
function RiskPanel({ risk }: { risk: import("../lib/api").PortfolioRisk }) {
  const s = sharpeVerdict(risk.sharpe);
  return (
    <div className="mb-4">
      <p className="mb-2 font-mono text-[0.6rem] uppercase tracking-[0.2em] text-muted-foreground">
        Ryzyko / nagroda — czego broker Ci nie pokaze
      </p>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        <RiskTile label="Sharpe" value={risk.sharpe.toFixed(2)} hint={s.label} className={s.color} />
        <RiskTile
          label="Beta (vs rynek)"
          value={risk.beta.toFixed(2)}
          hint={betaVerdict(risk.beta)}
          className="text-accent-tertiary"
        />
        <RiskTile
          label="Zwrot / ryzyko"
          value={risk.return_risk.toFixed(2)}
          hint={`zmiennosc ${risk.volatility_pct.toFixed(1)}%`}
          className={pnlColor(risk.return_risk)}
        />
      </div>
    </div>
  );
}

function RiskTile({
  label,
  value,
  hint,
  className,
}: {
  label: string;
  value: string;
  hint: string;
  className?: string;
}) {
  return (
    <div className="cyber-chamfer-sm border border-border bg-[#12121a] px-4 py-3">
      <p className="font-mono text-[0.6rem] uppercase tracking-[0.2em] text-muted-foreground">
        {label}
      </p>
      <p className={`mt-1 font-display text-xl font-bold ${className ?? "text-foreground"}`}>
        {value}
      </p>
      <p className="mt-0.5 font-mono text-[0.6rem] text-muted-foreground">{hint}</p>
    </div>
  );
}
