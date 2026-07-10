from typing import Literal

from fastapi import APIRouter, HTTPException
import pandas as pd
import yfinance as yf

from market import close_series
from quant import (
    annualized_volatility_pct,
    daily_returns,
    max_drawdown_pct,
    total_return_pct,
)

# S&P 500 przez ETF SPY - nasz "rynek", do ktorego porownujemy spolke.
BENCHMARK = "SPY"

# APIRouter = "mini-aplikacja" z wlasnymi trasami. Endpointy pisze sie na
# router, a nie na app. tags=[...] grupuje te trasy w /docs pod naglowkiem.
router = APIRouter(tags=["stock"])


# {ticker} to "dziura w adresie" - to, co wpiszesz po /stock/, trafia
# do funkcji jako argument ticker (np. /stock/AAPL -> ticker = "AAPL").
@router.get("/stock/{ticker}")
def stock_return(ticker: str):
    dane = yf.download(ticker, period="1mo", interval="1d", progress=False)

    # Zla spolka -> yfinance oddaje pusta tabele. Zamiast sie wywalic (500),
    # grzecznie mowimy klientowi "404, nie ma takiej spolki".
    if dane.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Nie znaleziono spolki '{ticker}'. Sprawdz symbol.",
        )

    zamkniecia = dane["Close"]
    cena_poczatkowa = zamkniecia.iloc[0].item()
    cena_koncowa = zamkniecia.iloc[-1].item()
    zwrot = (cena_koncowa - cena_poczatkowa) / cena_poczatkowa

    # Zwracamy slownik - FastAPI zamieni go na JSON dla klienta.
    return {
        "ticker": ticker.upper(),
        "start_price": round(cena_poczatkowa, 2),
        "end_price": round(cena_koncowa, 2),
        "return_pct": round(zwrot * 100, 2),
    }


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
