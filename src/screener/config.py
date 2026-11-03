"""Strategy parameters — the single place where numbers live.

Two groups:

* **Model** — how a company is scored (weights and percentile bands).
* **Portfolio** — how the book is built (size, valuation tilt, exits).

Anything that a reader might want to change belongs here, not in the modules.
"""

from __future__ import annotations

# --- model -------------------------------------------------------------------

#: Points per metric (sum = 100). Growth dominates on purpose: the score answers
#: "is this company growing", not "is it cheap".
MODEL_WEIGHTS: dict[str, float] = {
    "eps_lt_growth": 70.0,   # long-term EPS growth forecast
    "eps2y_rev3": 20.0,      # 3-month revision of the 2-year EPS forecast
    "ebitda_margin": 10.0,   # last reported TTM margin
}

#: Lower and upper percentile of the gated pool used to map a metric onto 0–1.
P_LO, P_HI = 0.03, 0.97

#: A score is only reported when at least this much of the model weight could be
#: computed; below it the score is ``None`` (missing inputs shrink the score, not
#: the ranking).
MIN_WEIGHT_COVERAGE = 40.0

#: A revision larger than this is treated as a fiscal-year shift, not a revision.
REV_MAX = 1.0

# --- quality sieve -----------------------------------------------------------

#: Hard minimum of analysts publishing a long-term growth estimate. The score
#: gives 70 of 100 points to that single number, so one analyst is not a forecast.
MIN_ANALYSTS = 3

# --- portfolio ---------------------------------------------------------------

#: Number of positions in the book.
PORTFOLIO_SIZE = 6

#: Valuation tilt: w = max(MIN_WEIGHT, 1 - LAMBDA * (pct - 50) / 50).
VALUATION_LAMBDA = 1.5
MIN_WEIGHT = 0.05

# --- exits -------------------------------------------------------------------

#: Exit when the 3-month EPS-2Y revision lands in this worst percentile of the
#: gated pool...
EXIT_PERCENTILE = 10

#: ...and does not rebound in the last month.
EXIT_REQUIRES_NO_REBOUND = True
