import { MarketScope } from "./components/MarketScope";
import { PortfoliosProvider } from "./components/PortfoliosProvider";
import { PortfoliosSection } from "./components/PortfoliosSection";
import { AnalysisSection } from "./components/AnalysisSection";
import { RiskSection } from "./components/RiskSection";
import { BehaviorSection } from "./components/BehaviorSection";
import { HowItWorks } from "./components/HowItWorks";
import { AuthProvider } from "./components/AuthProvider";
import { AuthGate } from "./components/AuthGate";
import { Nav } from "./components/Nav";
import { SectionLabel } from "./components/ui/SectionLabel";

// Server Component: powloka strony (nawigacja, naglowek, etykiety sekcji) nie
// ma zadnego stanu ani interakcji, wiec renderuje sie w calosci na serwerze -
// zero dodatkowego JS wysylanego do przegladarki za sam layout. PortfoliosProvider
// to jedyna granica klient/serwer wyzej: mimo ze jest "use client", te fragmenty
// JSX ktore nie potrzebuja stanu (Nav, naglowek, SectionLabel) zostaja server-side,
// bo sa przekazane jako zwykle dzieci/elementy, a nie zdefiniowane wewnatrz Providera.
export default function Dashboard() {
  return (
    // AuthProvider obejmuje pasek I tresc - dzieki temu i AuthStatus (w pasku),
    // i AuthGate (nizej) czytaja ten sam stan zalogowania.
    <AuthProvider>
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
            Dodaj spolki, ktore masz, a apka policzy Twoj realny zysk i ryzyko —
            na zywo z rynku.
            <span className="cursor-blink" />
          </p>
        </header>

        {/* Brama: niezalogowany widzi ekran logowania; reszta renderuje sie
            (i odpytuje chronione API) dopiero po zalogowaniu. */}
        <AuthGate>
          <HowItWorks />

          <PortfoliosProvider>
            {/* PORTFELE - Twoje holdingi + P&L (najpierw, bo to Twoje dane) */}
            <section id="portfele" className="mb-16 scroll-mt-20">
              <SectionLabel>./portfolios --list</SectionLabel>
              <PortfoliosSection />
            </section>

            {/* RYNEK - research dowolnej spolki (swiece + metryki), niezalezny stan */}
            <section id="rynek" className="scroll-mt-20">
              <SectionLabel>./market --scope</SectionLabel>
              <MarketScope />
            </section>

            {/* ANALIZA - werdykt, backtest vs rynek, ryzyko, korelacje */}
            <section id="analiza" className="mt-16 scroll-mt-20">
              <SectionLabel>./portfolio --analyze</SectionLabel>
              <AnalysisSection />
            </section>

            {/* RYZYKO - VaR/CVaR + stress test (ile realnie moge stracic) */}
            <section id="ryzyko" className="mt-16 scroll-mt-20">
              <SectionLabel>./portfolio --risk</SectionLabel>
              <RiskSection />
            </section>

            {/* ZACHOWANIE - log transakcji + werdykt timingu (behavior gap, 12b) */}
            <section id="zachowanie" className="mt-16 scroll-mt-20">
              <SectionLabel>./portfolio --behavior</SectionLabel>
              <BehaviorSection />
            </section>
          </PortfoliosProvider>
        </AuthGate>
      </main>
    </AuthProvider>
  );
}
