"""Testy normalizacji danych z market.py.

Testujemy CZYSTE funkcje (_normalize_quote/_normalize_info) na ZAMROZONYCH,
prawdziwych odpowiedziach Yahoo - bez sieci i bez mockow. To celowe:
mockujac yf.Search testowalibysmy zachowanie wlasnego mocka. Zamrozony
prawdziwy dict lapie blad, ktory realnie wystapi: dostawca zmienil nazwe pola.

Dane ponizej pochodza z odpowiedzi Yahoo z 2026-07-17 (skrocone).
"""

from market import _normalize_info, _normalize_quote, _profil_wart_zapamietania

# --- Zamrozone odpowiedzi ---------------------------------------------------

# yf.Search("cameco").quotes[0] - spolka na NYSE.
QUOTE_CCJ = {
    "exchange": "NYQ",
    "shortname": "Cameco Corporation",
    "quoteType": "EQUITY",
    "symbol": "CCJ",
    "index": "quotes",
    "score": 2547300.0,
    "typeDisp": "Equity",
    "longname": "Cameco Corporation",
    "exchDisp": "NYSE",
    "sector": "Energy",
    "sectorDisp": "Energy",
    "industry": "Uranium",
    "industryDisp": "Uranium",
    "isYahooFinance": True,
}

# Ten sam Cameco, ale z Toronto - CROSS-LISTING. Inny papier, inna waluta.
QUOTE_CCO_TO = {
    "exchange": "TOR",
    "shortname": "Cameco Corporation",
    "quoteType": "EQUITY",
    "symbol": "CCO.TO",
    "longname": "Cameco Corporation",
    "exchDisp": "Toronto",
    "sector": "Energy",
    "sectorDisp": "Energy",
    "industry": "Uranium",
    "industryDisp": "Uranium",
    "isYahooFinance": True,
}

QUOTE_ETF_URA = {
    "exchange": "PCX",
    "shortname": "Global X Uranium ETF",
    "quoteType": "ETF",
    "symbol": "URA",
    "longname": "Global X Uranium ETF",
    "exchDisp": "NYSEArca",
    "isYahooFinance": True,
}

# Kontrakt terminowy - NIE chcemy tego w podpowiedziach.
QUOTE_FUTURE = {
    "exchange": "NYM",
    "shortname": "Crude Oil",
    "quoteType": "FUTURE",
    "symbol": "CL=F",
    "exchDisp": "NY Mercantile",
    "isYahooFinance": True,
}

# yf.Ticker("CCJ").info - skrocone do pol, ktorych uzywamy.
INFO_CCJ = {
    "shortName": "Cameco Corporation",
    "longName": "Cameco Corporation",
    "sector": "Energy",
    "industry": "Uranium",
    "marketCap": 38048161792,
    "trailingPE": 83.200005,
    "beta": 1.0,
    "profitMargins": 0.18389,
    "currency": "USD",
    "longBusinessSummary": "Cameco Corporation provides uranium for the generation of electricity...",
    "regularMarketPrice": 71.02,
}


# --- _normalize_quote -------------------------------------------------------

def test_quote_spolki():
    r = _normalize_quote(QUOTE_CCJ)
    assert r == {
        "ticker": "CCJ",
        "name": "Cameco Corporation",
        "exchange": "NYSE",
        "quote_type": "EQUITY",
        "sector": "Energy",
        "industry": "Uranium",
    }


def test_quote_etf_przechodzi():
    r = _normalize_quote(QUOTE_ETF_URA)
    assert r is not None
    assert r["ticker"] == "URA"
    assert r["quote_type"] == "ETF"
    # ETF nie ma sektora - to OK, nie wywalamy sie.
    assert r["sector"] is None


def test_quote_kontrakt_terminowy_odpada():
    """W podpowiedziach chcemy spolki i ETF-y, nie ropę i waluty."""
    assert _normalize_quote(QUOTE_FUTURE) is None


def test_quote_bez_symbolu_odpada():
    assert _normalize_quote({"shortname": "Cos", "quoteType": "EQUITY"}) is None


def test_quote_cross_listing_to_osobne_papiery():
    """CCJ (NYSE) i CCO.TO (Toronto) to ta sama firma, ale rozne papiery -
    gielda jest jedynym, co je rozroznia. Nie wolno ich zlepic."""
    a = _normalize_quote(QUOTE_CCJ)
    b = _normalize_quote(QUOTE_CCO_TO)
    assert a["name"] == b["name"]          # ta sama firma
    assert a["ticker"] != b["ticker"]      # inny papier
    assert a["exchange"] != b["exchange"]  # to je rozroznia


def test_quote_longname_ma_pierwszenstwo():
    q = {**QUOTE_CCJ, "shortname": "Cameco", "longname": "Cameco Corporation"}
    assert _normalize_quote(q)["name"] == "Cameco Corporation"


# --- _normalize_info --------------------------------------------------------

def test_info_pelny_profil():
    r = _normalize_info("ccj", INFO_CCJ)
    assert r["ticker"] == "CCJ"            # normalizujemy wielkosc liter
    assert r["name"] == "Cameco Corporation"
    assert r["sector"] == "Energy"
    assert r["industry"] == "Uranium"
    assert r["market_cap"] == 38048161792
    assert r["trailing_pe"] == 83.200005
    assert r["beta"] == 1.0
    assert r["profit_margins"] == 0.18389


def test_info_pusty_to_brak_spolki():
    assert _normalize_info("ZZZZ", {}) is None


def test_info_brakujace_pola_nie_wywalaja():
    """Yahoo to darmowe zrodlo - kazde pole potrafi nie przyjsc. Profil ma
    wtedy dziury, ale MUSI sie zbudowac."""
    r = _normalize_info("XYZ", {"shortName": "Cos SA", "regularMarketPrice": 10.0})
    assert r is not None
    assert r["name"] == "Cos SA"
    assert r["trailing_pe"] is None
    assert r["beta"] is None
    assert r["sector"] is None


def test_info_bez_nazwy_ale_z_cena_przechodzi():
    """Sa papiery bez nazwy w .info, ale notowane - to nie 'brak spolki'."""
    r = _normalize_info("XYZ", {"regularMarketPrice": 10.0})
    assert r is not None
    assert r["name"] == "XYZ"


# --- czy profil warto zapamietac (obrona przed urwana odpowiedzia) ----------

def test_pelny_profil_spolki_wart_zapamietania():
    assert _profil_wart_zapamietania(_normalize_info("CCJ", INFO_CCJ)) is True


def test_etf_bez_sektora_ale_z_opisem_wart_zapamietania():
    """ETF-y (URA, SPY) LEGALNIE nie maja sektora, branzy ani kapitalizacji -
    ale maja opis. Nie wolno ich mylic z urwana odpowiedzia."""
    etf = _normalize_info("URA", {
        "shortName": "Global X Uranium ETF",
        "regularMarketPrice": 41.2,
        "longBusinessSummary": "The fund invests in uranium miners...",
        "currency": "USD",
    })
    assert etf["sector"] is None
    assert etf["market_cap"] is None
    assert _profil_wart_zapamietania(etf) is True


def test_urwana_odpowiedz_nie_wart_zapamietania():
    """Realny przypadek z 2026-07-17: Yahoo oddalo ceny i wskazniki, ale bez
    modulu profilowego - branza, marza i opis puste. Zapisane na 12 h,
    zostaloby na ekranie przez pol dnia."""
    urwane = _normalize_info("CCJ", {
        "shortName": "Cameco Corporation",
        "marketCap": 38048161792,
        "trailingPE": 83.2,
        "regularMarketPrice": 71.0,
        # brak: sector, industry, profitMargins, longBusinessSummary
    })
    assert urwane["market_cap"] == 38048161792   # dane sa...
    assert urwane["industry"] is None            # ...ale niepelne
    assert _profil_wart_zapamietania(urwane) is False


def test_brak_spolki_wart_zapamietania():
    """None = 'nie ma takiej spolki' - to trwaly fakt, nie awaria."""
    assert _profil_wart_zapamietania(None) is True
