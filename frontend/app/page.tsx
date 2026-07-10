"use client";

import { useCallback, useEffect, useState } from "react";
import { getPortfolios, Portfolio } from "./lib/api";
import { PortfolioCard } from "./components/PortfolioCard";
import { MarketScope } from "./components/MarketScope";
import { PortfolioVsMarket } from "./components/PortfolioVsMarket";
import { NewPortfolioForm } from "./components/NewPortfolioForm";
import { Nav } from "./components/Nav";

// Wspolny naglowek sekcji w stylu terminala (znacznik $ + komenda).
function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-4 font-mono text-xs uppercase tracking-[0.3em] text-accent-tertiary">
      <span className="text-accent">$</span> {children}
    </p>
  );
}

export default function Dashboard() {
  // Trzy stany zycia danych: ladowanie -> (sukces | blad).
  const [portfolios, setPortfolios] = useState<Portfolio[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // reload = jedno zrodlo prawdy: pobiera liste portfeli. Kazda mutacja
  // (utworz/dodaj/usun) wola to po sobie, wiec UI zawsze widzi swiezy stan.
  const reload = useCallback(() => {
    getPortfolios()
      .then(setPortfolios)
      .catch((e) => setError(e.message ?? "Brak polaczenia z API"));
  }, []);

  // Uruchom raz, gdy komponent wejdzie. fetch leci z PRZEGLADARKI -> bez CORS
  // na backendzie przegladarka tu zablokuje.
  useEffect(() => {
    reload();
  }, [reload]);

  return (
    <>
      <Nav />
      <main id="top" className="mx-auto max-w-7xl px-6 py-12">
        {/* NAGLOWEK */}
        <header className="mb-12">
          <p className="mb-3 font-mono text-xs uppercase tracking-[0.3em] text-accent-tertiary">
            <span className="text-accent">$</span> ./scopegain --connect
          </p>
          <h1 className="glitch font-display text-6xl font-black uppercase tracking-widest text-foreground sm:text-7xl">
            ScopeGain
          </h1>
          <p className="mt-4 max-w-xl font-mono text-sm leading-relaxed text-muted-foreground">
            Terminal analizy portfela. Dane na zywo z lokalnego API.
            <span className="cursor-blink" />
          </p>
        </header>

        {/* PORTFELE - Twoje holdingi + P&L (najpierw, bo to Twoje dane) */}
        <section id="portfele" className="mb-16 scroll-mt-20">
          <SectionLabel>./portfolios --list</SectionLabel>
          <NewPortfolioForm onChanged={reload} />

          {error ? (
            <ErrorPanel message={error} />
          ) : portfolios === null ? (
            <LoadingPanel />
          ) : portfolios.length === 0 ? (
            <EmptyPanel />
          ) : (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {portfolios.map((p) => (
                <PortfolioCard key={p.id} portfolio={p} onChanged={reload} />
              ))}
            </div>
          )}
        </section>

        {/* RYNEK - research dowolnej spolki (swiece + metryki) */}
        <section id="rynek" className="scroll-mt-20">
          <SectionLabel>./market --scope</SectionLabel>
          <MarketScope />
        </section>

        {/* ANALIZA - werdykt, backtest vs rynek, ryzyko, korelacje */}
        <section id="analiza" className="scroll-mt-20">
          <SectionLabel>./portfolio --analyze</SectionLabel>
          <PortfolioVsMarket portfolios={portfolios ?? []} />
        </section>
      </main>
    </>
  );
}

function LoadingPanel() {
  return (
    <div className="cyber-chamfer border border-border bg-card p-8 font-mono text-sm text-accent">
      <span className="cursor-blink">&gt; nawiazywanie polaczenia z API</span>
    </div>
  );
}

function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="cyber-chamfer border-2 border-destructive bg-card p-8 font-mono text-sm text-destructive shadow-[0_0_20px_#ff336640]">
      <p className="mb-2 uppercase tracking-[0.2em]">// signal lost</p>
      <p className="text-foreground">
        Nie udalo sie pobrac danych: <span className="text-destructive">{message}</span>
      </p>
      <p className="mt-3 text-xs text-muted-foreground">
        Sprawdz, czy backend chodzi na :8000 i ma wlaczone CORS.
      </p>
    </div>
  );
}

function EmptyPanel() {
  return (
    <div className="cyber-chamfer border border-border bg-card p-8 font-mono text-sm text-muted-foreground">
      <span className="text-accent">$</span> brak portfeli — kliknij „+ nowy portfel" powyzej, zeby zaczac.
    </div>
  );
}
