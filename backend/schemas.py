from pydantic import BaseModel, Field

# ------------------------------------------------------------------------
# Schematy Pydantic = "kontrakt" API. Opisuja ksztalt danych NA GRANICY
# aplikacji (co klient przysyla, co mu oddajemy). To NIE to samo co modele
# SQLAlchemy z models.py, ktore opisuja tabele w bazie.
# ------------------------------------------------------------------------


# --- AUTH (warstwa 5) ---

# Rejestracja/logowanie: to, co klient PRZYSYLA. Haslo min. 8 znakow -
# prosta bariera; Pydantic odrzuci krotsze, zanim dotkniemy bazy.
class UserCredentials(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


# To, co ODDAJEMY: nigdy hasla ani hasha - tylko id i email.
class UserRead(BaseModel):
    id: int
    email: str

    model_config = {"from_attributes": True}


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


# --- WYCENA (warstwa 6: quant) ---
# Te schematy NIE lustrza tabeli - to policzony wynik. Pola "| None" bo cena
# rynkowa moze byc niedostepna (np. wycofana spolka) - wtedy wyceny nie liczymy.

class PositionValuation(BaseModel):
    id: int
    ticker: str
    quantity: float
    buy_price: float          # cena zakupu (koszt wejscia na sztuke)
    current_price: float | None   # ostatnia cena rynkowa
    cost_basis: float         # ile wydano: ilosc * cena zakupu
    market_value: float | None    # ile warte dzis: ilosc * cena rynkowa
    pnl_abs: float | None     # zysk/strata w $ (market_value - cost_basis)
    pnl_pct: float | None     # zysk/strata w % wzgledem kosztu


class PortfolioValuation(BaseModel):
    id: int
    name: str
    positions: list[PositionValuation]
    total_cost: float         # suma kosztow wejscia (tylko wycenione pozycje)
    total_value: float        # suma wartosci rynkowej
    total_pnl_abs: float      # laczny zysk/strata BRUTTO w $
    total_pnl_pct: float      # laczny zysk/strata BRUTTO w %
    # --- P&L netto (warstwa 12a): ile REALNIE zostaje w kieszeni ---
    total_commission: float   # prowizja maklerska - kupno + (hipotetyczna) sprzedaz dzis
    total_tax_belka: float    # podatek od zyskow kapitalowych, 19% (tylko od zysku)
    total_pnl_net_abs: float  # zysk/strata NETTO w $ (brutto - prowizje - podatek)
    total_pnl_net_pct: float  # zysk/strata NETTO w %
