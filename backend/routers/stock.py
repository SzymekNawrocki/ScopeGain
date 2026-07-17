from typing import Literal

from fastapi import APIRouter, HTTPException, Path, Query
import pandas as pd
import yfinance as yf

from analysis import build_stock_verdict
from market import (
    BENCHMARK,
    MarketUnavailable,
    close_series,
    company_profile,
    search_companies,
)
from quant import (
    annualized_volatility_pct,
    daily_returns,
    max_drawdown_pct,
    total_return_pct,
)
from schemas import StockProfile, StockSearchHit, StockVerdict

# APIRouter = "mini-aplikacja" z wlasnymi trasami. Endpointy pisze sie na
# router, a nie na app. tags=[...] grupuje te trasy w /docs pod naglowkiem.
router = APIRouter(tags=["stock"])

# Realne symbole to nie tylko litery: BRK.B (klasa akcji), CCO.TO (Toronto),
# U-UN.TO (unit trust), ^GSPC (indeks). Sam [A-Z]+ zepsulby cross-listing.
TICKER_RE = r"^[A-Za-z0-9.\-^]{1,15}$"

# Zrodlo (Yahoo) jest darmowe i nieoficjalne - przy limicie zapytan odmawia.
# To stan PRZEJSCIOWY, wiec 503 + "sprobuj za chwile", a nie 404 ("nie ma
# spolki") ani 500 ("apka zepsuta").
_ODMOWA = "Zrodlo danych chwilowo odmawia (limit zapytan). Sprobuj za chwile."


# Podpowiedzi do wyszukiwarki: szukanie spolki PO NAZWIE, nie po symbolu.
# To zdejmuje z usera obowiazek znania symbolu na pamiec ("cameco" -> CCJ).
#
# UWAGA na granice tego zrodla: szukanie po nazwie dziala, ale TEMATYCZNE jest
# dziurawe - Search("uranium") nie zwraca Cameco, mimo ze profil CCJ mowi
# industry="Uranium". Dlatego tu wystawiamy tylko szukanie po nazwie; tematy
# maja dostac wlasny, kuratorowany mechanizm (ADR-0002).
@router.get("/stock/search", response_model=list[StockSearchHit])
def stock_search(
    # min_length=2: jednoznakowe zapytanie to setki bezuzytecznych trafien i
    # niepotrzebny strzal do Yahoo przy kazdym wcisnietym klawiszu.
    q: str = Query(min_length=2, max_length=50, description="Nazwa lub symbol"),
):
    try:
        return search_companies(q.strip())
    except MarketUnavailable:
        raise HTTPException(status_code=503, detail=_ODMOWA)


# Profil: czym ta spolka JEST (sektor, branza, opis) + fundamenty.
# Bez 'period' - fundamenty nie zaleza od zakresu wykresu. Gdyby profil byl
# sklejony z werdyktem, trzymalibysmy go pod kluczem z period i robili 5x
# wiecej strzalow w wolne .info.
@router.get("/stock/{ticker}/profile", response_model=StockProfile)
def stock_profile(ticker: str = Path(pattern=TICKER_RE)):
    try:
        profil = company_profile(ticker)
    except MarketUnavailable:
        raise HTTPException(status_code=503, detail=_ODMOWA)

    if profil is None:
        raise HTTPException(
            status_code=404,
            detail=f"Nie znaleziono spolki '{ticker}'. Sprawdz symbol.",
        )
    return profil


# Werdykt RYZYKA. Nie mowi "kup/sprzedaj" (ADR-0001) - mowi, czym ryzykujesz.
@router.get("/stock/{ticker}/verdict", response_model=StockVerdict)
def stock_verdict(
    ticker: str = Path(pattern=TICKER_RE),
    period: Literal["1mo", "3mo", "6mo", "1y", "5y"] = "6mo",
):
    close = close_series(ticker, period)
    if close.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Nie znaleziono spolki '{ticker}'. Sprawdz symbol.",
        )

    bench = close_series(BENCHMARK, period)

    # Profil jest DODATKIEM: gdy zrodlo odmowi fundamentow, nadal mamy metryki
    # policzone z cen. Werdykt wtedy leci dalej z mniejsza liczba regul i
    # mowi o tym wprost w data_gaps - zamiast wywalac cala trase (503).
    try:
        profil = company_profile(ticker) or {}
    except MarketUnavailable:
        profil = {}

    return build_stock_verdict(
        ticker=ticker,
        bench_label=BENCHMARK,
        volatility_pct=annualized_volatility_pct(daily_returns(close)),
        bench_vol=annualized_volatility_pct(daily_returns(bench)) if not bench.empty else 0.0,
        max_drawdown_pct=max_drawdown_pct(close),
        beta=profil.get("beta"),
        trailing_pe=profil.get("trailing_pe"),
        profit_margins=profil.get("profit_margins"),
    ) | {"period": period}


# Historia swiec (OHLC) do wykresu. Lightweight Charts na froncie oczekuje
# listy obiektow { time, open, high, low, close } - dokladnie to tu budujemy.
# period: Literal = FastAPI sam odrzuci zla wartosc (422), zanim wejdziemy w kod.
@router.get("/stock/{ticker}/history")
def stock_history(
    ticker: str,
    period: Literal["1mo", "3mo", "6mo", "1y", "5y"] = "6mo",
):
    dane = yf.download(
        ticker, period=period, interval="1d", progress=False, auto_adjust=True
    )

    if dane.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Nie znaleziono spolki '{ticker}'. Sprawdz symbol.",
        )

    # Przy JEDNEJ spolce yfinance oddaje "pietrowe" kolumny (MultiIndex):
    # ('Close', 'AAPL'). Splaszczamy do zwyklego 'Close', 'Open', ...,
    # zeby moc czytac wiersz po wierszu.
    if isinstance(dane.columns, pd.MultiIndex):
        dane.columns = dane.columns.get_level_values(0)

    # Kazdy wiersz tabeli -> jedna swieca. Index wiersza to data sesji.
    swiece = [
        {
            "time": data.strftime("%Y-%m-%d"),
            "open": round(float(wiersz["Open"]), 2),
            "high": round(float(wiersz["High"]), 2),
            "low": round(float(wiersz["Low"]), 2),
            "close": round(float(wiersz["Close"]), 2),
        }
        for data, wiersz in dane.iterrows()
    ]

    return {"ticker": ticker.upper(), "period": period, "candles": swiece}


# Metryki quant dla spolki + porownanie z rynkiem (S&P 500).
# To zbiera cala warstwe 6 w jeden wynik: zwrot (backtest), ryzyko
# (zmiennosc, drawdown) i "ja vs rynek" (alpha = zwrot ponad rynek).
@router.get("/stock/{ticker}/metrics")
def stock_metrics(
    ticker: str,
    period: Literal["1mo", "3mo", "6mo", "1y", "5y"] = "6mo",
):
    close = close_series(ticker, period)
    if close.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Nie znaleziono spolki '{ticker}'. Sprawdz symbol.",
        )

    zwrot = total_return_pct(close)

    # Rynek za ten sam okres. Gdyby benchmark sie nie pobral, nie wywalamy
    # calego endpointu - po prostu oddajemy null (spolka i tak ma metryki).
    bench = close_series(BENCHMARK, period)
    bench_zwrot = total_return_pct(bench) if not bench.empty else None
    alpha = round(zwrot - bench_zwrot, 2) if bench_zwrot is not None else None

    return {
        "ticker": ticker.upper(),
        "period": period,
        "return_pct": round(zwrot, 2),
        "volatility_pct": round(annualized_volatility_pct(daily_returns(close)), 2),
        "max_drawdown_pct": round(max_drawdown_pct(close), 2),
        "benchmark": {
            "ticker": BENCHMARK,
            "return_pct": round(bench_zwrot, 2) if bench_zwrot is not None else None,
        },
        "alpha_pct": alpha,  # nadwyzka nad rynkiem (dodatnia = bijesz rynek)
    }
