"""
Build the front-page hero from real model data.

The ornament on the front page is not decoration bought from anywhere. It is
the published model drawn on a rotating globe: real power stations at their
recorded coordinates, real recorded disasters at theirs, real national grids,
real insolation bands, over a real coastline. If a point is on the globe,
something in the data put it there.

It reads the same payload the atlas itself runs on, so the front page cannot
drift away from the model the way it does when it is built from a snapshot.

A uniform sample would be four parts power station and nothing else, so each
layer has a quota and the small layers stay visible. The brain is left out:
behaviour is the one layer that is not a place.

Reads:
    ../19 Atlas v6/countries.geo.json    coastlines
    site/assets/atlas-data.js            the live model, with lat/lon

Writes:
    site/assets/hero-data.js             a global, so it works over file:// too

Run:
    python3 build_hero.py
"""

import json
import math
import os
import random
import sys

# rdp recurses once per retained vertex on long coastlines
sys.setrecursionlimit(50000)

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
GEO = os.path.join(PARENT, "19 Atlas v6", "countries.geo.json")
SCENE = os.path.join(PARENT, "19 Atlas v6", "scene_v6.json")
OUT = os.path.join(HERE, "site", "assets", "hero-data.js")

# How many of each node kind to carry. The full 7,192 is more than a hero
# needs and would triple the page weight; these shares keep the visual
# character of the census — dominated by stations, punctuated by events.
QUOTA = {"station": 900, "event": 380, "grid": 190, "supply": 150,
         "district": 120, "consumer": 160, "market": 6, "climate": 2}

# Douglas-Peucker tolerance in degrees. Coastlines only need to read as
# coastlines at 700 pixels across.
TOLERANCE = 0.55


def rdp(points, eps):
    """Ramer-Douglas-Peucker simplification."""
    if len(points) < 3:
        return points
    x0, y0 = points[0]
    x1, y1 = points[-1]
    dx, dy = x1 - x0, y1 - y0
    norm = math.hypot(dx, dy)
    idx, far = 0, -1.0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        if norm == 0:
            d = math.hypot(px - x0, py - y0)
        else:
            d = abs(dy * px - dx * py + x1 * y0 - y1 * x0) / norm
        if d > far:
            idx, far = i, d
    if far > eps:
        left = rdp(points[:idx + 1], eps)
        right = rdp(points[idx:], eps)
        return left[:-1] + right
    return [points[0], points[-1]]


def rings_from(geom):
    t = geom.get("type")
    coords = geom.get("coordinates", [])
    if t == "Polygon":
        return coords
    if t == "MultiPolygon":
        return [ring for poly in coords for ring in poly]
    return []


def build_coast():
    with open(GEO, encoding="utf-8") as fh:
        gj = json.load(fh)
    out, kept, raw = [], 0, 0
    for feat in gj["features"]:
        for ring in rings_from(feat.get("geometry") or {}):
            pts = [(round(c[0], 3), round(c[1], 3)) for c in ring
                   if len(c) >= 2]
            raw += len(pts)
            if len(pts) < 4:
                continue
            simple = rdp(pts, TOLERANCE)
            if len(simple) < 4:
                continue
            # Drop specks; keep anything with real extent.
            xs = [p[0] for p in simple]
            ys = [p[1] for p in simple]
            if (max(xs) - min(xs)) < 1.2 and (max(ys) - min(ys)) < 1.2:
                continue
            out.append([[round(x, 2), round(y, 2)] for x, y in simple])
            kept += len(simple)
    print(f"coastline: {len(out)} rings, {raw} points -> {kept} "
          f"({100*kept/raw:.1f}% kept)")
    return out


def build_nodes():
    with open(SCENE, encoding="utf-8") as fh:
        scene = json.load(fh)
    by_kind = {}
    for n in scene["nodes"]:
        lat, lon = n.get("lat"), n.get("lon")
        if lat is None or lon is None:
            continue
        by_kind.setdefault(n["kind"], []).append(
            [round(lon, 2), round(lat, 2)])
    random.seed(11)
    out, census = [], {}
    kinds = list(QUOTA)
    for kind, want in QUOTA.items():
        pool = by_kind.get(kind, [])
        take = pool if len(pool) <= want else random.sample(pool, want)
        census[kind] = len(take)
        k = kinds.index(kind)
        out.extend([p[0], p[1], k] for p in take)
    print(f"nodes: {sum(census.values())} of "
          f"{sum(len(v) for v in by_kind.values())} placed  {census}")
    return kinds, out


def main():
    coast = build_coast()
    kinds, nodes = build_nodes()
    flat = [c for ring in nodes for c in ring]
    payload = {
        "coast": coast,
        "kinds": kinds,
        "nodes": flat,          # flat triples: lon, lat, kindIndex
        "n": len(nodes),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("window.HERO=")
        json.dump(payload, fh, separators=(",", ":"))
        fh.write(";\n")
    print(f"written: {OUT} ({os.path.getsize(OUT)/1024:.0f} kB)")


if __name__ == "__main__":
    main()
