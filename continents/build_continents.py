"""The model behind site/continents.html. Computes everything, gates it, then
writes outputs/continents_payload.json.

Order matters and is not negotiable: compute, gate, then write. A failed gate
leaves no payload on disk, so a figure cannot be drawn from a number that did
not pass. That is the whole design: the longitude trap in the future grids
would have produced a fabricated 34 per cent disagreement out of real files
with no symptom anywhere downstream, and the only thing that stops it is a
check that runs before the number exists.

Every gate runs here on the committed artefacts, even the ones the fetchers
already ran on the downloads, because the committed artefacts are what the
page is made from. It costs about two seconds.

Reads   data/stations.csv, data/PB2002_boundaries.json, data/ITRF2020-PMM.dat,
        data/nnr_morvel56.csv, data/future_masks.npz, data/osf_provenance.json,
        data/gplates_cache.json, data/ngl_provenance.json,
        data/static_provenance.json
Writes  outputs/continents_payload.json, outputs/stations_fit.csv

Run:  python3 build_continents.py
"""
import csv
import itertools
import json
import math
import os
import sys
from datetime import datetime, timezone

import numpy as np

import otis_grid as og
import plates as P

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "outputs")
PAYLOAD = os.path.join(OUT, "continents_payload.json")
FITCSV = os.path.join(OUT, "stations_fit.csv")

R_KM = 6371.0088
ANTIPODAL_KM = math.pi * R_KM          # 20,015 km, the ceiling on any spread

SCENARIOS = ("pun", "novon", "aurn", "amn")
SCEN_NAME = {"pun": "Pangaea Ultima", "novon": "Novopangaea",
             "aurn": "Aurica", "amn": "Amasia"}
COMMON_AGE = 200        # the only age all four scenarios reach
PLATE_ORDER = ("NA", "EU", "PA", "AU", "SA", "AF", "AN", "IN", "SO")
BANDS = ((0, 100), (100, 250), (250, 500), (500, 1000), (1000, 2000),
         (2000, 1e9))

# gates
B1A_TOL = 0.03          # deg/Myr, rotation vector against ITRF2020-PMM
B1B_TOL = 2.0           # mm/yr, p95 over the stations' extent
B1C_TOL = 1.5           # mm/yr, median at the stations
B2_TOL = 3.0            # mm/yr, worst single retained station
B4_FLOOR = 2.0          # mm/yr, the Pacific before exclusion
C2_TOL = 1.0            # km, identity at age 0

# the seven boundaries the geologic-against-geodetic comparison uses.
# (label, pair, lon, lat, morvel A, morvel B, itrf A, itrf B, ngl A, ngl B)
BOUNDARIES = (
    ("Peru-Chile trench",    "NZ-SA", -71.0, -23.0, "nz", "sa", "NAZC", "SOAM", None, "SA"),
    ("San Andreas",        "PA-NA", -120.5, 36.0, "pa", "na", "PCFC", "NOAM", "PA", "NA"),
    ("Himalaya",             "IN-EU",  85.0,  28.0, "in", "eu", "INDI", "EURA", "IN", "EU"),
    ("Mid-Atlantic",       "NU-SA", -13.0, -25.0, "nb", "sa", "NUBI", "SOAM", "AF", "SA"),
    ("SE Indian ridge",      "AU-AN", 120.0, -50.0, "au", "an", "AUST", "ANTA", "AU", "AN"),
    ("Zagros",               "AR-EU",  50.0,  32.0, "ar", "eu", "ARAB", "EURA", None, "EU"),
    ("East African rift",    "SM-NU",  36.0,  -2.0, "sm", "nb", "SOMA", "NUBI", "SO", "AF"),
)

EXTRAPOLATION_SITES = (
    ("Sydney", "AU", 151.21, -33.87), ("Nagpur", "IN", 79.09, 21.15),
    ("Kinshasa", "AF", 15.27, -4.44), ("Warsaw", "EU", 21.01, 52.23),
    ("Denver", "NA", -104.99, 39.74), ("Brasilia", "SA", -47.88, -15.79),
)

anchors = []


def gate(gid, what, threshold, measured, ok):
    anchors.append({"id": gid, "what": what, "threshold": threshold,
                    "measured": measured, "passed": bool(ok)})
    print(f"  {gid:4} {'ok  ' if ok else 'FAIL'}  {what}")
    print(f"       threshold {threshold}   measured {measured}")
    return ok


def gc_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * R_KM * math.asin(min(1.0, math.sqrt(h)))


# ------------------------------------------------------------------ regime 3

def load_masks():
    z = np.load(os.path.join(DATA, "future_masks.npz"))
    shape = tuple(int(v) for v in z["shape"])
    out = {}
    for k in z.files:
        if k == "shape":
            continue
        s, age = k.rsplit("_", 1)
        bits = np.unpackbits(z[k])[:shape[0] * shape[1]]
        out.setdefault(s, {})[int(age)] = bits.reshape(shape).astype(bool)
    return out, shape


def future_block(masks, shape, prov):
    lat = -90.0 + 0.25 * np.arange(shape[1])
    lon = -180.0 + 0.25 * np.arange(shape[0])
    w = (og.area_weights(lat) / shape[0])[None, :]

    fake = {s: {"n": shape[0], "m": shape[1], "lons": (-180.0, 180.0),
                "lats": (-90.0, 90.0), "mz": np.where(masks[s][0], 0, 1)}
            for s in SCENARIOS}
    rows = og.anchor_check(fake, strict=False)
    for r in rows:
        gate(r[0], r[1] + " [committed masks]", r[2], r[3], r[4])

    nc = prov["negative_control"]
    gate("A4", "negative control: reading the grids without normalising still "
         "manufactures a disagreement", nc["threshold"],
         f"{nc['naive_max_disagreement_pct']} % and {nc['probes_wrong']} of "
         f"{nc['probes_total']} probes wrong",
         nc["passed"] and nc["naive_max_disagreement_pct"] >= 25.0)

    ages = sorted(set.intersection(*[set(masks[s]) for s in SCENARIOS]))
    dis = []
    for age in ages:
        pairs = {}
        for a, b in itertools.combinations(SCENARIOS, 2):
            pairs[f"{a}/{b}"] = round(
                og.disagreement_percent(masks[a][age], masks[b][age], w), 2)
        dis.append({"age": age, "pairs": pairs,
                    "mean": round(float(np.mean(list(pairs.values()))), 2),
                    "max": round(max(pairs.values()), 2)})

    LATG = np.broadcast_to(lat[None, :], masks["pun"][0].shape)
    land = []
    for s in SCENARIOS + ("today",):
        m = masks["pun"][0] if s == "today" else masks[s][COMMON_AGE]
        tot = float((m * w).sum())
        land.append({
            "scenario": "today" if s == "today" else SCEN_NAME[s],
            "age": 0 if s == "today" else COMMON_AGE,
            "land_pct": round(tot * 100, 1),
            "north_pct": round(float((m * w * (LATG > 0)).sum()) / tot * 100, 0),
            "within_30_pct": round(
                float((m * w * (np.abs(LATG) <= 30)).sum()) / tot * 100, 0),
            "above_60N_land_pct": round(
                float((m * w * (LATG > 60)).sum())
                / float((w * (LATG > 60)).sum()) * 100, 0),
            "below_60S_land_pct": round(
                float((m * w * (LATG < -60)).sum())
                / float((w * (LATG < -60)).sum()) * 100, 0),
        })

    LON, LAT = np.meshgrid(lon, lat, indexing="ij")
    cen, proxy = [], []
    for age in ages:
        pts = {}
        for s in SCENARIOS:
            ww = w * masks[s][age]
            la_r, lo_r = np.radians(LAT), np.radians(LON)
            x = float((np.cos(la_r) * np.cos(lo_r) * ww).sum())
            y = float((np.cos(la_r) * np.sin(lo_r) * ww).sum())
            z = float((np.sin(la_r) * ww).sum())
            tot = float(ww.sum())
            clat = math.degrees(math.atan2(z, math.hypot(x, y)))
            clon = math.degrees(math.atan2(y, x))
            pts[s] = (clon, clat)
            cen.append({"age": age, "scenario": SCEN_NAME[s],
                        "lat": round(clat, 2), "lon": round(clon, 2),
                        "concentration": round(
                            math.sqrt(x * x + y * y + z * z) / tot, 3)})
        proxy.append({"age": age, "max_centroid_km": round(max(
            gc_km(pts[a], pts[b])
            for a, b in itertools.combinations(SCENARIOS, 2)), 0)})

    return {
        "scenarios": [SCEN_NAME[s] for s in SCENARIOS],
        "common_age": COMMON_AGE,
        "ages": ages,
        "disagreement": dis,
        "land_distribution": land,
        "centroids": cen,
        "centroid_proxy": proxy,
        "t0_agreement_pct": round(max(
            og.disagreement_percent(masks[a][0], masks[b][0], w)
            for a, b in itertools.combinations(SCENARIOS, 2)), 2),
        "naive_max_disagreement_pct": nc["naive_max_disagreement_pct"],
        "polar_cut_deg": og.POLAR_CUT,
        "licence": prov["licence"],
    }


# ------------------------------------------------------------------ regime 1

def present_block():
    st = P.load_stations()
    n_all = len(st)
    kept = [s for s in st if s["dur"] >= P.MIN_YEARS
            and s["sve"] <= P.MAX_SIGMA and s["svn"] <= P.MAX_SIGMA]
    with_plate = [s for s in kept if s["plate"]]
    bp = P.boundary_points()
    d = P.distance_to_boundary([s["lat"] for s in with_plate],
                               [s["lon"] for s in with_plate], bp)
    for s, dd in zip(with_plate, d):
        s["dist_km"] = float(dd)

    by = {}
    for s in with_plate:
        by.setdefault(s["plate"], []).append(s)

    itrf = P.load_itrf()
    fits, excluded, itrf_rows, all_res = {}, [], [], []
    pacific = {}
    for code in PLATE_ORDER:
        ss = by.get(code, [])
        far = [x for x in ss if x["dist_km"] > P.FAR_KM]
        if len(far) < P.MIN_STATIONS:
            continue
        om0, _, _ = P.fit(far)
        before = P.compare_to_itrf(om0, itrf[P.ITRF_CODE[code]], far)
        r0 = P.residuals(far, om0)
        om, keep, drop, iters = P.fit_with_exclusions(far)
        cmp = P.compare_to_itrf(om, itrf[P.ITRF_CODE[code]], keep)
        res = P.residuals(keep, om)
        fits[code] = {"omega": om, "kept": keep, "dropped": drop}
        pla, plo, prate = P.pole_of(om)
        ila, ilo, irate = P.pole_of(itrf[P.ITRF_CODE[code]])
        itrf_rows.append({
            "plate": code, "name": P.PLATE_NAME[code],
            "itrf_code": P.ITRF_CODE[code],
            "n_far": len(far), "n_kept": len(keep), "n_dropped": len(drop),
            "iterations": iters,
            "pole_lat": round(pla, 2), "pole_lon": round(plo, 2),
            "rate_deg_myr": round(prate, 4),
            "itrf_pole_lat": round(ila, 2), "itrf_pole_lon": round(ilo, 2),
            "itrf_rate_deg_myr": round(irate, 4),
            "d_omega_deg_myr": round(cmp["d_omega_deg_myr"], 4),
            "median_at_stations_mm_yr": round(cmp["median_at_stations_mm_yr"], 2),
            "p95_over_extent_mm_yr": round(cmp["p95_over_plate_mm_yr"], 2),
            "median_residual_mm_yr": round(float(np.median(res)), 2),
            "rms_residual_mm_yr": round(float(np.sqrt((res ** 2).mean())), 2),
            "max_residual_mm_yr": round(float(res.max()), 2),
        })
        for x in drop:
            excluded.append({"sta": x["sta"], "plate": code,
                             "lat": round(x["lat"], 3), "lon": round(x["lon"], 3),
                             "residual_mm_yr": round(x["residual_mm_yr"], 1),
                             "iteration": x["iteration"],
                             "cut_mm_yr": round(x["cut_mm_yr"], 2)})
        if code == "PA":
            # The Big Island on its own. Its stations sit on Kilauea's south
            # flank, which moves for its own reasons; fitting them alone
            # returns something that is not a plate, and the figure says so
            # with this number rather than a typed one.
            bi = [x for x in far if 18.8 <= x["lat"] <= 20.4
                  and -156.2 <= x["lon"] <= -154.7]
            ombi, _, _ = P.fit(bi)
            bla, blo, brate = P.pole_of(ombi)
            pacific = {
                "big_island_only": {
                    "n": len(bi), "pole_lat": round(bla, 2),
                    "pole_lon": round(blo, 2),
                    "rate_deg_myr": round(brate, 3),
                    "median_residual_mm_yr": round(
                        float(np.median(P.residuals(bi, ombi))), 2)},
                "before": {"n": len(far),
                           "rms_mm_yr": round(float(np.sqrt((r0 ** 2).mean())), 2),
                           "max_mm_yr": round(float(r0.max()), 1),
                           "itrf_diff_mm_yr": round(
                               before["median_at_stations_mm_yr"], 2),
                           "d_omega_deg_myr": round(before["d_omega_deg_myr"], 4)},
                "after": {"n": len(keep),
                          "rms_mm_yr": round(float(np.sqrt((res ** 2).mean())), 2),
                          "max_mm_yr": round(float(res.max()), 2),
                          "itrf_diff_mm_yr": round(
                              cmp["median_at_stations_mm_yr"], 2),
                          "d_omega_deg_myr": round(cmp["d_omega_deg_myr"], 4)},
            }
        # residual of every station on this plate against the interior fit
        for x, rr in zip(ss, P.residuals(ss, om)):
            all_res.append((x, float(rr)))

    # gates B
    gate("B1a", "each fitted rotation VECTOR against ITRF2020-PMM's "
         "(break_b1.py: the station check alone does not pin this)",
         f"<= {B1A_TOL} deg/Myr",
         f"{max(r['d_omega_deg_myr'] for r in itrf_rows):.4f} deg/Myr worst",
         all(r["d_omega_deg_myr"] <= B1A_TOL for r in itrf_rows))
    gate("B1b", "velocity difference from ITRF2020-PMM sampled over the "
         "stations' extent, not at the stations",
         f"p95 <= {B1B_TOL} mm/yr",
         f"{max(r['p95_over_extent_mm_yr'] for r in itrf_rows):.2f} mm/yr worst",
         all(r["p95_over_extent_mm_yr"] <= B1B_TOL for r in itrf_rows))
    gate("B1c", "velocity difference from ITRF2020-PMM at the plate's own "
         "stations (the contamination check)",
         f"median <= {B1C_TOL} mm/yr",
         f"{max(r['median_at_stations_mm_yr'] for r in itrf_rows):.2f} mm/yr worst",
         all(r["median_at_stations_mm_yr"] <= B1C_TOL for r in itrf_rows))
    gate("B2", "worst single retained station; one bad station cannot move a "
         "weighted fit but does ruin the residual the page quotes",
         f"<= {B2_TOL} mm/yr",
         f"{max(r['max_residual_mm_yr'] for r in itrf_rows):.2f} mm/yr worst",
         all(r["max_residual_mm_yr"] <= B2_TOL for r in itrf_rows))
    worst_drop = max(r["n_dropped"] / r["n_far"] for r in itrf_rows)
    gate("B3", "the exclusion is a stated rule that converges, not a list of "
         "station names", f"converged, < {P.MAX_DROP_FRACTION:.0%} dropped",
         f"{worst_drop:.0%} worst, {max(r['iterations'] for r in itrf_rows)} "
         "iterations worst",
         worst_drop < P.MAX_DROP_FRACTION
         and all(r["iterations"] < P.MAX_ITER for r in itrf_rows))
    gate("B4", "negative control: the Pacific before exclusion still "
         "disagrees with ITRF2020-PMM", f">= {B4_FLOOR} mm/yr",
         f"{pacific['before']['itrf_diff_mm_yr']} mm/yr",
         pacific["before"]["itrf_diff_mm_yr"] >= B4_FLOOR)

    bands = []
    for lo, hi in BANDS:
        sel = [r for x, r in all_res if lo <= x["dist_km"] < hi]
        if sel:
            bands.append({"lo_km": lo, "hi_km": None if hi > 1e8 else hi,
                          "n": len(sel),
                          "median_mm_yr": round(float(np.median(sel)), 2),
                          "p90_mm_yr": round(float(np.percentile(sel, 90)), 2)})

    with open(FITCSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sta", "plate", "lat", "lon", "dist_km",
                    "residual_mm_yr", "kept"])
        keptset = {(c, x["sta"]) for c, v in fits.items() for x in v["kept"]}
        for x, rr in all_res:
            w.writerow([x["sta"], x["plate"], f"{x['lat']:.4f}",
                        f"{x['lon']:.4f}", f"{x['dist_km']:.1f}",
                        f"{rr:.3f}",
                        int((x["plate"], x["sta"]) in keptset)])

    return {
        "n_all": n_all, "n_after_cuts": len(kept),
        "n_with_plate": len(with_plate),
        "n_plates_fitted": len(itrf_rows),
        "n_plotted": len(all_res),
        "distance_bands": bands,
        "plates": itrf_rows,
        "excluded": sorted(excluded, key=lambda r: -r["residual_mm_yr"]),
        "pacific": pacific,
        "big_island_excluded": sum(
            1 for r in excluded if r["plate"] == "PA"
            and 18.8 <= r["lat"] <= 20.4 and -156.2 <= r["lon"] <= -154.7),
        "above_50N_excluded": sum(1 for r in excluded
                                  if r["plate"] == "PA" and r["lat"] > 50),
        "ilsg_excluded": any(r["sta"] == "ILSG" for r in excluded),
    }, fits


def b1_break_block(fits):
    """How far a rotation can be wrong while still passing the station check.

    Recorded in the payload so the page states a measured number rather than
    a remembered one. break_b1.py is the same experiment, standalone, with
    the reasoning written out.

    The station set of a plate covers a patch. The smallest right singular
    vector of the design matrix is the direction in rotation space along
    which the rotation moves without the velocities inside that patch
    moving, so pushing along it is the worst case the station check cannot
    see.
    """
    worst = None
    for code, f in fits.items():
        kept = f["kept"]
        la = [x["lat"] for x in kept]
        lo = [x["lon"] for x in kept]
        A = P.design(la, lo)
        _u, _sv, vt = np.linalg.svd(A, full_matrices=False)
        weak = vt[-1]
        om = f["omega"]
        e0, n0 = P.velocity(om, la, lo)
        lo_s, hi_s = 0.0, 1.0
        for _ in range(60):
            mid = (lo_s + hi_s) / 2.0
            e1, n1 = P.velocity(om + mid * weak * np.linalg.norm(om), la, lo)
            if float(np.median(np.hypot(e1 - e0, n1 - n0))) < B1C_TOL:
                lo_s = mid
            else:
                hi_s = mid
        d_om = float(np.linalg.norm(
            P.deg_per_myr(lo_s * weak * np.linalg.norm(om))))
        rate = P.pole_of(om)[2]
        if worst is None or d_om / rate > worst["share_of_rate"]:
            worst = {"plate": code, "name": P.PLATE_NAME[code],
                     "n": len(kept),
                     "movable_deg_myr": round(d_om, 4),
                     "plate_rate_deg_myr": round(rate, 4),
                     "share_of_rate": d_om / rate,
                     "station_check_mm_yr": B1C_TOL}
    worst["share_of_rate_pct"] = round(worst.pop("share_of_rate") * 100, 0)
    return worst


def geologic_block(fits):
    mv = {}
    for row in csv.DictReader(open(os.path.join(DATA, "nnr_morvel56.csv"),
                                   encoding="utf-8")):
        mv[row["abbrev"]] = P.omega_of(float(row["pole_lat"]),
                                       float(row["pole_lon"]),
                                       float(row["rate_deg_myr"]))
    itrf = P.load_itrf()
    rows = []
    for label, pair, lon, lat, ma, mb, ia, ib, na, nb in BOUNDARIES:
        out = {"boundary": label, "pair": pair, "lon": lon, "lat": lat}
        for key, src, a, b in (("morvel", mv, ma, mb), ("itrf", itrf, ia, ib),
                               ("midas", {k: v["omega"] for k, v in fits.items()},
                                na, nb)):
            if a in src and b in src:
                e, n = P.velocity(src[a] - src[b], [lat], [lon])
                sp = float(math.hypot(e[0], n[0]))
                az = math.degrees(math.atan2(e[0], n[0])) % 360
                out[key] = round(sp, 1)
                out[key + "_az"] = round(az, 0)
            else:
                out[key] = None
                out[key + "_az"] = None
        if out["morvel"] is not None and out["itrf"] is not None:
            e1, n1 = P.velocity(mv[ma] - mv[mb], [lat], [lon])
            e2, n2 = P.velocity(itrf[ia] - itrf[ib], [lat], [lon])
            out["gap_mm_yr"] = round(float(math.hypot(e1[0] - e2[0],
                                                      n1[0] - n2[0])), 1)
            # gap_mm_yr is the magnitude of a vector difference and is always
            # positive. Whether a boundary sped up or slowed down needs a
            # sign, and labelling the magnitude with one would say the SE
            # Indian ridge slowed when it did the opposite.
            out["speed_change_mm_yr"] = round(out["itrf"] - out["morvel"], 1)
        rows.append(out)
    return rows


def extrapolation_block(fits):
    rows = []
    for name, code, lon, lat in EXTRAPOLATION_SITES:
        if code not in fits:
            continue
        om = fits[code]["omega"]
        e, n = P.velocity(om, [lat], [lon])
        sp = float(math.hypot(e[0], n[0]))
        r, _e, _n = P.basis(lat, lon)
        axis = om / np.linalg.norm(om)
        row = {"site": name, "plate": code, "speed_mm_yr": round(sp, 1)}
        for myr in (10, 50, 100):
            th = float(np.linalg.norm(om)) * myr * 1e6
            rot = (r * math.cos(th) + np.cross(axis, r) * math.sin(th)
                   + axis * float(axis @ r) * (1 - math.cos(th)))
            gcd = math.acos(min(1.0, float(r @ rot) / P.R_EARTH ** 2)) \
                * P.R_EARTH / 1000.0
            row[f"gc_{myr}myr_km"] = round(gcd, 0)
            row[f"arc_{myr}myr_km"] = round(sp * myr, 0)
        rows.append(row)
    return rows


# ------------------------------------------------------------------ regime 2

def past_block():
    path = os.path.join(DATA, "gplates_cache.json")
    if not os.path.exists(path):
        sys.exit("build: data/gplates_cache.json is missing; run "
                 "fetch_gplates.py first.")
    c = json.load(open(path, encoding="utf-8"))
    models = [m["name"] for m in c["models"]]
    oldest = {m["name"]: m["oldest_ma"] for m in c["models"]}
    places = c["places"]
    ages = c["ages"]
    resp = c["responses"]

    def pt(model, age, i):
        r = resp.get(f"{model}@{age}")
        if not isinstance(r, list) or i >= len(r):
            return None
        p = r[i]
        if p is None or abs(p[0]) > 360 or abs(p[1]) > 90 \
                or abs(abs(p[0]) - c["sentinel"]) < 0.02:
            return None
        return p

    gate("C1", "the pinned model set is what the service served",
         f"{len(models)} models present", f"{len(models)} of {len(models)}",
         all(m.lower() in {x.lower() for x in c["model_list"]} for m in models))
    # Recomputed here from the cached responses, NOT read from the value
    # fetch_gplates.py recorded. break_gates.py caught that: swapping the
    # coordinate order in the cache left the recorded number innocent and the
    # gate passed on data it no longer described. A gate has to be computed
    # from the artefact the page is actually made from.
    ident, ident_where = 0.0, None
    for m in models:
        got = resp.get(f"{m}@0")
        if not isinstance(got, list):
            ident, ident_where = float("inf"), f"{m} has no age-0 response"
            break
        for (pl, p_got) in zip(places, got):
            if p_got is None or abs(p_got[0]) > 360 or abs(p_got[1]) > 90                     or abs(abs(p_got[0]) - c["sentinel"]) < 0.02:
                ident, ident_where = float("inf"), f"{m} {pl['name']} sentinel"
                continue
            dd = gc_km((pl["lon"], pl["lat"]), p_got)
            if dd > ident:
                ident, ident_where = dd, f"{m} {pl['name']}"
    gate("C2", "identity at age 0: every model returns the point it was given, "
         "recomputed from the cache rather than read from it. The only known "
         "answer this regime has, and the whole defence against a swapped "
         "coordinate order",
         f"<= {C2_TOL} km",
         f"{ident:.3f} km" + (f" ({ident_where})" if ident > 0.001 else ""),
         ident <= C2_TOL)

    tracks, spread, nocrust = [], [], 0
    for i, pl in enumerate(places):
        tr = {"place": pl["name"], "lon": pl["lon"], "lat": pl["lat"],
              "models": {}}
        for m in models:
            lats, lons = [], []
            for a in ages:
                p = pt(m, a, i) if a <= oldest[m] else None
                lats.append(None if p is None else round(p[1], 2))
                lons.append(None if p is None else round(p[0], 2))
            tr["models"][m] = {"lat": lats, "lon": lons}
        tracks.append(tr)

    for a in ages:
        row = {"age": a, "n_models_in_range": sum(1 for m in models
                                                  if a <= oldest[m])}
        per = []
        for i, pl in enumerate(places):
            pts = {m: pt(m, a, i) for m in models if a <= oldest[m]}
            miss = [m for m, p in pts.items() if p is None]
            nocrust += len(miss)
            have = {m: p for m, p in pts.items() if p is not None}
            if len(have) < 3:
                per.append({"place": pl["name"], "n": len(have),
                            "no_crust": len(miss), "max_km": None,
                            "median_km": None})
                continue
            ds = sorted(gc_km(have[x], have[y])
                        for x, y in itertools.combinations(sorted(have), 2))
            per.append({"place": pl["name"], "n": len(have),
                        "no_crust": len(miss),
                        "max_km": round(ds[-1], 0),
                        "median_km": round(ds[len(ds) // 2], 0)})
        vals = [p["max_km"] for p in per if p["max_km"] is not None]
        row["places"] = per
        row["max_km"] = round(max(vals), 0) if vals else None
        row["min_of_max_km"] = round(min(vals), 0) if vals else None
        spread.append(row)

    # C3: no sentinel became a distance, and the no-crust state still occurs
    gate("C3", "no sentinel reached a distance, and models still decline to "
         "place crust at the oldest ages",
         "0 sentinels in any distance, no-crust count > 0",
         f"0 sentinels, {nocrust} no-crust cases",
         nocrust > 0)

    return {
        "models": [{"name": m["name"], "oldest_ma": m["oldest_ma"]}
                   for m in c["models"]],
        "places": places, "ages": ages,
        "fetched": c["fetched"],
        "identity_worst_km": round(ident, 6),
        "spread": spread, "tracks": tracks,
        "no_crust_cases": nocrust,
    }


# ---------------------------------------------------------------------- main

def main():
    print("gates:")
    masks, shape = load_masks()
    osf = json.load(open(os.path.join(DATA, "osf_provenance.json"),
                         encoding="utf-8"))
    ngl = json.load(open(os.path.join(DATA, "ngl_provenance.json"),
                         encoding="utf-8"))
    static = json.load(open(os.path.join(DATA, "static_provenance.json"),
                            encoding="utf-8"))

    gate("B7", "MIDAS velocities are in the frame the ITRF comparison assumes",
         "IGS20", ngl["frame"], ngl["frame"] == "IGS20")

    future = future_block(masks, shape, osf)
    present, fits = present_block()
    past = past_block()

    failed = [a["id"] for a in anchors if not a["passed"]]
    if failed:
        sys.exit(
            f"\nbuild: gates {failed} failed. Nothing was written, so no "
            "figure can be drawn from a number that did not pass. Read the "
            "rows above.")

    payload = {
        "generated_from": (
            "MIDAS IGS20 GNSS velocities (Nevada Geodetic Laboratory, "
            f"{ngl['fetched']}); ITRF2020-PMM and PB2002 plate boundaries "
            f"({static['fetched']}); NNR-MORVEL56 Table 1 extracted from "
            "Argus et al. 2011; the four future scenario grids from OSF 8NEQ4 "
            f"({osf['fetched']}); and eight plate reconstruction models from "
            f"the GPlates Web Service ({past['fetched']})."),
        "built": datetime.now(timezone.utc).date().isoformat(),
        "anchors": anchors,
        "cuts": {"min_years": P.MIN_YEARS,
                 "max_sigma_mm_yr": P.MAX_SIGMA * 1000,
                 "far_km": P.FAR_KM, "min_stations": P.MIN_STATIONS,
                 "mad_k": P.MAD_K, "resid_floor_mm_yr": P.RESID_FLOOR,
                 "max_iterations": P.MAX_ITER,
                 "polar_cut_deg": og.POLAR_CUT},
        "present": present,
        "b1_break": b1_break_block(fits),
        "geologic_vs_geodetic": geologic_block(fits),
        "extrapolation": extrapolation_block(fits),
        "past": past,
        "future": future,
        "antipodal_km": round(ANTIPODAL_KM, 0),
        "provenance": {"ngl": ngl, "osf": {k: v for k, v in osf.items()
                                           if k != "headers"},
                       "static": static},
    }
    os.makedirs(OUT, exist_ok=True)
    json.dump(payload, open(PAYLOAD, "w", encoding="utf-8"),
              indent=1, sort_keys=True)
    print(f"\n  all {len(anchors)} gates passed")
    print(f"  wrote {os.path.relpath(PAYLOAD, HERE)}  "
          f"{os.path.getsize(PAYLOAD):,} bytes")
    print(f"  wrote {os.path.relpath(FITCSV, HERE)}  "
          f"{os.path.getsize(FITCSV):,} bytes")


if __name__ == "__main__":
    main()
