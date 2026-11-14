"""Run the LC-1 LCA: scenarios, Monte Carlo, tornado, tables, figures.

python run.py [--n 10000] [--seed 20261107]   -> results/
"""
import argparse
import csv
import json
import os

import numpy as np

import lca
import params as PR

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")

SOLE_IN_T1 = {"P.eva_mould_kwh_kg": 0.0, "P.vulc_kwh_pair": 0.0, "P.etpu_mould_kwh_kg": 0.0, "P.tpu_inj_kwh_kg": 0.0}
SCENARIOS = {
    # name: (kwargs for lca.evaluate, input overrides)
    "design_only": (dict(upper_lives=1, clean_lc1=False, life_mult=1.0), {}),
    "lc1": (dict(upper_lives=1, clean_lc1=True, life_mult=1.0), {}),
    "lc1_resole": (dict(upper_lives=2, clean_lc1=True, life_mult=1.0), {}),
    "lc1_resole_informed": (dict(upper_lives=2, clean_lc1=True, life_mult=1.15), {}),
    "baseline_clean_power": (dict(upper_lives=1, clean_lc1=True, clean_base=True, life_mult=1.0), {}),
    "lc1_tpu_stress": (dict(upper_lives=1, clean_lc1=True, life_mult=1.0, tpu_override=PR.P["tpu_factor_stress"][0]), {}),  # D-106
    "lc1_cff_5050": (dict(upper_lives=1, clean_lc1=True, life_mult=1.0, cff=True), {}),
    "lc1_sole_making_in_t1": (dict(upper_lives=1, clean_lc1=True, life_mult=1.0), SOLE_IN_T1),
    "lc1_made_in_china": (dict(upper_lives=1, clean_lc1=True, life_mult=1.0, country="E.GRID_CN"), {}),
    "lc1_made_in_indonesia": (dict(upper_lives=1, clean_lc1=True, life_mult=1.0, country="E.GRID_ID"), {}),
}
LABELS = {
    "design_only": "LC-1 design, every supplier on the Viet Nam grid",
    "lc1": "LC-1 as specified: design + renewable electricity at final assembly and the sole moulder",
    "lc1_resole": "LC-1, upper kept for a second sole unit",
    "lc1_resole_informed": "LC-1, second sole unit, and soles run 15 % further (eTPU fatigue, Aimar 2024)",
    "baseline_clean_power": "Reference: the BASELINE shoe with renewable electricity at assembly and the sole maker, against the baseline on grid power",
    "lc1_tpu_stress": f"Stress case: TPU at {PR.P['tpu_factor_stress'][0]} kg CO2e/kg (build-up from the highest open raw-material figures), both shoes",
    "lc1_cff_5050": "Allocation sensitivity: recycled content carries half the virgin burden",
    "lc1_sole_making_in_t1": "If final-assembly energy already includes sole making: no separate sole-making energy for either shoe",
    "lc1_made_in_china": "Both shoes made in China (grid 528 g/kWh)",
    "lc1_made_in_indonesia": "Both shoes made in Indonesia (grid 705 g/kWh)",
}


def tri(rng, lo, mode, hi, n):
    if hi <= lo:
        return np.full(n, mode)
    mode = min(max(mode, lo), hi)
    return rng.triangular(lo, mode, hi, n)


def scenario_value(x, vol, name):
    kw, over = SCENARIOS[name]
    xx = dict(x)
    xx.update(over)
    r = lca.evaluate(xx, vol, **kw)
    if name == "baseline_clean_power":
        b = lca.evaluate(xx, vol, upper_lives=1)["base_per100"]
        return r, 100 * (1 - r["base_per100"] / b)
    return r, r["reduction_pct"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261107)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    vol = lca.load_volumes()
    x0 = lca.central()
    res = dict(functional_unit="one pair, men's US 9, per 100 km run, cradle to grave (retail and consumer travel excluded)",
               impact="GWP100, kg CO2e, fossil GHG only", scenarios={}, cheah_check=lca.cheah_check(x0))

    for name in SCENARIOS:
        r, red = scenario_value(x0, vol, name)
        res["scenarios"][name] = dict(label=LABELS[name], reduction_pct=round(red, 1),
                                      baseline_per100=round(r["base_per100"], 3), lc1_per100=round(r["lc1_per100"], 3))
    rc = lca.evaluate(x0, vol, upper_lives=1, clean_lc1=True)
    rd = lca.evaluate(x0, vol, upper_lives=1, clean_lc1=False)
    def pack(r):
        return dict(total_kg=round(r["total"], 3), stages={k: round(v, 3) for k, v in r["stages"].items()},
                    parts={k: round(v, 3) for k, v in r["parts"].items()},
                    parts_materials={k: round(v, 4) for k, v in r["parts_materials"].items()},
                    eol_parts={k: round(v, 3) for k, v in r["eol_parts"].items()},
                    mass={k: round(v, 1) for k, v in r["mass"].items()}, pack_g=r["pack_g"])
    res["pair"] = dict(baseline=pack(rc["baseline"]), lc1=pack(rc["lc1"]), lc1_design_only=pack(rd["lc1"]),
                       extra_sole_kg=round(rc["extra_sole"], 3))
    res["life_km_central"] = x0["P.life_km"]

    # ---- Monte Carlo (triangular on every swept input; same draw for both shoes)
    rng = np.random.default_rng(a.seed)
    R = lca.ranges()
    draws = {k: tri(rng, lo, mode, hi, a.n) for k, (lo, mode, hi) in R.items()}
    mc = {k: np.zeros(a.n) for k in ("design_only", "lc1", "lc1_resole_U", "base_per100", "lc1_per100")}
    U = rng.uniform(1.0, 2.0, a.n)
    for i in range(a.n):
        x = dict(x0)
        for k in R:
            x[k] = draws[k][i]
        x["P.upper_lives"] = 1.0
        r1 = lca.evaluate(x, vol, upper_lives=1, clean_lc1=True)
        mc["lc1"][i] = r1["reduction_pct"]
        mc["base_per100"][i] = r1["base_per100"]
        mc["lc1_per100"][i] = r1["lc1_per100"]
        mc["design_only"][i] = lca.evaluate(x, vol, upper_lives=1, clean_lc1=False)["reduction_pct"]
        mc["lc1_resole_U"][i] = lca.evaluate(x, vol, upper_lives=U[i], clean_lc1=True)["reduction_pct"]
    pct = lambda v: {p: round(float(np.percentile(v, p)), 3) for p in (5, 25, 50, 75, 95)}  # noqa: E731
    res["monte_carlo"] = dict(n=a.n, seed=a.seed, distribution="triangular(low, central, high) per input; upper lives uniform 1-2 in lc1_resole_U",
                              reduction_pct={k: pct(mc[k]) for k in ("design_only", "lc1", "lc1_resole_U")},
                              p_lc1_ge_50=round(float(np.mean(mc["lc1"] >= 50)), 3),
                              p_design_only_ge_50=round(float(np.mean(mc["design_only"] >= 50)), 3),
                              p_lc1_resole_U_ge_50=round(float(np.mean(mc["lc1_resole_U"] >= 50)), 3),
                              p_lc1_lower=round(float(np.mean(mc["lc1"] > 0)), 4),
                              base_per100=pct(mc["base_per100"]), lc1_per100=pct(mc["lc1_per100"]))
    with open(os.path.join(OUT, "mc_lc1_reduction_pct.csv"), "w", newline="\n") as f:
        f.write("lc1 reduction % per 100 km\n" + "".join(f"{v:.3f}\n" for v in mc["lc1"]))

    # ---- tornado on the LC-1 (as specified) reduction
    base_red = res["scenarios"]["lc1"]["reduction_pct"]
    torn = []
    for k, (lo, mode, hi) in R.items():
        vals = []
        for v in (lo, hi):
            x = dict(x0)
            x[k] = v
            vals.append(lca.evaluate(x, vol, upper_lives=1, clean_lc1=True)["reduction_pct"])
        torn.append(dict(input=k, low=lo, high=hi, red_at_low=round(vals[0], 2), red_at_high=round(vals[1], 2),
                         span=round(abs(vals[1] - vals[0]), 2)))
    torn.sort(key=lambda d: -d["span"])
    res["tornado"] = dict(central_reduction_pct=base_red, rows=torn[:15])

    with open(os.path.join(OUT, "lca_results.json"), "w", newline="\n") as f:
        json.dump(res, f, indent=1)

    # ---- tables
    with open(os.path.join(OUT, "factors_table.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["group", "id", "central", "low", "high", "unit", "basis", "source"])
        for g, d in (("factor", PR.F), ("energy_freight", PR.E), ("parameter", PR.P)):
            for k, v in d.items():
                w.writerow([g, k] + list(v))
        for k, v in PR.INCIN.items():
            w.writerow(["incineration", k, v, v, v, "kg CO2/kg", "derived", "carbon content x 44/12 (IPCC 2006 Vol 5 Ch 5 Eq 5.2)"])
    with open(os.path.join(OUT, "inventory.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["shoe", "component", "module", "factor", "g_per_shoe", "low", "high", "basis"])
        for r in lca.rows_for(x0, "baseline", vol):
            src = {b[0]: b for b in PR.BASELINE}[r[0]]
            w.writerow(["baseline", r[0], r[1], r[2], round(r[3], 1), src[4] if r[0] != "Midsole" else "", src[5] if r[0] != "Midsole" else "", src[9]])
        for r in lca.lc1_sole_rows(x0, vol):
            w.writerow(["lc1", r[0], r[1], r[2], round(r[3], 1), "", "", "CAD volume x density"])
        for r in PR.LC1_UPPER:
            w.writerow(["lc1", r[0], r[1], r[2], r[3], r[4], r[5], r[9]])
        for p in PR.BASE_PACK:
            w.writerow(["baseline", p[0], "packaging (per pair)", p[1], p[2], "", "", p[3]])
        for p in PR.LC1_PACK:
            w.writerow(["lc1", p[0], "packaging (per pair)", p[1], p[2], "", "", p[3]])

    figures(res, mc)
    s = res["scenarios"]
    print(json.dumps({k: v["reduction_pct"] for k, v in s.items()}, indent=1))
    print(json.dumps(res["monte_carlo"], indent=1))
    print([ (t["input"], t["red_at_low"], t["red_at_high"]) for t in torn[:8]])


def figures(res, mc):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))
    st = lca.STAGES
    for j, (k, lab) in enumerate((("baseline", "Baseline"), ("lc1_design_only", "LC-1 design,\ngrid power"), ("lc1", "LC-1 as\nspecified"))):
        bottom = 0
        for i, s in enumerate(st):
            v = res["pair"][k]["stages"][s]
            ax[0].bar(j, v, bottom=bottom, color=plt.cm.tab10(i), label=s if j == 0 else None)
            bottom += v
    ax[0].set_xticks([0, 1, 2], ["Baseline", "LC-1 design,\ngrid power", "LC-1 as\nspecified"])
    ax[0].set_ylabel("kg CO2e per pair")
    ax[0].legend(fontsize=8)
    ax[1].hist(mc["lc1"], bins=60, color="#245F73")
    ax[1].axvline(50, color="k", ls="--")
    ax[1].set_xlabel("LC-1 reduction per 100 km vs baseline (%)")
    t = res["tornado"]["rows"][:10][::-1]
    c = res["tornado"]["central_reduction_pct"]
    for i, r in enumerate(t):
        ax[2].barh(i, r["red_at_low"] - c, left=c, color="#733E24")
        ax[2].barh(i, r["red_at_high"] - c, left=c, color="#245F73")
    ax[2].set_yticks(range(len(t)), [r["input"] for r in t], fontsize=7)
    ax[2].axvline(c, color="k")
    ax[2].set_xlabel("reduction % (brown: input at low, blue: at high)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "lca_summary.png"), dpi=110)


if __name__ == "__main__":
    main()
