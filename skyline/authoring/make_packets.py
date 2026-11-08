"""Research packets for the authoring agents: per tower, what the data
already says (Wikidata height, year, floors, style, image, architect; the
OSM outline's size and orientation; the OSM 3D parts, summarised)."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import build_massing as M
M.COLLECT = {}
M.main()
C = M.COLLECT
pay = json.load(open('data/skylines.json', encoding='utf-8'))
ex = json.load(open(sorted(__import__('glob').glob('data/raw/wdextra_*.json'))[-1]))['answers']
def q(b): return b['b']['value'].rsplit('/', 1)[1]
facts = {}
for k in ('style', 'architect', 'image', 'floors', 'heights'):
    for b in ex[k]:
        d = facts.setdefault(q(b), {})
        if k == 'style': d.setdefault('style', []).append(b['sLabel']['value'])
        if k == 'architect': d.setdefault('architect', []).append(b['aLabel']['value'])
        if k == 'image': d['image'] = b['img']['value'].rsplit('/', 1)[1]
        if k == 'floors': d['floors'] = b['f']['value']
        if k == 'heights':
            lab = (b.get('critLabel', {}).get('value') or b.get('partLabel', {}).get('value') or '')
            d.setdefault('wd_heights', []).append([round(float(b['hm']['value']), 1), lab])

def mrr(pts):
    """minimum-area bounding rectangle: (long side, short side, bearing of the long side)"""
    best = None
    for a in range(0, 180):
        t = math.radians(a)
        ux, uy = math.sin(t), math.cos(t)          # bearing a
        us = [p[0] * ux + p[1] * uy for p in pts]
        vs = [-p[0] * uy + p[1] * ux for p in pts]
        L, Wd = max(us) - min(us), max(vs) - min(vs)
        if best is None or L * Wd < best[0]:
            best = (L * Wd, L, Wd, a)
    _, L, Wd, a = best
    if Wd > L:
        L, Wd, a = Wd, L, (a + 90) % 180
    return round(L, 1), round(Wd, 1), a

def summary(ring):
    area = abs(M.ring_area(ring))
    per = sum(math.hypot(ring[i+1][0]-ring[i][0], ring[i+1][1]-ring[i][1]) for i in range(len(ring)-1))
    L, Wd, a = mrr(ring)
    c = M.centroid(ring)
    circ = 4 * math.pi * area / per ** 2 if per else 0
    shape = ('round' if circ > 0.85 else 'rectangular' if area > 0.88 * L * Wd else
             'irregular')
    return {"long_m": L, "short_m": Wd, "long_axis_bearing": a, "area_m2": round(area),
            "vertices": len(ring) - 1, "plan": shape, "centroid_m": [round(c[0], 1), round(c[1], 1)]}

batches = []
for c in pay['cities']:
    towers = []
    for r in c['ring']:
        qid = r[7]
        info = C.get(qid)
        t = {"qid": qid, "name": r[4] or "(no English label)", "city": c['city'],
             "height_m": r[3], "year": r[5] or None,
             "wikidata": "https://www.wikidata.org/wiki/" + qid,
             "view_bearing_from_city_centre": r[6], "distance_km": r[2]}
        t.update(facts.get(qid, {}))
        if info:
            t["osm_source"] = info["src"]
            if info["outline"]:
                big = max(info["outline"], key=lambda rg: abs(M.ring_area(rg)))
                t["osm_outline"] = summary(big)
                t["osm_outline_points_m"] = [[round(x, 1), round(y, 1)] for x, y in
                                             M.simplify(big, 1.5)][:60]
            if info["src"] == "parts":
                ps = []
                for lp, b in info["mine"]:
                    sm = summary(lp)
                    ps.append({"z0": round(b[0], 1), "z1_walls": round(b[1], 1),
                               "roof_h": round(b[2], 1),
                               "roof": {0: "flat", 1: "pyramidal", 2: "dome", 3: "gabled/hipped",
                                        4: "skillion", 5: "onion", 6: "mansard"}[b[3]],
                               "long_m": sm["long_m"], "short_m": sm["short_m"],
                               "centroid_m": sm["centroid_m"]})
                ps.sort(key=lambda p: (p["z0"], -p["z1_walls"]))
                t["osm_3d_parts"] = ps[:40]
                t["osm_3d_parts_count"] = len(ps)
        else:
            t["osm_source"] = "generated (no usable outline)"
        towers.append(t)
    n = len(towers)
    k = max(1, math.ceil(n / 16))
    for j in range(k):
        part = towers[j * n // k:(j + 1) * n // k]
        batches.append({"batch": c['city'].replace(' ', '_') + (f"_{j+1}" if k > 1 else ""),
                        "city": c['city'], "towers": part})
# fold the very small cities together
small = [b for b in batches if len(b["towers"]) < 8]
big = [b for b in batches if len(b["towers"]) >= 8]
merged = []
cur = None
for b in small:
    if cur and len(cur['towers']) + len(b["towers"]) <= 20:
        cur['batch'] += '+' + b['batch']; cur['city'] += ' + ' + b['city']; cur['towers'] += b['towers']
    else:
        cur = dict(b); merged.append(cur)
batches = big + merged
for b in batches:
    json.dump(b, open(os.path.join(HERE, 'inputs', b['batch'] + '.json'), 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)
print(len(batches), 'batches', sum(len(b['towers']) for b in batches), 'towers')
for b in batches: print(' ', b['batch'], len(b['towers']))
