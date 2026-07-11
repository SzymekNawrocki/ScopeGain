"use client";

import { PortfolioVsMarket } from "./PortfolioVsMarket";
import { usePortfoliosContext } from "./PortfoliosProvider";

// Tresc sekcji "analiza": czyta ta sama liste portfeli co "portfele"
// z PortfoliosProvider, mimo ze sekcja "rynek" siedzi miedzy nimi w layoucie.
export function AnalysisSection() {
  const { portfolios } = usePortfoliosContext();
  return <PortfolioVsMarket portfolios={portfolios ?? []} />;
}
