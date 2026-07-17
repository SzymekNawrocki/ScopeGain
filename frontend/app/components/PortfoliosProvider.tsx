"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getPortfolios, Portfolio } from "../lib/api";

// Jedyne miejsce w apce, ktore trzyma stan listy portfeli ORAZ ktory z nich
// jest aktualnie wybrany do analizy. Wczesniej kazda sekcja analityczna
// (analiza / ryzyko / realna / zachowanie / rebalans) trzymala WLASNY selectedId
// i rysowala WLASNY rzad przyciskow wyboru - przy kilku portfelach user widzial
// ten sam wybor powtorzony 5 razy, a wybor w jednej sekcji nie synchronizowal
// sie z reszta. Teraz wybor jest jeden i wspolny: jeden PortfolioSelector na
// gorze zakladki "Moj portfel" steruje wszystkimi sekcjami naraz.
type Ctx = {
  portfolios: Portfolio[] | null;
  selectedId: number | null;
  setSelectedId: (id: number) => void;
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
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // reload = jedno zrodlo prawdy: pobiera liste portfeli. Kazda mutacja
  // (utworz/dodaj/usun) wola to po sobie, wiec caly UI zawsze widzi swiezy stan.
  const reload = useCallback(() => {
    getPortfolios()
      .then((list) => {
        setPortfolios(list);
        // Utrzymaj wybor wazny: gdy nic jeszcze nie wybrano albo wybrany portfel
        // zniknal (usuniety), przeskocz na pierwszy z listy. Gdy wybrany dalej
        // istnieje - nie ruszaj go (nie chcemy resetowac po dodaniu pozycji).
        setSelectedId((cur) =>
          cur !== null && list.some((p) => p.id === cur) ? cur : list[0]?.id ?? null,
        );
      })
      .catch((e) => setError(e.message ?? "Brak polaczenia z API"));
  }, []);

  // Uruchom raz, gdy komponent wejdzie. fetch leci z PRZEGLADARKI -> bez CORS
  // na backendzie przegladarka tu zablokuje.
  useEffect(() => {
    reload();
  }, [reload]);

  return (
    <PortfoliosContext.Provider value={{ portfolios, selectedId, setSelectedId, error, reload }}>
      {children}
    </PortfoliosContext.Provider>
  );
}
