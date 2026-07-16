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


# --- Realna sciezka portfela z LOGU TRANSAKCJI (uczciwosc) ------------------
# Backtest "ja vs rynek" rzutuje DZISIEJSZE wagi na cala historie - to hipoteza.
# Majac log kupna/sprzedazy (12b) da sie odtworzyc, co NAPRAWDE trzymalo sie
# kazdego dnia, i policzyc uczciwa krzywa. Zwroty liczymy metoda TWR
# (time-weighted): na dniu z transakcja neutralizujemy przeplyw gotowki, zeby
# dokupienie nie wygladalo jak "zysk" - dopiero to jest porownywalne z rynkiem.

def holdings_timeline(transactions: list[dict], dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Ile sztuk KAZDEJ spolki trzymalo sie w kazdym dniu (skumulowany log).

    transactions: [{ticker, side ('BUY'/'SELL'), quantity, executed_at}]. Dla
    kazdej transakcji dodajemy (+kupno / -sprzedaz) do wszystkich dni od jej
    daty wzwyz. Wynik: tabela dni x tickery z liczba posiadanych sztuk.
    """
    tickery = sorted({t["ticker"].upper() for t in transactions})
    hold = pd.DataFrame(0.0, index=dates, columns=tickery)
    for tx in transactions:
        znak = 1.0 if tx["side"].upper() == "BUY" else -1.0
        d = pd.Timestamp(tx["executed_at"])
        hold.loc[hold.index >= d, tx["ticker"].upper()] += znak * float(tx["quantity"])
    return hold


def twr_index(values: pd.Series, flows: pd.Series) -> pd.Series:
    """Krzywa time-weighted (indeks od 100), odporna na przeplywy gotowki.

    values V_t = wartosc trzymanych pozycji na zamknieciu dnia t. flows CF_t =
    gotowka wlozona(+)/wyjeta(-) tego dnia (po cenach zamkniecia). Zwrot dnia:
    r_t = (V_t - CF_t) / V_{t-1} - 1 - odejmujemy przeplyw, wiec liczy sie tylko
    ruch RYNKU, nie Twoje wplaty. Start = pierwszy dzien z niezerowa pozycja.
    """
    v = values.to_numpy(dtype=float)
    cf = flows.reindex(values.index).fillna(0.0).to_numpy(dtype=float)
    daty, poziomy = [], []
    poziom, prev, started = 100.0, None, False
    for i in range(len(v)):
        if not started:
            if v[i] > 0:                       # pierwszy dzien z pozycja = baza 100
                started, prev = True, v[i]
                daty.append(values.index[i]); poziomy.append(100.0)
            continue
        if prev and prev > 0:
            poziom *= (1 + (v[i] - cf[i]) / prev - 1)
        daty.append(values.index[i]); poziomy.append(round(poziom, 4))
        prev = v[i]
    return pd.Series(poziomy, index=pd.DatetimeIndex(daty))


def reconcile_holdings(
    log_net: dict[str, float],
    positions_net: dict[str, float],
    tol: float = 1e-4,
) -> dict:
    """Czy netto z logu transakcji zgadza sie z obecnymi pozycjami?

    Zrodlo prawdy dla sciezki = log, ale pozycje mowia "ile mam teraz". Gdy sie
    rozjezdzaja (user nie zalogowal wszystkiego), apka musi to POWIEDZIEC, a nie
    udawac. Zwraca {reconciled, discrepancies:[{ticker, log, positions, diff}]}.
    """
    tickery = set(log_net) | set(positions_net)
    rozjazdy = []
    for t in sorted(tickery):
        l = float(log_net.get(t, 0.0))
        p = float(positions_net.get(t, 0.0))
        if abs(l - p) > tol:
            rozjazdy.append({"ticker": t, "log": round(l, 4),
                             "positions": round(p, 4), "diff": round(l - p, 4)})
    return {"reconciled": len(rozjazdy) == 0, "discrepancies": rozjazdy}


# --- Rebalansing (warstwa 12c): jak daleko od rownych wag + koszt ruchu -----
# NIE robo-doradca (patrz ADR-0001) - to PUNKT ODNIESIENIA: rowne wagi (1/N)
# jako neutralna miara koncentracji, plus uczciwy koszt domkniecia rozjazdu.

def rebalance_plan(
    holdings: dict[str, float],
    target_weights: dict[str, float] | None = None,
) -> list[dict]:
    """Plan wyrownania portfela do wag docelowych (domyslnie rowne wagi 1/N).

    holdings = {ticker: dzisiejsza wartosc pozycji}. Dla kazdej spolki liczy:
    obecna waga, docelowa waga, dryf (pp, + = przewazona) i kwote do ruchu
    (+ dokup / - przytnij). Suma trade_value ~ 0 (przesuwamy w obrebie portfela).
    To miara "jak daleko od rownego rozlozenia", nie porada co kupic/sprzedac.
    """
    total = sum(holdings.values())
    if total <= 0:
        return []
    n = len(holdings)
    plan: list[dict] = []
    for t, val in holdings.items():
        cur_w = val / total
        tgt_w = (target_weights.get(t, 0.0) if target_weights else 1.0 / n)
        plan.append({
            "ticker": t,
            "current_value": round(val, 2),
            "current_weight_pct": round(cur_w * 100, 2),
            "target_weight_pct": round(tgt_w * 100, 2),
            "drift_pp": round((cur_w - tgt_w) * 100, 2),   # + przewazona / - niedowazona
            "trade_value": round(tgt_w * total - val, 2),  # + dokup / - przytnij
        })
    return plan


def estimate_rebalance_cost(
    legs: list[dict],
    commission_pct: float = BROKER_COMMISSION_PCT,
    tax_pct: float = BELKA_TAX_PCT,
) -> dict[str, float]:
    """Ile kosztuje WYKONANIE rebalansu: prowizja od kazdego ruchu + Belka od
    zrealizowanego zysku na SPRZEDAWANYCH czesciach.

    leg = {trade_value (+dokup/-przytnij), market_value, cost_basis}. Prowizja
    liczona od |trade_value| (kupno i sprzedaz kosztuja). Przy przycinaniu
    realizuje sie PROPORCJONALNY zysk pozycji: (|trade|/wartosc)*(wartosc-koszt);
    Belka tylko od dodatniego. To pokazuje, ze rebalansing NIE jest darmowy.
    """
    prowizja = 0.0
    podatek = 0.0
    for leg in legs:
        tv = float(leg["trade_value"])
        prowizja += abs(tv) * commission_pct / 100
        mv = float(leg.get("market_value") or 0.0)
        if tv < 0 and mv > 0:                      # sprzedaz -> mozliwy podatek
            frac = min(1.0, abs(tv) / mv)
            zysk = frac * (mv - float(leg["cost_basis"]))
            podatek += max(0.0, zysk) * tax_pct / 100
    return {
        "commission": round(prowizja, 2),
        "tax_belka": round(podatek, 2),
        "total_cost": round(prowizja + podatek, 2),
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
