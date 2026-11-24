"""Trust block: can the reported numbers be believed, and is the company sound?

- Piotroski F-Score (Piotroski 2000): nine yes/no tests of profitability,
  leverage/liquidity and operating efficiency.
- Altman Z-Score (Altman 1968) for manufacturers, Z''-Score (Altman 1995) for
  everyone else: bankruptcy risk in one number with published zones.
- Beneish M-Score (Beneish 1999): probability that earnings were manipulated.
  Knock-out criterion.
- Share dilution: is the share count growing (Pontiff & Woodgate 2008)?

All functions take annual rows from facts.annual_financials (oldest first).
"""

from criteria import FINANCIAL_SIC, MANUFACTURING_SIC, criterion, div, need, sic_in

PIOTROSKI_SOURCE = (
    "Piotroski, J. (2000). Value Investing: The Use of Historical Financial Statement "
    "Information to Separate Winners from Losers. Journal of Accounting Research 38."
)
ALTMAN_SOURCE = (
    "Altman, E. (1968). Financial Ratios, Discriminant Analysis and the Prediction of "
    "Corporate Bankruptcy. Journal of Finance 23(4)."
)
ALTMAN_ZPP_SOURCE = (
    "Altman, E., Hartzell, J., Peck, M. (1995). Emerging Markets Corporate Bonds: A "
    "Scoring System (Z''-Score for non-manufacturers). Salomon Brothers."
)
BENEISH_SOURCE = (
    "Beneish, M. (1999). The Detection of Earnings Manipulation. Financial Analysts "
    "Journal 55(5)."
)
DILUTION_SOURCE = (
    "Pontiff, J., Woodgate, A. (2008). Share Issuance and Cross-sectional Returns. "
    "Journal of Finance 63(2); Piotroski (2000), signal EQ_OFFER."
)

BENEISH_THRESHOLD = -1.78


# --- Piotroski ---------------------------------------------------------------

def _signal(cond: bool | None) -> int | None:
    return None if cond is None else int(cond)


def _gt(a: float | None, b: float | None) -> bool | None:
    return None if a is None or b is None else a > b


def piotroski(rows: list[dict]) -> dict:
    """F-Score for the latest year. Needs three years of assets (beginning-of-year scaling)."""
    t = rows[-1] if rows else None
    p = rows[-2] if len(rows) >= 2 else None
    pp = rows[-3] if len(rows) >= 3 else None
    g = lambda r, f: r.get(f) if r else None  # noqa: E731

    roa_t = div(g(t, "net_income"), g(p, "total_assets"))
    roa_p = div(g(p, "net_income"), g(pp, "total_assets"))
    cfo_scaled = div(g(t, "cfo"), g(p, "total_assets"))

    def avg(a, b):
        return None if a is None or b is None else (a + b) / 2

    def lever(row, prev_row):
        assets = avg(g(row, "total_assets"), g(prev_row, "total_assets"))
        return div(g(row, "long_term_debt"), assets)

    lev_t, lev_p = lever(t, p), lever(p, pp)
    cr_t = div(g(t, "current_assets"), g(t, "current_liabilities"))
    cr_p = div(g(p, "current_assets"), g(p, "current_liabilities"))
    gm_t = div(g(t, "gross_profit"), g(t, "revenue"))
    gm_p = div(g(p, "gross_profit"), g(p, "revenue"))
    turn_t = div(g(t, "revenue"), g(p, "total_assets"))
    turn_p = div(g(p, "revenue"), g(pp, "total_assets"))
    sh_t, sh_p = g(t, "shares_diluted"), g(p, "shares_diluted")

    signals = {
        "ROA > 0": _signal(None if roa_t is None else roa_t > 0),
        "CFO > 0": _signal(None if g(t, "cfo") is None else g(t, "cfo") > 0),
        "ΔROA > 0": _signal(_gt(roa_t, roa_p)),
        "CFO > zysk (jakość zysku)": _signal(_gt(cfo_scaled, roa_t)),
        "Dług długoterminowy/aktywa spadł": _signal(None if lev_t is None or lev_p is None
                                                     else lev_t <= lev_p),
        "Płynność bieżąca wzrosła": _signal(_gt(cr_t, cr_p)),
        "Brak emisji akcji": _signal(None if sh_t is None or sh_p is None else sh_t <= sh_p),
        "Marża brutto wzrosła": _signal(_gt(gm_t, gm_p)),
        "Rotacja aktywów wzrosła": _signal(_gt(turn_t, turn_p)),
    }
    known = [v for v in signals.values() if v is not None]
    unknown = len(signals) - len(known)
    score = sum(known)
    best = score + unknown

    # Piotroski (2000) calls 8-9 "high" and 0-1 "low"; tertiles 0-3 / 4-6 / 7-9
    # are the common practitioner reading of the score.
    if score >= 7:
        outcome = "pass"
    elif best <= 3:
        outcome = "fail"
    elif score >= 4 and best <= 6:
        outcome = "warn"
    else:
        outcome = "na"

    missing = [k for k, v in signals.items() if v is None]
    display = f"{score}/9" if unknown == 0 else f"{score}/{len(known)} (brak {unknown} z 9 testów)"
    meanings = {
        "pass": "Silna kondycja: większość testów rentowności, zadłużenia i efektywności zdana.",
        "warn": "Kondycja przeciętna: część testów zdana, część nie.",
        "fail": "Słaba kondycja: spółka oblewa większość testów jakości.",
        "na": "Za mało danych, żeby rozstrzygnąć wynik F-Score.",
    }
    return criterion(
        id="piotroski", block="trust", name="Piotroski F-Score", outcome=outcome,
        value=float(score) if unknown == 0 else None, display=display,
        threshold="≥ 7 silna · 4–6 przeciętna · ≤ 3 słaba (Piotroski: 8–9 wysoka, 0–1 niska)",
        source=PIOTROSKI_SOURCE, meaning=meanings[outcome], missing=missing,
        details={"signals": signals},
    )


# --- Altman ------------------------------------------------------------------

def altman(rows: list[dict], market_cap: float | None, sic: str | None) -> dict:
    t = rows[-1] if rows else None
    base = dict(id="altman", block="trust")

    if sic_in(sic, FINANCIAL_SIC):
        return criterion(**base, name="Altman Z-Score", outcome="na", value=None,
                         display="nie dotyczy", threshold="—", source=ALTMAN_SOURCE,
                         meaning="Model Altmana nie dotyczy banków, ubezpieczycieli i funduszy "
                                 "(inna struktura bilansu).")

    manufacturing = sic_in(sic, MANUFACTURING_SIC)
    fields = ["current_assets", "current_liabilities", "retained_earnings",
              "operating_income", "total_assets", "total_liabilities"]
    fields += ["revenue"] if manufacturing else ["equity"]
    missing = need(t, fields)
    if manufacturing and market_cap is None:
        missing.append("market_cap")
    name = "Altman Z-Score" if manufacturing else "Altman Z''-Score"
    source = ALTMAN_SOURCE if manufacturing else ALTMAN_ZPP_SOURCE
    threshold = ("> 2,99 bezpieczna · 1,81–2,99 szara strefa · < 1,81 zagrożenie"
                 if manufacturing else
                 "> 2,60 bezpieczna · 1,10–2,60 szara strefa · < 1,10 zagrożenie")
    if missing:
        return criterion(**base, name=name, outcome="na", value=None, display="brak danych",
                         threshold=threshold, source=source, missing=missing,
                         meaning="Nie da się policzyć ryzyka bankructwa bez pełnego bilansu.")

    ta = t["total_assets"]
    x1 = (t["current_assets"] - t["current_liabilities"]) / ta
    x2 = t["retained_earnings"] / ta
    x3 = t["operating_income"] / ta
    if manufacturing:
        x4 = market_cap / t["total_liabilities"]
        x5 = t["revenue"] / ta
        z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
        safe, distress = 2.99, 1.81
    else:
        x4 = t["equity"] / t["total_liabilities"]
        z = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4
        safe, distress = 2.60, 1.10

    if z > safe:
        outcome, meaning = "pass", "Strefa bezpieczna: niskie ryzyko bankructwa w horyzoncie ~2 lat."
    elif z >= distress:
        outcome, meaning = "warn", "Szara strefa: model nie rozstrzyga, ryzyko podwyższone."
    else:
        outcome, meaning = "fail", "Strefa zagrożenia: profil podobny do spółek, które zbankrutowały."
    return criterion(**base, name=name, outcome=outcome, value=round(z, 2),
                     display=f"{z:.2f}".replace(".", ","), threshold=threshold, source=source,
                     meaning=meaning, details={"model": "Z" if manufacturing else "Z''"})


# --- Beneish -----------------------------------------------------------------

def beneish(rows: list[dict], sic: str | None) -> dict:
    t = rows[-1] if rows else None
    p = rows[-2] if len(rows) >= 2 else None
    base = dict(id="beneish", block="trust", name="Beneish M-Score",
                threshold=f"> {BENEISH_THRESHOLD:.2f} = ryzyko manipulacji (wyklucza spółkę)".replace(".", ","),
                source=BENEISH_SOURCE)

    if sic_in(sic, FINANCIAL_SIC):
        return criterion(**base, outcome="na", value=None, display="nie dotyczy",
                         meaning="Beneish badał spółki niefinansowe; dla banków model nie działa.")

    core = ["revenue", "receivables", "gross_profit", "current_assets", "ppe",
            "total_assets", "current_liabilities"]
    missing = need(t, core + ["income_continuing", "cfo"], "") + need(p, core, "poprzedni rok: ")
    if missing:
        return criterion(**base, outcome="na", value=None, display="brak danych", missing=missing,
                         meaning="Bez dwóch pełnych lat sprawozdań nie da się ocenić ryzyka manipulacji.")

    assumed = []

    def ltd(r):
        return r.get("long_term_debt") or 0.0

    dsri = (t["receivables"] / t["revenue"]) / (p["receivables"] / p["revenue"])
    gmi = (p["gross_profit"] / p["revenue"]) / (t["gross_profit"] / t["revenue"])
    aqi = (1 - (t["current_assets"] + t["ppe"]) / t["total_assets"]) / \
          (1 - (p["current_assets"] + p["ppe"]) / p["total_assets"])
    sgi = t["revenue"] / p["revenue"]
    if t.get("depreciation") and p.get("depreciation"):
        depi = (p["depreciation"] / (p["depreciation"] + p["ppe"])) / \
               (t["depreciation"] / (t["depreciation"] + t["ppe"]))
    else:
        depi = 1.0
        assumed.append("DEPI = 1 (brak amortyzacji w danych)")
    if t.get("sga") and p.get("sga"):
        sgai = (t["sga"] / t["revenue"]) / (p["sga"] / p["revenue"])
    else:
        sgai = 1.0
        assumed.append("SGAI = 1 (brak kosztów SG&A w danych)")
    lvgi = ((t["current_liabilities"] + ltd(t)) / t["total_assets"]) / \
           ((p["current_liabilities"] + ltd(p)) / p["total_assets"])
    tata = (t["income_continuing"] - t["cfo"]) / t["total_assets"]

    m = (-4.84 + 0.920 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi
         + 0.115 * depi - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi)
    flagged = m > BENEISH_THRESHOLD
    meaning = ("Profil liczb przypomina spółki, które manipulowały wynikami. "
               "To wyklucza spółkę, dopóki nie sprawdzisz przyczyny."
               if flagged else
               "Brak sygnałów manipulacji wynikami według modelu Beneisha.")
    if assumed:
        meaning += " Założenia: " + "; ".join(assumed) + "."
    return criterion(**base, outcome="fail" if flagged else "pass", value=round(m, 2),
                     display=f"{m:.2f}".replace(".", ","), meaning=meaning, knockout=flagged,
                     details={"DSRI": dsri, "GMI": gmi, "AQI": aqi, "SGI": sgi, "DEPI": depi,
                              "SGAI": sgai, "LVGI": lvgi, "TATA": tata, "assumed": assumed})


# --- Dilution ----------------------------------------------------------------

def dilution(rows: list[dict]) -> dict:
    shares = [(r["fiscal_year_end"], r["shares_diluted"]) for r in rows
              if r.get("shares_diluted")]
    base = dict(id="dilution", block="trust", name="Rozwadnianie akcji (zmiana liczby akcji/rok)",
                threshold="≤ 0% brak · 0–2% umiarkowane · > 2% silne",
                source=DILUTION_SOURCE)
    if len(shares) < 2:
        return criterion(**base, outcome="na", value=None, display="brak danych",
                         missing=["shares_diluted"],
                         meaning="Brak historii liczby akcji.")
    window = shares[-4:]  # up to 3 annual steps
    years = len(window) - 1
    cagr = (window[-1][1] / window[0][1]) ** (1 / years) - 1
    pct = cagr * 100
    if pct <= 0:
        outcome, meaning = "pass", "Liczba akcji nie rośnie (lub spada przez skup): Twój udział się nie kurczy."
    elif pct <= 2:
        outcome, meaning = "warn", "Liczba akcji rośnie powoli: Twój udział w zyskach lekko się rozwadnia."
    else:
        outcome, meaning = "fail", "Spółka szybko dodrukowuje akcje: Twój udział w zyskach się kurczy."
    return criterion(**base, outcome=outcome, value=round(pct, 2),
                     display=f"{pct:+.1f}% rocznie ({years} l.)".replace(".", ","), meaning=meaning)


def trust_block(rows: list[dict], market_cap: float | None, sic: str | None) -> list[dict]:
    return [beneish(rows, sic), piotroski(rows), altman(rows, market_cap, sic), dilution(rows)]
