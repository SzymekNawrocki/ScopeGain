"""Gathers the data for stats.py criteria (SEC frames, SIC peers, Yahoo prices)."""

from facts import eps_points
from market import MarketUnavailable, closes_on, split_history
from sec import SecClient, SecUnavailable
from stats import frame_period, industry_percentile, pe_history
from criteria import criterion

REVENUE_TAGS = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"]


def _revenue_frame(sec: SecClient, year: int) -> dict[int, float]:
    merged: dict[int, float] = {}
    for tag in reversed(REVENUE_TAGS):  # first tag in the list wins
        merged.update(sec.frame(tag, f"CY{year}"))
    return merged


def _ratio_values(num: dict[int, float], den: dict[int, float], ciks: set[int]) -> dict[int, float]:
    return {c: num[c] / den[c] for c in ciks if c in num and c in den and den[c] > 0}


def industry_criteria(company: dict, sec: SecClient) -> list[dict]:
    rows, sic = company["annual"], company.get("sic")
    names = [("op_margin_pct", "Marża operacyjna na tle branży"),
             ("roa_pct", "Zwrot z aktywów (ROA) na tle branży")]
    if not rows or not sic:
        return [industry_percentile(id=i, name=n, company_value=None, peer_values=[],
                                    industry=None) for i, n in names]
    latest = rows[-1]
    try:
        year = frame_period(latest["fiscal_year_end"])
        peers = set(sec.sic_peers(sic)) - {company["cik"]}
        revenue = _revenue_frame(sec, year)
        op = sec.frame("OperatingIncomeLoss", f"CY{year}")
        ni = sec.frame("NetIncomeLoss", f"CY{year}")
        assets = sec.frame("Assets", f"CY{year}Q4I")
    except SecUnavailable:
        return [criterion(id=i, block="health", name=n, outcome="na", value=None,
                          display="brak danych", threshold="—", source="SEC frames",
                          missing=["SEC frames"], meaning="SEC nie odpowiedział.")
                for i, n in names]

    industry = company.get("sic_description")
    op_margins = _ratio_values(op, revenue, peers)
    roas = _ratio_values(ni, assets, peers)
    own_margin = (latest["operating_income"] / latest["revenue"]
                  if latest.get("operating_income") is not None and latest.get("revenue") else None)
    own_roa = (latest["net_income"] / latest["total_assets"]
               if latest.get("net_income") is not None and latest.get("total_assets") else None)
    return [
        industry_percentile(id="op_margin_pct", name=names[0][1], company_value=own_margin,
                            peer_values=list(op_margins.values()), industry=industry),
        industry_percentile(id="roa_pct", name=names[1][1], company_value=own_roa,
                            peer_values=list(roas.values()), industry=industry),
    ]


def history_criteria(company: dict, facts_payload: dict | None, ticker: str) -> list[dict]:
    points = eps_points(facts_payload or {})
    try:
        prices, current = closes_on(ticker, [p[0] for p in points])
        splits = split_history(ticker)
    except MarketUnavailable:
        prices, current, splits = {}, None, []
    return [pe_history(points, prices, current, splits)]
