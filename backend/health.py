"""Health block: debt load, ability to pay interest, short-term liquidity."""

from criteria import FINANCIAL_SIC, criterion, div, sic_in

SP_SOURCE = (
    "S&P Global Ratings (2013). Corporate Methodology: financial risk profile table "
    "(debt/EBITDA: < 3 at most intermediate, 3-4 significant, > 4 aggressive)."
)
DAMODARAN_SOURCE = (
    "Damodaran, A. Ratings, Interest Coverage Ratios and Default Spread (large "
    "non-financial firms): coverage ≥ 2.5 ≈ investment grade (BBB or better), "
    "< 1.5 ≈ B- or worse."
)
GRAHAM_SOURCE = (
    "Graham, B. (1973). The Intelligent Investor, 4th ed., ch. 14: current assets at "
    "least twice current liabilities for the defensive investor."
)

NOT_FOR_FINANCIALS = "Nie dotyczy banków i ubezpieczycieli (dług to ich surowiec, nie ciężar)."


def _na_financial(id: str, name: str, threshold: str, source: str) -> dict:
    return criterion(id=id, block="health", name=name, outcome="na", value=None,
                     display="nie dotyczy", threshold=threshold, source=source,
                     meaning=NOT_FOR_FINANCIALS)


def _fmt(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def net_debt_to_ebitda(rows: list[dict], sic: str | None) -> dict:
    name, threshold = "Dług netto / EBITDA", "< 3 umiarkowany · 3–4 znaczący · > 4 agresywny"
    if sic_in(sic, FINANCIAL_SIC):
        return _na_financial("net_debt_ebitda", name, threshold, SP_SOURCE)
    t = rows[-1] if rows else {}
    missing = [f for f in ("operating_income", "depreciation", "cash") if t.get(f) is None]
    if t.get("long_term_debt") is None and t.get("current_debt") is None:
        missing.append("long_term_debt")
    base = dict(id="net_debt_ebitda", block="health", name=name, threshold=threshold,
                source=SP_SOURCE)
    if missing:
        return criterion(**base, outcome="na", value=None, display="brak danych",
                         missing=missing, meaning="Brak danych o długu lub EBITDA.")

    debt = (t.get("long_term_debt") or 0.0) + (t.get("current_debt") or 0.0)
    net_debt = debt - t["cash"]
    ebitda = t["operating_income"] + t["depreciation"]
    if net_debt <= 0:
        return criterion(**base, outcome="pass", value=None,
                         display="gotówka netto",
                         meaning="Spółka ma więcej gotówki niż długu.")
    if ebitda <= 0:
        return criterion(**base, outcome="fail", value=None, display="EBITDA ujemna",
                         meaning="Spółka ma dług, a działalność nie generuje zysku operacyjnego.")
    ratio = net_debt / ebitda
    if ratio < 3:
        outcome, meaning = "pass", "Dług spłacalny z mniej niż 3 lat zysku operacyjnego."
    elif ratio <= 4:
        outcome, meaning = "warn", "Znaczące zadłużenie: 3–4 lata zysku operacyjnego na spłatę."
    else:
        outcome, meaning = "fail", "Wysokie zadłużenie: ponad 4 lata zysku operacyjnego na spłatę."
    return criterion(**base, outcome=outcome, value=round(ratio, 2), display=_fmt(ratio),
                     meaning=meaning)


def interest_coverage(rows: list[dict], sic: str | None) -> dict:
    name, threshold = "Pokrycie odsetek (EBIT / odsetki)", "≥ 2,5 bezpieczne · 1,5–2,5 słabe · < 1,5 groźne"
    if sic_in(sic, FINANCIAL_SIC):
        return _na_financial("interest_coverage", name, threshold, DAMODARAN_SOURCE)
    t = rows[-1] if rows else {}
    base = dict(id="interest_coverage", block="health", name=name, threshold=threshold,
                source=DAMODARAN_SOURCE)
    ebit, interest = t.get("operating_income"), t.get("interest_expense")
    if ebit is None:
        return criterion(**base, outcome="na", value=None, display="brak danych",
                         missing=["operating_income"], meaning="Brak zysku operacyjnego w danych.")
    if not interest:
        debt = (t.get("long_term_debt") or 0.0) + (t.get("current_debt") or 0.0)
        if debt == 0 and (t.get("long_term_debt") is not None or t.get("current_debt") is not None):
            return criterion(**base, outcome="pass", value=None, display="brak długu",
                             meaning="Spółka nie płaci odsetek, bo nie ma długu.")
        return criterion(**base, outcome="na", value=None, display="brak danych",
                         missing=["interest_expense"], meaning="Brak kosztów odsetek w danych.")
    cov = ebit / interest
    if cov >= 2.5:
        outcome, meaning = "pass", "Zysk operacyjny z zapasem pokrywa odsetki."
    elif cov >= 1.5:
        outcome, meaning = "warn", "Odsetki zjadają dużą część zysku operacyjnego."
    else:
        outcome, meaning = "fail", "Zysk operacyjny ledwo pokrywa (albo nie pokrywa) odsetek."
    return criterion(**base, outcome=outcome, value=round(cov, 2), display=_fmt(cov),
                     meaning=meaning)


def current_ratio(rows: list[dict], sic: str | None) -> dict:
    name, threshold = "Płynność bieżąca (aktywa / zobowiązania bieżące)", "≥ 2 dobra · 1–2 przeciętna · < 1 słaba"
    if sic_in(sic, FINANCIAL_SIC):
        return _na_financial("current_ratio", name, threshold, GRAHAM_SOURCE)
    t = rows[-1] if rows else {}
    base = dict(id="current_ratio", block="health", name=name, threshold=threshold,
                source=GRAHAM_SOURCE)
    cr = div(t.get("current_assets"), t.get("current_liabilities"))
    if cr is None:
        return criterion(**base, outcome="na", value=None, display="brak danych",
                         missing=[f for f in ("current_assets", "current_liabilities")
                                  if t.get(f) is None],
                         meaning="Brak danych o aktywach lub zobowiązaniach bieżących.")
    if cr >= 2:
        outcome, meaning = "pass", "Krótkoterminowe zobowiązania pokryte z dużym zapasem."
    elif cr >= 1:
        outcome, meaning = "warn", "Aktywa bieżące pokrywają zobowiązania, ale bez zapasu Grahama."
    else:
        outcome, meaning = "fail", "Zobowiązania bieżące większe niż aktywa bieżące."
    return criterion(**base, outcome=outcome, value=round(cr, 2), display=_fmt(cr),
                     meaning=meaning)


def health_block(rows: list[dict], sic: str | None) -> list[dict]:
    return [net_debt_to_ebitda(rows, sic), interest_coverage(rows, sic), current_ratio(rows, sic)]
