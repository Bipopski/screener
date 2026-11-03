"""Universe construction: listings from venues → one row per issuer above a cap floor.

The floor is expressed in USD and converted to the venue's currency **before** it
is applied — an unconverted floor is a no-op filter outside the dollar zone, and
the junk it lets through is then deleted downstream, which looks like a working
pipeline.

The provider is injected so the whole builder can be tested without a network
and so the paid/free choice stays outside the method.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .dedupe import DEFAULT_ALIAS, dedupe
from .markets import CURRENCY, EXCHANGES


@dataclass(frozen=True)
class Listing:
    ticker: str
    market: str
    name: str
    currency: str
    cap_usd: float
    turnover_usd: float = 0.0
    access: str = ""


Provider = Callable[[str, float, str], Iterable[Listing]]


def min_cap_local(min_cap_usd: float, currency: str, fx: dict[str, float]) -> float:
    """Convert a USD floor into the listing currency.

    ``fx`` maps a currency to its **USD value** (``{"PLN": 0.25}``). A missing
    rate raises: silently using 1.0 turns the floor into a no-op.
    """
    if currency == "USD":
        return min_cap_usd
    rate = fx.get(currency)
    if not rate:
        raise KeyError(f"no USD rate for {currency}; pass fx={{'{currency}': <usd per unit>}}")
    return min_cap_usd / rate


def build(markets: Iterable[str] | None = None, *, min_cap_usd: float = 9e9,
          provider: Provider, fx: dict[str, float], alias: dict[str, str] | None = None,
          ) -> list[Listing]:
    """Return one listing per issuer, largest first."""
    markets = list(markets or EXCHANGES)
    rows: list[dict] = []
    for market in markets:
        currency = CURRENCY[market]
        floor = min_cap_local(min_cap_usd, currency, fx)
        for listing in provider(market, floor, currency):
            rows.append({
                "ticker": listing.ticker, "market": market, "name": listing.name,
                "currency": listing.currency, "cap_usd": listing.cap_usd,
                "turnover_usd": listing.turnover_usd, "access": listing.access,
            })
    return sorted((Listing(**row) for row in dedupe(rows, alias or DEFAULT_ALIAS)),
                  key=lambda item: -item.cap_usd)


def write_csv(listings: list[Listing], path: str) -> None:
    """Write the universe in the schema the screen step reads."""
    import csv

    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ticker", "market", "name", "currency", "cap_usd", "turnover_usd",
                         "access"])
        for item in listings:
            writer.writerow([item.ticker, item.market, item.name, item.currency,
                             round(item.cap_usd), round(item.turnover_usd), item.access])
