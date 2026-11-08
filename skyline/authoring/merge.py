"""Fold every agent's drawings (authoring/out/*.json) into data/authored.json,
which build_massing.py reads. A file that does not parse is reported and
skipped; a later run picks it up once it is fixed."""
import glob, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
allq = {}
bad = []
# redo batches are later, better-researched drawings of the same towers: last
files = sorted(glob.glob(os.path.join(HERE, "out", "*.json")),
               key=lambda p: (os.path.basename(p).startswith("Redo_"), p))
for p in files:
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        bad.append((os.path.basename(p), str(e)[:80]))
        continue
    for q, v in d.items():
        if isinstance(v, dict) and q.startswith("Q"):
            v["_batch"] = os.path.basename(p)[:-5]
            allq[q] = v
json.dump(allq, open(os.path.join(ROOT, "data", "authored.json"), "w", encoding="utf-8"),
          indent=0, ensure_ascii=False)
k = sum(1 for v in allq.values() if v.get("keep_osm"))
print(f"  {len(allq)} towers from {len(glob.glob(os.path.join(HERE, 'out', '*.json')))} files: "
      f"{len(allq) - k} drawn, {k} OSM kept")
for b in bad:
    print("  UNREADABLE", *b)
