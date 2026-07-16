"use client";

import { useEffect, useState } from "react";
import {
  deletePortfolio,
  deletePosition,
  Portfolio,
  PortfolioValuation,
  costBasis,
  getPortfolioValuation,
} from "../lib/api";
import { AddPositionForm } from "./AddPositionForm";
import { TerminalWindow } from "./ui/TerminalWindow";
import { fmt, pnlColor, pnlSign } from "../lib/format";

export function PortfolioCard({
  portfolio,
  onChanged,
}: {
  portfolio: Portfolio;
  onChanged: () => void;
}) {
  const [val, setVal] = useState<PortfolioValuation | null>(null);
  const [confirmDel, setConfirmDel] = useState(false);

  // Podpis pozycji: zmienia sie, gdy cos dodasz/usuniesz -> wycena sie przelicza.
  const sig = portfolio.positions.map((p) => `${p.id}:${p.quantity}:${p.buy_price}`).join(",");

  useEffect(() => {
    let aktualne = true;
    setVal(null);
    getPortfolioValuation(portfolio.id)
      .then((v) => aktualne && setVal(v))
      .catch(() => {});
    return () => {
      aktualne = false;
    };
  }, [portfolio.id, sig]);

  const wyceny = new Map(val?.positions.map((p) => [p.id, p]) ?? []);

  async function usunPozycje(positionId: number) {
    try {
      await deletePosition(portfolio.id, positionId);
      onChanged();
    } catch {
      /* ciche - lista i tak sie odswiezy przy nastepnej akcji */
    }
  }

  async function usunPortfel() {
    try {
      await deletePortfolio(portfolio.id);
      onChanged();
    } catch {
      setConfirmDel(false);
    }
  }

  return (
    <article className="group relative">
      <span className="pointer-events-none absolute left-0 top-0 h-3 w-3 border-l-2 border-t-2 border-accent" />
      <span className="pointer-events-none absolute right-0 top-0 h-3 w-3 border-r-2 border-t-2 border-accent" />
      <span className="pointer-events-none absolute bottom-0 left-0 h-3 w-3 border-b-2 border-l-2 border-accent" />
      <span className="pointer-events-none absolute bottom-0 right-0 h-3 w-3 border-b-2 border-r-2 border-accent" />

      <TerminalWindow
        className="transition-all duration-300 group-hover:border-accent group-hover:shadow-glow"
        title={`~/portfolios/${portfolio.id}`}
        actions={
          val && (
            <span className={`font-mono text-xs font-bold ${pnlColor(val.total_pnl_pct)}`}>
              {pnlSign(val.total_pnl_pct)}
              {fmt(Math.abs(val.total_pnl_pct))}%
            </span>
          )
        }
      >
        <div className="flex items-start justify-between gap-2">
          <h2 className="font-display text-xl font-bold uppercase tracking-wide text-foreground">
            {portfolio.name}
          </h2>
          {/* Usuwanie portfela: dwuklik (pierwszy pyta, drugi kasuje) */}
          {confirmDel ? (
            <div className="flex shrink-0 gap-1">
              <button
                onClick={usunPortfel}
                className="cyber-chamfer-sm border border-destructive px-2 py-1 font-mono text-xs uppercase text-destructive transition-all hover:bg-destructive hover:text-background"
              >
                na pewno?
              </button>
              <button
                onClick={() => setConfirmDel(false)}
                className="font-mono text-xs uppercase text-muted-foreground hover:text-foreground"
              >
                nie
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDel(true)}
              aria-label="Usun portfel"
              className="shrink-0 font-mono text-sm text-muted-foreground transition-colors hover:text-destructive"
            >
              usun
            </button>
          )}
        </div>

        {/* Pozycje */}
        <div className="mt-4 space-y-1">
          {portfolio.positions.length === 0 ? (
            <p className="font-mono text-sm text-muted-foreground">
              <span className="text-accent">$</span> brak pozycji — dodaj pierwsza nizej
            </p>
          ) : (
            <>
              <div className="grid grid-cols-[1fr_auto_auto_auto_1.25rem] gap-3 border-b border-border pb-1 font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
                <span>Ticker</span>
                <span className="text-right">Ilosc</span>
                <span className="text-right">Teraz</span>
                <span className="text-right">Zysk</span>
                <span />
              </div>
              {portfolio.positions.map((pos) => {
                const w = wyceny.get(pos.id);
                return (
                  <div
                    key={pos.id}
                    className="group/row grid grid-cols-[1fr_auto_auto_auto_1.25rem] items-center gap-3 py-1 font-mono text-sm"
                  >
                    <span className="font-bold text-accent-tertiary">{pos.ticker}</span>
                    <span className="text-right text-foreground">{fmt(pos.quantity)}</span>
                    <span className="text-right text-muted-foreground">
                      {w?.current_price != null ? fmt(w.current_price) : "···"}
                    </span>
                    <span className={`text-right font-bold ${pnlColor(w?.pnl_pct)}`}>
                      {w?.pnl_pct != null ? `${w.pnl_pct >= 0 ? "+" : ""}${fmt(w.pnl_pct)}%` : "···"}
                    </span>
                    <button
                      onClick={() => usunPozycje(pos.id)}
                      aria-label={`Usun ${pos.ticker}`}
                      className="text-right text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover/row:opacity-100"
                    >
                      ×
                    </button>
                  </div>
                );
              })}
            </>
          )}
        </div>

        {/* Dodawanie pozycji */}
        <AddPositionForm portfolioId={portfolio.id} onChanged={onChanged} />

        {/* Podsumowanie */}
        <footer className="mt-4 space-y-2 border-t border-border pt-3">
          <div className="flex items-baseline justify-between">
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
              Koszt wejscia
            </span>
            <span className="font-mono text-sm text-muted-foreground">
              ${fmt(val?.total_cost ?? costBasis(portfolio))}
            </span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
              Wartosc dzis
            </span>
            <span className="font-display text-lg font-bold text-accent">
              {val ? `$${fmt(val.total_value)}` : "···"}
            </span>
          </div>
          {val && (
            <div className="flex items-baseline justify-between">
              <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
                Zysk / strata (brutto)
              </span>
              <span className={`font-display text-lg font-bold ${pnlColor(val.total_pnl_abs)}`}>
                {val.total_pnl_abs >= 0 ? "+" : "−"}${fmt(Math.abs(val.total_pnl_abs))}
              </span>
            </div>
          )}
          {val && (
            <div className="flex items-baseline justify-between" title="Po prowizji maklerskiej (kupno + sprzedaz) i podatku Belka (19% od zysku)">
              <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
                Netto w kieszeni
              </span>
              <span className={`font-mono text-sm font-bold ${pnlColor(val.total_pnl_net_abs)}`}>
                {val.total_pnl_net_abs >= 0 ? "+" : "−"}${fmt(Math.abs(val.total_pnl_net_abs))}
                <span className="ml-1 text-muted-foreground">
                  ({val.total_pnl_net_pct >= 0 ? "+" : ""}{fmt(val.total_pnl_net_pct)}%)
                </span>
              </span>
            </div>
          )}
          {/* Przeliczenie na PLN (kurs NBP). Uproszczenie: kurs biezacy - poprawna
              Belka liczy sie po kursie z dnia przed kazda transakcja. */}
          {val?.total_value_pln != null && (
            <div
              className="flex items-baseline justify-between"
              title={`Kurs NBP ${val.fx_usd_pln} PLN/USD. Uproszczenie: kurs biezacy - realna Belka liczy sie po kursie z dnia przed kazda transakcja.`}
            >
              <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
                W PLN (netto)
              </span>
              <span className="font-mono text-sm text-muted-foreground">
                ≈ {fmt(val.total_value_pln)} zl
                {val.total_pnl_net_pln != null && (
                  <span className={`ml-1 font-bold ${pnlColor(val.total_pnl_net_pln)}`}>
                    ({val.total_pnl_net_pln >= 0 ? "+" : "−"}{fmt(Math.abs(val.total_pnl_net_pln))} zl)
                  </span>
                )}
              </span>
            </div>
          )}
        </footer>
      </TerminalWindow>
    </article>
  );
}
