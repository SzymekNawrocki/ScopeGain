"""Testy silnika werdyktu z analysis.py.

To jest logika, ktora MOWI userowi "Twoj portfel jest slaby/mocny" - jesli
progi albo sumowanie ocen sa zle, apka wprost klamie. Testujemy kazda granice
osobno (good/warn/bad) i sama agregacje do oceny koncowej.
"""

import pytest

from analysis import (
    BAD,
    GOOD,
    WARN,
    build_behavior_verdict,
    build_stock_verdict,
    build_verdict,
)


def all_good_kwargs() -> dict:
    return dict(
        benchmark_label="SPY",
        alpha_pct=10.0,
        sharpe=1.5,
        port_vol=20.0,
        bench_vol=20.0,
        avg_corr=0.1,
        n_tickers=3,
        top_weight_pct=30.0,
        top_ticker="AAPL",
    )


def severities(verdict: dict) -> list[str]:
    return [f["severity"] for f in verdict["findings"]]


# --- alpha (bijesz rynek?) --------------------------------------------------

def test_alpha_bad_below_minus_five():
    v = build_verdict(**{**all_good_kwargs(), "alpha_pct": -5.0})
    assert severities(v)[0] == BAD


def test_alpha_warn_between_minus_five_and_five():
    v = build_verdict(**{**all_good_kwargs(), "alpha_pct": 0.0})
    assert severities(v)[0] == WARN


def test_alpha_good_at_five_or_above():
    v = build_verdict(**{**all_good_kwargs(), "alpha_pct": 5.0})
    assert severities(v)[0] == GOOD


# --- sharpe (zysk za ryzyko) -------------------------------------------------

def test_sharpe_bad_below_half():
    v = build_verdict(**{**all_good_kwargs(), "sharpe": 0.49})
    assert severities(v)[1] == BAD


def test_sharpe_warn_between_half_and_one():
    v = build_verdict(**{**all_good_kwargs(), "sharpe": 0.5})
    assert severities(v)[1] == WARN


def test_sharpe_good_at_one_or_above():
    v = build_verdict(**{**all_good_kwargs(), "sharpe": 1.0})
    assert severities(v)[1] == GOOD


# --- zmiennosc vs rynek -------------------------------------------------

def test_volatility_finding_skipped_when_benchmark_vol_is_zero():
    kwargs = {**all_good_kwargs(), "bench_vol": 0.0}
    v = build_verdict(**kwargs)
    titles = [f["title"] for f in v["findings"]]
    assert not any("rozchwiany" in t or "kontrola" in t for t in titles)


def test_volatility_warn_when_meaningfully_more_volatile_than_market():
    kwargs = {**all_good_kwargs(), "port_vol": 30.0, "bench_vol": 20.0}  # 1.5x
    v = build_verdict(**kwargs)
    vol_finding = next(f for f in v["findings"] if "rozchwiany" in f["title"] or "kontrola" in f["title"])
    assert vol_finding["severity"] == WARN


def test_volatility_good_when_close_to_market():
    kwargs = {**all_good_kwargs(), "port_vol": 21.0, "bench_vol": 20.0}  # 1.05x
    v = build_verdict(**kwargs)
    vol_finding = next(f for f in v["findings"] if "rozchwiany" in f["title"] or "kontrola" in f["title"])
    assert vol_finding["severity"] == GOOD


# --- dywersyfikacja -------------------------------------------------------

def test_diversification_bad_with_single_ticker():
    v = build_verdict(**{**all_good_kwargs(), "n_tickers": 1, "avg_corr": None})
    div_finding = next(f for f in v["findings"] if "dywersyfikacj" in f["title"] or "razem" in f["title"])
    assert div_finding["severity"] == BAD


def test_diversification_skipped_when_avg_corr_unknown():
    kwargs = {**all_good_kwargs(), "avg_corr": None}
    v = build_verdict(**kwargs)
    assert not any("dywersyfikacj" in f["title"] or "razem" in f["title"] for f in v["findings"])


def test_diversification_bad_when_stocks_move_together():
    v = build_verdict(**{**all_good_kwargs(), "avg_corr": 0.71})
    div_finding = next(f for f in v["findings"] if "razem" in f["title"])
    assert div_finding["severity"] == BAD


def test_diversification_warn_moderate_correlation():
    v = build_verdict(**{**all_good_kwargs(), "avg_corr": 0.4})
    div_finding = next(f for f in v["findings"] if "Umiarkowana" in f["title"])
    assert div_finding["severity"] == WARN


def test_diversification_good_low_correlation():
    v = build_verdict(**{**all_good_kwargs(), "avg_corr": 0.1})
    div_finding = next(f for f in v["findings"] if "Dobra dywersyfikacja" in f["title"])
    assert div_finding["severity"] == GOOD


# --- koncentracja pozycji -------------------------------------------------

def test_concentration_skipped_with_single_ticker():
    v = build_verdict(**{**all_good_kwargs(), "n_tickers": 1, "avg_corr": None})
    assert not any("koncentracj" in f["title"] or "rozsadnie" in f["title"] or "skupiony" in f["title"] for f in v["findings"])


def test_concentration_bad_above_sixty_percent():
    v = build_verdict(**{**all_good_kwargs(), "top_weight_pct": 61.0})
    conc = next(f for f in v["findings"] if "skupiony" in f["title"])
    assert conc["severity"] == BAD


def test_concentration_warn_between_forty_and_sixty():
    v = build_verdict(**{**all_good_kwargs(), "top_weight_pct": 40.0})
    conc = next(f for f in v["findings"] if "koncentracja" in f["title"])
    assert conc["severity"] == WARN


def test_concentration_good_below_forty_percent():
    v = build_verdict(**{**all_good_kwargs(), "top_weight_pct": 30.0})
    conc = next(f for f in v["findings"] if "rozsadnie" in f["title"])
    assert conc["severity"] == GOOD


# --- agregacja do oceny koncowej -------------------------------------------

def test_overall_grade_good_when_mostly_good_findings():
    v = build_verdict(**all_good_kwargs())
    assert v["grade"] == GOOD
    assert v["grade_label"] == "mocny"
    assert all(f["severity"] == GOOD for f in v["findings"])


def test_overall_grade_warn_when_points_sum_to_zero_or_one():
    # alpha good (+1), sharpe good (+1), n_tickers=1 -> dywersyfikacja bad (-1)
    # bench_vol=0 usuwa finding o zmiennosci, n_tickers=1 usuwa koncentracje
    # -> punkty = 1
    kwargs = {
        **all_good_kwargs(),
        "n_tickers": 1,
        "avg_corr": None,
        "bench_vol": 0.0,
    }
    v = build_verdict(**kwargs)
    assert v["grade"] == WARN
    assert v["grade_label"] == "przecietny"


def test_overall_grade_bad_when_points_are_negative():
    kwargs = {
        **all_good_kwargs(),
        "alpha_pct": -10.0,
        "sharpe": 0.2,
        "n_tickers": 1,
        "avg_corr": None,
        "bench_vol": 0.0,
    }
    v = build_verdict(**kwargs)
    assert v["grade"] == BAD
    assert v["grade_label"] == "slaby"


# --- werdykt zachowania (12b: behavior gap) --------------------------------

def _sell(ticker, sold, now, qty=10, date="2026-01-01") -> dict:
    return {"ticker": ticker, "quantity": qty, "sold_price": sold,
            "current_price": now, "executed_at": date}


def test_behavior_sold_a_winner_is_bad_and_counts_left_on_table():
    # sprzedales po 100, dzis 130 (+30%) -> za wczesnie; 10 szt -> 300 na stole.
    v = build_behavior_verdict([_sell("AAPL", 100.0, 130.0, qty=10)])
    assert v["findings"][0]["severity"] == BAD
    assert v["total_left_on_table"] == pytest.approx(300.0)
    assert v["grade"] == BAD


def test_behavior_good_exit_when_price_fell_after_sell():
    # sprzedales po 100, dzis 80 (-20%) -> dobre wyjscie, uniknieta strata.
    v = build_behavior_verdict([_sell("XYZ", 100.0, 80.0, qty=5)])
    assert v["findings"][0]["severity"] == GOOD
    assert v["total_left_on_table"] == pytest.approx(-100.0)  # trzymanie byloby gorsze
    assert v["grade"] == GOOD


def test_behavior_small_move_is_neutral_warn():
    # +5% to szum ponizej progu 10% -> neutralny timing.
    v = build_behavior_verdict([_sell("MSFT", 100.0, 105.0)])
    assert v["findings"][0]["severity"] == WARN
    assert v["grade"] == WARN


def test_behavior_empty_log_returns_no_data_grade():
    v = build_behavior_verdict([])
    assert v["grade"] == WARN
    assert v["grade_label"] == "brak danych"
    assert v["total_left_on_table"] == 0.0
    assert len(v["findings"]) == 1


def test_behavior_skips_rows_without_current_price():
    # spolka bez dzisiejszej ceny (np. wycofana) nie moze byc oceniona -> pomijana.
    rows = [
        {"ticker": "DEAD", "quantity": 3, "sold_price": 50.0,
         "current_price": None, "executed_at": "2025-06-01"},
    ]
    v = build_behavior_verdict(rows)
    assert v["grade_label"] == "brak danych"


def test_behavior_always_includes_honest_caveat():
    v = build_behavior_verdict([_sell("AAPL", 100.0, 130.0)])
    assert "gotowka" in v["caveat"]


# --- werdykt RYZYKA pojedynczej spolki --------------------------------------
# Uwaga na ODWROCONA semantyke: tu GOOD = niskie ryzyko, BAD = wysokie.

def all_low_risk_kwargs() -> dict:
    return dict(
        ticker="AAPL",
        bench_label="SPY",
        volatility_pct=20.0,
        bench_vol=20.0,      # ratio 1.0 -> GOOD
        max_drawdown_pct=-10.0,
        beta=1.0,
        trailing_pe=20.0,
        profit_margins=0.25,
    )


# --- zmiennosc vs rynek ---

def test_stock_vol_good_at_or_below_1_2x():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "volatility_pct": 24.0})
    assert severities(v)[0] == GOOD


def test_stock_vol_warn_above_1_2x():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "volatility_pct": 30.0})
    assert severities(v)[0] == WARN


def test_stock_vol_bad_above_1_8x():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "volatility_pct": 40.0})
    assert severities(v)[0] == BAD


def test_stock_vol_skipped_when_no_benchmark():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "bench_vol": 0.0})
    assert "zmiennosc rynku" in v["data_gaps"]


# --- max drawdown ---

def test_stock_drawdown_good_above_minus_20():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "max_drawdown_pct": -19.0})
    assert severities(v)[1] == GOOD


def test_stock_drawdown_warn_between_20_and_40():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "max_drawdown_pct": -40.0})
    assert severities(v)[1] == WARN


def test_stock_drawdown_bad_below_minus_40():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "max_drawdown_pct": -72.0})
    assert severities(v)[1] == BAD


# --- beta ---

def test_stock_beta_good_at_or_below_1_1():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "beta": 1.1})
    assert severities(v)[2] == GOOD


def test_stock_low_beta_is_not_described_as_moving_like_market():
    """Beta 0.35 (realnie Coca-Cola) znaczy 'rusza sie DUZO slabiej', a nie
    'mniej wiecej jak rynek' - tekst musi to rozroznic."""
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "beta": 0.35})
    assert severities(v)[2] == GOOD
    assert v["findings"][2]["title"] == "Slabiej reaguje na rynek"


def test_stock_beta_does_not_claim_calm():
    """Beta to ruch RAZEM Z RYNKIEM, nie spokoj: spolka moze bujac 4x mocniej
    niz rynek i miec bete 1.0 (buja na wlasny rachunek - realnie Cameco).
    Nazwanie tego 'spokojna' przeczyloby regule zmiennosci na tym samym
    ekranie."""
    v = build_stock_verdict(**{
        **all_low_risk_kwargs(), "volatility_pct": 56.0, "bench_vol": 13.0,
        "beta": 1.0,
    })
    assert severities(v)[0] == BAD                    # buja duzo mocniej
    assert "Spokojna" not in v["findings"][2]["title"]  # ...wiec nie "spokojna"


def test_stock_beta_warn_above_1_1():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "beta": 1.4})
    assert severities(v)[2] == WARN


def test_stock_beta_bad_above_1_5():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "beta": 2.0})
    assert severities(v)[2] == BAD


def test_stock_beta_none_goes_to_data_gaps():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "beta": None})
    assert "beta" in v["data_gaps"]
    assert len(v["findings"]) == 4  # regula pominieta, reszta liczy sie dalej


# --- marza zysku ---

def test_stock_margins_good_above_10_pct():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "profit_margins": 0.11})
    assert severities(v)[3] == GOOD


def test_stock_margins_warn_when_thin():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "profit_margins": 0.02})
    assert severities(v)[3] == WARN


def test_stock_margins_bad_when_negative():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "profit_margins": -0.3})
    assert severities(v)[3] == BAD


# --- P/E (ryzyko wyceny) ---

def test_stock_pe_good_at_or_below_25():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "trailing_pe": 25.0})
    assert severities(v)[4] == GOOD


def test_stock_pe_warn_above_25():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "trailing_pe": 40.0})
    assert severities(v)[4] == WARN


def test_stock_pe_bad_above_50():
    # Cameco realnie mial P/E 83 - w cenie siedza duze oczekiwania.
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "trailing_pe": 83.2})
    assert severities(v)[4] == BAD


def test_stock_pe_none_goes_to_data_gaps():
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "trailing_pe": None})
    assert "P/E" in v["data_gaps"]


def test_stock_pe_zero_or_negative_is_missing_not_bad():
    """yfinance NIE odroznia 'spolka nie ma zysku' od 'Yahoo nie podalo'.
    Zgadywanie ktorejkolwiek wersji byloby klamstwem - mowimy 'nie wiem'."""
    v = build_stock_verdict(**{**all_low_risk_kwargs(), "trailing_pe": -12.0})
    assert "P/E" in v["data_gaps"]
    assert len(v["findings"]) == 4


# --- ocena laczna ---

def test_stock_grade_low_risk_when_all_calm():
    v = build_stock_verdict(**all_low_risk_kwargs())
    assert v["grade"] == GOOD
    assert v["grade_label"] == "niskie ryzyko"


def test_stock_grade_high_risk_when_everything_screams():
    v = build_stock_verdict(**{
        **all_low_risk_kwargs(),
        "volatility_pct": 60.0, "max_drawdown_pct": -72.0,
        "beta": 2.1, "profit_margins": -0.4, "trailing_pe": 90.0,
    })
    assert v["grade"] == BAD
    assert v["grade_label"] == "wysokie ryzyko"


# --- straznicy uczciwosci (ADR-0001) ---

def test_stock_verdict_label_always_speaks_about_risk():
    """STRAZNIK ADR-0001. Apka nie wydaje zlecen kup/sprzedaj. Werdykt o
    POJEDYNCZEJ spolce etykietowany jakoscia ("mocny") czyta sie jak
    rekomendacja zakupu - dlatego etykieta MUSI mowic o ryzyku. Ten test
    ma paść, gdyby ktos kiedys skopiowal tu slownik z werdyktu portfela."""
    warianty = [
        all_low_risk_kwargs(),
        {**all_low_risk_kwargs(), "beta": 1.4},
        {**all_low_risk_kwargs(), "volatility_pct": 60.0, "max_drawdown_pct": -72.0,
         "beta": 2.1, "profit_margins": -0.4, "trailing_pe": 90.0},
    ]
    for kw in warianty:
        assert "ryzyko" in build_stock_verdict(**kw)["grade_label"]


def test_stock_verdict_always_includes_caveat():
    v = build_stock_verdict(**all_low_risk_kwargs())
    assert "kup/sprzedaj" in v["caveat"]


def test_stock_verdict_reports_data_gaps_honestly():
    """Werdykt z 2 regul nie moze wygladac tak samo pewnie jak z 5."""
    v = build_stock_verdict(**{
        **all_low_risk_kwargs(),
        "beta": None, "trailing_pe": None, "profit_margins": None,
    })
    assert set(v["data_gaps"]) == {"beta", "marza zysku", "P/E"}
    assert len(v["findings"]) == 2
