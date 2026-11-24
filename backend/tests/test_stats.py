import pytest

from stats import (frame_period, industry_percentile, pe_history, percentile,
                   split_factor_after)


def test_percentile_counts_ties_as_half():
    assert percentile(5, [1, 2, 3, 4]) == 100
    assert percentile(0, [1, 2, 3, 4]) == 0
    assert percentile(3, [1, 3, 5, 7]) == pytest.approx(37.5)


@pytest.mark.parametrize("end,year", [("2024-09-28", 2024), ("2024-12-31", 2024),
                                      ("2025-01-31", 2024), ("2024-06-30", 2023)])
def test_frame_period_uses_mostly_overlapping_calendar_year(end, year):
    assert frame_period(end) == year


def peers(n, lo=0.0, step=0.01):
    return [lo + i * step for i in range(n)]


def test_industry_percentile_terciles():
    ps = peers(30)  # 0.00 .. 0.29
    top = industry_percentile(id="m", name="M", company_value=0.28, peer_values=ps, industry="X")
    mid = industry_percentile(id="m", name="M", company_value=0.15, peer_values=ps, industry="X")
    low = industry_percentile(id="m", name="M", company_value=0.02, peer_values=ps, industry="X")
    assert (top["outcome"], mid["outcome"], low["outcome"]) == ("pass", "warn", "fail")
    assert "n=30" in top["display"]


def test_industry_percentile_needs_enough_peers_and_a_value():
    few = industry_percentile(id="m", name="M", company_value=0.1, peer_values=peers(5), industry="X")
    assert few["outcome"] == "na"
    none = industry_percentile(id="m", name="M", company_value=None, peer_values=peers(30), industry="X")
    assert none["outcome"] == "na"


def test_split_factor_counts_only_later_splits():
    splits = [("2014-06-09", 7.0), ("2020-08-31", 4.0)]
    assert split_factor_after("2013-10-30", splits) == 28.0
    assert split_factor_after("2019-10-31", splits) == 4.0
    assert split_factor_after("2021-10-29", splits) == 1.0


def test_pe_history_adjusts_eps_for_later_splits():
    # EPS 8 filed before a 4:1 split -> 2 on today's share basis. Price 40 -> P/E 20.
    eps = [(f"{y}-09-30", 2.0, f"{y}-11-01") for y in range(2015, 2020)]
    eps[0] = ("2015-09-30", 8.0, "2015-11-01")
    eps.append(("2020-09-30", 2.0, "2020-11-01"))
    splits = [("2016-01-01", 4.0)]
    prices = {e[0]: 40.0 for e in eps}
    c = pe_history(eps, prices, current_price=40.0, splits=splits)
    assert c["details"]["history"] == [20.0, 20.0, 20.0, 20.0, 20.0]


def test_pe_history_terciles():
    eps = [(f"{y}-12-31", 1.0, f"{y + 1}-02-01") for y in range(2015, 2022)]
    prices = {e[0]: p for e, p in zip(eps, [10, 15, 20, 25, 30, 35, 0])}
    cheap = pe_history(eps, prices, current_price=11, splits=[])
    dear = pe_history(eps, prices, current_price=34, splits=[])
    assert cheap["outcome"] == "pass" and dear["outcome"] == "fail"


def test_pe_history_loss_and_short_history_are_na():
    eps = [(f"{y}-12-31", 1.0, f"{y + 1}-02-01") for y in range(2018, 2021)]
    prices = {e[0]: 10.0 for e in eps}
    assert pe_history(eps, prices, 10.0, [])["display"] == "za krótka historia"
    loss = eps[:-1] + [("2021-12-31", -1.0, "2022-02-01")]
    assert pe_history(loss, prices, 10.0, [])["display"] == "strata"
