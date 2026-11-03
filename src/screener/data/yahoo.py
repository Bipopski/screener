"""Yahoo adapter — prices only, optional dependency.

Install with ``pip install -e ".[yahoo]"``. It fetches month-end closes and
converts them to one currency; it does **not** provide the analyst forecasts the
score needs (long-term growth, two-year EPS revisions), so a run built on Yahoo
alone can exercise the engine but cannot produce a ranking. Use a forecast source
for `signals.csv` — that constraint is the method, not the adapter.

Prices are public market data; check the provider's terms before redistributing
anything you download.
"""

from __future__ import annotations

from pathlib import Path


def fetch_prices(tickers: list[str], start: str, end: str,
                 fx: dict[str, float] | None = None) -> dict[str, dict[str, float]]:
    """Return ``{month: {ticker: price}}`` with month-end closes.

    ``fx`` maps a currency code to a multiplier into the portfolio currency
    (e.g. ``{"USD": 3.95, "EUR": 4.42}``); without it prices stay in their own
    currency and any comparison across markets is wrong.
    """
    try:
        import yfinance as yf  # type: ignore[import-not-found]
    except ImportError as exc:                       # pragma: no cover - optional
        raise ImportError('the Yahoo adapter needs yfinance: pip install -e ".[yahoo]"') from exc

    fx = fx or {}
    prices: dict[str, dict[str, float]] = {}
    for ticker in tickers:
        frame = yf.Ticker(ticker).history(start=start, end=end, interval="1mo")
        if frame.empty:
            continue
        currency = (yf.Ticker(ticker).info or {}).get("currency", "")
        rate = fx.get(currency, 1.0)
        for stamp, close in frame["Close"].dropna().items():
            month = stamp.strftime("%Y-%m")
            prices.setdefault(month, {})[ticker] = float(close) * rate
    return prices


def write_prices(prices: dict[str, dict[str, float]], path: str | Path) -> None:
    """Write the adapter output in the schema ``screener.data.csv`` reads."""
    import csv

    with Path(path).open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ticker", "month", "price_pln"])
        for month in sorted(prices):
            for ticker, price in sorted(prices[month].items()):
                writer.writerow([ticker, month, round(price, 4)])
