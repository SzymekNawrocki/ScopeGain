"use client";

import { usePortfoliosContext } from "./PortfoliosProvider";
import { PortfoliosSection } from "./PortfoliosSection";
import { PortfolioSelector } from "./PortfolioSelector";
import { PortfolioVsMarket } from "./PortfolioVsMarket";
import { RealPerformanceReport } from "./RealPerformanceReport";
import { RiskReport } from "./RiskReport";
import { BehaviorReport } from "./BehaviorReport";
import { RebalanceReport } from "./RebalanceReport";
import { HowItWorks } from "./HowItWorks";
import { SectionLabel } from "./ui/SectionLabel";

// Podtytul pod terminalowa etykieta: komenda zostaje (sygnatura apki), ale obok
// idzie jedno zdanie po ludzku - zeby "kazdy kto wejdzie" wiedzial, co sekcja robi.
function Sekcja({
  command,
  human,
  children,
}: {
  command: string;
  human: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <SectionLabel>{command}</SectionLabel>
      <p className="-mt-2 mb-4 font-mono text-xs text-muted-foreground">{human}</p>
      {children}
    </section>
  );
}

// Tryb "Moj portfel": wszystko o Twoich danych w jednym miejscu. Najpierw karty
// portfeli (wejscie), a gdy jakis portfel istnieje - JEDEN wspolny wybor portfela
// i pod nim cala analiza dla niego (backtest, realna sciezka, ryzyko, zachowanie,
// rebalans). Wczesniej kazda z tych sekcji miala wlasny wybor portfela.
export function PortfolioWorkspace() {
  const { portfolios } = usePortfoliosContext();
  const hasPortfolios = portfolios != null && portfolios.length > 0;

  return (
    <div className="space-y-14">
      <HowItWorks />

      {/* Portfele: nowy portfel + karty pozycji. Sam obsluguje stany
          ladowania / bledu / pustki. */}
      <section>
        <SectionLabel>./portfolios --list</SectionLabel>
        <p className="-mt-2 mb-4 font-mono text-xs text-muted-foreground">
          Twoje koszyki pozycji i ich wycena na zywo.
        </p>
        <PortfoliosSection />
      </section>

      {/* Analiza pojawia sie dopiero, gdy jest co analizowac. Jeden wspolny
          wybor portfela steruje wszystkimi sekcjami ponizej. */}
      {hasPortfolios && (
        <>
          <PortfolioSelector />

          <Sekcja
            command="./portfolio --analyze"
            human="Backtest vs rynek (hipotetyczny), werdykt i korelacje."
          >
            <PortfolioVsMarket />
          </Sekcja>

          <Sekcja
            command="./portfolio --real-path"
            human="Realna krzywa z logu transakcji (TWR), nie z dzisiejszych wag."
          >
            <RealPerformanceReport />
          </Sekcja>

          <Sekcja
            command="./portfolio --risk"
            human="Ile realnie mozesz stracic: VaR / CVaR + stress test krachow."
          >
            <RiskReport />
          </Sekcja>

          <Sekcja
            command="./portfolio --behavior"
            human="Log kupna/sprzedazy + ocena timingu (behavior gap)."
          >
            <BehaviorReport />
          </Sekcja>

          <Sekcja
            command="./portfolio --rebalance"
            human="Jak daleko od rownych wag i ile kosztuje domkniecie rozjazdu."
          >
            <RebalanceReport />
          </Sekcja>
        </>
      )}
    </div>
  );
}
