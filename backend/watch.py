"""Pure logic for the watchlist: snapshot an analysis and explain what changed."""

GRADE_ICON = {"good": "🟢", "mixed": "🟡", "bad": "🔴"}
OUTCOME_ICON = {"pass": "✅", "warn": "🟡", "fail": "❌", "na": "⚪"}


def snapshot(analysis: dict) -> dict:
    out = {}
    for block in analysis["blocks"].values():
        for c in block["criteria"]:
            out[c["id"]] = {"name": c["name"], "outcome": c["outcome"], "display": c["display"]}
    return out


def diff(old_grade: str | None, old: dict | None, new_grade: str, new: dict,
         old_fy: str | None = None, new_fy: str | None = None) -> list[str] | None:
    """Reasons the verdict changed, or None when the grade is the same.

    The first check of a ticker sets the baseline and is not a change.
    """
    if old_grade is None or old is None or old_grade == new_grade:
        return None
    reasons = []
    if old_fy and new_fy and old_fy != new_fy:
        reasons.append(f"Nowy raport roczny: {old_fy} → {new_fy}.")
    for cid, now in new.items():
        before = old.get(cid)
        if before is None or before["outcome"] == now["outcome"]:
            continue
        reasons.append(
            f"{now['name']}: {OUTCOME_ICON[before['outcome']]} → {OUTCOME_ICON[now['outcome']]} "
            f"({before['display']} → {now['display']})"
        )
    if not reasons:
        reasons.append("Zmiana wyniku bez zmiany pojedynczego kryterium (przesunięcie w bloku).")
    return reasons


def headline(old_grade: str, new_grade: str) -> str:
    return f"{GRADE_ICON.get(old_grade, '⚪')} → {GRADE_ICON[new_grade]}"
