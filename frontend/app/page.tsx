"use client";

import { useEffect, useState } from "react";
import { getPortfolios, Portfolio } from "./lib/api";
import { PortfolioCard } from "./components/PortfolioCard";
import { MarketScope } from "./components/MarketScope";

export default function Dashboard() {
  // Trzy stany zycia danych: ladowanie -> (sukces | blad).
  const [portfolios, setPortfolios] = useState<Portfolio[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // useEffect z pusta lista zaleznosci = uruchom raz, gdy komponent wejdzie.
  // fetch leci z PRZEGLADARKI -> bez CORS na backendzie przegladarka tu zablokuje.
  useEffect(() => {
    getPortfolios()
      .then(setPortfolios)
      .catch((e) => setError(e.message ?? "Brak polaczenia z API"));
  }, []);

  return (
    <main className="mx-auto max-w-7xl px-6 py-16">
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

      {/* WYKRES KURSU - swiece z /stock/{ticker}/history */}
      <MarketScope />

      {/* PORTFELE */}
      <p className="mb-4 font-mono text-xs uppercase tracking-[0.3em] text-accent-tertiary">
        <span className="text-accent">$</span> ./portfolios --list
      </p>

      {/* STANY */}
      {error ? (
        <ErrorPanel message={error} />
      ) : portfolios === null ? (
        <LoadingPanel />
      ) : portfolios.length === 0 ? (
        <EmptyPanel />
      ) : (
        <section className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {portfolios.map((p) => (
            <PortfolioCard key={p.id} portfolio={p} />
          ))}
        </section>
      )}
    </main>
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
      <span className="text-accent">$</span> brak portfeli w bazie — utworz pierwszy przez API.
    </div>
  );
}
