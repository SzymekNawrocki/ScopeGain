"use client";

import { PortfolioCard } from "./PortfolioCard";
import { NewPortfolioForm } from "./NewPortfolioForm";
import { StatusPanel } from "./ui/StatusPanel";
import { usePortfoliosContext } from "./PortfoliosProvider";

// Tresc sekcji "portfele": formularz + lista kart. Czyta stan z
// PortfoliosProvider (wspolny z sekcja "analiza").
export function PortfoliosSection() {
  const { portfolios, error, reload } = usePortfoliosContext();

  return (
    <>
      <NewPortfolioForm onChanged={reload} />

      {error ? (
        <StatusPanel variant="error">
          <p className="mb-2 uppercase tracking-[0.2em]">// signal lost</p>
          <p className="text-foreground">
            Nie udalo sie pobrac danych: <span className="text-destructive">{error}</span>
          </p>
          <p className="mt-3 text-xs text-muted-foreground">
            Sprawdz, czy backend chodzi na :8000 i ma wlaczone CORS.
          </p>
        </StatusPanel>
      ) : portfolios === null ? (
        <StatusPanel variant="loading">
          <span className="cursor-blink">&gt; nawiazywanie polaczenia z API</span>
        </StatusPanel>
      ) : portfolios.length === 0 ? (
        <StatusPanel variant="empty">
          <p>
            <span className="text-accent">$</span> brak portfeli — kliknij{" "}
            <span className="text-accent">„+ nowy portfel"</span> powyzej, zeby
            zaczac.
          </p>
          <p className="mt-2 text-xs">
            Potem w karcie portfela dodasz pierwsza pozycje (ticker + liczba
            sztuk + cena), a analiza policzy sie sama.
          </p>
        </StatusPanel>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {portfolios.map((p) => (
            <PortfolioCard key={p.id} portfolio={p} onChanged={reload} />
          ))}
        </div>
      )}
    </>
  );
}
