"""Build outputs/payload.json for site/lowcarbon-shoe.html.

Reads the prototype package's own results (lca/results, tests/results,
cad/out/volumes.json), re-runs the LCA's central case from the shipped code and
checks it against the stored results, and stops on any failed known answer
(a figure the page prints must come from code that still produces it).

python build_lowcarbon_shoe.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lca"))
import lca  # noqa: E402

OUT = os.path.join(HERE, "outputs", "payload.json")
UPPER_BASE = ["Strobel board", "Upper mesh", "Lining", "Collar padding", "Overlays", "Heel counter", "Toe puff",
              "Laces", "Thread", "Labels", "Adhesive and primer"]
UPPER_LC1 = ["Upper mesh and lining (recycled PET)", "Collar padding (recycled PET spacer)", "Strobel sock (recycled PET)",
             "Heel counter (recycled TPU)", "Laces (recycled PET)", "Stitchdown thread (recycled PET)", "Label (recycled PET)"]


def load(*p):
    with open(os.path.join(HERE, *p), encoding="utf-8") as f:
        return json.load(f)


def groups(pair, shoe):
    pm, st = pair["parts_materials"], pair["stages"]
    if shoe == "baseline":
        g = dict(upper=sum(pm[k] for k in UPPER_BASE), sock=pm["Sockliner"], mid=pm["Midsole"],
                 out=pm["Outsole"] + pm["Shank"])
    else:
        g = dict(upper=sum(pm[k] for k in UPPER_LC1), sock=pm["Sockliner (recycled PET spacer)"],
                 mid=pm["Midsole (expanded TPU)"], out=pm["Outsole skin (TPU, recycled share)"] + pm["Stitch rim (TPU, recycled share)"])
    g["factory"] = st["part_making"] + st["assembly"]
    g["rest"] = st["packaging"] + st["transport"] + st["end_of_life"]
    return {k: round(v, 4) for k, v in g.items()}


def build():
    R = load("lca", "results", "lca_results.json")
    fea = load("tests", "results", "fea.json")
    lat = load("tests", "results", "fea_lattice.json")
    er = load("tests", "results", "energy_return.json")
    wear = load("tests", "results", "wear.json")
    mass = load("tests", "results", "mass.json")
    vol = load("cad", "out", "volumes.json")
    pair = R["pair"]
    sc = {k: v["reduction_pct"] for k, v in R["scenarios"].items()}
    P = dict(
        pair={k: round(pair[k]["total_kg"], 3) for k in ("baseline", "lc1_design_only", "lc1")},
        stages={k: pair[k]["stages"] for k in ("baseline", "lc1_design_only", "lc1")},
        groups={k: groups(pair[k], "baseline" if k == "baseline" else "lc1") for k in ("baseline", "lc1_design_only", "lc1")},
        mass_g={k: pair[k]["mass"] for k in ("baseline", "lc1")},
        pack_g={k: pair[k]["pack_g"] for k in ("baseline", "lc1")},
        life_km=R["life_km_central"],
        per100={k: R["scenarios"][k]["lc1_per100"] for k in ("design_only", "lc1", "lc1_resole")},
        base_per100=R["scenarios"]["lc1"]["baseline_per100"],
        base_clean_per100=R["scenarios"]["baseline_clean_power"]["baseline_per100"],
        scenarios=sc,
        mc=R["monte_carlo"],
        tornado=R["tornado"]["rows"][:6],
        fea=dict(base_N=fea["cases"]["baseline"]["drop_5J"]["peak_force_N"], lc1_N=fea["cases"]["lc1"]["drop_5J"]["peak_force_N"],
                 diff_pct=fea["lc1_vs_baseline_drop_pct"], published=fea["published_F1976_5J_range_N"],
                 heel_ratio=round(fea["cases"]["lc1"]["heel_1p12BW"]["deflection_mm"] / fea["cases"]["baseline"]["heel_1p12BW"]["deflection_mm"], 2),
                 sweep=[r for r in fea["t4_sweep"] if r["etpu_density"] == 200.0], rate=fea["rate_factor"]),
        lattice=lat,
        energy_return=dict(base=er["baseline_pct"], lc1=er["lc1_pct"]),
        wear_km=dict(base=wear["wear_through_km"]["baseline"]["50"], lc1=wear["wear_through_km"]["lc1"]["50"]),
        particles=wear["particle_loss_g_per_100km_pair"],
        shoe_g=dict(lc1=mass["lc1_g"], base=round(mass["baseline_g"], 1)),
        volumes=vol["volumes_cm3"], dims=vol["dims"],
        cheah=R["cheah_check"],
        inputs={k: lca.central()[v] for k, v in (("tpu", "F.TPU"), ("t1_kwh", "P.t1_kwh"), ("grid", "E.GRID"))},
    )
    x, vol = lca.central(), lca.load_volumes()
    rb = lca.evaluate(x, vol, upper_lives=1, clean_lc1=True, clean_base=True)
    P["pair"]["baseline_clean"] = round(rb["baseline"]["total"], 3)
    P["groups"]["baseline_clean"] = groups(dict(parts_materials=rb["baseline"]["parts_materials"], stages=rb["baseline"]["stages"]), "baseline")
    rbox = lca.evaluate(x, vol, upper_lives=1, clean_lc1=False, lc1_pack=lca.PR.BASE_PACK)
    P["per100"]["design_box"] = round(rbox["lc1_per100"], 3)
    P["scenarios"]["design_with_box"] = round(rbox["reduction_pct"], 1)
    b100, d100, l100, r100 = P["base_per100"], P["per100"]["design_only"], P["per100"]["lc1"], P["per100"]["lc1_resole"]
    db = P["per100"]["design_box"]
    P["per100_steps"] = [
        ("Typical trainer", b100, "level"),
        ("Materials, no glue", round(b100 - db, 3), "step"),
        ("No shoebox", round(db - d100, 3), "step"),
        ("Renewable power, two factories", round(d100 - l100, 3), "step"),
        ("LC-1 as specified", l100, "level"),
        ("Upper kept for a second sole", round(l100 - r100, 3), "step"),
        ("LC-1, two soles per upper", r100, "level"),
    ]
    P["known_answers"] = known_answers(P, R, fea)
    return P


def known_answers(P, R, fea):
    out, bad = [], []

    def chk(name, ok, detail):
        out.append(dict(check=name, ok=bool(ok), detail=detail))
        print(("ok   " if ok else "FAIL ") + name + ": " + detail)
        if not ok:
            bad.append(name)

    x, vol = lca.central(), lca.load_volumes()
    r = lca.evaluate(x, vol, upper_lives=1, clean_lc1=True)
    chk("lca recompute", abs(r["reduction_pct"] - R["scenarios"]["lc1"]["reduction_pct"]) < 0.05,
        f"{r['reduction_pct']:.2f} % from the shipped code vs {R['scenarios']['lc1']['reduction_pct']} stored")
    chk("lca pair totals", abs(r["baseline"]["total"] - P["pair"]["baseline"]) < 1e-3 and abs(r["lc1"]["total"] - P["pair"]["lc1"]) < 1e-3,
        f"{r['baseline']['total']:.3f} / {r['lc1']['total']:.3f} kg")
    for k in ("baseline", "baseline_clean", "lc1_design_only", "lc1"):
        s = sum(P["groups"][k].values())
        chk(f"groups sum {k}", abs(s - P["pair"][k]) < 0.01, f"{s:.3f} vs {P['pair'][k]:.3f}")
    worst = max(abs(c["err_pct"]) for c in fea["self_check_1d"])
    chk("fea 1-D column", worst < 0.1, f"worst error {worst} %")
    lo, hi = fea["published_F1976_5J_range_N"]
    b = fea["cases"]["baseline"]["drop_5J"]["peak_force_N"]
    chk("fea baseline in published F1976 range", lo <= b <= hi, f"{b} N in {lo}-{hi} N")
    chk("fea stiffer foam raises the peak", fea["check_stiffer_foam_peak_N"] > b, f"{fea['check_stiffer_foam_peak_N']} > {b} N")
    c = R["cheah_check"]
    chk("coal factor vs Cheah", abs(c["total"] / c["paper_total"] - 1) < 0.1, f"{c['total']} vs {c['paper_total']} kg (factor check only)")
    if bad:
        raise SystemExit("known answers failed: " + ", ".join(bad))
    return out


if __name__ == "__main__":
    P = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1)
        f.write("\n")
    print("wrote", OUT)
