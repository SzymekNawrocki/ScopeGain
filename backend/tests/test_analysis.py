"""Testy silnika werdyktu z analysis.py.

To jest logika, ktora MOWI userowi "Twoj portfel jest slaby/mocny" - jesli
progi albo sumowanie ocen sa zle, apka wprost klamie. Testujemy kazda granice
osobno (good/warn/bad) i sama agregacje do oceny koncowej.
"""

from analysis import BAD, GOOD, WARN, build_verdict


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
