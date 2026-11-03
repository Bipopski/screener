"""Universe: one row per issuer, and a floor that is actually applied."""

from __future__ import annotations

import pytest

from screener.universe import Listing, build, dedupe, issuer_of, min_cap_local, name_key


def test_name_key_strips_legal_and_class_tokens():
    assert name_key("Canadian Pacific Kansas City Limited") == "canadian pacific kansas city"
    assert name_key("Broadcom Inc.") == "broadcom"
    assert name_key("Bombardier Inc., Cl. A") == "bombardier"


def test_similar_names_do_not_collide():
    """A short prefix key folded three different Canadian companies into one."""
    keys = {name_key(n) for n in (
        "Canadian Pacific Kansas City Limited",
        "Canadian Natural Resources Limited",
        "Canadian Imperial Bank of Commerce",
    )}
    assert len(keys) == 3


def test_short_names_are_never_merged():
    assert name_key("EQT AB") != name_key("EQT Corporation")


def test_alias_merges_a_dual_listing():
    assert issuer_of("TSM", "Taiwan Semiconductor") == issuer_of("2330.TW", "TSMC")


def test_dedupe_keeps_one_row_per_issuer():
    rows = [
        {"ticker": "TSM", "name": "Taiwan Semiconductor", "cap_usd": 2e12, "turnover_usd": 9e9},
        {"ticker": "2330.TW", "name": "TSMC", "cap_usd": 2e12, "turnover_usd": 1e10},
        {"ticker": "AAPL", "name": "Apple Inc.", "cap_usd": 3e12, "turnover_usd": 5e9},
    ]
    kept = {row["ticker"] for row in dedupe(rows)}
    assert kept == {"2330.TW", "AAPL"}          # higher turnover wins the pair


def test_floor_is_converted_and_a_missing_rate_raises():
    assert min_cap_local(9e9, "USD", {}) == 9e9
    assert min_cap_local(9e9, "PLN", {"PLN": 0.25}) == pytest.approx(36e9)
    with pytest.raises(KeyError):
        min_cap_local(9e9, "PLN", {})


def test_build_dedupes_and_sorts_by_size():
    def fake_provider(market, floor, currency):
        assert currency == "USD"
        return [
            Listing("AAA", market, "Alpha Industries Corp", "USD", 50e9),
            Listing("BBB", market, "Beta Holdings Inc.", "USD", 200e9),
            Listing("AAA.US", market, "Alpha Industries Corporation", "USD", 40e9),
        ]

    result = build(["US"], min_cap_usd=1e9, provider=fake_provider, fx={"USD": 1.0})
    assert [item.ticker for item in result] == ["BBB", "AAA"]


def test_short_base_names_are_left_apart_on_purpose():
    """A duplicate row is visible; a wrong merge is not. The guard errs visible."""
    rows = [{"ticker": "AAA", "name": "Alpha Corp", "cap_usd": 50e9},
            {"ticker": "AAA.US", "name": "Alpha Corporation", "cap_usd": 40e9}]
    assert len(dedupe(rows)) == 2


def test_build_applies_the_floor_per_currency():
    seen = {}

    def fake_provider(market, floor, currency):
        seen[currency] = floor
        return []

    build(["US", "PL"], min_cap_usd=9e9, provider=fake_provider,
          fx={"USD": 1.0, "PLN": 0.25})
    assert seen["USD"] == 9e9
    assert seen["PLN"] == pytest.approx(36e9, rel=1e-9)
