"use client";

import { useEffect, useState } from "react";
import {
  getPortfolioCorrelations,
  getPortfolioPerformance,
  getPortfolioVerdict,
  PERIODS,
  Period,
  PortfolioCorrelations,
  PortfolioPerformance,
  PortfolioVerdict,
} from "../lib/api";
import { PerformanceChart } from "./PerformanceChart";
import { CorrelationMatrix } from "./CorrelationMatrix";
import { usePortfoliosContext } from "./PortfoliosProvider";
import { TerminalWindow } from "./ui/TerminalWindow";
import { StatTile } from "./ui/StatTile";
import { StatusPanel } from "./ui/StatusPanel";
import { VerdictFindings } from "./ui/VerdictFindings";
import { pnlColor, withSign } from "../lib/format";


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

// Sekcja "portfel vs rynek": krzywa wzrostu i alpha dla wspolnie wybranego
// portfela (selectedId z PortfoliosProvider) + wybor zakresu.
export function PortfolioVsMarket() {
  const { selectedId } = usePortfoliosContext();
  const [period, setPeriod] = useState<Period>("1y");
  const [perf, setPerf] = useState<PortfolioPerformance | null>(null);
  const [corr, setCorr] = useState<PortfolioCorrelations | null>(null);
  const [verdict, setVerdict] = useState<PortfolioVerdict | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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

    getPortfolioVerdict(selectedId, period)
      .then((v) => aktualne && setVerdict(v))
      .catch(() => aktualne && setVerdict(null));

    return () => {
      aktualne = false;
    };
  }, [selectedId, period]);

  return (
    <div>
      <TerminalWindow title={`Analiza vs rynek${perf ? ` — ${perf.name}` : ""}`}>
        {/* Sterowanie: zakres (wybor portfela jest wspolny, na gorze zakladki) */}
        <div className="mb-5 flex flex-wrap items-center gap-4">
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

        {/* WERDYKT - apka mowi wprost, co z liczb wynika (wniosek najpierw) */}
        {verdict && verdict.id === selectedId && <VerdictPanel verdict={verdict} />}

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
              <span className="text-sm uppercase tracking-[0.15em] text-muted-foreground">alpha</span>
              <span className={`font-display text-lg font-bold ${pnlColor(perf.alpha_pct)}`}>
                {withSign(perf.alpha_pct)}%
              </span>
            </span>
          </div>
        )}

        {/* Uczciwosc: backtest rzutuje DZISIEJSZE ilosci na caly okres (brak logu
            transakcji) - to hipoteza "gdybym od poczatku trzymal to, co mam dzis",
            nie Twoja realna sciezka. */}
        {perf && (
          <p className="mb-4 font-mono text-xs italic text-muted-foreground">
            * krzywa hipotetyczna — zaklada dzisiejsze wagi przez caly okres (bez historii transakcji)
          </p>
        )}

        {/* Panel ryzyko/nagroda - twarde metryki, ktorych broker nie daje */}
        {perf && <RiskPanel risk={perf.risk} />}

        {/* Stany */}
        {error ? (
          <StatusPanel variant="error">
            <p className="mb-1 uppercase tracking-[0.2em]">// signal lost</p>
            <p className="text-foreground">{error}</p>
          </StatusPanel>
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
            <p className="mb-3 font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
              Korelacje — <span className="text-accent">0 = niezalezne (dobra dywersyfikacja)</span>,{" "}
              <span className="text-accent-secondary">+1 = chodza razem</span>
            </p>
            <CorrelationMatrix tickers={corr.tickers} matrix={corr.matrix} />
          </div>
        )}
      </TerminalWindow>
    </div>
  );
}

// Panel werdyktu: ocena laczna + lista wnioskow po ludzku z kolorem wagi.
function VerdictPanel({ verdict }: { verdict: PortfolioVerdict }) {
  return (
    <VerdictFindings
      title="Werdykt - czego broker Ci nie powie"
      grade={verdict.grade}
      // Bylo: wlasny slownik SEV_LABEL kluczowany po severity, ktory
      // ignorowal grade_label z backendu. Teraz jedno zrodlo prawdy - API.
      gradeLabel={`ocena: ${verdict.grade_label}`}
      findings={verdict.findings}
    />
  );
}

// Panel metryk ryzyko/nagroda: Sharpe + beta + zwrot/ryzyko.
function RiskPanel({ risk }: { risk: import("../lib/api").PortfolioRisk }) {
  const s = sharpeVerdict(risk.sharpe);
  return (
    <div className="mb-4">
      <p className="mb-2 font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
        Ryzyko / nagroda — czego broker Ci nie pokaze
      </p>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        <StatTile label="Sharpe" value={risk.sharpe.toFixed(2)} hint={s.label} className={s.color} />
        <StatTile
          label="Beta (vs rynek)"
          value={risk.beta.toFixed(2)}
          hint={betaVerdict(risk.beta)}
          className="text-accent-tertiary"
        />
        <StatTile
          label="Zwrot / ryzyko"
          value={risk.return_risk.toFixed(2)}
          hint={`zmiennosc ${risk.volatility_pct.toFixed(1)}%`}
          className={pnlColor(risk.return_risk)}
        />
      </div>
    </div>
  );
}
