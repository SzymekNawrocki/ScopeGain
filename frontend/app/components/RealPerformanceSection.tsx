"use client";

import { RealPerformanceReport } from "./RealPerformanceReport";
import { usePortfoliosContext } from "./PortfoliosProvider";

// Tresc sekcji "realna sciezka": czyta te sama liste portfeli co reszta
// dashboardu z PortfoliosProvider.
export function RealPerformanceSection() {
  const { portfolios } = usePortfoliosContext();
  return <RealPerformanceReport portfolios={portfolios ?? []} />;
}
