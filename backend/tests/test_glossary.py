"""Every criterion the API can return must have a glossary entry in the frontend."""

import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
GLOSSARY = BACKEND.parent / "frontend" / "app" / "lib" / "glossary.ts"
MODULES = ["trust.py", "health.py", "valuation.py", "stats.py", "stats_data.py", "dividends.py"]


def criterion_ids() -> set[str]:
    ids = set()
    for m in MODULES:
        text = (BACKEND / m).read_text(encoding="utf-8")
        ids |= set(re.findall(r'id="([a-z_]+)"', text))
        ids |= set(re.findall(r'_(?:na_financial|not_payer)\("([a-z_]+)"', text))
    return ids


def test_every_criterion_has_a_glossary_entry():
    glossary = GLOSSARY.read_text(encoding="utf-8")
    keys = set(re.findall(r"^  ([a-z_]+): \{", glossary, flags=re.M))
    ids = criterion_ids()
    assert len(ids) >= 13
    assert ids - keys == set()
