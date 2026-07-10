"""Dostep do danych rynkowych (yfinance) - ODDZIELONY od API i od obliczen.

Po co osobny plik? Zeby zrodlo danych bylo w jednym miejscu: routery pytaja
"daj cene", a nie wiedza, ze pod spodem jest yfinance. Jak kiedys zmienimy
dostawce danych, ruszamy tylko ten plik. To tez ulatwia testy (mozna podmienic).
"""

import pandas as pd
import yfinance as yf


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
