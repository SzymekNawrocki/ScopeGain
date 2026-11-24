"""Trust criteria checked against hand calculations of the published formulas.

Each expected number below is worked out by hand from the paper's coefficients,
so a wrong coefficient or a swapped ratio fails the test.
"""

import pytest

from trust import altman, beneish, dilution, piotroski


def row(**kw):
    base = {"fiscal_year_end": "2024-12-31"}
    base.update(kw)
    return base


# --- Altman ------------------------------------------------------------------

BALANCE = dict(total_assets=1000, current_assets=500, current_liabilities=300,
               retained_earnings=300, operating_income=100, total_liabilities=500,
               revenue=1000, equity=500)


def test_altman_z_manufacturer_hand_calculation():
    # X1=0.2 X2=0.3 X3=0.1 X4=1500/500=3 X5=1.0
    # Z = 1.2*0.2 + 1.4*0.3 + 3.3*0.1 + 0.6*3 + 1.0*1 = 3.79
    c = altman([row(**BALANCE)], market_cap=1500, sic="3571")
    assert c["value"] == pytest.approx(3.79)
    assert c["outcome"] == "pass"
    assert c["details"]["model"] == "Z"


def test_altman_z_double_prime_for_non_manufacturer():
    # X4 = book equity / liabilities = 1
    # Z'' = 6.56*0.2 + 3.26*0.3 + 6.72*0.1 + 1.05*1 = 4.01
    c = altman([row(**BALANCE)], market_cap=None, sic="7372")
    assert c["value"] == pytest.approx(4.01)
    assert c["details"]["model"] == "Z''"


@pytest.mark.parametrize("mc,outcome", [(1500, "pass"), (200, "warn"), (1, "warn")])
def test_altman_zones(mc, outcome):
    # mc=200: Z = 0.99 + 0.6*0.4 + 1 = 2.23 (grey); mc=1: Z = 1.99 (still grey)
    assert altman([row(**BALANCE)], market_cap=mc, sic="3571")["outcome"] == outcome


def test_altman_distress_zone():
    weak = dict(BALANCE, current_assets=200, retained_earnings=-300, operating_income=-50,
                revenue=400)
    c = altman([row(**weak)], market_cap=100, sic="3571")
    assert c["value"] < 1.81 and c["outcome"] == "fail"


def test_altman_not_applicable_to_banks_and_missing_data_is_na():
    assert altman([row(**BALANCE)], 1500, sic="6022")["display"] == "nie dotyczy"
    c = altman([row(total_assets=1000)], 1500, sic="3571")
    assert c["outcome"] == "na" and "retained_earnings" in c["missing"]


# --- Beneish -----------------------------------------------------------------

YEAR = dict(revenue=1000, receivables=100, gross_profit=400, current_assets=500, ppe=300,
            total_assets=1000, current_liabilities=200, long_term_debt=100, depreciation=50,
            sga=150, income_continuing=100, cfo=100)


def test_beneish_unchanged_company_hand_calculation():
    # All indices = 1, TATA = 0:
    # M = -4.84 + 0.920 + 0.528 + 0.404 + 0.892 + 0.115 - 0.172 - 0.327 = -2.48
    c = beneish([row(**YEAR), row(**YEAR)], sic="3571")
    assert c["value"] == pytest.approx(-2.48)
    assert c["outcome"] == "pass" and c["knockout"] is False


def test_beneish_flags_accruals_and_fast_growth_as_knockout():
    # SGI = 1.5 adds 0.892*0.5 = 0.446; receivables keep pace (DSRI = 1);
    # TATA = (250 - 100)/1500 = 0.1 adds 0.468. M = -2.48 + 0.446 + 0.468 = -1.566
    cur = dict(YEAR, revenue=1500, receivables=150, gross_profit=600, current_assets=750,
               ppe=450, total_assets=1500, current_liabilities=300, long_term_debt=150,
               depreciation=75, sga=225, income_continuing=250, cfo=100)
    c = beneish([row(**YEAR), row(**cur)], sic="3571")
    assert c["value"] == pytest.approx(-1.57, abs=0.01)
    assert c["outcome"] == "fail" and c["knockout"] is True


def test_beneish_missing_sga_is_assumed_neutral_and_disclosed():
    y = dict(YEAR, sga=None)
    c = beneish([row(**y), row(**y)], sic="3571")
    assert c["value"] == pytest.approx(-2.48)
    assert "SGAI = 1" in c["meaning"]


def test_beneish_needs_two_full_years():
    c = beneish([row(**YEAR)], sic="3571")
    assert c["outcome"] == "na" and c["knockout"] is False


# --- Piotroski ---------------------------------------------------------------

def year(**kw):
    base = dict(net_income=100, total_assets=1000, cfo=150, long_term_debt=200,
                current_assets=500, current_liabilities=250, shares_diluted=100,
                gross_profit=400, revenue=1000)
    base.update(kw)
    return row(**base)


def test_piotroski_all_nine_signals_pass():
    rows = [
        year(),
        year(net_income=80, long_term_debt=300, current_assets=450, shares_diluted=105,
             gross_profit=350, revenue=900),
        year(net_income=120, long_term_debt=150, current_assets=600, shares_diluted=100,
             gross_profit=440, revenue=1100, cfo=200),
    ]
    c = piotroski(rows)
    assert c["value"] == 9 and c["outcome"] == "pass"
    assert all(v == 1 for v in c["details"]["signals"].values())


def test_piotroski_all_nine_signals_fail():
    rows = [
        year(),
        year(net_income=50, long_term_debt=100, current_assets=600, shares_diluted=100,
             gross_profit=450, revenue=1200),
        year(net_income=-10, cfo=-20, long_term_debt=400, current_assets=400,
             shares_diluted=120, gross_profit=300, revenue=1000),
    ]
    c = piotroski(rows)
    assert c["value"] == 0 and c["outcome"] == "fail"


def test_piotroski_unknown_signals_never_count_as_passed():
    c = piotroski([year(), year()])  # no year t-2 -> ΔROA, Δleverage, Δturnover unknown
    assert c["value"] is None
    assert "ΔROA > 0" in c["missing"]
    assert "brak 3 z 9" in c["display"]


# --- Dilution ----------------------------------------------------------------

def test_dilution_buybacks_pass_and_issuance_fails():
    shrinking = [row(shares_diluted=s) for s in (110, 105, 100)]
    growing = [row(shares_diluted=s) for s in (100, 105, 110)]
    assert dilution(shrinking)["outcome"] == "pass"
    assert dilution(growing)["outcome"] == "fail"
    assert dilution([row(shares_diluted=100)])["outcome"] == "na"
