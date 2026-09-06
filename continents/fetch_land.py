"""Fetch reconstructed coastlines so the viewer can show the continents move.

The viewer used to draw an empty coordinate frame with eight dots on it, on
the argument that modern outlines are wrong at every age but zero. That
argument is right about MODERN outlines and says nothing about reconstructed
ones: the same models that place the dots also reconstruct coastlines, so the
land here is each model's own paleogeography rather than today's world pasted
onto the past. Nothing modern is drawn at any age.

Land is fetched for a SUBSET of the models, not all eight. Switching the land
model is the point: at 400 Ma the same slider position gives visibly
different worlds, which is the page's argument about disagreement made out of
continents instead of dots. Three is enough to show that and keeps the asset
to a couple of megabytes; all eight would be six.

WHAT IS DONE TO THE GEOMETRY, AND WHY
-------------------------------------
A raw response is about 2.4 MB and 100,000 points, which is far more than a
900-pixel map can show. Each frame is therefore:

  1. unwrapped in longitude, so a ring that crosses the antimeridian is
     continuous rather than a polygon that spans the world backwards;
  2. unioned, so the per-plate coastline pieces stop leaving white slivers
     between them where they abut;
  3. clipped to -180..180 and to the two neighbouring branches, which is real
     clipping rather than breaking a line at the seam - breaking it leaves
     the fill to close across the whole map;
  4. simplified with preserve_topology=True. Without that flag the simplifier
     produces self-intersecting spikes, which look like a rendering fault;
  5. dropped below a minimum area, quantised to a quarter degree, and
     delta-encoded along each ring, which is what makes the asset affordable.

Writes
------
data/land.json      committed; the viewer's asset is built from it

Run:  python3 fetch_land.py [--resume]
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union
from shapely import set_precision

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "land.json")
CACHE = os.path.join(HERE, "data", "gplates_cache.json")

BASE = "https://gws.gplates.org/reconstruct/coastlines/"
# The land models. All three reach 500 Ma, so the selector never goes blank,
# and they sit in different reference frames, which is why they disagree.
LAND_MODELS = ("MERDITH2021", "MULLER2022", "PALEOMAP")
TOL = 0.6            # degrees; below this the outlines cost more than they show
MIN_AREA = 6.0       # square degrees; drops islands a 900 px map cannot render
Q = 4                # quantisation, quarter of a degree


def frame(model, age, tries=4):
    """One reconstructed frame. The service returns an occasional 502 under
    a long run of large requests, so a transient failure is retried rather
    than ending a half-hour fetch."""
    url = f"{BASE}?time={age}&model={model}"
    for attempt in range(1, tries + 1):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                d = json.loads(r.read())
            break
        except Exception as exc:                                # noqa: BLE001
            if attempt == tries:
                raise
            print(f"    {model}@{age}: {exc}; retry {attempt} of {tries - 1}")
            time.sleep(5 * attempt)
    parts = []
    for f in d.get("features", []):
        g = f.get("geometry")
        if not g:
            continue
        s = shape(g)
        for p in (s.geoms if s.geom_type == "MultiPolygon" else [s]):
            c = np.array(p.exterior.coords)
            if len(c) < 4:
                continue
            lon = c[:, 0].copy()
            step = np.diff(lon)
            lon[1:] += -360 * np.cumsum(step > 180) + 360 * np.cumsum(step < -180)
            q = Polygon(np.column_stack([lon, c[:, 1]]))
            if not q.is_valid:
                q = q.buffer(0)
            if not q.is_empty:
                parts.append(q)
    if not parts:
        return []
    # Snap to a fine grid before unioning. Some frames contain degenerate
    # slivers - a ring whose points collapse to a single coordinate - and
    # unioning them raises a non-noded intersection rather than returning
    # anything. Snapping resolves those; the grid is far finer than the
    # quarter degree the output is quantised to, so it changes nothing that
    # is drawn.
    snapped = []
    for q in parts:
        try:
            q = set_precision(q, 1e-7)
        except Exception:                                       # noqa: BLE001
            pass
        if not q.is_empty and q.area > 0:
            snapped.append(q)
    if not snapped:
        return []
    try:
        merged = unary_union(snapped)
    except Exception:                                           # noqa: BLE001
        merged = unary_union([q.buffer(0) for q in snapped])
    rings = []
    for shift in (0, -360, 360):
        clip = affinity.translate(merged, xoff=shift).intersection(
            box(-180, -90, 180, 90))
        if clip.is_empty:
            continue
        clip = clip.simplify(TOL, preserve_topology=True)
        for p in (clip.geoms if clip.geom_type == "MultiPolygon" else [clip]):
            if p.geom_type != "Polygon" or p.area < MIN_AREA:
                continue
            c = np.array(p.exterior.coords)
            ring, px, py = [], 0, 0
            for x, y in c:
                ix, iy = int(round(x * Q)), int(round(y * Q))
                ring.append(ix - px)
                ring.append(iy - py)
                px, py = ix, iy
            rings.append(ring)
    return rings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    cache = json.load(open(CACHE, encoding="utf-8"))
    ages = cache["ages"]
    oldest = {m["name"]: m["oldest_ma"] for m in cache["models"]}
    for m in LAND_MODELS:
        if m not in oldest:
            sys.exit(f"fetch_land: {m} is not one of the pinned models. The "
                     "land the viewer draws must come from a model the page "
                     "also names.")

    have = {}
    if args.resume and os.path.exists(OUT):
        have = json.load(open(OUT, encoding="utf-8")).get("frames", {})
        print(f"  resuming with {len(have)} frames")

    todo = [(m, a) for m in LAND_MODELS for a in ages
            if a <= oldest[m] and f"{m}@{a}" not in have]
    print(f"  {len(todo)} frames to fetch, one per second")
    for k, (m, a) in enumerate(todo, 1):
        try:
            have[f"{m}@{a}"] = frame(m, a)
        except Exception as exc:                                # noqa: BLE001
            print(f"    {m}@{a}: {exc}")
            json.dump({"frames": have}, open(OUT, "w", encoding="utf-8"))
            sys.exit("fetch_land: a request failed; rerun with --resume. "
                     "Progress was kept.")
        if k % 20 == 0:
            print(f"    {k}/{len(todo)}  "
                  f"{sum(len(json.dumps(v)) for v in have.values())/1048576:.2f} MB so far")
        time.sleep(1.0)

    payload = {
        "source": BASE,
        "fetched": datetime.now(timezone.utc).date().isoformat(),
        "models": list(LAND_MODELS),
        "ages": ages,
        "quantisation": Q,
        "simplify_deg": TOL,
        "min_area_sq_deg": MIN_AREA,
        "note": ("Reconstructed coastlines from each model, not modern "
                 "outlines. Rings are delta-encoded on a quarter-degree grid; "
                 "the first pair is absolute and each pair after it is a step."),
        "frames": have,
    }
    json.dump(payload, open(OUT, "w", encoding="utf-8"), separators=(",", ":"))
    print(f"  wrote {os.path.relpath(OUT, HERE)}  "
          f"{os.path.getsize(OUT):,} bytes  {len(have)} frames")


if __name__ == "__main__":
    main()
