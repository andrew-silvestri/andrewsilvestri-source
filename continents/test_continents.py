"""This project's own failure modes.

Each of these is something that would produce a confident, plausible, wrong
page rather than an error, which is why it gets a test rather than a comment.

 1. The longitude trap, positive. The four future grids are read on the
    convention each one declares, so they agree with an ordinary world map.
 2. The longitude trap, NEGATIVE CONTROL. Read without normalising, they
    still manufacture a large fake disagreement. A check never seen to fail
    is not known to work, and if a future release harmonises the conventions
    the page's account of the trap becomes false and must be rewritten.
 3. The plate gates, positive. Every fitted rotation matches ITRF2020-PMM as
    a vector, and no retained station is wildly out.
 4. The plate trap, NEGATIVE CONTROL. Before exclusion the Pacific still
    disagrees with ITRF2020-PMM. If the source file ever reassigns the
    Hawaiian stations, the exclusion machinery would quietly stop doing any
    work while every positive gate still passed.
 5. The exclusion is a rule, not a list. Re-running the stated rule
    reproduces the excluded set, and that set contains the Big Island
    stations, the western Alaska stations and ILSG.
 6. The weak gate is still weak. The station-level check can still be fooled
    by a rotation wrong by a large fraction of its own rate, which is why the
    gate on the rotation vector exists. If this ever stops being true the
    reasoning on the page is out of date.
 7. Reconstructions return the present at age 0. The only known answer this
    regime has, and the whole defence against a swapped coordinate order.
 8. No sentinel became a distance, and models still decline to place crust.
 9. The pinned model set is what shipped.
10. The artificial polar mask is excluded from every area statistic.
11. The page equals the payload.
12. Nothing on the page is unsourced.

Run:  python3 test_continents.py
"""
import json
import math
import os
import re
import sys
import zipfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import otis_grid as og            # noqa: E402
import plates as P                # noqa: E402
import build_continents as B      # noqa: E402

PAYLOAD = os.path.join(HERE, "outputs", "continents_payload.json")
PAGE = os.path.join(ROOT, "site", "continents.html")
ZIP = os.path.join(ROOT, "site", "downloads", "continents-code.zip")


def main():
    if not os.path.exists(PAYLOAD):
        print("run build_continents.py first")
        return 1
    D = json.load(open(PAYLOAD, encoding="utf-8"))
    fails = []
    anch = {a["id"]: a for a in D["anchors"]}
    masks, shape = B.load_masks()

    # 1 ----------------------------------------------------------------
    fake = {s: {"n": shape[0], "m": shape[1], "lons": (-180.0, 180.0),
                "lats": (-90.0, 90.0), "mz": np.where(masks[s][0], 0, 1)}
            for s in B.SCENARIOS}
    rows = {r[0]: r for r in og.anchor_check(fake, strict=False)}
    lands = [og.land_percent(g) for g in fake.values()]
    ok1 = rows["A1"][4] and rows["A2"][4]
    if not ok1:
        fails.append("1. the future grids disagree with an ordinary world map")
    print(f"  1. probes {rows['A1'][3]}, land "
          f"{min(lands):.2f}-{max(lands):.2f} % (Earth is "
          f"{og.EARTH_LAND_FRACTION})")

    # 2 ----------------------------------------------------------------
    naive = D["future"]["naive_max_disagreement_pct"]
    t0 = D["future"]["t0_agreement_pct"]
    nc = D["provenance"]["osf"]["negative_control"]
    ok2 = naive >= 25.0 and nc["probes_wrong"] > 0
    if not ok2:
        fails.append("2. the naive read no longer manufactures a "
                     "disagreement; the page's account of the trap is stale")
    print(f"  2. naive t=0 disagreement {naive:.2f} % and "
          f"{nc['probes_wrong']} of {nc['probes_total']} probes wrong "
          f"(normalised {t0:.2f} %)")

    # 3 ----------------------------------------------------------------
    worst_om = max(r["d_omega_deg_myr"] for r in D["present"]["plates"])
    worst_st = max(r["max_residual_mm_yr"] for r in D["present"]["plates"])
    ok3 = worst_om <= B.B1A_TOL and worst_st <= B.B2_TOL
    if not ok3:
        fails.append(f"3. a fitted rotation is out by {worst_om:.4f} deg/Myr "
                     f"or a station by {worst_st:.2f} mm/yr")
    print(f"  3. worst rotation vs ITRF {worst_om:.4f} deg/Myr "
          f"(<= {B.B1A_TOL}), worst station {worst_st:.2f} mm/yr "
          f"(<= {B.B2_TOL})")

    # 4 ----------------------------------------------------------------
    pa = D["present"]["pacific"]
    ok4 = pa["before"]["itrf_diff_mm_yr"] >= B.B4_FLOOR
    if not ok4:
        fails.append("4. the Pacific no longer disagrees before exclusion, so "
                     "the exclusion is doing no work and the page says it is")
    print(f"  4. Pacific before exclusion {pa['before']['itrf_diff_mm_yr']} "
          f"mm/yr, after {pa['after']['itrf_diff_mm_yr']} "
          f"(>= {B.B4_FLOOR} required before)")

    # 5 ----------------------------------------------------------------
    st = [s for s in P.load_stations()
          if s["dur"] >= P.MIN_YEARS and s["sve"] <= P.MAX_SIGMA
          and s["svn"] <= P.MAX_SIGMA and s["plate"] == "PA"]
    bp = P.boundary_points(os.path.join(HERE, "data",
                                        "PB2002_boundaries.json"))
    d = P.distance_to_boundary([s["lat"] for s in st],
                               [s["lon"] for s in st], bp)
    far = [s for s, dd in zip(st, d) if dd > P.FAR_KM]
    _om, _kept, dropped, _it = P.fit_with_exclusions(far)
    got = {x["sta"] for x in dropped}
    want = {r["sta"] for r in D["present"]["excluded"] if r["plate"] == "PA"}
    big = sum(1 for x in dropped if 18.8 <= x["lat"] <= 20.4
              and -156.2 <= x["lon"] <= -154.7)
    ak = sum(1 for x in dropped if x["lat"] > 50)
    ok5 = got == want and big >= 10 and ak == 4 and "ILSG" in got
    if not ok5:
        fails.append("5. the exclusion rule no longer reproduces the "
                     "excluded set named in the payload")
    print(f"  5. rule drops {len(got)} of {len(far)} Pacific stations: "
          f"{big} Big Island, {ak} above 50 N, ILSG "
          f"{'yes' if 'ILSG' in got else 'NO'}")

    # 6 ----------------------------------------------------------------
    br = D["b1_break"]
    ok6 = br["share_of_rate_pct"] >= 20.0
    if not ok6:
        fails.append("6. the station-level check can no longer be fooled, so "
                     "the page's reason for checking the rotation vector is "
                     "out of date")
    print(f"  6. {br['name']}'s rotation can move {br['movable_deg_myr']:.3f} "
          f"deg/Myr ({br['share_of_rate_pct']:.0f} % of its rate) inside the "
          f"{br['station_check_mm_yr']} mm/yr station check")

    # 7 ----------------------------------------------------------------
    ok7 = D["past"]["identity_worst_km"] <= B.C2_TOL
    if not ok7:
        fails.append("7. a model did not return the point it was given at "
                     "age 0; the coordinate order may have changed")
    print(f"  7. identity at age 0, worst "
          f"{D['past']['identity_worst_km']:.3f} km (<= {B.C2_TOL})")

    # 8 ----------------------------------------------------------------
    bad = 0
    for row in D["past"]["spread"]:
        for pl in row["places"]:
            for k in ("max_km", "median_km"):
                v = pl[k]
                if v is not None and (v < 0 or v > D["antipodal_km"] + 1):
                    bad += 1
    ok8 = bad == 0 and D["past"]["no_crust_cases"] > 0
    if not ok8:
        fails.append("8. a sentinel reached a distance, or no model declines "
                     "to place crust anywhere")
    print(f"  8. {D['past']['no_crust_cases']} no-crust cases, {bad} "
          "impossible distances")

    # 9 ----------------------------------------------------------------
    cache = json.load(open(os.path.join(HERE, "data", "gplates_cache.json"),
                           encoding="utf-8"))
    listed = {x.lower() for x in cache["model_list"]}
    ok9 = all(m["name"].lower() in listed for m in D["past"]["models"])
    if not ok9:
        fails.append("9. the pinned model set is not what the service served")
    print(f"  9. {len(D['past']['models'])} models pinned, list matches, "
          f"fetched {D['past']['fetched']}")

    # 10 ---------------------------------------------------------------
    lat = -90.0 + 0.25 * np.arange(shape[1])
    w = og.area_weights(lat)
    beyond = float(w[np.abs(lat) > D["cuts"]["polar_cut_deg"]].sum())
    ok10 = beyond == 0.0
    if not ok10:
        fails.append("10. the artificial polar mask is being counted")
    print(f"  10. weight beyond {D['cuts']['polar_cut_deg']:.0f} degrees: "
          f"{beyond:.1f}")

    # 11 ---------------------------------------------------------------
    ok11 = os.path.exists(PAGE)
    if ok11:
        import update_page
        rendered, probs = update_page.cite(update_page.render(D))
        shipped = open(PAGE, encoding="utf-8").read()
        ok11 = rendered == shipped and not probs
        if not ok11:
            fails.append("11. the page does not equal the payload rendered "
                         "through the template" + (f"; {probs}" if probs else ""))
    else:
        fails.append("11. site/continents.html has not been written")
    print(f"  11. page: {'matches the payload' if ok11 else 'DOES NOT MATCH'}")

    # 12 ---------------------------------------------------------------
    prov = D["provenance"]
    need = ["ngl", "osf", "static"]
    ok12 = all(k in prov for k in need) and all(
        prov[k].get("licence") or prov[k].get("morvel") for k in need)
    if not ok12:
        fails.append("12. a source is missing its provenance or licence")
    print(f"  12. provenance for {len(need)} sources, "
          f"{len(D['anchors'])} gates recorded with thresholds")

    # 13 ---------------------------------------------------------------
    if os.path.exists(ZIP):
        names = zipfile.ZipFile(ZIP).namelist()
        forbidden = [n for n in names
                     if "/data/raw/" in "/" + n or n.endswith(".png")]
        ok13 = not forbidden
        if not ok13:
            fails.append(f"13. the download ships {forbidden[:3]}")
        print(f"  13. continents-code.zip: {len(names)} members, "
              f"{len(forbidden)} forbidden")
    else:
        print("  13. continents-code.zip not built yet, skipped")

    print("")
    if fails:
        print("FAIL")
        for f in fails:
            print("  - " + f)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
