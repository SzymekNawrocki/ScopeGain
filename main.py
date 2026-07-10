from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
import yfinance as yf

from database import get_db
from models import Portfolio
from schemas import PortfolioCreate, PortfolioRead

app = FastAPI(title="ScopeGain API")


@app.get("/health")
def health():
    return {"status": "ok"}


# {ticker} to "dziura w adresie" - to, co wpiszesz po /stock/, trafia
# do funkcji jako argument ticker (np. /stock/AAPL -> ticker = "AAPL").
@app.get("/stock/{ticker}")
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


# ------------------------------------------------------------------------
# PORTFELE (warstwa 4a)
# response_model = schemat, ktorym FastAPI FILTRUJE odpowiedz. Nawet gdy
# obiekt z bazy ma wiecej pol, klient dostanie tylko to, co w schemacie.
# ------------------------------------------------------------------------


@app.post("/portfolios", response_model=PortfolioRead, status_code=201)
def create_portfolio(dane: PortfolioCreate, db: Session = Depends(get_db)):
    # dane sa juz zwalidowane przez Pydantic (bramkarz). Tworzymy wiersz w bazie.
    portfel = Portfolio(name=dane.name)
    db.add(portfel)       # "dopisz do sesji"
    db.commit()           # "zatwierdz w bazie" (dopiero teraz trafia na dysk)
    db.refresh(portfel)   # dociagnij id, ktore nadala baza
    return portfel


@app.get("/portfolios", response_model=list[PortfolioRead])
def list_portfolios(db: Session = Depends(get_db)):
    # select(...) buduje zapytanie; scalars().all() zwraca liste obiektow.
    return db.scalars(select(Portfolio)).all()
