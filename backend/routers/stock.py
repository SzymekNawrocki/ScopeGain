from fastapi import APIRouter, HTTPException, Path, Query

from market import MarketUnavailable, company_profile, search_companies
from schemas import StockProfile, StockSearchHit

# APIRouter = "mini-aplikacja" z wlasnymi trasami. Bez auth: apka slucha tylko
# na 127.0.0.1 (ADR-0005), wiec z sieci nikt tu nie dojdzie.
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
# sa poza ScopeGain (ADR-0005).
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
