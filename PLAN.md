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

### Warstwa 4 — Frontend / dashboard  ← TU JESTEM
- [x] **4a.** Endpointy portfela w API: `POST /portfolios`, `GET /portfolios` (+ Pydantic!)
- [ ] **4b.** Next.js gada z moim API
- [ ] Widok portfela: lista pozycji + wartości
- [ ] Wykres kursu (Lightweight Charts)
- **Zaskok:** „to wygląda jak prawdziwa apka giełdowa" ← pierwszy duży efekt „wow"
- **Teoria:** fetch do API, CORS, komponenty (dużo już umiem)

### Warstwa 5 — Auth + sekrety
- [ ] Rejestracja / logowanie
- [ ] JWT — token po zalogowaniu
- [ ] Każdy widzi tylko swój portfel
- [ ] Klucze i hasła w zmiennych środowiskowych, nie w kodzie
- **Zaskok:** „mam prawdziwe logowanie, które sam napisałem"
- **Teoria:** hashowanie haseł, tokeny, po co sekrety poza kodem

### Warstwa 6 — Quant (serce projektu)
- [ ] Metryki ryzyka (zmienność, max drawdown)
- [ ] Korelacje między spółkami
- [ ] Prosty backtest: „gdybym kupił X rok temu, mam +Y%"
- [ ] Porównanie „ja vs rynek" (np. vs S&P 500)
- **Zaskok:** „moja apka daje realny wgląd inwestycyjny"
- **Teoria:** statystyka finansowa, zmienność, drawdown, benchmark

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
- [ ] **Warstwa 4** — Frontend / dashboard ← **START tutaj** (najpierw 4a: endpointy portfela)

**Repo:** https://github.com/SzymekNawrocki/ScopeGain
**Układ:** monorepo — `backend/` (FastAPI) + `frontend/` (Next.js)
**Odpalenie lokalnie:**
- baza: `docker start scopegain-db`
- API: `cd backend` → `.venv\Scripts\python.exe -m uvicorn main:app --reload` → http://127.0.0.1:8000/docs
- front: `cd frontend` → `npm run dev` → http://localhost:3000

_Plik żywy — odhaczam zadania i aktualizuję w miarę postępu._
