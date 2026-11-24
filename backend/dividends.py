"""Dividend block: how much lands in a Polish investor's pocket, and is it safe?

Tax mechanics for a Polish tax resident holding US shares (ordinary account):
- the US withholds 15% with a W-8BEN on file (Poland-US treaty), 30% without;
- Poland taxes dividends at 19% (PIT-38, section G, art. 30a). Foreign tax can be
  credited only up to the treaty rate (KIS interpretation 0113-KDIPT2-3.4011.303.2025.2.NM,
  NSA II FSK 1171/22), so the Polish top-up is 4% in both cases.
  Net with W-8BEN: 100 - 15 - 4 = 81%. Without: 100 - 30 - 4 = 66%.
"""

from datetime import date

from criteria import criterion

PL_RATE = 0.19
US_TREATY_RATE = 0.15
US_STATUTORY_RATE = 0.30

TAX_SOURCE = (
    "Umowa PL-USA o unikaniu podwójnego opodatkowania (1974), art. 11: 15%; ustawa o PIT "
    "art. 30a ust. 1 pkt 4 i ust. 9; interpretacja KIS 0113-KDIPT2-3.4011.303.2025.2.NM."
)
PAYOUT_SOURCE = (
    "Dividends paid / free cash flow (CFO − capex). Above 100% the dividend is paid from "
    "debt or cash reserves; the 75% warning line is a convention."
)
STREAK_SOURCE = (
    "Nasdaq US Broad Dividend Achievers (≥ 10 consecutive years of increases) and S&P 500 "
    "Dividend Aristocrats (≥ 25); here the milder test: years without a cut."
)
CUT_TOLERANCE = 0.01  # a drop below 1% is rounding/FX noise, not a cut


def net_factor(w8ben: bool = True) -> float:
    withheld = US_TREATY_RATE if w8ben else US_STATUTORY_RATE
    credited = min(withheld, US_TREATY_RATE, PL_RATE)
    top_up = max(PL_RATE - credited, 0.0)
    return 1.0 - withheld - top_up


def annual_totals(payments: list[tuple[str, float]], today: date) -> dict[int, float]:
    """Regular dividend per payment for each full calendar year (median of that year's payments).

    A median, not a sum: when one quarterly payment slips into the next calendar
    year, the sum drops and looks like a cut, while the regular rate did not change.
    A one-off special dividend does not move the median either.
    """
    by_year: dict[int, list[float]] = {}
    for when, amount in payments:
        y = int(when[:4])
        if y < today.year:
            by_year.setdefault(y, []).append(amount)
    out = {}
    for y, amounts in by_year.items():
        a = sorted(amounts)
        mid = len(a) // 2
        out[y] = a[mid] if len(a) % 2 else (a[mid - 1] + a[mid]) / 2
    return out


def ttm(payments: list[tuple[str, float]], today: date) -> float:
    cutoff = date(today.year - 1, today.month, min(today.day, 28)).isoformat()
    return sum(a for d, a in payments if d > cutoff)


def years_without_cut(totals: dict[int, float]) -> int:
    """Consecutive full years, counting back from the latest, with no dividend cut."""
    years = sorted(totals)
    if not years:
        return 0
    streak = 1
    for prev, cur in zip(reversed(years[:-1]), reversed(years[1:])):
        if cur - prev != 1 or totals[cur] < totals[prev] * (1 - CUT_TOLERANCE):
            break
        streak += 1
    return streak


def net_dividend(dps_ttm: float, price_usd: float | None, usd_pln: float | None) -> dict:
    """What a dividend is worth to the owner, in PLN, for the next 12 months (TTM-based)."""
    gross_yield = dps_ttm / price_usd if price_usd else None
    out = {
        "dps_ttm_usd": round(dps_ttm, 4),
        "gross_yield_pct": round(gross_yield * 100, 2) if gross_yield is not None else None,
        "net_factor_w8ben": net_factor(True),
        "net_factor_no_w8ben": net_factor(False),
        "usd_pln": usd_pln,
        "source": TAX_SOURCE,
        "assumptions": [
            "Dywidenda z ostatnich 12 miesięcy powtórzy się w kolejnych 12.",
            "Zwykły rachunek maklerski (nie IKE/IKZE) i złożony formularz W-8BEN.",
            "Kurs NBP z dnia poprzedzającego wypłatę zmieni kwotę w PLN; tu kurs bieżący.",
        ],
    }
    if gross_yield is not None:
        out["net_per_1000_pln"] = round(1000 * gross_yield * net_factor(True), 2)
        out["net_per_1000_pln_no_w8ben"] = round(1000 * gross_yield * net_factor(False), 2)
    if usd_pln:
        out["dps_net_pln"] = round(dps_ttm * net_factor(True) * usd_pln, 4)
    return out


def _not_payer(id: str, name: str, threshold: str, source: str) -> dict:
    return criterion(id=id, block="dividend", name=name, outcome="na", value=None,
                     display="nie dotyczy", threshold=threshold, source=source,
                     meaning="Spółka nie płaci dywidendy.")


def payout_from_fcf(rows: list[dict], pays: bool) -> dict:
    name, threshold = "Dywidenda / wolne przepływy (FCF)", "≤ 75% bezpieczna · 75–100% napięta · > 100% z długu"
    if not pays:
        return _not_payer("payout_fcf", name, threshold, PAYOUT_SOURCE)
    t = rows[-1] if rows else {}
    base = dict(id="payout_fcf", block="dividend", name=name, threshold=threshold,
                source=PAYOUT_SOURCE)
    missing = [f for f in ("dividends_paid", "cfo", "capex") if t.get(f) is None]
    if missing:
        return criterion(**base, outcome="na", value=None, display="brak danych",
                         missing=missing, meaning="Brak danych o dywidendach lub przepływach.")
    fcf = t["cfo"] - t["capex"]
    if fcf <= 0:
        return criterion(**base, outcome="fail", value=None, display="FCF ujemny",
                         meaning="Spółka nie generuje wolnej gotówki, a płaci dywidendę.")
    ratio = t["dividends_paid"] / fcf
    if ratio <= 0.75:
        outcome, meaning = "pass", "Dywidenda z zapasem mieści się w wolnej gotówce."
    elif ratio <= 1.0:
        outcome, meaning = "warn", "Dywidenda zjada prawie całą wolną gotówkę."
    else:
        outcome, meaning = "fail", "Dywidenda większa niż wolna gotówka: płacona z długu lub rezerw."
    return criterion(**base, outcome=outcome, value=round(ratio * 100, 1),
                     display=f"{ratio * 100:.0f}%", meaning=meaning)


def dividend_streak(totals: dict[int, float]) -> dict:
    name, threshold = "Lata bez cięcia dywidendy", "≥ 10 ✅ · 5–9 🟡 · < 5 ❌"
    if not totals:
        return _not_payer("dividend_streak", name, threshold, STREAK_SOURCE)
    n = years_without_cut(totals)
    if n >= 10:
        outcome, meaning = "pass", "Spółka od co najmniej 10 lat nie obcięła dywidendy."
    elif n >= 5:
        outcome, meaning = "warn", "Kilka lat bez cięcia: historia krótka albo było cięcie."
    else:
        outcome, meaning = "fail", "Dywidenda była niedawno cięta albo płacona od niedawna."
    first = min(totals)
    return criterion(id="dividend_streak", block="dividend", name=name, outcome=outcome,
                     value=float(n), display=f"{n} l. (dane od {first})", threshold=threshold,
                     source=STREAK_SOURCE, meaning=meaning)


def dividend_block(rows: list[dict], payments: list[tuple[str, float]], today: date) -> list[dict]:
    totals = annual_totals(payments, today)
    pays = ttm(payments, today) > 0
    return [payout_from_fcf(rows, pays), dividend_streak(totals if pays else {})]
