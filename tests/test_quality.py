"""The sieve: eight conditions, no partial credit, missing data is a failure."""

from __future__ import annotations

import pytest

from screener.quality import TRELA_FILTERS, quality_score

PASSING = {
    "rev_est_2y": 0.20,      # fraction
    "eps_est_2y": 0.30,      # fraction
    "eps_ttm": 2.50,
    "ebitda_margin": 36.6,   # percent
    "roic": 22.6,            # percent
    "cfo": 464_000_000.0,
    "price": 150.0,
    "ltg_analysts": 3,
}


def test_passing_row_gets_full_marks():
    score, reasons = quality_score(PASSING)
    assert score == 100.0
    assert reasons == []


def test_two_analysts_disqualify_before_anything_else():
    score, reasons = quality_score({**PASSING, "ltg_analysts": 2})
    assert score == 0.0
    assert len(reasons) == 1
    assert "mniej niż 3 analityków" in reasons[0]


@pytest.mark.parametrize("key,value,label", [
    ("rev_est_2y", 0.02, "prognoza wzrostu przychodów 2Y"),
    ("eps_est_2y", 0.01, "prognoza wzrostu EPS 2Y"),
    ("eps_ttm", 0.05, "EPS TTM"),
    ("ebitda_margin", 9.0, "marża EBITDA"),
    ("roic", 4.0, "ROIC"),
    ("cfo", -1.0, "gotówka operacyjna"),
    ("price", 3.0, "cena akcji"),
])
def test_each_condition_can_fail_on_its_own(key, value, label):
    """One failing input is enough — the sieve is an AND, not a score."""
    score, reasons = quality_score({**PASSING, key: value})
    assert score == 0.0
    assert any(label in reason for reason in reasons)
    assert len(reasons) == 1


@pytest.mark.parametrize("key", [f[0] for f in TRELA_FILTERS])
def test_missing_input_is_a_failure_not_a_neutral(key):
    row = {k: v for k, v in PASSING.items() if k != key}
    score, reasons = quality_score(row)
    assert score == 0.0
    assert any("brak danych" in reason for reason in reasons)


def test_margin_units_are_percent_not_fraction():
    """A 36% margin passed as 0.366 must fail: the sieve compares against 15.0."""
    score, _ = quality_score({**PASSING, "ebitda_margin": 0.366})
    assert score == 0.0


def test_zero_analysts_fails_even_with_perfect_fundamentals():
    score, _ = quality_score({**PASSING, "ltg_analysts": 0})
    assert score == 0.0
