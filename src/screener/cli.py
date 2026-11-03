"""Command line: run the backtest on a dataset, or screen a table of companies.

Two verbs, no network:

``screener backtest``  — walk a price/signal dataset month by month (defaults to
                         the bundled demo) and print the result;
``screener screen``    — apply the sieve and the score to a table of raw metrics
                         and print who passes, who does not and why.

Anything that needs a live feed belongs in a data adapter, not here.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from .account import Costs
from .backtest import run_backtest
from .data.csv import load_demo
from .quality import quality_score
from .scoring import score_all

DEMO = Path(__file__).resolve().parents[2] / "examples" / "demo"


def _demo_dir(given: str | None) -> Path:
    directory = Path(given) if given else DEMO
    if not (directory / "prices.csv").exists():
        raise SystemExit(f"no dataset at {directory} (expected prices.csv and signals.csv)")
    return directory


def cmd_backtest(args: argparse.Namespace) -> int:
    signals, prices = load_demo(_demo_dir(args.data))
    costs = Costs(spread_bps=args.spread_bps, fx_fee=args.fx_fee,
                  tax_rate=args.tax_rate, wrapper=args.wrapper)
    result = run_backtest(signals, prices, set(), costs=costs, contrib=args.contrib,
                          n=args.n, lam=args.lam, skip_smallest=not args.no_skip)
    months = len(result.months)
    print(f"dataset: {Path(args.data or DEMO)} · {months} months · "
          f"{len(prices[result.months[0]])} instruments")
    print(f"invested {result.invested:,.0f} zł → final {result.final:,.0f} zł")
    print(f"TWR {result.twr:.1%} · IRR {result.irr:.1%} · max drawdown "
          f"{result.max_drawdown:.1%} · trades {result.trades} · tax {result.tax_paid:,.0f} zł")
    print("closing book: " + ", ".join(result.positions_hist[-1][1]))
    return 0


def cmd_screen(args: argparse.Namespace) -> int:
    path = Path(args.table)
    if not path.exists():
        raise SystemExit(f"no such file: {path}")
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))

    passed, failed = [], []
    for row in rows:
        values = {}
        for key in ("rev_est_2y", "eps_est_2y", "eps_ttm", "ebitda_margin", "roic", "cfo",
                    "price", "ltg_analysts"):
            raw = row.get(key)
            values[key] = float(raw) if raw not in (None, "") else None
        score, reasons = quality_score(values)
        record = {"ticker": row["ticker"], "score": score, "reasons": reasons,
                  "eps_lt_growth": _num(row.get("eps_lt_growth")),
                  "eps2y_rev3": _num(row.get("eps2y_rev3")),
                  "ebitda_margin": (values["ebitda_margin"] / 100
                                    if values["ebitda_margin"] is not None else None)}
        (passed if score >= 70 else failed).append(record)

    print(f"{len(rows)} companies · {len(passed)} pass the sieve · {len(failed)} rejected")
    if failed:
        print("\nrejected:")
        for record in failed:
            print(f"  {record['ticker']:10} {'; '.join(record['reasons'][:2])}")

    if not passed:
        return 0
    scores, bounds = score_all({r["ticker"]: {k: r[k] for k in
                                              ("eps_lt_growth", "eps2y_rev3", "ebitda_margin")}
                                for r in passed})
    print("\nranked by growth score:")
    for record in sorted(passed, key=lambda r: -(scores.get(r["ticker"]) or 0))[:args.top]:
        value = scores.get(record["ticker"])
        shown = f"{value:5.1f}" if value is not None else "  —  "
        print(f"  {record['ticker']:10}{shown}")
    print(f"\nscale: 3rd–97th percentile of the passed pool "
          f"(ltg {bounds['eps_lt_growth'][0]:.3f}…{bounds['eps_lt_growth'][1]:.3f})")
    return 0


def _num(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="screener", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    back = sub.add_parser("backtest", help="run the monthly backtest on a dataset")
    back.add_argument("--data", help="directory with prices.csv and signals.csv")
    back.add_argument("--contrib", type=float, default=1000.0)
    back.add_argument("--n", type=int, default=6)
    back.add_argument("--lam", type=float, default=1.5)
    back.add_argument("--wrapper", choices=["ike", "regular", "none"], default="ike")
    back.add_argument("--spread-bps", type=float, default=10.0)
    back.add_argument("--fx-fee", type=float, default=0.005)
    back.add_argument("--tax-rate", type=float, default=0.19)
    back.add_argument("--no-skip", action="store_true",
                      help="fund every target every month instead of dropping the smallest slice")
    back.set_defaults(func=cmd_backtest)

    screen = sub.add_parser("screen", help="apply the sieve and score to a table")
    screen.add_argument("table", help="CSV with raw quality inputs and the three model metrics")
    screen.add_argument("--top", type=int, default=10)
    screen.set_defaults(func=cmd_screen)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
