"""
Build outputs/economy_payload.json: every number site/economy.html states.

Four blocks, and the page's three labels map onto them exactly:

  computed    the elasticity curve, the time a saving buys, the two routes to
              the transfer coefficient, the compounding null, and the two
              cohort checks. All arithmetic over published coefficients or
              over the two CC BY tables in data/.
  looked_up   figures quoted from papers and never recomputed here. Each
              carries a source string with a DOI.
  assumed     the three places this page extends a measurement past what was
              measured. The template renders these as labelled assumptions.
  provenance  run date, versions, file hashes.

Every entry that carries a number carries a "source". test_economy.py fails
the build if one does not, and fails it if a source names a book: the
copyright rule for this project is that nothing comes from a training manual,
so nothing may cite one.

Run:  python3 build_economy.py
"""

import datetime
import hashlib
import json
import math
import os
import sys

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import model as M                                              # noqa: E402

DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "outputs")
PAYLOAD = os.path.join(OUT, "economy_payload.json")

# The paces the page speaks about, chosen to span the readership: a 4:30
# marathon, a 3:21, a 2:56, a 2:36, and the 2:03 that was the world record
# when Kipp et al. wrote. Kept here so the figure and the prose cannot drift.
PACES = (2.60, 3.00, 3.50, 4.00, 4.50, 5.00, 5.50, 5.72)
SAVINGS = (0.01, 0.02, 0.03, 0.04, 0.05)
HEADLINE_SAVING = 0.04


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy)


# ---------------------------------------------------------------- curve ----
def elasticity_block():
    """The elasticity of speed to metabolic cost, across the readership's
    paces, for every published curve. The primary curve carries the page's
    numbers; the others are drawn beside it so the reader sees that the
    choice of curve moves the answer, and by how much."""
    grid = [round(2.20 + 0.02 * i, 2) for i in range(int((6.00 - 2.20) / 0.02) + 1)]
    curves = {}
    for key, c in M.CURVES.items():
        curves[key] = {
            "label": c["label"], "note": c["note"], "primary": c["primary"],
            "coef": list(c["coef"]),
            "elasticity": [M.elasticity(v, key) for v in grid],
            "source": M.CURVE_SOURCE,
        }
    # where the primary curve crosses 1: the pace at which a saving is worth
    # exactly itself, and below which it is worth more
    lo, hi = 2.2, 4.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if M.elasticity(mid) > 1:
            lo = mid
        else:
            hi = mid
    crossing = (lo + hi) / 2
    spread = [(min(M.elasticity(v, k) for k in M.CURVES),
               max(M.elasticity(v, k) for k in M.CURVES)) for v in grid]
    return {
        "grid_ms": grid, "curves": curves,
        "crossing_ms": crossing,
        "crossing_marathon_s": M.marathon_seconds(crossing),
        "spread_at_headline": {
            "v": 4.00,
            "lo": min(M.elasticity(4.00, k) for k in M.CURVES),
            "hi": max(M.elasticity(4.00, k) for k in M.CURVES),
        },
        "spread_band": spread,
        "source": M.CURVE_SOURCE,
    }


def paces_block():
    rows = []
    for v in PACES:
        base = M.marathon_seconds(v)
        gains = {}
        for s in SAVINGS:
            v2 = M.speed_for_saving(v, s)
            gains[f"{s:.2f}"] = {
                "speed_pct": 100 * (v2 / v - 1),
                "saved_s": base - M.marathon_seconds(v2),
            }
        rows.append({
            "v_ms": v,
            "marathon_s": base,
            "marathon_hms": M.hms(base),
            "vo2_ml_kg_min": M.vo2(v),
            "cost_ml_kg_km": M.cost_per_km(v),
            "drag_share": M.drag_share(v),
            "elasticity": M.elasticity(v),
            "gain": gains,
        })
    return {"rows": rows, "savings": list(SAVINGS),
            "headline_saving": HEADLINE_SAVING, "source": M.CURVE_SOURCE}


def transfer_block():
    meas = M.transfer_measured()
    mod = M.transfer_modelled()
    return {
        "measured": meas, "modelled": mod,
        "difference": abs(meas["value"] - mod["value"]),
        "reconciliation_source": M.HOOGKAMER_2016["speed_source"],
        "naive_pct": 100 * HEADLINE_SAVING,
        "honest_pct": 100 * M.speed_gain(4.00, HEADLINE_SAVING),
    }


# --------------------------------------------------------------- cohorts ---
def lanferdini():
    """Does the product predict performance better than its terms?

    n = 20 recreational men. The performance model's terms are VO2max, the
    fraction of it held at the second ventilatory threshold, and the oxygen
    cost of a kilometre; the response is 3000 m speed. Economy here is VO2 at
    16 km/h, which divided by 16 is ml/kg per km."""
    path = os.path.join(DATA, "lanferdini_2020_table1.xlsx")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    hdr = rows[2]
    col = {h: i for i, h in enumerate(hdr) if h}
    data = [r for r in rows[3:] if r and isinstance(r[0], (int, float))]
    get = lambda r, k: float(r[col[k]])                          # noqa: E731
    t3k = [get(r, "3000m performance (s)") for r in data]
    vo2max = [get(r, "VO2max (ml/kg/min)") for r in data]
    vt2 = [get(r, "VT2 (ml/kg/min)") for r in data]
    re16 = [get(r, "RE16 (ml/kg/min)") for r in data]
    speed = [3000.0 / t for t in t3k]                            # m/s
    # VO2 at 16 km/h in ml/kg/min -> ml/kg/km: multiply by 60 minutes per hour
    # and divide by the 16 km covered in that hour.
    cost_km = [r * 60.0 / 16.0 for r in re16]
    frac = [a / b for a, b in zip(vt2, vo2max)]
    prod_vt2 = [a / b for a, b in zip(vt2, cost_km)]
    prod_max = [a / b for a, b in zip(vo2max, cost_km)]
    corr = {
        "ceiling": {"r": pearson(vo2max, speed),
                    "what": "VO2max alone"},
        "economy": {"r": pearson(cost_km, speed),
                    "what": "oxygen cost of a kilometre alone, so a negative "
                            "correlation is the expected direction"},
        "fraction": {"r": pearson(frac, speed),
                     "what": "the share of VO2max held at the second "
                             "ventilatory threshold, alone"},
        "product_vt2": {"r": pearson(prod_vt2, speed),
                        "what": "threshold uptake divided by cost"},
        "product_max": {"r": pearson(prod_max, speed),
                        "what": "VO2max divided by cost: the model's form"},
        "v_vo2max": {"r": pearson([get(r, "vVO2max (km/h)") for r in data], speed),
                     "what": "measured velocity at VO2max, for comparison"},
    }
    # VO2max / cost is km per minute; 1000/60 converts it to m/s so it can be
    # compared with the measured 3000 m speed. Getting this factor wrong would
    # silently rescale the "share of the ceiling" the page quotes, so
    # test_economy.py checks the result lands inside a plausible band.
    ceiling_speed = [p * 1000.0 / 60.0 for p in prod_max]
    share = [s / p for s, p in zip(speed, ceiling_speed)]
    return {
        "n": len(data),
        "t3000_s": {"min": min(t3k), "max": max(t3k)},
        "vo2max": {"min": min(vo2max), "max": max(vo2max)},
        "cost_ml_kg_km": {"min": min(cost_km), "max": max(cost_km)},
        "fraction": {"min": min(frac), "max": max(frac)},
        "correlations": corr,
        "points": [{"speed_ms": s, "ceiling": a, "cost": c, "fraction": f,
                    "product": p}
                   for s, a, c, f, p in zip(speed, vo2max, cost_km, frac, prod_max)],
        "share_of_ceiling_over_cost": {"mean": sum(share) / len(share),
                                       "min": min(share), "max": max(share)},
        "source": ("Lanferdini et al., Frontiers in Physiology 11:979, 2020, "
                   "doi:10.3389/fphys.2020.00979, Supplementary Table 1, CC BY 4.0"),
    }


def vickers():
    """How far the sustainable fraction falls between a 5 km and a marathon,
    in 2,303 recreational runners, and the endurance exponent that describes
    it."""
    path = os.path.join(DATA, "vickers_2016_master.xlsx")
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb[wb.sheetnames[0]]
    it = ws.iter_rows(values_only=True)
    hdr = next(it)
    c = {k: i for i, k in enumerate(hdr) if k}
    pairs = []
    for r in it:
        t5, tm = r[c["k5_ti"]], r[c["mf_ti"]]
        d5, dm = r[c["k5_d"]], r[c["mf_d"]]
        if all(isinstance(x, (int, float)) and x for x in (t5, tm, d5, dm)):
            pairs.append((float(t5), float(tm), float(d5), float(dm)))
    ratios = sorted((dm / tm) / (d5 / t5) for t5, tm, d5, dm in pairs)
    ks = sorted(math.log(tm / t5) / math.log(dm / d5) for t5, tm, d5, dm in pairs)
    q = lambda a, f: a[int(f * (len(a) - 1))]                    # noqa: E731
    by_speed = sorted(((d5 / t5), (dm / tm) / (d5 / t5)) for t5, tm, d5, dm in pairs)
    third = len(by_speed) // 3
    terciles = []
    for i, name in enumerate(("slowest third", "middle third", "fastest third")):
        seg = sorted(s[1] for s in by_speed[i * third:(i + 1) * third])
        terciles.append({"band": name, "median_ratio": seg[len(seg) // 2],
                         "n": len(seg)})
    return {
        "n_both": len(pairs),
        "ratio": {"median": q(ratios, .5), "q1": q(ratios, .25), "q3": q(ratios, .75),
                  "p5": q(ratios, .05), "p95": q(ratios, .95)},
        "riegel_k": {"median": q(ks, .5), "q1": q(ks, .25), "q3": q(ks, .75)},
        "terciles": terciles,
        "source": ("Vickers & Vertosick, BMC Sports Science, Medicine and "
                   "Rehabilitation 8:26, 2016, doi:10.1186/s13102-016-0052-y, "
                   "Additional file 2, CC BY 4.0"),
    }


# ------------------------------------------------------------- looked up ---
LOOKED_UP = {
    "joyner_1991": {
        "value": {"form": "marathon speed = VO2max x %VO2max at threshold x economy",
                  "best_case_hms": "1:57:58", "all_average_hms": "2:24:10",
                  "vo2max_inputs": [70, 77, 84], "fraction_inputs": [0.75, 0.80, 0.85],
                  "haircut_pct": 10},
        "source": ("Joyner, Journal of Applied Physiology 70(2):683-687, 1991, "
                   "doi:10.1152/jappl.1991.70.2.683"),
        "note": "the model's form and its published worked range; the flat 10% "
                "reduction covers wind resistance and drift",
    },
    "joyner_coyle_2008": {
        "value": {"vo2max_elite": [70, 85], "fraction_trained": [0.75, 0.90],
                  "economy_between_individuals_pct": [30, 40]},
        "source": ("Joyner & Coyle, Journal of Physiology 586(1):35-44, 2008, "
                   "doi:10.1113/jphysiol.2007.143834, PMC2375555"),
    },
    "coyle_1995": {
        "value": {"ceiling_explains_threshold_variance_pct": [31, 72]},
        "source": "Coyle, Exercise and Sport Sciences Reviews 23:25-63, 1995, PMID 7556353",
        "note": "why the three terms are not independent inputs",
    },
    "zanini_2025": {
        "value": {"n": 14, "economy_worse_pct_at_90min": 4.2,
                  "economy_worse_pct_at_120min": 5.8,
                  "vo2peak_fall_pct": [3.1, 7.1],
                  "threshold_speed_kmh": [14.0, 13.5, 13.0]},
        "source": ("Zanini, Folland & Blagrove, Scandinavian Journal of Medicine & "
                   "Science in Sports 35:e70076, 2025, PMC12082016"),
    },
    "hunter_2025": {
        "value": {"n": 18, "vo2max_before": 56.7, "vo2max_after": 53.4,
                  "threshold_speed_before_kmh": 12.8, "threshold_speed_after_kmh": 12.1,
                  "economy_change": "not significant",
                  "r_with_marathon_time": 0.68},
        "source": ("Hunter & Muniz-Pumares, European Journal of Sport Science "
                   "25:e70073, 2025, PMC12547624"),
    },
    "smyth_2020": {
        "value": {"n": 25000, "share_of_critical_speed_overall": 0.848,
                  "at_150_min": 0.930, "at_360_min": 0.789},
        "source": ("Smyth & Muniz-Pumares, Medicine & Science in Sports & Exercise "
                   "52(12):2637-2645, 2020, PMC7664951"),
        "note": "computed from Strava training data under a research licence; the "
                "data are not public, so these are quoted, not recomputed",
    },
    "jones_2024": {
        "value": {"predicted_hms": "1:55:05",
                  "critical_power_fall_pct": [8, 11],
                  "individual_range_pct": [0.4, 32]},
        "source": ("Jones, Journal of Physiology 602(17):4113-4128, 2024, "
                   "doi:10.1113/JP284205"),
        "note": "the argument that the three-term model omits durability",
    },
    "barnes_kilding_2015": {
        "value": {"elite_ml_kg_km": 180, "highly_trained_ml_kg_km": 190,
                  "recreational_ml_kg_km": [200, 210],
                  "typical_error_pct": [1.3, 5.0],
                  "smallest_worthwhile_change_pct": [2.2, 2.6]},
        "source": ("Barnes & Kilding, Sports Medicine - Open 1:8, 2015, PMC4555089"),
        "note": "economy norms at 16 km/h, and the measurement error a change "
                "has to clear",
    },
    "van_hooren_2024": {
        "value": {"studies": 51, "n": 1115,
                  "technique_explains_pct": [4, 12],
                  "contact_time_r": -0.02, "vertical_displacement_r": 0.35},
        "source": "Van Hooren et al., Sports Medicine 54:1269-1316, 2024, PMC11127892",
    },
    "footwear_spread": {
        "value": {"lab_comparisons": 12, "min_pct": 1.10, "max_pct": 4.20,
                  "median_pct": 2.82,
                  "individual_min_pct": -11.3, "individual_max_pct": 11.4},
        "source": ("collected in 03 RESEARCH/shoe/effects.json from thirteen papers; "
                   "the individual range is Knopp et al., Sports Medicine "
                   "53:1255-1271, 2023, PMC10185608"),
        "note": "quoted in one sentence only; the spread is the subject of a "
                "separate page and is not re-analysed here",
    },
}

ASSUMED = {
    "reference_runner": {
        "text": "The cost curve is fitted to a 58 kg runner 1.71 m tall with a "
                "0.45 square metre frontal area. A reader of another size has "
                "another curve, and the air term in particular scales with "
                "frontal area.",
        "source": M.CURVE_SOURCE,
    },
    "transfer_carries": {
        "text": "The measured transfer was obtained by adding mass over 3000 m "
                "in trained men. Applying it to a different intervention over a "
                "different distance is an extension of it, not a finding.",
        "source": M.HOOGKAMER_2016["source"],
    },
    "terms_move_alone": {
        "text": "The arithmetic moves one term with the others held still. In "
                "trained runners they are correlated, and the ceiling explains "
                "between 31 and 72 per cent of the variance in the threshold, so "
                "the independent case is a counterfactual rather than a "
                "prediction about a person.",
        "source": LOOKED_UP["coyle_1995"]["source"],
    },
}


def main():
    os.makedirs(OUT, exist_ok=True)
    ok, checks = M.check_paper_numbers()
    if not ok:
        sys.exit("  the transcribed coefficients do not reproduce the paper's own "
                 "stated results; nothing was written.")
    P = {
        "generated": datetime.date.today().isoformat(),
        "units": {"v": "m/s", "vo2": "ml/kg/min gross", "cost": "ml/kg/km",
                  "time": "seconds"},
        "reference_runner": M.REFERENCE_RUNNER,
        "paper_check": {"value": checks, "source": M.CURVE_SOURCE,
                        "note": "the three results Kipp et al. state, recomputed "
                                "from the transcribed coefficients"},
        "elasticity": elasticity_block(),
        "paces": paces_block(),
        "transfer": transfer_block(),
        "compounding": {
            "value": M.compounding_table(),
            "baseline_hms": "3:00:00",
            "source": LOOKED_UP["joyner_1991"]["source"],
            "note": "a null: the product exceeds the sum by less than a "
                    "percentage point at every gain a runner can make",
        },
        "lanferdini": lanferdini(),
        "vickers": vickers(),
        "looked_up": LOOKED_UP,
        "assumed": ASSUMED,
        "provenance": {
            "files": {n: digest(os.path.join(DATA, n))
                      for n in sorted(os.listdir(DATA)) if n.endswith(".xlsx")},
            "source": "computed by build_economy.py",
        },
    }
    with open(PAYLOAD, "w", encoding="utf-8") as fh:
        json.dump(P, fh, indent=1)
    e = P["elasticity"]
    t = P["transfer"]
    print(f"  paper check         3 of 3 reproduce, worst "
          f"{max(abs(c['diff_pp']) for c in checks):.4f} pp")
    print(f"  elasticity crosses 1 at {e['crossing_ms']:.2f} m/s "
          f"({M.hms(e['crossing_marathon_s'])} marathon)")
    print(f"  transfer            measured {t['measured']['value']:.3f}, "
          f"modelled {t['modelled']['value']:.3f}, apart by "
          f"{t['difference']:.3f}")
    print(f"  Lanferdini          n = {P['lanferdini']['n']}, product r = "
          f"{P['lanferdini']['correlations']['product_max']['r']:+.2f}, "
          f"economy alone r = {P['lanferdini']['correlations']['economy']['r']:+.2f}")
    print(f"  Vickers             n = {P['vickers']['n_both']}, median ratio "
          f"{P['vickers']['ratio']['median']:.3f}, k = "
          f"{P['vickers']['riegel_k']['median']:.2f}")
    print(f"  -> {os.path.relpath(PAYLOAD, HERE)}")


if __name__ == "__main__":
    main()
