"""Assemble the visualiser: template + data + app into one self-contained file.

The towers' shapes (data/massing.json, build_massing.py) are folded in as
D.shapes, one list per city aligned with its ring, each tower packed as
[source, facade, floors, u-min, u-max, needle or 0, parts, drawing
confidence (0 high, 1 medium, 2 low, -1 not drawn), checked against
photos (1/0)], a part as
[z0, z1, roof height, roof code, u0, u1, faces, roof fall,
roof outline [[u, dz], ...] or 0, roof normal [bearing, tilt] or 0], a face as
[u0, u1, shade, true length]."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "data", "skylines.json"),
                      encoding="utf-8"))
mass = json.load(open(os.path.join(HERE, "data", "massing.json"),
                      encoding="utf-8"))
SRC = {"parts": 0, "outline": 1, "authored": 2, "generated": 3, "podium": 4}
FAC = {"masonry": 0, "ribbon": 1, "grid": 2}


def pack(t):
    parts = []
    for p in t["parts"]:
        parts.append([p["z0"], p["z1"], p["rh"], p["roof"], p["u"][0],
                      p["u"][1], [f if len(f) == 4 else f + [0] for f in
                                  p["f"]], p.get("rd", 0),
                      p.get("prof") or 0, p.get("rn") or 0])
    conf = {"high": 0, "medium": 1, "low": 2}.get(t.get("conf"), -1)
    return [SRC[t["src"]], FAC[t["fac"]], t["lv"], t["w"][0], t["w"][1],
            t.get("needle") or 0, parts, conf, 1 if t.get("checked") else 0]


shapes = []
for c in data["cities"]:
    recs = {t["q"]: t for t in mass["cities"][c["city"]]}
    shapes.append([pack(recs[r[7]]) for r in c["ring"]])
data["shapes"] = shapes
data["shapeSources"] = mass["sources"]

tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
app = open(os.path.join(HERE, "app.js"), encoding="utf-8").read()
blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
html = tpl.replace("/*APP*/", app).replace(
    "/*DATA*/", json.dumps(blob, ensure_ascii=False))
out = os.path.join(HERE, "skyline-app.html")
# newline="\n": site/.gitattributes declares eol=lf and Python text mode on Windows writes CRLF.
open(out, "w", encoding="utf-8", newline="\n").write(html)
print(f"  {out}  ({os.path.getsize(out)/1024:.0f} kB, "
      f"{len(data['cities'])} cities)")
