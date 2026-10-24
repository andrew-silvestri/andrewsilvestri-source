"""The storage page's checks (R4, 2026-10-23). Each one was seen to fail with its break.

    python test_storage.py                 # every check; exit 0 only if all pass
    python test_storage.py --break NAME    # put one fault back; that check must fail, exit 1

Checks, and the fault each break puts back:
  simultaneous  model.optimize never charges and discharges in the same hour. Until 2026-10-21
                it carried `c + d <= p_max`, which did not forbid it: with twelve hours of one
                720-hour block forced to -$250/MWh the 2h case charged 0.538 MW and discharged
                0.462 MW at once in ten of them. --break simultaneous runs that formulation.
  square        the LP against a price pattern with a closed-form answer: 12 h at $10 then
                12 h at $100, 60 days, 4 MWh from empty; net per day
                100*E*eta - 10*E/eta - 2*0.5*(E*eta + E/eta). --break square halves the RTE.
  dst           the reader's step count follows Central time: every year's file has 23 hours
                on the spring change and 25 on the fall one, and a reader that assumed 24 a day
                would refuse 2025 (8,760 steps either way in a full year, but not in a part
                year: 2026's file to 17 Oct has 6,959 hours, not 6,960 - the first fault the
                reader met). --break dst makes every day 24 hours; 2026's DAM must be refused.
  filled        RTM 2013 lacks exactly one 15-minute interval (3 Nov 2013, hour 2, interval 1);
                the reader fills it and lists it. --break filled sets MAX_FILLED to 0: refused.
  ice           ERCOT DAM HB_NORTH on-peak against EIA's ICE ERCOT North trades, 2015: under
                3% over the year, every month within 8%, daily r >= 0.95. --break ice reads the
                DAM one day late (r falls to about 0.79). It cannot tell HB_WEST from HB_NORTH
                in 2015 (tried: passes), so the settlement point is pinned by name in `point`.
  point         the payload trades HB_HUBAVG and the ICE check reads HB_NORTH, by name.
  payload       RTM 2023 and 2025, and DAM 2021, recomputed here from the price files with
                model.optimize: net per kW, days for half, best-10-days share, on the
                earnings basis (days that made money). --break payload computes the shares on
                the NET basis instead, which is the historical fault: a share of the net
                passed 100% (the best 1% of 2021's DAM hours were "137%" of the net).
  claims        update_page.claims() refuses a payload that contradicts the page's words.
                --break claims makes 2025 a scarcity year (days for half 10); it must stop.
"""
import copy
import datetime as dt
import json
import os
import sys

import numpy as np
import pulp

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ercot_prices as E  # noqa: E402
import model as M  # noqa: E402

RAW = os.path.join(HERE, "data", "raw")
CACHE = os.path.join(HERE, "data", "cache")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
BRK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
results = []


def say(ok, name, msg):
    results.append((ok, name))
    print(("  ok    " if ok else "  FAIL  ") + name + ": " + msg)


def old_optimize(prices, duration_h=2, p_max=1.0, rte=0.86, c_deg=2.0):
    """The pre-2026-10-21 formulation, one block, for --break simultaneous."""
    eta = np.sqrt(rte); E_ = duration_h * p_max; T = range(len(prices))
    prob = pulp.LpProblem("arb", pulp.LpMaximize)
    c = pulp.LpVariable.dicts("c", T, 0, p_max)
    d = pulp.LpVariable.dicts("d", T, 0, p_max)
    x = pulp.LpVariable.dicts("soc", range(len(prices) + 1), 0, E_)
    prob += pulp.lpSum(prices[t] * (d[t] - c[t]) - c_deg * 0.5 * (d[t] + c[t]) for t in T)
    prob += x[0] == 0.5 * E_
    for t in T:
        prob += x[t + 1] == x[t] + eta * c[t] - d[t] / eta
        prob += c[t] + d[t] <= p_max
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    return dict(ch=np.array([c[t].value() for t in T]), dis=np.array([d[t].value() for t in T]))


def t_simultaneous():
    prices, _ = M.load_prices()
    p = prices[24 * 180: 24 * 210].copy()
    p[250:262] = -250.0
    r = old_optimize(p) if BRK == "simultaneous" else M.optimize(p, 2)
    both = int(np.sum((r["ch"] > 1e-6) & (r["dis"] > 1e-6)))
    say(both == 0, "simultaneous", f"{both} hour(s) charging and discharging at once")


def t_square():
    eta, En, days = np.sqrt(0.86), 4.0, 60
    want = days * (100 * En * eta - 10 * En / eta - 2 * 0.5 * (En * eta + En / eta))
    p = np.tile(np.r_[np.full(12, 10.0), np.full(12, 100.0)], days)
    got = M.optimize(p, 4, rte=0.43 if BRK == "square" else 0.86, soc0_frac=0.0)["revenue"]
    say(abs(got - want) < 1e-6 * want, "square", f"closed form {want:.4f}, LP {got:.4f}")


def t_dst():
    real = E._hours_in
    if BRK == "dst":
        E._hours_in = lambda day: 24
    try:
        refused = None
        try:
            E.parse(os.path.join(RAW, "DAM_2026.zip"))
        except RuntimeError as e:
            refused = str(e)
        spring = real(dt.date(2026, 3, 8)), real(dt.date(2026, 11, 1))
        say(refused is None and spring == (23, 25), "dst",
            f"2026 DAM read {'(refused: ' + refused[-60:] + ')' if refused else 'whole'}; 8 Mar and 1 Nov 2026 have {spring} hours")
    finally:
        E._hours_in = real


def t_filled():
    real = E.MAX_FILLED
    if BRK == "filled":
        E.MAX_FILLED = 0
    try:
        try:
            d = E.parse(os.path.join(RAW, "RTM_2013.zip"))
            f = list(d["filled"])
            say([str(x) for x in f] == ["2013-11-03 h2 i1"], "filled", f"filled {[str(x) for x in f]}")
        except RuntimeError as e:
            say(False, "filled", "refused: " + str(e)[-70:])
    finally:
        E.MAX_FILLED = real


def t_ice():
    import build_storage as B
    real = E.hourly
    if BRK == "ice":
        E.hourly = lambda d, pt: np.roll(real(d, pt), 24)
    try:
        r = B.ice_check()
    finally:
        E.hourly = real
    ok = r["annual_pct"] < 3 and r["month_pct_max"] < 8 and r["r"] >= 0.95
    say(ok, "ice", f"{r['days']} days, annual {r['annual_pct']:.2f}%, worst month {r['month_pct_max']:.1f}%, r {r['r']:.3f}")


def t_point(P):
    import inspect
    import build_storage as B
    src = inspect.getsource(B.ice_check)
    say(P["point"] == "HB_HUBAVG" and '"HB_NORTH"' in src, "point", f"payload trades {P['point']}; ICE reads HB_NORTH")


def shares(cash, days, basis):
    if basis == "net":
        dsrt = np.sort(days)[::-1]
        den = days.sum()
        return int(np.searchsorted(np.cumsum(dsrt), den / 2) + 1), float(dsrt[:10].sum() / den)
    dpos = np.sort(days[days > 0])[::-1]
    return int(np.searchsorted(np.cumsum(dpos), dpos.sum() / 2) + 1), float(dpos[:10].sum() / dpos.sum())


def t_payload(P):
    import build_storage as B
    bad = []
    for mkt, y in (("RTM", 2023), ("RTM", 2025), ("DAM", 2021)):
        d = E.year_prices(os.path.join(RAW, "%s_%d.zip" % (mkt, y)), CACHE)
        p = E.hourly(d, "HB_HUBAVG")
        r = M.optimize(p, 4)
        cash = p * (r["dis"] - r["ch"]) - r["c_deg"] * 0.5 * (r["dis"] + r["ch"])
        days = B.daily(cash, dt.date(y, 1, 1), d["days"])
        half, best10 = shares(cash, days, "net" if BRK == "payload" else "earnings")
        got = P[mkt.lower()][str(y)]["dur"]["4"]
        if not (abs(r["revenue"] / 1000 - got["net_per_kw"]) < 1e-6 and half == got["days_for_half"]
                and abs(best10 - got["best10_days_share"]) < 1e-9 and 0 < best10 <= 1):
            bad.append(f"{mkt} {y}: net {r['revenue'] / 1000:.3f} vs {got['net_per_kw']:.3f}, half {half} vs "
                       f"{got['days_for_half']}, best10 {best10:.3f} vs {got['best10_days_share']:.3f}")
    say(not bad, "payload", "RTM 2023, RTM 2025, DAM 2021 recomputed from the price files" + (": " + "; ".join(bad) if bad else ""))


def t_claims(P):
    import update_page as U
    I = json.load(open(os.path.join(HERE, "data", "imm.json"), encoding="utf-8"))
    Q = copy.deepcopy(P)
    if BRK == "claims":
        Q["rtm"]["2025"]["dur"]["4"]["days_for_half"] = 10
    try:
        U.claims(U.facts(Q, I), Q, I)
        say(True, "claims", "the payload agrees with every comparison the page makes")
    except SystemExit as e:
        say(False, "claims", str(e).splitlines()[-1].strip())


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    t_simultaneous(); t_square(); t_dst(); t_filled(); t_ice(); t_point(P); t_payload(P); t_claims(P)
    fails = [n for ok, n in results if not ok]
    if BRK:
        print(f"break {BRK}: {'caught' if BRK in fails else 'NOT caught - this run exits 0, the check is blind'}")
    print(f"{len(results) - len(fails)}/{len(results)} checks pass")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
