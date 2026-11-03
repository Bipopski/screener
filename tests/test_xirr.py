"""Returns: XIRR on real dates and time-weighted return."""

from __future__ import annotations

import datetime as dt

import pytest

from screener.xirr import dates_of, twr, xirr, xirr_from_result


def test_xirr_of_a_single_year_gain_of_ten_percent():
    rate = xirr([(dt.date(2023, 1, 1), -1000.0), (dt.date(2024, 1, 1), 1100.0)])
    assert rate == pytest.approx(0.10, abs=1e-3)


def test_xirr_needs_a_sign_change():
    assert xirr([(dt.date(2023, 1, 1), -1000.0), (dt.date(2024, 1, 1), -500.0)]) is None
    assert xirr([]) is None


def test_month_end_dates_handle_leap_years():
    assert dates_of(["2024-02"])[0] == dt.date(2024, 2, 29)
    assert dates_of(["2023-02"])[0] == dt.date(2023, 2, 28)


def test_closing_value_sits_on_the_last_contribution_date():
    """Valuation one period late understates the rate — the bug this function fixes.

    The same closing value, placed 31 days after the last deposit instead of on
    it, must produce a lower annual rate.
    """
    months = [f"2023-{m:02d}" for m in range(1, 13)]
    unit_hist = [(m, 1.0 + 0.02 * i, 0.0, 0.0) for i, m in enumerate(months)]
    res = {"unit_hist": unit_hist, "final": 13200.0}

    on_time = xirr_from_result(res, contrib=1000.0)
    ds = dates_of(months)
    late = [(d, -1000.0) for d in ds] + [(ds[-1] + dt.timedelta(days=31), 13200.0)]

    assert on_time is not None and xirr(late) is not None
    assert on_time > xirr(late)


def test_twr_annualises_geometrically():
    """24 monthly points ending +21% is 10% a year, not the 10.5% of an arithmetic mean."""
    n = 25
    unit_hist = [(f"m{i}", 1.21 ** (i / (n - 1)), 0.0, 0.0) for i in range(n)]
    assert twr({"unit_hist": unit_hist}) == pytest.approx(0.10, abs=1e-6)


def test_twr_needs_two_points():
    assert twr({"unit_hist": [("2023-01", 1.0, 0, 0)]}) is None
