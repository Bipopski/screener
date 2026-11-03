"""Quality sieve — all eight conditions must hold, no partial credit.

Units, because they are easy to get wrong and the sieve silently rewards the
mistake:

* ``rev_est_2y``, ``eps_est_2y`` — **fractions** (0.05 = 5% growth).
* ``ebitda_margin``, ``roic`` — **percent** (15.0 = 15%), as reported by the
  data source. A margin passed as 0.366 fails the sieve even though the company
  is profitable; ``test_quality.py`` pins this down.
* ``eps_ttm``, ``cfo``, ``price`` — absolute values in the reporting currency.

A missing input is a failure, never a neutral value: a company whose margins
cannot be sourced has not proven anything.
"""

from __future__ import annotations

from .config import MIN_ANALYSTS

#: (key, threshold, human label, is_percent)
TRELA_FILTERS: list[tuple[str, float, str, bool]] = [
    ("rev_est_2y", 0.05, "prognoza wzrostu przychodów 2Y > 5%", True),
    ("eps_est_2y", 0.05, "prognoza wzrostu EPS 2Y > 5%", True),
    ("eps_ttm", 0.10, "EPS TTM > 0,10", False),
    ("ebitda_margin", 15.0, "marża EBITDA > 15%", True),
    ("roic", 10.0, "ROIC > 10%", True),
    ("cfo", 0.0, "gotówka operacyjna > 0", False),
    ("price", 10.0, "cena akcji > 10", False),
]


def quality_score(row: dict) -> tuple[float, list[str]]:
    """Return ``(100.0, [])`` when every condition holds, else ``(0.0, reasons)``.

    The analyst gate is checked first and short-circuits: a company without a
    usable long-term forecast is disqualified before the other inputs matter,
    and the reason says so explicitly (coverage, not quality).
    """
    if (row.get("ltg_analysts") or 0) < MIN_ANALYSTS:
        return 0.0, ["LTG: mniej niż 3 analityków — dyskwalifikacja"]

    failed: list[str] = []
    for key, threshold, label, _is_percent in TRELA_FILTERS:
        value = row.get(key)
        if value is None:
            failed.append(f"{label}: brak danych")
        elif value <= threshold:
            failed.append(label)
    if failed:
        return 0.0, failed
    return 100.0, []
