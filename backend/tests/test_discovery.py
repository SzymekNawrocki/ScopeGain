"""Testy normalizacji odkrywania (market.py, Etap B).

Znowu CZYSTE funkcje na ZAMROZONYCH ksztaltach z prawdziwych odpowiedzi Yahoo
(2026-07-17), bez sieci. Kluczowy test uczciwosci: kolumna `rating` ("Strong
Buy") NIE moze wyciec z modulu - to jezyk porady zakazany przez ADR-0001.
"""

import pandas as pd

from market import (
    _normalize_holdings,
    _normalize_industries,
    _normalize_top_companies,
    browsable_sectors,
)


def _df(rows: list[dict], index_name: str) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df = df.set_index(df.columns[0])
    df.index.name = index_name
    return df


# --- browsable_sectors (bez sieci) -----------------------------------------

def test_11_sektorow_ze_slugami():
    sekt = browsable_sectors()
    assert len(sekt) == 11
    klucze = {s["key"] for s in sekt}
    assert "energy" in klucze
    assert "basic-materials" in klucze     # slug: lowercase + myslnik
    # klucz to slug (do yf.Sector), name to nazwa czytelna
    energy = next(s for s in sekt if s["key"] == "energy")
    assert energy["name"] == "Energy"


# --- _normalize_industries (yf.Sector(...).industries) ----------------------

def test_industries_klucz_z_indeksu():
    # index = KLUCZ branzy (to on idzie do yf.Industry), kolumna name = nazwa.
    df = _df(
        [
            {"key": "uranium", "name": "Uranium", "symbol": "x", "market weight": 0.01},
            {"key": "oil-gas-integrated", "name": "Oil & Gas Integrated", "symbol": "y", "market weight": 0.4},
        ],
        index_name="key",
    )
    out = _normalize_industries(df)
    assert {"key": "uranium", "name": "Uranium"} in out
    assert out[1]["key"] == "oil-gas-integrated"


def test_industries_puste():
    assert _normalize_industries(pd.DataFrame()) == []


# --- _normalize_top_companies (yf.Industry(...).top_companies) --------------

def test_top_companies_wywala_rating():
    """UEC, LEU, NUCL z branzy uranium - kolumna `rating` (Strong Buy/Buy)
    NIE moze przejsc dalej (ADR-0001)."""
    df = _df(
        [
            {"symbol": "UEC", "name": "Uranium Energy Corp.", "rating": "Strong Buy", "market weight": 0.58},
            {"symbol": "LEU", "name": "Centrus Energy Corp.", "rating": "Buy", "market weight": 0.39},
        ],
        index_name="symbol",
    )
    out = _normalize_top_companies(df)
    assert out == [
        {"ticker": "UEC", "name": "Uranium Energy Corp."},
        {"ticker": "LEU", "name": "Centrus Energy Corp."},
    ]
    # zadne pole nie moze niesc oceny/porady
    for c in out:
        assert set(c.keys()) == {"ticker", "name"}


def test_top_companies_puste():
    assert _normalize_top_companies(None) == []


# --- _normalize_holdings (ETF funds_data.top_holdings) ----------------------

def test_holdings_ticker_i_nazwa():
    df = _df(
        [
            {"Symbol": "ARQQ", "Name": "Arqit Quantum Inc", "Holding Percent": 0.024},
            {"Symbol": "AMAT", "Name": "Applied Materials Inc", "Holding Percent": 0.015},
        ],
        index_name="Symbol",
    )
    out = _normalize_holdings(df)
    assert out == [
        {"ticker": "ARQQ", "name": "Arqit Quantum Inc"},
        {"ticker": "AMAT", "name": "Applied Materials Inc"},
    ]
