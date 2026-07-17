"use client";

import { useEffect, useState } from "react";
import {
  getPortfolioRealPerformance,
  RealPerformance,
} from "../lib/api";
import { PerformanceChart } from "./PerformanceChart";
import { usePortfoliosContext } from "./PortfoliosProvider";
import { TerminalWindow } from "./ui/TerminalWindow";
import { StatusPanel } from "./ui/StatusPanel";
import { pnlColor, withSign } from "../lib/format";

// Sekcja "realna sciezka": TWR z logu transakcji zamiast hipotezy dzisiejszych
// wag. Gdy log nie domyka sie z pozycjami - mowi o tym wprost (rekoncyliacja).
export function RealPerformanceReport() {
  const { selectedId } = usePortfoliosContext();
  const [data, setData] = useState<RealPerformance | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedId === null) return;
    let aktualne = true;
    setLoading(true);
    setError(null);
    getPortfolioRealPerformance(selectedId)
      .then((d) => aktualne && setData(d))
      .catch((e) => {
        if (aktualne) {
          setError(e.message ?? "Blad pobierania");
          setData(null);
        }
      })
      .finally(() => aktualne && setLoading(false));
    return () => {
      aktualne = false;
    };
  }, [selectedId]);

  const rec = data?.reconciliation;

  return (
    <div>
      <TerminalWindow title={`Realna ścieżka${data ? ` — ${data.name}` : ""}`}>
        <p className="mb-5 max-w-2xl font-mono text-xs leading-relaxed text-muted-foreground">
          <span className="text-accent">$</span> to co <span className="text-foreground">NAPRAWDE</span>{" "}
          trzymales dzien po dniu, z Twojego logu transakcji — metoda TWR (dokupienia
          nie licza sie jak zysk). W przeciwienstwie do backtestu w „analizie" ta krzywa
          nie zaklada dzisiejszych wag.
        </p>

        {error ? (
          <StatusPanel variant="error">
            <p className="text-foreground">{error}</p>
          </StatusPanel>
        ) : loading && !data ? (
          <p className="font-mono text-sm text-accent">
            <span className="cursor-blink">&gt; odtwarzanie sciezki</span>
          </p>
        ) : data && data.id === selectedId ? (
          data.available ? (
            <div className={loading ? "opacity-50 transition-opacity" : ""}>
              {/* Rekoncyliacja: log vs obecne pozycje */}
              {rec && !rec.reconciled && (
                <div className="cyber-chamfer-sm mb-4 border border-[#ffcc00]/50 bg-[#ffcc00]/5 px-4 py-3">
                  <p className="mb-1 font-mono text-xs font-bold text-[#ffcc00]">
                    ⚠ Log nie domyka sie z obecnymi pozycjami
                  </p>
                  <p className="font-mono text-xs leading-relaxed text-muted-foreground">
                    Sciezka liczona z logu, ale netto transakcji rozni sie od pozycji —
                    dodaj brakujace transakcje, zeby byla pelna:
                  </p>
                  <ul className="mt-1.5 font-mono text-xs text-[#ffcc00]">
                    {rec.discrepancies.map((d) => (
                      <li key={d.ticker}>
                        {d.ticker}: log {d.log}, pozycje {d.positions} (roznica {withSign(d.diff)})
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Podsumowanie zwrotow */}
              <div className="mb-4 flex flex-wrap items-center gap-x-8 gap-y-2 font-mono text-sm">
                <span className="flex items-center gap-2">
                  <span className="inline-block h-0.5 w-5 bg-accent" />
                  <span className="text-muted-foreground">realny portfel</span>
                  <span className={`font-bold ${pnlColor(data.portfolio_return_pct ?? 0)}`}>
                    {withSign(data.portfolio_return_pct ?? 0)}%
                  </span>
                </span>
                <span className="flex items-center gap-2">
                  <span className="inline-block h-0.5 w-5 bg-accent-tertiary" />
                  <span className="text-muted-foreground">{data.benchmark_ticker}</span>
                  <span className={`font-bold ${pnlColor(data.benchmark_return_pct ?? 0)}`}>
                    {withSign(data.benchmark_return_pct ?? 0)}%
                  </span>
                </span>
                <span className="flex items-center gap-2">
                  <span className="text-sm uppercase tracking-[0.15em] text-muted-foreground">alpha</span>
                  <span className={`font-display text-lg font-bold ${pnlColor(data.alpha_pct ?? 0)}`}>
                    {withSign(data.alpha_pct ?? 0)}%
                  </span>
                </span>
              </div>

              {rec?.reconciled && (
                <p className="mb-3 font-mono text-xs text-accent">
                  ✓ log zgadza sie z pozycjami — sciezka kompletna
                </p>
              )}

              {data.series && (
                <PerformanceChart series={data.series} benchmarkLabel={data.benchmark_ticker ?? "SPY"} />
              )}

              <p className="mt-3 font-mono text-xs italic text-muted-foreground">
                * {data.method}; od {data.start_date} (pierwsza transakcja).
              </p>
            </div>
          ) : (
            <p className="font-mono text-sm text-muted-foreground">
              <span className="text-accent">$</span> {data.reason}
            </p>
          )
        ) : null}
      </TerminalWindow>
    </div>
  );
}
