"""One company, one row — and two companies that share a prefix stay two.

Deduplication by a short name prefix is the classic quiet failure: a seven-letter
key folded Canadian Pacific, Canadian Natural and Canadian Imperial into one
issuer, and Samsung's eleven entities into another, so dozens of companies were
never ranked and nothing reported an error. The rules here:

* strip legal and class tokens (``Inc``, ``NV``, ``Cl. A``, ``ADR``…) from the
  end of the name, then compare the **whole** remaining name;
* refuse to merge names shorter than six characters — ``EQT AB`` is not
  ``EQT Corporation``;
* apply an explicit alias map for known dual listings (ADR/ordinary pairs), which
  is the only safe way to merge names that genuinely differ.
"""

from __future__ import annotations

import re

from .markets import EXCHANGES

LEGAL_TOKENS = {
    "inc", "incorporated", "corp", "corporation", "ltd", "limited", "plc", "ag", "nv",
    "sa", "ab", "oyj", "asa", "spa", "se", "co", "company", "holdings", "holding",
    "group", "ord", "ordinary", "registered", "shares", "ser", "class", "cl", "a", "b",
    "c", "the", "new", "york", "adr", "spons", "sponsored", "gdr", "reg", "s",
}

#: listings of the same issuer -> the canonical listing
DEFAULT_ALIAS: dict[str, str] = {
    "TSM": "2330.TW", "2330.TW": "2330.TW",
    "UMC": "2303.TW", "2303.TW": "2303.TW",
    "ASML": "ASML.AS", "ASML.AS": "ASML.AS",
    "SHOP": "SHOP.TO", "SHOP.TO": "SHOP.TO",
    "AZN.L": "AZN", "AZN.ST": "AZN", "AZN": "AZN",
}


def name_key(name: str) -> str:
    """Normalise a company name to its issuer key."""
    tokens = re.findall(r"[a-z0-9]+", (name or "").lower())
    while tokens and tokens[-1] in LEGAL_TOKENS:
        tokens.pop()
    key = " ".join(tokens)
    if len(key) < 6:
        return f"~{(name or '').lower().strip()}"
    return key


def issuer_of(ticker: str, name: str, alias: dict[str, str] | None = None) -> str:
    """Canonical issuer key for a listing."""
    alias = alias or DEFAULT_ALIAS
    if ticker in alias:
        return alias[ticker]
    return name_key(name)


def pick_survivor(rows: list[dict]) -> dict:
    """Choose the listing to keep for one issuer.

    Prefer the venue the retail broker actually offers, then turnover, then market
    cap — a local turnover figure favours weak currencies, so it is only a
    tie-break after reachability.
    """
    def score(row: dict) -> tuple:
        reachable = 1 if str(row.get("access", "")).startswith("XTB") else 0
        return (reachable, row.get("turnover_usd") or 0.0, row.get("cap_usd") or 0.0)

    return max(rows, key=score)


def dedupe(rows: list[dict], alias: dict[str, str] | None = None) -> list[dict]:
    """Collapse listings of one issuer to a single row, keeping the survivor."""
    groups: dict[str, list[dict]] = {}
    for row in rows:
        key = issuer_of(row["ticker"], row.get("name", ""), alias)
        groups.setdefault(key, []).append(row)
    return [pick_survivor(group) for group in groups.values()]


def market_of(ticker: str) -> str | None:
    """Market code from a ticker suffix, for reporting only."""
    if "." not in ticker:
        return "US"
    suffix = ticker.rsplit(".", 1)[1].upper()
    for market, codes in EXCHANGES.items():
        if suffix in codes:
            return market
    return None
