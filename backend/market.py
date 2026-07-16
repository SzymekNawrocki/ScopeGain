"""Dostep do danych rynkowych (yfinance) - ODDZIELONY od API i od obliczen.

Po co osobny plik? Zeby zrodlo danych bylo w jednym miejscu: routery pytaja
"daj cene", a nie wiedza, ze pod spodem jest yfinance. Jak kiedys zmienimy
dostawce danych, ruszamy tylko ten plik. To tez ulatwia testy (mozna podmienic).
"""

import requests
import pandas as pd
import yfinance as yf

# S&P 500 przez ETF SPY - nasz "rynek", do ktorego porownujemy wyniki.
BENCHMARK = "SPY"

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
