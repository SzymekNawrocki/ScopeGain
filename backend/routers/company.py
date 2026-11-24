from fastapi import APIRouter, Depends, HTTPException, Path

from analysis import analyze
from deps import sec_client
from facts import annual_financials, reporting_currency_ok
from market import MarketUnavailable, company_profile
from sec import SecClient, SecNotConfigured, SecUnavailable

router = APIRouter(prefix="/company", tags=["company"])

TICKER_RE = r"^[A-Za-z0-9.\-]{1,15}$"


def load_company(ticker: str, sec: SecClient) -> dict:
    """CIK, metadata and annual financials for a ticker, or an HTTP error."""
    try:
        cik = sec.cik_for(ticker)
        if cik is None:
            raise HTTPException(
                status_code=404,
                detail=f"SEC nie zna spółki '{ticker.upper()}'. ScopeGain analizuje spółki "
                       "raportujące do SEC (USA). Spółki z GPW sprawdzisz na Biznesradarze.",
            )
        facts = sec.company_facts(cik)
        meta = sec.submissions(cik) or {}
    except SecNotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e))
    except SecUnavailable:
        raise HTTPException(status_code=503, detail="SEC chwilowo nie odpowiada. Spróbuj za chwilę.")

    if not facts:
        raise HTTPException(status_code=404, detail="SEC nie ma danych finansowych tej spółki.")
    return {
        "ticker": ticker.upper(),
        "cik": cik,
        "name": facts.get("entityName") or meta.get("name"),
        "sic": meta.get("sic"),
        "sic_description": meta.get("sicDescription"),
        "usd": reporting_currency_ok(facts),
        "annual": annual_financials(facts),
    }


@router.get("/{ticker}/financials")
def financials(ticker: str = Path(pattern=TICKER_RE), sec: SecClient = Depends(sec_client)):
    company = load_company(ticker, sec)
    latest = company["annual"][-1] if company["annual"] else {}
    company["data_gaps"] = sorted(k for k, v in latest.items() if v is None)
    return company


def market_snapshot(ticker: str) -> dict:
    """Market cap from Yahoo. Missing is fine: criteria that need it become 'no data'."""
    try:
        profile = company_profile(ticker) or {}
    except MarketUnavailable:
        profile = {}
    return {"market_cap": profile.get("market_cap"), "currency": profile.get("currency")}


@router.get("/{ticker}/analysis")
def company_analysis(ticker: str = Path(pattern=TICKER_RE), sec: SecClient = Depends(sec_client)):
    company = load_company(ticker, sec)
    if not company["usd"]:
        raise HTTPException(status_code=422,
                            detail="Spółka raportuje w innej walucie niż USD. ScopeGain tego nie przelicza.")
    if not company["annual"]:
        raise HTTPException(status_code=404, detail="Brak rocznych raportów 10-K w danych SEC.")
    return analyze(company, market_snapshot(ticker))
