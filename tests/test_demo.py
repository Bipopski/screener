"""End to end: the demo dataset through the engine, with the books checked."""

from __future__ import annotations

from pathlib import Path

import pytest

from screener.account import Costs
from screener.backtest import run_backtest
from screener.data.csv import load_demo

DEMO = Path(__file__).resolve().parents[1] / "examples" / "demo"


@pytest.fixture(scope="module")
def result():
    signals, prices = load_demo(DEMO)
    return run_backtest(signals, prices, foreign=set(),
                        costs=Costs(spread_bps=10.0, fx_fee=0.0, wrapper="ike"),
                        contrib=1000.0, n=6)


def test_demo_loads_the_documented_shape():
    signals, prices = load_demo(DEMO)
    assert len(signals) == len(prices) == 60
    assert all(len(month) == 25 for month in prices.values())


def test_engine_runs_and_keeps_its_books(result):
    """``run_backtest`` asserts contributions + P&L = value every single month."""
    assert result.invested == pytest.approx(60_000.0)
    assert result.final > 0
    assert result.trades > 20


def test_position_count_never_exceeds_n(result):
    assert max(k for _, _, _, k in result.unit_hist) <= 6
    assert len(result.positions_hist[-1][1]) == 6


def test_exits_actually_fire_on_the_demo(result):
    """Three companies lose the sieve and three get forecasts cut — names must leave."""
    left = 0
    for (_m1, prev), (_m2, now) in zip(result.positions_hist,
                                       result.positions_hist[1:], strict=False):
        left += len(set(prev) - set(now))
    assert left >= 3


def test_metrics_are_finite(result):
    assert result.twr is not None and -1.0 < result.twr < 5.0
    assert result.irr is not None and -1.0 < result.irr < 5.0
    assert -1.0 <= result.max_drawdown <= 0.0
