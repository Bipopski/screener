"""Generate the demo dataset: synthetic, deterministic, provenance-free.

The demo exists so the repo runs after a clone with no data account, and so the
tests have a market to walk through. It is **synthetic**: geometric random walks
with a per-ticker drift, plus invented model inputs. Nothing here comes from a
paid feed, and nothing here says anything about a real company — the tickers are
``DEMO01…DEMO25`` on purpose.

Run: ``python scripts/make_demo.py`` (writes into ``examples/demo/``).
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

TICKERS = [f"DEMO{i:02d}" for i in range(1, 26)]
MONTHS = [f"{y}-{m:02d}" for y in range(2021, 2027) for m in range(1, 13)][:60]
OUT = Path(__file__).resolve().parents[1] / "examples" / "demo"


def main() -> None:
    rng = random.Random(20261103)
    OUT.mkdir(parents=True, exist_ok=True)

    with (OUT / "prices.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ticker", "month", "price_pln"])
        for ticker in TICKERS:
            price = rng.uniform(20, 400)
            drift = rng.uniform(-0.004, 0.018)
            vol = rng.uniform(0.04, 0.12)
            for month in MONTHS:
                price = max(1.0, price * (1 + rng.gauss(drift, vol)))
                writer.writerow([ticker, month, round(price, 2)])

    with (OUT / "signals.csv").open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ticker", "month", "score", "quality", "rev3", "rev1", "val_pct"])
        for ticker in TICKERS:
            base_score = rng.uniform(45, 90)
            base_val = rng.uniform(0, 100)
            # three companies lose the sieve halfway through, three get a forecast cut
            weak = ticker in {"DEMO04", "DEMO11", "DEMO19"}
            cut = ticker in {"DEMO07", "DEMO16", "DEMO22"}
            for i, month in enumerate(MONTHS):
                score = round(min(100.0, max(0.0, base_score + rng.gauss(0, 3))), 1)
                quality = 100.0 if not (weak and i > 30) else 0.0
                rev3 = round(rng.gauss(0.02, 0.05), 4)
                if cut and i > 24:
                    rev3 = round(-0.12 + rng.gauss(0, 0.01), 4)
                writer.writerow([ticker, month, score, quality, rev3,
                                 round(rev3 / 2, 4), round(min(100.0, max(0.0, base_val
                                                                       + rng.gauss(0, 6))), 1)])

    print(f"demo: {len(TICKERS)} tickers × {len(MONTHS)} months → {OUT}")


if __name__ == "__main__":
    main()
