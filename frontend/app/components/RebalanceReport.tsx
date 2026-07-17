"use client";

import { useEffect, useState } from "react";
import {
  getPortfolioRebalance,
  RebalanceLeg,
  RebalancePlan,
} from "../lib/api";
import { usePortfoliosContext } from "./PortfoliosProvider";
import { TerminalWindow } from "./ui/TerminalWindow";
import { StatTile } from "./ui/StatTile";
import { StatusPanel } from "./ui/StatusPanel";
import { fmt } from "../lib/format";

const usd = (n: number) => `${n < 0 ? "-" : ""}$${fmt(Math.abs(n))}`;

// Sekcja "rebalans" (12c): jak daleko portfel od rownych wag + ile kosztuje
// domkniecie rozjazdu. NIE porada (ADR-0001) - punkt odniesienia + trade-off.
export function RebalanceReport() {
  const { selectedId } = usePortfoliosContext();
  const [plan, setPlan] = useState<RebalancePlan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedId === null) return;
    let aktualne = true;
    setLoading(true);
    setError(null);
    getPortfolioRebalance(selectedId)
      .then((p) => aktualne && setPlan(p))
      .catch((e) => {
        if (aktualne) {
          setError(e.message ?? "Blad pobierania");
          setPlan(null);
        }
      })
      .finally(() => aktualne && setLoading(false));
    return () => {
      aktualne = false;
    };
  }, [selectedId]);

  return (
    <div>
      <TerminalWindow title={`Rebalans${plan ? ` — ${plan.name}` : ""}`}>
        <p className="mb-5 max-w-2xl font-mono text-xs leading-relaxed text-muted-foreground">
          <span className="text-accent">$</span> punkt odniesienia:{" "}
          <span className="text-foreground">rowne wagi (1/N)</span> jako neutralna miara
          koncentracji. To NIE porada „kup/sprzedaz" — pokazuje rozjazd i ile kosztowaloby
          jego domkniecie.
        </p>

        {error ? (
          <StatusPanel variant="error">
            <p className="text-foreground">{error}</p>
          </StatusPanel>
        ) : loading && !plan ? (
          <p className="font-mono text-sm text-accent">
            <span className="cursor-blink">&gt; liczenie rebalansu</span>
          </p>
        ) : plan && plan.id === selectedId ? (
          <div className={loading ? "opacity-50 transition-opacity" : ""}>
            <p className="mb-4 font-mono text-xs text-muted-foreground">
              Wartosc portfela:{" "}
              <span className="font-bold text-foreground">{usd(plan.total_value)}</span>
            </p>

            <div className="space-y-2">
              {plan.legs.map((leg) => (
                <RebalanceRow key={leg.ticker} leg={leg} />
              ))}
            </div>

            {/* Koszt domkniecia rozjazdu - rebalansing nie jest darmowy */}
            <div className="mt-6 border-t border-border pt-5">
              <p className="mb-3 font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
                Ile kosztowaloby wyrownanie do rownych wag
              </p>
              <div className="grid grid-cols-3 gap-3">
                <StatTile label="Prowizja" value={usd(plan.cost.commission)} className="text-destructive" />
                <StatTile label="Podatek Belka" value={usd(plan.cost.tax_belka)} className="text-destructive" />
                <StatTile label="Koszt razem" value={usd(plan.cost.total_cost)} className="text-destructive" />
              </div>
              <p className="mt-3 font-mono text-xs italic text-muted-foreground">
                * rebalansing nie jest darmowy — prowizja od kazdego ruchu, a przycinanie
                zyskownej pozycji uruchamia Belke (19% od zrealizowanego zysku). Rozwaz, czy
                korzysc z dywersyfikacji przewyzsza ten koszt.
              </p>
            </div>
          </div>
        ) : null}
      </TerminalWindow>
    </div>
  );
}

// Jeden wiersz: obecna vs docelowa waga (pasek) + dryf + sugestia ruchu.
function RebalanceRow({ leg }: { leg: RebalanceLeg }) {
  const over = leg.drift_pp > 0;
  const balanced = Math.abs(leg.drift_pp) < 0.5;
  return (
    <div className="cyber-chamfer-sm border border-border bg-[#12121a] px-4 py-3">
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <span className="font-mono text-sm font-bold text-foreground">{leg.ticker}</span>
        <span className="font-mono text-xs text-muted-foreground">
          {leg.current_weight_pct.toFixed(1)}% → cel {leg.target_weight_pct.toFixed(1)}%
        </span>
      </div>
      {/* Pasek: obecna waga, znacznik celu */}
      <div className="relative mb-2 h-1.5 w-full overflow-hidden rounded bg-border">
        <div
          className={`h-full ${over ? "bg-destructive" : "bg-accent"}`}
          style={{ width: `${Math.min(leg.current_weight_pct, 100)}%` }}
        />
        <div
          className="absolute top-[-2px] h-[10px] w-0.5 bg-foreground"
          style={{ left: `${Math.min(leg.target_weight_pct, 100)}%` }}
          title="cel"
        />
      </div>
      <p className="font-mono text-xs">
        {balanced ? (
          <span className="text-accent">na celu — bez ruchu</span>
        ) : over ? (
          <span className="text-muted-foreground">
            przewazona o {leg.drift_pp.toFixed(1)} pp —{" "}
            <span className="text-destructive">przytnij ~{usd(Math.abs(leg.trade_value))}</span>
          </span>
        ) : (
          <span className="text-muted-foreground">
            niedowazona o {Math.abs(leg.drift_pp).toFixed(1)} pp —{" "}
            <span className="text-accent">dokup ~{usd(leg.trade_value)}</span>
          </span>
        )}
      </p>
    </div>
  );
}
