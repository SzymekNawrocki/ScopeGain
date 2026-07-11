"use client";

import { useAuth } from "./AuthProvider";

// Prawy rog paska nawigacji: kto jest zalogowany + przycisk wyloguj.
// Gdy nikt nie zalogowany (albo jeszcze sprawdzamy), nie pokazujemy nic -
// pasek zostaje czysty na ekranie logowania.
export function AuthStatus() {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="flex items-center gap-3">
      <span className="hidden font-mono text-xs text-muted-foreground sm:inline">
        <span className="text-accent">●</span> {user.email}
      </span>
      <button
        onClick={() => logout()}
        className="cyber-chamfer-sm border border-border px-3 py-1.5 font-mono text-xs uppercase tracking-wider text-muted-foreground transition-all hover:border-destructive hover:text-destructive"
      >
        wyloguj
      </button>
    </div>
  );
}
