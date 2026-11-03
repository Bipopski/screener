"""The ledger: cash, positions, units and the accounting identity.

Three numbers must always agree, to the grosz: **contributions + P&L = value**.
The cost basis of a position is the gross amount taken out of cash (fees
included), so a sale's P&L already carries the spread, the conversion and the
tax. When a contribution is added, units are bought at the *current* unit value;
otherwise deposits raise the value curve and the drawdown collapses to almost
nothing — a smooth winner with no losing month is the symptom, not the strategy.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Costs:
    """Trading costs and tax. ``fx_fee`` applies per side on foreign positions."""

    spread_bps: float = 10.0
    fx_fee: float = 0.005
    tax_rate: float = 0.19
    wrapper: str = "ike"          # "ike" (tax-free, conversion fee) | "regular" | "none"

    @property
    def spread(self) -> float:
        return self.spread_bps / 10_000.0


@dataclass
class Position:
    shares: float = 0.0
    cost: float = 0.0             # gross cash spent, fees included


@dataclass
class Account:
    costs: Costs = field(default_factory=Costs)
    cash: float = 0.0
    units: float = 0.0
    unit_value: float = 1.0
    positions: dict[str, Position] = field(default_factory=dict)
    realised: dict[str, float] = field(default_factory=dict)
    contributions: float = 0.0
    tax_paid: float = 0.0
    trades: int = 0

    # --- flows ---------------------------------------------------------------

    def contribute(self, amount: float) -> None:
        if amount <= 0:
            return
        self.cash += amount
        self.contributions += amount
        self.units += amount / self.unit_value if self.unit_value else 0.0

    # --- trades --------------------------------------------------------------

    def buy(self, ticker: str, gross: float, price: float, foreign: bool) -> bool:
        """Spend ``gross`` of cash on ``ticker``. Returns False when not fillable."""
        if gross <= 0 or price <= 0 or gross > self.cash + 1e-9:
            return False
        net = gross * (1.0 - self.costs.spread)
        if foreign and self.costs.wrapper == "ike":
            net *= 1.0 - self.costs.fx_fee
        position = self.positions.get(ticker, Position())
        position.shares += net / price
        position.cost += gross
        self.positions[ticker] = position
        self.cash -= gross
        self.trades += 1
        return True

    def sell(self, ticker: str, price: float, foreign: bool) -> float:
        """Close ``ticker``; returns the cash received (after costs and tax)."""
        position = self.positions.get(ticker)
        if position is None or price <= 0:
            return 0.0
        proceeds = position.shares * price * (1.0 - self.costs.spread)
        if foreign and self.costs.wrapper == "ike":
            proceeds *= 1.0 - self.costs.fx_fee
        gain = proceeds - position.cost
        if self.costs.wrapper == "regular" and gain > 0:
            tax = self.costs.tax_rate * gain
            proceeds -= tax
            self.tax_paid += tax
        self.cash += proceeds
        self.realised[ticker] = self.realised.get(ticker, 0.0) + (proceeds - position.cost)
        self.trades += 1
        del self.positions[ticker]
        return proceeds

    # --- valuation -----------------------------------------------------------

    def market_value(self, prices: dict[str, float]) -> float:
        """Cash plus positions marked at ``prices``; a missing price uses cost."""
        total = self.cash
        for ticker, position in self.positions.items():
            price = prices.get(ticker)
            total += position.shares * price if price else position.cost
        return total

    def mark(self, prices: dict[str, float]) -> float:
        """Mark to market, update the unit value, return the book value."""
        value = self.market_value(prices)
        if self.units > 0:
            self.unit_value = value / self.units
        return value

    # --- audit ---------------------------------------------------------------

    def pnl(self, prices: dict[str, float]) -> float:
        """Realised plus unrealised P&L, net of costs and tax."""
        unrealised = 0.0
        for ticker, position in self.positions.items():
            price = prices.get(ticker)
            if price:
                unrealised += position.shares * price - position.cost
        return sum(self.realised.values()) + unrealised

    def check(self, prices: dict[str, float], tolerance: float = 0.01) -> None:
        """Raise when contributions + P&L does not equal the book value."""
        value = self.market_value(prices)
        expected = self.contributions + self.pnl(prices)
        if abs(value - expected) > tolerance:
            raise AssertionError(
                f"accounting broken: value {value:.2f} != contributions + P&L {expected:.2f}")
