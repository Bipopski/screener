# Reference run

These are the numbers the method was validated on. They come from a **private
panel** built from a paid forecast source — the repository ships the engine, not
the data, so you cannot reproduce them from a clone. What you *can* reproduce is
the mechanics: `screener backtest` walks the bundled synthetic demo end to end.

## Parameters

| parameter | value |
|---|---|
| panel | 2022-11 → 2026-10 (48 months), 20 exchanges, ~3 400 companies with forecasts |
| entry | quality sieve (8 conditions, ≥3 analysts on the long-term forecast), top 6 by growth score |
| sizing | `w = max(0.05, 1 − 1.5 × (P/E 2Y percentile − 50)/50)`, applied to each contribution |
| rebalancing | none — no ranking swaps, no trimming |
| exits | quality loss, or a 3-month EPS-2Y cut in the worst decile of the gated pool with no rebound |
| contributions | 1 000 zł per month |
| costs | 10 bp spread per side, 0.5% conversion per side on foreign positions (IKE wrapper) |
| currency | everything converted to PLN at the monthly rate |

## Result

| measure | value |
|---|---|
| final value | 100 731 zł from 48 000 zł contributed |
| TWR (time-weighted) | **37,0%** a year |
| IRR (money-weighted) | 40,5% |
| max drawdown | −13,8% |
| trades | 240 buys, **11 sells** over 48 months |
| tax | ≈3 400 zł, i.e. 3,9% of the final value |

Benchmarks over the same period, same currency:

| | per year | Sharpe | max drawdown |
|---|---|---|---|
| **strategy** | **37,0%** | 1,62 | −13,8% |
| S&P 500 (TR) | 14,7% | 1,31 | −14,3% |
| Nasdaq 100 | 20,3% | 1,24 | −15,0% |
| S&P 500 IT | 23,9% | 1,15 | −17,0% |

Closing book: TSMC, Kioxia, Broadcom, Hilton, Meta, Micron.

## Parity

The public engine reproduces the reference run on the same panel:

| variant | final | TWR | trades | book |
|---|---|---|---|---|
| reference implementation | 100 731 zł | 37,0% | 240 buys + 11 sells | as above |
| this engine, skip-smallest off | 100 518 zł | 37,0% | 288 buys + 11 sells | identical every month |
| this engine, skip-smallest on | 99 912 zł | 37,0% | 240 buys + 11 sells | identical every month |

With the execution rule off the two agree to the złoty. With it on they differ by
819 zł (0,8%) — see `docs/decisions.md` for why that is the rule's own noise
rather than a defect.

## What these numbers are not

1. **One regime.** 48 months of an AI-led bull market. Nothing here says how the
   rules behave when semiconductors leave their cycle — that regime is absent
   from the sample.
2. **A coverage-gated universe.** Companies without analyst forecasts are
   excluded by design, so the result says nothing about small caps or about
   markets where the forecast series is thin (Korea and Poland contribute zero
   names for exactly this reason).
3. **A survivorship-free panel.** Delisted companies are not in the data.
4. **Not a forecast.** The drawdown figure belongs to a book that held software,
   industrials and consumer names at various points. A book concentrated in one
   value chain will draw down deeper.
5. **No second independent period.** Thresholds and weights were chosen on this
   panel; the block tests (`docs/decisions.md`) check stability inside it, not
   out of sample.
