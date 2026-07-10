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
