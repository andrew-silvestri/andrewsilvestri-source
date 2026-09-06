"""
Everything site/shoes.html and the four figures state, computed from
data/studies.py and written to outputs/shoes_payload.json.

There is no model here and there is deliberately no fitting. The whole
computation is arithmetic over a table of published numbers: sort them, take
the extremes, count how many published a dispersion and how many did not,
measure how wide each individual range is and whether it crosses zero, and
divide one Hoogkamer 2016 row by the other to get the transfer coefficient.

The one derived quantity that is not a measurement is the predicted time
effect, which pushes the laboratory range through that coefficient. It
carries assumed=True through the payload and reaches the page as the word
"assumed" beside it, because the coefficient was measured for added mass over
3000 m and this applies it to a different intervention over a different
distance.

Run:  python3 build_shoes.py
"""

import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from data.studies import META, ROWS, STUDIES, TRANSFER_NOTE   # noqa: E402

OUT = os.path.join(HERE, "outputs", "shoes_payload.json")


def rows_of(family):
    return {k: v for k, v in ROWS.items() if v["family"] == family}


def dispersion_kind(r):
    """What this row published, in one word. Never both, never inferred."""
    if r.get("ci_pct") is not None and r.get("sd_pct") is not None:
        raise SystemExit(f"{r['comparison']!r} carries both an SD and a CI; "
                         "they are different quantities and the table may "
                         "only hold what the paper published")
    if r.get("ci_pct") is not None:
        return "ci"
    if r.get("sd_pct") is not None:
        return "sd"
    return "none"


def check_signs():
    """The sign convention, asserted at build time as well as in the test.

    An advanced-footwear row is a shoe helping and must be positive; a
    mass row is mass added and must be negative. HANDOFF §8 item 12 is the
    reason this is checked in two places rather than assumed once.
    """
    bad = []
    for k, r in ROWS.items():
        e = r.get("effect_pct")
        if e is None:
            continue
        if r["family"] == "aft" and e <= 0:
            bad.append(f"{k}: aft row is not positive ({e})")
        if r["family"] == "mass" and e >= 0:
            bad.append(f"{k}: mass row is not negative ({e})")
    if bad:
        raise SystemExit("sign convention violated:\n  " + "\n  ".join(bad))


def main():
    check_signs()

    # ---- the advanced-footwear comparisons, the spread ---------------------
    aft = []
    for k, r in sorted(rows_of("aft").items(),
                       key=lambda kv: -kv[1]["effect_pct"]):
        aft.append(dict(
            key=k, study=r["study"], colour=STUDIES[r["study"]]["colour"],
            label=STUDIES[r["study"]]["label"],
            comparison=r["comparison"], short=r["short"],
            effect_pct=r["effect_pct"], sd_pct=r.get("sd_pct"),
            ci_pct=r.get("ci_pct"), dispersion=dispersion_kind(r),
            n=r["n"], speed_kmh=r.get("speed_kmh"), setting=r["setting"],
            outdoor="outdoor" in r["setting"]))
    vals = [a["effect_pct"] for a in aft]
    n_sd = sum(1 for a in aft if a["dispersion"] == "sd")
    n_none = sum(1 for a in aft if a["dispersion"] == "none")

    spread = dict(
        n=len(aft), lo=min(vals), hi=max(vals),
        median=round(statistics.median(vals), 2),
        ratio=round(max(vals) / min(vals), 1),
        n_with_sd=n_sd, n_without=n_none,
        without_fraction=f"{n_none} of {len(aft)}")

    # ---- the individual ranges, and how much wider they are ----------------
    ind = []
    for k, r in ROWS.items():
        rng = r.get("individual_range_pct")
        if not rng:
            continue
        lo, hi = min(rng), max(rng)
        ind.append(dict(
            key=k, study=r["study"], colour=STUDIES[r["study"]]["colour"],
            label=STUDIES[r["study"]]["label"],
            group=r.get("individual_group") or r["short"],
            lo=lo, hi=hi, width=round(hi - lo, 2),
            spans_zero=lo < 0 < hi, n=r["n"]))
    ind.sort(key=lambda d: -d["width"])
    individual = dict(
        n=len(ind), rows=ind,
        widest=max(d["width"] for d in ind),
        n_spanning_zero=sum(1 for d in ind if d["spans_zero"]),
        studies=sorted({d["label"] for d in ind}))

    # ---- economy is not time ----------------------------------------------
    # The exchange rate between a metabolic saving and race time. It is worked
    # out, and reconciled against the cost-of-running curve, on the sibling
    # page site/economy.html; this recomputes it from the same two rows rather
    # than reading that project's payload, so neither project can break the
    # other, and test_shoes.py asserts the two agree.
    met = ROWS["hoogkamer2016_mass_metabolic"]
    tim = ROWS["hoogkamer2016_mass_time"]
    transfer = tim["effect_pct"] / met["effect_pct"]
    # Its own interval, from the two published confidence intervals: the
    # smallest time effect over the largest metabolic one, and the reverse.
    t_lo = min(abs(c) for c in tim["ci_pct"]) / max(abs(c) for c in met["ci_pct"])
    t_hi = max(abs(c) for c in tim["ci_pct"]) / min(abs(c) for c in met["ci_pct"])
    predicted = dict(
        lo=spread["lo"] * transfer, hi=spread["hi"] * transfer,
        assumed=True,
        note="The laboratory range pushed through the transfer coefficient. "
             "Assumed: the coefficient was measured for added mass over "
             "3000 m in trained men, not for advanced footwear over a "
             "marathon.")

    race = []
    for k, r in rows_of("race").items():
        race.append(dict(key=k, study=r["study"], short=r["short"],
                         lo=r["ci_pct"][0], hi=r["ci_pct"][1],
                         sex=r["sex"], assumed=False))
    race.sort(key=lambda d: -(d["hi"] - d["lo"]))

    # ---- the mass rows, and the contradiction ------------------------------
    mass = []
    for k, r in rows_of("mass").items():
        mass.append(dict(
            key=k, study=r["study"], label=STUDIES[r["study"]]["label"],
            short=r["short"], comparison=r["comparison"],
            effect_pct=r["effect_pct"], ci_pct=r.get("ci_pct"),
            dispersion=dispersion_kind(r), n=r["n"],
            measures=r.get("measures", "economy"),
            ratio_to_rule=round(abs(r["effect_pct"] / met["effect_pct"]), 1)))
    contradiction = [m for m in mass
                     if m["study"] == "rodrigocarranza2020"]

    # ---- what the table does not contain -----------------------------------
    all_rows = list(ROWS.values())
    limits = dict(
        n_rows=len(all_rows),
        n_female=sum(1 for r in all_rows
                     if r.get("sex") and "female" in r["sex"]),
        n_outdoor=sum(1 for r in all_rows
                      if "outdoor" in (r.get("setting") or "")),
        n_time=sum(1 for r in all_rows if r.get("measures") == "time"))

    payload = dict(
        spread=spread, aft=aft, individual=individual,
        transfer=dict(value=transfer, lo=t_lo, hi=t_hi,
                      metabolic=met["effect_pct"], metabolic_ci=met["ci_pct"],
                      time=tim["effect_pct"], time_ci=tim["ci_pct"],
                      note=TRANSFER_NOTE),
        predicted=predicted, race=race,
        mass=mass, contradiction=contradiction,
        limits=limits,
        meta={k: {kk: vv for kk, vv in v.items()} for k, v in META.items()},
        studies={k: {kk: vv for kk, vv in v.items()}
                 for k, v in STUDIES.items()},
        rows={k: {kk: vv for kk, vv in v.items()} for k, v in ROWS.items()})

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
        fh.write("\n")

    print(f"  {len(ROWS)} rows, {spread['n']} advanced-footwear comparisons")
    print(f"  spread            {spread['lo']:.2f}% to {spread['hi']:.2f}%  "
          f"({spread['ratio']}x, median {spread['median']:.2f}%)")
    print(f"  dispersion        {spread['n_with_sd']} published an SD, "
          f"{spread['n_without']} published none")
    print(f"  widest individual {individual['widest']:.2f} points, "
          f"{individual['n_spanning_zero']} of {individual['n']} span zero")
    print(f"  transfer          {transfer:.4f}  "
          f"-> predicted time {predicted['lo']:.2f}% to {predicted['hi']:.2f}% "
          f"(assumed)")
    print(f"  written           {os.path.relpath(OUT, HERE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
