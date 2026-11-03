# Demo dataset

Synthetic, deterministic and small: **25 tickers × 60 months** (2021-01 … 2026-10),
about 60 KB per file. It exists so the repo runs after a clone without any data
account, and so tests have a market to walk through.

**Nothing here is real, and its returns mean nothing.** Tickers are `DEMO01…DEMO25`,
prices are seeded random walks, model inputs are invented *independently of the
prices* — so the demo exercises the mechanics (exits, sizing, accounting) and
cannot show performance. A negative result on this data is not a result. There are no prices, forecasts or fundamentals
from any provider in this directory, which is also why it can live in a public
repository.

Regenerate with `python scripts/make_demo.py` (seed 20261103 — the output is
byte-stable for a given Python version).

## `prices.csv`

| column | type | meaning |
|---|---|---|
| `ticker` | string | instrument identifier |
| `month` | `YYYY-MM` | month-end valuation date |
| `price_pln` | float | month-end close, already converted to the portfolio currency |

## `signals.csv`

| column | type | meaning |
|---|---|---|
| `ticker` | string | instrument identifier |
| `month` | `YYYY-MM` | month of the decision |
| `score` | 0–100 | growth score (see `screener.scoring`) |
| `quality` | 0 or 100 | sieve result; anything below the floor is an exit |
| `rev3` | fraction | 3-month revision of the 2-year EPS forecast |
| `rev1` | fraction | 1-month revision, used to require "no rebound" |
| `val_pct` | 0–100 | percentile of forward P/E against the company's own history |

The engine reads exactly these two mappings — `{month: {ticker: ...}}` — so a
real adapter (free API or paid feed) only has to produce the same shape.

## Why it is synthetic

A demo built from a paid source would put licensed data in a public commit and
make the quickstart depend on a subscription. Synthetic data keeps the repo
honest: the method is demonstrated, no vendor is redistributed, and the numbers
in `docs/results.md` stay the only place where real-market results are quoted.
