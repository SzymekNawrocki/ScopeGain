"""Statistics criteria: where the company stands among its industry and its own past.

Both are percentiles, so no one's opinion sets the bar. The cut-offs (top/bottom
third) are a convention and are disclosed as such.
"""

from datetime import date

from criteria import criterion

FRAMES_SOURCE = (
    "SEC XBRL frames API (one concept, all filers, one calendar year); peers = companies "
    "with the same SIC code in EDGAR. Tercile cut-offs are a convention."
)
HISTORY_SOURCE = (
    "Company's own P/E at each fiscal-year end (SEC EPS, split-adjusted; Yahoo closing "
    "prices). Tercile cut-offs are a convention."
)
MIN_PEERS = 10
MIN_HISTORY = 5


def percentile(value: float, others: list[float]) -> float:
    """Share of others below value, ties counted as half (0-100)."""
    if not others:
        raise ValueError("no comparison values")
    below = sum(1 for o in others if o < value)
    equal = sum(1 for o in others if o == value)
    return 100.0 * (below + 0.5 * equal) / len(others)


def frame_period(fiscal_year_end: str) -> int:
    """Calendar year SEC frames assign to a fiscal year (the year it mostly overlaps)."""
    end = date.fromisoformat(fiscal_year_end)
    return end.year if end.month >= 7 else end.year - 1


def _fmt_pct(p: float) -> str:
    return f"{p:.0f}. percentyl"


def industry_percentile(
    *, id: str, name: str, company_value: float | None, peer_values: list[float],
    industry: str | None, higher_is_better: bool = True, unit: str = "%",
) -> dict:
    base = dict(id=id, block="health", name=name, source=FRAMES_SOURCE,
                threshold="górna tercja branży ✅ · środek 🟡 · dolna tercja ❌")
    if company_value is None:
        return criterion(**base, outcome="na", value=None, display="brak danych",
                         missing=[id], meaning="Brak wartości tej spółki w danych SEC.")
    if len(peer_values) < MIN_PEERS:
        return criterion(**base, outcome="na", value=None, display="za mało spółek w branży",
                         missing=[f"co najmniej {MIN_PEERS} spółek z tym samym kodem SIC"],
                         meaning="Branża ma za mało raportujących spółek, żeby liczyć percentyl.")
    p = percentile(company_value, peer_values)
    rank = p if higher_is_better else 100 - p
    shown = f"{company_value * 100:.1f}{unit}" if unit == "%" else f"{company_value:.2f}"
    who = f"spółek z branży {industry}" if industry else "spółek z tej samej branży"
    if rank >= 200 / 3:
        outcome, meaning = "pass", f"Lepiej niż {rank:.0f}% {who}."
    elif rank >= 100 / 3:
        outcome, meaning = "warn", f"Środek stawki: lepiej niż {rank:.0f}% {who}."
    else:
        outcome, meaning = "fail", f"Słabo na tle branży: lepiej tylko niż {rank:.0f}% {who}."
    return criterion(**base, outcome=outcome, value=round(rank, 1),
                     display=f"{shown} ({_fmt_pct(rank)}, n={len(peer_values)})",
                     meaning=meaning, details={"peers": len(peer_values)})


def split_factor_after(filed: str, splits: list[tuple[str, float]]) -> float:
    """Product of split ratios that happened after a filing date."""
    f = 1.0
    for when, ratio in splits:
        if when > filed and ratio > 0:
            f *= ratio
    return f


def pe_history(
    eps_points: list[tuple[str, float, str]],
    prices_at: dict[str, float],
    current_price: float | None,
    splits: list[tuple[str, float]],
) -> dict:
    """eps_points: (fiscal_year_end, eps, filed); prices_at: {fiscal_year_end: close}."""
    base = dict(id="pe_vs_history", block="valuation", name="C/Z na tle własnej historii",
                source=HISTORY_SOURCE,
                threshold="dolna tercja historii ✅ · środek 🟡 · górna tercja ❌")
    adjusted = [(end, eps / split_factor_after(filed, splits)) for end, eps, filed in eps_points]
    history = [prices_at[end] / eps for end, eps in adjusted[:-1]
               if eps > 0 and end in prices_at]
    latest_eps = adjusted[-1][1] if adjusted else None
    if current_price is None or latest_eps is None:
        return criterion(**base, outcome="na", value=None, display="brak danych",
                         missing=["cena" if current_price is None else "EPS"],
                         meaning="Brak ceny albo zysku na akcję.")
    if latest_eps <= 0:
        return criterion(**base, outcome="na", value=None, display="strata",
                         meaning="Ostatni rok ze stratą: C/Z nie ma sensu.")
    if len(history) < MIN_HISTORY:
        return criterion(**base, outcome="na", value=None, display="za krótka historia",
                         missing=[f"co najmniej {MIN_HISTORY} lat zysku na akcję"],
                         meaning="Za mało lat z zyskiem, żeby porównać z historią.")
    pe_now = current_price / latest_eps
    p = percentile(pe_now, history)
    median = sorted(history)[len(history) // 2]
    if p <= 100 / 3:
        outcome, meaning = "pass", "Taniej niż zwykle: obecne C/Z w dolnej tercji własnej historii."
    elif p < 200 / 3:
        outcome, meaning = "warn", "Wycena typowa dla tej spółki."
    else:
        outcome, meaning = "fail", "Drożej niż zwykle: obecne C/Z w górnej tercji własnej historii."
    return criterion(**base, outcome=outcome, value=round(pe_now, 1),
                     display=f"{pe_now:.1f} (mediana {median:.1f}, {len(history)} lat)".replace(".", ","),
                     meaning=meaning, details={"history": history, "percentile": p})
