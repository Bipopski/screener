"""The engine: accounting identity, position count, exits, costs and tax."""

from __future__ import annotations

import pytest

from screener.account import Costs
from screener.backtest import Signal, make_decision, run_backtest

FREE = Costs(spread_bps=0.0, fx_fee=0.0)


def _signals(scores, **kwargs):
    return {t: Signal(score=s, quality=100.0, **kwargs) for t, s in scores.items()}


def test_contributions_plus_pnl_equal_the_book_value():
    """The identity that makes every published number auditable."""
    months = ["2024-01", "2024-02", "2024-03"]
    signals = {m: _signals({"A": 90.0}) for m in months}
    prices = {m: {"A": 10.0} for m in months}

    result = run_backtest(signals, prices, costs=FREE, contrib=1000.0, n=1)

    assert result.final == pytest.approx(3000.0)
    assert result.invested == pytest.approx(3000.0)
    assert result.twr == pytest.approx(0.0, abs=1e-12)
    assert result.trades == 3


def test_book_never_holds_more_than_n_positions():
    months = [f"2024-{m:02d}" for m in range(1, 7)]
    scores = {f"T{i}": 90.0 - i for i in range(10)}
    signals = {m: _signals(scores) for m in months}
    prices = {m: {t: 10.0 + i for i, t in enumerate(scores)} for m in months}

    result = run_backtest(signals, prices, costs=FREE, contrib=1000.0, n=3)

    assert max(k for _, _, _, k in result.unit_hist) <= 3
    assert len(result.positions_hist[-1][1]) == 3


def test_losing_the_sieve_sells_the_position():
    months = ["2024-01", "2024-02"]
    signals = {
        "2024-01": {"A": Signal(score=90.0, quality=100.0)},
        "2024-02": {"A": Signal(score=90.0, quality=0.0)},
    }
    prices = {m: {"A": 10.0} for m in months}

    result = run_backtest(signals, prices, costs=FREE, contrib=1000.0, n=1)

    assert result.positions_hist[-1][1] == ()


def test_a_cut_forecast_in_the_worst_decile_sells():
    """Ten names in the pool: the decile lands on the second-lowest revision."""
    months = ["2024-01", "2024-02"]
    good = {f"G{i}": Signal(score=90.0 - i, quality=100.0, rev3=0.10, rev1=0.02)
            for i in range(9)}
    pool_jan = {**good, "X": Signal(score=95.0, quality=100.0, rev3=0.10, rev1=0.02)}
    pool_feb = {**good, "X": Signal(score=95.0, quality=100.0, rev3=-0.20, rev1=-0.01)}
    prices = {m: {t: 10.0 for t in pool_jan} for m in months}

    result = run_backtest({"2024-01": pool_jan, "2024-02": pool_feb},
                          prices, costs=FREE, contrib=1000.0, n=1)

    assert result.positions_hist[0][1] == ("X",)
    assert "X" not in result.positions_hist[1][1]


def test_missing_signal_is_not_a_sell_signal():
    months = ["2024-01", "2024-02"]
    signals = {"2024-01": {"A": Signal(score=90.0, quality=100.0)}, "2024-02": {}}
    prices = {m: {"A": 10.0} for m in months}

    result = run_backtest(signals, prices, costs=FREE, contrib=1000.0, n=1)

    assert result.positions_hist[-1][1] == ("A",)


def test_selling_a_gain_outside_a_wrapper_pays_tax():
    signals = {"2024-01": {"A": Signal(score=90.0, quality=100.0)},
               "2024-02": {"A": Signal(score=90.0, quality=0.0)}}
    prices = {"2024-01": {"A": 10.0}, "2024-02": {"A": 20.0}}
    regular = Costs(spread_bps=0.0, fx_fee=0.0, tax_rate=0.19, wrapper="regular")

    result = run_backtest(signals, prices, costs=regular, contrib=1000.0, n=1)

    # 1000 zł invested, doubled, minus 190 zł tax, plus the second contribution
    assert result.tax_paid == pytest.approx(190.0, rel=1e-6)
    assert result.final == pytest.approx(2810.0, rel=1e-6)


def test_spread_reduces_what_the_same_money_buys():
    months = ["2024-01", "2024-02"]
    signals = {m: {"A": Signal(score=90.0, quality=100.0)} for m in months}
    prices = {"2024-01": {"A": 10.0}, "2024-02": {"A": 10.0}}
    with_cost = Costs(spread_bps=100.0, fx_fee=0.0)

    free = run_backtest(signals, prices, costs=FREE, contrib=1000.0, n=1)
    charged = run_backtest(signals, prices, costs=with_cost, contrib=1000.0, n=1)

    assert charged.final < free.final
    assert charged.final == pytest.approx(2 * 1000 * 0.99, rel=1e-6)


def test_decision_keeps_held_names_and_fills_free_slots():
    signals = {"A": Signal(score=80.0, quality=100.0),
               "B": Signal(score=95.0, quality=100.0),
               "C": Signal(score=90.0, quality=100.0)}
    target, exits = make_decision(signals, {"A"}, n=2)
    assert exits == []
    assert target == ["A", "B"]


def test_decision_does_not_rebuy_what_it_just_sold():
    signals = {"A": Signal(score=99.0, quality=0.0), "B": Signal(score=50.0, quality=100.0)}
    target, exits = make_decision(signals, {"A"}, n=2, q_min=70.0)
    assert exits == ["A"]
    assert target == ["B"]
