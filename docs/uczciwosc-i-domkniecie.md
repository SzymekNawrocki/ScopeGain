# Uczciwość i domknięcie (lokalnie) — 2026-07-16

Wątek po zamknięciu warstwy 12. Cel: zrobić z ScopeGain narzędzie, **któremu
można ufać** — kompletne i uczciwe, choć lokalne (wdrożenie 7–9 świadomie
odłożone). Trzy fazy, wszystko offline poza pobieraniem danych (yfinance, NBP).

## Faza 1 — spłata długu

- Odpalona migracja 12b: `alembic upgrade head` (`f9ef892aa9cc → a1b2c3d4e5f6`) —
  tabela `transactions` istnieje w bazie.
- E2E na żywej bazie + auth przez `TestClient`/`requests`: rejestracja → login →
  portfel → pozycje → transakcje (BUY/SELL) → `transactions`/`behavior`/`risk`/
  `rebalance` — wszystkie `200`, dane sensowne, cleanup `204`.

## Faza 2 — realna ścieżka portfela z logu transakcji

Zamiast rzutować **dzisiejsze wagi** na całą historię (hipoteza), apka odtwarza,
co NAPRAWDĘ trzymało się każdego dnia, z logu transakcji.

- **Metoda: TWR (time-weighted return).** Na dniu z transakcją neutralizujemy
  przepływ gotówki (`r_t = (V_t − CF_t) / V_{t−1} − 1`), żeby dokupienie nie
  wyglądało jak zysk — dopiero to jest porównywalne z rynkiem.
- **Źródło prawdy = LOG + REKONCYLIACJA.** Ścieżkę liczymy z logu; pozycje
  zostają „ile mam teraz". Gdy netto z logu ≠ pozycje → **jawne ostrzeżenie** z
  listą rozjazdów (apka mówi, kiedy nie ufa danym, zamiast zmyślać).
- Czyste funkcje: `quant.holdings_timeline`, `quant.twr_index`,
  `quant.reconcile_holdings` (+ 8 testów).
- `market.closes_frame_range` / `close_series_range(end=None)` — ceny od pierwszej
  transakcji do dziś.
- Endpoint `GET /portfolios/{id}/real-performance` → `available`, `method`,
  krzywa realna vs SPY, `reconciliation`, `alpha`.
- Front: sekcja **„realna"** (`RealPerformanceReport`) obok „analizy" —
  bezpośredni kontrast realna vs hipotetyczna; ostrzeżenie rekoncyliacji.
- Weryfikacja: portfel AAPL od 2023 → realny TWR +171% vs SPY +106% (alpha +65);
  po dodaniu pozycji spoza logu `reconciled: false` z rozjazdem.

## Faza 3 — USD→PLN (kurs NBP)

Spółki są w USD, a Belka to podatek złotówkowy — bez przeliczenia „w kieszeni"
było półprawdą.

- `market.usd_pln_rate()` — kurs średni z NBP (tabela A), darmowe, bez klucza;
  `None` gdy NBP nie odpowie (wycena USD zostaje).
- `GET /portfolios/{id}/valuation` dokłada `fx_usd_pln`, `total_value_pln`,
  `total_pnl_net_pln`.
- Front: wiersz „W PLN (netto)" w `PortfolioCard`.
- **Uczciwy caveat:** MVP przelicza po kursie BIEŻĄCYM; poprawna Belka liczy się
  po kursie NBP z dnia przed KAŻDĄ transakcją (zaznaczone w tooltipie).
- Weryfikacja: 3329,40 USD × 3,7731 = 12 562,16 zł.

## Stan testów
`pytest` 80 zielonych (VaR/stress, 12b, 12c, holdings/TWR/reconcile). `tsc` czysty.

## Jak odpalić lokalnie
1. Baza: `docker start scopegain-db` → `cd backend && alembic upgrade head`.
2. API: `.venv\Scripts\python.exe -m uvicorn main:app --port 8000` (bez `--reload`).
3. Front: `cd frontend && npm run dev`.
