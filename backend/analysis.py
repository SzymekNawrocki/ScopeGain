"""One place that runs every criterion for a company and builds the verdict."""

from datetime import date

from health import health_block
from trust import trust_block
from valuation import valuation_block
from verdict import build_verdict


def analyze(company: dict, market: dict) -> dict:
    """company: output of routers.company.load_company; market: {"market_cap": float|None, ...}."""
    rows = company["annual"]
    sic = company.get("sic")
    mc = market.get("market_cap")
    criteria = (
        trust_block(rows, mc, sic)
        + valuation_block(rows, mc)
        + health_block(rows, sic)
        + market.get("extra_criteria", [])
    )
    verdict = build_verdict(criteria)
    latest = rows[-1]["fiscal_year_end"] if rows else None
    return {
        "ticker": company["ticker"],
        "name": company["name"],
        "sic": sic,
        "sic_description": company.get("sic_description"),
        "fiscal_year_end": latest,
        "years_of_data": len(rows),
        "market_cap": mc,
        "dividend": market.get("dividend"),
        "as_of": date.today().isoformat(),
        "caveat": "Werdykt opisuje stan spółki według ostatniego raportu rocznego. "
                  "Nie jest obietnicą zysku.",
        **verdict,
    }
