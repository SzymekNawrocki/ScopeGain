"use client";

import { AuthStatus } from "./AuthStatus";
import { useWorkspace, WorkspaceTab } from "./WorkspaceProvider";

// Przyklejony pasek nawigacji. Zamiast siedmiu kotwic do jednego dlugiego
// scrolla mamy TRYBY idace za petla decyzyjna: "Odkrywaj" (znajdz spolki),
// "Tematy" (rozwazam - tezy i rozliczenie), "Moj portfel" (mam - analiza).
// Aktywny tryb podswietla sie jak reszta akcentow w apce.
const TABS: [WorkspaceTab, string][] = [
  ["odkrywaj", "Odkrywaj"],
  ["tematy", "Tematy"],
  ["portfel", "Moj portfel"],
];

export function Nav() {
  const { tab, setTab } = useWorkspace();

  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-6 py-3">
        <button
          onClick={() => setTab("odkrywaj")}
          className="font-display text-lg font-black uppercase tracking-widest text-foreground"
        >
          Scope<span className="text-accent">Gain</span>
        </button>
        <div className="ml-auto flex items-center gap-4">
          <div className="flex gap-1">
            {TABS.map(([id, label]) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                aria-pressed={tab === id}
                className={`cyber-chamfer-sm border px-3 py-1.5 font-mono text-sm uppercase tracking-wider transition-all ${
                  tab === id
                    ? "border-accent bg-accent/10 text-accent shadow-glow"
                    : "border-transparent text-muted-foreground hover:border-accent hover:text-accent"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          {/* Kto zalogowany + wyloguj (klientowy, czyta AuthProvider) */}
          <AuthStatus />
        </div>
      </div>
    </nav>
  );
}
