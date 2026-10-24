"""
The second source: what OpenStreetMap maps as standing at each tower.

Wikidata says what a building is and how tall; it does not reliably say
whether the building stands. QA (2026-10-22, D-31) found a tower destroyed
in 2001, towers never built and towers still going up on the wheels. OSM is
mapped from the ground and from imagery, so a tower that is not there tends
not to be in it, and one under construction is tagged as such. So a tower is
kept only if OSM maps it too (build_skylines.osm_match()).

Two stages per city, against overpass-api.de, every answer kept whole and
gzipped in data/raw/osm_<date>.json.gz with its query text and date:

  linked  every node, way or relation within RADIUS_KM carrying a wikidata=*
          tag and a building or building:part tag: OSM's own link to a
          Wikidata item, including the ones it tags as under construction.
  near    for each tower Wikidata alone would keep (build_skylines.
          wikidata_verdict()) that no linked OSM object names, every building
          or building:part within NEAR_M of the tower's coordinate, so the
          build can look for one of matching height or name.

The first version asked instead for every building near the city with a
mapped height of 50 m or more. Overpass ran out of memory on Los Angeles
(answering with HTTP 200, a "remark" and no elements, which the script took
for "0 elements"), and the set still missed towers OSM maps without a
height, such as Moscow's Neva Towers. An answer with a remark or no elements
is now an error, not data.

Run:  python fetch_osm.py            both stages, a new archive
      python fetch_osm.py --extend   the "near" stage for towers the filters
                                     now let through that the archive has no
                                     answer for (R5, 2026-10-24: building
                                     complexes and county-located downtown
                                     towers), appended with its own date
"""

import datetime
import gzip
import json
import os
import sys
import time
import urllib.parse
import urllib.request

from fetch_wikidata import CITIES, RAW_DIR, UA

ENDPOINT = "https://overpass-api.de/api/interpreter"
RADIUS_KM = 30.0
NEAR_M = 100
BATCH = 40

Q_LINKED = """[out:json][timeout:240];
(
 nwr(around:%(r)d,%(lat)s,%(lon)s)["wikidata"]["building"];
 nwr(around:%(r)d,%(lat)s,%(lon)s)["wikidata"]["building:part"];
);
out tags center;"""

Q_NEAR_ONE = ('way(around:%(m)d,%(lat)s,%(lon)s)["building"];'
              'way(around:%(m)d,%(lat)s,%(lon)s)["building:part"];'
              'relation(around:%(m)d,%(lat)s,%(lon)s)["building"];')


def overpass(q, tries=6, allow_empty=False):
    data = urllib.parse.urlencode({"data": q}).encode()
    for i in range(tries):
        req = urllib.request.Request(ENDPOINT, data=data,
                                     headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                ans = json.loads(r.read().decode("utf-8"))
            if ans.get("remark") or not (ans.get("elements") or allow_empty):
                raise RuntimeError("empty or remarked answer: " +
                                   str(ans.get("remark", "no elements")))
            return ans
        except Exception as e:
            wait = 30 * (i + 1)
            print(f"    retry {i + 1} after {e!r}; waiting {wait}s",
                  file=sys.stderr, flush=True)
            time.sleep(wait)
    raise SystemExit("Overpass did not answer; nothing written")


def extend():
    import glob
    import build_skylines as B
    wd = json.load(open(B.latest("wikidata_*.json"), encoding="utf-8"))
    B.set_classes(wd)
    path = sorted(glob.glob(os.path.join(RAW_DIR, "osm_*.json.gz")))[-1]
    with gzip.open(path, "rb") as fh:
        out = json.loads(fh.read().decode("utf-8"))
    for name, (_, lat, lon) in CITIES.items():
        c = out["cities"][name]
        named = set()
        for e in c["linked"]:
            for q in e.get("tags", {}).get("wikidata", "").replace(",", ";") \
                    .split(";"):
                named.add(q.strip())
        have = {p[0] for p in c["points"]}
        pts = []
        for it in B.items_for(wd["cities"][name], wd).values():
            h, why = B.wikidata_verdict(it, wd["fetched"])
            if h is not None and it["qid"] not in named and \
                    it["qid"] not in have:
                pts.append([it["qid"], it["coord"][0], it["coord"][1]])
        pts.sort()
        for i in range(0, len(pts), BATCH):
            q = ("[out:json][timeout:180];\n(\n" +
                 "\n".join(Q_NEAR_ONE % {"m": NEAR_M, "lat": p[1],
                                         "lon": p[2]}
                           for p in pts[i:i + BATCH]) +
                 "\n);\nout tags center;")
            c["queries_near"].append(q)
            c["near"].extend(overpass(q, allow_empty=True)["elements"])
            time.sleep(3)
        c["points"].extend(pts)
        if pts:
            c.setdefault("extended", []).append(
                {"fetched": datetime.date.today().isoformat(),
                 "points": len(pts)})
        print(f"  {name:12s} {len(pts):4d} new towers checked", flush=True)
    with gzip.GzipFile(path, "wb", mtime=0) as fh:
        fh.write(json.dumps(out, ensure_ascii=False,
                            separators=(",", ":")).encode("utf-8"))
    print(f"  wrote {path} ({os.path.getsize(path) / 1e6:.1f} MB)")


def main():
    if "--extend" in sys.argv:
        return extend()
    import build_skylines as B
    wd = json.load(open(B.latest("wikidata_*.json"), encoding="utf-8"))
    B.set_classes(wd)
    out = {"fetched": datetime.date.today().isoformat(), "endpoint": ENDPOINT,
           "radius_km": RADIUS_KM, "near_m": NEAR_M,
           "wikidata": os.path.basename(B.latest("wikidata_*.json")),
           "cities": {}}
    for name, (_, lat, lon) in CITIES.items():
        t = time.time()
        ql = Q_LINKED % {"r": RADIUS_KM * 1000, "lat": lat, "lon": lon}
        linked = overpass(ql)
        named = set()
        for e in linked["elements"]:
            for q in e.get("tags", {}).get("wikidata", "").replace(",", ";") \
                    .split(";"):
                named.add(q.strip())
        pts = []
        for it in B.items_for(wd["cities"][name], wd).values():
            h, why = B.wikidata_verdict(it, wd["fetched"])
            if h is not None and it["qid"] not in named:
                pts.append([it["qid"], it["coord"][0], it["coord"][1]])
        pts.sort()
        qn, near = [], []
        for i in range(0, len(pts), BATCH):
            q = ("[out:json][timeout:180];\n(\n" +
                 "\n".join(Q_NEAR_ONE % {"m": NEAR_M, "lat": p[1],
                                         "lon": p[2]}
                           for p in pts[i:i + BATCH]) +
                 "\n);\nout tags center;")
            qn.append(q)
            near.extend(overpass(q, allow_empty=True)["elements"])
            time.sleep(3)
        out["cities"][name] = {
            "query_linked": ql, "osm3s": linked.get("osm3s", {}),
            "linked": linked["elements"], "points": pts,
            "queries_near": qn, "near": near}
        print(f"  {name:12s} {len(linked['elements']):5d} linked, "
              f"{len(pts):4d} unlinked towers, {len(near):5d} near  "
              f"{time.time() - t:5.1f}s", flush=True)
        time.sleep(3)
    path = os.path.join(RAW_DIR, f"osm_{out['fetched']}.json.gz")
    # mtime=0 so the same answer gzips to the same bytes
    with gzip.GzipFile(path, "wb", mtime=0) as fh:
        fh.write(json.dumps(out, ensure_ascii=False,
                            separators=(",", ":")).encode("utf-8"))
    print(f"  wrote {path} ({os.path.getsize(path) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
