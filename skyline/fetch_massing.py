"""
The third source: the shape of each tower, from OpenStreetMap.

fetch_osm.py asked only for a point and the tags (out tags center), enough
to say a tower stands. To draw it, the outline is needed, and where mappers
have modelled it in 3D (Simple 3D Buildings), every building:part with its
own height, min_height and roof. So for each city, one Overpass query:

  outline  the OSM object build_skylines.osm_match() confirmed each ring
           tower with (its id is in data/massing_ids.json), out geom
  parts    every building:part way or relation within PART_M of those
           outlines, out geom; which tower each part belongs to is decided
           in build_massing.py by containment, not here

The whole answer is kept, gzipped, in data/raw/massing_<date>.json.gz with
its query text and date. Run on a machine that can reach overpass-api.de:

    python fetch_massing.py
"""
import gzip, json, os, sys, time, urllib.parse, urllib.request, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ENDPOINT = "https://overpass-api.de/api/interpreter"
PART_M = 20
UA = "skylines-played/1.0 (andrewsilvestri.com; one query per city)"

def query(ids):
    ways = [i.split("/")[1] for i in ids if i.startswith("way/")]
    rels = [i.split("/")[1] for i in ids if i.startswith("relation/")]
    nodes = [i.split("/")[1] for i in ids if i.startswith("node/")]
    sel = ""
    if ways: sel += "way(id:%s);" % ",".join(ways)
    if rels: sel += "relation(id:%s);" % ",".join(rels)
    q = ("[out:json][timeout:600][maxsize:536870912];(" + sel + ")->.t;.t out geom;"
         "(way(around.t:%d)[\"building:part\"];relation(around.t:%d)[\"building:part\"];)->.p;"
         ".p out geom;" % (PART_M, PART_M))
    if nodes:  # a tower OSM maps only as a point: take what stands around it
        q += "(node(id:%s);)->.n;(way(around.n:40)[\"building\"];way(around.n:40)[\"building:part\"];relation(around.n:40)[\"building:part\"];)->.m;.m out geom;" % ",".join(nodes)
    return q

def run(q, tries=4):
    for k in range(tries):
        try:
            req = urllib.request.Request(ENDPOINT, data=urllib.parse.urlencode({"data": q}).encode(),
                                         headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=900) as r:
                ans = json.load(r)
            if ans.get("remark") and not ans.get("elements"):
                raise RuntimeError("remark: " + ans["remark"])
            return ans
        except Exception as e:
            print("   try", k + 1, "failed:", e, flush=True)
            time.sleep(30 * (k + 1))
    raise SystemExit("gave up")

def main():
    """One query per city; the archive is rewritten after every city, and a
    run picks up today's archive and skips the cities it already holds, so
    an Overpass outage halfway through costs one city, not the lot.
    python fetch_massing.py [City ...] fetches only those."""
    ids = json.load(open(os.path.join(HERE, "data", "massing_ids.json")))
    today = datetime.date.today().isoformat()
    p = os.path.join(HERE, "data", "raw", "massing_%s.json.gz" % today)
    if os.path.exists(p):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            out = json.load(f)
    else:
        out = {"fetched": today, "endpoint": ENDPOINT, "part_m": PART_M,
               "cities": {}}
    only = sys.argv[1:]
    for city, cid in ids.items():
        if only and city not in only:
            continue
        if city in out["cities"] and not only:
            continue
        q = query(cid)
        t0 = time.time()
        ans = run(q)
        out["cities"][city] = {"query": q, "elements": ans["elements"]}
        print(f"{city}: {len(ans['elements'])} elements in {time.time()-t0:.0f}s", flush=True)
        with gzip.open(p + ".tmp", "wt", encoding="utf-8") as f:
            json.dump(out, f)
        os.replace(p + ".tmp", p)
        time.sleep(8)
    print("wrote", p, len(out["cities"]), "cities", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
