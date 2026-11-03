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

Working core, tested end to end on a synthetic dataset:

| module | what it does |
|---|---|
| `screener.quality` | the eight-condition sieve, no partial credit |
| `screener.scoring` | growth score 0–100 on dynamic percentile bounds |
| `screener.portfolio` | weights from valuation history, cash split by deficit |
| `screener.account` | ledger: cash, positions, units, contributions + P&L = value |
| `screener.backtest` | monthly loop: decision → execution → valuation → accounting |
| `screener.xirr` | XIRR on real dates and time-weighted return |
| `screener.config` | every threshold and weight, in one place |
| `screener.data.csv` | the demo/CSV adapter (a free or paid feed plugs in here) |

Next: a free-data adapter, a CLI (`scan`, `backtest`, `audit`), and CI.

## Quickstart

```bash
uv venv && uv pip install -e ".[dev]"
pytest
```

Run the engine on the bundled demo (25 synthetic tickers × 60 months):

```python
from screener import Costs, load_demo, run_backtest

signals, prices = load_demo("examples/demo")
result = run_backtest(signals, prices, costs=Costs(wrapper="ike"),
                      contrib=1000.0, n=6)

print(f"{result.final:,.0f} zł from {result.invested:,.0f} zł invested")
print(f"TWR {result.twr:.1%} · IRR {result.irr:.1%} · max DD {result.max_drawdown:.1%}")
```

The accounting identity is checked inside the loop every month — a run that
loses a fee somewhere raises instead of returning a plausible number.

## Units, because they bite

- growth forecasts (`rev_est_2y`, `eps_est_2y`) are **fractions**: `0.05` = 5%
- margins (`ebitda_margin`, `roic`) are **percent**: `36.6` = 36.6%
- a missing input fails the sieve; it is never treated as neutral

## Licence

MIT. See `LICENSE`.
