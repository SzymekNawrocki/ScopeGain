"use client";

import { useEffect, useState } from "react";
import {
  getStockHistory,
  getStockMetrics,
  getStockProfile,
  getStockVerdict,
  PERIODS,
  Period,
  StockHistory,
  StockMetrics,
  StockProfile,
  StockVerdict,
} from "../lib/api";
import { PriceChart } from "./PriceChart";
import { SearchBox } from "./SearchBox";
import { StockProfilePanel } from "./StockProfilePanel";
import { TerminalWindow } from "./ui/TerminalWindow";
import { StatTile } from "./ui/StatTile";
import { StatusPanel } from "./ui/StatusPanel";
import { VerdictFindings } from "./ui/VerdictFindings";
import { pnlColor, withSign } from "../lib/format";

// Sekcja "market scope": szukasz spolki -> apka mowi, czym ona jest, czym
// ryzykujesz i jak sie zachowywala. Ten komponent tylko ORKIESTRUJE (pobiera
// i rozdaje), a maluja: SearchBox, StockProfilePanel, VerdictFindings,
// PriceChart.
export function MarketScope() {
  const [ticker, setTicker] = useState("AAPL"); // aktywnie ogladana spolka
  const [period, setPeriod] = useState<Period>("6mo");

  const [data, setData] = useState<StockHistory | null>(null);
  const [metrics, setMetrics] = useState<StockMetrics | null>(null);
  const [profile, setProfile] = useState<StockProfile | null>(null);
  const [verdict, setVerdict] = useState<StockVerdict | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Cztery niezalezne strzaly - kazdy moze dojsc w innym tempie i kazdy moze
  // zawiesc osobno. Wykres jest krytyczny (jego blad widac), profil i werdykt
  // sa dodatkiem: gdy zrodlo odmowi fundamentow, reszta ma dzialac dalej.
  useEffect(() => {
    let aktualne = true; // straznik: ignoruj odpowiedz starego zapytania
    setLoading(true);
    setError(null);

    getStockHistory(ticker, period)
      .then((h) => aktualne && setData(h))
      .catch((e) => {
        if (aktualne) {
          setError(e.message ?? "Blad pobierania");
          setData(null);
        }
      })
      .finally(() => aktualne && setLoading(false));

    getStockMetrics(ticker, period)
      .then((m) => aktualne && setMetrics(m))
      .catch(() => aktualne && setMetrics(null));

    getStockProfile(ticker)
      .then((p) => aktualne && setProfile(p))
      .catch(() => aktualne && setProfile(null));

    getStockVerdict(ticker, period)
      .then((v) => aktualne && setVerdict(v))
      .catch(() => aktualne && setVerdict(null));

    return () => {
      aktualne = false; // odpowiedz przyjdzie za pozno -> odrzuc ja
    };
  }, [ticker, period]);

  const swiezyProfil = profile && profile.ticker === ticker;
  const swiezyWerdykt = verdict && verdict.ticker === ticker && verdict.period === period;

  return (
    <div className="mb-12">
      <TerminalWindow title={ticker}>
        {/* Sterowanie: wyszukiwarka + zakres */}
        <div className="mb-5 flex flex-wrap items-center gap-4">
          <SearchBox value={ticker} onPick={setTicker} />

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

        {/* PROFIL - czym ta spolka jest (przed liczbami) */}
        {swiezyProfil && <StockProfilePanel profile={profile} />}

        {/* WERDYKT RYZYKA - wniosek najpierw, jak w reszcie apki.
            To NIE porada zakupu (ADR-0001): etykieta mowi o ryzyku, a
            zastrzezenie i braki danych ida razem z werdyktem. */}
        {swiezyWerdykt && (
          <VerdictFindings
            title={`Ryzyko — ${ticker} (${period})`}
            grade={verdict.grade}
            gradeLabel={verdict.grade_label}
            findings={verdict.findings}
            caveat={verdict.caveat}
            dataGaps={verdict.data_gaps}
          />
        )}

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

        {/* Panel metryk quant: zwrot, ryzyko, ja vs rynek. Kazda liczba
            tlumaczy sama siebie przez dymek (term=...). */}
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
              term="zmiennosc"
            />
            <StatTile
              label="Max drawdown"
              value={`${metrics.max_drawdown_pct.toFixed(2)}%`}
              className="text-destructive"
              term="drawdown"
            />
            <StatTile
              label={`vs ${metrics.benchmark.ticker}`}
              value={metrics.alpha_pct != null ? `${withSign(metrics.alpha_pct)}%` : "—"}
              className={pnlColor(metrics.alpha_pct)}
              term="alpha"
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
            <p className="mb-1 uppercase tracking-[0.2em]">{"// signal lost"}</p>
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
