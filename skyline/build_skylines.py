"""
Turn real, standing buildings into a 360-degree skyline wheel, one per city.

The observation this project rests on is that a skyline and a spectrum
analyser are the same picture. Both are a row of vertical bars of varying
height; both are read left to right; and in both the tall spikes are what the
eye goes to. That is a coincidence of drawing conventions rather than of
physics, but it is a usable one, because it means a city can be played.

WHERE THE TOWERS COME FROM (rebuilt 2026-10-24, DECISIONS D-31). The payload
shipped until then came from a Wikidata dump nobody archived. When QA checked
it, the wheels held the World Trade Center's destroyed North Tower, towers
never built, towers still going up, the same building under two items, a
radio mast as Warsaw's tallest, and towers from neighbouring cities. This
file now reads two archived pulls and nothing else:

  data/raw/wikidata_<date>.json   fetch_wikidata.py: heights, classes,
                                  states, dates and the located-in test
  data/raw/osm_<date>.json.gz     fetch_osm.py: what OpenStreetMap maps as a
                                  building near each city

and a tower is kept only if every one of these holds, each counted and
reported per city so a filter that stops firing shows up as a zero:

  building    one of its classes is a subclass of building (Q41176) or a
              group of buildings (COMPLEX), and it
              is not a tower-type structure (TOWER below) unless it is also a
              high-rise (HIGHRISE). Wikidata files TV towers, masts and
              observation towers under building, through "tower"; the first
              version of this file let a 950 m bridge and then a radio mast
              through, so the class test names what it excludes.
  in city     inside the city's own Wikidata item through P131 followed
              transitively (fetch_wikidata.CITIES says which item), or
              within CORE_KM of the city's coordinate and located only in
              places the city is itself in (its county or state). The old
              35 km disc put Yokohama in Tokyo and The Hague in Rotterdam.
  standing    no demolition date (P576), no past end date (P582), no class or
              state of use that says demolished, proposed, unfinished, under
              construction, on hold or cancelled (NOT_STANDING), AND present
              in OpenStreetMap: an OSM building carrying the item's QID, or
              failing that one within NEAR_KEEP_M of its coordinate that
              agrees on height or name (osm_match()). Wikidata does not
              mark every unbuilt tower; OSM does not map a tower that is not
              there. A tower OSM tags as under construction does not count.
  plausible   one usable height (HEIGHT below) between RING_FLOOR and the
              tallest building there is.
  once        two items for one building (same normalised name nearby, the
              same OSM building, or the same spot and height) are one tower.

The three hand-transcribed supplements (Austin, Nashville, Fort Worth) are
retired with the old payload. They made those cities look denser than Hong
Kong because the lists were complete and Wikidata is not (QA finding 5), and
Austin's contradicted its own source. A city whose Wikidata record is too thin
for a wheel is now dropped and named, not filled by hand.

  REARRANGED. The spacing around the wheel: equalised, so the ring is full.
  Order survives, angle does not. The app says so on screen.

  INVENTED. The sound. There is no sense in which a city has a pitch. The
  mapping from geometry to audio is a choice, documented in the app, and
  deterministic - the same skyline always produces the same sound.

The meter (`rprof`) holds HEIGHT in metres. Until 2026-10-24 it held each
tower's elevation angle from the centre, so a 189 m tower 400 m away
outsounded a 541 m one 3.4 km away, while the page said loudness follows
height; in 17 of 27 cities the tallest tower was not the loudest (QA,
sk_audio.py). The wheel was already drawn in metres; now the meter agrees
with it and with the page.

Run:  python build_skylines.py            report only
      python build_skylines.py --apply    write data/skylines.json
"""

import argparse
import datetime
import glob
import gzip
import json
import math
import os
import re

import keys as KEYS_MOD
from fetch_wikidata import CITIES

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "data", "raw")
OUT = os.path.join(HERE, "data", "skylines.json")

BINS = 360                 # one sample per degree of azimuth
# The headline count uses MIN_HEIGHT; the wheel takes the tallest buildings
# the city has down to RING_FLOOR, still a twelve-storey block, at most
# RING_MAX of them. The two numbers are reported separately on screen so
# nobody reads one as the other.
MIN_HEIGHT = 80.0
RING_FLOOR = 55.0
RING_MAX = 120
# A wheel needs enough towers to be worth turning: at least MIN_TALL at or
# above MIN_HEIGHT and MIN_RING on the wheel. Beijing once had seven towers in
# the database and a thousand in life; publishing it would say more about the
# database's coverage than about Beijing.
MIN_TALL, MIN_RING = 7, 16
TALLEST_BUILDING_M = 830.0  # Burj Khalifa, 828 m; anything above is a typo
EYE_M = 1.7
CLAMP_M = 400.0            # a tower closer than this is held at it
NEAR_KEEP_M = 120.0        # an unlinked OSM building this close may match
OSM_TOL = 0.20             # ...if its mapped height is within 20%

# Classes that mean "not a standing building", whatever else the item is.
NOT_STANDING = {
    "Q19860854": "destroyed building or structure",
    "Q56556915": "demolished or destroyed",
    "Q57644089": "destroyed church",
    "Q96084375": "former building or structure",
    "Q811683": "proposed building or structure",
    "Q124835105": "proposed tower",
    "Q64728694": "proposed entity",
    "Q25447168": "architectural project",
    "Q12372814": "engineering project",
    "Q21514702": "abandoned project",
    "Q1570262": "unfinished building",
    "Q12377751": "building or structure under construction",
    "Q1441983": "redevelopment",
}
# States of use (P5817) that mean the same. "In use", "permanently closed",
# "topped out" and "under reconstruction" all describe something standing.
STATE_NOT_STANDING = {
    "Q12377751": "under construction", "Q56556915": "demolished or destroyed",
    "Q811683": "proposed", "Q97317113": "on hold", "Q30108381": "cancelled",
}
# Structures Wikidata files under building that a skyline is not made of.
TOWER = {
    "Q12518": "tower", "Q11166728": "television tower",
    "Q1440300": "observation tower", "Q1068623": "transmitter mast",
    "Q1798641": "communication tower", "Q1440476": "lattice tower",
    "Q797765": "inclined tower", "Q853854": "clock tower",
    "Q81917": "fortified tower", "Q274153": "water tower",
    "Q5191724": "steeple", "Q815448": "belfry", "Q200334": "bell tower",
    "Q685204": "gate tower", "Q72926449": "church tower", "Q213643": "silo",
    "Q39715": "lighthouse", "Q1601458": "combined heat and power station",
    "Q13416228": "incinerator",
}
# ...unless the item is also one of these (a skyscraper that is also filed as
# a tower is a skyscraper).
HIGHRISE = {
    "Q11303": "skyscraper", "Q18142": "tower block",
    "Q2304397": "residential tower", "Q104829543": "supertall building",
    "Q1021645": "office building", "Q13402009": "apartment building",
    "Q27686": "hotel", "Q15622489": "skyscraper in Japan",
    "Q134570257": "office tower", "Q47012103": "mixed-use building",
    "Q11755959": "multi-story urban building",
}
# Buildings Wikidata files as groups of buildings rather than under building
# itself. Federation Tower (Moscow, 374 m), Emirates Towers and Franklin
# Center were dropped as "not a building" until the claims check of
# 2026-10-24 found them.
COMPLEX = {
    "Q1497364": "building complex", "Q118896406": "twin towers",
    "Q27556845": "skyscraper complex", "Q4298922": "mixed-use development",
}
# A tower Wikidata places only in its county, state or province (downtown
# Chicago and Calgary) is in the city if it stands within CORE_KM of the
# city's coordinate. One placed in another municipality never is.
CORE_KM = 3.0
ARCH, PINNACLE, OCCUPIED = "Q24192182", "Q26970842", "Q31271474"
ROOF = "Q83180"
# "applies to part" values that are not parts: two items qualify a whole-
# building height with the unit system it was given in (345 Park Avenue)
NOT_A_PART = {"Q641227", "Q232405"}  # imperial system, metric system
OSM_NOT_STANDING = ("construction", "proposed", "demolished", "abandoned",
                    "disused", "razed", "planned")

R_EARTH = 6371000.0


def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = (math.sin(dp / 2) ** 2 +
         math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * R_EARTH * math.asin(min(1.0, math.sqrt(a)))


def bearing(lat1, lon1, lat2, lon2):
    """Compass bearing from point 1 to point 2, in degrees clockwise from
    north. This is the azimuth a person standing at 1 would have to face."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def qid(uri):
    return uri.rsplit("/", 1)[-1]


def latest(pattern):
    hits = sorted(glob.glob(os.path.join(RAW_DIR, pattern)))
    if not hits:
        raise SystemExit(f"no {pattern} in {RAW_DIR}: run the fetch first")
    return hits[-1]


def load_raw():
    wpath, opath = latest("wikidata_*.json"), latest("osm_*.json.gz")
    wd = json.load(open(wpath, encoding="utf-8"))
    with gzip.open(opath, "rb") as fh:
        osm = json.loads(fh.read().decode("utf-8"))
    return wd, osm, os.path.basename(wpath), os.path.basename(opath)


def pick_height(stmts):
    """One height per item, from its P2048 statements (metres, via psn:).
    Deprecated statements are ignored; preferred ones win if any exist; then a
    statement qualified as architectural height, then an unqualified one
    (the most common case, and the tallest if there are several), then roof
    or occupied-floor height (Azabudai Hills Mori JP Tower carries only a
    roof and a spire height). Pinnacle and spire heights, and statements that
    apply to any other part of the item, are never used: a mast is not the
    building."""
    s = [dict(x, part="" if x["part"] in NOT_A_PART else x["part"])
         for x in stmts if not x["rank"].endswith("DeprecatedRank")]
    pref = [x for x in s if x["rank"].endswith("PreferredRank")]
    s = pref or s
    for test in (lambda x: x["crit"] == ARCH or x["part"] == ARCH,
                 lambda x: not x["crit"] and not x["part"],
                 lambda x: x["crit"] == OCCUPIED or x["part"] == ROOF):
        hit = [x["h"] for x in s if test(x)]
        if hit:
            return max(hit)
    return None


def items_for(city, wd=None):
    """Every item the pull returned for one city, with its facts gathered.
    With the whole pull, also whether an item outside the city by P131+ is
    located only in places the city is itself in (wd["located"])."""
    items = {}
    for f in city["facts"]:
        b = qid(f["b"]["value"])
        it = items.setdefault(b, {"qid": b, "cls": set(), "state": set(),
                                  "dem": False, "end": [], "open": [],
                                  "incep": [], "label": "", "in": False,
                                  "h": [], "coord": None})
        if "cls" in f:
            it["cls"].add(qid(f["cls"]["value"]))
        if "state" in f:
            it["state"].add(qid(f["state"]["value"]))
        it["dem"] |= "dem" in f
        for k in ("end", "open", "incep"):
            if k in f:
                it[k].append(f[k]["value"][:10])
        lab = f.get("bLabel", {}).get("value", "")
        if lab and not re.fullmatch(r"Q\d+", lab):
            it["label"] = lab
        it["in"] = f["inCity"]["value"] == "true"
    pt = re.compile(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)")
    for h in city["heights"]:
        b = qid(h["b"]["value"])
        if b not in items:
            continue
        m = pt.match(h["coord"]["value"])
        if m and items[b]["coord"] is None:
            items[b]["coord"] = (float(m.group(2)), float(m.group(1)))
        items[b]["h"].append({
            "h": float(h["hm"]["value"]), "rank": h["rank"]["value"],
            "part": qid(h["part"]["value"]) if "part" in h else "",
            "crit": qid(h["crit"]["value"]) if "crit" in h else ""})
    if wd is not None and "located" in wd:
        name = next(k for k, v in wd["cities"].items() if v is city)
        locs = {}
        for r in wd["located"]["cities"][name]["rows"]:
            locs.setdefault(qid(r["b"]["value"]), []).append(
                r["ancestor"]["value"] == "true")
        _, clat, clon = CITIES[name]
        for it in items.values():
            anc = locs.get(it["qid"])
            it["core"] = bool(
                not it["in"] and anc and all(anc) and it["coord"] and
                haversine(clat, clon, *it["coord"]) <= CORE_KM * 1000)
    return items


CLS_OK = {}


def set_classes(wd):
    """Which P31 classes are subclasses of building, from the archived
    class query."""
    CLS_OK.clear()
    CLS_OK.update({qid(r["cls"]["value"]): r["isBuilding"]["value"] == "true"
                   for r in wd["classes"]})


def wikidata_verdict(it, today):
    """(height, None) if Wikidata alone would keep this item, else
    (None, (the count it falls under, the reason to report))."""
    cl = it["cls"]
    if not any(CLS_OK.get(c) for c in cl) and not cl & set(COMPLEX):
        return None, ("not building", "")
    if cl & set(TOWER) and not cl & set(HIGHRISE):
        return None, ("tower structure", "tower structure")
    if not it["in"] and not it.get("core"):
        return None, ("outside city", "outside city")
    # Height before standing, so every item the standing tests reject is a
    # building of RING_FLOOR or more in the city: the page's "one in ten"
    # divides by exactly that set.
    h = pick_height(it["h"])
    if h is None or it["coord"] is None:
        return None, ("no usable height", "")
    if h < RING_FLOOR:
        return None, ("below floor", "")
    if h > TALLEST_BUILDING_M:
        return None, ("implausible height", f"height {h:.0f} m")
    why = ([NOT_STANDING[c] for c in sorted(cl) if c in NOT_STANDING] +
           [STATE_NOT_STANDING[s] for s in sorted(it["state"])
            if s in STATE_NOT_STANDING])
    if it["dem"]:
        why.append("demolition date")
    if any(e <= today for e in it["end"]):
        why.append("end date")
    if why:
        return None, ("not standing (Wikidata)", "; ".join(why))
    return h, None


def osm_rec(e):
    t = e.get("tags", {})
    c = e.get("center") or ({"lat": e["lat"], "lon": e["lon"]}
                            if "lat" in e else None)
    if not c:
        return None
    b = t.get("building") or t.get("building:part") or ""
    dead = (b in OSM_NOT_STANDING or
            any(k in t for k in ("construction", "proposed", "demolished",
                                 "construction:building")) or
            any(k.startswith(p + ":") for k in t
                for p in ("demolished", "razed", "was", "proposed")))

    def num(key):
        m = re.match(r"\s*([\d.]+)", t.get(key, ""))
        if not m:
            return None
        try:
            v = float(m.group(1))
        except ValueError:
            return None
        if "ft" in t.get(key, "") or "'" in t.get(key, ""):
            v *= 0.3048
        return v
    return {"id": f"{e['type']}/{e['id']}", "lat": c["lat"], "lon": c["lon"],
            "h": num("height"), "levels": num("building:levels"),
            "standing": not dead,
            "names": [t[k] for k in ("name", "name:en", "alt_name",
                                     "official_name") if t.get(k)],
            "qids": [q.strip() for q in t.get("wikidata", "")
                     .replace(",", ";").split(";") if q.strip()]}


def osm_index(city):
    byq = {}
    for e in city["linked"]:
        r = osm_rec(e)
        if r:
            for q in r["qids"]:
                byq.setdefault(q, []).append(r)
    near = [r for r in map(osm_rec, city["near"]) if r]
    return byq, near


def osm_match(it, h, byq, near):
    """The OSM building that confirms this tower stands, or None.

    First OSM's own link: a building tagged with the item's QID. A link only
    to something OSM tags as under construction, proposed or demolished is a
    no, whatever else stands nearby. Failing a link, a standing building or
    building part within NEAR_KEEP_M of the item's coordinate that agrees on
    height (OSM_TOL, or its storeys at 3.5 m each within 30%) or carries the
    same name. A building there that agrees on neither is the tower's site,
    not the tower: 1 Park Lane's site holds a hotel a third of its height."""
    linked = byq.get(it["qid"], [])
    lat, lon = it["coord"]
    if linked:
        up = [r for r in linked if r["standing"]]
        if not up:
            return None
        return min(up, key=lambda r: haversine(lat, lon, r["lat"], r["lon"]))
    me = norm_name(it["label"])
    best = None
    for r in near:
        # A building OSM links to a different item is that item, not this
        # one: unfinished Marina 106 matched Marina 101 next door by height.
        if not r["standing"] or (r["qids"] and it["qid"] not in r["qids"]):
            continue
        d = haversine(lat, lon, r["lat"], r["lon"])
        if d > NEAR_KEEP_M:
            continue
        ok = ((r["h"] and abs(r["h"] - h) <= OSM_TOL * h) or
              (r["levels"] and abs(3.5 * r["levels"] - h) <= 0.30 * h) or
              (len(me) >= 4 and any(norm_name(n) == me for n in r["names"])))
        if ok and (best is None or d < best[0]):
            best = (d, r)
    return best[1] if best else None


def norm_name(s):
    s = (s or "").lower()
    s = re.sub(r"\b(the|tower|towers|building|torre|tour|turm|wieza)\b", " ", s)
    return re.sub(r"[^\w]+", "", s)


def filter_city(name, wd_city, osm_city, today, wd=None):
    items = items_for(wd_city, wd)
    byq, near = osm_index(osm_city)
    count = {k: 0 for k in ("items", "not building", "tower structure",
                            "outside city", "not standing (Wikidata)",
                            "no usable height", "below floor",
                            "implausible height", "not in OSM",
                            "duplicate", "kept")}
    dropped, kept = [], []
    for it in sorted(items.values(), key=lambda x: x["qid"]):
        count["items"] += 1
        h, why = wikidata_verdict(it, today)
        if h is None:
            count[why[0]] += 1
            if why[1]:
                dropped.append((it, why[1]))
            continue
        om = osm_match(it, h, byq, near)
        if om is None:
            count["not in OSM"] += 1
            dropped.append((it, "not in OSM"))
            continue
        year = None
        for d in sorted(it["open"]) + sorted(it["incep"]):
            if re.match(r"\d{4}", d):
                year = int(d[:4])
                break
        kept.append({"qid": it["qid"], "name": it["label"], "h": h,
                     "lat": it["coord"][0], "lon": it["coord"][1],
                     "year": year, "osm": om["id"], "osm_h": om["h"],
                     "osm_linked": bool(byq.get(it["qid"]))})
    # once: a linked, named, taller item wins a duplicate pair. Two items
    # OSM links to two different buildings are two buildings, even on one
    # spot at one height: 10 and 15 Hudson Yards share a Wikidata coordinate.
    kept.sort(key=lambda b: (not b["osm_linked"], not b["name"], -b["h"],
                             b["qid"]))
    out = []
    for b in kept:
        dup = None
        for o in out:
            d = haversine(b["lat"], b["lon"], o["lat"], o["lon"])
            if (b["osm"] == o["osm"] or
                    (norm_name(b["name"]) and
                     norm_name(b["name"]) == norm_name(o["name"]) and
                     d < 300) or
                    (d < 30 and abs(b["h"] - o["h"]) <= 0.05 * o["h"] and
                     not (b["osm_linked"] and o["osm_linked"]))):
                dup = o
                break
        if dup:
            count["duplicate"] += 1
            dropped.append(({"qid": b["qid"], "label": b["name"]},
                            f"duplicate of {dup['qid']} {dup['name']}"))
            continue
        out.append(b)
    count["kept"] = len(out)
    return out, count, dropped


def build(apply=False):
    wd, osm, wname, oname = load_raw()
    today = wd["fetched"]
    set_classes(wd)
    print(f"  sources: {wname} (fetched {wd['fetched']}), {oname} "
          f"(fetched {osm['fetched']})")
    out, gone, report = [], [], {}
    for name in CITIES:
        towers, count, dropped = filter_city(name, wd["cities"][name],
                                             osm["cities"][name], today, wd)
        report[name] = {"count": count,
                        "dropped": [[d[0]["qid"], d[0].get("label", ""), why]
                                    for d, why in
                                    ((x, x[1]) for x in dropped)]}
        mem = [b for b in towers if b["h"] >= MIN_HEIGHT]
        if len(mem) < MIN_TALL or len(towers) < MIN_RING:
            gone.append((name, len(mem), len(towers)))
            continue
        peak = max(mem, key=lambda b: b["h"])
        rw = sum(b["h"] for b in mem)
        rlat = sum(b["lat"] * b["h"] for b in mem) / rw
        rlon = sum(b["lon"] * b["h"] for b in mem) / rw

        # The wheel keeps the towers' true compass ORDER, clockwise from
        # north as on the ground, but equalises their SPACING so the ring is
        # full. A downtown fills perhaps forty degrees of a real horizon, so
        # a faithful wheel would be mostly empty sky: turn ninety degrees and
        # the screen is blank. Neighbours on the wheel are neighbours in the
        # city; the angle between them is not.
        picked = sorted(towers, key=lambda x: (-x["h"], x["qid"]))[:RING_MAX]
        for b in picked:
            b["_az"] = bearing(rlat, rlon, b["lat"], b["lon"])
            b["_d"] = max(CLAMP_M, haversine(rlat, rlon, b["lat"], b["lon"]))
        picked.sort(key=lambda b: (b["_az"], b["qid"]))
        n = len(picked)
        ring = [[round(360.0 * i / n, 2),
                 round(math.degrees(math.atan2(b["h"] - EYE_M, b["_d"])), 3),
                 round(b["_d"] / 1000.0, 3), round(b["h"], 1), b["name"],
                 b["year"] or 0, round(b["_az"], 1), b["qid"]]
                for i, b in enumerate(picked)]

        # The meter: each slot carries its tower's HEIGHT, so what sounds
        # loudest is what stands tallest (see the docstring).
        rprof = [0.0] * BINS
        half = max(1.2, 0.5 * 360.0 / n)
        for r in ring:
            for i in range(int(math.floor(r[0] - half)),
                           int(math.ceil(r[0] + half)) + 1):
                rprof[i % BINS] = max(rprof[i % BINS], r[3])

        look = max(ring, key=lambda r: r[3])[0]
        named = [{"n": b["name"], "h": round(b["h"], 1), "y": b["year"]}
                 for b in sorted(mem, key=lambda x: -x["h"]) if b["name"]][:20]
        withosm = [b for b in towers if b["osm_h"]]
        out.append({
            "city": name,
            "n": len(mem), "mass": round(math.sqrt(sum(b["h"] ** 2
                                                       for b in mem)), 1),
            "tallest": round(peak["h"], 1), "tallestName": peak["name"],
            "median": round(sorted(b["h"] for b in mem)[len(mem) // 2], 1),
            "look": round(look, 1), "towers": named, "ring": ring,
            "rprof": [round(v, 1) for v in rprof],
            "centre": [round(rlat, 5), round(rlon, 5)],
            "key": KEYS_MOD.key_for(name),
            "osmLinked": sum(b["osm_linked"] for b in towers),
            "osmHeights": len(withosm),
            "osmWithin10": sum(abs(b["osm_h"] - b["h"]) <= 0.10 * b["h"]
                               for b in withosm),
        })

    print(f"\n  {'city':12s} {'items':>5s} {'notbld':>6s} {'tower':>5s} "
          f"{'outside':>7s} {'unbuilt':>7s} {'noOSM':>5s} {'dup':>4s} "
          f"{'kept':>4s} {'>=80':>4s}  tallest")
    for name in CITIES:
        c = report[name]["count"]
        city = next((x for x in out if x["city"] == name), None)
        print(f"  {name:12s} {c['items']:5d} {c['not building']:6d} "
              f"{c['tower structure']:5d} {c['outside city']:7d} "
              f"{c['not standing (Wikidata)']:7d} {c['not in OSM']:5d} "
              f"{c['duplicate']:4d} {c['kept']:4d} "
              f"{city['n'] if city else 0:4d}  "
              + (f"{city['tallestName']} {city['tallest']:.0f} m" if city
                 else "DROPPED: too thin for a wheel"))
    print(f"  {len(out)} cities; dropped: " +
          ", ".join(f"{g[0]} ({g[1]} at {MIN_HEIGHT:.0f} m, {g[2]} on the "
                    f"wheel)" for g in gone))
    if not apply:
        print("\n  report only. Re-run with --apply.")
        return out, gone, report
    payload = {"bins": BINS, "minHeight": MIN_HEIGHT, "ringFloor": RING_FLOOR,
               "sources": {"wikidata": wname, "wikidataFetched": wd["fetched"],
                           "osm": oname, "osmFetched": osm["fetched"]},
               "dropped": [{"city": g[0], "tall": g[1], "ring": g[2]}
                           for g in gone],
               "cities": out}
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    rep = os.path.join(HERE, "data", "filter_report.json")
    with open(rep, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(f"\n  wrote {OUT} ({os.path.getsize(OUT) / 1024:.0f} kB) and "
          f"{os.path.basename(rep)}")
    return out, gone, report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    build(ap.parse_args().apply)
