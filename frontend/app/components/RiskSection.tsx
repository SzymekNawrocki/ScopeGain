"use client";

import { RiskReport } from "./RiskReport";
import { usePortfoliosContext } from "./PortfoliosProvider";

// Tresc sekcji "ryzyko": czyta te sama liste portfeli co reszta dashboardu
// z PortfoliosProvider.
export function RiskSection() {
  const { portfolios } = usePortfoliosContext();
  return <RiskReport portfolios={portfolios ?? []} />;
}
