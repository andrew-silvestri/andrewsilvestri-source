"""The heat page's checks (R4, 2026-10-23). Each one was seen to fail with its break.

    python test_heat.py                 # every check; exit 0 only if all pass
    python test_heat.py --break NAME    # put one fault back; that check fails and the run exits 1

  breakeven  model.breakeven_Pe at the old page's example ($3.50/MMBtu gas, defaults) against the
             same arithmetic written out here: (gas fuel + gas capital + gas O&M - electric capital
             - electric O&M) * eta_e / 293.07 = 1.5294 c/kWh. --break breakeven swaps the two
             efficiencies, the classic slip in a spark-gap formula.
  convert    one month by hand from the raw EIA files: $/Mcf divided by (Btu/cf / 1000), with the
             year's heat content. --break convert treats a Mcf as an MMBtu.
  last       the payload's last month is the last month BOTH EIA files have. Electricity runs a
             month ahead of gas, and pairing the newer electricity month with no gas price is
             the fault. --break last takes the last electricity month instead.
  never      no month below the break-even, recomputed from the raw files here (not read from
             the payload, trap 20). --break never sets the gas efficiency to 0.5, which a slip in
             a default would do; months then fall below and the check must see them.
  flexible   2025's central-case hours and savings recomputed from ERCOT's file and EIA's gas
             prices. --break flexible adds the delivery charge to the gas side instead.
  key        EIA_API_KEY appears in no stored file (fetched.json, data/raw). --break key copies a
             raw file with the key written into it into a temp dir and scans that.
  claims     update_page.claims() refuses a payload that contradicts the page. --break claims
             puts one month below the break-even.
"""
import copy
import datetime as dt
import glob
import json
import os
import shutil
import sys
import tempfile
from dataclasses import asdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import model as H  # noqa: E402
import build_heat as B  # noqa: E402

BRK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
P = json.load(open(os.path.join(HERE, "outputs", "payload.json"), encoding="utf-8"))
results = []


def say(ok, name, msg):
    results.append((ok, name))
    print(("  ok    " if ok else "  FAIL  ") + name + ": " + msg)


def t_breakeven():
    p = H.Params(**{**asdict(H.Params()), "P_g": 3.50})
    eg, ee = (p.eta_e, p.eta_g) if BRK == "breakeven" else (p.eta_g, p.eta_e)
    crf = p.r * (1 + p.r) ** p.life / ((1 + p.r) ** p.life - 1)
    gas = 3.50 / eg + (p.capex_g * crf + p.capex_g * p.fom_g) / p.hours
    elec_nonfuel = (p.capex_e * crf + p.capex_e * p.fom_e) / p.hours
    want = (gas - elec_nonfuel) * ee / 293.07 * 100
    got = H.breakeven_Pe(p) * 100
    say(abs(want - got) < 1e-9 and abs(got - 1.5294) < 5e-5, "breakeven", f"by hand {want:.4f} c, model {got:.4f} c")


def t_convert():
    gs = {r["period"]: float(r["value"]) for r in B.rows("eia_tx_ind_gas_price.json") if r["value"] not in (None, "")}
    hc = {int(r["period"]): float(r["value"]) for r in B.rows("eia_tx_gas_heat_content.json")}
    m = P["months"][-1]
    y = int(m["period"][:4])
    hy = min(hc, key=lambda k: abs(k - y))
    want = gs[m["period"]] / (1.0 if BRK == "convert" else hc[hy] / 1000)
    say(abs(want - m["gas_usd_mmbtu"]) < 1e-9, "convert", f"{m['period']}: ${gs[m['period']]}/Mcf at {hc[hy]:.0f} Btu/cf = ${want:.4f}/MMBtu; payload ${m['gas_usd_mmbtu']:.4f}")


def t_last():
    el = {r["period"] for r in B.rows("eia_tx_ind_elec_price.json") if r["price"] not in (None, "")}
    gs = {r["period"] for r in B.rows("eia_tx_ind_gas_price.json") if r["value"] not in (None, "")}
    want = max(el) if BRK == "last" else max(el & gs)
    say(P["summary"]["last"] == want, "last", f"payload {P['summary']['last']}; both files end {max(el & gs)} (electricity alone {max(el)})")


def t_never():
    months, _, _, _ = B.monthly()
    p0 = H.Params()
    below = 0
    for m in months:
        q = H.Params(**{**asdict(p0), "P_g": m["gas_usd_mmbtu"], **({"eta_g": 0.5} if BRK == "never" else {})})
        if m["elec_c_kwh"] < H.breakeven_Pe(q) * 100:
            below += 1
    say(below == 0 and P["summary"]["below"] == 0, "never", f"{below} of {len(months)} months below the break-even, recomputed")


def t_flexible():
    row = [y for y in P["flexible"]["years"] if y["year"] == 2025][0]["by_adder"]["central"]
    d = B.E.year_prices(os.path.join(B.ERCOT_RAW, "RTM_2025.zip"), B.ERCOT_CACHE)
    p = B.E.hourly(d, "HB_HUBAVG")
    gas = {m["period"]: m["gas_usd_mmbtu"] for m in P["months"]}
    mon = []
    for k in range(d["days"]):
        dd = dt.date(2025, 1, 1) + dt.timedelta(k)
        mon += ["2025-%02d" % dd.month] * B.E._hours_in(dd)
    p0 = H.Params()
    g = np.array([gas[m] for m in mon]) * (p0.eta_e * 1000 / H.KWH_PER_MMBTU) / p0.eta_g
    a = B.SRC["delivery_adders_usd_mwh"]["central"]
    if BRK == "flexible":
        win = p < g + a
        sav = float((g + a - p)[win].sum() / 1000)
    else:
        win = p + a < g
        sav = float((g - p - a)[win].sum() / 1000)
    say(int(win.sum()) == row["hours"] and abs(sav - row["savings_kw_yr"]) < 1e-9, "flexible",
        f"2025 central: {int(win.sum())} h, ${sav:.4f}/kW; payload {row['hours']} h, ${row['savings_kw_yr']:.4f}")


def t_key():
    import envfile
    k = envfile.get("EIA_API_KEY")
    if not k:
        say(False, "key", "EIA_API_KEY is not set, so the scan cannot run")
        return
    files = [os.path.join(HERE, "data", "fetched.json")] + glob.glob(os.path.join(HERE, "data", "raw", "*.json"))
    tmp = None
    if BRK == "key":
        tmp = tempfile.mkdtemp()
        f = os.path.join(tmp, "leak.json")
        shutil.copy(files[1], f)
        open(f, "a", encoding="utf-8").write(json.dumps({"api_key": k}))
        files.append(f)
    hits = [os.path.basename(f) for f in files if k in open(f, encoding="utf-8").read()]
    if tmp:
        shutil.rmtree(tmp)
    say(not hits, "key", f"{len(files)} stored files scanned for EIA_API_KEY's value: {len(hits)} hit(s)")


def t_claims():
    import update_page as U
    Q = copy.deepcopy(P)
    if BRK == "claims":
        Q["summary"]["below"] = 1
    try:
        U.claims(U.facts(Q), Q)
        say(True, "claims", "the payload agrees with every statement the page makes")
    except SystemExit as e:
        say(False, "claims", str(e).splitlines()[-1].strip())


def main():
    t_breakeven(); t_convert(); t_last(); t_never(); t_flexible(); t_key(); t_claims()
    fails = [n for ok, n in results if not ok]
    if BRK:
        print(f"break {BRK}: {'caught' if BRK in fails else 'NOT caught - this run exits 0, the check is blind'}")
    print(f"{len(results) - len(fails)}/{len(results)} checks pass")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
