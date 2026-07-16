"use client";

import { BehaviorReport } from "./BehaviorReport";
import { usePortfoliosContext } from "./PortfoliosProvider";

// Tresc sekcji "zachowanie" (12b): czyta te sama liste portfeli co reszta
// dashboardu z PortfoliosProvider.
export function BehaviorSection() {
  const { portfolios } = usePortfoliosContext();
  return <BehaviorReport portfolios={portfolios ?? []} />;
}
