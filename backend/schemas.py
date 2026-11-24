
from pydantic import BaseModel

# ------------------------------------------------------------------------
# Schematy Pydantic = "kontrakt" API. Opisuja ksztalt danych NA GRANICY
# aplikacji (co klient przysyla, co mu oddajemy). To NIE to samo co modele
# SQLAlchemy z models.py, ktore opisuja tabele w bazie.
# ------------------------------------------------------------------------


# --- SPOLKA ---

class StockSearchHit(BaseModel):
    ticker: str
    name: str
    # Gielda ROZROZNIA cross-listing: CCJ (NYSE) i CCO.TO (Toronto) to ta sama
    # firma, ale rozne papiery, waluty i metryki. Bez tego pola user nie
    # odroznilby dwoch identycznie nazwanych wynikow.
    exchange: str | None = None
    quote_type: str | None = None   # "EQUITY" | "ETF"
    sector: str | None = None
    industry: str | None = None


class StockProfile(BaseModel):
    """Czym ta spolka JEST. Bez 'period' - fundamenty nie zaleza od zakresu
    wykresu, wiec trasa jest osobna od werdyktu (i cache'owana na 12 h)."""
    ticker: str
    name: str
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = None
    trailing_pe: float | None = None
    beta: float | None = None
    profit_margins: float | None = None
    currency: str | None = None
    summary: str | None = None


