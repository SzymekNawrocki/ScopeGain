// Adres API z env (NEXT_PUBLIC_ = widoczne w przegladarce). Fallback = lokalny backend.
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

// Jedno wejscie do API dla calej apki. Bez ciasteczek - ScopeGain jest lokalny
// i nie ma logowania (ADR-0005).
function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`${API_BASE}${path}`, init);
}

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

// --- Spolka: wyszukiwanie i profil ---

export type StockSearchHit = {
  ticker: string;
  name: string;
  // Gielda ROZROZNIA cross-listing: CCJ (NYSE, USD) i CCO.TO (Toronto, CAD)
  // to ta sama firma, ale inny papier. Bez tego pola user widzi dwa
  // identyczne wiersze "Cameco Corporation" i nie wie, czym sie roznia.
  exchange: string | null;
  quote_type: string | null; // "EQUITY" | "ETF"
  sector: string | null;
  industry: string | null;
};

export type StockProfile = {
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  market_cap: number | null;
  trailing_pe: number | null;
  beta: number | null;
  profit_margins: number | null;
  currency: string | null;
  summary: string | null;
};

// Podpowiedzi do wyszukiwarki (szukanie po NAZWIE, nie tylko po symbolu).
export async function searchStocks(q: string): Promise<StockSearchHit[]> {
  const res = await apiFetch(`/stock/search?q=${encodeURIComponent(q)}`);
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function getStockProfile(ticker: string): Promise<StockProfile> {
  const res = await apiFetch(`/stock/${encodeURIComponent(ticker)}/profile`);
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

// --- Werdykt (wspolny ksztalt dla VerdictFindings; nowy werdykt w plastrze 3) ---
export type Severity = "good" | "warn" | "bad";

export type VerdictFinding = {
  severity: Severity;
  title: string;
  detail: string;
};
