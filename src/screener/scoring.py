"""Growth score, 0–100, computed on the gated pool.

The scale is dynamic: bounds are the 3rd and 97th percentile of the pool being
scored, so a score means "where this company sits among today's candidates",
never "how good in the abstract". Pass ``bounds`` explicitly to score names that
are not in the pool (watchlists) on the pool's scale.

Missing metrics are skipped and the remaining weights are renormalised, but the
score is withheld entirely below ``MIN_WEIGHT_COVERAGE`` of computed weight — a
name scored on one metric is not comparable with a name scored on three.
"""

from __future__ import annotations

from .config import MIN_WEIGHT_COVERAGE, MODEL_WEIGHTS, P_HI, P_LO

WEIGHTS = MODEL_WEIGHTS


def pctile(vals, p):
    """Nearest-rank percentile of ``vals``."""
    if not vals:
        return None
    s = sorted(vals)
    k = int(round((len(s) - 1) * p))
    return s[max(0, min(len(s) - 1, k))]


def score_all(raw_by_ticker, bounds=None):
    """Return ``({ticker: score|None}, bounds)``.

    ``raw_by_ticker`` maps a ticker to ``{metric: value|None}``. When ``bounds``
    is omitted, it is derived from the passed pool — which is why callers must
    pass the whole pool, not a single name.
    """
    if bounds is None:
        bounds = {}
        for key in WEIGHTS:
            vals = [r[key] for r in raw_by_ticker.values() if r.get(key) is not None]
            bounds[key] = (pctile(vals, P_LO), pctile(vals, P_HI)) if vals else (None, None)

    out: dict[str, float | None] = {}
    for ticker, raw in raw_by_ticker.items():
        num = den = 0.0
        for key, weight in WEIGHTS.items():
            lo, hi = bounds[key]
            value = raw.get(key)
            if value is None or lo is None or hi is None or hi <= lo:
                continue
            points = max(0.0, min(1.0, (value - lo) / (hi - lo)))
            num += weight * points
            den += weight
        out[ticker] = round(num / den * 100, 1) if den >= MIN_WEIGHT_COVERAGE else None
    return out, bounds
