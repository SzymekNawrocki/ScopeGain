"use client";

import { useEffect, useState } from "react";
import { getStockProfile, StockProfile } from "../lib/api";
import { SearchBox } from "./SearchBox";
import { StockProfilePanel } from "./StockProfilePanel";
import { StatusPanel } from "./ui/StatusPanel";
import { TerminalWindow } from "./ui/TerminalWindow";

// Wynik zawsze niesie ticker, dla ktorego przyszedl. "Laduje" = nie mamy
// jeszcze wyniku dla AKTUALNEGO tickera - bez osobnego setLoading w efekcie.
type Result =
  | { ticker: string; profile: StockProfile; error: null }
  | { ticker: string; profile: null; error: string };

// Ekran "Spolka": wpisujesz ticker -> apka mowi, czym spolka jest.
// Szkielet pod karte spolki z plastra 3 (werdykt + Za/Przeciw + braki danych).
export function CompanyWorkspace() {
  const [ticker, setTicker] = useState("AAPL");
  const [result, setResult] = useState<Result | null>(null);

  useEffect(() => {
    let aktualne = true; // straznik: ignoruj odpowiedz starego zapytania
    getStockProfile(ticker)
      .then((profile) => aktualne && setResult({ ticker, profile, error: null }))
      .catch(
        (e) =>
          aktualne &&
          setResult({ ticker, profile: null, error: e.message ?? "Blad pobierania" }),
      );
    return () => {
      aktualne = false;
    };
  }, [ticker]);

  const current = result?.ticker === ticker ? result : null;

  return (
    <TerminalWindow title="Spółka">
      <div className="mb-5">
        <SearchBox value={ticker} onPick={setTicker} />
      </div>

      {!current && <StatusPanel variant="loading">Pobieram profil {ticker}…</StatusPanel>}
      {current?.error && <StatusPanel variant="error">{current.error}</StatusPanel>}
      {current?.profile && <StockProfilePanel profile={current.profile} />}
    </TerminalWindow>
  );
}
