from datetime import date

import pytest

from dividends import (annual_totals, dividend_block, dividend_streak, net_dividend, net_factor,
                       payout_from_fcf, ttm, years_without_cut)

TODAY = date(2026, 11, 24)


def test_net_factor_with_and_without_w8ben():
    # 15% US + 4% PL top-up -> 81%; 30% US, credit capped at treaty 15%, +4% -> 66%
    assert net_factor(True) == pytest.approx(0.81)
    assert net_factor(False) == pytest.approx(0.66)


def test_net_dividend_per_1000_pln():
    # yield 4% gross -> 40 PLN gross per 1000 PLN, 32.40 PLN net with W-8BEN
    out = net_dividend(dps_ttm=4.0, price_usd=100.0, usd_pln=4.0)
    assert out["gross_yield_pct"] == 4.0
    assert out["net_per_1000_pln"] == pytest.approx(32.4)
    assert out["net_per_1000_pln_no_w8ben"] == pytest.approx(26.4)
    assert out["dps_net_pln"] == pytest.approx(4.0 * 0.81 * 4.0)


def test_net_dividend_without_price_has_no_yield():
    out = net_dividend(1.0, None, None)
    assert out["gross_yield_pct"] is None and "net_per_1000_pln" not in out


def quarterly(year, amount):
    return [(f"{year}-{m:02d}-15", amount) for m in (2, 5, 8, 11)]


def test_annual_totals_skip_current_year_and_ttm():
    pays = quarterly(2024, 0.25) + quarterly(2025, 0.26) + quarterly(2026, 0.27)
    assert annual_totals(pays, TODAY) == {2024: 0.25, 2025: pytest.approx(0.26)}
    assert ttm(pays, TODAY) == pytest.approx(0.27 * 4)


def test_years_without_cut_stops_at_a_cut_or_gap():
    assert years_without_cut({y: 1.0 + 0.1 * (y - 2010) for y in range(2010, 2026)}) == 16
    assert years_without_cut({2020: 2.0, 2021: 1.0, 2022: 1.1, 2023: 1.2}) == 3
    assert years_without_cut({2020: 1.0, 2022: 1.0, 2023: 1.0}) == 2
    assert years_without_cut({2024: 1.0, 2025: 0.995}) == 2  # within 1% tolerance


def test_streak_criterion_zones_and_non_payer():
    assert dividend_streak({y: 1.0 for y in range(2010, 2026)})["outcome"] == "pass"
    assert dividend_streak({y: 1.0 for y in range(2019, 2026)})["outcome"] == "warn"
    assert dividend_streak({2024: 1.0, 2025: 1.0})["outcome"] == "fail"
    assert dividend_streak({})["display"] == "nie dotyczy"


def r(**kw):
    return {"fiscal_year_end": "2025-12-31", **kw}


def test_payout_from_fcf():
    assert payout_from_fcf([r(dividends_paid=50, cfo=150, capex=50)], True)["outcome"] == "pass"
    assert payout_from_fcf([r(dividends_paid=90, cfo=150, capex=50)], True)["outcome"] == "warn"
    assert payout_from_fcf([r(dividends_paid=120, cfo=150, capex=50)], True)["outcome"] == "fail"
    assert payout_from_fcf([r(dividends_paid=10, cfo=50, capex=60)], True)["display"] == "FCF ujemny"
    assert payout_from_fcf([r()], False)["display"] == "nie dotyczy"


def test_non_payer_block_is_not_applicable_everywhere():
    block = dividend_block([r()], [], TODAY)
    assert all(c["display"] == "nie dotyczy" for c in block)


def test_payment_slipping_into_next_year_is_not_a_cut():
    pays = quarterly(2022, 0.5) + quarterly(2023, 0.5)[:3] + quarterly(2024, 0.5) + [("2024-01-02", 0.5)]
    assert years_without_cut(annual_totals(pays, TODAY)) == 3


def test_special_dividend_does_not_reset_the_streak():
    pays = quarterly(2023, 0.5) + quarterly(2024, 0.5) + [("2024-12-20", 5.0)] + quarterly(2025, 0.5)
    assert years_without_cut(annual_totals(pays, TODAY)) == 3
