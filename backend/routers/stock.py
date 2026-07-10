from fastapi import APIRouter, HTTPException
import yfinance as yf

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
