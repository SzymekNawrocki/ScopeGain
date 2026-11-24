import pytest
from fastapi.testclient import TestClient

from analysis import analyze
from criteria import criterion
from health import current_ratio, interest_coverage, net_debt_to_ebitda
from valuation import graham_multiplier
from verdict import block_status, build_verdict


def c(block, outcome, id=None, knockout=False, display="x"):
    return criterion(id=id or f"{block}-{outcome}", block=block, name=id or "K", outcome=outcome,
                     value=None, display=display, threshold="t", source="s", meaning="m",
                     knockout=knockout)


# --- block status ------------------------------------------------------------

@pytest.mark.parametrize("outcomes,status", [
    (["pass", "pass"], "good"),
    (["pass", "warn"], "good"),
    (["pass", "fail"], "mixed"),
    (["warn", "warn"], "mixed"),
    (["fail", "warn"], "bad"),
    (["na", "na"], "na"),
])
def test_block_status(outcomes, status):
    assert block_status([c("trust", o) for o in outcomes])["status"] == status


# --- overall rule ------------------------------------------------------------

def test_knockout_wins_over_everything():
    v = build_verdict([c("trust", "fail", id="Beneish", knockout=True), c("trust", "pass"),
                       c("trust", "pass"), c("health", "pass"), c("valuation", "pass")])
    assert v["grade"] == "bad" and "Wykluczona" in v["reason"]


def test_good_needs_trust_good_and_two_good_blocks():
    v = build_verdict([c("trust", "pass"), c("health", "pass"), c("valuation", "warn")])
    assert v["grade"] == "good"
    v = build_verdict([c("trust", "pass"), c("health", "warn"), c("valuation", "warn")])
    assert v["grade"] == "mixed"


def test_two_bad_blocks_is_bad():
    v = build_verdict([c("trust", "pass"), c("health", "fail"), c("valuation", "fail")])
    assert v["grade"] == "bad"


def test_too_little_data_caps_at_mixed():
    v = build_verdict([c("trust", "pass"), c("health", "pass"), c("trust", "na"),
                       c("trust", "na"), c("valuation", "na")])
    assert v["grade"] == "mixed" and "Za mało danych" in v["reason"]
    assert len(v["data_gaps"]) == 3


def test_not_applicable_does_not_count_as_missing_data():
    v = build_verdict([c("trust", "pass"), c("health", "pass"),
                       c("trust", "na", display="nie dotyczy")])
    assert v["coverage"] == {"checked": 2, "applicable": 2}
    assert v["data_gaps"] == []


def test_pros_and_cons_come_from_outcomes():
    v = build_verdict([c("trust", "pass", id="A"), c("health", "fail", id="B"),
                       c("health", "warn", id="C")])
    assert [p["id"] for p in v["pros"]] == ["A"]
    assert [x["id"] for x in v["cons"]] == ["B", "C"]


# --- health & valuation criteria --------------------------------------------

def r(**kw):
    return {"fiscal_year_end": "2024-12-31", **kw}


def test_net_debt_to_ebitda_zones_and_net_cash():
    base = dict(operating_income=80, depreciation=20, cash=50)
    assert net_debt_to_ebitda([r(**base, long_term_debt=250)], "3571")["outcome"] == "pass"  # 2.0
    assert net_debt_to_ebitda([r(**base, long_term_debt=400)], "3571")["outcome"] == "warn"  # 3.5
    assert net_debt_to_ebitda([r(**base, long_term_debt=600)], "3571")["outcome"] == "fail"  # 5.5
    assert net_debt_to_ebitda([r(**base, long_term_debt=10)], "3571")["display"] == "gotówka netto"
    assert net_debt_to_ebitda([r(**base, long_term_debt=10)], "6022")["display"] == "nie dotyczy"


def test_interest_coverage_and_no_debt():
    assert interest_coverage([r(operating_income=100, interest_expense=20)], "1")["value"] == 5
    assert interest_coverage([r(operating_income=100, interest_expense=50)], "1")["outcome"] == "warn"
    assert interest_coverage([r(operating_income=100, interest_expense=80)], "1")["outcome"] == "fail"
    no_debt = interest_coverage([r(operating_income=100, long_term_debt=0)], "1")
    assert no_debt["outcome"] == "pass" and no_debt["display"] == "brak długu"
    assert interest_coverage([r(operating_income=100)], "1")["outcome"] == "na"


def test_current_ratio_graham():
    assert current_ratio([r(current_assets=200, current_liabilities=100)], "1")["outcome"] == "pass"
    assert current_ratio([r(current_assets=150, current_liabilities=100)], "1")["outcome"] == "warn"
    assert current_ratio([r(current_assets=50, current_liabilities=100)], "1")["outcome"] == "fail"


def test_graham_multiplier_hand_calculation():
    # P/E = 1500/100 = 15, P/B = 1500/1000 = 1.5, product = 22.5 -> pass (boundary)
    g = graham_multiplier([r(net_income=100, equity=1000)], market_cap=1500)
    assert g["value"] == 22.5 and g["outcome"] == "pass"
    assert graham_multiplier([r(net_income=100, equity=500)], 1500)["outcome"] == "fail"
    assert graham_multiplier([r(net_income=-5, equity=500)], 1500)["display"] == "strata"
    assert graham_multiplier([r(net_income=100, equity=500)], None)["outcome"] == "na"


# --- end to end over the API with a fake SEC --------------------------------

def test_analysis_endpoint_end_to_end(monkeypatch):
    import main
    from routers import company as company_router
    from deps import sec_client

    rows = []
    for year, ni in ((2022, 90), (2023, 100), (2024, 120)):
        rows.append(dict(fiscal_year_end=f"{year}-12-31", net_income=ni, revenue=1000 + ni,
                         gross_profit=400 + ni, cogs=600, total_assets=1000, current_assets=500,
                         current_liabilities=200, total_liabilities=400, equity=600,
                         retained_earnings=300, operating_income=ni + 30, cfo=ni + 40,
                         long_term_debt=100, current_debt=0, cash=150, depreciation=40,
                         interest_expense=5, receivables=100, ppe=300, sga=150,
                         income_continuing=ni, shares_diluted=100))

    monkeypatch.setattr(company_router, "load_company", lambda t, sec: {
        "ticker": t.upper(), "cik": 1, "name": "Test", "sic": "3571",
        "sic_description": "Computers", "usd": True, "annual": rows})
    monkeypatch.setattr(company_router, "market_snapshot", lambda t: {"market_cap": 1500})
    monkeypatch.setattr(company_router, "extra_criteria", lambda c, s, t: [])
    monkeypatch.setattr(company_router, "dividend_section", lambda c, t: (None, []))
    main.app.dependency_overrides[sec_client] = lambda: None
    try:
        res = TestClient(main.app).get("/company/test/analysis")
    finally:
        main.app.dependency_overrides.clear()
    body = res.json()
    assert res.status_code == 200
    assert body["grade"] in {"good", "mixed", "bad"}
    assert set(body["blocks"]) == {"trust", "valuation", "health"}
    assert body["fiscal_year_end"] == "2024-12-31"


def test_analyze_without_market_cap_marks_gaps():
    rows = [{"fiscal_year_end": "2024-12-31", "net_income": 10, "equity": 100}]
    out = analyze({"ticker": "X", "name": "X", "annual": rows, "sic": "3571"}, {"market_cap": None})
    gap_names = [g["criterion"] for g in out["data_gaps"]]
    assert "Mnożnik Grahama (C/Z × C/WK)" in gap_names
