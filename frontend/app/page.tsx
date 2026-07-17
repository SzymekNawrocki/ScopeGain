import { PortfoliosProvider } from "./components/PortfoliosProvider";
import { WorkspaceProvider } from "./components/WorkspaceProvider";
import { WorkspaceBody } from "./components/WorkspaceBody";
import { AuthProvider } from "./components/AuthProvider";
import { AuthGate } from "./components/AuthGate";
import { Nav } from "./components/Nav";
import { HowItWorks } from "./components/HowItWorks";

// Server Component: powloka strony (naglowek) nie ma stanu, wiec renderuje sie
// na serwerze. Interaktywne granice to providery kliencke:
//  - AuthProvider  obejmuje pasek I tresc (AuthStatus w pasku, AuthGate w tresci
//                  czytaja ten sam stan zalogowania),
//  - WorkspaceProvider trzyma aktywny tryb (Szukaj / Moj portfel) - musi objac
//                  Nav (przelacza) i WorkspaceBody (renderuje aktywny tryb),
//  - PortfoliosProvider trzyma liste portfeli i wspolny wybor portfela dla calej
//                  analizy w trybie "Moj portfel".
export default function Dashboard() {
  return (
    <AuthProvider>
      <WorkspaceProvider>
        <Nav />
        <main id="top" className="mx-auto max-w-7xl px-6 py-12">
          {/* NAGLOWEK */}
          <header className="mb-12">
            <h1 className="font-display text-6xl font-black uppercase tracking-widest text-foreground sm:text-7xl">
              ScopeGain
            </h1>
            <p className="mt-4 max-w-2xl font-mono text-base leading-relaxed text-muted-foreground">
              Twój dziennik inwestora: zapisujesz swoje decyzje, a apka pamięta je,
              uczciwie liczy Twój realny zysk i ryzyko — i nie zmyśla.
              <span className="cursor-blink" />
            </p>
          </header>

          {/* Brama: niezalogowany widzi ekran logowania; reszta (i chronione API)
              renderuje sie dopiero po zalogowaniu. */}
          <AuthGate>
            {/* Instrukcja dla nowego uzytkownika - widoczna na kazdej zakladce */}
            <HowItWorks />
            <PortfoliosProvider>
              <WorkspaceBody />
            </PortfoliosProvider>
          </AuthGate>
        </main>
      </WorkspaceProvider>
    </AuthProvider>
  );
}
