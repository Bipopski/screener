"""Parytet silnika: stary backtest.py vs nowy screener.backtest na tym samym panelu.

Cel: sprawdzić, czy nowa pętla odtwarza wynik referencyjny (37,2% TWR, 100 731 zł).
Uruchamiane ręcznie, ścieżki prywatne — plik poza repo.
"""
import sys

sys.path.insert(0, "/home/hermes/workspace/inwestycje/backtest")
sys.path.insert(0, "/home/hermes/workspace/screener/src")

import backtest as old                     # noqa: E402
import signals as sg                       # noqa: E402
from screener import Costs, Signal, run_backtest   # noqa: E402

START, END = "2022-11", "2026-10"
prepared = old.prepare(START, END)
sigs, px, px_ff, cur, mkt, sec = prepared
months = sg.months(START, END)

kw = dict(old.STRATEGY)
kw.update(dedup=False, alt_rule=False)
ref = old.run(prepared=prepared, **kw)
print(f"STARY : final {ref['final']:,.0f} zł · IRR {ref['irr']:.2%} · "
      f"TWR {(ref['unit_hist'][-1][1]) ** (12 / (len(ref['unit_hist']) - 1)) - 1:.2%} · "
      f"transakcje {ref['trades']} (kup {ref['n_buys']}, sprzedaże {ref['n_sells']})")

new_sig, new_px = {}, {}
for m in months:
    pxs = {t: px_ff[(t, m)] for (tt, mm) in px_ff if mm == m and (t := tt)}
    new_px[m] = pxs
    row = {}
    for t, x in sigs[m].items():
        sector = (sec.get(t) or (None, None))[0]
        q = x.get("q")
        row[t] = Signal(
            score=x.get("g"),
            quality=q,
            rev3=(x.get("m") or {}).get("eps2y_rev3"),
            rev1=(x.get("m") or {}).get("eps2y_rev1"),
            val_pct=x.get("v_pe2y"),
            eligible=(sector != "Healthcare" and x.get("v") is not None and t in pxs),
        )
    new_sig[m] = row

foreign = {t for t in cur if cur.get(t) != "PLN"}
res = run_backtest(new_sig, new_px, foreign,
                   costs=Costs(spread_bps=10.0, fx_fee=0.005, wrapper="ike"),
                   contrib=1000.0, n=6, lam=1.5, q_min=70.0, exit_percentile=10,
                   allocation="prop", skip_smallest=True)

print(f"NOWY  : final {res.final:,.0f} zł · IRR {res.irr:.2%} · TWR {res.twr:.2%} · "
      f"transakcje {res.trades} · pozycji na koniec {len(res.positions_hist[-1][1])}")
print(f"delta : final {res.final - ref['final']:+,.0f} zł · "
      f"TWR {(res.twr - ((ref['unit_hist'][-1][1]) ** (12 / (len(ref['unit_hist']) - 1)) - 1)) * 100:+.2f} pp")
print(f"stary skład: {sorted(ref['final_pos'])}")
print(f"nowy  skład: {sorted(res.positions_hist[-1][1])}")
