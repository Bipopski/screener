"""XIRR on real dates, plus a time-weighted return.

Money-weighted return answers "what did the investor earn"; time-weighted
answers "what does the strategy earn per unit of capital". Reporting only one of
them hides whether a result came from the strategy or from the timing of
deposits, so both live here.
"""

from __future__ import annotations

import calendar
import datetime as dt


def _eom(year: int, month: int) -> dt.date:
    return dt.date(year, month, calendar.monthrange(year, month)[1])


def dates_of(months: list[str]) -> list[dt.date]:
    """``['2022-11', ...]`` -> month-end dates."""
    out = []
    for s in months:
        y, m = s.split("-")
        out.append(_eom(int(y), int(m)))
    return out


def xirr(flows, lo: float = -0.9999, hi: float = 10.0, tol: float = 1e-9):
    """Annual rate for ``[(date, amount)]``; ``None`` when there is no sign change.

    Solved by bisection on actual dates with a 365-day year. Putting the closing
    valuation one period after the last contribution understates the rate by
    1.5–2.6 pp on a four-year book, so flows must carry the valuation on the
    last contribution's date.
    """
    if not flows:
        return None
    d0 = min(d for d, _ in flows)

    def npv(rate: float) -> float:
        return sum(a / (1.0 + rate) ** ((d - d0).days / 365.0) for d, a in flows)

    f_lo, f_hi = npv(lo), npv(hi)
    if f_lo * f_hi > 0:
        return None
    for _ in range(300):
        mid = (lo + hi) / 2
        value = npv(mid)
        if abs(value) < tol:
            return mid
        if value * f_lo > 0:
            lo, f_lo = mid, value
        else:
            hi = mid
    return (lo + hi) / 2


def xirr_from_result(res: dict, contrib: float = 1000.0):
    """XIRR of a backtest result (``unit_hist`` + contributions)."""
    months = [m for m, _, _, _ in res["unit_hist"]]
    ds = dates_of(months)
    flows = [(d, -contrib) for d in ds]
    flows[-1] = (flows[-1][0], flows[-1][1] + res["final"])
    return xirr(flows)


def twr(res: dict):
    """Time-weighted annual return from the unit-value series."""
    uv = [u for _, u, _, _ in res["unit_hist"]]
    if len(uv) < 2 or uv[0] <= 0:
        return None
    return (uv[-1] / uv[0]) ** (12.0 / (len(uv) - 1)) - 1
