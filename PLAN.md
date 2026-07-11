# Plan projektu — ScopeGain (analiza portfela + backtest)

> **Cel:** zbudować JEDNĄ pełnoprawną aplikację full-stack, na której nauczę się
> backendu, DevOps, chmury, fintechu i security — warstwa po warstwie, aż każda
> zaskoczy, zanim ruszę dalej. Wszystko za darmo lub za grosze.

---

## 🎯 Czym będzie aplikacja

Platforma do analizy portfela inwestycyjnego:
- pobiera dane rynkowe (kursy spółek/ETF-ów),
- liczy metryki (zwroty, ryzyko, korelacje),
- pokazuje dashboard z wykresami,
- pozwala przetestować prostą strategię na danych historycznych (backtest),
- stoi w chmurze pod realnym adresem, wdraża się sama po `git push`.

**Co „obronię" na rozmowie:** działający, wdrożony produkt z CI/CD, monitoringiem,
testami i przemyślanymi decyzjami — nie kolejne repo z tutorialem.

---

## 🧱 Zasady pracy (WAŻNE — czytać przed każdą sesją)

1. **Jedna warstwa naraz.** Nie dokładam kolejnej, dopóki obecna nie zaskoczy.
2. **Teoria wywołana praktyką.** Utykam na pojęciu → czytam TYLKO to pojęcie →
   stosuję → wracam. Nie uczę się teorii „na zapas".
3. **Najpierw brzydko, że działa. Potem ładnie.** Pierwsza wersja każdej warstwy
   ma po prostu działać — refactor przychodzi później.
4. **Każda warstwa = osobny zaskok.** „Fajny efekt" pojawia się już przy warstwie 4,
   nie muszę czekać do końca.
5. **Nie robię wszystkiego naraz** — to jedyny sposób, żeby się wypalić.

---

## 🛠️ Stack technologiczny

| Warstwa | Wybór | Po co |
|---|---|---|
| Język backendu | **Python 3.12** | Ten sam język do API i do algorytmów inwestycyjnych |
| Framework API | **FastAPI** | Nowoczesny, szybki, auto-dokumentacja API |
| Dane rynkowe | **yfinance** | Za darmo, jedna linijka pobiera historię kursu |
| Obliczenia / quant | **pandas + numpy** | Standard branży — zwroty, ryzyko, backtest |
| Baza danych | **PostgreSQL** | Baza nr 1 w fintechu |
| ORM + migracje | **SQLAlchemy + Alembic** | Python zamiast SQL; Alembic wersjonuje zmiany w bazie |
| Frontend | **Next.js (React + TypeScript)** | To, co już ogarniam |
| Wykresy | **Lightweight Charts** (TradingView) | Świecowe wykresy jak w prawdziwej apce giełdowej |
| Auth | **własne JWT** | Napiszę sam, żeby zrozumieć jak działa logowanie |
| Konteneryzacja | **Docker + docker-compose** | „U mnie działa" → „działa wszędzie" |
| Hosting backend | **Railway** / Fly.io | Darmowy tier, deploy z gita, ogarnia Dockera |
| Hosting bazy | **Neon** / Supabase | Darmowy Postgres w chmurze |
| Hosting frontend | **Vercel** | Deploy = `git push`, darmowy |
| CI/CD | **GitHub Actions** | Commit → testy → auto-deploy |
| Monitoring | **Sentry** + logi hostingu | Widzę crashe na produkcji |
| Testy | **pytest** | To odróżnia juniora od „piszę i się modlę" |
| Sekrety | **zmienne środowiskowe (.env)** | Klucze API nigdy w kodzie |

**Koszt:** 0 zł na start. Opcjonalnie własna domena ~40 zł/rok dla efektu.

### Jak to się łączy w jeden organizm

```
[Ja: git push]
      │
      ▼
[GitHub] ──► [GitHub Actions: testy pytest] ──► deploy
      │                                          │
      ▼                                          ▼
[Vercel: Next.js]  ◄──── HTTP/JSON ────►  [Railway: FastAPI]
   dashboard,                               │  pandas liczy zwroty
   wykresy                                  ▼
                                    [Neon: PostgreSQL]
                                       portfel, historia
                              [yfinance ──► pobiera kursy]
                              [Sentry ──► łapie błędy]
```

---

## 🪜 Plan warstwa po warstwie

Każda warstwa to osobny „rozdział". Zaczynam kolejny dopiero, gdy poprzedni działa
i rozumiem, dlaczego działa.

### ✅ Warstwa 1 — Rdzeń lokalnie (brzydko, ale działa) — ZROBIONE
- [x] Pusty folder, wirtualne środowisko Pythona (`.venv`)
- [x] Instalacja `yfinance`, `pandas`
- [x] Skrypt `hello_stock.py`: pobiera kurs AAPL, liczy zwrot, wypisuje liczbę
- **Zaskok:** „pobrałem prawdziwe dane giełdowe i coś z nich policzyłem"
- **Teoria po drodze:** czym jest zwrot (return), środowisko wirtualne, pip

### ✅ Warstwa 2 — Backend porządnie (FastAPI) — ZROBIONE
- [x] Postawienie FastAPI, pierwszy endpoint `GET /health`
- [x] Endpoint `GET /stock/{ticker}` zwracający kurs + zwrot jako JSON
- [x] Obsługa błędów: nieistniejąca spółka → 404 (nie 500)
- [ ] Walidacja treści (Pydantic) — przeniesiona do warstwy 4a (endpointy `POST`)
- [x] Automatyczna dokumentacja API (`/docs`)
- **Zaskok:** „mam własne API, które ktoś mógłby odpytać"
- **Teoria:** czym jest REST API, request/response, JSON, kody HTTP

### ✅ Warstwa 3 — Baza danych (PostgreSQL) — ZROBIONE
- [x] Lokalny Postgres 16 przez Docker (kontener `scopegain-db`, port 5432)
- [x] Modele: portfel ——< pozycja (klucz obcy). Użytkownik → warstwa 5 (auth)
- [x] SQLAlchemy — zapis i odczyt z bazy (`database.py`, `models.py`)
- [x] Alembic — pierwsza migracja (tabele `portfolios`, `positions`)
- **Zaskok:** „dane przeżywają restart aplikacji" (zweryfikowane — restart kontenera)
- **Teoria:** relacyjna baza, tabele, klucze, migracje, po co ORM

> **Decyzja:** SQLite odrzucone — uczymy się „na poważnie" od razu na Postgresie.
> Docker podprowadzony z warstwy 7 (tylko `docker run`), żeby postawić bazę czysto.

### ✅ Warstwa 4 — Frontend / dashboard — ZROBIONE
- [x] **4a.** Endpointy portfela w API: `POST /portfolios`, `GET /portfolios` (+ Pydantic!)
- [x] **4b.** Next.js gada z moim API (fetch z przeglądarki + CORS na backendzie)
- [x] Widok portfela: lista pozycji + koszt wejścia (design cyberpunk wg DESIGN.md)
- [x] **4c.** Wykres kursu (Lightweight Charts): endpoint `GET /stock/{ticker}/history`
      (świece OHLC) + komponent `PriceChart` + sekcja `MarketScope` (ticker + zakres)
- **Zaskok:** „to wygląda jak prawdziwa apka giełdowa" ← pierwszy duży efekt „wow" ✅
- **Teoria:** fetch do API, CORS, komponenty, `useRef` do integracji z biblioteką spoza Reacta

### ✅ Warstwa 5 — Auth + sekrety — ZROBIONE
- [x] Rejestracja / logowanie (`POST /auth/register`, `/auth/login`, `/logout`, `GET /auth/me`)
- [x] JWT — podpisany token po zalogowaniu, trzymany w **httpOnly cookie**
      (JS go nie widzi → odporne na kradziez tokenu przez XSS; produkcyjne podejscie)
- [x] Każdy widzi tylko swój portfel — model `User`, FK `Portfolio.user_id`,
      `get_current_user` na wszystkich trasach portfela + scoping po userze
      (cudzy portfel = 404, nie zdradzamy nawet ze istnieje)
- [x] Hasla hashowane bcryptem (nigdy jawne w bazie); `SECRET_KEY` z env (dev-default z ostrzezeniem)
- **Zaskok:** „mam prawdziwe logowanie, które sam napisałem" ✅
- **Teoria:** hashowanie haseł (bcrypt + sól), JWT (podpis HS256, exp), httpOnly cookie
  vs localStorage (XSS), CORS z `allow_credentials`, po co sekrety poza kodem
- **Decyzja:** token w httpOnly cookie, nie localStorage — bezpieczniej (JS nie czyta),
  kosztem paru ruchomych czesci (CORS credentials, SameSite). Broni sie na rozmowie.
- **Uwaga:** stary seed-portfel sprzed auth ma `user_id = NULL` (osierocony,
  niewidoczny dla nikogo) — nowe portfele tworzy sie juz na koncie.

### ✅ Warstwa 6 — Quant (serce projektu) — ZROBIONE
- [x] **6a.** Żywa wycena portfela + P&L: `GET /portfolios/{id}/valuation`
      (baza × ceny z rynku → zysk/strata na karcie, zielone/czerwone)
- [x] **6b.** Metryki ryzyka + „ja vs rynek": `GET /stock/{ticker}/metrics`
      (zwrot, zmienność, max drawdown, alpha vs S&P 500) → panel kafelków
- [x] **6c.** Backtest w czasie: `GET /portfolios/{id}/performance`
      (krzywa portfel vs SPY, obie od 100) → dwuliniowy wykres
- [x] **6d.** Korelacje między spółkami: `GET /portfolios/{id}/correlations`
      → mapa cieplna (dywersyfikacja)
- [x] **6e.** Metryki ryzyko/nagroda portfela (Sharpe, beta, zwrot/ryzyko)
      w `GET /portfolios/{id}/performance` → panel kafelków
- [x] **6f.** WERDYKT: silnik reguł `analysis.py` zamienia liczby w wnioski
      po ludzku + ocenę 🟢🟡🔴 — `GET /portfolios/{id}/verdict`
- **Kod:** czyste obliczenia w `quant.py` (pandas/numpy), reguły w `analysis.py`,
  dane rynkowe w `market.py` (yfinance) — wszystko oddzielone od API (testowalne).
- **Zaskok:** „moja apka daje realny wgląd inwestycyjny i MÓWI, co z niego wynika" ✅
- **Teoria:** zmienność, drawdown, benchmark, korelacja, Sharpe, beta, alpha

### ✅ Warstwa UX — z „tablicy do gapienia" w używalne narzędzie — ZROBIONE
> Wtrącona po warstwie 6, bo analiza liczyła się o seedzie, nie o danych usera.
- [x] **ux-1.** Zarządzanie danymi z UI: `+ nowy portfel`, dodaj/usuń pozycję,
      usuń portfel. Walidacja rynkowa przy dodawaniu (`400` na nieznany ticker).
      Nowe: `DELETE /portfolios/{id}`, `DELETE /portfolios/{id}/positions/{pid}`.
- [x] **ux-2.** Przyklejony pasek nawigacji + sekcje z kotwicami
      (Portfele → Rynek → Analiza), płynne przewijanie, puste stany prowadzące.
- **Zaskok:** „to jest MOJE narzędzie na MOICH danych, nie demo"
- **Do dopchnięcia później:** edycja pozycji, globalny wybór portfela w pasku,
  podświetlanie aktywnej sekcji przy scrollu.

### Warstwa 7 — Konteneryzacja (Docker)
- [ ] Dockerfile dla backendu
- [ ] docker-compose: backend + baza jednym poleceniem
- **Zaskok:** „`docker compose up` i całość wstaje od zera"
- **Teoria:** czym jest kontener, obraz, po co to w ogóle

### Warstwa 8 — Chmura (deploy)
- [ ] Backend na Railway
- [ ] Baza na Neon
- [ ] Frontend na Vercel
- [ ] Wszystko połączone, działa pod realnym URL
- **Zaskok:** „wysyłam komuś link i on TO widzi"
- **Teoria:** czym różni się produkcja od lokalnego, zmienne środowiskowe w chmurze

### Warstwa 9 — CI/CD (GitHub Actions)
- [ ] Pipeline: push → uruchom testy → jeśli zielone, wdróż
- **Zaskok:** „nie dotykam serwera, wszystko dzieje się samo po commicie"
- **Teoria:** czym jest CI/CD, pipeline, dlaczego automatyzacja

### Warstwa 10 — Monitoring + logi
- [ ] Sentry łapie błędy z produkcji
- [ ] Przeglądanie logów hostingu
- **Zaskok:** „wiem o crashu, zanim ktokolwiek mi go zgłosi"
- **Teoria:** obserwowalność, logi vs metryki vs błędy

### Warstwa 11 — Security-hardening (wątek ethical-hacking)
- [ ] Przegląd własnej apki pod kątem podatności (OWASP Top 10)
- [ ] Rate limiting, walidacja, zabezpieczenie endpointów
- [ ] Próba „zhakowania" siebie
- **Zaskok:** „patrzę na swój kod oczami atakującego"
- **Teoria:** OWASP Top 10, typowe podatności, myślenie ofensywne

### Warstwa 12 — Realna wartość inwestycyjna (research-driven)
> **Decyzja (po researchu 07/2026):** dane (DALBAR, badania nad kosztami
> funduszy, badania nad pułapkami backtestu) NIE potwierdzają, że wyrafinowane
> sygnały (AI agenci, modele reżimów) to droga do realnej wartości dla
> inwestora indywidualnego. Trzy rzeczy faktycznie decydują o wyniku: KOSZTY
> (0,5% opłaty rocznej = ~165k $ straty na 100k $ w 30 lat, przez efekt
> składany), ZACHOWANIE (DALBAR: -8,5pp/rok w 2024 przez złe momenty
> wejścia/wyjścia — to główna przyczyna niedoważenia wyniku rynku, nie dobór
> aktywów) i DYWERSYFIKACJA/KONCENTRACJA (10 największych spółek S&P 500 to
> już 36% indeksu, 5 lat temu 23%). Ta warstwa dokłada te trzy rzeczy w
> kolejności wg udowodnionego wpływu — PRZED warstwą reżimów rynkowych (13).
- [x] **12a.** P&L netto: prowizja maklerska + podatek Belka (19% od zysku)
      obok istniejącego P&L brutto w `GET /portfolios/{id}/valuation` —
      ile REALNIE zostaje w kieszeni, nie tylko ile urosła cena.
      Czyste `quant.net_pnl()` (prowizja 0,29% kupno+sprzedaż, Belka tylko
      od zysku po prowizjach) + 4 nowe pola w `PortfolioValuation` + wiersz
      „netto w kieszeni" pod brutto w `PortfolioCard`.
- [ ] **12b.** Log transakcji + „werdykt zachowania": zapisuj historię
      kupna/sprzedaży (nie tylko aktualny stan pozycji — nowa tabela/model),
      żeby werdykt umiał powiedzieć „sprzedałeś X trzy miesiące temu, od
      tamtej pory rynek urósł o Y%". Atakuje bezpośrednio przyczynę #1
      niedoważenia wyniku (behavior gap), nie tylko dobór aktywów.
- [ ] **12c.** Sugestia rebalancingu: werdykt już wykrywa koncentrację
      (`top_weight_pct` w `analysis.py`) — dołóż konkretną podpowiedź
      „przytnij X o Y%, dokup Z", nie tylko samo ostrzeżenie.
- **Zaskok:** „apka mówi mi coś, czego mój dotychczasowy P&L brutto ukrywał"
- **Teoria:** podatek Belka, efekt składany kosztów, behavior gap, diversification return

### Warstwa 13 — Reżimy rynkowe (Markov) — eksploracyjna, NIE priorytetowa
> Ciekawa warstwa quant (stan rynku bull/bear/sideways + macierz przejść,
> zainspirowana materiałem o hedge-fundowym podejściu do rynku), ale zgodnie
> z Decyzją w Warstwie 12 — to nauka matematyki finansowej, nie droga do
> realnej wartości. Robię DOPIERO po Warstwie 12.
- [ ] **13a.** `regime.py`: klasyfikacja stanu rynku + macierz przejść jako
      czyste, testowalne funkcje (styl `quant.py`)
- [ ] **13b.** Walk-forward: macierz na dzień `t` liczona TYLKO z danych do
      `t` (bez lookahead bias — najczęstszy grzech DIY backtestów)
- [ ] **13c.** Panel w UI: dzisiejszy stan + prognoza (reużywa heatmapy
      z `CorrelationMatrix`)
- **Zaskok:** „rozumiem różnicę między ładnym backtestem a takim, który nie kłamie"
- **Teoria:** łańcuchy Markowa, macierz przejść, walk-forward validation

---

## 🧪 Rzeczy dokładane po drodze (nie osobne warstwy)
- **Testy (pytest)** — dokładam od warstwy 2, rosną z projektem
- **Git / commity** — od warstwy 1, dobra higiena od początku
- **README** — aktualizowane co warstwę, to też portfolio

---

## 📌 Gdzie teraz jestem
- [x] **Warstwa 1** — Rdzeń lokalnie ✅
- [x] **Warstwa 2** — Backend FastAPI ✅
- [x] **Warstwa 3** — Baza Postgres + Alembic ✅
- [x] **Warstwa 4** — Frontend / dashboard (portfele + wykres świecowy) ✅
- [x] **Warstwa 6** — Quant: wycena+P&L, ryzyko, backtest vs rynek, korelacje, Sharpe/beta, WERDYKT ✅
- [x] **Warstwa UX** — zarządzanie danymi z UI (CRUD) + nawigacja/układ ✅
- [x] **Warstwa UX+** — onboarding „jak to działa" (3 kroki) + jaśniejszy nagłówek/puste stany ✅
- [x] **Warstwa 5** — Auth: rejestracja/logowanie, JWT w httpOnly cookie, portfele per-user ✅
- [ ] **Warstwy 7–11** — Docker, chmura, CI/CD, monitoring, security (później)
- [ ] **Warstwa 12** — Realna wartość: P&L netto (koszty+Belka ✅ 12a), werdykt zachowania (12b), rebalancing (12c) ← **następna**
- [ ] **Warstwa 13** — Reżimy rynkowe (Markov) — eksploracyjna, po Warstwie 12

**Backend — moduły (mapa):**
- `routers/` — HTTP: `auth.py` (rejestracja/logowanie/me, ustawia httpOnly cookie),
  `stock.py` (kursy, historia świec, metryki — publiczne), `portfolios.py` (CRUD + wycena,
  backtest, korelacje, werdykt — wszystko chronione i scope'owane per-user)
- `security.py` — bcrypt (hash/verify), JWT (create/decode), `get_current_user` (czyta cookie)
- `quant.py` — czyste obliczenia (zwroty, zmienność, drawdown, Sharpe, beta)
- `analysis.py` — silnik reguł werdyktu (liczby → wnioski + ocena)
- `market.py` — jedyne miejsce z yfinance (ceny, historia, benchmark SPY)

**Frontend — auth (mapa):**
- `AuthProvider` — jedno źródło prawdy o userze (`/auth/me` na starcie), login/register/logout
- `AuthGate` — niezalogowany → `AuthPanel` (login/rejestracja); zalogowany → dashboard
- `AuthStatus` — email + „wyloguj" w pasku; `lib/api.ts` — `apiFetch` dokłada `credentials:"include"`

**Testy:** `backend/tests/` — pytest na `quant.py` (zwroty, zmiennosc, Sharpe, beta,
max drawdown) i `analysis.py` (kazda galaz reguly werdyktu + agregacja oceny).
Odpalenie: `cd backend && .venv\Scripts\python.exe -m pytest tests/ -v`.

**Do dopchnięcia (używalność):** edycja pozycji, globalny wybór portfela w pasku.
**Analiza — dalej:** patrz Warstwa 12 (P&L netto, werdykt zachowania, rebalancing).
**Kierunek quant (kandydatury + rekomendacja):** `QUANT_ROADMAP.md` — Monte Carlo,
  granica efektywna (Markowitz), silnik rebalancingu (12c), VaR/stress test.
  Diagnoza: apka „opisuje przeszłość”, brakuje spojrzenia w przód i konkretu do
  działania. Decyzja o wyborze następnej funkcji — otwarta.

**Repo:** https://github.com/SzymekNawrocki/ScopeGain
**Układ:** monorepo — `backend/` (FastAPI) + `frontend/` (Next.js)
**Odpalenie lokalnie:**
- baza: `docker start scopegain-db`
- API: `cd backend` → `.venv\Scripts\python.exe -m uvicorn main:app --port 8000` → http://127.0.0.1:8000/docs
  (bez `--reload` — na tym Windowsie zostawia osierocone workery na porcie 8000)
- front: `cd frontend` → `npm run dev` → http://localhost:3000

_Plik żywy — odhaczam zadania i aktualizuję w miarę postępu._
