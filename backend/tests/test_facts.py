from facts import annual_financials, reporting_currency_ok
from tests.helpers import dur, facts, inst


def test_one_row_per_fiscal_year_oldest_first():
    rows = annual_financials(facts({
        "Revenues": [dur(2023, 100), dur(2024, 120)],
        "Assets": [inst(2023, 500), inst(2024, 550)],
    }))
    assert [r["fiscal_year_end"] for r in rows] == ["2023-09-30", "2024-09-30"]
    assert rows[1]["revenue"] == 120 and rows[1]["total_assets"] == 550


def test_restatement_filed_later_wins():
    rows = annual_financials(facts({"Revenues": [
        dur(2023, 100, filed="2023-11-01"),
        dur(2023, 95, filed="2024-11-01"),  # comparative in next year's 10-K, restated
    ]}))
    assert rows[0]["revenue"] == 95


def test_quarterly_and_non_annual_forms_are_ignored():
    q = {"start": "2024-07-01", "end": "2024-09-30", "val": 30, "form": "10-K", "filed": "2024-11-01"}
    tenq = dur(2024, 999, form="10-Q")
    rows = annual_financials(facts({"Revenues": [dur(2024, 120), q, tenq]}))
    assert len(rows) == 1 and rows[0]["revenue"] == 120


def test_falls_back_to_second_tag_when_first_missing_for_year():
    rows = annual_financials(facts({
        "Revenues": [dur(2022, 80)],
        "RevenueFromContractWithCustomerExcludingAssessedTax": [dur(2023, 100)],
    }))
    assert [r["revenue"] for r in rows] == [80, 100]


def test_missing_values_stay_none_and_derived_values_are_filled():
    rows = annual_financials(facts({
        "Revenues": [dur(2024, 100)],
        "CostOfRevenue": [dur(2024, 60)],
        "LiabilitiesAndStockholdersEquity": [inst(2024, 300)],
        "StockholdersEquity": [inst(2024, 120)],
    }))
    r = rows[0]
    assert r["gross_profit"] == 40
    assert r["total_liabilities"] == 180
    assert r["retained_earnings"] is None


def test_per_share_units():
    rows = annual_financials(facts(
        {"Revenues": [dur(2024, 100)], "EarningsPerShareDiluted": [dur(2024, 6.1)]},
        unit_overrides={"EarningsPerShareDiluted": "USD/shares"},
    ))
    assert rows[0]["eps_diluted"] == 6.1


def test_no_us_gaap_means_no_rows_and_currency_check():
    assert annual_financials({"facts": {"ifrs-full": {}}}) == []
    assert reporting_currency_ok(facts({"Assets": [inst(2024, 1)]}))
    assert not reporting_currency_ok({"facts": {"us-gaap": {"Assets": {"units": {"EUR": []}}}}})


def test_eps_points_keep_filing_date_for_split_adjustment():
    from facts import eps_points
    payload = facts({"EarningsPerShareDiluted": [
        dur(2019, 11.89, filed="2019-10-31"),
        dur(2019, 2.97, filed="2021-10-29"),  # restated after the 2020 4:1 split
        dur(2020, 3.28, filed="2020-10-30"),
    ]}, unit_overrides={"EarningsPerShareDiluted": "USD/shares"})
    assert eps_points(payload) == [("2019-09-30", 2.97, "2021-10-29"),
                                   ("2020-09-30", 3.28, "2020-10-30")]
