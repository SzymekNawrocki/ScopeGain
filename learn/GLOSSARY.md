# ScopeGain Glossary

Kanoniczny język tego workspace'u. Pojęcia z warstw 1–4, których użyłeś poprawnie w
praktyce. Definicje mówią czym coś JEST, nie jak to zrobić.

## Terms

**Endpoint**:
Pojedynczy adres w API (metoda + ścieżka, np. `GET /portfolios`), pod który klient wysyła
żądanie i dostaje odpowiedź.
_Avoid_: url, route (route = wzorzec ścieżki; endpoint = konkretne wejście)

**Router (APIRouter)**:
Zestaw powiązanych endpointów wydzielony do osobnego pliku, wpinany do głównej aplikacji
jednym `include_router`. Dzieli monolit na tematy.
_Avoid_: kontroler

**Schemat (Pydantic)**:
Opis kształtu danych **na granicy API** — co klient przysyła i co dostaje. Waliduje wejście
automatycznie (złe dane → `422`). Osobny od modelu bazy.
_Avoid_: model, DTO

**Model (SQLAlchemy)**:
Opis kształtu danych **w bazie** — tabela, kolumny, klucze. Klasa mapowana na wiersze.
_Avoid_: schemat (to co innego — patrz wyżej)

**ORM**:
Warstwa, która pozwala pisać zapytania do bazy w Pythonie (obiekty) zamiast w surowym SQL.
SQLAlchemy to nasz ORM.

**Migracja (Alembic)**:
Wersjonowana zmiana schematu bazy (dodanie tabeli, kolumny). Jak "commit" dla struktury bazy.

**Sesja (DB session)**:
Jedna "rozmowa" z bazą w obrębie żądania. Otwierana i **zamykana** per-request przez `get_db`.

**Dependency injection (`Depends`)**:
Mechanizm FastAPI: endpoint deklaruje czego potrzebuje (np. sesji bazy), a framework mu to
dostarcza i sprząta po nim. Stąd `db: Session = Depends(get_db)`.

**CORS**:
Reguła **przeglądarki**: blokuje `fetch` między różnymi pochodzeniami (port/host/protokół),
dopóki serwer nagłówkiem nie powie "ufam temu frontowi". Nie dotyczy żądań serwer→serwer.
_Avoid_: blokada CORS-a jako "błąd backendu" (to celowa ochrona przeglądarki)

**Pochodzenie (origin)**:
Trójka protokół + host + port (np. `http://localhost:3000`). Inny port = inne pochodzenie.

**Client Component (`"use client"`)**:
Komponent React renderowany/uruchamiany w przeglądarce — może używać `useState`/`useEffect`
i to on strzela `fetch` (dlatego wchodzi CORS).
_Avoid_: komponent kliencki vs serwerowy myląco — trzymamy angielskie nazwy

**Design token**:
Nazwana wartość stylu (kolor, cień, font) trzymana w jednym miejscu (zmienne CSS), z której
korzysta cały interfejs. Zmiana w jednym miejscu → zmiana wszędzie.

**Kod HTTP**:
Liczba w odpowiedzi mówiąca jak poszło: `200` OK, `201` utworzono, `404` nie ma, `422`
walidacja odrzuciła, `500` serwer się wywalił.

## Terms — warstwa ryzyka (VaR / stress)

**VaR (Value at Risk)**:
Próg straty, którego z danym prawdopodobieństwem NIE przekroczysz w danym horyzoncie
(np. „z 95% pewnością dzienny wynik nie będzie gorszy niż −2,7%"). Liczony METODĄ
HISTORYCZNĄ: percentyl realnych zwrotów portfela — bez zakładania rozkładu normalnego.
_Avoid_: „maksymalna strata" (VaR mówi o progu, nie o najgorszym możliwym scenariuszu).

**CVaR (Conditional VaR / expected shortfall)**:
Średnia strata w ogonie POZA progiem VaR — „a jak już jest źle, to średnio ile".
Domykamy nim VaR, który sam usypia („95% OK" nie mówi, co w tych 5%).
_Avoid_: mylenie z VaR — VaR to granica ogona, CVaR to jego głębokość.

**Stress test**:
Odtworzenie realnego krachu (2008, COVID) na DZISIEJSZYM portfelu — „gdyby się
powtórzyło, −X%". Nie prognoza, tylko replay historii.

**Pokrycie (stress)**:
Ile spółek policzono z REALNYCH danych z krachu, a ile przez PROXY (beta × spadek
indeksu), bo nie istniały wtedy. Raportowane jawnie — o uczciwość wyniku.

**Backtest hipotetyczny (dzisiejsze wagi)**:
Krzywa „ja vs rynek" rzutuje dzisiejsze ilości na cały okres (brak logu transakcji) —
to hipoteza „gdybym od początku trzymał to, co mam dziś", nie realna ścieżka.
Oznaczona jako hipotetyczna. Prawdziwa naprawa = log transakcji (warstwa 12b).
