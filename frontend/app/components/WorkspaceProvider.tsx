"use client";

import { createContext, useContext, useState } from "react";

// Powloka apki dzieli sie na tryby-zadania zamiast jednego dlugiego scrolla.
// Wybor trybu jest wspolny miedzy paskiem nawigacji (przelacza) a trescia
// (renderuje aktywny tryb), wiec zyje w kontekscie ponad oboma. Tryby ida za
// petla decyzyjna: odkryj -> rozwazam (temat + teza) -> mam (portfel).
//  - "odkrywaj" -> przegladaj po branzy/ETF + szukaj po nazwie + podglad spolki
//                  (wejscie dla kogos, kto nie zna symbolu).
//  - "tematy"   -> koszyki kuratorowane: tezy, uniewaznienia, rozliczenie typow.
//  - "portfel"  -> Twoje pozycje i cala analiza portfela w jednym miejscu.
export type WorkspaceTab = "odkrywaj" | "tematy" | "portfel";

type Ctx = { tab: WorkspaceTab; setTab: (t: WorkspaceTab) => void };

const WorkspaceContext = createContext<Ctx | null>(null);

export function useWorkspace(): Ctx {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error("useWorkspace musi byc uzyte wewnatrz WorkspaceProvider");
  return ctx;
}

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  // Domyslnie "odkrywaj": nowy uzytkownik trafia na przegladanie/szukanie,
  // nie na pusty ekran portfela.
  const [tab, setTab] = useState<WorkspaceTab>("odkrywaj");
  return (
    <WorkspaceContext.Provider value={{ tab, setTab }}>{children}</WorkspaceContext.Provider>
  );
}
