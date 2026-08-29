"""
Build the atlas data file for the globe application.

The old atlas carried its data inline in a 1.8 MB HTML file, which made the
presentation impossible to change without editing around the data. This pulls
the data out into `site/assets/atlas-data.js` so the application is a program
again rather than a document with a program stuck to it.

Nothing is resampled or thinned. All 7,192 nodes and 13,826 edges go through,
because the atlas is the place where the whole model is supposed to be
available — the front-page hero is where a sample is appropriate.

Reads:
    ../19 Atlas v6/scene_v6.json
    ../19 Atlas v6/countries.geo.json

Writes:
    site/assets/atlas-data.js

Run:
    python3 build_atlas.py
"""

import json
import math
import os
import sys

sys.setrecursionlimit(50000)

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
SCENE = os.path.join(PARENT, "19 Atlas v6", "scene_v6.json")
GEO = os.path.join(PARENT, "19 Atlas v6", "countries.geo.json")
OUT = os.path.join(HERE, "site", "assets", "atlas-data.js")

# The atlas gets finer coastlines than the hero: it is zoomable, so the
# simplification has to survive magnification.
TOLERANCE = 0.28

KINDS = ["market", "climate", "grid", "supply", "district", "consumer",
         "event", "station", "psych"]

# Where each of the six behaviour channels sits in the brain. Positions are in
# a right-handed anatomical frame, x right, y up, z forward, in units of half
# the brain's length. They are placed to be anatomically defensible rather than
# precise: this is a schematic solid, not an MRI, and the page says so.
BRAIN_XYZ = {
    "present_bias":  [0.30, 0.16, 0.74],    # prefrontal cortex
    "dissonance":    [0.06, 0.34, 0.20],    # anterior cingulate, near midline
    "norm":          [0.72, 0.20, -0.34],   # temporo-parietal junction
    "status":        [0.24, -0.22, 0.34],   # ventral striatum, deep
    "habit":         [0.30, -0.04, 0.06],   # basal ganglia, deep
    "loss_aversion": [0.44, -0.30, 0.24],   # amygdala, deep anterior temporal
}


def rdp(points, eps):
    if len(points) < 3:
        return points
    x0, y0 = points[0]
    x1, y1 = points[-1]
    dx, dy = x1 - x0, y1 - y0
    norm = math.hypot(dx, dy)
    idx, far = 0, -1.0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        d = (math.hypot(px - x0, py - y0) if norm == 0 else
             abs(dy * px - dx * py + x1 * y0 - y1 * x0) / norm)
        if d > far:
            idx, far = i, d
    if far > eps:
        return rdp(points[:idx + 1], eps)[:-1] + rdp(points[idx:], eps)
    return [points[0], points[-1]]


def coastlines():
    gj = json.load(open(GEO, encoding="utf-8"))
    out = 0
    rings = []
    for feat in gj["features"]:
        geom = feat.get("geometry") or {}
        polys = (geom.get("coordinates", []) if geom.get("type") == "Polygon"
                 else [r for p in geom.get("coordinates", []) for r in p]
                 if geom.get("type") == "MultiPolygon" else [])
        for ring in polys:
            pts = [(c[0], c[1]) for c in ring if len(c) >= 2]
            if len(pts) < 4:
                continue
            s = rdp(pts, TOLERANCE)
            if len(s) < 4:
                continue
            xs = [p[0] for p in s]
            ys = [p[1] for p in s]
            if (max(xs) - min(xs)) < 0.8 and (max(ys) - min(ys)) < 0.8:
                continue
            rings.append([[round(x, 2), round(y, 2)] for x, y in s])
            out += len(s)
    print(f"coastline: {len(rings)} rings, {out} points")
    return rings


def main():
    d = json.load(open(SCENE, encoding="utf-8"))
    nodes = d["nodes"]

    lat, lon, kind, tab, res = [], [], [], [], []
    name, src, ident = [], [], []
    missing = 0
    for n in nodes:
        la, lo = n.get("lat"), n.get("lon")
        if la is None or lo is None:
            missing += 1
            la, lo = 0.0, 0.0
        lat.append(round(la, 3))
        lon.append(round(lo, 3))
        kind.append(KINDS.index(n["kind"]))
        tab.append(int(n["tab"]))
        res.append(round(float(n["res"]), 4))
        name.append(n["name"])
        src.append(n.get("src", ""))
        ident.append(n["id"])

    es = [e["s"] for e in d["edges"]]
    et = [e["t"] for e in d["edges"]]
    ew = [round(float(e["w"]), 4) for e in d["edges"]]

    # brain channels, keyed by the node id the model already uses
    brain = []
    for key, region in d["brain"].items():
        nid = "PSYCH_" + key
        if nid in ident:
            brain.append({"id": nid, "key": key, "region": region,
                          "xyz": BRAIN_XYZ.get(key, [0, 0, 0]),
                          "i": ident.index(nid)})
    print(f"brain channels placed in 3D: {len(brain)}")

    payload = {
        "kinds": KINDS,
        "tabs": d["tabs"],
        "scenarios": d["scenarios"],
        "n": len(nodes),
        "lat": lat, "lon": lon, "kind": kind, "tab": tab, "res": res,
        "name": name, "src": src, "id": ident,
        "es": es, "et": et, "ew": ew,
        "coast": coastlines(),
        "brain": brain,
        "co2": d.get("co2", []),
        "temp": d.get("temp", []),
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("window.ATLAS=")
        json.dump(payload, fh, separators=(",", ":"), ensure_ascii=False)
        fh.write(";\n")

    print(f"nodes: {len(nodes)} ({missing} without coordinates) · "
          f"edges: {len(es)}")
    by_tab = {}
    for t in tab:
        by_tab[t] = by_tab.get(t, 0) + 1
    for i, t in enumerate(d["tabs"]):
        print(f"    tab {i} {t['name']:18s} {by_tab.get(i, 0):5d} nodes")
    print(f"written: {OUT} ({os.path.getsize(OUT)/1024:.0f} kB)")


if __name__ == "__main__":
    main()
