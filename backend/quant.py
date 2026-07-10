"""Serce projektu: obliczenia finansowe - CZYSTE funkcje na pandas/numpy.

Zadnego FastAPI, zadnego yfinance. Wejscie: szereg cen (pandas Series).
Wyjscie: liczba. Dzieki temu kazda metryke da sie przetestowac w izolacji
(podajesz recznie ceny, sprawdzasz wynik) i wyjasnic na rozmowie "co i czemu".

252 = typowa liczba dni sesyjnych w roku (do 'zrocznienia' metryk dziennych).
"""

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def daily_returns(close: pd.Series) -> pd.Series:
    """Dzienne zwroty procentowe: (dzis - wczoraj) / wczoraj.

    pct_change() liczy to dla calej serii; pierwszy dzien nie ma "wczoraj",
    wiec wychodzi NaN - odrzucamy go przez dropna().
    """
    return close.pct_change().dropna()


def total_return_pct(close: pd.Series) -> float:
    """Zwrot za CALY okres: o ile % urosla cena od pierwszego do ostatniego dnia.

    To jest backtest "gdybym kupil na poczatku okresu, mam +Y%".
    """
    return float((close.iloc[-1] / close.iloc[0] - 1) * 100)


def annualized_volatility_pct(returns: pd.Series) -> float:
    """Zmiennosc (ryzyko): jak bardzo zwroty skacza wokol sredniej.

    Odchylenie standardowe dziennych zwrotow * sqrt(252) = wersja roczna.
    Wieksza liczba = dziksze wahania = wieksze ryzyko.
    """
    return float(returns.std() * np.sqrt(TRADING_DAYS) * 100)


def max_drawdown_pct(close: pd.Series) -> float:
    """Najwieksze obsuniecie od szczytu do pozniejszego dolka (liczba ujemna).

    cummax() = najwyzszy dotychczasowy szczyt na kazdy dzien. Cena / szczyt - 1
    mowi, jak gleboko jestesmy pod ostatnim szczytem. Bierzemy najgorszy punkt.
    Odpowiada na "ile bym maksymalnie stracil, gdybym kupil na gorce".
    """
    szczyt = close.cummax()
    obsuniecie = close / szczyt - 1
    return float(obsuniecie.min() * 100)
