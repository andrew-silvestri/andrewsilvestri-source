"""Build outputs/payload.json for the scales page from the hash-checked raw files (sources.py).

The page puts everything on one pair of axes: mass (kg) against power per kilogram (W/kg). Life comes from
Hatton et al. (2019), processed the way their own R code does by default (Analysis.R, Funx.R); people with
their fuel come from OWID's primary energy per person; stars come from Eker et al. (2018); cities come from
our own fit of BEA county GDP summed to Census metropolitan areas. The checks at the bottom compare the
results with figures the sources print, so a reader that misreads a file stops the build.

Run:  python build_scales.py            writes outputs/payload.json
"""
import json
import math
import os
import random
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sources as S   # noqa: E402

OUT = os.path.join(HERE, "outputs", "payload.json")

# Hatton's Plot2 codes (ReadMe.R) and the groups the page draws.
GROUPS = {"8": "bacteria", "3": "protists", "4": "plants", "5": "invertebrates", "6": "coldvert",
          "7": "birds", "1": "mammals", "2": "mammals", "9": "mammals"}
LABEL = {"bacteria": "Bacteria", "protists": "Single-celled eukaryotes", "plants": "Plants",
         "invertebrates": "Invertebrates", "coldvert": "Fish, amphibians, reptiles",
         "birds": "Birds", "mammals": "Mammals"}
CORRECT = {"3", "4", "5", "6", "8"}      # Hatton's xendo: every group but birds and mammals
T_REF, E_ACT, K_B = 20.0, 0.6, 8.617e-5  # Analysis.R line 29; Funx.R lines 13-14
G_CODATA = 6.67430e-11                   # CODATA 2018, m3 kg-1 s-2
HOURS_YEAR = 8766                        # 365.25 days
BODY_KG = 70.0                           # the reference adult in Hatton's table (AnAge row, 70 kg)


def ols(x, y):
    x, y = np.asarray(x), np.asarray(y)
    b, a = np.polyfit(x, y, 1)
    return float(a), float(b)


def boot_slope(x, y, n=1000, seed=1):
    rng = random.Random(seed)
    x, y = list(x), list(y)
    idx = range(len(x))
    bs = []
    for _ in range(n):
        s = [rng.choice(idx) for _ in idx]
        bs.append(ols([x[i] for i in s], [y[i] for i in s])[1])
    bs.sort()
    return bs[int(0.025 * n)], bs[int(0.975 * n) - 1]


def life():
    rows = S.metabolism()
    n_rows = len(rows)
    kept = []
    for r in rows:
        g = r["Plot2"]
        if g == "9999":                  # Hatton leaves these plants out of every analysis
            continue
        w, m = float(r["Metabolism_W"]), float(r["Mass_g"])
        if g in CORRECT:
            if not r["Temperature_C"].strip():
                continue                 # tempcorr() drops rows it cannot correct
            t = float(r["Temperature_C"])
            w = w / math.exp(E_ACT / K_B * (1 / (273.15 + T_REF) - 1 / (273.15 + t)))
        kept.append({"g": g, "sp": r["Species"], "m": m, "w": w})
    # aggre(funx=min, aggmass=FALSE): one value per species, its lowest power and that row's mass; plants
    # and "Unknown" species are not aggregated
    by = {}
    pts = []
    for k in kept:
        if k["g"] == "4" or k["sp"] == "Unknown":
            pts.append(k)
        else:
            by.setdefault(k["sp"], []).append(k)
    for v in by.values():
        pts.append(min(v, key=lambda k: k["w"]))
    for p in pts:
        p["grp"] = GROUPS[p["g"]]
        p["lx"] = math.log10(p["m"] / 1000)                 # kg
        p["ly"] = math.log10(p["w"] / (p["m"] / 1000))      # W/kg
        p["lw"] = math.log10(p["w"])
    euk = [p for p in pts if p["grp"] != "bacteria"]
    a, b = ols([p["lx"] for p in euk], [p["lw"] for p in euk])
    lo, hi = boot_slope([p["lx"] for p in euk], [p["lw"] for p in euk])
    groups = {}
    for key in LABEL:
        q = [p for p in pts if p["grp"] == key]
        ga, gb = ols([p["lx"] for p in q], [p["lw"] for p in q])
        lxs = sorted(p["lx"] for p in q)
        groups[key] = {
            "label": LABEL[key], "n": len(q),
            "gmean_wkg": 10 ** (sum(p["ly"] for p in q) / len(q)),
            "lx_lo": lxs[int(0.02 * len(q))], "lx_hi": lxs[int(0.98 * len(q)) - 1],
            "lx_mid": sum(lxs) / len(q),
            "slope": gb, "icpt": ga,
            # binned cloud for the figure: one mark per 0.2 decade of mass by 0.1 decade of W/kg
            "cloud": sorted({(round(round(p["lx"] / 0.2) * 0.2, 1), round(round(p["ly"] / 0.1) * 0.1, 1))
                             for p in q}),
        }
    eu_means = [groups[k]["gmean_wkg"] for k in LABEL if k != "bacteria"]
    lys = sorted(p["ly"] for p in euk)
    lx_e = sorted(p["lx"] for p in euk)
    human = [r for r in rows if r["Species"] == "Homo sapiens" and float(r["Mass_g"]) == BODY_KG * 1000]
    if len(human) != 1:
        raise SystemExit(f"expected one 70 kg Homo sapiens row in Metabolism.csv, found {len(human)}")
    h_w = float(human[0]["Metabolism_W"])
    within = {k: groups[k]["slope"] for k in LABEL if k not in ("bacteria",)}
    return {
        "n_rows": n_rows, "n_species_pts": len(pts), "n_euk": len(euk),
        "n_species": len({p["sp"] for p in pts if p["sp"] != "Unknown"}),
        "heaviest": {k: max((p for p in pts if p["grp"] == k), key=lambda p: p["m"])["sp"] for k in LABEL},
        "heaviest_kg": {k: max(p["m"] for p in pts if p["grp"] == k) / 1000 for k in LABEL},
        "lightest": {k: min((p for p in pts if p["grp"] == k), key=lambda p: p["m"])["sp"] for k in LABEL},
        "lightest_kg": {k: min(p["m"] for p in pts if p["grp"] == k) / 1000 for k in LABEL},
        "euk_slope": b, "euk_icpt": a, "euk_ci": [lo, hi],
        "euk_lx_span": [lx_e[0], lx_e[-1]],
        "within_min": min(within.values()), "within_max": max(within.values()),
        "band_lo": min(eu_means), "band_hi": max(eu_means),
        "sp_p01": 10 ** lys[int(0.01 * len(lys))], "sp_p99": 10 ** lys[int(0.99 * len(lys)) - 1],
        "groups": groups,
        "human": {"kg": BODY_KG, "w": h_w, "wkg": h_w / BODY_KG, "ref": human[0]["Reference"].split(";")[0]},
    }


def fuel(body_w):
    E = S.energy_per_capita()
    meta = S.owid_meta()
    out = {}
    for ent, key in (("World", "world"), ("United States", "us"), ("India", "india"),
                     ("Germany", "germany"), ("Chad", "chad"), ("Iceland", "iceland")):
        yr = max(E[ent])
        kwh = E[ent][yr]
        w = kwh * 1000 / HOURS_YEAR
        out[key] = {"name": ent, "year": yr, "kwh": kwh, "w": w, "wkg": w / BODY_KG, "x_body": w / body_w}
    col = meta["columns"]["total_energy_supply_per_capita_kwh"]
    out["updated"] = col["lastUpdated"]
    out["citation"] = col["citationShort"]
    return out


def stars():
    L_N = float(S.quote("iau_2015_b3.pdf", r"1LN ⊙ = (\d\.\d+) × 10(26) W").group(1)) * 1e26
    T_N = float(S.quote("iau_2015_b3.pdf", r"1T N ⊙ = (\d{4}) K").group(1))
    GM = float(S.quote("iau_2015_b3.pdf", r"= (\d\.\d{7}) × 1020 m3 s−2").group(1)) * 1e20
    msun = GM / G_CODATA
    rows = S.stars()
    cal = [r for r in rows if r[4].startswith("*")]          # Eker's 509-star calibration sample
    pts = []
    for name, m, rad, teff, _ in cal:
        L = rad ** 2 * (teff / T_N) ** 4
        pts.append({"name": name, "lx": math.log10(m * msun), "ly": math.log10(L * L_N / (m * msun)),
                    "msun": m, "L": L})
    a, b = ols([math.log10(p["msun"]) for p in pts], [math.log10(p["L"]) for p in pts])
    a2, b2 = ols([p["lx"] for p in pts], [p["ly"] for p in pts])
    ms = sorted(p["msun"] for p in pts)
    wk = sorted(10 ** p["ly"] for p in pts)
    return {
        "L_N": L_N, "T_N": T_N, "GM": GM, "msun": msun, "sun_wkg": L_N / msun,
        "n_all": len(rows), "n": len(pts), "m_lo": ms[0], "m_hi": ms[-1],
        "wkg_lo": wk[0], "wkg_hi": wk[-1],
        "mlr_slope": b, "wkg_slope": b2, "wkg_icpt": a2,
        "pts": sorted({(round(p["lx"], 2), round(p["ly"], 2)) for p in pts}),
    }


def cities(year=2023):
    gdp = S.county_gdp(year)
    msa, counties = S.msa_population(year)
    # BEA's combined areas: give each part's FIPS a pointer to the combo, matched by name in the Census file
    names = S.county_names()
    part_of, outside = {}, set()
    for bfips, (st, parts) in S.county_combos().items():
        for j, part in enumerate(parts):
            # BEA names the county first and the independent cities after it ("Roanoke + Salem")
            want = (part + " County", part + " County and city") if j == 0 else (part + " city",)
            if st == "HI":
                want = (part + " County",)
            hits = [f for f, n in names.items() if n.endswith(", " + st) and n[:-len(st) - 2] in want]
            if len(hits) > 1:
                raise SystemExit(f"BEA combo part {part}, {st}: {len(hits)} Census matches")
            if hits:
                part_of[hits[0]] = bfips
            else:                       # a part outside every metro area: the combo cannot be split
                outside.add(bfips)
    pts, dropped, merged = [], 0, 0
    for c in msa:
        fs = counties[c]
        combos = {part_of[f] for f in fs if f not in gdp and f in part_of}
        whole = all(f in fs for f, b in part_of.items() if b in combos)   # every part of each combo in this MSA
        if combos and whole and not combos & outside:
            counties[c] = [f for f in fs if f not in part_of] + sorted(combos)
            merged += 1
    for c, (name, pop) in msa.items():
        g = [gdp.get(f) for f in counties[c]]
        if not g or any(v is None for v in g):
            dropped += 1
            continue
        pts.append({"cbsa": c, "name": name, "pop": pop, "gdp": sum(g) * 1e3})
    x = [math.log10(p["pop"]) for p in pts]
    y = [math.log10(p["gdp"]) for p in pts]
    a, b = ols(x, y)
    lo, hi = boot_slope(x, y)
    res = np.array(y) - (a + b * np.array(x))
    r2 = 1 - res.var() / np.var(y)
    big = max(pts, key=lambda p: p["pop"])
    small = min(pts, key=lambda p: p["pop"])
    return {
        "year": year, "n": len(pts), "n_msa": len(msa), "dropped": dropped, "merged": merged,
        "dropped_names": sorted(n for c, (n, _) in msa.items() if c not in {p["cbsa"] for p in pts}),
        "slope": b, "icpt": a, "ci": [lo, hi], "r2": float(r2),
        "pts": sorted((round(math.log10(p["pop"]), 3), round(math.log10(p["gdp"] / p["pop"]), 3)) for p in pts),
        "big": {"name": big["name"], "pop": big["pop"], "gdp_pc": big["gdp"] / big["pop"]},
        "small": {"name": small["name"], "pop": small["pop"], "gdp_pc": small["gdp"] / small["pop"]},
        "x10": 10 ** (b - 1),         # per-person gain for a city ten times larger
    }


def main():
    L = life()
    P = {"life": L, "fuel": fuel(L["human"]["w"]), "stars": stars(), "cities": cities()}
    span = P["life"]["euk_lx_span"]
    # a single 3/4-power law over the eukaryote mass span would spread W/kg by this factor
    P["life"]["kleiber_spread"] = 10 ** (0.25 * (span[1] - span[0]))
    P["life"]["band_ratio"] = P["life"]["band_hi"] / P["life"]["band_lo"]
    P["sun_vs_human"] = P["life"]["human"]["wkg"] / P["stars"]["sun_wkg"]
    check(P)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1, sort_keys=True)
        f.write("\n")
    L, F, St, C = P["life"], P["fuel"], P["stars"], P["cities"]
    print(f"life: {L['n_rows']} rows -> {L['n_species_pts']} points; eukaryote slope {L['euk_slope']:.3f} "
          f"[{L['euk_ci'][0]:.3f}, {L['euk_ci'][1]:.3f}]; within groups {L['within_min']:.2f}-{L['within_max']:.2f}; "
          f"group means {L['band_lo']:.2f}-{L['band_hi']:.2f} W/kg (x{L['band_ratio']:.0f}); "
          f"species 1-99% {L['sp_p01']:.3f}-{L['sp_p99']:.1f}; 3/4 spread x{L['kleiber_spread']:.2e}")
    for k, g in L["groups"].items():
        print(f"  {k:14s} n={g['n']:5d} gmean {g['gmean_wkg']:.3g} W/kg slope {g['slope']:.3f} "
              f"mass 10^{g['lx_lo']:.1f}-10^{g['lx_hi']:.1f} kg")
    print(f"human {L['human']['w']:.1f} W = {L['human']['wkg']:.2f} W/kg ({L['human']['ref']})")
    for k in ("world", "us", "india", "germany", "chad", "iceland"):
        f = F[k]
        print(f"  {f['name']} {f['year']}: {f['w']:.0f} W/person = {f['wkg']:.1f} W/kg = x{f['x_body']:.1f} body")
    print(f"stars: {St['n']} of {St['n_all']}; {St['m_lo']}-{St['m_hi']} Msun; W/kg {St['wkg_lo']:.2e}-{St['wkg_hi']:.2f}; "
          f"MLR slope {St['mlr_slope']:.2f}; W/kg slope {St['wkg_slope']:.2f}; Sun {St['sun_wkg']:.3e} W/kg; "
          f"human/Sun x{P['sun_vs_human']:.0f}")
    print(f"cities {C['year']}: {C['n']} of {C['n_msa']} MSAs; slope {C['slope']:.3f} [{C['ci'][0]:.3f}, {C['ci'][1]:.3f}] "
          f"R2 {C['r2']:.2f}; x10 city -> x{C['x10']:.2f} GDP per person")


def check(P):
    """Known answers from the sources' own text: if a reader is off, these fail."""
    L, F, St, C = P["life"], P["fuel"], P["stars"], P["cities"]
    errs = []
    if L["n_rows"] != 8098:
        errs.append(f"Metabolism.csv has 8,098 rows (Zenodo 3145281); read {L['n_rows']}")
    # Hatton et al. print a pooled eukaryote exponent of about 0.96 and within-group exponents near 3/4
    if not 0.92 < L["euk_slope"] < 0.98:
        errs.append(f"eukaryote slope {L['euk_slope']:.3f} is not near the paper's 0.96")
    # Makarieva et al. (2008) print group means of 0.3 to 9 W/kg; Hatton's data must land near that band
    if not (0.1 < L["band_lo"] < 0.6 and 4 < L["band_hi"] < 15):
        errs.append(f"group means {L['band_lo']:.2f}-{L['band_hi']:.2f} W/kg not near 0.3-9")
    # FAO/WHO/UNU (2004) and Henry (2005): a 70 kg adult rests at about 80 W
    if not 70 < L["human"]["w"] < 95:
        errs.append(f"human resting power {L['human']['w']:.0f} W")
    if not 15000 < F["world"]["kwh"] < 25000:
        errs.append(f"world primary energy {F['world']['kwh']:.0f} kWh a person")
    if St["L_N"] != 3.828e26 or St["T_N"] != 5772:
        errs.append("IAU nominal luminosity or temperature misread")
    if not 1.9e-4 < St["sun_wkg"] < 1.95e-4:
        errs.append(f"Sun {St['sun_wkg']:.3e} W/kg")
    if St["n"] != 509:
        errs.append(f"Eker's calibration sample has 509 stars; read {St['n']}")
    # Eker et al.'s mass range is 0.179 to 31 Msun
    if not (abs(St["m_lo"] - 0.179) < 0.01 and abs(St["m_hi"] - 31) < 1):
        errs.append(f"star mass range {St['m_lo']}-{St['m_hi']}")
    # published US fits of GDP or wages on metro population run 1.12-1.16 (Bettencourt et al. 2007, Table 1); our
    # first fit (2026-11-07) read Metropolitan Divisions as if they were whole MSAs (New York at 11.9 million);
    # the 387 MSAs are now read alone, and New York must come out near 19.5 million people
    if not (1.05 < C["slope"] < 1.22 and 340 < C["n"] <= 387):
        errs.append(f"city GDP slope {C['slope']:.3f} on {C['n']} MSAs")
    if not 18e6 < C["big"]["pop"] < 21e6:
        errs.append(f"largest MSA {C['big']['name']} {C['big']['pop']:.0f} people")
    if errs:
        raise SystemExit("payload checks failed:\n  " + "\n  ".join(errs))


if __name__ == "__main__":
    main()
