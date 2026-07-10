"""Serce projektu: obliczenia finansowe - CZYSTE funkcje na pandas/numpy.

Zadnego FastAPI, zadnego yfinance. Wejscie: szereg cen (pandas Series).
Wyjscie: liczba. Dzieki temu kazda metryke da sie przetestowac w izolacji
(podajesz recznie ceny, sprawdzasz wynik) i wyjasnic na rozmowie "co i czemu".

252 = typowa liczba dni sesyjnych w roku (do 'zrocznienia' metryk dziennych).
"""

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def returns_frame(closes: pd.DataFrame) -> pd.DataFrame:
    """Dzienne zwroty dla TABELI cen (wiele spolek naraz) - do korelacji.

    To samo co daily_returns, ale kolumna po kolumnie. dropna() wywala
    pierwszy dzien (bez "wczoraj") dla calej tabeli.
    """
    return closes.pct_change().dropna()


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


def sharpe_ratio(returns: pd.Series, risk_free_annual: float = 0.0) -> float:
    """Sharpe: ile zwrotu dostajesz NA JEDNOSTKE ryzyka (zroczniony).

    (sredni dzienny zwrot - stopa wolna od ryzyka) / odchylenie std, razy
    sqrt(252). Wysoki = zysk 'zdrowy'; niski = duzo bujania za maly zwrot.
    risk_free = 0 to uproszczenie MVP (realnie ~bony skarbowe).
    Regula kciuka: <1 slaby, 1-2 dobry, >2 swietny.
    """
    std = returns.std()
    if std == 0 or returns.empty:
        return 0.0
    rf_dzienna = risk_free_annual / TRADING_DAYS
    return float((returns.mean() - rf_dzienna) / std * np.sqrt(TRADING_DAYS))


def beta(asset_returns: pd.Series, market_returns: pd.Series) -> float:
    """Beta: jak mocno ruszasz sie RAZEM z rynkiem.

    kowariancja(portfel, rynek) / wariancja(rynku). 1 = jak rynek,
    >1 = mocniej (agresywniej), <1 = spokojniej, <0 = odwrotnie do rynku.
    Serie wyrownujemy po datach (dropna), bo licza sie tylko wspolne dni.
    """
    df = pd.concat([asset_returns, market_returns], axis=1).dropna()
    if len(df) < 2:
        return 0.0
    portfel, rynek = df.iloc[:, 0], df.iloc[:, 1]
    war_rynku = rynek.var()
    if war_rynku == 0:
        return 0.0
    return float(portfel.cov(rynek) / war_rynku)


def max_drawdown_pct(close: pd.Series) -> float:
    """Najwieksze obsuniecie od szczytu do pozniejszego dolka (liczba ujemna).

    cummax() = najwyzszy dotychczasowy szczyt na kazdy dzien. Cena / szczyt - 1
    mowi, jak gleboko jestesmy pod ostatnim szczytem. Bierzemy najgorszy punkt.
    Odpowiada na "ile bym maksymalnie stracil, gdybym kupil na gorce".
    """
    szczyt = close.cummax()
    obsuniecie = close / szczyt - 1
    return float(obsuniecie.min() * 100)
