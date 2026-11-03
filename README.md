# screener

A rules-based equity screener and portfolio backtester: a hard quality sieve, a
growth score computed on the surviving pool, a six-position book weighted by
each name's own valuation history, and two exit rules.

The point of the repo is the **method and its accounting**, not a stock tip. The
backtest is built to be auditable: portfolio values are converted to one
currency, contributions and P&L reconcile to the złoty, the money-weighted
return is checked against a date-based XIRR, and results are reported on
disjoint blocks rather than one lucky path.

## What this is not

- **Not investment advice**, and not a promise of returns. The reference run
  covers 48 months of a single regime (an AI-led bull market); the same rules
  would have behaved differently in another one.
- **Not a screener for everything.** The universe is capped by market
  capitalisation and requires analyst forecasts; companies without coverage are
  deliberately excluded, even when they are good businesses.
- **Not a trading system.** The tested design holds positions for a median of
  nine months and sells 11 times in four years. Adding rotation, stops or
  market-timing overlays was tested and made results worse — see
  `docs/decisions.md` once it lands.

## Status

Early. What exists today is the model core, moved from a working research
codebase and covered by tests:

| module | what it does |
|---|---|
| `screener.quality` | the eight-condition sieve, no partial credit |
| `screener.scoring` | growth score 0–100 on dynamic percentile bounds |
| `screener.xirr` | XIRR on real dates and time-weighted return |
| `screener.config` | every threshold and weight, in one place |

Next: universe building, portfolio construction, the monthly backtest loop and a
CLI — each landing with tests and a demo dataset, so the repo runs after a clone
without any paid data account.

## Quickstart

```bash
uv venv && uv pip install -e ".[dev]"
pytest
```

## Units, because they bite

- growth forecasts (`rev_est_2y`, `eps_est_2y`) are **fractions**: `0.05` = 5%
- margins (`ebitda_margin`, `roic`) are **percent**: `36.6` = 36.6%
- a missing input fails the sieve; it is never treated as neutral

## Licence

MIT. See `LICENSE`.
