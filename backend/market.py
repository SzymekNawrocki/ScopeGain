"""Dostep do danych rynkowych (yfinance) - ODDZIELONY od API i od obliczen.

Po co osobny plik? Zeby zrodlo danych bylo w jednym miejscu: routery pytaja
"daj cene", a nie wiedza, ze pod spodem jest yfinance. Jak kiedys zmienimy
dostawce danych, ruszamy tylko ten plik. To tez ulatwia testy (mozna podmienic).
"""

import requests
import pandas as pd
import yfinance as yf
from yfinance import const as yf_const
from yfinance.exceptions import YFRateLimitError

from cache import ttl_cache

# S&P 500 przez ETF SPY - nasz "rynek", do ktorego porownujemy wyniki.
BENCHMARK = "SPY"

# Jak dlugo trzymamy dane w cache'u. Fundamenty sa wolnozmienne (sektor
# spolki nie zmieni sie do jutra), podpowiedzi tez - stad godziny, nie sekundy.
SEARCH_TTL = 60 * 60          # 1 h
PROFILE_TTL = 12 * 60 * 60    # 12 h
DISCOVER_TTL = 12 * 60 * 60   # 12 h - katalog sektorow/branz zmienia sie wolno


class MarketUnavailable(Exception):
    """Dostawca danych odmowil (limit zapytan / awaria) - to NIE jest 'brak
    takiej spolki'.

    Rozroznienie jest wazne: "nie ma spolki XYZ" to trwaly fakt (404), a
    "Yahoo chwilowo nie chce gadac" to stan przejsciowy (503, sprobuj za
    chwile). Wlasny wyjatek zamiast YFRateLimitError, zeby yfinance nie
    wyciekal do warstwy HTTP - routery lapia MarketUnavailable i nie wiedza,
    kto jest pod spodem.
    """

# Okna historycznych krachow do stress testu (data od, data do). Bierzemy
# szczyt->dolek, zeby zlapac PELNA skale spadku. Uzywane przez endpoint /risk:
# realny zwrot spolki w tym oknie = "gdyby to sie powtorzylo na moim portfelu".
CRASH_WINDOWS = {
    "gfc_2008": {"label": "Kryzys 2008 (Lehman)", "start": "2008-09-01", "end": "2009-03-09"},
    "covid_2020": {"label": "COVID-19 (III 2020)", "start": "2020-02-19", "end": "2020-03-23"},
}


# Kurs USD/PLN z NBP (tabela A, kurs sredni). Darmowe, bez klucza. Po co?
# Spolki notowane sa w USD, a Belka to podatek ZLOTOWKOWY - bez przeliczenia
# "realny zysk w kieszeni" jest polprawda.
NBP_USD_URL = "https://api.nbp.pl/api/exchangerates/rates/A/USD/?format=json"


def usd_pln_rate() -> float | None:
    """Aktualny kurs sredni USD/PLN z NBP. None, gdy NBP nie odpowie (nie
    wywalamy wyceny - front pokaze tylko USD)."""
    try:
        r = requests.get(NBP_USD_URL, timeout=5)
        r.raise_for_status()
        return float(r.json()["rates"][0]["mid"])
    except Exception:
        return None


def latest_prices(tickers: list[str]) -> dict[str, float]:
    """Ostatnia znana cena zamkniecia dla kazdej spolki.

    Jeden strzal do yfinance na WSZYSTKIE tickery naraz (szybciej niz w petli).
    Zwraca {TICKER: cena}. Spolki bez danych po prostu nie ma w wyniku.
    """
    unikalne = sorted({t.upper() for t in tickers})
    if not unikalne:
        return {}

    dane = yf.download(
        unikalne, period="5d", interval="1d", progress=False, auto_adjust=True
    )
    if dane.empty:
        return {}

    close = dane["Close"]

    # yfinance jest kaprysny: przy JEDNEJ spolce "Close" bywa Series,
    # przy wielu - DataFrame z kolumnami-tickerami. Ujednolicamy do DataFrame.
    if isinstance(close, pd.Series):
        close = close.to_frame(name=unikalne[0])

    ceny: dict[str, float] = {}
    for kolumna in close.columns:
        seria = close[kolumna].dropna()   # wywal dni bez notowania (NaN)
        if not seria.empty:
            ceny[str(kolumna).upper()] = float(seria.iloc[-1])  # ostatnia cena
    return ceny


def close_series(ticker: str, period: str = "6mo") -> pd.Series:
    """Szereg cen zamkniecia jednej spolki za dany okres (do metryk quant).

    Zwraca czysta pandas Series (bez NaN). Pusta Series = brak danych/zly ticker.
    """
    dane = yf.download(
        ticker, period=period, interval="1d", progress=False, auto_adjust=True
    )
    if dane.empty:
        return pd.Series(dtype=float)

    close = dane["Close"]
    # Przy jednej spolce "Close" bywa DataFrame z jedna kolumna - bierzemy ja.
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close.dropna()


def close_series_range(ticker: str, start: str, end: str | None = None) -> pd.Series:
    """Ceny zamkniecia jednej spolki miedzy dwiema DATAMI (nie 'period').

    Do stress testu okno krachu (start..end), do realnej sciezki - od pierwszej
    transakcji do DZIS (end=None -> yfinance ciagnie do teraz). Pusta Series =
    spolka wtedy nie istniala/brak danych (stress uzyje wtedy proxy beta x indeks).
    """
    dane = yf.download(
        ticker, start=start, end=end, interval="1d", progress=False, auto_adjust=True
    )
    if dane.empty:
        return pd.Series(dtype=float)

    close = dane["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close.dropna()


def closes_frame_range(tickers: list[str], start: str, end: str | None = None) -> pd.DataFrame:
    """Tabela cen zamkniecia WIELU spolek miedzy datami (nie 'period').

    Do realnej sciezki z logu transakcji: okres wyznacza pierwsza transakcja,
    nie staly period. W przeciwienstwie do closes_frame NIE robimy dropna po
    wszystkich kolumnach (spolki dokupione pozniej maja NaN na poczatku - to OK,
    bo wtedy i tak ich nie trzymalismy); zostawiamy wyrownanie po datach.
    """
    unikalne = sorted({t.upper() for t in tickers})
    if not unikalne:
        return pd.DataFrame()

    dane = yf.download(
        unikalne, start=start, end=end, interval="1d", progress=False, auto_adjust=True
    )
    if dane.empty:
        return pd.DataFrame()

    close = dane["Close"]
    if isinstance(close, pd.Series):
        close = close.to_frame(name=unikalne[0])
    close.columns = [str(c).upper() for c in close.columns]
    # Wywalamy tylko dni, w ktore ZADNA spolka sie nie notowala (calkowite luki).
    return close.dropna(how="all")


def closes_frame(tickers: list[str], period: str = "6mo") -> pd.DataFrame:
    """Tabela cen zamkniecia WIELU spolek, WYROWNANA po datach.

    Kolumny = tickery, wiersze = dni. dropna() zostawia tylko dni, w ktore
    notowaly sie WSZYSTKIE spolki - dzieki temu mozna je sumowac dzien po dniu
    (do wartosci portfela) bez dziur. Pusta tabela = brak danych.
    """
    unikalne = sorted({t.upper() for t in tickers})
    if not unikalne:
        return pd.DataFrame()

    dane = yf.download(
        unikalne, period=period, interval="1d", progress=False, auto_adjust=True
    )
    if dane.empty:
        return pd.DataFrame()

    close = dane["Close"]
    if isinstance(close, pd.Series):
        close = close.to_frame(name=unikalne[0])
    close.columns = [str(c).upper() for c in close.columns]
    return close.dropna()


# --- Wyszukiwanie spolek i fundamenty --------------------------------------
# Do tej pory apka umiala tylko CENY. Zeby user mogl SZUKAC spolki (a nie
# znac symbol na pamiec) i zobaczyc, czym ona w ogole jest, potrzebne sa dwa
# nowe zrodla: wyszukiwarka po nazwie i profil (sektor, branza, fundamenty).
#
# UWAGA na granice tego zrodla: szukanie po NAZWIE dziala dobrze
# (Search("cameco") -> CCJ na pierwszym miejscu), ale szukanie TEMATYCZNE
# jest dziurawe (Search("uranium") NIE zwraca Cameco - najwiekszej spolki
# uranowej swiata). Dlatego tu wystawiamy tylko szukanie po nazwie; tematy
# maja wlasny, kuratorowany mechanizm (patrz ADR-0002).

# Co pokazujemy w podpowiedziach. Bez tego filtra wlecialyby kontrakty
# terminowe, waluty i indeksy - user szuka spolki albo ETF-u.
_TYPY_W_PODPOWIEDZIACH = ("EQUITY", "ETF")


def _normalize_quote(q: dict) -> dict | None:
    """Surowy wynik z wyszukiwarki -> nasz ksztalt. CZYSTA funkcja (dict->dict).

    Wydzielona, bo to jedyne miejsce, gdzie zalezymy od nazw pol dostawcy.
    Da sie ja testowac na ZAMROZONYCH prawdziwych odpowiedziach, bez sieci i
    bez mockow - i wtedy test lapie realny blad (dostawca zmienil klucz), a
    nie zachowanie mocka.

    None = wpis do pominiecia (nie spolka/ETF albo bez symbolu).
    """
    symbol = q.get("symbol")
    if not symbol or q.get("quoteType") not in _TYPY_W_PODPOWIEDZIACH:
        return None
    return {
        # longname bywa pelniejsze ("Cameco Corporation"), shortname krotsze.
        "ticker": str(symbol).upper(),
        "name": q.get("longname") or q.get("shortname") or str(symbol),
        # Gielda rozroznia CROSS-LISTING: CCJ (NYSE) i CCO.TO (Toronto) to ta
        # sama firma, ale rozne papiery, waluty i metryki. Nie deduplikowac.
        "exchange": q.get("exchDisp") or q.get("exchange"),
        "quote_type": q.get("quoteType"),
        # Sektor i branza sa juz w wyniku wyszukiwarki - pokazemy je w
        # podpowiedziach ZA DARMO, bez dodatkowego (wolnego) strzalu w .info.
        "sector": q.get("sectorDisp") or q.get("sector"),
        "industry": q.get("industryDisp") or q.get("industry"),
    }


def _normalize_info(ticker: str, info: dict) -> dict | None:
    """Surowe .info (100+ pol) -> nasz staly ksztalt. CZYSTA funkcja.

    Nie oddajemy .info na zewnatrz: to blob o niestabilnym kontrakcie, a
    przepuszczenie go zabija sens tego modulu (routery zaczelyby znac pola
    yfinance). Wszedzie .get() - kazde pole potrafi nie przyjsc.

    None = nie ma takiej spolki.
    """
    nazwa = info.get("shortName") or info.get("longName")
    # Pusty info albo sam ticker bez nazwy i bez ceny = zly symbol.
    if not nazwa and info.get("regularMarketPrice") is None:
        return None
    return {
        "ticker": ticker.upper(),
        "name": nazwa or ticker.upper(),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "trailing_pe": info.get("trailingPE"),
        "beta": info.get("beta"),
        "profit_margins": info.get("profitMargins"),
        "currency": info.get("currency"),
        "summary": info.get("longBusinessSummary"),
    }


@ttl_cache(SEARCH_TTL)
def search_companies(query: str, limit: int = 8) -> list[dict]:
    """Podpowiedzi do wyszukiwarki: szukanie spolki PO NAZWIE lub symbolu.

    Zwraca liste [{ticker, name, exchange, quote_type, sector, industry}].
    Pusta lista = nic nie znaleziono.
    """
    try:
        # news_count/lists_count=0: domyslnie yfinance dociaga 8 newsow i 8
        # list, ktorych nie uzywamy - to darmowy narzut na kazde zapytanie.
        wynik = yf.Search(query, max_results=limit, news_count=0, lists_count=0)
        quotes = wynik.quotes or []
    except YFRateLimitError as e:
        raise MarketUnavailable("Limit zapytan do zrodla danych.") from e

    znalezione = [_normalize_quote(q) for q in quotes]
    return [z for z in znalezione if z is not None][:limit]


def _profil_wart_zapamietania(profil: dict | None) -> bool:
    """Czy ta odpowiedz wyglada na PELNA (a nie na urwana w polowie)?

    Yahoo potrafi oddac .info bez modulu profilowego: ceny i wskazniki sa,
    ale sektora, branzy, marzy i opisu juz nie. Widziane na zywo: profil
    Cameco pokazal kapitalizacje i P/E, a branze i marze jako "-". Zapisany
    na 12 h, taki ogryzek zostalby na ekranie przez pol dnia.

    Sygnal: OPIS BIZNESU. Maja go i spolki, i ETF-y - wiec jego brak znaczy
    "modul profilowy nie dojechal", a nie "to ETF". (Sektor sie nie nadaje:
    ETF-y jak URA czy SPY legalnie nie maja ani sektora, ani branzy, ani
    kapitalizacji.) None przepuszczamy - "nie ma takiej spolki" to trwaly fakt.
    """
    if profil is None:
        return True
    return bool(profil.get("summary"))


@ttl_cache(PROFILE_TTL, cache_if=_profil_wart_zapamietania)
def company_profile(ticker: str) -> dict | None:
    """Profil spolki: czym ona jest (sektor, branza, opis) + fundamenty.

    None = nie ma takiej spolki. MarketUnavailable = zrodlo odmowilo.
    Uwaga: .info NIE da sie pobrac hurtem (strzal na spolke) i bywa wolne
    (1-3 s na zimno) - stad cache na 12 h.
    """
    try:
        info = yf.Ticker(ticker).info or {}
    except YFRateLimitError as e:
        raise MarketUnavailable("Limit zapytan do zrodla danych.") from e
    except Exception:
        # yfinance przy zlym symbolu potrafi rzucic czym popadnie zamiast
        # oddac pusty dict - dla nas to po prostu "nie ma takiej spolki".
        return None

    return _normalize_info(ticker, info)


# --- Odkrywanie: przegladanie po branzy i rozbicie ETF (Etap B) -------------
# Wejscie dla kogos, kto NIE zna symbolu i chce "skategoryzowac". Uczciwosc jest
# tu twardym ograniczeniem (ADR-0002), bo zrodlo klamie przez przemilczenie:
#
#   yf.Industry("uranium").top_companies -> UEC, LEU, NUCL. CAMECO (CCJ) WYPADA,
#   mimo ze jego wlasny profil mowi industry="Uranium". `top_companies` to
#   ranking "top" od Yahoo, NIE spis branzy - i gubi lidera, tak samo jak
#   Search("uranium"). Dlatego:
#     1) NIE oddajemy kolumny `rating` ("Strong Buy"/"Buy") - to jezyk porady,
#        zakazany przez ADR-0001. Zostaje sam {ticker, name}.
#     2) Front dokleja jawne zastrzezenie ("to ranking, nie pelny spis"), a luki
#        latane sa rozbiciem ETF i szukaniem po nazwie.
#   ETF (funds_data.top_holdings) daje realny koszyk dla tematow bez branzy
#   (QTUM -> spolki "kwantowe"), tez z symbolami do dalszej kuracji.

# 11 sektorow Yahoo (zamknieta, stabilna lista). Klucz = slug do yf.Sector();
# dla tych 11 nazw wystarczy lowercase + myslnik zamiast spacji (brak "&").
_SECTOR_NAMES = list(yf_const.SECTOR_INDUSTY_MAPPING.keys())


def _sector_key(name: str) -> str:
    return name.lower().replace(" ", "-")


def browsable_sectors() -> list[dict]:
    """11 sektorow do przegladania (drill-down: sektor -> branza -> spolki).

    Bez sieci - lista jest w taksonomii yfinance. Zwraca [{key, name}].
    """
    return [{"key": _sector_key(n), "name": n} for n in _SECTOR_NAMES]


def _normalize_industries(df: pd.DataFrame) -> list[dict]:
    """DataFrame branz sektora -> [{key, name}]. CZYSTA funkcja.

    yf.Sector(...).industries: index = KLUCZ branzy ('uranium'), kolumna 'name'
    = nazwa czytelna. Klucz bierzemy z indeksu (to on idzie do yf.Industry).
    """
    if df is None or df.empty:
        return []
    out: list[dict] = []
    for key, row in df.iterrows():
        out.append({"key": str(key), "name": str(row.get("name") or key)})
    return out


def _normalize_top_companies(df: pd.DataFrame) -> list[dict]:
    """DataFrame top_companies branzy -> [{ticker, name}]. CZYSTA funkcja.

    Index = symbol. Kolumne `rating` (Strong Buy/Buy/Hold) SWIADOMIE POMIJAMY -
    to jezyk porady zakazany przez ADR-0001; niech nie wycieka z modulu.
    """
    if df is None or df.empty:
        return []
    out: list[dict] = []
    for symbol, row in df.iterrows():
        out.append({"ticker": str(symbol).upper(), "name": str(row.get("name") or symbol)})
    return out


def _normalize_holdings(df: pd.DataFrame) -> list[dict]:
    """DataFrame top_holdings ETF-u -> [{ticker, name}]. CZYSTA funkcja.

    funds_data.top_holdings: index = Symbol, kolumna 'Name'. Wagi pomijamy -
    do kuracji tematu wystarczy, kto jest w koszyku.
    """
    if df is None or df.empty:
        return []
    out: list[dict] = []
    for symbol, row in df.iterrows():
        out.append({"ticker": str(symbol).upper(), "name": str(row.get("Name") or symbol)})
    return out


@ttl_cache(DISCOVER_TTL)
def sector_industries(sector_key: str) -> list[dict]:
    """Branze w danym sektorze (drugi poziom drill-downu). [{key, name}].

    Pusta lista = zly klucz sektora / brak danych. MarketUnavailable = limit.
    """
    try:
        df = yf.Sector(sector_key).industries
    except YFRateLimitError as e:
        raise MarketUnavailable("Limit zapytan do zrodla danych.") from e
    except Exception:
        return []
    return _normalize_industries(df)


@ttl_cache(DISCOVER_TTL)
def industry_companies(industry_key: str) -> list[dict]:
    """Spolki z branzy przez yf.Industry(...).top_companies. [{ticker, name}].

    UWAGA: to ranking "top" Yahoo, NIE pelny spis - gubi liderow (CCJ przy
    uranie). Zastrzezenie dokleja front; tu tylko oddajemy, co zrodlo daje,
    bez kolumny `rating`. Pusta lista = zly klucz / brak danych.
    """
    try:
        df = yf.Industry(industry_key).top_companies
    except YFRateLimitError as e:
        raise MarketUnavailable("Limit zapytan do zrodla danych.") from e
    except Exception:
        return []
    return _normalize_top_companies(df)


@ttl_cache(DISCOVER_TTL)
def etf_holdings(etf_ticker: str) -> list[dict]:
    """Sklad ETF-u (funds_data.top_holdings) jako kandydaci. [{ticker, name}].

    Dla tematow bez branzy (kwanty -> QTUM). Pusta lista = to nie ETF / brak
    danych o skladzie. MarketUnavailable = limit zapytan.
    """
    try:
        df = yf.Ticker(etf_ticker).funds_data.top_holdings
    except YFRateLimitError as e:
        raise MarketUnavailable("Limit zapytan do zrodla danych.") from e
    except Exception:
        return []
    return _normalize_holdings(df)
