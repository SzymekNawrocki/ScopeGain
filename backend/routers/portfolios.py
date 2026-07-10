from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from market import latest_prices
from models import Portfolio, Position
from schemas import (
    PortfolioCreate,
    PortfolioRead,
    PortfolioValuation,
    PositionCreate,
    PositionRead,
    PositionValuation,
)

# prefix="/portfolios" -> wszystkie trasy ponizej dostaja ten przedrostek,
# wiec w srodku podajemy juz tylko koncowki ("" = samo /portfolios).
router = APIRouter(prefix="/portfolios", tags=["portfolios"])


# response_model = schemat, ktorym FastAPI FILTRUJE odpowiedz. Nawet gdy
# obiekt z bazy ma wiecej pol, klient dostanie tylko to, co w schemacie.
@router.post("", response_model=PortfolioRead, status_code=201)
def create_portfolio(dane: PortfolioCreate, db: Session = Depends(get_db)):
    # dane sa juz zwalidowane przez Pydantic (bramkarz). Tworzymy wiersz w bazie.
    portfel = Portfolio(name=dane.name)
    db.add(portfel)       # "dopisz do sesji"
    db.commit()           # "zatwierdz w bazie" (dopiero teraz trafia na dysk)
    db.refresh(portfel)   # dociagnij id, ktore nadala baza
    return portfel


@router.get("", response_model=list[PortfolioRead])
def list_portfolios(db: Session = Depends(get_db)):
    # select(...) buduje zapytanie; scalars().all() zwraca liste obiektow.
    return db.scalars(select(Portfolio)).all()


# Zywa wycena portfela: bierze pozycje z bazy, dociaga aktualne ceny z rynku
# i liczy zysk/strate. To pierwszy prawdziwy "quant" - laczy DANE (baza) z
# RYNKIEM (yfinance) w policzony wynik, ktorego nie ma w zadnej tabeli.
@router.get("/{portfolio_id}/valuation", response_model=PortfolioValuation)
def portfolio_valuation(portfolio_id: int, db: Session = Depends(get_db)):
    portfel = db.get(Portfolio, portfolio_id)
    if portfel is None:
        raise HTTPException(
            status_code=404,
            detail=f"Nie ma portfela o id {portfolio_id}.",
        )

    # Jeden strzal po ceny wszystkich spolek z portfela (nie w petli!).
    ceny = latest_prices([p.ticker for p in portfel.positions])

    pozycje_out: list[PositionValuation] = []
    total_cost = 0.0
    total_value = 0.0

    for p in portfel.positions:
        # Z bazy quantity/buy_price przychodza jako Decimal - na float do liczenia.
        ilosc = float(p.quantity)
        cena_zakupu = float(p.buy_price)
        koszt = ilosc * cena_zakupu

        cena_teraz = ceny.get(p.ticker.upper())
        if cena_teraz is not None:
            wartosc = ilosc * cena_teraz
            zysk = wartosc - koszt
            zysk_pct = (zysk / koszt * 100) if koszt else 0.0
            # Do sum bierzemy tylko pozycje z ZNANA cena - inaczej % bylby fałszywy.
            total_cost += koszt
            total_value += wartosc
        else:
            wartosc = zysk = zysk_pct = None

        pozycje_out.append(
            PositionValuation(
                id=p.id,
                ticker=p.ticker,
                quantity=ilosc,
                buy_price=round(cena_zakupu, 2),
                current_price=round(cena_teraz, 2) if cena_teraz is not None else None,
                cost_basis=round(koszt, 2),
                market_value=round(wartosc, 2) if wartosc is not None else None,
                pnl_abs=round(zysk, 2) if zysk is not None else None,
                pnl_pct=round(zysk_pct, 2) if zysk_pct is not None else None,
            )
        )

    zysk_total = total_value - total_cost
    zysk_total_pct = (zysk_total / total_cost * 100) if total_cost else 0.0

    return PortfolioValuation(
        id=portfel.id,
        name=portfel.name,
        positions=pozycje_out,
        total_cost=round(total_cost, 2),
        total_value=round(total_value, 2),
        total_pnl_abs=round(zysk_total, 2),
        total_pnl_pct=round(zysk_total_pct, 2),
    )


@router.post(
    "/{portfolio_id}/positions",
    response_model=PositionRead,
    status_code=201,
)
def add_position(
    portfolio_id: int,               # z adresu: do ktorego portfela dopisujemy
    dane: PositionCreate,            # z tresci: jaka spolka, ile, po ile
    db: Session = Depends(get_db),
):
    # Najpierw sprawdzamy, czy portfel w ogole istnieje. Bez tego proba
    # zapisu wybuchlaby brzydko na kluczu obcym (500). Wolimy grzeczne 404.
    portfel = db.get(Portfolio, portfolio_id)
    if portfel is None:
        raise HTTPException(
            status_code=404,
            detail=f"Nie ma portfela o id {portfolio_id}.",
        )

    pozycja = Position(
        ticker=dane.ticker.upper(),
        quantity=dane.quantity,
        buy_price=dane.buy_price,
        portfolio_id=portfolio_id,   # spinamy pozycje z portfelem (klucz obcy)
    )
    db.add(pozycja)
    db.commit()
    db.refresh(pozycja)
    return pozycja
