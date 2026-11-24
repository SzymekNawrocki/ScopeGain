"""The fixed rule that turns criteria into a verdict (ADR-0005).

Per block: pass = +1, warn = 0, fail = -1 (criteria without data are skipped).
  🟢 good  - no fail and a positive sum
  🔴 bad   - negative sum
  🟡 mixed - anything else

Overall:
  🔴 if a knock-out criterion fired (Beneish), the Trust block is 🔴,
     or two or more blocks are 🔴;
  🟡 if fewer than half of the applicable criteria had data;
  🟢 if Trust is 🟢, no block is 🔴 and at least two blocks are 🟢;
  🟡 otherwise.
"""

BLOCKS = ["trust", "dividend", "valuation", "health"]
BLOCK_NAMES = {"trust": "Zaufanie", "dividend": "Dywidenda", "valuation": "Wycena",
               "health": "Zdrowie"}
POINTS = {"pass": 1, "warn": 0, "fail": -1}

GRADES = {
    "good": "Warto rozważyć",
    "mixed": "Na granicy",
    "bad": "Nie warto",
}


def _applicable(c: dict) -> bool:
    return c["display"] != "nie dotyczy"


def block_status(criteria: list[dict]) -> dict:
    known = [c for c in criteria if c["outcome"] != "na"]
    counts = {k: sum(1 for c in criteria if c["outcome"] == k) for k in ("pass", "warn", "fail", "na")}
    if not known:
        status = "na"
    else:
        total = sum(POINTS[c["outcome"]] for c in known)
        has_fail = any(c["outcome"] == "fail" for c in known)
        status = "good" if not has_fail and total > 0 else "bad" if total < 0 else "mixed"
    return {"status": status, "counts": counts}


def build_verdict(criteria: list[dict]) -> dict:
    blocks = {}
    for b in BLOCKS:
        items = [c for c in criteria if c["block"] == b]
        if items:
            blocks[b] = {"name": BLOCK_NAMES[b], **block_status(items), "criteria": items}

    applicable = [c for c in criteria if _applicable(c)]
    known = [c for c in applicable if c["outcome"] != "na"]
    coverage = len(known) / len(applicable) if applicable else 0.0
    knockouts = [c for c in criteria if c["knockout"]]
    statuses = {b: v["status"] for b, v in blocks.items()}
    bad_blocks = [b for b, s in statuses.items() if s == "bad"]
    good_blocks = [b for b, s in statuses.items() if s == "good"]

    if knockouts:
        grade, reason = "bad", f"Wykluczona: {knockouts[0]['name']} {knockouts[0]['display']}."
    elif statuses.get("trust") == "bad":
        grade, reason = "bad", "Blok Zaufanie wypada źle."
    elif len(bad_blocks) >= 2:
        grade, reason = "bad", "Dwa lub więcej bloków wypada źle: " + \
            ", ".join(BLOCK_NAMES[b] for b in bad_blocks) + "."
    elif coverage < 0.5:
        grade, reason = "mixed", f"Za mało danych: sprawdzono {len(known)} z {len(applicable)} kryteriów."
    elif statuses.get("trust") == "good" and not bad_blocks and len(good_blocks) >= 2:
        grade, reason = "good", "Zaufanie dobre i żaden blok nie wypada źle."
    else:
        grade, reason = "mixed", "Wyniki mieszane: są mocne strony i wyraźne słabości."

    pros = [_argument(c) for c in criteria if c["outcome"] == "pass"]
    cons = [_argument(c) for c in criteria if c["outcome"] in ("fail", "warn")]
    gaps = [{"criterion": c["name"], "missing": c["missing"]}
            for c in applicable if c["outcome"] == "na"]
    return {
        "grade": grade,
        "label": GRADES[grade],
        "reason": reason,
        "coverage": {"checked": len(known), "applicable": len(applicable)},
        "blocks": blocks,
        "pros": pros,
        "cons": cons,
        "data_gaps": gaps,
    }


def _argument(c: dict) -> dict:
    return {"id": c["id"], "severity": c["outcome"], "title": f"{c['name']}: {c['display']}",
            "detail": c["meaning"], "threshold": c["threshold"]}
