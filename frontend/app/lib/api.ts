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

// Pobiera liste portfeli. fetch leci Z PRZEGLADARKI - dlatego backend musi
// miec wlaczone CORS, inaczej przegladarka zablokuje odpowiedz.
export async function getPortfolios(): Promise<Portfolio[]> {
  const res = await fetch(`${API_BASE}/portfolios`);
  if (!res.ok) {
    throw new Error(`API zwrocilo ${res.status}`);
  }
  return res.json();
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
