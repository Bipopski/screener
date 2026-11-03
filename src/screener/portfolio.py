"""Position sizing: weights from valuation history, cash from deficits.

Two rules, both tested:

* **Weight** — a cheaper name (low percentile of its own forward P/E history)
  gets more capital: ``w = max(floor, 1 - lam * (pct - 50) / 50)``. Valuation
  never selects a name, only sizes it.
* **Cash** — money is split **proportionally to each target's deficit**, not in
  list order. Walking the list first-come-first-served lets topping up existing
  holdings absorb the whole balance, so a new candidate at the end of the list
  never gets funded and the book silently runs below N.
"""

from __future__ import annotations

from .config import MIN_WEIGHT, VALUATION_LAMBDA


def val_weight(percentile: float | None, lam: float = VALUATION_LAMBDA,
               floor: float = MIN_WEIGHT) -> float:
    """Weight multiplier for one position, given its valuation percentile."""
    pct = 50.0 if percentile is None else percentile
    return max(floor, 1.0 - lam * ((pct - 50.0) / 50.0))


def target_weights(tickers, percentiles: dict, lam: float = VALUATION_LAMBDA,
                   floor: float = MIN_WEIGHT) -> dict[str, float]:
    """Normalised weights that sum to 1 (empty dict when there is nothing to hold)."""
    raw = {t: val_weight(percentiles.get(t), lam, floor) for t in tickers}
    total = sum(raw.values())
    if total <= 0:
        return {}
    return {t: w / total for t, w in raw.items()}


def plan_contribution(cash: float, target: list[str], percentiles: dict,
                      held: set[str] | None = None, lam: float = VALUATION_LAMBDA,
                      floor: float = MIN_WEIGHT, skip_smallest: bool = True) -> dict[str, float]:
    """Split this month's cash across the target list by valuation weight.

    This is the mechanism the published results use: every contribution is
    divided by ``w = max(floor, 1 - lam * (pct - 50) / 50)``, so cheaper names
    receive more of *new money*. The book is never rebalanced to target weights —
    positions drift with performance, and a position that has run gets no
    trimming (and no top-up beyond its share of the inflow).

    A name entering the book for the first time takes an equal share of the
    contribution before the valuation split, so a new position is never funded
    with a few złoty while older ones absorb the deposit.

    ``skip_smallest`` drops the smallest slice and renormalises the rest — an
    execution rule that keeps the last position buyable at any broker.
    """
    if cash <= 0 or not target:
        return {}
    held = held or set()
    plan: dict[str, float] = {}
    cash_left = cash

    new_names = [t for t in target if t not in held]
    if new_names:
        share = cash / len(target)
        for ticker in new_names:
            take = min(share, cash_left)
            if take <= 0:
                break
            plan[ticker] = plan.get(ticker, 0.0) + take
            cash_left -= take

    if cash_left > 0:
        weights = target_weights(target, percentiles, lam=lam, floor=floor)
        # the reference implementation inserted the split in descending weight
        # order; the order decides which slice is dropped when two are tied
        for ticker, weight in sorted(weights.items(), key=lambda kv: -kv[1]):
            plan[ticker] = plan.get(ticker, 0.0) + cash_left * weight

    if skip_smallest and len(plan) > 1:
        smallest = min(plan, key=plan.get)
        budget = sum(plan.values())
        plan.pop(smallest)
        rest = sum(plan.values())
        if rest > 0:
            plan = {t: amount * budget / rest for t, amount in plan.items()}
    return {t: amount for t, amount in plan.items() if amount > 0}


def allocate(cash: float, target_values: dict[str, float], held_values: dict[str, float],
             skip_smallest: bool = True) -> dict[str, float]:
    """Split ``cash`` across the positions that are below their target value.

    Returns gross amounts (before costs), proportional to each deficit and capped
    by it. With ``skip_smallest`` the smallest slice is dropped and the rest is
    renormalised, which keeps the last position from being bought for a few
    złoty — the rule is an execution detail, neutral for the result.
    """
    if cash <= 0:
        return {}
    deficits = {t: target_values[t] - held_values.get(t, 0.0) for t in target_values}
    deficits = {t: d for t, d in deficits.items() if d > 0}
    total = sum(deficits.values())
    if total <= 0:
        return {}

    plan = {t: cash * d / total for t, d in deficits.items()}
    plan = {t: min(amount, deficits[t]) for t, amount in plan.items() if amount > 0}

    if skip_smallest and len(plan) > 1:
        smallest = min(plan, key=plan.get)
        budget = sum(plan.values())
        plan.pop(smallest)
        rest = sum(plan.values())
        if rest > 0:
            plan = {t: amount * budget / rest for t, amount in plan.items()}
    return plan
