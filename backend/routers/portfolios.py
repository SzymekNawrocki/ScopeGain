from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Portfolio, Position
from schemas import PortfolioCreate, PortfolioRead, PositionCreate, PositionRead

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
