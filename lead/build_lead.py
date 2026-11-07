"""Build outputs/payload.json for the lead page.

1. Reproduce McFarland, Hauer and Reuben (PNAS 2022): the share of each birth cohort alive in 2015 whose
   blood lead at ages 1-4 fell in each band (SI Dataset S01), times the IQ points the paper assigns to each
   band (SI Dataset S03). Known answers the paper printed are checked before anything is written:
   824,097,690 points in total, 2.6 per person, and the cohort means 4.8 (1961-65), 5.9 (1966-70) and
   5.7 (1971-75).
2. The same exposure under two other published dose-response functions (Method, "How much the answer
   depends on the curve"): Lanphear et al. 2005's log-linear fit, counted from 2.4 ug/dL (the 5th
   percentile of its pooled data), and the Crump et al. 2013 function that Larsen and Sanchez-Triana
   apply worldwide, which has no threshold. Bands are represented by their mid-points; 30+ by 32.5.
   These are this page's calculations, not the paper's.
3. An illustration of what a shift in the mean does at the top of the distribution: scores taken as
   normal with mean 100 and SD 15 in the absence of lead, and each band shifted by its own loss. This is
   an assumption made to show scale, not a finding of any study.
4. The lead series (Bureau of Mines), the measured fall in children's blood lead (EPA from NHANES), and
   the world estimate for 2019 (Larsen and Sanchez-Triana 2023).

Run:  python build_lead.py
"""
import json
import math
from collections import defaultdict
from statistics import NormalDist

import sources as S
from netfetch import HERE

OUT = HERE / "outputs" / "payload.json"
FIRST, LAST = 1940, 2015
MID = {"0-4.9": 2.5, "5-9.9": 7.5, "10-14.9": 12.5, "15-19.9": 17.5, "20-24.9": 22.5, "25-29.9": 27.5, "30+": 32.5}
LANPHEAR_BETA = 2.70     # IQ points per ln(ug/dL), Lanphear et al. 2005 (read from the article by test_lead.py)
LANPHEAR_FLOOR = 2.4     # ug/dL, the 5th percentile of the pooled concurrent blood lead (same article)
LANPHEAR_EARLY_BETA = 2.04   # the same table's fit on early-childhood blood lead (mean of ages 6-24 months)
LANPHEAR_EARLY_FLOOR = 4.1   # ug/dL, its 5th percentile
CRUMP_BETA = 3.246       # Crump et al. 2013 as used by Larsen and Sanchez-Triana 2023 (read from the PDF)


def lanphear(band):
    b = MID[band]
    return LANPHEAR_BETA * math.log(b / LANPHEAR_FLOOR) if b > LANPHEAR_FLOOR else 0.0


def lanphear_early(band):
    b = MID[band]
    return LANPHEAR_EARLY_BETA * math.log(b / LANPHEAR_EARLY_FLOOR) if b > LANPHEAR_EARLY_FLOOR else 0.0


def crump(band):
    return CRUMP_BETA * math.log(MID[band] + 1)


def cohorts():
    """2015 cross-section: population and population in each band, by birth year."""
    pop = defaultdict(lambda: defaultdict(float))
    for r in S.s01():
        if r["year"] == 2015:
            pop[r["cohort"]][r["band"]] += r["leadpop"]
    return pop


def build():
    loss = S.band_loss()
    pop = cohorts()
    alive = S.s03_population()
    years = list(range(FIRST, LAST + 1))

    def points(fn, ys=years):
        return sum(n * fn(b) for c in ys for b, n in pop[c].items())

    paper = lambda b: loss[b]
    total = points(paper)
    per_year = []
    for c in years:
        n = sum(pop[c].values())
        q = sum(v * loss[b] for b, v in pop[c].items())
        ge5 = n - pop[c]["0-4.9"]
        ge10 = ge5 - pop[c]["5-9.9"]
        per_year.append({"cohort": c, "pop": round(n), "points": round(q), "mean": q / n, "ge5": ge5 / n,
                         "ge10": ge10 / n})

    def group(a, b):
        ys = range(a, b + 1)
        n = sum(sum(pop[c].values()) for c in ys)
        q = sum(v * loss[k] for c in ys for k, v in pop[c].items())
        g5 = sum(sum(pop[c].values()) - pop[c]["0-4.9"] for c in ys)
        g10 = sum(sum(pop[c].values()) - pop[c]["0-4.9"] - pop[c]["5-9.9"] for c in ys)
        return {"from": a, "to": b, "pop": round(n), "points": round(q), "mean": q / n, "ge5": g5 / n, "ge10": g10 / n}

    fives = [group(1940, 1945)] + [group(a, a + 4) for a in range(1946, 2015, 5)]
    by = {(g["from"], g["to"]): g for g in fives}
    n_ge5 = sum(sum(pop[c].values()) - pop[c]["0-4.9"] for c in years)

    # known answers the paper printed (main text and Table 2)
    assert round(total) == 824097690, total
    assert round(total / alive, 1) == 2.6
    for k, v in {(1961, 1965): 4.8, (1966, 1970): 5.9, (1971, 1975): 5.7}.items():
        assert round(by[k]["mean"], 1) == v, (k, by[k]["mean"])
    assert round(100 * n_ge5 / alive, 1) == 53.5, n_ge5 / alive

    peak5 = max(fives, key=lambda g: g["mean"])
    peak1 = max(per_year, key=lambda r: r["mean"])
    mid_century = group(1951, 1980)

    # the same exposure under other published curves
    curves = {
        "paper": {"label": "McFarland et al. (as published)", "points": total},
        "lanphear": {"label": "Lanphear et al. 2005, from 2.4 ug/dL", "points": points(lanphear)},
        "lanphear_early": {"label": "Lanphear et al. 2005, early childhood, from 4.1 ug/dL",
                           "points": points(lanphear_early)},
        "crump": {"label": "Crump et al. 2013, no threshold", "points": points(crump)},
    }
    for k in curves:
        curves[k]["per_person"] = curves[k]["points"] / alive
    curves["lanphear"]["peak5_mean"] = sum(n * lanphear(b) for c in range(1966, 1971) for b, n in pop[c].items()) \
        / by[(1966, 1970)]["pop"]
    curves["lanphear_early"]["peak5_mean"] = sum(n * lanphear_early(b) for c in range(1966, 1971)
                                                 for b, n in pop[c].items()) / by[(1966, 1970)]["pop"]
    curves["crump"]["peak5_mean"] = sum(n * crump(b) for c in range(1966, 1971) for b, n in pop[c].items()) \
        / by[(1966, 1970)]["pop"]
    curves["paper"]["peak5_mean"] = by[(1966, 1970)]["mean"]
    # what the paper's own curve gives with the 0-4.9 band charged at its mid-point (2.5 x 0.513)
    low = 2.5 * 0.513
    curves["paper_low"] = {"label": "McFarland curve, 0-4.9 band charged", "points": total + low * sum(
        pop[c]["0-4.9"] for c in years)}

    # the top of the distribution, an illustration (see docstring)
    z = NormalDist(100, 15)
    cut = 130
    base = 1 - z.cdf(cut)
    ys = range(1966, 1971)
    n = by[(1966, 1970)]["pop"]
    shifted = sum(v * (1 - z.cdf(cut + loss[b])) for c in ys for b, v in pop[c].items()) / n
    below70 = sum(v * z.cdf(70 + loss[b]) for c in ys for b, v in pop[c].items()) / n
    tail = {"cut": cut, "base_share": base, "share_1966_70": shifted, "fewer": 1 - shifted / base, "pop": n,
            "n_base": base * n, "n_shifted": shifted * n,
            "below70_base": z.cdf(70), "below70_1966_70": below70}

    gas = S.gasoline()
    gpeak = max(gas, key=lambda r: r["tonnes"])
    # McFarland's NHANES calibration runs 1976-93; the years before it with more additive lead than any year in it
    cal_max = max(r["tonnes"] for r in gas if r["year"] >= 1976)
    above_cal = [r["year"] for r in gas if r["year"] < 1976 and r["tonnes"] > cal_max]
    gtot = sum(r["tonnes"] for r in gas)
    g = {r["year"]: r["tonnes"] for r in gas}

    b1 = S.epa_b1()
    first, last = b1[0], b1[-1]

    lr = S.larsen_regions()
    world = next(r for r in lr if r["name"] == "Worldwide")
    lmic = next(r for r in lr if r["name"] == "Low and middle income")
    regions = sorted([r for r in lr if r["group"].startswith("region")], key=lambda r: -r["iq_m"])

    return {
        "source_note": "McFarland, Hauer and Reuben 2022 (PNAS), SI Datasets S01 and S03; Bureau of Mines; EPA; "
                       "Larsen and Sanchez-Triana 2023",
        "us": {"total": total, "alive_2015": alive,
               "born_before": round(sum(sum(pop[c].values()) for c in pop if c < FIRST)), "per_person": total / alive, "n_ge5": n_ge5,
               "share_ge5": n_ge5 / alive, "band_loss": loss, "per_year": per_year, "fives": fives,
               "peak5": peak5, "peak1": peak1, "mid_century": mid_century,
               "mid_century_share": mid_century["points"] / total},
        "curves": curves,
        "tail": tail,
        "gasoline": {"series": [{"year": r["year"], "tonnes": r["tonnes"]} for r in gas], "peak_year": gpeak["year"],
                     "peak_tonnes": gpeak["tonnes"], "total_tonnes": gtot, "first": gas[0]["year"], "last": gas[-1]["year"],
                     "t1980": g[1980], "t1986": g[1986], "fall_1970_1986": 1 - g[1986] / g[1970],
                     "cal_max": cal_max, "above_cal": above_cal},
        "blood": {"rows": b1, "first": first, "last": last, "median_ratio": first["median"] / last["median"]},
        "world": {"total_m": world["iq_m"], "lo": world["lo"], "hi": world["hi"], "lmic_m": lmic["iq_m"],
                  "lmic_share": lmic["iq_m"] / world["iq_m"], "regions": regions},
    }


def main():
    P = build()
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1, sort_keys=True)
        f.write("\n")
    u, c, t = P["us"], P["curves"], P["tail"]
    print(f"total {u['total']:,.0f} points, {u['per_person']:.2f} per person, {u['share_ge5']:.1%} at >=5 ug/dL")
    print(f"peak 5-yr {u['peak5']['from']}-{u['peak5']['to']} {u['peak5']['mean']:.2f}; peak year {u['peak1']['cohort']} "
          f"{u['peak1']['mean']:.2f}; 1951-80 share {u['mid_century_share']:.1%}")
    for k, v in c.items():
        print(f"  curve {k}: {v['points'] / 1e6:,.0f} M points" + (f", 1966-70 mean {v['peak5_mean']:.2f}" if "peak5_mean" in v else ""))
    print(f"tail >130: {t['base_share']:.2%} -> {t['share_1966_70']:.2%} ({t['fewer']:.0%} fewer); <70: "
          f"{t['below70_base']:.2%} -> {t['below70_1966_70']:.2%}")
    g = P["gasoline"]
    print(f"gasoline peak {g['peak_year']} {g['peak_tonnes']:,.0f} t; total {g['total_tonnes'] / 1e6:.2f} Mt {g['first']}-{g['last']}")
    b = P["blood"]
    print(f"blood median {b['first']['median']} ({b['first']['period']}) -> {b['last']['median']} ({b['last']['period']})")
    w = P["world"]
    print(f"world {w['total_m']:.0f} M ({w['lmic_share']:.1%} LMIC)")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
