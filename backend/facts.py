"""Turn SEC `companyfacts` into a clean table of annual (10-K) financials.

XBRL is messy: the same line item has several possible tags (Revenues vs
RevenueFromContractWithCustomer...), every 10-K repeats prior years as
comparatives, and restatements appear in later filings. The rules here:

- duration items (revenue, income, cash flow): 10-K entries covering ~1 year
  (300-400 days); one value per period end, the most recently filed wins;
- instant items (assets, debt): 10-K entries whose date matches a fiscal-year end;
- for each field, tags are tried in order and the first tag that has a value
  for that year is used.

Nothing is guessed: a value that is not in the filings stays None.
"""

from datetime import date

# field -> (kind, unit, [tags in order of preference])
FIELDS: dict[str, tuple[str, str, list[str]]] = {
    "revenue": ("duration", "USD", [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
    ]),
    "cogs": ("duration", "USD", [
        "CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold",
    ]),
    "gross_profit": ("duration", "USD", ["GrossProfit"]),
    "operating_income": ("duration", "USD", ["OperatingIncomeLoss"]),
    "net_income": ("duration", "USD", ["NetIncomeLoss", "ProfitLoss"]),
    "income_continuing": ("duration", "USD", [
        "IncomeLossFromContinuingOperations", "NetIncomeLoss",
    ]),
    "cfo": ("duration", "USD", [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ]),
    "capex": ("duration", "USD", [
        "PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets",
    ]),
    "dividends_paid": ("duration", "USD", [
        "PaymentsOfDividendsCommonStock", "PaymentsOfDividends",
    ]),
    "dps": ("duration", "USD/shares", [
        "CommonStockDividendsPerShareDeclared", "CommonStockDividendsPerShareCashPaid",
    ]),
    "eps_diluted": ("duration", "USD/shares", ["EarningsPerShareDiluted", "EarningsPerShareBasic"]),
    "interest_expense": ("duration", "USD", [
        "InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt",
    ]),
    "depreciation": ("duration", "USD", [
        "DepreciationDepletionAndAmortization", "DepreciationAndAmortization",
        "DepreciationAmortizationAndAccretionNet", "Depreciation",
    ]),
    "sga": ("duration", "USD", ["SellingGeneralAndAdministrativeExpense"]),
    "shares_diluted": ("duration", "shares", [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "WeightedAverageNumberOfSharesOutstandingBasic",
    ]),
    "total_assets": ("instant", "USD", ["Assets"]),
    "current_assets": ("instant", "USD", ["AssetsCurrent"]),
    "current_liabilities": ("instant", "USD", ["LiabilitiesCurrent"]),
    "total_liabilities": ("instant", "USD", ["Liabilities"]),
    "equity": ("instant", "USD", [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ]),
    "liabilities_and_equity": ("instant", "USD", ["LiabilitiesAndStockholdersEquity"]),
    "retained_earnings": ("instant", "USD", ["RetainedEarningsAccumulatedDeficit"]),
    "receivables": ("instant", "USD", ["AccountsReceivableNetCurrent", "ReceivablesNetCurrent"]),
    "ppe": ("instant", "USD", ["PropertyPlantAndEquipmentNet"]),
    "long_term_debt": ("instant", "USD", [
        "LongTermDebtNoncurrent", "LongTermDebt", "LongTermDebtAndCapitalLeaseObligations",
    ]),
    "current_debt": ("instant", "USD", [
        "LongTermDebtCurrent", "DebtCurrent", "ShortTermBorrowings",
    ]),
    "cash": ("instant", "USD", [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ]),
}

ANNUAL_FORMS = {"10-K", "10-K/A", "10-KT"}
MAX_YEARS = 12
MATCH_DAYS = 10  # an instant counts for a fiscal year if within this many days of its end


def _d(s: str) -> date:
    return date.fromisoformat(s)


def _annual_duration(entries: list[dict]) -> dict[date, float]:
    best: dict[date, tuple[str, float]] = {}
    for e in entries:
        if e.get("form") not in ANNUAL_FORMS or "start" not in e:
            continue
        days = (_d(e["end"]) - _d(e["start"])).days
        if not 300 <= days <= 400:
            continue
        end = _d(e["end"])
        filed = e.get("filed", "")
        if end not in best or filed > best[end][0]:
            best[end] = (filed, float(e["val"]))
    return {k: v for k, (_, v) in best.items()}


def _annual_instant(entries: list[dict]) -> dict[date, float]:
    best: dict[date, tuple[str, float]] = {}
    for e in entries:
        if e.get("form") not in ANNUAL_FORMS or "start" in e:
            continue
        end = _d(e["end"])
        filed = e.get("filed", "")
        if end not in best or filed > best[end][0]:
            best[end] = (filed, float(e["val"]))
    return {k: v for k, (_, v) in best.items()}


def _series(gaap: dict, kind: str, unit: str, tags: list[str]) -> list[dict[date, float]]:
    out = []
    for tag in tags:
        entries = gaap.get(tag, {}).get("units", {}).get(unit)
        if not entries:
            continue
        out.append(_annual_duration(entries) if kind == "duration" else _annual_instant(entries))
    return out


def _pick(series: list[dict[date, float]], fy_end: date) -> float | None:
    for s in series:
        for d, v in s.items():
            if abs((d - fy_end).days) <= MATCH_DAYS:
                return v
    return None


def annual_financials(companyfacts: dict) -> list[dict]:
    """Annual rows, oldest first: {"fiscal_year_end": "YYYY-MM-DD", field: value|None}."""
    gaap = companyfacts.get("facts", {}).get("us-gaap", {})
    if not gaap:
        return []

    series = {f: _series(gaap, kind, unit, tags) for f, (kind, unit, tags) in FIELDS.items()}

    # Fiscal-year ends are anchored on income-statement periods (revenue, then net income).
    anchors: set[date] = set()
    for f in ("revenue", "net_income"):
        for s in series[f]:
            anchors |= set(s)
    # Collapse anchors that are a few days apart (52/53-week years, tag differences).
    ends: list[date] = []
    for d in sorted(anchors):
        if ends and (d - ends[-1]).days <= MATCH_DAYS:
            ends[-1] = d
        else:
            ends.append(d)
    ends = ends[-MAX_YEARS:]

    rows = []
    for end in ends:
        row: dict = {"fiscal_year_end": end.isoformat()}
        for f in FIELDS:
            row[f] = _pick(series[f], end)
        if row["total_liabilities"] is None and row["liabilities_and_equity"] is not None \
                and row["equity"] is not None:
            row["total_liabilities"] = row["liabilities_and_equity"] - row["equity"]
        if row["gross_profit"] is None and row["revenue"] is not None and row["cogs"] is not None:
            row["gross_profit"] = row["revenue"] - row["cogs"]
        rows.append(row)
    return rows


def reporting_currency_ok(companyfacts: dict) -> bool:
    """True when the filer reports core figures in USD (we do not convert others)."""
    gaap = companyfacts.get("facts", {}).get("us-gaap", {})
    assets = gaap.get("Assets", {}).get("units", {})
    return "USD" in assets if assets else bool(gaap)


def eps_points(companyfacts: dict) -> list[tuple[str, float, str]]:
    """(fiscal_year_end, diluted EPS, filed) per year, oldest first.

    The filing date matters: EPS is stated on the share count at filing time,
    so later stock splits must be applied before comparing with today's prices.
    """
    gaap = companyfacts.get("facts", {}).get("us-gaap", {})
    best: dict[date, tuple[str, float]] = {}
    for tag in ("EarningsPerShareDiluted", "EarningsPerShareBasic"):
        for e in gaap.get(tag, {}).get("units", {}).get("USD/shares", []):
            if e.get("form") not in ANNUAL_FORMS or "start" not in e:
                continue
            if not 300 <= (_d(e["end"]) - _d(e["start"])).days <= 400:
                continue
            end, filed = _d(e["end"]), e.get("filed", "")
            if end not in best or filed > best[end][0]:
                best[end] = (filed, float(e["val"]))
        if best:
            break
    return [(d.isoformat(), v, f) for d, (f, v) in sorted(best.items())][-MAX_YEARS:]
