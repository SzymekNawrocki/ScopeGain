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
    cvar_pct,
    daily_returns,
    estimate_rebalance_cost,
    historical_var_pct,
    holdings_timeline,
    max_drawdown_pct,
    net_pnl,
    overlapping_horizon_returns,
    portfolio_shock_pct,
    rebalance_plan,
    reconcile_holdings,
    returns_frame,
    sharpe_ratio,
    total_return_pct,
    twr_index,
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


# --- historical_var_pct / cvar_pct (warstwa ryzyka) ------------------------

def test_historical_var_is_the_low_percentile_of_returns():
    # 100 zwrotow: -100 do -1 (procentowo -1.00 do -0.01). 5. percentyl (VaR 95%)
    # to okolice -0.95. Sprawdzamy wprost kwantyl, ktory liczy funkcja.
    returns = pd.Series([-i / 100 for i in range(1, 101)])
    expected = returns.quantile(0.05) * 100
    assert historical_var_pct(returns, confidence=0.95) == pytest.approx(expected)


def test_higher_confidence_gives_worse_var():
    # 99% siega glebiej w ogon niz 95% -> strata (liczba ujemna) wieksza co do modulu.
    returns = pd.Series([-i / 100 for i in range(1, 101)])
    assert historical_var_pct(returns, 0.99) < historical_var_pct(returns, 0.95)


def test_var_empty_series_returns_zero_not_crash():
    assert historical_var_pct(pd.Series(dtype=float)) == 0.0


def test_cvar_is_mean_of_the_tail_beyond_var():
    # Ogon (najgorsze 5%) to zwroty <= progu VaR; CVaR = ich srednia,
    # zawsze <= VaR (glebiej w strate).
    returns = pd.Series([-i / 100 for i in range(1, 101)])
    prog = returns.quantile(0.05)
    expected = returns[returns <= prog].mean() * 100
    assert cvar_pct(returns, 0.95) == pytest.approx(expected)
    assert cvar_pct(returns, 0.95) <= historical_var_pct(returns, 0.95)


def test_cvar_empty_series_returns_zero_not_crash():
    assert cvar_pct(pd.Series(dtype=float)) == 0.0


# --- overlapping_horizon_returns -------------------------------------------

def test_overlapping_window_compounds_consecutive_days():
    # Staly +10% dziennie przez 3 dni w oknie 2: kazde okno = 1.1*1.1 - 1 = 21%.
    returns = pd.Series([0.1, 0.1, 0.1])
    out = overlapping_horizon_returns(returns, window=2)
    assert len(out) == 2                       # dwa nakladajace sie okna
    assert out.iloc[0] == pytest.approx(0.21)
    assert out.iloc[1] == pytest.approx(0.21)


def test_overlapping_window_too_short_returns_empty():
    returns = pd.Series([0.1, 0.2])
    assert overlapping_horizon_returns(returns, window=5).empty


# --- portfolio_shock_pct (czysta arytmetyka stress testu) ------------------

def test_portfolio_shock_is_weighted_sum_of_shocks():
    # 60% w spolce ktora spada -50%, 40% w spolce ktora spada -10%:
    # 0.6*-0.5 + 0.4*-0.1 = -0.34 -> -34%.
    weights = {"AAA": 0.6, "BBB": 0.4}
    shocks = {"AAA": -0.5, "BBB": -0.1}
    assert portfolio_shock_pct(weights, shocks) == pytest.approx(-34.0)


def test_portfolio_shock_single_position_passes_shock_through():
    assert portfolio_shock_pct({"AAA": 1.0}, {"AAA": -0.55}) == pytest.approx(-55.0)


# --- rebalance_plan (warstwa 12c) ------------------------------------------

def test_rebalance_equal_weight_targets_one_over_n():
    # 3 spolki -> cel 33.33% kazda. Przewazona ma dryf dodatni i trade ujemny.
    holdings = {"AAA": 6000.0, "BBB": 2000.0, "CCC": 2000.0}  # total 10000
    plan = {p["ticker"]: p for p in rebalance_plan(holdings)}
    assert plan["AAA"]["target_weight_pct"] == pytest.approx(33.33, abs=0.01)
    assert plan["AAA"]["current_weight_pct"] == pytest.approx(60.0)
    assert plan["AAA"]["drift_pp"] == pytest.approx(26.67, abs=0.01)  # przewazona
    assert plan["AAA"]["trade_value"] == pytest.approx(-2666.67, abs=0.01)  # przytnij
    assert plan["BBB"]["trade_value"] == pytest.approx(1333.33, abs=0.01)   # dokup


def test_rebalance_trades_sum_to_zero():
    # Przesuwamy w obrebie portfela - suma ruchow ~ 0.
    holdings = {"AAA": 5000.0, "BBB": 3000.0, "CCC": 2000.0}
    plan = rebalance_plan(holdings)
    assert sum(p["trade_value"] for p in plan) == pytest.approx(0.0, abs=0.05)


def test_rebalance_already_balanced_needs_no_trades():
    holdings = {"AAA": 1000.0, "BBB": 1000.0}
    plan = rebalance_plan(holdings)
    assert all(p["trade_value"] == pytest.approx(0.0) for p in plan)
    assert all(p["drift_pp"] == pytest.approx(0.0) for p in plan)


def test_rebalance_custom_target_weights():
    holdings = {"AAA": 5000.0, "BBB": 5000.0}  # total 10000
    plan = {p["ticker"]: p for p in rebalance_plan(holdings, {"AAA": 0.7, "BBB": 0.3})}
    assert plan["AAA"]["trade_value"] == pytest.approx(2000.0)   # do 70% = 7000, dokup 2000
    assert plan["BBB"]["trade_value"] == pytest.approx(-2000.0)  # do 30% = 3000, przytnij


def test_rebalance_empty_or_zero_total_returns_empty():
    assert rebalance_plan({}) == []
    assert rebalance_plan({"AAA": 0.0}) == []


# --- estimate_rebalance_cost -----------------------------------------------

def test_rebalance_cost_commission_on_both_sides():
    # przytnij 1000 (z zyskownej pozycji) + dokup 1000: prowizja 0.29% od kazdej.
    legs = [
        {"trade_value": -1000.0, "market_value": 5000.0, "cost_basis": 2500.0},
        {"trade_value": 1000.0, "market_value": 1000.0, "cost_basis": 1000.0},
    ]
    out = estimate_rebalance_cost(legs)
    assert out["commission"] == pytest.approx(2000.0 * 0.29 / 100)  # 5.80


def test_rebalance_cost_belka_only_on_realized_gain_of_sells():
    # przycinamy 1000 z pozycji wartej 5000 przy koszcie 2500 (zysk 50%).
    # zrealizowany zysk = (1000/5000)*(5000-2500) = 500 -> Belka 19% = 95.
    legs = [{"trade_value": -1000.0, "market_value": 5000.0, "cost_basis": 2500.0}]
    out = estimate_rebalance_cost(legs)
    assert out["tax_belka"] == pytest.approx(95.0)


def test_rebalance_cost_no_belka_when_trimming_a_loser():
    # pozycja pod woda (wartosc < koszt) -> sprzedaz nie generuje podatku.
    legs = [{"trade_value": -1000.0, "market_value": 2000.0, "cost_basis": 3000.0}]
    out = estimate_rebalance_cost(legs)
    assert out["tax_belka"] == 0.0


def test_rebalance_cost_buys_pay_only_commission():
    legs = [{"trade_value": 1000.0, "market_value": 1000.0, "cost_basis": 1000.0}]
    out = estimate_rebalance_cost(legs)
    assert out["tax_belka"] == 0.0
    assert out["commission"] == pytest.approx(1000.0 * 0.29 / 100)


# --- holdings_timeline (realna sciezka z logu) -----------------------------

def test_holdings_timeline_steps_on_transaction_dates():
    dates = pd.date_range("2024-01-01", periods=5)
    txs = [
        {"ticker": "AAPL", "side": "BUY", "quantity": 10, "executed_at": "2024-01-01"},
        {"ticker": "AAPL", "side": "BUY", "quantity": 5, "executed_at": "2024-01-03"},
        {"ticker": "AAPL", "side": "SELL", "quantity": 4, "executed_at": "2024-01-04"},
    ]
    h = holdings_timeline(txs, dates)
    # 10 od 1., 15 od 3., 11 od 4.
    assert h["AAPL"].tolist() == [10.0, 10.0, 15.0, 11.0, 11.0]


def test_holdings_timeline_multiple_tickers():
    dates = pd.date_range("2024-01-01", periods=3)
    txs = [
        {"ticker": "AAPL", "side": "BUY", "quantity": 10, "executed_at": "2024-01-01"},
        {"ticker": "MSFT", "side": "BUY", "quantity": 2, "executed_at": "2024-01-02"},
    ]
    h = holdings_timeline(txs, dates)
    assert h["MSFT"].tolist() == [0.0, 2.0, 2.0]
    assert h["AAPL"].tolist() == [10.0, 10.0, 10.0]


# --- twr_index (time-weighted, odporny na przeplywy) -----------------------

def test_twr_starts_at_100_on_first_holding_day():
    dates = pd.date_range("2024-01-01", periods=3)
    values = pd.Series([1000.0, 1100.0, 1210.0], index=dates)
    flows = pd.Series([1000.0, 0.0, 0.0], index=dates)   # tylko poczatkowa wplata
    twr = twr_index(values, flows)
    assert twr.iloc[0] == pytest.approx(100.0)
    assert twr.iloc[1] == pytest.approx(110.0)   # +10%
    assert twr.iloc[2] == pytest.approx(121.0)   # +10% skladane


def test_twr_neutralizes_a_cash_inflow_midway():
    # dzien 2: wartosc rosnie z 1000 do 2100, ale 1000 to DOKUPIENIE (flow),
    # wiec realny zwrot rynku = (2100-1000)/1000 - 1 = +10%, nie +110%.
    dates = pd.date_range("2024-01-01", periods=2)
    values = pd.Series([1000.0, 2100.0], index=dates)
    flows = pd.Series([1000.0, 1000.0], index=dates)
    twr = twr_index(values, flows)
    assert twr.iloc[1] == pytest.approx(110.0)


def test_twr_ignores_leading_empty_days():
    dates = pd.date_range("2024-01-01", periods=3)
    values = pd.Series([0.0, 1000.0, 1050.0], index=dates)
    flows = pd.Series([0.0, 1000.0, 0.0], index=dates)
    twr = twr_index(values, flows)
    assert len(twr) == 2                          # zaczyna od dnia z pozycja
    assert twr.iloc[0] == pytest.approx(100.0)
    assert twr.iloc[1] == pytest.approx(105.0)


# --- reconcile_holdings ----------------------------------------------------

def test_reconcile_matches_when_log_equals_positions():
    out = reconcile_holdings({"AAPL": 6.0, "MSFT": 5.0}, {"AAPL": 6.0, "MSFT": 5.0})
    assert out["reconciled"] is True
    assert out["discrepancies"] == []


def test_reconcile_flags_mismatch_with_diff():
    out = reconcile_holdings({"AAPL": 6.0}, {"AAPL": 10.0})
    assert out["reconciled"] is False
    assert out["discrepancies"][0]["diff"] == pytest.approx(-4.0)


def test_reconcile_flags_ticker_missing_on_one_side():
    out = reconcile_holdings({"AAPL": 6.0, "NVDA": 3.0}, {"AAPL": 6.0})
    assert out["reconciled"] is False
    assert {d["ticker"] for d in out["discrepancies"]} == {"NVDA"}


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
