import { PortfoliosProvider } from "./components/PortfoliosProvider";
import { WorkspaceProvider } from "./components/WorkspaceProvider";
import { WorkspaceBody } from "./components/WorkspaceBody";
import { AuthProvider } from "./components/AuthProvider";
import { AuthGate } from "./components/AuthGate";
import { Nav } from "./components/Nav";

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
            <p className="mb-3 font-mono text-sm uppercase tracking-[0.3em] text-accent-tertiary">
              <span className="text-accent">$</span> ./scopegain --connect
            </p>
            <h1 className="font-display text-6xl font-black uppercase tracking-widest text-foreground sm:text-7xl">
              ScopeGain
            </h1>
            <p className="mt-4 max-w-xl font-mono text-base leading-relaxed text-muted-foreground">
              Narzedzie do myslenia o inwestycjach: szukaj spolek, sprawdzaj ryzyko i
              policz realny zysk swojego portfela — na zywo z rynku.
              <span className="cursor-blink" />
            </p>
          </header>

          {/* Brama: niezalogowany widzi ekran logowania; reszta (i chronione API)
              renderuje sie dopiero po zalogowaniu. */}
          <AuthGate>
            <PortfoliosProvider>
              <WorkspaceBody />
            </PortfoliosProvider>
          </AuthGate>
        </main>
      </WorkspaceProvider>
    </AuthProvider>
  );
}
