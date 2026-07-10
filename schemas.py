from pydantic import BaseModel, Field

# ------------------------------------------------------------------------
# Schematy Pydantic = "kontrakt" API. Opisuja ksztalt danych NA GRANICY
# aplikacji (co klient przysyla, co mu oddajemy). To NIE to samo co modele
# SQLAlchemy z models.py, ktore opisuja tabele w bazie.
# ------------------------------------------------------------------------


# --- POZYCJA ---

# To, co klient PRZYSYLA, tworzac pozycje. Brak "id" i "portfolio_id" -
# baza nada id sama, a portfel wynika z adresu/kontekstu.
class PositionCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=10)
    quantity: float = Field(gt=0)      # gt=0 -> musi byc wieksze od zera
    buy_price: float = Field(gt=0)


# To, co ODDAJEMY klientowi. Ma juz "id" nadane przez baze.
class PositionRead(BaseModel):
    id: int
    ticker: str
    quantity: float
    buy_price: float

    # Pozwala Pydanticowi zbudowac ten schemat wprost z obiektu SQLAlchemy
    # (czytajac .id, .ticker itd.), a nie tylko ze slownika.
    model_config = {"from_attributes": True}


# --- PORTFEL ---

# To, co klient PRZYSYLA, tworzac portfel. Tylko nazwa - reszta to sprawa bazy.
class PortfolioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


# To, co ODDAJEMY: portfel z id i z lista jego pozycji.
class PortfolioRead(BaseModel):
    id: int
    name: str
    positions: list[PositionRead] = []

    model_config = {"from_attributes": True}
