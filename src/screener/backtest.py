"""Monthly backtest: decision → execution → valuation → accounting → metrics.

The loop is deliberately thin. Each step is a named function so the accounting
can be tested without a market and the decision can be tested without money:

* :func:`make_decision` — who should be held this month (exits, then free slots).
* :func:`execute`        — turn the decision and the cash into buy orders.
* :func:`value`          — mark to market.
* :func:`account`        — units, contributions, the identity check.
* :func:`metrics`        — TWR, IRR, drawdown, trade count.

Only the tested configuration is implemented: N positions, no ranking swaps,
valuation as a sizing input, two exit rules. Every parameter that was rejected
in research (stops, regime filters, buffers) is absent on purpose — see
``docs/decisions.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .account import Account, Costs
from .config import EXIT_PERCENTILE, PORTFOLIO_SIZE, VALUATION_LAMBDA
from .portfolio import allocate, target_weights
from .xirr import dates_of, twr, xirr


@dataclass(frozen=True)
class Signal:
    """What the model knows about one company in one month."""

    score: float | None = None
    quality: float | None = None
    rev3: float | None = None
    rev1: float | None = None
    val_pct: float | None = None
    eligible: bool = True


@dataclass
class Result:
    months: list[str]
    unit_hist: list[tuple[str, float, float, int]]
    final: float
    invested: float
    contrib: float
    tax_paid: float
    trades: int
    positions_hist: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)

    @property
    def twr(self) -> float | None:
        return twr({"unit_hist": [(m, u, v, k) for m, u, v, k in self.unit_hist]})

    @property
    def irr(self) -> float | None:
        """Money-weighted return; the closing value sits on the last contribution."""
        months = self.months
        if not months:
            return None
        flows = [(d, -self.contrib) for d in dates_of(months)]
        flows[-1] = (flows[-1][0], flows[-1][1] + self.final)
        return xirr(flows)

    @property
    def max_drawdown(self) -> float:
        peak, worst = 0.0, 0.0
        for _m, unit, _v, _k in self.unit_hist:
            peak = max(peak, unit)
            worst = min(worst, unit / peak - 1.0 if peak else 0.0)
        return worst


def _decile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(percentile / 100.0 * len(ordered))))
    return ordered[index]


def make_decision(signals: dict[str, Signal], held, *,
                  n: int = PORTFOLIO_SIZE, q_min: float = 70.0,
                  exit_percentile: float = EXIT_PERCENTILE,
                  traded_this_month: set[str] | None = None) -> tuple[list[str], list[str]]:
    """Return ``(target, exits)`` for one month.

    Exits run first so the target is built from what is left plus free slots —
    building the target from the ranking alone lets a held name outside the top
    ``n`` occupy a slot without being counted, and the book grows past ``n``.
    """
    traded = traded_this_month or set()
    pool = {t: s for t, s in signals.items()
            if s.eligible and s.score is not None and (s.quality or 0) >= q_min}
    eps_cut = _decile([s.rev3 for s in pool.values() if s.rev3 is not None], exit_percentile)

    exits: list[str] = []
    for ticker in held:
        if ticker in traded:
            continue
        signal = signals.get(ticker)
        if signal is None:
            continue                                  # no data is not a sell signal
        if (signal.quality or 0) < q_min:
            exits.append(ticker)
            continue
        if (eps_cut is not None and signal.rev3 is not None and signal.rev3 <= eps_cut
                and (signal.rev1 is None or signal.rev1 <= 0)):
            exits.append(ticker)

    remaining = [t for t in held if t not in exits]
    free_slots = max(0, n - len(remaining))
    # a name sold this month is not a candidate this month: re-buying it on the
    # same signal is pure churn (the old engine allowed it, the tests pin it)
    sold = set(exits)
    ranked = sorted((t for t in pool if t not in remaining and t not in sold),
                    key=lambda t: -pool[t].score)
    target = remaining + ranked[:free_slots]
    return target, exits


def execute(account: Account, plan: dict[str, float], prices: dict[str, float],
            foreign: set[str]) -> int:
    """Place the buy orders; returns how many filled."""
    filled = 0
    for ticker, gross in sorted(plan.items(), key=lambda kv: -kv[1]):
        price = prices.get(ticker)
        if price and account.buy(ticker, gross, price, ticker in foreign):
            filled += 1
    return filled


def value(account: Account, prices: dict[str, float]) -> float:
    return account.mark(prices)


def account(account: Account, prices: dict[str, float]) -> None:
    """Run the identity check; a mismatch means a cost or tax left the books."""
    account.check(prices)


def metrics(result: Result) -> dict:
    return {"twr": result.twr, "irr": result.irr, "max_drawdown": result.max_drawdown,
            "final": result.final, "invested": result.invested,
            "trades": result.trades, "tax_paid": result.tax_paid}


def run_backtest(signals: dict[str, dict[str, Signal]], prices: dict[str, dict[str, float]],
                 foreign: set[str] | None = None, *, costs: Costs | None = None,
                 contrib: float = 1000.0, n: int = PORTFOLIO_SIZE,
                 lam: float = VALUATION_LAMBDA, q_min: float = 70.0,
                 exit_percentile: float = EXIT_PERCENTILE,
                 skip_smallest: bool = True) -> Result:
    """Run the strategy month by month and return the book's history."""
    foreign = foreign or set()
    acc = Account(costs=costs or Costs())
    unit_hist: list[tuple[str, float, float, int]] = []
    positions_hist: list[tuple[str, tuple[str, ...]]] = []
    months = list(signals)

    for month in months:
        month_signals = signals[month]
        month_prices = prices.get(month, {})
        acc.contribute(contrib)

        target, exits = make_decision(month_signals, acc.positions.keys(),
                                      n=n, q_min=q_min, exit_percentile=exit_percentile)
        for ticker in exits:
            acc.sell(ticker, month_prices.get(ticker, 0.0), ticker in foreign)

        held_values = {t: p.shares * month_prices[t]
                       for t, p in acc.positions.items() if month_prices.get(t)}
        total = acc.market_value(month_prices)
        weights = target_weights(target, {t: (month_signals.get(t).val_pct
                                              if month_signals.get(t) else None)
                                          for t in target}, lam=lam)
        target_values = {t: total * w for t, w in weights.items()}
        plan = allocate(acc.cash, target_values, held_values, skip_smallest=skip_smallest)
        execute(acc, plan, month_prices, foreign)

        book = value(acc, month_prices)
        account(acc, month_prices)
        unit_hist.append((month, acc.unit_value, book, len(acc.positions)))
        positions_hist.append((month, tuple(sorted(acc.positions))))

    return Result(months=months, unit_hist=unit_hist,
                  final=unit_hist[-1][2] if unit_hist else 0.0,
                  invested=acc.contributions, contrib=contrib,
                  tax_paid=acc.tax_paid, trades=acc.trades,
                  positions_hist=positions_hist)
