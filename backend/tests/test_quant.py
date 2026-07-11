"""Testy czystych obliczen finansowych z quant.py.

Kazda funkcja tam to formula - sprawdzamy ja na recznie policzonych danych,
zeby blad w formule (np. zla kolejnosc w Sharpe) nie przeszedl cicho.
"""

import numpy as np
import pandas as pd
import pytest

from quant import (
    annualized_volatility_pct,
    beta,
    daily_returns,
    max_drawdown_pct,
    net_pnl,
    returns_frame,
    sharpe_ratio,
    total_return_pct,
)


# --- daily_returns / returns_frame ---------------------------------------

def test_daily_returns_basic():
    close = pd.Series([100.0, 110.0, 99.0])
    out = daily_returns(close)
    assert len(out) == 2
    assert out.iloc[0] == pytest.approx(0.10)
    assert out.iloc[1] == pytest.approx(-0.10)


def test_daily_returns_drops_first_day_without_yesterday():
    close = pd.Series([50.0, 55.0])
    out = daily_returns(close)
    assert len(out) == 1


def test_returns_frame_multiple_columns():
    closes = pd.DataFrame({"AAPL": [100.0, 110.0, 121.0], "MSFT": [50.0, 55.0, 49.5]})
    out = returns_frame(closes)
    assert list(out.columns) == ["AAPL", "MSFT"]
    assert len(out) == 2
    assert out["AAPL"].iloc[0] == pytest.approx(0.10)
    assert out["MSFT"].iloc[1] == pytest.approx(-0.10)


# --- total_return_pct ------------------------------------------------------

def test_total_return_pct_gain():
    assert total_return_pct(pd.Series([100.0, 150.0])) == pytest.approx(50.0)


def test_total_return_pct_loss():
    assert total_return_pct(pd.Series([200.0, 100.0])) == pytest.approx(-50.0)


def test_total_return_pct_flat_is_zero():
    assert total_return_pct(pd.Series([100.0, 100.0, 100.0])) == pytest.approx(0.0)


# --- annualized_volatility_pct ----------------------------------------------

def test_annualized_volatility_matches_manual_formula():
    returns = pd.Series([0.01, -0.02, 0.015, 0.0, -0.005])
    expected = returns.std() * np.sqrt(252) * 100
    assert annualized_volatility_pct(returns) == pytest.approx(expected)


def test_annualized_volatility_zero_for_constant_returns():
    returns = pd.Series([0.01, 0.01, 0.01, 0.01])
    assert annualized_volatility_pct(returns) == pytest.approx(0.0)


# --- sharpe_ratio ------------------------------------------------------------

def test_sharpe_ratio_matches_manual_formula():
    returns = pd.Series([0.01, -0.02, 0.015, 0.0, -0.005])
    expected = (returns.mean() / returns.std()) * np.sqrt(252)
    assert sharpe_ratio(returns) == pytest.approx(expected)


def test_sharpe_ratio_zero_std_returns_zero_not_crash():
    returns = pd.Series([0.01, 0.01, 0.01])
    assert sharpe_ratio(returns) == 0.0


def test_sharpe_ratio_empty_series_returns_zero():
    assert sharpe_ratio(pd.Series(dtype=float)) == 0.0


def test_sharpe_ratio_higher_mean_return_gives_higher_sharpe():
    low = pd.Series([0.001, -0.001, 0.001, -0.001, 0.001])
    high = pd.Series([0.01, -0.001, 0.01, -0.001, 0.01])
    assert sharpe_ratio(high) > sharpe_ratio(low)


def test_sharpe_ratio_uses_risk_free_rate():
    returns = pd.Series([0.01, -0.02, 0.015, 0.0, -0.005])
    no_rf = sharpe_ratio(returns, risk_free_annual=0.0)
    with_rf = sharpe_ratio(returns, risk_free_annual=0.05)
    # wyzsza stopa wolna od ryzyka podnosi "poprzeczke" -> nizszy Sharpe
    assert with_rf < no_rf


# --- beta ----------------------------------------------------------------

def test_beta_of_market_with_itself_is_one():
    market = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
    assert beta(market, market) == pytest.approx(1.0)


def test_beta_double_market_moves_is_two():
    market = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
    assert beta(market * 2, market) == pytest.approx(2.0)


def test_beta_inverse_of_market_is_negative_one():
    market = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
    assert beta(-market, market) == pytest.approx(-1.0)


def test_beta_zero_market_variance_returns_zero_not_crash():
    market = pd.Series([0.0, 0.0, 0.0, 0.0])
    asset = pd.Series([0.01, -0.02, 0.03, -0.01])
    assert beta(asset, market) == 0.0


def test_beta_insufficient_overlap_returns_zero():
    market = pd.Series([0.01], index=[pd.Timestamp("2024-01-01")])
    asset = pd.Series([0.02], index=[pd.Timestamp("2024-01-01")])
    assert beta(asset, market) == 0.0


def test_beta_uses_only_dates_present_in_both_series():
    idx_common = pd.date_range("2024-01-01", periods=3)
    market = pd.Series([0.01, -0.02, 0.03], index=idx_common)
    asset = pd.Series([0.02, -0.01, 0.05], index=idx_common)
    expected = asset.cov(market) / market.var()

    # dzien, ktory istnieje TYLKO w market - nie powinien wplynac na wynik
    market_with_extra_day = pd.concat(
        [market, pd.Series([0.5], index=[pd.Timestamp("2024-02-01")])]
    )
    assert beta(asset, market_with_extra_day) == pytest.approx(expected)


# --- net_pnl (warstwa 12a: prowizja + podatek Belka) ------------------------

def test_net_pnl_gain_is_taxed_after_both_commissions():
    # koszt 1000, dzis warte 1200: prowizja 0,29% przy kupnie I przy
    # (hipotetycznej) sprzedazy dzis, Belka 19% dopiero od zysku PO prowizjach.
    out = net_pnl(cost_basis=1000.0, market_value=1200.0)
    assert out["commission_total"] == pytest.approx(6.38)
    assert out["tax_belka"] == pytest.approx(36.79, abs=0.01)
    assert out["net_pnl_abs"] == pytest.approx(156.83, abs=0.01)
    assert out["net_pnl_pct"] == pytest.approx(15.68, abs=0.01)


def test_net_pnl_loss_pays_no_belka_tax():
    # strata nie generuje podatku - tylko prowizje obu (hipotetycznych) transakcji.
    out = net_pnl(cost_basis=1000.0, market_value=900.0)
    assert out["tax_belka"] == 0.0
    assert out["net_pnl_abs"] == pytest.approx(-105.51, abs=0.01)
    assert out["net_pnl_abs"] < (900.0 - 1000.0)  # netto gorsze niz brutto (koszty)


def test_net_pnl_zero_cost_basis_returns_zero_pct_not_crash():
    out = net_pnl(cost_basis=0.0, market_value=0.0)
    assert out["net_pnl_pct"] == 0.0
    assert out["net_pnl_abs"] == 0.0


def test_net_pnl_custom_rates_override_defaults():
    # prowizja=0, podatek=50% -> netto = zysk brutto / 2, bez zadnych kosztow transakcyjnych.
    out = net_pnl(cost_basis=100.0, market_value=200.0, commission_pct=0.0, tax_pct=50.0)
    assert out["commission_total"] == 0.0
    assert out["tax_belka"] == pytest.approx(50.0)
    assert out["net_pnl_abs"] == pytest.approx(50.0)
    assert out["net_pnl_pct"] == pytest.approx(50.0)


# --- max_drawdown_pct ------------------------------------------------------

def test_max_drawdown_known_peak_to_trough():
    close = pd.Series([100.0, 120.0, 80.0, 90.0])
    # szczyt 120 -> dolek 80 -> 80/120 - 1 = -33.33%
    assert max_drawdown_pct(close) == pytest.approx(-33.3333, rel=1e-4)


def test_max_drawdown_monotonic_up_is_zero():
    close = pd.Series([100.0, 110.0, 120.0])
    assert max_drawdown_pct(close) == pytest.approx(0.0)


def test_max_drawdown_straight_loss():
    close = pd.Series([100.0, 50.0])
    assert max_drawdown_pct(close) == pytest.approx(-50.0)


def test_max_drawdown_recovers_after_the_deepest_point():
    # dolek nie jest na koncu serii - drawdown ma zapamietac najgorszy punkt,
    # nie punkt koncowy.
    close = pd.Series([100.0, 40.0, 200.0])
    assert max_drawdown_pct(close) == pytest.approx(-60.0)
