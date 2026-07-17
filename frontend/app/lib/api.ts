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

// Jedno wejscie do API dla calej apki. credentials: "include" KAZE przegladarce
// dolaczyc httpOnly cookie z tokenem - bez tego cross-origin (3000 -> 8000)
// ciasteczko nie leci i chronione trasy oddaja 401. Trzymanie tego w jednym
// miejscu = nie da sie zapomniec w zadnym z kilkunastu fetchy nizej.
function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`${API_BASE}${path}`, { ...init, credentials: "include" });
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

// --- Auth (warstwa 5) ---
export type User = { id: number; email: string };

// Rzucany, gdy API mowi 401 (brak/wygasle cookie). Front lapie go i pokazuje
// ekran logowania zamiast traktowac to jak zwykla awarie.
export class UnauthorizedError extends Error {
  constructor() {
    super("Nie zalogowano.");
    this.name = "UnauthorizedError";
  }
}

export async function register(email: string, password: string): Promise<User> {
  const res = await apiFetch("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function login(email: string, password: string): Promise<User> {
  const res = await apiFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function logout(): Promise<void> {
  await apiFetch("/auth/logout", { method: "POST" });
}

// Kim jestem? Zwraca usera albo null (gdy 401 = niezalogowany). Front wola to
// na starcie, zeby zdecydowac: dashboard czy ekran logowania.
export async function getMe(): Promise<User | null> {
  const res = await apiFetch("/auth/me");
  if (res.status === 401) return null;
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

// Pobiera liste portfeli. fetch leci Z PRZEGLADARKI - dlatego backend musi
// miec wlaczone CORS, inaczej przegladarka zablokuje odpowiedz.
export async function getPortfolios(): Promise<Portfolio[]> {
  const res = await apiFetch("/portfolios");
  if (res.status === 401) throw new UnauthorizedError();
  if (!res.ok) {
    throw new Error(await apiError(res));
  }
  return res.json();
}

// --- Mutacje: tworzenie i kasowanie (zarzadzanie wlasnymi danymi z UI) ---

export async function createPortfolio(name: string): Promise<Portfolio> {
  const res = await apiFetch(`/portfolios`, {
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
  const res = await apiFetch(`/portfolios/${portfolioId}/positions`, {
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
  const res = await apiFetch(
    `/portfolios/${portfolioId}/positions/${positionId}`,
    { method: "DELETE" },
  );
  if (!res.ok) throw new Error(await apiError(res));
}

export async function deletePortfolio(portfolioId: number): Promise<void> {
  const res = await apiFetch(`/portfolios/${portfolioId}`, {
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
  total_pnl_abs: number;   // brutto
  total_pnl_pct: number;   // brutto
  // --- P&L netto (warstwa 12a): prowizja maklerska + podatek Belka ---
  total_commission: number;
  total_tax_belka: number;
  total_pnl_net_abs: number;
  total_pnl_net_pct: number;
  // --- Przeliczenie na PLN (kurs NBP); null gdy NBP nie odpowie ---
  fx_usd_pln: number | null;
  total_value_pln: number | null;
  total_pnl_net_pln: number | null;
};

// Dociaga aktualna wycene portfela (ceny z rynku + policzony zysk/strata).
export async function getPortfolioValuation(
  id: number,
): Promise<PortfolioValuation> {
  const res = await apiFetch(`/portfolios/${id}/valuation`);
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
  const res = await apiFetch(`/portfolios/${id}/performance?period=${period}`);
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
  const res = await apiFetch(`/portfolios/${id}/verdict?period=${period}`);
  if (!res.ok) {
    throw new Error(`API zwrocilo ${res.status}`);
  }
  return res.json();
}

// --- Ryzyko: VaR / CVaR / stress test (ile realnie moge stracic) ---
// Ksztalt 1:1 ze schematami PortfolioRisk / VarMeasure / StressScenario.
// Apka NIE prognozuje - VaR to percentyl REALNYCH zwrotow, stress to
// odtworzenie realnych krachow. Kwoty w USD (spolki w dolarach).

export const RISK_WINDOWS = ["1y", "2y", "5y"] as const;
export type RiskWindow = (typeof RISK_WINDOWS)[number];

export type VarMeasure = {
  confidence: number; // 0.95 / 0.99
  horizon: string; // "1d" / "1m"
  var_pct: number; // ujemny: strata
  var_abs: number; // w walucie portfela
  cvar_pct: number; // srednia strata poza VaR (ogon)
  cvar_abs: number;
};

export type StressScenario = {
  key: string;
  label: string;
  shock_pct: number; // laczne uderzenie w portfel (ujemne)
  pnl_abs: number;
  coverage_real: string[]; // spolki z realnych danych z krachu
  coverage_proxy: string[]; // spolki przez proxy (beta x indeks)
};

export type PortfolioRiskReport = {
  id: number;
  name: string;
  window: string;
  currency: string; // "USD"
  portfolio_value: number;
  n_days: number;
  var: VarMeasure[];
  stress: StressScenario[];
  warning: string | null;
};

export async function getPortfolioRisk(
  id: number,
  window: RiskWindow = "2y",
): Promise<PortfolioRiskReport> {
  const res = await apiFetch(`/portfolios/${id}/risk?window=${window}`);
  if (!res.ok) {
    throw new Error(await apiError(res));
  }
  return res.json();
}

// --- Transakcje + werdykt zachowania (warstwa 12b: behavior gap) ---
// Pozycja = "co mam teraz"; transakcja = "co zrobilem i kiedy". Log sprzedazy
// pozwala apce ocenic timing (czy sprzedales za wczesnie zwycieska spolke).

export type TransactionSide = "BUY" | "SELL";

export type Transaction = {
  id: number;
  ticker: string;
  side: string; // "BUY" / "SELL"
  quantity: number;
  price: number;
  executed_at: string; // "YYYY-MM-DD"
};

export async function getTransactions(portfolioId: number): Promise<Transaction[]> {
  const res = await apiFetch(`/portfolios/${portfolioId}/transactions`);
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function addTransaction(
  portfolioId: number,
  tx: {
    ticker: string;
    side: TransactionSide;
    quantity: number;
    price: number;
    executed_at: string;
  },
): Promise<Transaction> {
  const res = await apiFetch(`/portfolios/${portfolioId}/transactions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(tx),
  });
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function deleteTransaction(
  portfolioId: number,
  transactionId: number,
): Promise<void> {
  const res = await apiFetch(
    `/portfolios/${portfolioId}/transactions/${transactionId}`,
    { method: "DELETE" },
  );
  if (!res.ok) throw new Error(await apiError(res));
}

// Werdykt zachowania: findings maja ten sam ksztalt co werdykt portfela
// (severity/title/detail), plus laczne "zostawione na stole" i uczciwy caveat.
export type BehaviorVerdict = {
  id: number;
  name: string;
  grade: Severity;
  grade_label: string;
  total_left_on_table: number; // + = trzymanie byloby lepsze; - = dobre wyjscia
  caveat: string;
  findings: VerdictFinding[];
};

export async function getPortfolioBehavior(id: number): Promise<BehaviorVerdict> {
  const res = await apiFetch(`/portfolios/${id}/behavior`);
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

// --- Realna sciezka portfela z logu transakcji (uczciwosc) ---
// Zamiast rzutowac dzisiejsze wagi wstecz (hipoteza), liczy TWR z tego, co
// NAPRAWDE trzymalo sie kazdego dnia. "available: false" gdy brak logu.

export type ReconciliationDiscrepancy = {
  ticker: string;
  log: number;
  positions: number;
  diff: number;
};

export type RealPerformance = {
  id: number;
  name: string;
  available: boolean;
  reason?: string;
  method?: string;
  start_date?: string;
  benchmark_ticker?: string;
  portfolio_return_pct?: number;
  benchmark_return_pct?: number;
  alpha_pct?: number;
  reconciliation?: {
    reconciled: boolean;
    discrepancies: ReconciliationDiscrepancy[];
  };
  series?: PerformancePoint[];
};

export async function getPortfolioRealPerformance(id: number): Promise<RealPerformance> {
  const res = await apiFetch(`/portfolios/${id}/real-performance`);
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

// --- Rebalansing (warstwa 12c: punkt odniesienia, NIE porada) ---
// Rowne wagi jako neutralna miara koncentracji + ile kosztowaloby domkniecie
// rozjazdu (prowizja + Belka). Apka nie mowi "zrob to" - pokazuje trade-off.

export type RebalanceLeg = {
  ticker: string;
  current_value: number;
  current_weight_pct: number;
  target_weight_pct: number;
  drift_pp: number; // + przewazona / - niedowazona
  trade_value: number; // + dokup / - przytnij
};

export type RebalanceCost = {
  commission: number;
  tax_belka: number;
  total_cost: number;
};

export type RebalancePlan = {
  id: number;
  name: string;
  currency: string; // "USD"
  total_value: number;
  target: string; // "equal"
  legs: RebalanceLeg[];
  cost: RebalanceCost;
};

export async function getPortfolioRebalance(id: number): Promise<RebalancePlan> {
  const res = await apiFetch(`/portfolios/${id}/rebalance`);
  if (!res.ok) throw new Error(await apiError(res));
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
  const res = await apiFetch(`/portfolios/${id}/correlations?period=${period}`);
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
  const res = await apiFetch(
    `/stock/${encodeURIComponent(ticker)}/metrics?period=${period}`,
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
  const res = await apiFetch(
    `/stock/${encodeURIComponent(ticker)}/history?period=${period}`,
  );
  if (!res.ok) {
    if (res.status === 404) {
      throw new Error(`Nie znaleziono spolki "${ticker.toUpperCase()}"`);
    }
    throw new Error(`API zwrocilo ${res.status}`);
  }
  return res.json();
}

// --- Wyszukiwanie i analiza spolki ---
// Poczatek sciezki decyzyjnej: szukam -> ogladam. Wczesniej apka umiala tylko
// to, co juz masz, a "rynek" wymagal znajomosci symbolu na pamiec.

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

// Werdykt RYZYKA - nie ocena spolki i nie sygnal kup/sprzedaj (ADR-0001).
export type StockVerdict = {
  ticker: string;
  period: string;
  grade: Severity; // uwaga: "good" = NISKIE RYZYKO (semantyka odwrocona)
  grade_label: string; // "niskie ryzyko" | "podwyzszone ryzyko" | "wysokie ryzyko"
  caveat: string;
  data_gaps: string[]; // czego apka nie wiedziala
  findings: VerdictFinding[];
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

export async function getStockVerdict(
  ticker: string,
  period: Period = "6mo",
): Promise<StockVerdict> {
  const res = await apiFetch(
    `/stock/${encodeURIComponent(ticker)}/verdict?period=${period}`,
  );
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

// --- Odkrywanie po kategoriach (Etap B) ---
// Drill-down bez wpisywania tickera: sektor -> branza -> spolki, plus rozbicie
// ETF. UWAGA (ADR-0002): lista spolek branzy to ranking "top" Yahoo, NIE pelny
// spis - gubi liderow (Cameco przy uranie). Dlatego front dokleja zastrzezenie,
// a luki latane sa szukaniem po nazwie i rozbiciem ETF.

export type DiscoverNode = { key: string; name: string };
export type DiscoverCompany = { ticker: string; name: string };

export async function getDiscoverSectors(): Promise<DiscoverNode[]> {
  const res = await apiFetch(`/discover/sectors`);
  if (res.status === 401) throw new UnauthorizedError();
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function getSectorIndustries(sectorKey: string): Promise<DiscoverNode[]> {
  const res = await apiFetch(`/discover/sector/${encodeURIComponent(sectorKey)}`);
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function getIndustryCompanies(industryKey: string): Promise<DiscoverCompany[]> {
  const res = await apiFetch(`/discover/industry/${encodeURIComponent(industryKey)}`);
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function getEtfHoldings(ticker: string): Promise<DiscoverCompany[]> {
  const res = await apiFetch(`/discover/etf/${encodeURIComponent(ticker)}`);
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

// --- Tematy + Obserwacje (Etap B / plan decyzji) ---
// Temat = koszyk KURATOROWANY (ADR-0002). Obserwacja = typ z Teza +
// Uniewaznieniem; para (data, cena) z dodania pozwala go pozniej rozliczyc.

export type Observation = {
  id: number;
  ticker: string;
  name: string;
  origin: string; // Pochodzenie ("branza:uranium" / "ETF:QTUM" / "nazwa")
  thesis: string;
  invalidation_note: string | null;
  invalidation_price: number | null;
  entry_note: string | null;
  added_at: string; // "YYYY-MM-DD"
  added_price: number | null; // null gdy rynek nie odpowiedzial przy dodaniu
  acted: boolean;
};

export type Theme = {
  id: number;
  name: string;
  created_at: string;
  observations: Observation[];
};

// Wejscie do dodania obserwacji. Uniewaznienie obowiazkowe, ale moze byc cena
// LUB opis - walidacje "co najmniej jedno" pilnuje backend (i formularz).
export type ObservationInput = {
  ticker: string;
  name: string;
  origin: string;
  thesis: string;
  invalidation_note?: string | null;
  invalidation_price?: number | null;
  entry_note?: string | null;
};

export async function getThemes(): Promise<Theme[]> {
  const res = await apiFetch(`/themes`);
  if (res.status === 401) throw new UnauthorizedError();
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function getTheme(id: number): Promise<Theme> {
  const res = await apiFetch(`/themes/${id}`);
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function createTheme(name: string): Promise<Theme> {
  const res = await apiFetch(`/themes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function deleteTheme(id: number): Promise<void> {
  const res = await apiFetch(`/themes/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await apiError(res));
}

export async function addObservation(
  themeId: number,
  obs: ObservationInput,
): Promise<Observation> {
  const res = await apiFetch(`/themes/${themeId}/observations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(obs),
  });
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

export async function deleteObservation(themeId: number, obsId: number): Promise<void> {
  const res = await apiFetch(`/themes/${themeId}/observations/${obsId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await apiError(res));
}

// Przelacza flage "zadzialalem" (kupilem) - rozliczenie pyta o to wprost.
export async function toggleObservationActed(
  themeId: number,
  obsId: number,
): Promise<Observation> {
  const res = await apiFetch(`/themes/${themeId}/observations/${obsId}/acted`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}

// --- Rozliczenie typu (Etap 5) ---
// Hit rate na CALEJ puli, neutralnie. Nigdy "trzeba bylo kupic" (ADR-0001).

export type ReckoningRow = {
  id: number;
  ticker: string;
  name: string;
  added_at: string;
  added_price: number | null;
  current_price: number | null;
  move_pct: number | null; // ruch od dodania
  invalidation_price: number | null;
  invalidation_note: string | null;
  invalidation_triggered: boolean | null; // null = uniewaznienie opisowe (recznie)
  acted: boolean;
};

export type ReckoningSummary = {
  total: number;
  priced: number;
  up: number;
  down: number;
  invalidated: number;
  acted: number;
};

export type Reckoning = {
  id: number;
  name: string;
  caveat: string;
  rows: ReckoningRow[];
  summary: ReckoningSummary;
};

export async function getThemeReckoning(id: number): Promise<Reckoning> {
  const res = await apiFetch(`/themes/${id}/reckoning`);
  if (!res.ok) throw new Error(await apiError(res));
  return res.json();
}
