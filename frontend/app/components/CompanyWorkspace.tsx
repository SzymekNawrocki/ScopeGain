"use client";

import { useEffect, useState } from "react";
import { CompanyAnalysis, getCompanyAnalysis } from "../lib/api";
import { CompanyCard } from "./CompanyCard";
import { SearchBox } from "./SearchBox";
import { StatusPanel } from "./ui/StatusPanel";
import { TerminalWindow } from "./ui/TerminalWindow";

// The result always carries the ticker it belongs to. "Loading" = no result yet
// for the CURRENT ticker, so no setState runs synchronously inside the effect.
type Result =
  | { ticker: string; analysis: CompanyAnalysis; error: null }
  | { ticker: string; analysis: null; error: string };

export function CompanyWorkspace({ initialTicker = "AAPL" }: { initialTicker?: string }) {
  const [ticker, setTicker] = useState(initialTicker.toUpperCase());
  const [result, setResult] = useState<Result | null>(null);

  useEffect(() => {
    let current = true; // ignore a response that arrives after the ticker changed
    getCompanyAnalysis(ticker)
      .then((analysis) => current && setResult({ ticker, analysis, error: null }))
      .catch(
        (e) =>
          current &&
          setResult({ ticker, analysis: null, error: e.message ?? "Błąd pobierania" }),
      );
    return () => {
      current = false;
    };
  }, [ticker]);

  const shown = result?.ticker === ticker ? result : null;

  return (
    <TerminalWindow title="Spółka">
      <div className="mb-5">
        <SearchBox value={ticker} onPick={(t) => setTicker(t.toUpperCase())} />
      </div>

      {!shown && (
        <StatusPanel variant="loading">
          Analizuję {ticker}: sprawozdania z SEC, wycena, ryzyko…
        </StatusPanel>
      )}
      {shown?.error && <StatusPanel variant="error">{shown.error}</StatusPanel>}
      {shown?.analysis && <CompanyCard analysis={shown.analysis} />}
    </TerminalWindow>
  );
}
