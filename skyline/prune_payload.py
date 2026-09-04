"""One-off, kept for the record: strip the retired panorama from skylines.json.

build_skylines.py cannot be re-run - its raw input, data/raw/wikidata_buildings.json,
was never archived (AUDIT_SKYLINE_2026-09-04.md, finding 0). So the shipped
payload is the last output of a pipeline nobody can rerun, and the only way to
change its shape is to edit that output directly. This script did that once, on
2026-09-04, and build_skylines.py was changed the same day to emit this shape,
so a future run from a fresh pull produces the same fields.

What came out, and why: `prof`, `draw`, `view`, `dist` were the panorama
rendering's geometry - a true horizon from a stated viewpoint, with occlusion.
That rendering was retired before the page shipped; the app read none of these
fields (app.js references: zero), yet skyline.html described them as the
instrument's "Measured" behaviour. `towers` keeps name, height and year only;
its bearing and distance were from the panorama viewpoint too. What came in:
`ringFloor` (the 55 m floor the wheel uses, which was never on screen) and
`listFloor` for the three supplemented cities (the height above which the
published list overrules Wikidata - supplement.py LIST_FLOOR). `look`, the
starting bearing, was the retired viewpoint's; it is now the wheel slot of
the tallest tower.

Run:  python3 prune_payload.py        (idempotent)
"""
import json, os
import supplement as SUPP

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "data", "skylines.json")
DROP = ("prof", "draw", "view", "dist")
RING_FLOOR = 55.0     # build_skylines.RING_FLOOR

d = json.load(open(PATH, encoding="utf-8"))
before = os.path.getsize(PATH)
d["ringFloor"] = RING_FLOOR
for c in d["cities"]:
    for k in DROP:
        c.pop(k, None)
    c["towers"] = [{"n": t["n"], "h": t["h"], "y": t["y"]} for t in c["towers"]]
    # the starting bearing used to be the retired viewpoint's; face the
    # tallest tower's slot on the wheel instead (build_skylines does the same)
    c["look"] = max(c["ring"], key=lambda r: r[3])[0]
    if c["hand"]:
        c["listFloor"] = SUPP.LIST_FLOOR[c["city"]]
    else:
        c.pop("listFloor", None)
out = {"bins": d["bins"], "minHeight": d["minHeight"], "ringFloor": d["ringFloor"],
       "cities": d["cities"]}
with open(PATH, "w", encoding="utf-8") as fh:
    json.dump(out, fh, separators=(",", ":"))
print(f"  {os.path.basename(PATH)}: {before/1024:.0f} kB -> {os.path.getsize(PATH)/1024:.0f} kB, "
      f"{len(out['cities'])} cities, fields: {sorted(out['cities'][0].keys())}")
