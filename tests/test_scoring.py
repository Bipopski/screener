"""The growth score: dynamic bounds, renormalisation, no silent zeros."""

from __future__ import annotations

import pytest

from screener.config import MIN_WEIGHT_COVERAGE
from screener.scoring import pctile, score_all

POOL = {
    "A": {"eps_lt_growth": 0.50, "eps2y_rev3": 0.15, "ebitda_margin": 0.60},
    "B": {"eps_lt_growth": 0.30, "eps2y_rev3": 0.02, "ebitda_margin": 0.30},
    "C": {"eps_lt_growth": 0.10, "eps2y_rev3": -0.05, "ebitda_margin": 0.20},
}


def test_best_in_pool_scores_100_and_worst_scores_0():
    scores, _ = score_all(POOL)
    assert scores["A"] == 100.0
    assert scores["C"] == 0.0


def test_middle_name_lands_between():
    scores, _ = score_all(POOL)
    assert 0.0 < scores["B"] < 100.0


def test_missing_metric_is_renormalised_not_penalised():
    """A name with two metrics is scored on those two, not dragged down by a zero."""
    scores, bounds = score_all(POOL)
    single = {"A": {"eps_lt_growth": 0.50, "eps2y_rev3": None, "ebitda_margin": 0.60}}
    score, _ = score_all(single, bounds=bounds)
    assert score["A"] == 100.0


def test_score_withheld_below_minimum_weight_coverage():
    """Only the 10-point metric available — not enough to rank a company."""
    _, bounds = score_all(POOL)
    thin = {"X": {"eps_lt_growth": None, "eps2y_rev3": None, "ebitda_margin": 0.40}}
    score, _ = score_all(thin, bounds=bounds)
    assert score["X"] is None
    assert MIN_WEIGHT_COVERAGE > 10


def test_flat_bounds_do_not_divide_by_zero():
    bounds = {k: (0.2, 0.2) for k in ("eps_lt_growth", "eps2y_rev3", "ebitda_margin")}
    score, _ = score_all(POOL, bounds=bounds)
    assert all(v is None for v in score.values())


def test_score_is_monotonic_in_long_term_growth():
    _, bounds = score_all(POOL)
    low = {"T": {"eps_lt_growth": 0.20, "eps2y_rev3": 0.02, "ebitda_margin": 0.30}}
    high = {"T": {"eps_lt_growth": 0.45, "eps2y_rev3": 0.02, "ebitda_margin": 0.30}}
    s_low, _ = score_all(low, bounds=bounds)
    s_high, _ = score_all(high, bounds=bounds)
    assert s_high["T"] > s_low["T"]


def test_scores_are_clipped_to_the_scale():
    """A value beyond the 97th percentile is 100, not 130 — the scale saturates."""
    _, bounds = score_all(POOL)
    extreme = {"X": {"eps_lt_growth": 5.0, "eps2y_rev3": 5.0, "ebitda_margin": 5.0}}
    score, _ = score_all(extreme, bounds=bounds)
    assert score["X"] == 100.0


@pytest.mark.parametrize("p,expected", [(0.0, 1.0), (0.5, 2.0), (1.0, 3.0)])
def test_pctile_edges(p, expected):
    assert pctile([3.0, 1.0, 2.0], p) == expected


def test_pctile_of_empty_is_none():
    assert pctile([], 0.5) is None
