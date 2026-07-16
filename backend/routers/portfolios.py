from collections import defaultdict
from datetime import date
from typing import Literal

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from analysis import build_behavior_verdict, build_verdict
from database import get_db
from market import (
    BENCHMARK,
    CRASH_WINDOWS,
    close_series,
    close_series_range,
    closes_frame,
    closes_frame_range,
    latest_prices,
    usd_pln_rate,
)
from models import Portfolio, Position, Transaction, User
from security import get_current_user
from quant import (
    annualized_volatility_pct,
    beta,
    cvar_pct,
    estimate_rebalance_cost,
    historical_var_pct,
    holdings_timeline,
    max_drawdown_pct,
    net_pnl,
    overlapping_horizon_returns,
    portfolio_shock_pct,
    rebalance_plan,
    reconcile_holdings,
    returns_frame,
    sharpe_ratio,
    twr_index,
)

from schemas import (
    PortfolioCreate,
    PortfolioRead,
    PortfolioRisk,
    PortfolioValuation,
    PositionCreate,
    PositionRead,
    PositionValuation,
    RebalanceCost,
    RebalanceLeg,
    RebalancePlan,
    StressScenario,
    TransactionCreate,
    TransactionRead,
    VarMeasure,
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


def _quantities_by_ticker(positions: list[Position]) -> dict[str, float]:
    """Sumuje ilosci per ticker (ten sam ticker moze byc w kilku pozycjach)."""
    ilosci: dict[str, float] = defaultdict(float)
    for p in positions:
        ilosci[p.ticker.upper()] += float(p.quantity)
    return dict(ilosci)


def _portfolio_value_series(positions: list[Position], ceny: pd.DataFrame) -> pd.Series:
    """Wartosc portfela dzien po dniu = suma (ilosc * cena) po pozycjach.

    JEDNO miejsce prawdy dla "krzywej portfela" - wczesniej ten sam wzor byl
    powielony w performance i verdict. UWAGA: bierze DZISIEJSZE ilosci i rzutuje
    je na caly okres (brak logu transakcji, warstwa 12b) - to hipoteza "gdybym
    od poczatku trzymal to, co mam dzis", nie realna sciezka. Front oznacza to
    jako "hipotetyczny".
    """
    ilosci = _quantities_by_ticker(positions)
    wartosc = pd.Series(0.0, index=ceny.index)
    for t, q in ilosci.items():
        if t in ceny.columns:
            wartosc = wartosc + q * ceny[t]
    return wartosc


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

    # Przeliczenie na PLN (kurs NBP). None, gdy NBP nie odpowie - wycena USD zostaje.
    kurs = usd_pln_rate()
    value_pln = round(total_value * kurs, 2) if kurs else None
    net_pln = round(netto["net_pnl_abs"] * kurs, 2) if kurs else None

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
        fx_usd_pln=round(kurs, 4) if kurs else None,
        total_value_pln=value_pln,
        total_pnl_net_pln=net_pln,
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

    # Wartosc portfela w kazdym dniu (helper - jedno miejsce prawdy).
    wartosc = _portfolio_value_series(portfel.positions, ceny)

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
    ilosci = _quantities_by_ticker(portfel.positions)

    ceny = closes_frame(list(ilosci.keys()), period)
    if ceny.empty:
        raise HTTPException(status_code=404, detail="Brak danych rynkowych dla tego portfela.")

    tickery = list(ceny.columns)

    # Wartosc portfela dzien po dniu -> zwroty, zmiennosc, Sharpe (helper).
    wartosc = _portfolio_value_series(portfel.positions, ceny)
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


# RYZYKO: "ile realnie moge stracic". VaR/CVaR (metoda historyczna) + stress
# test (odtworzenie krachow). Apka NIE prognozuje - odtwarza realny rozklad i
# realna historie. Kwoty w USD (spolki w dolarach - nie udajemy PLN).
@router.get("/{portfolio_id}/risk", response_model=PortfolioRisk)
def portfolio_risk(
    portfolio_id: int,
    window: Literal["1y", "2y", "5y"] = "2y",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfel = _get_owned_portfolio(portfolio_id, user, db)
    if not portfel.positions:
        raise HTTPException(status_code=400, detail="Portfel jest pusty - nie ma czego liczyc.")

    ilosci = _quantities_by_ticker(portfel.positions)

    # Dzisiejsza wartosc i wagi - baza dla kwot ryzyka (tylko spolki z cena).
    ceny_teraz = latest_prices(list(ilosci.keys()))
    wartosci_dzis = {t: ilosci[t] * cena for t, cena in ceny_teraz.items()}
    portfolio_value = sum(wartosci_dzis.values())
    if portfolio_value <= 0:
        raise HTTPException(status_code=404, detail="Brak aktualnych cen dla tego portfela.")
    wagi = {t: v / portfolio_value for t, v in wartosci_dzis.items()}

    # Szereg dziennych zwrotow portfela z okna estymacji (helper - ta sama
    # krzywa co backtest, wiec VaR liczy sie ze spojnego zrodla).
    ceny = closes_frame(list(ilosci.keys()), window)
    if ceny.empty:
        raise HTTPException(status_code=404, detail="Brak danych rynkowych dla tego portfela.")
    port_idx = _portfolio_value_series(portfel.positions, ceny)
    port_ret = port_idx.pct_change().dropna()
    mies_ret = overlapping_horizon_returns(port_ret, window=21)

    # VaR/CVaR dla 95%/99% w dwoch horyzontach (dzien / ~miesiac). Miesieczny
    # z nakladajacych sie okien, nie ze skalowania sqrt(21).
    var_out: list[VarMeasure] = []
    for conf in (0.95, 0.99):
        for horyzont, seria in (("1d", port_ret), ("1m", mies_ret)):
            if seria.empty:
                continue
            v_pct = historical_var_pct(seria, conf)
            c_pct = cvar_pct(seria, conf)
            var_out.append(VarMeasure(
                confidence=conf,
                horizon=horyzont,
                var_pct=round(v_pct, 2),
                var_abs=round(v_pct / 100 * portfolio_value, 2),
                cvar_pct=round(c_pct, 2),
                cvar_abs=round(c_pct / 100 * portfolio_value, 2),
            ))

    # Bety spolek vs rynek (do proxy w stressie): z tego samego okna estymacji.
    ret_frame = returns_frame(ceny)
    bench_ret_window = close_series(BENCHMARK, window).pct_change().dropna()
    bety = {
        t: beta(ret_frame[t], bench_ret_window)
        for t in wagi if t in ret_frame.columns
    }

    # Stress test: dla kazdego krachu licz szok kazdej spolki. Realny zwrot,
    # jesli spolka wtedy istniala; inaczej PROXY = beta * spadek indeksu.
    # Pokrycie (realne vs proxy) raportujemy jawnie - to o uczciwosc.
    stress_out: list[StressScenario] = []
    for key, okno in CRASH_WINDOWS.items():
        spy_okno = close_series_range(BENCHMARK, okno["start"], okno["end"])
        spy_shock = float(spy_okno.iloc[-1] / spy_okno.iloc[0] - 1) if len(spy_okno) >= 2 else 0.0

        szoki: dict[str, float] = {}
        real, proxy = [], []
        for t in wagi:
            seria_t = close_series_range(t, okno["start"], okno["end"])
            if len(seria_t) >= 2:
                szoki[t] = float(seria_t.iloc[-1] / seria_t.iloc[0] - 1)
                real.append(t)
            else:
                szoki[t] = bety.get(t, 1.0) * spy_shock   # proxy przez bete
                proxy.append(t)

        shock_pct = portfolio_shock_pct(wagi, szoki)
        stress_out.append(StressScenario(
            key=key,
            label=okno["label"],
            shock_pct=round(shock_pct, 2),
            pnl_abs=round(shock_pct / 100 * portfolio_value, 2),
            coverage_real=sorted(real),
            coverage_proxy=sorted(proxy),
        ))

    # Ostrzezenie o oknie: jesli w oknie estymacji nie bylo prawdziwego obsuniecia,
    # VaR (uczony na spokojnym rynku) prawie na pewno zanizy ryzyko.
    max_dd = max_drawdown_pct(port_idx)
    warning = None
    if max_dd > -15:
        warning = (
            f"Okno '{window}' obejmuje glownie spokojny rynek (najwieksze obsuniecie "
            f"{max_dd:.0f}%) - VaR uczony na takim oknie zanizy ryzyko realnego krachu. "
            f"Patrz stress test ponizej."
        )

    return PortfolioRisk(
        id=portfel.id,
        name=portfel.name,
        window=window,
        currency="USD",
        portfolio_value=round(portfolio_value, 2),
        n_days=int(len(port_ret)),
        var=var_out,
        stress=stress_out,
        warning=warning,
    )


# --- TRANSAKCJE + WERDYKT ZACHOWANIA (warstwa 12b) ---
# Pozycje mowia "co mam TERAZ". Log transakcji pamieta "co ZROBILEM i KIEDY" -
# bez tego apka nie zna Twoich decyzji, a werdykt zachowania (behavior gap) nie
# mialby na czym stanac. Append-only: nie edytujemy historii, tylko dopisujemy.

@router.post(
    "/{portfolio_id}/transactions",
    response_model=TransactionRead,
    status_code=201,
)
def add_transaction(
    portfolio_id: int,
    dane: TransactionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfel = _get_owned_portfolio(portfolio_id, user, db)

    # Walidacja rynkowa: nieznany ticker -> werdykt zachowania nie dociagnie
    # dzisiejszej ceny i cala transakcja bylaby bezuzyteczna do oceny.
    if not latest_prices([dane.ticker]):
        raise HTTPException(
            status_code=400,
            detail=f"Nie znaleziono spolki '{dane.ticker.upper()}' na rynku. Sprawdz symbol.",
        )

    tx = Transaction(
        ticker=dane.ticker.upper(),
        side=dane.side,               # Pydantic Literal juz ograniczyl do BUY/SELL
        quantity=dane.quantity,
        price=dane.price,
        executed_at=dane.executed_at,
        portfolio_id=portfolio_id,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.get("/{portfolio_id}/transactions", response_model=list[TransactionRead])
def list_transactions(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_owned_portfolio(portfolio_id, user, db)
    # Najnowsze na gorze (po dacie, potem po id - stabilnie przy tej samej dacie).
    return db.scalars(
        select(Transaction)
        .where(Transaction.portfolio_id == portfolio_id)
        .order_by(Transaction.executed_at.desc(), Transaction.id.desc())
    ).all()


@router.delete("/{portfolio_id}/transactions/{transaction_id}", status_code=204)
def delete_transaction(
    portfolio_id: int,
    transaction_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_owned_portfolio(portfolio_id, user, db)
    tx = db.get(Transaction, transaction_id)
    if tx is None or tx.portfolio_id != portfolio_id:
        raise HTTPException(status_code=404, detail="Nie ma takiej transakcji w tym portfelu.")
    db.delete(tx)
    db.commit()


# WERDYKT ZACHOWANIA: czy sprzedaze mialy dobry timing? Dla kazdej SPRZEDAZY
# porownuje cene sprzedazy z dzisiejsza cena tej spolki (urosla -> za wczesnie).
# Atakuje behavior gap - #1 przyczyne niedowazenia wyniku rynku (DALBAR).
@router.get("/{portfolio_id}/behavior")
def portfolio_behavior(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfel = _get_owned_portfolio(portfolio_id, user, db)

    sprzedaze = db.scalars(
        select(Transaction)
        .where(Transaction.portfolio_id == portfolio_id, Transaction.side == "SELL")
        .order_by(Transaction.executed_at.desc())
    ).all()

    # Jeden strzal po dzisiejsze ceny sprzedanych spolek (do porownania z cena
    # sprzedazy). Spolki bez ceny werdykt sam pominie.
    ceny = latest_prices([t.ticker for t in sprzedaze]) if sprzedaze else {}
    rows = [
        {
            "ticker": t.ticker,
            "quantity": float(t.quantity),
            "sold_price": float(t.price),
            "current_price": ceny.get(t.ticker.upper()),
            "executed_at": t.executed_at.isoformat(),
        }
        for t in sprzedaze
    ]

    werdykt = build_behavior_verdict(rows)
    return {"id": portfel.id, "name": portfel.name, **werdykt}


# REBALANSING (warstwa 12c): jak daleko portfel od rownych wag + ile
# kosztowaloby domkniecie rozjazdu. NIE zlecenie "kup/sprzedaj" (ADR-0001) -
# rowne wagi to neutralny PUNKT ODNIESIENIA, koszt (prowizja+Belka) to
# uczciwy trade-off ("rebalansing nie jest darmowy"), nie porada.
@router.get("/{portfolio_id}/rebalance", response_model=RebalancePlan)
def portfolio_rebalance(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfel = _get_owned_portfolio(portfolio_id, user, db)
    if not portfel.positions:
        raise HTTPException(status_code=400, detail="Portfel jest pusty - nie ma co rebalansowac.")

    # Agregacja per ticker: ilosc, koszt wejscia (do Belki na przycieciach).
    ilosci = _quantities_by_ticker(portfel.positions)
    koszt_bazowy: dict[str, float] = defaultdict(float)
    for p in portfel.positions:
        koszt_bazowy[p.ticker.upper()] += float(p.quantity) * float(p.buy_price)

    # Dzisiejsza wartosc per ticker (tylko spolki z cena rynkowa).
    ceny = latest_prices(list(ilosci.keys()))
    holdings = {t: ilosci[t] * cena for t, cena in ceny.items()}
    total = sum(holdings.values())
    if total <= 0:
        raise HTTPException(status_code=404, detail="Brak aktualnych cen dla tego portfela.")

    plan = rebalance_plan(holdings)   # domyslnie rowne wagi 1/N

    # Koszt wykonania: prowizja od kazdego ruchu + Belka od zysku na przycieciach.
    legi = [
        {
            "trade_value": p["trade_value"],
            "market_value": holdings[p["ticker"]],
            "cost_basis": koszt_bazowy[p["ticker"]],
        }
        for p in plan
    ]
    koszt = estimate_rebalance_cost(legi)

    # Najpierw najbardziej przewazone (najwiekszy dodatni dryf).
    plan.sort(key=lambda p: p["drift_pp"], reverse=True)

    return RebalancePlan(
        id=portfel.id,
        name=portfel.name,
        currency="USD",
        total_value=round(total, 2),
        target="equal",
        legs=[RebalanceLeg(**p) for p in plan],
        cost=RebalanceCost(**koszt),
    )


# REALNA sciezka portfela z LOGU TRANSAKCJI: zamiast rzutowac dzisiejsze wagi
# wstecz (hipoteza), odtwarza co NAPRAWDE trzymalo sie kazdego dnia i liczy TWR
# (neutralizacja przeplywow). Zrodlo prawdy = log; pozycje to "ile mam teraz",
# wiec gdy netto z logu != pozycje, mowimy o tym wprost (rekoncyliacja).
@router.get("/{portfolio_id}/real-performance")
def portfolio_real_performance(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfel = _get_owned_portfolio(portfolio_id, user, db)

    transakcje = db.scalars(
        select(Transaction)
        .where(Transaction.portfolio_id == portfolio_id)
        .order_by(Transaction.executed_at.asc())
    ).all()
    if not transakcje:
        return {"id": portfel.id, "name": portfel.name, "available": False,
                "reason": "Brak transakcji w logu - dodaj kupna/sprzedaze, zeby zobaczyc realna sciezke."}

    txs = [{"ticker": t.ticker.upper(), "side": t.side,
            "quantity": float(t.quantity), "executed_at": t.executed_at} for t in transakcje]
    tickery = sorted({t["ticker"] for t in txs})
    start = min(t["executed_at"] for t in txs).isoformat()

    ceny = closes_frame_range(tickery, start)
    if ceny.empty:
        return {"id": portfel.id, "name": portfel.name, "available": False,
                "reason": "Brak danych rynkowych dla spolek z logu."}
    ceny = ceny.ffill().bfill()   # 0-holdingowe dni maja i tak wage 0

    # Ile sztuk kazdego dnia -> wartosc portfela dzien po dniu.
    hold = holdings_timeline(txs, ceny.index).reindex(columns=ceny.columns, fill_value=0.0)
    wartosc = (hold * ceny).sum(axis=1)

    # Przeplywy: kazda transakcja to gotowka wlozona(+)/wyjeta(-) po cenie z dnia
    # (pierwszy dzien notowan >= data transakcji).
    flows = pd.Series(0.0, index=ceny.index)
    for t in txs:
        d = pd.Timestamp(t["executed_at"])
        dni = ceny.index[ceny.index >= d]
        if len(dni) == 0 or t["ticker"] not in ceny.columns:
            continue
        eff = dni[0]
        znak = 1.0 if t["side"].upper() == "BUY" else -1.0
        flows.loc[eff] += znak * t["quantity"] * float(ceny.loc[eff, t["ticker"]])

    twr = twr_index(wartosc, flows)
    if twr.empty:
        return {"id": portfel.id, "name": portfel.name, "available": False,
                "reason": "Log nie daje zadnego dnia z otwarta pozycja."}

    # Benchmark (SPY) wyrownany do dni realnej sciezki, indeks od 100.
    bench = close_series_range(BENCHMARK, start).reindex(twr.index).ffill().bfill()
    bench_idx = bench / bench.iloc[0] * 100

    # Rekoncyliacja: netto z logu vs obecne pozycje.
    log_net: dict[str, float] = defaultdict(float)
    for t in txs:
        log_net[t["ticker"]] += (1.0 if t["side"].upper() == "BUY" else -1.0) * t["quantity"]
    rek = reconcile_holdings(dict(log_net), _quantities_by_ticker(portfel.positions))

    seria = [
        {"time": d.strftime("%Y-%m-%d"),
         "portfolio": round(float(twr.loc[d]), 2),
         "benchmark": round(float(bench_idx.loc[d]), 2)}
        for d in twr.index
    ]
    port_zwrot = round(float(twr.iloc[-1] - 100), 2)
    bench_zwrot = round(float(bench_idx.iloc[-1] - 100), 2)

    return {
        "id": portfel.id,
        "name": portfel.name,
        "available": True,
        "method": "TWR (time-weighted, przeplywy neutralizowane)",
        "start_date": twr.index[0].strftime("%Y-%m-%d"),
        "benchmark_ticker": BENCHMARK,
        "portfolio_return_pct": port_zwrot,
        "benchmark_return_pct": bench_zwrot,
        "alpha_pct": round(port_zwrot - bench_zwrot, 2),
        "reconciliation": rek,
        "series": seria,
    }


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
