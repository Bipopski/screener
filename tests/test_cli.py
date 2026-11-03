"""The CLI: two verbs, no network, output that a reader can check."""

from __future__ import annotations

from pathlib import Path

import pytest

from screener.cli import main

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "demo"
SCREEN = ROOT / "examples" / "screen" / "inputs.csv"


def test_backtest_prints_a_result(capsys):
    assert main(["backtest", "--data", str(DEMO)]) == 0
    out = capsys.readouterr().out
    assert "invested 60,000 zł" in out
    assert "TWR" in out and "max drawdown" in out
    assert "closing book:" in out


def test_backtest_accepts_a_different_book_size(capsys):
    assert main(["backtest", "--data", str(DEMO), "--n", "3", "--contrib", "500"]) == 0
    out = capsys.readouterr().out
    assert "invested 30,000 zł" in out


def test_missing_dataset_fails_loudly():
    with pytest.raises(SystemExit):
        main(["backtest", "--data", "/nonexistent/path"])


def test_screen_reports_who_passes_and_why_not(capsys):
    assert main(["screen", str(SCREEN)]) == 0
    out = capsys.readouterr().out
    assert "12 companies · 6 pass the sieve · 6 rejected" in out
    assert "COVERAGE" in out and "mniej niż 3 analityków" in out
    assert "ranked by growth score" in out


def test_screen_ranks_the_best_name_first(capsys):
    main(["screen", str(SCREEN), "--top", "3"])
    out = capsys.readouterr().out
    ranked = out.split("ranked by growth score:")[1].strip().splitlines()
    assert ranked[0].strip().startswith("DELTA")
