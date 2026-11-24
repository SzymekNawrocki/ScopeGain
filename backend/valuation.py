"""Valuation block: is the price reasonable for what the company earns and owns?"""

from criteria import criterion

GRAHAM_SOURCE = (
    "Graham, B. (1973). The Intelligent Investor, 4th ed., ch. 14: P/E × P/B should "
    "not exceed 22.5 (15 × 1.5) for the defensive investor."
)


def _fmt(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def graham_multiplier(rows: list[dict], market_cap: float | None) -> dict:
    t = rows[-1] if rows else {}
    base = dict(id="graham_multiplier", block="valuation", name="Mnożnik Grahama (C/Z × C/WK)",
                threshold="≤ 22,5", source=GRAHAM_SOURCE)
    missing = [f for f in ("net_income", "equity") if t.get(f) is None]
    if market_cap is None:
        missing.append("market_cap")
    if missing:
        return criterion(**base, outcome="na", value=None, display="brak danych",
                         missing=missing, meaning="Brak zysku, kapitału własnego lub kapitalizacji.")
    if t["net_income"] <= 0:
        return criterion(**base, outcome="fail", value=None, display="strata",
                         meaning="Spółka nie ma zysku, więc nie da się jej wycenić zyskiem.")
    if t["equity"] <= 0:
        return criterion(**base, outcome="fail", value=None, display="ujemny kapitał",
                         meaning="Kapitał własny ujemny: długi przewyższają majątek księgowy.")
    pe = market_cap / t["net_income"]
    pb = market_cap / t["equity"]
    product = pe * pb
    if product <= 22.5:
        outcome, meaning = "pass", "Cena rozsądna względem zysków i majątku według Grahama."
    else:
        outcome, meaning = "fail", ("Płacisz dużo ponad zyski i majątek księgowy. "
                                    "Wymaga to wiary we wzrost, a nie twardych liczb.")
    return criterion(**base, outcome=outcome, value=round(product, 1),
                     display=f"{_fmt(product)} (C/Z {_fmt(pe)} × C/WK {_fmt(pb)})",
                     meaning=meaning, details={"pe": pe, "pb": pb})


def valuation_block(rows: list[dict], market_cap: float | None) -> list[dict]:
    return [graham_multiplier(rows, market_cap)]
