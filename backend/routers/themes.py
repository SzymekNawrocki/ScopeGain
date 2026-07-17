"""Tematy, odkrywanie kandydatow i rozliczenie typow (Etap B + Etap 5).

Domyka poczatek i koniec petli decyzyjnej: ODKRYWAJ kandydatow (po branzy /
ETF, z pochodzeniem) -> zapisz TYP z teza i uniewaznieniem -> ROZLICZ sie.
Zgodnie z ADR-0002 apka nigdy nie udaje, ze zna sklad tematu - podsuwa
kandydatow, user kuratoruje.
"""
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from analysis import build_reckoning
from database import get_db
from market import (
    MarketUnavailable,
    browsable_sectors,
    etf_holdings,
    industry_companies,
    latest_prices,
    sector_industries,
)
from models import Observation, Theme, User
from schemas import (
    DiscoverCompany,
    DiscoverNode,
    ObservationCreate,
    ObservationRead,
    ReckoningOut,
    ThemeCreate,
    ThemeRead,
)
from security import get_current_user

# Auth na calym routerze (jak /stock): odkrywanie tez chronimy, zeby nie bylo
# otwartym proxy do Yahoo. Handlery, ktore potrzebuja obiektu usera, i tak
# wstrzykuja go osobno (do sprawdzenia wlasciciela).
router = APIRouter(tags=["themes"], dependencies=[Depends(get_current_user)])

_ODMOWA = "Zrodlo danych chwilowo odmawia (limit zapytan). Sprobuj za chwile."


def _get_owned_theme(theme_id: int, user: User, db: Session) -> Theme:
    """Temat zalogowanego usera albo 404 (cudzy/osierocony = jakby nie istnial).
    Jedno miejsce, wolane przez wszystkie trasy z {theme_id}."""
    temat = db.get(Theme, theme_id)
    if temat is None or temat.user_id != user.id:
        raise HTTPException(status_code=404, detail=f"Nie ma tematu o id {theme_id}.")
    return temat


# --- ODKRYWANIE: drill-down sektor -> branza -> spolki + rozbicie ETF -------

@router.get("/discover/sectors", response_model=list[DiscoverNode])
def discover_sectors():
    return browsable_sectors()


@router.get("/discover/sector/{key}", response_model=list[DiscoverNode])
def discover_sector(key: str = Path(min_length=1, max_length=60)):
    try:
        return sector_industries(key)
    except MarketUnavailable:
        raise HTTPException(status_code=503, detail=_ODMOWA)


@router.get("/discover/industry/{key}", response_model=list[DiscoverCompany])
def discover_industry(key: str = Path(min_length=1, max_length=60)):
    try:
        return industry_companies(key)
    except MarketUnavailable:
        raise HTTPException(status_code=503, detail=_ODMOWA)


@router.get("/discover/etf/{ticker}", response_model=list[DiscoverCompany])
def discover_etf(ticker: str = Path(min_length=1, max_length=15)):
    try:
        return etf_holdings(ticker)
    except MarketUnavailable:
        raise HTTPException(status_code=503, detail=_ODMOWA)


# --- TEMATY (CRUD) ----------------------------------------------------------

@router.post("/themes", response_model=ThemeRead, status_code=201)
def create_theme(
    dane: ThemeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    temat = Theme(name=dane.name, user_id=user.id)
    db.add(temat)
    db.commit()
    db.refresh(temat)
    return temat


@router.get("/themes", response_model=list[ThemeRead])
def list_themes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.scalars(select(Theme).where(Theme.user_id == user.id)).all()


@router.get("/themes/{theme_id}", response_model=ThemeRead)
def get_theme(
    theme_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _get_owned_theme(theme_id, user, db)


@router.delete("/themes/{theme_id}", status_code=204)
def delete_theme(
    theme_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    temat = _get_owned_theme(theme_id, user, db)
    db.delete(temat)   # cascade sprząta obserwacje
    db.commit()


# --- OBSERWACJE (typy w temacie) -------------------------------------------

@router.post("/themes/{theme_id}/observations", response_model=ObservationRead, status_code=201)
def add_observation(
    theme_id: int,
    dane: ObservationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    temat = _get_owned_theme(theme_id, user, db)

    # Cena z momentu dodania - to ona pozwala pozniej rozliczyc typ. Gdy rynek
    # chwilowo odmawia, zapisujemy typ mimo to (added_price = None); rozliczenie
    # to uczciwie zniesie. Data leci z domyslnej wartosci modelu (dzis).
    try:
        ceny = latest_prices([dane.ticker])
    except MarketUnavailable:
        ceny = {}
    added_price = ceny.get(dane.ticker.upper())

    obs = Observation(
        theme_id=temat.id,
        ticker=dane.ticker.upper(),
        name=dane.name,
        origin=dane.origin,
        thesis=dane.thesis,
        invalidation_note=dane.invalidation_note,
        invalidation_price=dane.invalidation_price,
        entry_note=dane.entry_note,
        added_price=added_price,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs


@router.delete("/themes/{theme_id}/observations/{obs_id}", status_code=204)
def delete_observation(
    theme_id: int,
    obs_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_owned_theme(theme_id, user, db)   # wlasciciel tematu
    obs = db.get(Observation, obs_id)
    if obs is None or obs.theme_id != theme_id:
        raise HTTPException(status_code=404, detail=f"Nie ma obserwacji o id {obs_id}.")
    db.delete(obs)
    db.commit()


@router.post("/themes/{theme_id}/observations/{obs_id}/acted", response_model=ObservationRead)
def mark_acted(
    theme_id: int,
    obs_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Oznacz, ze na typie ZADZIALALES (kupiles). Rozliczenie pyta 'czy
    zadzialales' - to jest odpowiedz. Przelacznik (toggle)."""
    _get_owned_theme(theme_id, user, db)
    obs = db.get(Observation, obs_id)
    if obs is None or obs.theme_id != theme_id:
        raise HTTPException(status_code=404, detail=f"Nie ma obserwacji o id {obs_id}.")
    obs.acted = not obs.acted
    db.commit()
    db.refresh(obs)
    return obs


# --- ROZLICZENIE (Etap 5) ---------------------------------------------------

@router.get("/themes/{theme_id}/reckoning", response_model=ReckoningOut)
def theme_reckoning(
    theme_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    temat = _get_owned_theme(theme_id, user, db)

    tickery = [o.ticker for o in temat.observations]
    try:
        ceny = latest_prices(tickery) if tickery else {}
    except MarketUnavailable:
        raise HTTPException(status_code=503, detail=_ODMOWA)

    obserwacje = [
        {
            "id": o.id,
            "ticker": o.ticker,
            "name": o.name,
            "added_at": o.added_at,
            "added_price": float(o.added_price) if o.added_price is not None else None,
            "invalidation_price": float(o.invalidation_price) if o.invalidation_price is not None else None,
            "invalidation_note": o.invalidation_note,
            "acted": o.acted,
        }
        for o in temat.observations
    ]

    rozliczenie = build_reckoning(obserwacje, ceny)
    return {"id": temat.id, "name": temat.name, **rozliczenie}
