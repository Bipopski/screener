"""Which venues the universe is built from.

A market is a country code used for currency and reporting; the exchanges are the
listings actually queried. Keeping them apart matters: the same issuer can be
listed on several exchanges, and the screener must not treat two listings as two
companies (see ``dedupe.py``).
"""

from __future__ import annotations

#: market code -> Yahoo exchange codes
EXCHANGES: dict[str, list[str]] = {
    "US": ["NMS", "NYQ", "ASE"],
    "UK": ["LSE"],
    "DE": ["GER"],
    "FR": ["PAR", "ENX"],
    "NL": ["AMS"],
    "CH": ["EBS"],
    "SE": ["STO"],
    "IT": ["MIL"],
    "ES": ["MCE"],
    "JP": ["JPX"],
    "TW": ["TAI"],
    "CN": ["SHH", "SHZ"],
    "PL": ["WSE"],
    "KR": ["KSC"],
    "CA": ["TOR", "VAN"],
    "DK": ["CPH"],
    "NO": ["OSL"],
    "BE": ["BRU"],
    "AU": ["ASX"],
    "FI": ["HEL"],
}

#: market code -> listing currency (a market cap quoted locally must be converted)
CURRENCY: dict[str, str] = {
    "US": "USD", "CA": "CAD", "UK": "GBP", "DE": "EUR", "FR": "EUR", "NL": "EUR",
    "ES": "EUR", "IT": "EUR", "BE": "EUR", "FI": "EUR", "CH": "CHF", "SE": "SEK",
    "NO": "NOK", "DK": "DKK", "PL": "PLN", "JP": "JPY", "TW": "TWD", "CN": "CNY",
    "KR": "KRW", "AU": "AUD",
}

#: markets whose domestic names are usually cross-listings of US companies —
#: screening them by region returns the same mega-caps again, not local coverage.
CROSS_LISTED = {"DE", "CA", "BR", "MX"}
