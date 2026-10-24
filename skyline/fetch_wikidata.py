"""
Pull every tall thing Wikidata records near each city, and archive the answer.

The payload this project shipped until October 2026 came from a Wikidata dump
nobody archived, so it could not be re-run or checked, and when it was checked
(QA, 2026-10-22, DECISIONS D-31) it held demolished, unbuilt and duplicated
towers and a radio mast. This script is the pull that replaces it, and its
whole output is kept: data/raw/wikidata_<date>.json holds every query's text,
the endpoint, the date, and the answers exactly as they came back.
build_skylines.py reads only that file, so every filter it applies can be
re-run, varied and checked against the same raw rows.

Three queries per city, all against query.wikidata.org:

  heights   every item within RADIUS_KM of the city's coordinate with a
            height statement (P2048) of at least FLOOR_M, read through psn:
            so the value comes back normalised to metres whatever unit it was
            entered in, with the statement's rank and its "applies to part"
            (P518) and "criterion" (P1013) qualifiers.
  facts     for those items: every P31 class, the English label, demolition
            or end dates (P576, P582), state of use (P5817), opening (P1619),
            inception (P571), and whether the item sits inside the city's own
            Wikidata item through P131 (located in) followed transitively.
  classes   (once, for every class seen) whether that class is a subclass of
            building, Q41176, through P279*. Masts, TV towers, observation
            towers and bridges are not, which is the point.

  located  (--locate, appended to the newest archive with its own date) for
            every item the P131+ test put outside its city: its direct
            "located in" values, and whether each is an ancestor of the city
            (a county or state the city is itself in). Downtown Chicago and
            Calgary towers carry only their county or province, so the
            transitive test alone put them outside (claims check, R5,
            2026-10-24); build_skylines.in_city() uses this to let them in
            without letting in Ramat Gan.

Run:  python fetch_wikidata.py            pull and write the archive
      python fetch_wikidata.py --city "New York"   one city, printed, not saved
      python fetch_wikidata.py --locate   add the "located" answers
"""

import argparse
import datetime
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "data", "raw")
ENDPOINT = "https://query.wikidata.org/sparql"
UA = "andrewsilvestri.com skyline rebuild/2026-10 (https://andrewsilvestri.com/skyline.html)"

RADIUS_KM = 30.0    # wide on purpose: the P131 flag, not the radius, decides
FLOOR_M = 50.0      # below the wheel's 55 m floor, so the floor is applied later

# The 27 cities the page has carried, with their own Wikidata items. A city's
# item is what "located in" (P131) is followed to, so it has to be the item
# buildings actually point at: the Brussels-Capital Region rather than the
# City of Brussels, whose towers stand in Saint-Josse and Schaerbeek; the
# Tokyo Metropolis rather than the 23 wards; Greater London rather than
# London, because boroughs point at the former; the Emirate of Dubai, the
# Auckland Region and the municipality of Rotterdam for the same reason
# (first pull, 2026-10-24: 11, 0, 28 and 0 of each city's buildings were
# found inside the city's own item). Neighbouring cities stay out: Ramat Gan
# is not Tel Aviv, Yokohama is not Tokyo, La Defense (Courbevoie, Puteaux)
# is not Paris, The Hague is not Rotterdam.
CITIES = {
    "New York": ("Q60", 40.713, -74.006),
    "Dubai": ("Q613", 25.205, 55.271),
    "Shenzhen": ("Q15174", 22.543, 114.058),
    "Tokyo": ("Q1490", 35.690, 139.692),
    "Chicago": ("Q1297", 41.878, -87.630),
    "Toronto": ("Q172", 43.653, -79.383),
    "Paris": ("Q90", 48.857, 2.352),
    "Moscow": ("Q649", 55.756, 37.617),
    "Taipei": ("Q1867", 25.033, 121.565),
    "Hong Kong": ("Q8646", 22.302, 114.177),
    "Tel Aviv": ("Q33935", 32.085, 34.781),
    "Seoul": ("Q8684", 37.567, 126.978),
    "Austin": ("Q16559", 30.267, -97.743),
    "London": ("Q23306", 51.507, -0.128),
    "Frankfurt": ("Q1794", 50.111, 8.682),
    "Warsaw": ("Q270", 52.230, 21.012),
    "Osaka": ("Q35765", 34.694, 135.502),
    "Los Angeles": ("Q65", 34.052, -118.244),
    "Miami": ("Q8652", 25.762, -80.192),
    "Auckland": ("Q726917", -36.848, 174.763),
    "Nashville": ("Q23197", 36.163, -86.781),
    "Calgary": ("Q36312", 51.045, -114.057),
    "Madrid": ("Q2807", 40.417, -3.704),
    "Rotterdam": ("Q2680952", 51.924, 4.478),
    "Vienna": ("Q1741", 48.208, 16.373),
    "Brussels": ("Q240", 50.851, 4.352),
    "Fort Worth": ("Q16558", 32.7555, -97.3308),
}

Q_HEIGHTS = """
SELECT ?b ?coord ?hm ?rank ?part ?crit WHERE {
  SERVICE wikibase:around {
    ?b wdt:P625 ?coord .
    bd:serviceParam wikibase:center "Point(%(lon)s %(lat)s)"^^geo:wktLiteral .
    bd:serviceParam wikibase:radius "%(radius)s" .
  }
  ?b p:P2048 ?st .
  ?st psn:P2048/wikibase:quantityAmount ?hm .
  ?st wikibase:rank ?rank .
  FILTER(?hm >= %(floor)s)
  OPTIONAL { ?st pq:P518 ?part }
  OPTIONAL { ?st pq:P1013 ?crit }
}
"""

Q_FACTS = """
SELECT ?b ?bLabel ?cls ?dem ?end ?state ?open ?incep ?inCity WHERE {
  VALUES ?b { %(items)s }
  OPTIONAL { ?b wdt:P31 ?cls }
  OPTIONAL { ?b wdt:P576 ?dem }
  OPTIONAL { ?b wdt:P582 ?end }
  OPTIONAL { ?b wdt:P5817 ?state }
  OPTIONAL { ?b wdt:P1619 ?open }
  OPTIONAL { ?b wdt:P571 ?incep }
  BIND(EXISTS { ?b wdt:P131+ wd:%(city)s } AS ?inCity)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,mul". }
}
"""

Q_LOCATED = """
SELECT ?b ?loc ?ancestor WHERE {
  VALUES ?b { %(items)s }
  ?b wdt:P131 ?loc .
  BIND(EXISTS { wd:%(city)s wdt:P131+ ?loc } AS ?ancestor)
}
"""

Q_CLASSES = """
SELECT ?cls ?clsLabel ?isBuilding WHERE {
  VALUES ?cls { %(items)s }
  BIND(EXISTS { ?cls wdt:P279* wd:Q41176 } AS ?isBuilding)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,mul". }
}
"""


def sparql(q, tries=4):
    data = urllib.parse.urlencode({"query": q}).encode()
    for i in range(tries):
        req = urllib.request.Request(ENDPOINT, data=data, headers={
            "User-Agent": UA, "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:                       # 429 / 5xx / timeout
            wait = 10 * (i + 1)
            print(f"    retry {i + 1} after {e!r}; waiting {wait}s",
                  file=sys.stderr)
            time.sleep(wait)
    raise SystemExit("WDQS did not answer; nothing written")


def qid(uri):
    return uri.rsplit("/", 1)[-1]


def pull_city(name):
    city, lat, lon = CITIES[name]
    qh = Q_HEIGHTS % {"lat": lat, "lon": lon, "radius": RADIUS_KM,
                      "floor": FLOOR_M}
    h = sparql(qh)
    items = sorted({qid(b["b"]["value"]) for b in h["results"]["bindings"]})
    facts, qfs = [], []
    for i in range(0, len(items), 150):
        qf = Q_FACTS % {"items": " ".join("wd:" + x for x in items[i:i + 150]),
                        "city": city}
        qfs.append(qf)
        facts.extend(sparql(qf)["results"]["bindings"])
        time.sleep(1)
    return {"city_qid": city, "lat": lat, "lon": lon,
            "q_heights": qh, "heights": h["results"]["bindings"],
            "q_facts": qfs, "facts": facts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city")
    ap.add_argument("--locate", action="store_true")
    a = ap.parse_args()
    if a.locate:
        return locate()
    if a.city:
        r = pull_city(a.city)
        print(f"{a.city}: {len(r['heights'])} height rows, "
              f"{len(r['facts'])} fact rows")
        return
    out = {"fetched": datetime.date.today().isoformat(), "endpoint": ENDPOINT,
           "radius_km": RADIUS_KM, "floor_m": FLOOR_M, "cities": {}}
    for name in CITIES:
        t = time.time()
        out["cities"][name] = r = pull_city(name)
        print(f"  {name:12s} {len(r['heights']):5d} height rows "
              f"{len(r['facts']):6d} fact rows  {time.time() - t:5.1f}s")
        time.sleep(2)
    cls = sorted({qid(f["cls"]["value"]) for c in out["cities"].values()
                  for f in c["facts"] if "cls" in f})
    rows, qcs = [], []
    for i in range(0, len(cls), 200):
        qc = Q_CLASSES % {"items": " ".join("wd:" + x for x in cls[i:i + 200])}
        qcs.append(qc)
        rows.extend(sparql(qc)["results"]["bindings"])
    out["q_classes"], out["classes"] = qcs, rows
    # the city items themselves, labelled, so the archive says which area
    # each city's "located in" test was run against
    qi = ("SELECT ?c ?cLabel WHERE { VALUES ?c { %s } SERVICE wikibase:label "
          "{ bd:serviceParam wikibase:language \"en\". } }"
          % " ".join("wd:" + v[0] for v in CITIES.values()))
    out["q_city_items"] = qi
    out["city_items"] = sparql(qi)["results"]["bindings"]
    os.makedirs(RAW_DIR, exist_ok=True)
    path = os.path.join(RAW_DIR, f"wikidata_{out['fetched']}.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"  {len(cls)} classes; wrote {path} "
          f"({os.path.getsize(path) / 1e6:.1f} MB)")


def locate():
    import glob
    path = sorted(glob.glob(os.path.join(RAW_DIR, "wikidata_*.json")))[-1]
    out = json.load(open(path, encoding="utf-8"))
    loc = {"fetched": datetime.date.today().isoformat(), "cities": {}}
    for name, c in out["cities"].items():
        outside = sorted({qid(f["b"]["value"]) for f in c["facts"]
                          if f["inCity"]["value"] == "false"})
        rows, qs = [], []
        for i in range(0, len(outside), 150):
            q = Q_LOCATED % {"items": " ".join("wd:" + x
                                               for x in outside[i:i + 150]),
                             "city": c["city_qid"]}
            qs.append(q)
            rows.extend(sparql(q)["results"]["bindings"])
            time.sleep(1)
        loc["cities"][name] = {"queries": qs, "rows": rows}
        print(f"  {name:12s} {len(outside):4d} outside, {len(rows):4d} rows",
              flush=True)
    out["located"] = loc
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"  added to {path}")


if __name__ == "__main__":
    main()
