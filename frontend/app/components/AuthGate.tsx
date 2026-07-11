"use client";

import { useAuth } from "./AuthProvider";
import { AuthPanel } from "./AuthPanel";
import { StatusPanel } from "./ui/StatusPanel";

// Bramka: decyduje, co user w ogole zobaczy pod naglowkiem.
//  - loading  -> krotki komunikat (czekamy na /auth/me),
//  - brak usera -> ekran logowania/rejestracji (children sie NIE renderuja,
//    wiec dashboard nawet nie odpytuje chronionego API),
//  - zalogowany -> wlasciwa tresc (children).
export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <StatusPanel variant="loading">
        <span className="cursor-blink">&gt; sprawdzam sesje</span>
      </StatusPanel>
    );
  }

  if (!user) {
    return <AuthPanel />;
  }

  return <>{children}</>;
}
