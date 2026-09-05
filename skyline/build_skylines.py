"""
Turn real buildings into a 360-degree skyline profile, one per city.

The observation this project rests on is that a skyline and a spectrum
analyser are the same picture. Both are a row of vertical bars of varying
height; both are read left to right; and in both the tall spikes are what the
eye goes to. That is a coincidence of drawing conventions rather than of
physics, but it is a usable one, because it means a city can be played.

What is real here and what is not, stated plainly, because sonification
projects usually blur this:

  REAL. Every building is a Wikidata entity with a published structural
  height and a published coordinate (or, for the three supplemented cities,
  a row of the city's published tallest-buildings list - see supplement.py).
  Compass order around the wheel is the true bearing order from the
  height-weighted centroid of the city's towers; distance from that centroid
  is measured, then clamped to 400 m so a tower the observer is standing
  under does not dwarf the rest.

  A warning worth recording, because the first version of this file shipped
  with it. Wikidata's height property applies to anything with a height:
  mountains, waterfalls, bridges, dams, radio masts, and - genuinely - nuclear
  weapons tests. Asking for "things over 120 metres near a city" produced a
  950-metre tower in Rotterdam, which is a suspension bridge. And the property
  carries a unit, so a value of 950 may be feet. Both are fixed here: heights
  come back normalised to metres, and the class of every entity is checked
  against a list of things that are actually buildings, with everything
  rejected being reported rather than silently dropped.

  REARRANGED. The spacing around the wheel: equalised, so the ring is full.
  Order survives, angle does not. The app says so on screen.

  INVENTED. The sound. There is no sense in which a city has a pitch. The
  mapping from geometry to audio is a choice, it is documented in the app, and
  it is deterministic - the same skyline always produces the same sound.

There used to be a second, "realistic" rendering: a true panorama from a
chosen viewpoint outside the city, with occlusion and empty sky. It was
retired before the page shipped, but its geometry (`prof`, `draw`, `view`,
`dist`, and the viewpoint bearings inside `towers` and `look`) was still
being emitted, and skyline.html described it as the instrument's measured
behaviour, until 2026-09-04. None of it is emitted any more: the wheel is
the only rendering and the output holds only what the app reads. viewpoint()
and profile() below are kept for the record and are not called.

The raw pull this file reads, data/raw/wikidata_buildings.json, was never
archived, so this script cannot currently be run. The shipped
data/skylines.json was brought to this shape by prune_payload.py instead.

WHAT A FRESH PULL WOULD TAKE (written 2026-09-05, so nobody has to rediscover
it): one SPARQL query per city against query.wikidata.org, asking for every
item within a radius of the city's centroid (wikibase:around, ~25 km) that
has a height (P2048, read through psv: so the unit comes back and feet can
be converted) and a coordinate (P625), and whose class (P31, followed up
P279*) is on this file's list of things that are buildings - the class check
and the unit check are the two fixes recorded above, and the pull must keep
them. Twenty-seven cities, so twenty-seven queries, each under the service's
sixty-second limit if the radius is kept small; the whole pull is minutes.
Save the raw answers to data/raw/wikidata_buildings.json AND commit it,
because a raw pull that is not archived is the reason this note exists.
Then: run this script, run supplement.py's three cities (their published
lists overrule Wikidata above each list's floor), run test_app.js (43
checks: no empty bearing, no label collision at eight bearings), and
regenerate skyline_towers.png. Expect a different dataset: heights get
corrected on Wikidata, towers finish and get added, and every downstream
number on skyline.html (the tallest, the twenty named per city, the notes
line) moves with it. That is a new release of the project, not a rebuild
of this one; the shipped data/skylines.json stays the dataset of record
until someone does it.

Run:  python3 build_skylines.py            report only
      python3 build_skylines.py --apply    write data/skylines.json
"""

import argparse
import json
import math
import os
import re

import keys as KEYS_MOD
import supplement as SUPP

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw", "wikidata_buildings.json")
OUT = os.path.join(HERE, "data", "skylines.json")

BINS = 360                 # one sample per degree of azimuth
# 120 m was the wrong floor. It is a defensible definition of "tall building"
# and it left Chongqing with nine towers, because Wikidata's coverage thins
# fast below the famous ones - so turning to a bearing with nothing in it gave
# a blank screen, which is accurate and useless. 80 m is still a high-rise by
# any definition and roughly triples the set.
MIN_HEIGHT = 80.0
# The headline count and the city ranking use MIN_HEIGHT. The wheel does not:
# a ring of seven towers is a bad carousel however defensible its floor, so it
# takes the tallest buildings the city has down to RING_FLOOR, which is still
# a twelve-storey block. The two numbers are reported separately on screen so
# nobody reads one as the other.
RING_FLOOR = 55.0
RADIUS_KM = 35.0           # how far from a centre a building may be and count
EYE_M = 1.7                # observer eye height

# Candidate cities. Assignment is by proximity, so this list only has to
# contain the places that have skylines; the top fifty are then chosen by how
# much skyline each one actually turns out to have, not by reputation.
CITIES = [
    ("Hong Kong", "China", 22.302, 114.177), ("Shenzhen", "China", 22.543, 114.058),
    ("New York", "United States", 40.713, -74.006), ("Dubai", "UAE", 25.205, 55.271),
    ("Shanghai", "China", 31.230, 121.474), ("Tokyo", "Japan", 35.690, 139.692),
    ("Chicago", "United States", 41.878, -87.630), ("Guangzhou", "China", 23.129, 113.264),
    ("Kuala Lumpur", "Malaysia", 3.139, 101.687), ("Chongqing", "China", 29.563, 106.551),
    ("Singapore", "Singapore", 1.352, 103.820), ("Seoul", "South Korea", 37.567, 126.978),
    ("Toronto", "Canada", 43.653, -79.383), ("Bangkok", "Thailand", 13.756, 100.502),
    ("Wuhan", "China", 30.593, 114.306), ("Jakarta", "Indonesia", -6.208, 106.846),
    ("Melbourne", "Australia", -37.814, 144.963), ("Sydney", "Australia", -33.869, 151.209),
    ("Miami", "United States", 25.762, -80.192), ("Busan", "South Korea", 35.180, 129.075),
    ("Panama City", "Panama", 8.983, -79.517), ("Istanbul", "Turkey", 41.008, 28.978),
    ("Moscow", "Russia", 55.756, 37.617), ("Mumbai", "India", 19.076, 72.878),
    ("Doha", "Qatar", 25.286, 51.531), ("Riyadh", "Saudi Arabia", 24.713, 46.675),
    ("Nanjing", "China", 32.061, 118.796), ("Tianjin", "China", 39.343, 117.361),
    ("Beijing", "China", 39.904, 116.407), ("Shenyang", "China", 41.805, 123.431),
    ("Changsha", "China", 28.228, 112.939), ("Suzhou", "China", 31.299, 120.585),
    ("Hangzhou", "China", 30.274, 120.155), ("Chengdu", "China", 30.573, 104.067),
    ("Dalian", "China", 38.914, 121.615), ("Qingdao", "China", 36.067, 120.383),
    ("Xiamen", "China", 24.480, 118.089), ("Wuxi", "China", 31.491, 120.312),
    ("Taipei", "Taiwan", 25.033, 121.565), ("Manila", "Philippines", 14.599, 120.984),
    ("Ho Chi Minh City", "Vietnam", 10.823, 106.630), ("Osaka", "Japan", 34.694, 135.502),
    ("Los Angeles", "United States", 34.052, -118.244),
    ("San Francisco", "United States", 37.775, -122.419),
    ("Houston", "United States", 29.760, -95.370),
    ("Austin", "United States", 30.267, -97.743),
    ("Fort Worth", "United States", 32.7555, -97.3308),
    ("Nashville", "United States", 36.163, -86.781), ("Boston", "United States", 42.360, -71.059),
    ("Philadelphia", "United States", 39.953, -75.165),
    ("Atlanta", "United States", 33.749, -84.388), ("Seattle", "United States", 47.606, -122.332),
    ("Dallas", "United States", 32.777, -96.797), ("Las Vegas", "United States", 36.170, -115.140),
    ("Vancouver", "Canada", 49.283, -123.121), ("Calgary", "Canada", 51.045, -114.057),
    ("Montreal", "Canada", 45.502, -73.567), ("Mexico City", "Mexico", 19.433, -99.133),
    ("Sao Paulo", "Brazil", -23.551, -46.633), ("Rio de Janeiro", "Brazil", -22.907, -43.173),
    ("Buenos Aires", "Argentina", -34.604, -58.382), ("Santiago", "Chile", -33.449, -70.669),
    ("London", "United Kingdom", 51.507, -0.128), ("Paris", "France", 48.857, 2.352),
    ("Frankfurt", "Germany", 50.111, 8.682), ("Madrid", "Spain", 40.417, -3.704),
    ("Milan", "Italy", 45.464, 9.190), ("Warsaw", "Poland", 52.230, 21.012),
    ("Rotterdam", "Netherlands", 51.924, 4.478), ("Benidorm", "Spain", 38.538, -0.131),
    ("Tel Aviv", "Israel", 32.085, 34.781), ("Abu Dhabi", "UAE", 24.453, 54.377),
    ("Kuwait City", "Kuwait", 29.376, 47.977), ("Manama", "Bahrain", 26.229, 50.586),
    ("Cairo", "Egypt", 30.044, 31.236), ("Johannesburg", "South Africa", -26.204, 28.047),
    ("Lagos", "Nigeria", 6.524, 3.379), ("Nairobi", "Kenya", -1.286, 36.817),
    ("Auckland", "New Zealand", -36.848, 174.763), ("Honolulu", "United States", 21.307, -157.858),
    ("Gold Coast", "Australia", -28.017, 153.400), ("Brisbane", "Australia", -27.469, 153.025),
    ("Perth", "Australia", -31.953, 115.857), ("Astana", "Kazakhstan", 51.169, 71.449),
    ("Baku", "Azerbaijan", 40.409, 49.867), ("Delhi", "India", 28.614, 77.209),
    ("Kolkata", "India", 22.573, 88.364), ("Colombo", "Sri Lanka", 6.927, 79.861),
    ("Jeddah", "Saudi Arabia", 21.486, 39.192), ("Amman", "Jordan", 31.956, 35.945),
    ("Vienna", "Austria", 48.208, 16.373), ("Brussels", "Belgium", 50.851, 4.352),
    ("Lisbon", "Portugal", 38.722, -9.139), ("Stockholm", "Sweden", 59.329, 18.069),
]

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


def offset(lat, lon, brg, dist_m):
    """A point dist_m away on bearing brg."""
    p1 = math.radians(lat)
    l1 = math.radians(lon)
    b = math.radians(brg)
    d = dist_m / R_EARTH
    p2 = math.asin(math.sin(p1) * math.cos(d) +
                   math.cos(p1) * math.sin(d) * math.cos(b))
    l2 = l1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(p1),
                         math.cos(d) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), (math.degrees(l2) + 540) % 360 - 180


# What counts as skyline. Towers that dominate a horizon - television and
# observation towers - are in, because they are what people photograph;
# bridges, masts and mountains are out, because they are not what anybody
# means by a skyline even when they are taller than one.
KEEP = ("skyscraper", "tower block", "office building", "building complex",
        "residential", "apartment", "condominium", "twin towers", "high-rise",
        "hotel", "television tower", "observation tower", "clock tower",
        "commercial building", "mixed-use", "administrative building",
        "government building", "bell tower", "minaret", "cathedral",
        "church building", "tower")
DROP = ("waterfall", "mountain", "hill", "bridge", "mast", "transmitter",
        "settlement", "village", "town", "city", "dam", "power station",
        "weapon", "chimney", "volcano", "peak", "canyon", "lake", "river",
        "island", "cave", "mine", "antenna", "pylon", "crane", "wind",
        "lighthouse", "viaduct", "aqueduct", "stadium", "cooling")


def is_building(cls_label):
    c = (cls_label or "").lower()
    if any(k in c for k in DROP):
        return False
    return any(k in c for k in KEEP)


def load_buildings():
    d = json.load(open(RAW, encoding="utf-8"))
    pt = re.compile(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)")
    # one entity may carry several class statements, so keep the entity if any
    # of them is a building, and count it once
    ok_ids, all_ids, rejected = set(), set(), {}
    for b in d["results"]["bindings"]:
        qid = b["b"]["value"]
        all_ids.add(qid)
        cl = b.get("clsLabel", {}).get("value", "")
        if is_building(cl):
            ok_ids.add(qid)
        else:
            rejected[cl] = rejected.get(cl, 0) + 1
    for cl in list(rejected):
        pass
    print(f"  {len(all_ids):,} entities returned, {len(ok_ids):,} are "
          f"buildings")
    top = sorted(rejected.items(), key=lambda kv: -kv[1])[:6]
    print("  largest rejected classes: " +
          ", ".join(f"{k} ({n})" for k, n in top))

    seen = set()
    out = []
    for b in d["results"]["bindings"]:
        if b["b"]["value"] not in ok_ids or b["b"]["value"] in seen:
            continue
        seen.add(b["b"]["value"])
        m = pt.match(b["coord"]["value"])
        if not m:
            continue
        try:
            h = float(b["h"]["value"])
        except (KeyError, ValueError):
            continue
        if h < RING_FLOOR or h > 830.0:
            continue
        name = b.get("bLabel", {}).get("value", "")
        if name.startswith("Q") and name[1:].isdigit():
            name = ""
        year = None
        if "start" in b:
            ym = re.match(r"(-?\d{4})", b["start"]["value"])
            if ym:
                year = int(ym.group(1))
        out.append({"name": name, "h": h,
                    "lon": float(m.group(1)), "lat": float(m.group(2)),
                    "year": year,
                    # the entity id, so the page can link to the record it
                    # came from; hand-entered buildings have none and are
                    # therefore not linked
                    "qid": b["b"]["value"].rsplit("/", 1)[-1]})
    return out


def assign(buildings):
    """Nearest city within RADIUS_KM. A building more than that from any of
    the listed centres is not part of a skyline anybody looks at, and is
    dropped rather than forced into the closest one."""
    lim = RADIUS_KM * 1000.0
    groups = {}
    unplaced = 0
    byname = {c[0]: c for c in CITIES}
    for b in buildings:
        best, bestd = None, lim
        for name, country, lat, lon in CITIES:
            # cheap rejection first; haversine on 6,623 x 90 is wasteful
            if abs(lat - b["lat"]) > 0.45 or abs(lon - b["lon"]) > 0.55:
                continue
            d = haversine(lat, lon, b["lat"], b["lon"])
            if d < bestd:
                best, bestd = (name, country, lat, lon), d
        if best is None:
            unplaced += 1
            continue
        groups.setdefault(best, []).append(b)
    # Cities the database barely covers get a supplement transcribed from
    # published records, kept in its own file and marked in the output.
    # A database row that is the same building under a different name -
    # "505 Nashville" against "505", say - would be drawn twice, so any
    # database row standing within 150 m and 15 m of height of a supplement
    # row is taken to be that row and dropped in its favour. Nothing else is
    # touched.
    for name, rows in SUPP.SUPPLEMENT.items():
        key = byname.get(name)
        if not key:
            continue
        supp = SUPP.rows_for(name)
        db = groups.get(key, [])
        names = {b["name"] for b in supp}
        # Above the published list's own floor, the published list is
        # complete: it records every finished building that tall. A database
        # row up there that the list does not have is a proposal, a
        # demolition, or a misrecorded height - Wikidata carried the never
        # built 228.6 m Paramount Tower for Nashville as if it stood - so it
        # is dropped and named. Below the floor the database still fills the
        # wheel.
        floor = SUPP.LIST_FLOOR[name]
        kept, dropped = [], 0
        for b in db:
            dup = b["name"] in names or any(
                haversine(b["lat"], b["lon"], s["lat"], s["lon"]) < 150.0
                and abs(b["h"] - s["h"]) < 15.0 for s in supp)
            if dup:
                dropped += 1
            elif b["h"] >= floor:
                print(f"  {name}: dropping {b['name'] or b.get('qid', '?')} "
                      f"({b['h']:.0f} m) - absent from the published list "
                      f"at a height it covers")
            else:
                kept.append(b)
        groups[key] = kept + supp
        print(f"  {name}: {len(supp)} published rows added, {dropped} "
              f"database duplicates dropped ({len(groups[key])} total)")
    return groups, unplaced


def viewpoint(city, blds):
    """Where to stand. Far enough out to see the cluster whole, on the bearing
    that puts the most of it in front of you."""
    name, country, clat, clon = city
    # centroid weighted by height, so the viewpoint answers to the towers
    # rather than to the outliers
    wsum = sum(b["h"] for b in blds)
    mlat = sum(b["lat"] * b["h"] for b in blds) / wsum
    mlon = sum(b["lon"] * b["h"] for b in blds) / wsum

    # Stand outside the whole cluster, not outside its middle. Placing the
    # observer at a fixed distance from the centroid put them inside Dubai,
    # 200 metres from the Burj Khalifa, which then filled 75 degrees of the
    # sky. The 90th percentile is used rather than the maximum so that one
    # outlying tower in a suburb does not push the viewer into the next
    # county.
    ds = sorted(haversine(mlat, mlon, b["lat"], b["lon"]) for b in blds)
    spread = ds[int(0.90 * (len(ds) - 1))]
    dist = max(2500.0, min(14000.0, spread + 2600.0))

    best_brg, best_score = 0.0, -1.0
    for brg in range(0, 360, 5):
        vlat, vlon = offset(mlat, mlon, brg, dist)
        # looking back towards the centroid
        look = (brg + 180.0) % 360.0
        score = 0.0
        for b in blds:
            a = bearing(vlat, vlon, b["lat"], b["lon"])
            off = abs((a - look + 180.0) % 360.0 - 180.0)
            if off <= 60.0:
                d = max(300.0, haversine(vlat, vlon, b["lat"], b["lon"]))
                score += math.atan2(b["h"], d)
        if score > best_score:
            best_brg, best_score = float(brg), score

    vlat, vlon = offset(mlat, mlon, best_brg, dist)
    return vlat, vlon, (best_brg + 180.0) % 360.0, dist


def profile(vlat, vlon, blds, inside=False):
    """Apparent elevation angle of the skyline at each degree of azimuth.

    A building occupies a wedge of the horizon whose width falls off with
    distance, and stands at an apparent height of arctan(h/d). Taking the
    maximum over every building that covers a bin is what makes this a
    silhouette rather than a sum: a tower behind a taller tower contributes
    nothing, which is exactly what your eye does.
    """
    prof = [0.0] * BINS
    owner = [None] * BINS
    for b in blds:
        d = haversine(vlat, vlon, b["lat"], b["lon"])
        # A tower the observer is standing under is not part of a skyline.
        # From the panorama viewpoint that means dropping it; from the centre
        # of a downtown it means holding it at arm's length, because there the
        # near towers are the point.
        if d < 600.0:
            if not inside:
                continue
            d = 220.0
        a = bearing(vlat, vlon, b["lat"], b["lon"])
        # Wikidata has no footprint, so width is inferred from height.
        w = min(70.0, max(25.0, 0.18 * b["h"]))
        half = math.degrees(math.atan2(w / 2.0, d))
        elev = math.degrees(math.atan2(b["h"] - EYE_M, d))
        lo = a - half
        hi = a + half
        i0 = int(math.floor(lo))
        i1 = int(math.ceil(hi))
        for i in range(i0, i1 + 1):
            k = i % BINS
            if elev > prof[k]:
                prof[k] = elev
                owner[k] = b
    return prof, owner


def build(apply=False):
    blds = load_buildings()
    groups, unplaced = assign(blds)
    print(f"  {len(blds):,} buildings at or above {RING_FLOOR:.0f} m")
    print(f"  {len(groups)} cities matched, {unplaced:,} buildings outside "
          f"every listed centre")

    ranked = []
    for city, allmem in groups.items():
        # Two floors, and both have to be cleared. A city needs a real skyline
        # to be worth ranking, and enough buildings of any size to make a
        # wheel worth turning. Beijing has seven towers in this database and a
        # thousand in life; publishing it would say more about the database's
        # coverage than about Beijing, and a reader would take it for the
        # second thing.
        mem = [b for b in allmem if b["h"] >= MIN_HEIGHT]
        if len(mem) < 7 or len(allmem) < 16:
            continue
        # skyline mass: heights added in quadrature, so one very tall tower
        # does not outrank a genuine forest of them, but is not ignored either
        mass = math.sqrt(sum(b["h"] ** 2 for b in mem))
        ranked.append((mass, city, mem, allmem))
    ranked.sort(key=lambda r: -r[0])
    ranked = ranked[:50]

    out = []
    for mass, city, mem, allmem in ranked:
        name, country, clat, clon = city
        peak = max(mem, key=lambda b: b["h"])

        # ---- the ring ----------------------------------------------------
        # The panorama above is a true view: real bearings, real angles, and
        # for most cities two thirds of a full turn is empty sky, because a
        # downtown occupies perhaps forty degrees of anybody's horizon. That
        # is honest and it is a bad carousel - turn ninety degrees and the
        # screen is blank.
        #
        # So the wheel does one stated thing to the geography. Buildings keep
        # their true compass ORDER, going clockwise from north exactly as they
        # do on the ground, but their SPACING is equalised so the ring is full.
        # Neighbours on the wheel are neighbours in the city; the angle between
        # them is not the angle between them. It is the same liberty a transit
        # map takes with distance, taken for the same reason, and the app says
        # so on screen.
        rw = sum(b["h"] for b in mem)
        rlat = sum(b["lat"] * b["h"] for b in mem) / rw
        rlon = sum(b["lon"] * b["h"] for b in mem) / rw

        picked = sorted(allmem, key=lambda x: -x["h"])[:120]
        for b in picked:
            b["_az"] = bearing(rlat, rlon, b["lat"], b["lon"])
            # 120 m was too close: a tower that near subtends eighty degrees
            # and becomes the ceiling every other building is measured
            # against. 400 m is about as close as anyone stands to a
            # skyscraper and still calls it part of a skyline.
            b["_d"] = max(400.0, haversine(rlat, rlon, b["lat"], b["lon"]))
        picked.sort(key=lambda b: b["_az"])

        ring = []
        n = len(picked)
        for idx, b in enumerate(picked):
            slot = 360.0 * idx / n
            ring.append([
                round(slot, 2),                                   # equalised
                round(math.degrees(math.atan2(b["h"] - EYE_M, b["_d"])), 3),
                round(b["_d"] / 1000.0, 3),
                round(b["h"], 1),
                b["name"] or "",
                b["year"] or 0,
                round(b["_az"], 1),                               # where it is
                b.get("qid", ""),                                 # or nothing
            ])

        # The meter reads the wheel, not the panorama, so that what you hear
        # and what is in front of you are the same thing.
        rprof = [0.0] * BINS
        for r in ring:
            half = max(1.2, 0.5 * 360.0 / max(1, n))
            i0 = int(math.floor(r[0] - half))
            i1 = int(math.ceil(r[0] + half))
            for i in range(i0, i1 + 1):
                k = i % BINS
                if r[1] > rprof[k]:
                    rprof[k] = r[1]

        # The starting bearing: the equalised slot of the tallest tower, so
        # the wheel opens facing the building the city is known by.
        look = max(ring, key=lambda r: r[3])[0]
        # The twenty tallest, named: what build_skyline_figure.py draws.
        # Name, height, year only - the bearing and distance these used to
        # carry were from the retired viewpoint.
        named = []
        for b in sorted(mem, key=lambda x: -x["h"])[:20]:
            if not b["name"]:
                continue
            named.append({"n": b["name"], "h": round(b["h"], 1),
                          "y": b["year"]})
        named.sort(key=lambda x: -x["h"])
        key = KEYS_MOD.key_for(name)
        out.append({
            "city": name, "country": country,
            "n": len(mem), "mass": round(mass, 1),
            "tallest": round(peak["h"], 1), "tallestName": peak["name"],
            "median": round(sorted(b["h"] for b in mem)[len(mem) // 2], 1),
            "look": round(look, 1),
            "towers": named[:20],
            "ring": ring,
            "rprof": [round(v, 3) for v in rprof],
            "centre": [round(rlat, 5), round(rlon, 5)],
            "key": key,
            "hand": sum(1 for b in allmem if b.get("hand")),
        })
        if out[-1]["hand"]:
            # the height above which the published list overrules the
            # database; the app shows it beside the hand-entered count
            out[-1]["listFloor"] = SUPP.LIST_FLOOR[name]

    print(f"\n  {'city':20s} {'towers':>7s} {'tallest':>8s} {'ring':>6s}  key")
    for c in out[:14]:
        print(f"  {c['city']:20s} {c['n']:7,d} {c['tallest']:8.0f} "
              f"{len(c['ring']):6d}  {c['key']['label']} "
              f"({c['key']['tier'].lower()})")
    print(f"  ... {len(out)} cities in all")

    if not apply:
        print("\n  report only. Re-run with --apply.")
        return out
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"bins": BINS, "minHeight": MIN_HEIGHT,
                   "ringFloor": RING_FLOOR, "cities": out}, fh,
                  separators=(",", ":"))
    print(f"\n  wrote {OUT} ({os.path.getsize(OUT)/1024:.0f} kB)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    build(ap.parse_args().apply)
