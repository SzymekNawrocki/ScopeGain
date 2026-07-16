from datetime import date
from typing import Literal

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


# --- TRANSAKCJA (warstwa 12b: log kupna/sprzedazy) ---
# Osobny byt od pozycji: pozycja = "co mam teraz", transakcja = "co zrobilem
# i kiedy". Potrzebne, zeby werdykt zachowania ocenil timing sprzedazy.

class TransactionCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=10)
    side: Literal["BUY", "SELL"]          # tylko te dwie wartosci - Pydantic pilnuje
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)            # cena za sztuke w momencie transakcji
    executed_at: date                     # dzien transakcji (YYYY-MM-DD)


class TransactionRead(BaseModel):
    id: int
    ticker: str
    side: str
    quantity: float
    price: float
    executed_at: date

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
    # --- Przeliczenie na PLN (kurs NBP) - "realnie w kieszeni" po polsku ---
    # None, gdy NBP nie odpowie. UPROSZCZENIE: kurs BIEZACY; poprawna Belka
    # liczy sie po kursie NBP z dnia przed KAZDA transakcja (front to zaznacza).
    fx_usd_pln: float | None = None       # kurs sredni USD/PLN
    total_value_pln: float | None = None  # wartosc portfela w PLN
    total_pnl_net_pln: float | None = None  # zysk/strata NETTO w PLN


# --- RYZYKO (VaR / CVaR / stress test) ---
# Policzony wynik, nie tabela. "Ile realnie moge stracic" w % I w kwocie.

class VarMeasure(BaseModel):
    confidence: float   # 0.95 lub 0.99 - poziom pewnosci
    horizon: str        # "1d" (dzien) / "1m" (~21 sesji)
    var_pct: float      # VaR w % (ujemny: strata, ktorej z danym p-stwem nie przekroczysz)
    var_abs: float      # VaR w walucie portfela (var_pct * wartosc)
    cvar_pct: float     # CVaR w % - srednia strata POZA progiem VaR (ogon)
    cvar_abs: float     # CVaR w walucie portfela


class StressScenario(BaseModel):
    key: str            # "gfc_2008" / "covid_2020"
    label: str          # ludzka nazwa krachu
    shock_pct: float    # laczne uderzenie w portfel w % (ujemne)
    pnl_abs: float      # strata w walucie portfela
    coverage_real: list[str]   # spolki policzone z REALNYCH danych z krachu
    coverage_proxy: list[str]  # spolki przez PROXY (beta x indeks) - nie zyly wtedy


class PortfolioRisk(BaseModel):
    id: int
    name: str
    window: str              # okno estymacji VaR ("1y"/"2y"/"5y")
    currency: str            # waluta kwot - dzis "USD" (spolki w dolarach, nie udajemy PLN)
    portfolio_value: float   # dzisiejsza wartosc portfela (baza kwot ryzyka)
    n_days: int              # ile dni danych stalo za VaR (wiarygodnosc okna)
    var: list[VarMeasure]
    stress: list[StressScenario]
    warning: str | None      # np. "okno to glownie hossa - VaR moze zanizac ryzyko"


# --- REBALANSING (warstwa 12c) ---
# NIE zlecenia "kup/sprzedaj" (ADR-0001) - PUNKT ODNIESIENIA: jak daleko od
# rownych wag + ile kosztowaloby domkniecie rozjazdu (prowizja + Belka).

class RebalanceLeg(BaseModel):
    ticker: str
    current_value: float
    current_weight_pct: float
    target_weight_pct: float
    drift_pp: float          # + = przewazona, - = niedowazona (punkty procentowe)
    trade_value: float       # + = dokup, - = przytnij (w walucie portfela)


class RebalanceCost(BaseModel):
    commission: float        # prowizja od wszystkich ruchow
    tax_belka: float         # podatek od zrealizowanego zysku na przycieciach
    total_cost: float        # laczny koszt wykonania rebalansu


class RebalancePlan(BaseModel):
    id: int
    name: str
    currency: str            # "USD"
    total_value: float
    target: str              # "equal" - rowne wagi jako neutralny punkt odniesienia
    legs: list[RebalanceLeg]
    cost: RebalanceCost
