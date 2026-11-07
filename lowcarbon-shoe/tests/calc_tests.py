"""Calculated tests (no physical test was done): energy return, outsole wear life,
mass. Each writes results/<name>.json with method, assumptions, result,
uncertainty and pass/fail against research/SPEC.md.

python calc_tests.py
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lca"))
import lca  # noqa: E402
import params as PR  # noqa: E402

OUT = os.path.join(HERE, "results")
RNG = np.random.default_rng(20261107)
N = 20000


def save(name, d):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".json"), "w", newline="\n") as f:
        json.dump(d, f, indent=1)


def energy_return():
    """T5: energy return >= 65 %. Shoe-level values are Hoogkamer et al. 2018
    (Sports Med 48:1009-1019, PMC5856879), Instron, heel, same protocol for all
    shoes. Material-level values are derived from Aimar et al. 2024 loss factors:
    return = 1 - pi*eta (first cycle -> 200,000 cycles)."""
    import math
    eta = {"EVA_F1": (0.1276, 0.0871), "ETPU_F3": (0.0568, 0.0373)}
    mat = {k: (round(100 * (1 - math.pi * a), 1), round(100 * (1 - math.pi * b), 1)) for k, (a, b) in eta.items()}
    d = dict(
        method="Published hysteresis: shoe-level (Hoogkamer 2018) and material-level (Aimar 2024, 1 - pi*eta). Calculated, not measured on LC-1.",
        shoe_level_pct=dict(EVA_trainer_Nike_Zoom_Streak_6=65.5, eTPU_Adidas_Adios_Boost_2=75.9, PEBA_Nike_prototype=87.0),
        material_level_pct_new_to_200k_cycles=mat,
        printed_TPU_lattice_pct=dict(range=[61, 77], confidence="low: one FDM open-cell study, abstract/snippet only (research/w1-10)"),
        baseline_pct=65.5, lc1_pct=75.9, lc1_range_pct=[75.9, mat["ETPU_F3"][0]],
        target_pct=65.0, passed=75.9 >= 65.0,
        note="LC-1's midsole is the same material class as the Adios Boost 2 midsole (expanded TPU beads); its geometry differs.")
    save("energy_return", d)
    return d


def wear():
    """T7: outsole wear life >= baseline. Wear depth per 100 km for rubber outsoles
    from Ohno et al. 2024 (23 pairs, forefoot hot spot: median 0.14, range
    0.07-0.56 mm/100 km; research/w2-04). TPU wears at a fraction r of rubber's
    volume rate, r from ISO 4649 volume loss: moulded TPU 25-40 mm3 against
    shoe-sole SBR 157 mm3 (r 0.16-0.25), widened to 0.6 for the recycled share
    (property loss on remelting, research/w2-05). ISO 4649 states it is for
    comparison only, so r is a ranking, not a prediction."""
    rate = np.exp(RNG.normal(np.log(0.14), 0.45, N)).clip(0.07, 0.56)  # mm/100 km, lognormal around the median
    r = RNG.triangular(0.16, 0.25, 0.60, N)
    t_base, t_lc1 = 3.0, 1.5
    life_b = 100 * t_base / rate
    life_l = 100 * t_lc1 / (rate * r)
    r_print = RNG.triangular(0.41, 0.52, 1.2, N)
    life_p = 100 * t_lc1 / (rate * r_print)
    pct = lambda v: {p: round(float(np.percentile(v, p))) for p in (5, 50, 95)}  # noqa: E731
    gpkm = 35.0  # mg per km per pair: Manabe et al. 2025's own rate for running shoes (walked and jogged, 92.4 km)
    d = dict(
        method=wear.__doc__.strip(),
        assumptions=dict(baseline_tread_mm=t_base, lc1_skin_mm=t_lc1, rate_mm_per_100km="lognormal, median 0.14, clipped 0.07-0.56",
                         tpu_to_rubber_ratio="triangular 0.16 / 0.25 / 0.60", printed_ratio="triangular 0.41 / 0.52 / 1.2 (FDM TPU 64-82 mm3, research/w2-04)"),
        wear_through_km=dict(baseline=pct(life_b), lc1=pct(life_l), home_printed=pct(life_p)),
        p_lc1_at_least_baseline=round(float(np.mean(life_l >= life_b)), 3),
        p_printed_at_least_baseline=round(float(np.mean(life_p >= life_b)), 3),
        particle_loss_g_per_100km_pair=dict(baseline=round(gpkm * 100 / 1000, 1),
                                            lc1=round(gpkm * 100 / 1000 * 0.25 * 1.2 / 1.15, 2),
                                            note="baseline: Manabe et al. 2025, running shoes, 35 mg/km per pair (measured); LC-1 scaled by r = 0.25 and density 1.20/1.15 (calculated)"),
        target="LC-1 wear-through distance >= baseline (median, same runner)",
        passed=bool(np.median(life_l / life_b) >= 1.0),
        caveat="Wet grip of a TPU outsole is untested; BASF rates standard TPU wet grip 'average' against rubber. A physical slip test is required (BUILD.md).")
    save("wear", d)
    return d


def mass():
    """T6: mass per shoe <= 300 g. LC-1 sole parts = CAD volume x density; upper
    rows from prototype/lca/params.py. Baseline = the BOM in params.py (research/w2-03)."""
    x = lca.central()
    vol = lca.load_volumes()
    sole = {r[0]: round(r[3], 1) for r in lca.lc1_sole_rows(x, vol)}
    upper = {r[0]: r[3] for r in PR.LC1_UPPER}
    lc1 = sum(sole.values()) + sum(upper.values())
    base = sum(r[3] for r in lca.rows_for(x, "baseline", vol))
    d0, dlo, dhi = PR.P["etpu_density"][:3]
    lo = sum(r[4] for r in PR.LC1_UPPER) + sum(sole.values()) - sole["Midsole (expanded TPU)"] * (1 - dlo / d0)
    hi = sum(r[5] for r in PR.LC1_UPPER) + sum(sole.values()) + sole["Midsole (expanded TPU)"] * (dhi / d0 - 1)
    d = dict(method=mass.__doc__.strip(), lc1_parts_g=dict(sole, **upper), lc1_g=round(lc1, 1),
             lc1_range_g=[round(lo, 1), round(hi, 1)], baseline_g=base,
             daily_trainer_range_g=[212, 282], target_g=300, passed=lc1 <= 300)
    save("mass", d)
    return d


if __name__ == "__main__":
    for f in (energy_return, wear, mass):
        d = f()
        print(f.__name__, {k: v for k, v in d.items() if k in ("passed", "lc1_pct", "wear_through_km", "lc1_g", "baseline_g", "lc1_range_g", "p_lc1_at_least_baseline")})
