# screener

A rules-based equity screener and portfolio backtester: a hard quality sieve, a
growth score computed on the surviving pool, a six-position book sized by each
name's own valuation history, and two exit rules.

The point of the repo is the **method and its accounting**, not a stock tip. The
backtest is built to be auditable: portfolio values are converted to one
currency, contributions and P&L reconcile to the złoty every month, the
money-weighted return is checked against a date-based XIRR, and the reference run
is reported with the trades it actually made.

## What this is not

- **Not investment advice**, and not a promise of returns. The reference run
  covers 48 months of a single regime (an AI-led bull market); the same rules
  would have behaved differently in another one.
- **Not a screener for everything.** The universe is capped by market
  capitalisation and requires analyst forecasts; companies without coverage are
  deliberately excluded, even when they are good businesses.
- **Not a trading system.** The tested design holds positions for a median of
  nine months and sells 11 times in four years. Rotation, stops and market-timing
  overlays were tested and made results worse — `docs/decisions.md` has the
  numbers.

## Status

Working, tested end to end on a synthetic dataset, CI on 3.11 and 3.12.

| module | what it does |
|---|---|
| `screener.quality` | the eight-condition sieve, no partial credit |
| `screener.scoring` | growth score 0–100 on dynamic percentile bounds |
| `screener.portfolio` | valuation weights, contribution split, deficit allocation |
| `screener.account` | ledger: cash, positions, units, contributions + P&L = value |
| `screener.backtest` | monthly loop: decision → execution → valuation → accounting |
| `screener.xirr` | XIRR on real dates and time-weighted return |
| `screener.config` | every threshold and weight, in one place |
| `screener.data` | adapters: CSV/demo (bundled), Yahoo (optional, prices only) |
| `screener.cli` | `backtest` and `screen` |

## Quickstart

```bash
uv venv && uv pip install -e ".[dev]"
pytest
screener backtest                 # 25 synthetic tickers × 60 months
screener screen examples/screen/inputs.csv
```

`screener backtest` prints invested capital, TWR, IRR, drawdown, trade count and
the closing book. `screener screen` applies the sieve to a table of raw inputs
and prints who was rejected and on which condition — the part that matters, since
most rejections are missing coverage rather than bad businesses.

From Python:

```python
from screener import Costs, load_demo, run_backtest

signals, prices = load_demo("examples/demo")
result = run_backtest(signals, prices, costs=Costs(wrapper="ike"),
                      contrib=1000.0, n=6)

print(f"{result.final:,.0f} zł from {result.invested:,.0f} zł invested")
print(f"TWR {result.twr:.1%} · IRR {result.irr:.1%} · max DD {result.max_drawdown:.1%}")
```

The accounting identity is checked inside the loop every month — a run that loses
a fee somewhere raises instead of returning a plausible number.

## Reference result

On a private 48-month panel (2022-11 → 2026-10): **100 731 zł from 48 000 zł
contributed**, TWR 37,0% a year, 11 sells, max drawdown −13,8%. The engine in
this repo reproduces it to the złoty with the execution rule off and within 0,8%
with it on. Numbers, benchmarks and the limits of the sample: `docs/results.md`.

## Units, because they bite

- growth forecasts (`rev_est_2y`, `eps_est_2y`) are **fractions**: `0.05` = 5%
- margins (`ebitda_margin`, `roic`) are **percent**: `36.6` = 36.6%
- a missing input fails the sieve; it is never treated as neutral

## Docs

- `docs/decisions.md` — everything that was tested and rejected, with numbers
- `docs/results.md` — the reference run, its benchmarks, and what it does not say
- `examples/demo/README.md` — the dataset schema

## Licence

MIT. See `LICENSE`.
