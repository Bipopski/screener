"""Rules-based equity screener and portfolio backtester.

Public API is re-exported here so callers do not need to know the module layout.
"""

from __future__ import annotations

from .quality import TRELA_FILTERS, quality_score
from .scoring import pctile, score_all
from .xirr import dates_of, twr, xirr, xirr_from_result

__version__ = "0.1.0"

__all__ = [
    "TRELA_FILTERS",
    "quality_score",
    "pctile",
    "score_all",
    "dates_of",
    "twr",
    "xirr",
    "xirr_from_result",
]
