"use client";

import { RebalanceReport } from "./RebalanceReport";
import { usePortfoliosContext } from "./PortfoliosProvider";

// Tresc sekcji "rebalans" (12c): czyta te sama liste portfeli co reszta
// dashboardu z PortfoliosProvider.
export function RebalanceSection() {
  const { portfolios } = usePortfoliosContext();
  return <RebalanceReport portfolios={portfolios ?? []} />;
}
