"""The shape every check returns, plus small numeric helpers.

A criterion never guesses: when an input is missing, the outcome is "na" and
the missing inputs are listed, so the card can show them as data gaps.
"""

from typing import Literal

Outcome = Literal["pass", "warn", "fail", "na"]
Block = Literal["trust", "dividend", "valuation", "health"]

FINANCIAL_SIC = range(6000, 6800)  # banks, insurers, REITs, brokers
MANUFACTURING_SIC = range(2000, 4000)


def criterion(
    *,
    id: str,
    block: Block,
    name: str,
    outcome: Outcome,
    value: float | None,
    display: str,
    threshold: str,
    source: str,
    meaning: str,
    missing: list[str] | None = None,
    knockout: bool = False,
    details: dict | None = None,
) -> dict:
    return {
        "id": id,
        "block": block,
        "name": name,
        "outcome": outcome,
        "value": value,
        "display": display,
        "threshold": threshold,
        "source": source,
        "meaning": meaning,
        "missing": missing or [],
        "knockout": knockout,
        "details": details or {},
    }


def div(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def sic_in(sic: str | None, codes: range) -> bool:
    try:
        return int(sic) in codes  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


def need(row: dict | None, fields: list[str], label: str = "") -> list[str]:
    """Names of fields missing from a row (prefixed with the year label)."""
    if row is None:
        return [f"{label}{f}" for f in fields]
    return [f"{label}{f}" for f in fields if row.get(f) is None]
