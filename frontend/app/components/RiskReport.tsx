"use client";

import { useEffect, useState } from "react";
import {
  getPortfolioRisk,
  PortfolioRiskReport,
  RISK_WINDOWS,
  RiskWindow,
  StressScenario,
  VarMeasure,
} from "../lib/api";
import { usePortfoliosContext } from "./PortfoliosProvider";
import { TerminalWindow } from "./ui/TerminalWindow";
import { StatTile } from "./ui/StatTile";
import { StatusPanel } from "./ui/StatusPanel";
import { fmt } from "../lib/format";

// Kwota w USD ze znakiem (straty ryzyka sa ujemne). Nie udajemy PLN -
// spolki notowane sa w dolarach, wiec VaR/stress tez sa w dolarach.
const usd = (n: number) => `${n < 0 ? "-" : ""}$${fmt(Math.abs(n))}`;

const HORIZON_LABEL: Record<string, string> = { "1d": "Dzienny", "1m": "Miesieczny" };

// Sekcja "ryzyko": ile realnie mozesz stracic. VaR/CVaR (metoda historyczna)
// + stress test (odtworzenie krachow) dla wspolnie wybranego portfela + okno
// estymacji.
export function RiskReport() {
  const { selectedId } = usePortfoliosContext();
  const [window, setWindow] = useState<RiskWindow>("2y");
  const [risk, setRisk] = useState<PortfolioRiskReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedId === null) return;
    let aktualne = true;
    setLoading(true);
    setError(null);

    getPortfolioRisk(selectedId, window)
      .then((r) => aktualne && setRisk(r))
      .catch((e) => {
        if (aktualne) {
          setError(e.message ?? "Blad pobierania");
          setRisk(null);
        }
      })
      .finally(() => aktualne && setLoading(false));

    return () => {
      aktualne = false;
    };
  }, [selectedId, window]);

  const daily = risk?.var.filter((v) => v.horizon === "1d") ?? [];
  const monthly = risk?.var.filter((v) => v.horizon === "1m") ?? [];

  return (
    <div>
      <TerminalWindow title={`~/risk${risk ? `/${risk.name}` : ""}`}>
        {/* Sterowanie: okno estymacji VaR (wybor portfela jest wspolny, na gorze) */}
        <div className="mb-5 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
              okno:
            </span>
            <div className="flex gap-1">
              {RISK_WINDOWS.map((w) => (
                <button
                  key={w}
                  onClick={() => setWindow(w)}
                  className={`cyber-chamfer-sm border px-3 py-1.5 font-mono text-xs uppercase tracking-wider transition-all ${
                    w === window
                      ? "border-accent bg-accent/10 text-accent shadow-glow"
                      : "border-border text-muted-foreground hover:border-accent hover:text-accent"
                  }`}
                >
                  {w}
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="mb-5 max-w-2xl font-mono text-xs leading-relaxed text-muted-foreground">
          <span className="text-accent">$</span> ile realnie mozesz stracic. VaR to
          percentyl <span className="text-foreground">realnych</span> zwrotow (nie prognoza),
          CVaR mowi jak gleboki jest ogon, a stress test odtwarza prawdziwe krachy na
          Twoim dzisiejszym portfelu.
        </p>

        {error ? (
          <StatusPanel variant="error">
            <p className="mb-1 uppercase tracking-[0.2em]">// signal lost</p>
            <p className="text-foreground">{error}</p>
          </StatusPanel>
        ) : loading && !risk ? (
          <p className="font-mono text-sm text-accent">
            <span className="cursor-blink">&gt; liczenie ryzyka</span>
          </p>
        ) : risk && risk.id === selectedId ? (
          <div className={loading ? "opacity-50 transition-opacity" : ""}>
            {/* Ostrzezenie o oknie hossy - VaR uczony na spokojnym rynku zaniza ryzyko */}
            {risk.warning && (
              <div className="cyber-chamfer-sm mb-5 border border-[#ffcc00]/50 bg-[#ffcc00]/5 px-4 py-3">
                <p className="font-mono text-xs leading-relaxed text-[#ffcc00]">
                  ⚠ {risk.warning}
                </p>
              </div>
            )}

            <p className="mb-4 font-mono text-xs text-muted-foreground">
              Wartosc portfela:{" "}
              <span className="font-bold text-foreground">{usd(risk.portfolio_value)}</span>
              {" · "}
              VaR liczony z {risk.n_days} dni ({risk.window})
            </p>

            {/* VaR/CVaR - dwa horyzonty, kazdy dla 95% i 99% */}
            <VarGroup title="Strata dzienna (VaR)" measures={daily} />
            <VarGroup title="Strata miesieczna (VaR, ~21 sesji)" measures={monthly} />

            {/* STRESS TEST - odtworzenie krachow z jawnym pokryciem */}
            <div className="mt-6 border-t border-border pt-5">
              <p className="mb-3 font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
                Stress test — gdyby krach powtorzyl sie dzis
              </p>
              <div className="space-y-3">
                {risk.stress.map((s) => (
                  <StressRow key={s.key} scenario={s} value={risk.portfolio_value} />
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </TerminalWindow>
    </div>
  );
}

// Grupa kafelkow VaR/CVaR dla jednego horyzontu (95% i 99% obok siebie).
function VarGroup({ title, measures }: { title: string; measures: VarMeasure[] }) {
  if (measures.length === 0) return null;
  return (
    <div className="mb-4">
      <p className="mb-2 font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
        {title}
      </p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {measures.map((m) => (
          <StatTile
            key={m.confidence}
            label={`pewnosc ${(m.confidence * 100).toFixed(0)}%`}
            value={usd(m.var_abs)}
            className="text-destructive"
            hint={`${m.var_pct.toFixed(1)}% · gdy gorzej (CVaR): ${usd(m.cvar_abs)}`}
          />
        ))}
      </div>
    </div>
  );
}

// Jeden scenariusz stress: pasek proporcjonalny do straty + jawne pokrycie
// (ile spolek policzono z realnych danych, ile przez proxy beta x indeks).
function StressRow({ scenario, value }: { scenario: StressScenario; value: number }) {
  const szer = Math.min(Math.abs(scenario.shock_pct), 100);
  const nReal = scenario.coverage_real.length;
  const nProxy = scenario.coverage_proxy.length;
  const total = nReal + nProxy;

  return (
    <div className="cyber-chamfer-sm border border-border bg-[#12121a] px-4 py-3">
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <span className="font-mono text-sm text-foreground">{scenario.label}</span>
        <span className="font-display text-lg font-bold text-destructive">
          {scenario.shock_pct.toFixed(1)}% · {usd(scenario.pnl_abs)}
        </span>
      </div>
      <div className="mb-2 h-1.5 w-full overflow-hidden rounded bg-border">
        <div className="h-full bg-destructive" style={{ width: `${szer}%` }} />
      </div>
      <p className="font-mono text-xs text-muted-foreground">
        Pokrycie: {nReal} z {total} spolek z realnych danych z krachu
        {nProxy > 0 && (
          <>
            {" · "}
            {nProxy} przez bete (nie istnialy wtedy):{" "}
            <span className="text-[#ffcc00]">{scenario.coverage_proxy.join(", ")}</span>
          </>
        )}
      </p>
    </div>
  );
}
