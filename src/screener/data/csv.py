"""CSV adapter — the demo dataset and any file with the same schema.

Two files, documented in ``examples/demo/README.md``:

``prices.csv``   ticker, month (``YYYY-MM``), price_pln
``signals.csv``  ticker, month, score, quality, rev3, rev1, val_pct

The adapter is deliberately dumb: it turns files into the two mappings the
engine consumes and refuses to guess. A real feed (free API or paid provider)
implements the same output shape — that is the whole point of keeping data
access behind one seam.
"""

from __future__ import annotations

import csv
from pathlib import Path

from ..backtest import Signal


def _rows(path: Path):
    with path.open(newline="") as fh:
        yield from csv.DictReader(fh)


def load_prices(path: str | Path) -> dict[str, dict[str, float]]:
    prices: dict[str, dict[str, float]] = {}
    for row in _rows(Path(path)):
        prices.setdefault(row["month"], {})[row["ticker"]] = float(row["price_pln"])
    return prices


def load_signals(path: str | Path) -> dict[str, dict[str, Signal]]:
    signals: dict[str, dict[str, Signal]] = {}
    for row in _rows(Path(path)):
        signals.setdefault(row["month"], {})[row["ticker"]] = Signal(
            score=float(row["score"]),
            quality=float(row["quality"]),
            rev3=float(row["rev3"]),
            rev1=float(row["rev1"]),
            val_pct=float(row["val_pct"]),
        )
    return signals


def load_demo(directory: str | Path) -> tuple[dict, dict]:
    """Load ``prices.csv`` and ``signals.csv`` from a directory, sorted by month."""
    directory = Path(directory)
    prices = load_prices(directory / "prices.csv")
    signals = load_signals(directory / "signals.csv")
    months = sorted(set(prices) & set(signals))
    return ({m: signals[m] for m in months}, {m: prices[m] for m in months})
