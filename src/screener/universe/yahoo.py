"""Yahoo provider for the universe builder — optional dependency.

Install with ``pip install -e ".[yahoo]"``. One screener query per exchange,
filtered by market cap in the **local** currency (the floor is converted before
the call), then normalised into :class:`screener.universe.build.Listing`.

Yahoo's quotes carry no broker reachability and no analyst coverage, so this
provider answers "what exists and how big is it", nothing more. Coverage is what
the sieve needs and it has to come from a forecast source.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from .build import Listing
from .markets import EXCHANGES


def provider(fx: dict[str, float], *, size: int = 250) -> Callable:
    """Return a provider bound to a set of USD rates."""

    def fetch(market: str, min_cap_local: float, currency: str) -> Iterable[Listing]:
        try:
            import yfinance as yf  # type: ignore[import-not-found]
        except ImportError as exc:                    # pragma: no cover - optional
            raise ImportError('the Yahoo provider needs yfinance: pip install -e ".[yahoo]"') from exc

        rate = fx.get(currency)
        if rate is None:
            raise KeyError(f"no USD rate for {currency}")

        for exchange in EXCHANGES[market]:
            query = yf.EquityQuery("and", [
                yf.EquityQuery("gt", ["intradaymarketcap", min_cap_local]),
                yf.EquityQuery("eq", ["exchange", exchange]),
            ])
            result = yf.screen(query, size=size,
                               sortField="intradaymarketcap", sortAsc=False) or {}
            for quote in result.get("quotes", []):
                # the *long* name is what identifies the issuer: Yahoo lists
                # foreign shares on local venues as certificates ("AAPL C.XGLO
                # PLN"), whose short name says nothing and whose market cap is
                # the parent's. Keying on the long name lets the issuer dedupe
                # collapse them into the primary listing.
                name = quote.get("longName") or quote.get("shortName") or quote["symbol"]
                if quote.get("quoteType") != "EQUITY":
                    continue
                cap_local = quote.get("marketCap") or 0.0
                volume = quote.get("regularMarketVolume") or 0.0
                price = quote.get("regularMarketPrice") or 0.0
                yield Listing(
                    ticker=quote["symbol"],
                    market=market,
                    name=name,
                    currency=currency,
                    cap_usd=cap_local * rate,
                    turnover_usd=volume * price * rate,
                )

    return fetch
