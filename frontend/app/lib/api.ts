// Typy lustrzane do schematow Pydantic w backendzie (PortfolioRead/PositionRead).
export type Position = {
  id: number;
  ticker: string;
  quantity: number;
  buy_price: number;
};

export type Portfolio = {
  id: number;
  name: string;
  positions: Position[];
};

// Adres API z env (NEXT_PUBLIC_ = widoczne w przegladarce). Fallback = lokalny backend.
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Wyciaga czytelny komunikat bledu z odpowiedzi API (pole "detail" od FastAPI).
async function apiError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    // brak JSON-a w odpowiedzi - trudno, damy sam status
  }
  return `API zwrocilo ${res.status}`;
}

// Pobiera liste portfeli. fetch leci Z PRZEGLADARKI - dlatego backend musi
// miec wlaczone CORS, inaczej przegladarka zablokuje odpowiedz.
export async function getPortfolios(): Promise<Portfolio[]> {
  const res = await fetch(`${API_BASE}/portfolios`);
  if (!res.ok) {
    throw new Error(await apiError(res));
  }
  return res.json();
}

// --- Mutacje: tworzenie i kasowanie (zarzadzanie wlasnymi danymi z UI) ---

export async function createPortfolio(name: string): Promise<Portfolio> {
  const res = await fetch(`${API_BASE}/portfolios`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function addPosition(
  portfolioId: number,
  pos: { ticker: string; quantity: number; buy_price: number },
): Promise<Position> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}/positions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pos),
  });
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function deletePosition(
  portfolioId: number,
  positionId: number,
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/portfolios/${portfolioId}/positions/${positionId}`,
    { method: "DELETE" },
  );
  if (!res.ok) throw new Error(await apiError(res));
}

export async function deletePortfolio(portfolioId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/portfolios/${portfolioId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await apiError(res));
}

// Suma "kosztu wejscia" portfela = ile lacznie wydano (ilosc * cena zakupu).
// Zywej wyceny (ile to warte dzis) jeszcze nie liczymy - to warstwa 6 (quant).
export function costBasis(p: Portfolio): number {
  return p.positions.reduce((sum, pos) => sum + pos.quantity * pos.buy_price, 0);
}

// --- Zywa wycena portfela (warstwa 6: quant) ---
// Ksztalt 1:1 ze schematami PortfolioValuation / PositionValuation w backendzie.
// "| null" bo cena rynkowa moze byc niedostepna - wtedy wyceny nie liczymy.
export type PositionValuation = {
  id: number;
  ticker: string;
  quantity: number;
  buy_price: number;
  current_price: number | null;
  cost_basis: number;
  market_value: number | null;
  pnl_abs: number | null;
  pnl_pct: number | null;
};

export type PortfolioValuation = {
  id: number;
  name: string;
  positions: PositionValuation[];
  total_cost: number;
  total_value: number;
  total_pnl_abs: number;
  total_pnl_pct: number;
};

// Dociaga aktualna wycene portfela (ceny z rynku + policzony zysk/strata).
export async function getPortfolioValuation(
  id: number,
): Promise<PortfolioValuation> {
  const res = await fetch(`${API_BASE}/portfolios/${id}/valuation`);
  if (!res.ok) {
    throw new Error(`API zwrocilo ${res.status}`);
  }
  return res.json();
}

// --- Backtest portfela w czasie: "ja vs rynek" (warstwa 6c) ---
// Jeden punkt = jeden dzien. Obie liczby to INDEKS od 100 na starcie okresu,
// wiec portfel i rynek da sie porownac na jednej skali niezaleznie od kwot.
export type PerformancePoint = {
  time: string; // "YYYY-MM-DD"
  portfolio: number;
  benchmark: number;
};

// Metryki ryzyko/nagroda calego portfela (twarde liczby, ktorych broker
// nie pokazuje). Sharpe = zwrot na jednostke ryzyka; beta = jak mocno
// portfel rusza sie razem z rynkiem.
export type PortfolioRisk = {
  sharpe: number;
  beta: number;
  volatility_pct: number;
  return_risk: number;
};

export type PortfolioPerformance = {
  id: number;
  name: string;
  period: string;
  benchmark_ticker: string;
  portfolio_return_pct: number;
  benchmark_return_pct: number;
  alpha_pct: number; // nadwyzka portfela nad rynkiem (dodatnia = bijesz rynek)
  risk: PortfolioRisk;
  series: PerformancePoint[];
};

// Pobiera krzywa wzrostu portfela vs rynek za dany zakres.
export async function getPortfolioPerformance(
  id: number,
  period: Period = "6mo",
): Promise<PortfolioPerformance> {
  const res = await fetch(`${API_BASE}/portfolios/${id}/performance?period=${period}`);
  if (!res.ok) {
    throw new Error(`API zwrocilo ${res.status}`);
  }
  return res.json();
}

// --- Werdykt: apka MOWI, co z liczb wynika (warstwa 6f) ---
export type Severity = "good" | "warn" | "bad";

export type VerdictFinding = {
  severity: Severity;
  title: string;
  detail: string;
};

export type PortfolioVerdict = {
  id: number;
  name: string;
  period: string;
  grade: Severity; // ocena laczna
  grade_label: string; // slowo: mocny / przecietny / slaby
  findings: VerdictFinding[];
};

export async function getPortfolioVerdict(
  id: number,
  period: Period = "1y",
): Promise<PortfolioVerdict> {
  const res = await fetch(`${API_BASE}/portfolios/${id}/verdict?period=${period}`);
  if (!res.ok) {
    throw new Error(`API zwrocilo ${res.status}`);
  }
  return res.json();
}

// --- Korelacje miedzy spolkami w portfelu (warstwa 6d) ---
// matrix[i][j] = korelacja spolki tickers[i] z tickers[j] (od -1 do 1).
export type PortfolioCorrelations = {
  period: string;
  tickers: string[];
  matrix: number[][];
};

export async function getPortfolioCorrelations(
  id: number,
  period: Period = "6mo",
): Promise<PortfolioCorrelations> {
  const res = await fetch(`${API_BASE}/portfolios/${id}/correlations?period=${period}`);
  if (!res.ok) {
    throw new Error(`API zwrocilo ${res.status}`);
  }
  return res.json();
}

// --- Historia kursu (swiece OHLC) do wykresu ---

// Jedna swieca. Ksztalt 1:1 z tym, czego oczekuje Lightweight Charts.
export type Candle = {
  time: string; // "YYYY-MM-DD"
  open: number;
  high: number;
  low: number;
  close: number;
};

export type StockHistory = {
  ticker: string;
  period: string;
  candles: Candle[];
};

// Dozwolone zakresy - te same, co Literal w backendzie (/stock/{t}/history).
export const PERIODS = ["1mo", "3mo", "6mo", "1y", "5y"] as const;
export type Period = (typeof PERIODS)[number];

// Metryki quant spolki + porownanie z rynkiem (S&P 500).
export type StockMetrics = {
  ticker: string;
  period: string;
  return_pct: number; // zwrot za okres (backtest "gdybym kupil na start")
  volatility_pct: number; // zmiennosc (ryzyko), zroczniona
  max_drawdown_pct: number; // najwieksze obsuniecie (liczba ujemna)
  benchmark: { ticker: string; return_pct: number | null };
  alpha_pct: number | null; // nadwyzka nad rynkiem (dodatnia = bijesz rynek)
};

// Pobiera metryki quant dla spolki za dany zakres.
export async function getStockMetrics(
  ticker: string,
  period: Period = "6mo",
): Promise<StockMetrics> {
  const res = await fetch(
    `${API_BASE}/stock/${encodeURIComponent(ticker)}/metrics?period=${period}`,
  );
  if (!res.ok) {
    throw new Error(`API zwrocilo ${res.status}`);
  }
  return res.json();
}

// Pobiera historie swiec dla spolki. 404 = zly ticker -> czytelny komunikat.
export async function getStockHistory(
  ticker: string,
  period: Period = "6mo",
): Promise<StockHistory> {
  const res = await fetch(
    `${API_BASE}/stock/${encodeURIComponent(ticker)}/history?period=${period}`,
  );
  if (!res.ok) {
    if (res.status === 404) {
      throw new Error(`Nie znaleziono spolki "${ticker.toUpperCase()}"`);
    }
    throw new Error(`API zwrocilo ${res.status}`);
  }
  return res.json();
}
