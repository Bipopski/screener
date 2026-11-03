"""Rules-based equity screener and portfolio backtester.

Public API is re-exported here so callers do not need to know the module layout.
"""

from __future__ import annotations

from .account import Account, Costs, Position
from .backtest import Result, Signal, make_decision, metrics, run_backtest
from .data.csv import load_demo, load_prices, load_signals
from .portfolio import allocate, target_weights, val_weight
from .quality import TRELA_FILTERS, quality_score
from .scoring import pctile, score_all
from .xirr import dates_of, twr, xirr, xirr_from_result

__version__ = "0.2.0"

__all__ = [
    "Account",
    "Costs",
    "Position",
    "Result",
    "Signal",
    "TRELA_FILTERS",
    "allocate",
    "dates_of",
    "load_demo",
    "load_prices",
    "load_signals",
    "make_decision",
    "metrics",
    "pctile",
    "quality_score",
    "run_backtest",
    "score_all",
    "target_weights",
    "twr",
    "val_weight",
    "xirr",
    "xirr_from_result",
]
