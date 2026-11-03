"""Sizing: valuation sets the weight, cash follows the deficit."""

from __future__ import annotations

import pytest

from screener.config import MIN_WEIGHT
from screener.portfolio import allocate, target_weights, val_weight


def test_cheapest_name_gets_the_largest_weight():
    weights = target_weights(["cheap", "mid", "dear"], {"cheap": 0, "mid": 50, "dear": 100})
    assert weights["cheap"] > weights["mid"] > weights["dear"]


def test_weights_sum_to_one():
    weights = target_weights(["a", "b", "c"], {"a": 10, "b": 55, "c": 95})
    assert sum(weights.values()) == pytest.approx(1.0)


def test_percentile_of_zero_is_a_value_not_missing_data():
    """0 means cheapest in its own history; treating it as missing flips the sizing."""
    assert val_weight(0) == pytest.approx(2.5)
    assert val_weight(None) == pytest.approx(1.0)


def test_weight_never_falls_below_the_floor():
    assert val_weight(100) == pytest.approx(MIN_WEIGHT)


def test_allocation_is_proportional_to_deficits():
    """A first-come-first-served loop starves the last name; this must not."""
    cash = 400.0                      # exactly the sum of the deficits
    target = {"a": 1000.0, "b": 1000.0}
    held = {"a": 700.0, "b": 900.0}   # deficits: 300 and 100
    plan = allocate(cash, target, held, skip_smallest=False)
    assert plan["a"] == pytest.approx(300.0)
    assert plan["b"] == pytest.approx(100.0)


def test_cash_beyond_the_deficits_stays_in_cash():
    """A single pass never buys past a target weight — leftover stays uninvested."""
    plan = allocate(1000.0, {"a": 1000.0, "b": 1000.0}, {"a": 700.0, "b": 900.0},
                    skip_smallest=False)
    assert sum(plan.values()) == pytest.approx(400.0)


def test_allocation_is_capped_by_the_deficit():
    plan = allocate(1000.0, {"a": 50.0}, {}, skip_smallest=False)
    assert plan["a"] == pytest.approx(50.0)


def test_overweight_names_get_nothing():
    plan = allocate(500.0, {"a": 100.0, "b": 900.0}, {"a": 400.0}, skip_smallest=False)
    assert "a" not in plan
    assert plan["b"] == pytest.approx(500.0)


def test_skip_smallest_drops_the_tail_and_renormalises():
    plan = allocate(1000.0, {"a": 900.0, "b": 100.0}, {}, skip_smallest=True)
    assert list(plan) == ["a"]
    assert plan["a"] == pytest.approx(1000.0)


def test_nothing_to_do_returns_empty():
    assert allocate(0.0, {"a": 100.0}, {}) == {}
    assert allocate(100.0, {"a": 10.0}, {"a": 50.0}) == {}
