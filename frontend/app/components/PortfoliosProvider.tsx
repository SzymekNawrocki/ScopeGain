"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getPortfolios, Portfolio } from "../lib/api";

// Jedyne miejsce w apce, ktore trzyma stan listy portfeli. "portfele" (karty +
// formularz) i "analiza" (portfel vs rynek) czytaja te sama liste, ale nie
// siedza obok siebie w layoucie (miedzy nimi jest sekcja "rynek") - Context
// pozwala im dzielic stan bez zmiany kolejnosci sekcji na stronie i bez
// zamieniania calego page.tsx w Client Component.
type Ctx = {
  portfolios: Portfolio[] | null;
  error: string | null;
  reload: () => void;
};

const PortfoliosContext = createContext<Ctx | null>(null);

export function usePortfoliosContext(): Ctx {
  const ctx = useContext(PortfoliosContext);
  if (!ctx) throw new Error("usePortfoliosContext musi byc uzyte wewnatrz PortfoliosProvider");
  return ctx;
}

export function PortfoliosProvider({ children }: { children: React.ReactNode }) {
  const [portfolios, setPortfolios] = useState<Portfolio[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // reload = jedno zrodlo prawdy: pobiera liste portfeli. Kazda mutacja
  // (utworz/dodaj/usun) wola to po sobie, wiec caly UI zawsze widzi swiezy stan.
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
    <PortfoliosContext.Provider value={{ portfolios, error, reload }}>
      {children}
    </PortfoliosContext.Provider>
  );
}
