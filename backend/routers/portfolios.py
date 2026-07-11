from collections import defaultdict
from typing import Literal

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from analysis import build_verdict
from database import get_db
from market import BENCHMARK, close_series, closes_frame, latest_prices
from models import Portfolio, Position, User
from security import get_current_user
from quant import (
    annualized_volatility_pct,
    beta,
    net_pnl,
    returns_frame,
    sharpe_ratio,
    total_return_pct,
)

from schemas import (
    PortfolioCreate,
    PortfolioRead,
    PortfolioValuation,
    PositionCreate,
    PositionRead,
    PositionValuation,
)

# Ludzka nazwa benchmarku do komunikatow (SPY = ETF na S&P 500).
BENCHMARK_LABEL = "S&P 500"

# prefix="/portfolios" -> wszystkie trasy ponizej dostaja ten przedrostek,
# wiec w srodku podajemy juz tylko koncowki ("" = samo /portfolios).
router = APIRouter(prefix="/portfolios", tags=["portfolios"])


def _get_owned_portfolio(portfolio_id: int, user: User, db: Session) -> Portfolio:
    """Pobiera portfel i sprawdza, ze nalezy do zalogowanego usera. Cudzy
    (albo osierocony sprzed auth) traktujemy jak NIEISTNIEJACY (404, nie 403) -
    nie zdradzamy nawet, ze taki portfel istnieje. Jedno miejsce, wolane przez
    wszystkie trasy z {portfolio_id}, wiec autoryzacji nie da sie zapomniec."""
    portfel = db.get(Portfolio, portfolio_id)
    if portfel is None or portfel.user_id != user.id:
        raise HTTPException(status_code=404, detail=f"Nie ma portfela o id {portfolio_id}.")
    return portfel


# response_model = schemat, ktorym FastAPI FILTRUJE odpowiedz. Nawet gdy
# obiekt z bazy ma wiecej pol, klient dostanie tylko to, co w schemacie.
@router.post("", response_model=PortfolioRead, status_code=201)
def create_portfolio(
    dane: PortfolioCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # dane sa juz zwalidowane przez Pydantic (bramkarz). Tworzymy wiersz w bazie,
    # przypisany do zalogowanego usera (user_id).
    portfel = Portfolio(name=dane.name, user_id=user.id)
    db.add(portfel)       # "dopisz do sesji"
    db.commit()           # "zatwierdz w bazie" (dopiero teraz trafia na dysk)
    db.refresh(portfel)   # dociagnij id, ktore nadala baza
    return portfel


@router.get("", response_model=list[PortfolioRead])
def list_portfolios(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Tylko portfele zalogowanego usera - obcych nie widac.
    return db.scalars(select(Portfolio).where(Portfolio.user_id == user.id)).all()


# Zywa wycena portfela: bierze pozycje z bazy, dociaga aktualne ceny z rynku
# i liczy zysk/strate. To pierwszy prawdziwy "quant" - laczy DANE (baza) z
# RYNKIEM (yfinance) w policzony wynik, ktorego nie ma w zadnej tabeli.
@router.get("/{portfolio_id}/valuation", response_model=PortfolioValuation)
def portfolio_valuation(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfel = _get_owned_portfolio(portfolio_id, user, db)

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

    # Ile REALNIE zostaje w kieszeni: brutto pomniejszone o prowizje maklerska
    # i podatek Belka (patrz quant.net_pnl - warstwa 12a).
    netto = net_pnl(total_cost, total_value)

    return PortfolioValuation(
        id=portfel.id,
        name=portfel.name,
        positions=pozycje_out,
        total_cost=round(total_cost, 2),
        total_value=round(total_value, 2),
        total_pnl_abs=round(zysk_total, 2),
        total_pnl_pct=round(zysk_total_pct, 2),
        total_commission=netto["commission_total"],
        total_tax_belka=netto["tax_belka"],
        total_pnl_net_abs=netto["net_pnl_abs"],
        total_pnl_net_pct=netto["net_pnl_pct"],
    )


# Backtest portfela w czasie: "ja vs rynek". Liczy wartosc portfela dzien po
# dniu (suma ilosc*cena kazdej spolki) i normalizuje do 100 na starcie, tak
# samo benchmark (SPY). Dwie krzywe od 100 - widac, kto rosnie szybciej.
@router.get("/{portfolio_id}/performance")
def portfolio_performance(
    portfolio_id: int,
    period: Literal["1mo", "3mo", "6mo", "1y", "5y"] = "6mo",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfel = _get_owned_portfolio(portfolio_id, user, db)
    if not portfel.positions:
        raise HTTPException(status_code=400, detail="Portfel jest pusty - nie ma co liczyc.")

    # Wyrownane ceny wszystkich spolek z portfela (wspolne dni notowan).
    ceny = closes_frame([p.ticker for p in portfel.positions], period)
    if ceny.empty:
        raise HTTPException(status_code=404, detail="Brak danych rynkowych dla tego portfela.")

    # Wartosc portfela w kazdym dniu = suma (ilosc * cena) po pozycjach.
    wartosc = pd.Series(0.0, index=ceny.index)
    for p in portfel.positions:
        kol = p.ticker.upper()
        if kol in ceny.columns:
            wartosc = wartosc + float(p.quantity) * ceny[kol]

    # Indeks od 100: kazdy punkt to "ile masz, jesli start = 100". Pozwala
    # porownac portfel i rynek na jednej skali, niezaleznie od kwot.
    portfel_idx = wartosc / wartosc.iloc[0] * 100

    # Benchmark wyrownany do tych samych dni (ffill zasklepia ew. luki).
    bench = close_series(BENCHMARK, period)
    bench = bench.reindex(portfel_idx.index).ffill().bfill()
    bench_idx = bench / bench.iloc[0] * 100

    seria = [
        {
            "time": data.strftime("%Y-%m-%d"),
            "portfolio": round(float(portfel_idx.loc[data]), 2),
            "benchmark": round(float(bench_idx.loc[data]), 2),
        }
        for data in portfel_idx.index
    ]

    portfel_zwrot = round(float(portfel_idx.iloc[-1] - 100), 2)
    bench_zwrot = round(float(bench_idx.iloc[-1] - 100), 2)

    # Metryki ryzyko/nagroda liczymy z dziennych zwrotow serii (indeks od 100
    # ma te same zwroty co realna wartosc - normalizacja nic tu nie psuje).
    port_zwroty = portfel_idx.pct_change().dropna()
    bench_zwroty = bench_idx.pct_change().dropna()
    zmiennosc = annualized_volatility_pct(port_zwroty)

    ryzyko = {
        "sharpe": round(sharpe_ratio(port_zwroty), 2),
        "beta": round(beta(port_zwroty, bench_zwroty), 2),
        "volatility_pct": round(zmiennosc, 2),
        # zwrot na jednostke ryzyka - proste, intuicyjne uzupelnienie Sharpe'a
        "return_risk": round(portfel_zwrot / zmiennosc, 2) if zmiennosc else 0.0,
    }

    return {
        "id": portfel.id,
        "name": portfel.name,
        "period": period,
        "benchmark_ticker": BENCHMARK,
        "portfolio_return_pct": portfel_zwrot,
        "benchmark_return_pct": bench_zwrot,
        "alpha_pct": round(portfel_zwrot - bench_zwrot, 2),
        "risk": ryzyko,
        "series": seria,
    }


# WERDYKT: apka nie tylko liczy, ale MOWI, co z liczb wynika. Zbiera alpha,
# Sharpe, zmiennosc vs rynek, korelacje i koncentracje w wnioski + ocene.
# Wszystko z JEDNEJ tabeli cen (closes_frame) + rynku - bez zbednych strzalow.
@router.get("/{portfolio_id}/verdict")
def portfolio_verdict(
    portfolio_id: int,
    period: Literal["1mo", "3mo", "6mo", "1y", "5y"] = "1y",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfel = _get_owned_portfolio(portfolio_id, user, db)
    if not portfel.positions:
        raise HTTPException(status_code=400, detail="Portfel jest pusty - nie ma co oceniac.")

    # Sumujemy ilosci per ticker (ten sam ticker moze byc w kilku pozycjach).
    ilosci: dict[str, float] = defaultdict(float)
    for p in portfel.positions:
        ilosci[p.ticker.upper()] += float(p.quantity)

    ceny = closes_frame(list(ilosci.keys()), period)
    if ceny.empty:
        raise HTTPException(status_code=404, detail="Brak danych rynkowych dla tego portfela.")

    tickery = list(ceny.columns)

    # Wartosc portfela dzien po dniu -> zwroty, zmiennosc, Sharpe.
    wartosc = pd.Series(0.0, index=ceny.index)
    for t in tickery:
        wartosc = wartosc + ilosci[t] * ceny[t]
    port_idx = wartosc / wartosc.iloc[0] * 100
    port_ret = port_idx.pct_change().dropna()
    port_zwrot = float(port_idx.iloc[-1] - 100)
    port_vol = annualized_volatility_pct(port_ret)

    # Rynek za ten sam okres (wyrownany po datach).
    bench = close_series(BENCHMARK, period).reindex(port_idx.index).ffill().bfill()
    bench_idx = bench / bench.iloc[0] * 100
    bench_zwrot = float(bench_idx.iloc[-1] - 100)
    bench_vol = annualized_volatility_pct(bench_idx.pct_change().dropna())

    # Srednia korelacja miedzy spolkami (bez przekatnej) - miara dywersyfikacji.
    avg_corr = None
    if len(tickery) >= 2:
        macierz = returns_frame(ceny).corr().values
        n = len(macierz)
        avg_corr = float((macierz.sum() - n) / (n * n - n))  # -n usuwa przekatna (jedynki)

    # Koncentracja: udzial najwiekszej pozycji wg dzisiejszej wyceny.
    ostatnie = ceny.iloc[-1]
    wagi = {t: ilosci[t] * float(ostatnie[t]) for t in tickery}
    suma = sum(wagi.values())
    top_ticker = max(wagi, key=wagi.get) if wagi else None
    top_weight = (wagi[top_ticker] / suma * 100) if suma and top_ticker else 0.0

    werdykt = build_verdict(
        benchmark_label=BENCHMARK_LABEL,
        alpha_pct=port_zwrot - bench_zwrot,
        sharpe=sharpe_ratio(port_ret),
        port_vol=port_vol,
        bench_vol=bench_vol,
        avg_corr=avg_corr,
        n_tickers=len(tickery),
        top_weight_pct=top_weight,
        top_ticker=top_ticker,
    )

    return {"id": portfel.id, "name": portfel.name, "period": period, **werdykt}


# Korelacje miedzy spolkami w portfelu (na dziennych zwrotach).
# Blisko +1 = spolki chodza razem (slaba dywersyfikacja - jak jedna spada,
# druga tez). Blisko 0 lub ujemna = niezalezne (lepiej rozlozone ryzyko).
@router.get("/{portfolio_id}/correlations")
def portfolio_correlations(
    portfolio_id: int,
    period: Literal["1mo", "3mo", "6mo", "1y", "5y"] = "6mo",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfel = _get_owned_portfolio(portfolio_id, user, db)

    tickery = sorted({p.ticker.upper() for p in portfel.positions})
    # Korelacja ma sens dopiero dla >= 2 ROZNYCH spolek.
    if len(tickery) < 2:
        return {"period": period, "tickers": tickery, "matrix": [[1.0]] if tickery else []}

    ceny = closes_frame(tickery, period)
    if ceny.empty:
        raise HTTPException(status_code=404, detail="Brak danych rynkowych dla tego portfela.")

    corr = returns_frame(ceny).corr()   # pandas liczy cala macierz korelacji
    kolumny = [str(c) for c in corr.columns]
    macierz = [[round(float(corr.iloc[i, j]), 2) for j in range(len(kolumny))]
               for i in range(len(kolumny))]

    return {"period": period, "tickers": kolumny, "matrix": macierz}


@router.post(
    "/{portfolio_id}/positions",
    response_model=PositionRead,
    status_code=201,
)
def add_position(
    portfolio_id: int,               # z adresu: do ktorego portfela dopisujemy
    dane: PositionCreate,            # z tresci: jaka spolka, ile, po ile
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Portfel musi istniec I nalezec do zalogowanego usera (inaczej 404) -
    # bez tego mozna by dopisywac pozycje do cudzego portfela.
    portfel = _get_owned_portfolio(portfolio_id, user, db)

    # Walidacja rynkowa: nie wpuszczamy spolki, ktorej rynek nie zna - inaczej
    # wycena, backtest i werdykt dostana smiec (spolka bez ceny). {} = brak.
    if not latest_prices([dane.ticker]):
        raise HTTPException(
            status_code=400,
            detail=f"Nie znaleziono spolki '{dane.ticker.upper()}' na rynku. Sprawdz symbol.",
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


# Usuwanie pozycji. 204 = "zrobione, nie mam nic do oddania" (pusty body).
# Sprawdzamy tez, czy pozycja NALEZY do tego portfela - inaczej ktos moglby
# skasowac cudza pozycje, podajac zle portfolio_id w adresie.
@router.delete("/{portfolio_id}/positions/{position_id}", status_code=204)
def delete_position(
    portfolio_id: int,
    position_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Najpierw autoryzacja portfela (cudzy -> 404), potem czy pozycja jest jego.
    _get_owned_portfolio(portfolio_id, user, db)
    pozycja = db.get(Position, position_id)
    if pozycja is None or pozycja.portfolio_id != portfolio_id:
        raise HTTPException(status_code=404, detail="Nie ma takiej pozycji w tym portfelu.")
    db.delete(pozycja)
    db.commit()


# Usuwanie calego portfela. Pozycje znikaja same dzieki cascade="all,
# delete-orphan" na relacji w models.py (baza sprzata dzieci za nas).
@router.delete("/{portfolio_id}", status_code=204)
def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfel = _get_owned_portfolio(portfolio_id, user, db)
    db.delete(portfel)
    db.commit()
