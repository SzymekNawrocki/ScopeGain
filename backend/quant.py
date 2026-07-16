"""Serce projektu: obliczenia finansowe - CZYSTE funkcje na pandas/numpy.

Zadnego FastAPI, zadnego yfinance. Wejscie: szereg cen (pandas Series).
Wyjscie: liczba. Dzieki temu kazda metryke da sie przetestowac w izolacji
(podajesz recznie ceny, sprawdzasz wynik) i wyjasnic na rozmowie "co i czemu".

252 = typowa liczba dni sesyjnych w roku (do 'zrocznienia' metryk dziennych).
"""

import numpy as np
import pandas as pd

TRADING_DAYS = 252

# Zalozenia Warstwy 12a: typowa prowizja maklerska (np. XTB - 0,29% od
# wartosci transakcji) i polski podatek od zyskow kapitalowych (Belka, 19%).
BROKER_COMMISSION_PCT = 0.29
BELKA_TAX_PCT = 19.0


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


def net_pnl(
    cost_basis: float,
    market_value: float,
    commission_pct: float = BROKER_COMMISSION_PCT,
    tax_pct: float = BELKA_TAX_PCT,
) -> dict[str, float]:
    """Ile REALNIE zostaje w kieszeni: brutto pomniejszone o prowizje i Belke.

    Prowizja placi sie DWA razy - raz przy kupnie (juz poniesiona, ale nie
    widac jej w cost_basis), raz przy (hipotetycznej) sprzedazy dzis. Podatek
    Belka liczy sie od zysku PO odjeciu obu prowizji, i tylko gdy ten zysk
    jest dodatni - strata nie generuje podatku (uproszczenie: bez rozliczania
    strat z innych lat).
    """
    prowizja_kupno = cost_basis * commission_pct / 100
    prowizja_sprzedaz = market_value * commission_pct / 100
    zysk_po_prowizji = (market_value - prowizja_sprzedaz) - (cost_basis + prowizja_kupno)
    podatek = max(0.0, zysk_po_prowizji) * tax_pct / 100
    netto = zysk_po_prowizji - podatek
    return {
        "commission_total": round(prowizja_kupno + prowizja_sprzedaz, 2),
        "tax_belka": round(podatek, 2),
        "net_pnl_abs": round(netto, 2),
        "net_pnl_pct": round(netto / cost_basis * 100, 2) if cost_basis else 0.0,
    }


# --- Warstwa ryzyka: VaR / CVaR / stress test ------------------------------
# VaR = "jak duzo moge stracic w normalnie zly dzien/miesiac". CVaR = "a jak
# JUZ jest zle (poza VaR), to srednio ile". Liczymy METODA HISTORYCZNA: bez
# zalozenia rozkladu normalnego - bierzemy realne zwroty portfela, wiec grube
# ogony rynku (krachy) sa w danych, a nie wygladzone przez ladny wzor.

def historical_var_pct(returns: pd.Series, confidence: float = 0.95) -> float:
    """VaR historyczny: kwantyl (1 - confidence) rozkladu dziennych zwrotow.

    Dla confidence=0.95 bierzemy 5. percentyl realnych zwrotow - prog, ponizej
    ktorego ląduje najgorsze 5% dni. Zwracamy jako % (liczba UJEMNA: strata).
    "Z 95% pewnoscia dzienny wynik nie bedzie gorszy niz ta liczba."
    """
    if returns.empty:
        return 0.0
    return float(returns.quantile(1 - confidence) * 100)


def cvar_pct(returns: pd.Series, confidence: float = 0.95) -> float:
    """CVaR (expected shortfall): srednia zwrotow GORSZYCH niz prog VaR.

    VaR mowi "gdzie zaczyna sie ogon", CVaR "jak gleboki jest ten ogon srednio"
    - dlatego dokladamy go do VaR, ktory sam usypia ("95% OK" nie mowi, co w tych
    5%). Liczba ujemna, zwykle gorsza (nizsza) niz VaR.
    """
    if returns.empty:
        return 0.0
    prog = returns.quantile(1 - confidence)
    ogon = returns[returns <= prog]
    if ogon.empty:                      # skrajnie krotka seria - brak ogona
        return float(prog * 100)
    return float(ogon.mean() * 100)


def overlapping_horizon_returns(returns: pd.Series, window: int = 21) -> pd.Series:
    """Nakladajace sie skumulowane zwroty z okna N dni (np. 21 = ~miesiac).

    Do VaR dluzszego niz 1 dzien. Uczciwiej niz mnozenie dziennego VaR przez
    sqrt(N) - to skalowanie zaklada niezalezne, normalne zwroty; rynek takich
    nie ma. Tu skladamy REALNE ciagi N kolejnych dni: (1+r).rolling(N).prod()-1.
    """
    if len(returns) < window:
        return pd.Series(dtype=float)
    skumulowane = (1 + returns).rolling(window).apply(np.prod, raw=True) - 1
    return skumulowane.dropna()


def portfolio_shock_pct(weights: dict[str, float], shocks: dict[str, float]) -> float:
    """Uderzenie w portfel = suma (waga spolki * jej szok) w %.

    Czysta arytmetyka stress testu: wagi (udzialy sumujace sie do 1) i szoki
    (zwrot spolki w oknie krachu, np. -0.55) na wejsciu, laczny procentowy
    spadek portfela na wyjsciu. Skad biora sie szoki (realna historia czy
    proxy przez bete) rozstrzyga warstwa wyzej - tu tylko liczymy.
    """
    return float(sum(weights[t] * shocks[t] for t in weights) * 100)


def max_drawdown_pct(close: pd.Series) -> float:
    """Najwieksze obsuniecie od szczytu do pozniejszego dolka (liczba ujemna).

    cummax() = najwyzszy dotychczasowy szczyt na kazdy dzien. Cena / szczyt - 1
    mowi, jak gleboko jestesmy pod ostatnim szczytem. Bierzemy najgorszy punkt.
    Odpowiada na "ile bym maksymalnie stracil, gdybym kupil na gorce".
    """
    szczyt = close.cummax()
    obsuniecie = close / szczyt - 1
    return float(obsuniecie.min() * 100)
