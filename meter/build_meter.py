"""Build outputs/payload.json: every number the meter page and figures print.

Runs the model (model.py) on:
  - one default receipt meter alone, input by input (figure 1);
  - the default system in three cases of the one sharing no open source fixes,
    the discharge coefficient's (figure 3, the headline numbers):
      fC0   every meter's C error independent;
      fC1   fully shared among meters of one tap type and beta band, which here
            puts receipts (beta 0.50) and deliveries (0.55) in one class;
      fC1r  fully shared among receipts and, separately, among deliveries;
  - N receipt meters into one delivery meter, N = 1 to 100 (figure 2);
and reads the context figures from the fetched public data: Henry Hub
(EIA RNGWHHD), EIA Natural Gas Annual Table A1, PHMSA distribution reports.

Every Monte Carlo result is run to JCGM 101 7.9.4's stopping rule
(model.adaptive) from a fixed seed, so the payload is reproducible byte for
byte and the page generator's drift check can hold it.

Run:  python build_meter.py      (about ten minutes)
"""
import datetime as dt
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import xlrd

import model as M
from aga8lib import AGA8
from netfetch import verified

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs" / "payload.json"
SEED = 20261018
M3_PER_MCF = 28.316846592            # 1000 ft3 in m3 (exact: 0.3048^3 x 1000)
J_PER_MMBTU = 1.05505585262e9        # International Table Btu: 1055.05585262 J


CASES = [("fC0", 0.0, "beta"), ("fC1", 1.0, "beta"), ("fC1r", 1.0, "role")]


def rng(tag):
    return np.random.default_rng([SEED, sum(map(ord, tag))])


def henry_hub():
    path, row = verified("RNGWHHDm.xls")
    s = xlrd.open_workbook(str(path)).sheet_by_name("Data 1")
    vals = [(xlrd.xldate_as_datetime(s.cell(r, 0).value, 0).date(), float(s.cell(r, 1).value))
            for r in range(s.nrows) if isinstance(s.cell(r, 0).value, float) and s.cell(r, 1).value != ""]
    last = vals[-12:]
    prices = [v for _, v in last]
    return {"series": "RNGWHHD", "fetched": row["fetched"],
            "first": last[0][0].strftime("%Y-%m"), "last": last[-1][0].strftime("%Y-%m"),
            "median": float(np.median(prices)), "mean": float(np.mean(prices)),
            "max": max(prices), "max_month": max(last, key=lambda t: t[1])[0].strftime("%Y-%m")}


def eia_a1():
    path, row = verified("eia_nga_table_a01.pdf")
    txt = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True,
                         check=True).stdout
    year = re.search(r"by state, (\d{4})", txt).group(1)
    m = re.search(r"^Total\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)", txt, re.M)
    losses, uaf, cons, pct = (float(g.replace(",", "")) for g in m.groups())
    return {"year": int(year), "losses_mmcf": losses, "uaf_mmcf": uaf, "consumption_mmcf": cons,
            "printed_pct": pct, "computed_pct": 100 * (losses + uaf) / cons, "fetched": row["fetched"]}


def phmsa():
    import read_phmsa
    rows = [r for r in read_phmsa.load() if r.get("COMMODITY") == "Natural Gas"]
    year = max(int(r["REPORT_YEAR"]) for r in rows)
    v = np.array([float(r["PERCENT_UNACC_GAS"]) for r in rows if int(r["REPORT_YEAR"]) == year])
    return {"year": year, "reports": int(v.size), "median": float(np.median(v)),
            "negative": int((v < 0).sum()), "zero": int((v == 0).sum()),
            "p10": float(np.percentile(v, 10)), "p90": float(np.percentile(v, 90))}


def per_day(states, x):
    """True throughput of the receipts: MMcf/d at base and MMBtu/d."""
    n = sum(s.qm / (s.MW * 1e-3) for s in states if s.m.role == "R")      # mol/s
    vb = n * states[0].Zb * M.R_GERG * M.T_BASE / (M.P_BASE * 1e3)       # m3/s at base
    e = n * states[0].HN * 1e3                                             # W
    return vb * 86400 / M3_PER_MCF / 1e3, e * 86400 / J_PER_MMBTU


def run(states, x, comps, keys, tag, intervals=4):
    r = rng(tag)
    t = dt.datetime.now()
    res = M.adaptive(lambda K: M.simulate(states, x, comps, K, r, intervals=intervals), keys)
    k = keys[0]
    print(f"  {tag:24s} {res[k]['batches']:4d} batches  u {res[k]['u']:.3e}  "
          f"{(dt.datetime.now() - t).total_seconds():6.1f} s", flush=True)
    return res


def strip(res):
    return {k: {s: v[s] for s in ("mean", "u", "low", "high", "delta", "trials", "batches")}
            for k, v in res.items()}


def one_meter(aga):
    """One receipt meter (R1's design) on its own, into a delivery meter that is not measured
    with error: only the receipt's own error is in rec_v. Input by input, f irrelevant for one
    meter, one interval (like-for-like with a single-meter budget)."""
    ms = [m for m in M.default_meters() if m.name == "R1"]
    ms.append(M.Meter("D", "D", D=0.1023, beta=0.5, p1=800 * M.PSI, T1=M.T_BASE, span_dp=50.0, share=1.0))
    st, x = M.build_system(ms, aga=aga)
    out = {}
    for g in M.GROUPS:
        comps = [c for c in M.default_comps() if c.group == g]
        out[g] = strip(run(st, x, comps, ["rec_v"], "one:" + g, intervals=1))["rec_v"]
    out["all"] = strip(run(st, x, M.default_comps(), ["rec_v"], "one:all", intervals=1))["rec_v"]
    return out, {"D_mm": ms[0].D * 1e3, "beta": ms[0].beta, "p1_psia": ms[0].p1 / M.PSI,
                 "dp_kpa": ms[0].dp, "span_kpa": ms[0].span_dp}


def system(aga):
    states, x = M.build_system(M.default_meters(), aga=aga)
    mmcfd, mmbtud = per_day(states, x)
    out = {}
    for key, fC, cls in CASES:
        comps = M.default_comps({"C": fC}, c_class=cls)
        res = strip(run(states, x, comps, ["imb_v", "imb_e", "rec_v"], key))
        contrib = {}
        for g in M.GROUPS:
            cg = [c for c in comps if c.group == g]
            contrib[g] = strip(run(states, x, cg, ["imb_e"], key + ":" + g))["imb_e"]
        r = rng(key + ":hist")
        y = M.simulate(states, x, comps, 200000, r)["imb_e"] * 100
        edges = np.linspace(-1.0, 1.0, 81)
        h, _ = np.histogram(y, bins=edges)
        out[key] = {"results": res, "by_input": contrib,
                    "hist": {"edges_pct": edges.tolist(), "counts": h.tolist(),
                             "outside": int(((y < edges[0]) | (y > edges[-1])).sum()), "n": int(y.size)}}
    table = [{"name": s.m.name, "role": s.m.role, "D_mm": s.m.D * 1e3, "beta": s.m.beta,
              "p1_psia": s.m.p1 / M.PSI, "T1_F": (s.m.T1 - 273.15) * 1.8 + 32,
              "dp_kpa": s.m.dp, "span_kpa": s.m.span_dp, "Z1": s.Z1, "Re": s.Re,
              "mmcfd": s.qm / (s.MW * 1e-3) * s.Zb * M.R_GERG * M.T_BASE / (M.P_BASE * 1e3)
              * 86400 / M3_PER_MCF / 1e3} for s in states]
    return out, table, mmcfd, mmbtud, states


def sweep(aga):
    """N receipt meters (R1..R4's designs, cycled) into one delivery meter sized for them."""
    Ns = [1, 2, 4, 8, 16, 32, 64, 100]
    base = [m for m in M.default_meters() if m.role == "R"]
    out = {"N": Ns}
    for key, fC, cls in CASES:
        rows = []
        for n in Ns:
            ms = [M.Meter(f"R{i + 1}", "R", **{k: getattr(base[i % 4], k) for k in
                                               ("D", "beta", "p1", "T1", "span_dp", "dp")}) for i in range(n)]
            ms.append(M.Meter("D", "D", D=0.1023 * math.sqrt(n) * 1.1, beta=0.55, p1=400 * M.PSI,
                              T1=M.T_BASE, span_dp=50.0, share=1.0))
            st, x = M.build_system(ms, aga=aga)
            res = strip(run(st, x, M.default_comps({"C": fC}, c_class=cls), ["rec_v", "imb_v"], f"sweep:{key}:{n}"))
            rows.append({"N": n, "u_total": res["rec_v"]["u"], "u_imb": res["imb_v"]["u"],
                         "delta_total": res["rec_v"]["delta"], "delta_imb": res["imb_v"]["delta"]})
        out[key] = rows
    return out


def main():
    aga = AGA8()
    t0 = dt.datetime.now()
    hh = henry_hub()
    a1 = eia_a1()
    ph = phmsa()
    single, single_design = one_meter(aga)
    sysres, table, mmcfd, mmbtud, states = system(aga)
    sw = sweep(aga)
    price = hh["median"]
    money = {}
    for key, v in sysres.items():
        e = v["results"]["imb_e"]
        money[key] = {"u_mmbtud": e["u"] * mmbtud,
                      "u_usd_yr": e["u"] * mmbtud * M.DAYS * price,
                      "half95_usd_yr": (e["high"] - e["low"]) / 2 * mmbtud * M.DAYS * price}
    payload = {
        "about": "meter/build_meter.py; every figure on site/meter.html comes from here",
        "seed": SEED,
        "gas": "Gulf Coast",
        "base": {"p_psia": 14.73, "T_F": 60.0},
        "intervals": 4,
        "throughput": {"mmcfd": mmcfd, "mmbtud": mmbtud},
        "price": hh,
        "eia_a1": a1,
        "phmsa": ph,
        "single": single,
        "single_design": single_design,
        "system": sysres,
        "money": money,
        "meters": table,
        "sweep": sw,
        "defaults": {"cd_u_pct": float(M.cd_u(0.5)) * 100, "Z_u_ref_pct": M.Z_U_REF * 100,
                     "z_ref": M.z_ref(aga), "mu": M.MU, "comp_u_pct": M.COMP_U},
    }
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"wrote {OUT} in {(dt.datetime.now() - t0).seconds} s")
    for key, _, _ in CASES:
        r = sysres[key]["results"]
        print(f"  {key}: u(I) volume {r['imb_v']['u']:.4%}, energy {r['imb_e']['u']:.4%} "
              f"({r['imb_e']['batches']} batches); u(total) {r['rec_v']['u']:.4%}; "
              f"${money[key]['u_usd_yr']:,.0f}/yr at ${price:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
