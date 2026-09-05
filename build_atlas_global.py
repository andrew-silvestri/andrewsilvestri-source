"""
Rebuild the atlas payload with a world set of power plants and a wider
behaviour layer.

Two things were wrong with the previous build, and both were invisible until
somebody turned the globe.

The plant layer came from the United States Energy Information Administration,
so all four thousand of its units sat between longitude -167 and -68. Fifty-six
per cent of the atlas was one country. Rotating the globe therefore did not
reveal a world model; it revealed North America and then a lot of ocean. The
World Resources Institute's global database carries 34,936 plants in 167
countries with coordinates, capacity and fuel, which is the same quantity of
information about the whole planet rather than about one part of it. Above a
ten-megawatt floor it holds 21,337 units, 163 countries and 99.1% of world
generating capacity, and the United States falls back to its real share, which
is about a fifth.

The behaviour layer had six channels. Six is enough to say the layer exists and
too few to say anything with it, so it is widened here to a full set of
behavioural mechanisms placed on named Allen Brain Atlas regions.

Everything else in the scene, the grids and markets and disasters and demand
cohorts, is carried across unchanged from the model of record.

Run:  python3 build_atlas_global.py
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
SCENE = os.path.join(PARENT, "19 Atlas v6", "scene_v6.json")
PLANTS = os.path.join(PARENT, "19 Atlas v6", "raw",
                      "global_power_plant_database.csv")
OUT = os.path.join(HERE, "site", "assets", "atlas-data.js")

sys.path.insert(0, HERE)
from build_atlas import coastlines, KINDS            # noqa: E402

MIN_MW = 0.0     # every plant in the database, down to the smallest

CITIES = os.path.join(PARENT, "19 Atlas v6", "raw", "cities15000.zip")
ADMIN1 = os.path.join(PARENT, "19 Atlas v6", "raw", "admin1CodesASCII.txt")
QUAKES = os.path.join(PARENT, "19 Atlas v6", "raw", "usgs_quakes.csv")
PORTS = os.path.join(PARENT, "19 Atlas v6", "raw", "wpi.json")
ALLEN_TREE = os.path.join(PARENT, "19 Atlas v6", "raw", "allen_structures.json")
ALLEN_XYZ = os.path.join(PARENT, "19 Atlas v6", "raw", "allen_centers.json")
CINFO = os.path.join(PARENT, "19 Atlas v6", "raw", "countryInfo.txt")


def iso2_to_iso3():
    """GeoNames identifies countries by two letters and the grid nodes by
    three. Taking the first two letters of the three-letter code as the
    two-letter one is right often enough to look like it works - USA to US,
    FRA to FR - and wrong for Aruba, Switzerland's neighbours and about a
    fifth of the world, which is how twenty per cent of the cities and ports
    ended up wired to nothing."""
    m = {}
    if not os.path.exists(CINFO):
        return m
    for line in open(CINFO, encoding="utf-8", errors="replace"):
        if line.startswith("#") or not line.strip():
            continue
        f = line.split("\t")
        if len(f) > 2 and len(f[0]) == 2 and len(f[1]) == 3:
            m[f[0]] = f[1]
    return m

# ------------------------------------------------------------------ brain ---
# Behavioural mechanisms, each placed on a named region. The regions are real
# and the assignment is defensible rather than measured: this is a model of
# where demand decisions are made, not a claim about neuroanatomy, and the
# application says so on screen.
BRAIN = [
    ("present_bias",   "CTXpl: Cortical plate",                  [0.00,  0.42,  0.62]),
    ("dissonance",     "ACAd: Anterior cingulate, dorsal",       [0.00,  0.30,  0.20]),
    ("norm",           "TEa: Temporal association areas",        [0.66,  0.02, -0.05]),
    ("loss_aversion",  "BLA: Basolateral amygdalar nucleus",     [0.52, -0.28,  0.12]),
    ("habit",          "STRd: Striatum, dorsal region",          [0.34, -0.02,  0.16]),
    ("status",         "ACB: Nucleus accumbens",                 [0.22, -0.20,  0.34]),
    ("salience",       "AId: Agranular insular, dorsal",         [0.60,  0.10,  0.28]),
    ("effort_cost",    "ACAv: Anterior cingulate, ventral",      [0.00,  0.18,  0.30]),
    ("risk_appetite",  "ORBl: Orbital area, lateral",            [0.30,  0.30,  0.58]),
    ("delay_discount", "PL: Prelimbic area",                     [0.10,  0.34,  0.44]),
    ("social_proof",   "TEa: Temporal association, ventral",     [0.70, -0.10, -0.18]),
    ("identity",       "RSPd: Retrosplenial, dorsal",            [0.08, -0.10, -0.62]),
    ("threat",         "CEA: Central amygdalar nucleus",         [0.46, -0.34,  0.06]),
    ("reward_learn",   "VTA: Ventral tegmental area",            [0.14, -0.42, -0.16]),
    ("attention",      "SSp: Primary somatosensory",             [0.56,  0.34,  0.10]),
    ("memory_recall",  "CA1: Field CA1, hippocampus",            [0.48, -0.14, -0.32]),
    ("planning",       "MOs: Secondary motor area",              [0.24,  0.44,  0.44]),
    ("inhibition",     "ORBm: Orbital area, medial",             [0.06,  0.26,  0.56]),
    ("valuation",      "OFC: Orbitofrontal cortex",              [0.22,  0.34,  0.60]),
    ("arousal",        "LC: Locus coeruleus",                    [0.10, -0.46, -0.44]),
    ("satiety",        "ARH: Arcuate hypothalamic nucleus",      [0.06, -0.40,  0.08]),
    ("thermal_comfort","POA: Preoptic area",                     [0.12, -0.30,  0.26]),
    ("routine",        "STRv: Striatum, ventral region",         [0.28, -0.24,  0.24]),
    ("novelty",        "SNc: Substantia nigra, compact part",    [0.20, -0.38, -0.10]),
]


def load_plants():
    import csv
    rows = []
    with open(PLANTS, newline="", encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            try:
                mw = float(r["capacity_mw"])
                la = float(r["latitude"])
                lo = float(r["longitude"])
            except (TypeError, ValueError, KeyError):
                continue
            if mw < MIN_MW or not (-90 <= la <= 90) or not (-180 <= lo <= 180):
                continue
            rows.append({
                "name": (r.get("name") or "").strip() or "unnamed plant",
                "country": (r.get("country_long") or "").strip(),
                "iso": (r.get("country") or "").strip(),
                "fuel": (r.get("primary_fuel") or "").strip() or "Other",
                "mw": mw, "lat": la, "lon": lo,
                "year": (r.get("commissioning_year") or "").split(".")[0],
            })
    return rows


def resonance(mw, world_max):
    """How hard a plant rings when the system is shocked.

    Capacity spans five orders of magnitude, so a linear map would give every
    plant below a gigawatt the same invisible value. The cube root compresses
    it into a range the eye and the propagation engine can both use, and it is
    the same transform the rest of this project uses for the same reason.
    """
    return round(0.12 + 0.62 * (mw / world_max) ** (1.0 / 3.0), 4)


def load_cities():
    """Every settlement above fifteen thousand people, as a demand cohort.

    The demand layer held 1,142 cohorts against 21,000 plants, which made the
    atlas a map of supply with a footnote about who uses it. Demand is where
    the system is actually driven, and it is at least as spatially detailed as
    generation.
    """
    import csv, io, zipfile
    if not os.path.exists(CITIES):
        return []
    out = []
    with zipfile.ZipFile(CITIES) as z:
        txt = z.read("cities15000.txt").decode("utf-8", "replace")
    for r in csv.reader(io.StringIO(txt), delimiter="\t"):
        if len(r) < 15:
            continue
        try:
            la, lo, pop = float(r[4]), float(r[5]), int(r[14] or 0)
        except ValueError:
            continue
        if pop <= 0:
            continue
        out.append({"name": r[1], "iso": r[8], "lat": la, "lon": lo,
                    "pop": pop, "adm": r[10]})
    return out


def load_admin1():
    """First-level administrative regions, as grid districts."""
    if not os.path.exists(ADMIN1):
        return []
    out = []
    for line in open(ADMIN1, encoding="utf-8", errors="replace"):
        f = line.rstrip("\n").split("\t")
        if len(f) < 4:
            continue
        code = f[0]
        out.append({"code": code, "iso": code.split(".")[0], "name": f[1]})
    return out


def load_quakes():
    """Recorded earthquakes of magnitude 5.5 and above since 1960.

    The event layer held 526 disasters. Seismicity is the one hazard with a
    complete, uniform, global instrumental record, so it is the honest way to
    make the layer as detailed everywhere as the plant layer is.
    """
    import csv
    if not os.path.exists(QUAKES):
        return []
    out = []
    with open(QUAKES, newline="", encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            try:
                la, lo, mag = (float(r["latitude"]), float(r["longitude"]),
                               float(r["mag"]))
            except (TypeError, ValueError, KeyError):
                continue
            if not (-90 <= la <= 90 and -180 <= lo <= 180):
                continue
            out.append({"lat": la, "lon": lo, "mag": mag,
                        "place": (r.get("place") or "").strip(),
                        "when": (r.get("time") or "")[:10]})
    return out


def load_ports():
    """Every port in the World Port Index, as a market node.

    Markets held six price benchmarks against thirty-five thousand plants.
    A port is where fuel physically changes hands, which is the part of a
    market that has a coordinate, and the index carries harbour size and
    the cargo types each one handles.
    """
    if not os.path.exists(PORTS):
        return []
    w = json.load(open(PORTS, encoding="utf-8"))
    rows = w.get("ports", w if isinstance(w, list) else [])
    import re as _re

    def dms(v):
        """The index publishes coordinates as 30 deg 20' 00" N, not as a
        number. Parsed rather than guessed at."""
        if v is None:
            return None
        s = str(v).strip()
        try:
            return float(s)
        except ValueError:
            pass
        m = _re.match(r"(\d+)\D+(\d+)\D+(\d+)?\D*([NSEW])", s)
        if not m:
            return None
        deg = float(m.group(1)) + float(m.group(2)) / 60.0 + \
            float(m.group(3) or 0) / 3600.0
        return -deg if m.group(4) in ("S", "W") else deg

    out = []
    for r in rows:
        la, lo = dms(r.get("latitude")), dms(r.get("longitude"))
        if la is None or lo is None:
            continue
        if not (-90 <= la <= 90 and -180 <= lo <= 180):
            continue
        size = (r.get("harborSize") or "").strip()
        out.append({
            "name": (r.get("portName") or "port").strip(),
            "country": (r.get("countryName") or "").strip(),
            "iso": (r.get("countryCode") or "").strip()[:2],
            "size": size, "lat": la, "lon": lo,
            "oil": bool(r.get("cargoPierDepth") or r.get("oilTerminalDepth")),
        })
    return out


# Harbour size is the only capacity figure the index carries, so it is what
# sets how hard a port rings. These are the index's own categories.
# The index records harbour size as a single letter. These are its own
# categories, not a scale invented here.
PORT_W = {"L": 0.62, "M": 0.42, "S": 0.26, "V": 0.16,
          "Large": 0.62, "Medium": 0.42, "Small": 0.26, "Very Small": 0.16}
PORT_SIZE = {"L": "large harbour", "M": "medium harbour",
             "S": "small harbour", "V": "very small harbour"}


def load_allen():
    """Named structures of the Allen Mouse Brain Common Coordinate Framework,
    with the centre of mass the atlas publishes for each one.

    These are drawn as structure and nothing else. They carry no behavioural
    channel, no edge and no weight, because there is no measurement behind an
    assignment of behaviour to most of them. What they buy is a brain that
    looks like a brain instead of two dozen dots in a void, and the twenty-four
    channels that do carry weight sit inside it.

    The CCF is 13,200 by 8,000 by 11,400 micrometres, anterior-posterior by
    dorsal-ventral by left-right. It is rescaled here onto the unit-ish box the
    existing brain mesh occupies; no coordinate is invented, only divided.
    """
    if not (os.path.exists(ALLEN_TREE) and os.path.exists(ALLEN_XYZ)):
        return []
    tree = json.load(open(ALLEN_TREE, encoding="utf-8"))
    names = {}

    def walk(n):
        names[n["id"]] = (n.get("acronym") or "", n.get("name") or "",
                          n.get("st_level"))
        for c in n.get("children", []):
            walk(c)
    for root in tree["msg"]:
        walk(root)

    cen = json.load(open(ALLEN_XYZ, encoding="utf-8"))
    AP, DV, LR = 13200.0, 8000.0, 11400.0
    out, seen = [], set()
    for c in cen.get("msg", []):
        sid = c.get("structure_id")
        if sid in seen or sid not in names:
            continue
        seen.add(sid)
        acr, nm, lvl = names[sid]
        # CCF axes to the scene's axes: x is left-right, y is up, z is
        # front-back, and the origin moves to the middle of the volume
        x = (c["z"] / LR - 0.5) * 1.30
        y = (0.5 - c["y"] / DV) * 0.95
        z = (c["x"] / AP - 0.5) * 1.45
        out.append({"acr": acr, "name": nm, "lvl": lvl,
                    "xyz": [round(x, 4), round(y, 4), round(z, 4)]})
    return out


def main():
    d = json.load(open(SCENE, encoding="utf-8"))
    old = d["nodes"]
    old_edges = d["edges"]

    # keep every layer except the American plant set and the six-channel brain
    keep, remap = [], {}
    for n in old:
        if n["kind"] in ("station", "psych"):
            continue
        remap[n["i"]] = len(keep)
        keep.append(n)
    print(f"  carried over {len(keep):,} nodes from the model of record")

    # grids, so a plant can be wired to the system it feeds
    grid_by_iso = {}
    for i, n in enumerate(keep):
        if n["kind"] == "grid":
            iso = (n.get("id") or "").replace("GRID_", "")[:3]
            grid_by_iso.setdefault(iso, i)

    plants = load_plants()
    world_max = max(p["mw"] for p in plants)
    print(f"  {len(plants):,} plants at or above {MIN_MW:.0f} MW across "
          f"{len({p['country'] for p in plants})} countries")

    nodes = list(keep)
    edges = [{"s": remap[e["s"]], "t": remap[e["t"]], "w": e["w"]}
             for e in old_edges
             if e["s"] in remap and e["t"] in remap]
    print(f"  {len(edges):,} edges survive the removal")

    unwired = 0
    for p in plants:
        idx = len(nodes)
        nodes.append({
            "i": idx, "id": f"PP_{idx}",
            "name": f"{p['name']} ({p['fuel']}, {p['mw']:.0f} MW)",
            "kind": "station", "tab": 4,
            "res": resonance(p["mw"], world_max),
            "src": f"WRI Global Power Plant Database v1.3 · {p['country']}"
                   + (f" · commissioned {p['year']}" if p["year"] else ""),
            "lat": round(p["lat"], 4), "lon": round(p["lon"], 4),
            "mw": p["mw"],
        })
        g = grid_by_iso.get(p["iso"])
        if g is None:
            unwired += 1
            continue
        # a plant's grip on its grid scales with its share of a large plant
        edges.append({"s": idx, "t": g,
                      "w": round(0.20 + 0.55 * (p["mw"] / world_max) ** 0.5, 4)})
    print(f"  {unwired:,} plants had no matching grid node and stand alone")

    # the behaviour layer, wired into demand the way the six-channel one was
    demand = [i for i, n in enumerate(nodes) if n["kind"] == "consumer"]
    brain = []
    for k, (key, region, xyz) in enumerate(BRAIN):
        idx = len(nodes)
        nodes.append({
            "i": idx, "id": "PSYCH_" + key, "name": f"{key} ({region})",
            "kind": "psych", "tab": 6, "res": round(0.30 + 0.02 * k, 4),
            "src": "Allen Brain Atlas region; channel assignment is a model "
                   "of where demand is decided, not a measurement",
            "lat": 0.0, "lon": 0.0,
        })
        brain.append({"id": "PSYCH_" + key, "key": key, "region": region,
                      "xyz": xyz, "i": idx})
        # each channel touches a slice of the demand cohorts
        for j in range(k, len(demand), max(1, len(BRAIN))):
            edges.append({"s": idx, "t": demand[j], "w": 0.28})
    print(f"  behaviour layer: {len(brain)} channels on named regions")

    # ---- demand: one cohort per city ---------------------------------
    cities = load_cities()
    I2I3 = iso2_to_iso3()
    grid_by_iso2 = {}
    for i, n in enumerate(nodes):
        if n["kind"] == "grid":
            iso3 = (n.get("id") or "").replace("GRID_", "")[:3]
            for a2, a3 in I2I3.items():
                if a3 == iso3:
                    grid_by_iso2.setdefault(a2, i)
    print(f"  {len(grid_by_iso2)} countries mapped from two-letter to "
          f"three-letter codes")
    popmax = max((c["pop"] for c in cities), default=1)
    for c in cities:
        idx = len(nodes)
        nodes.append({
            "i": idx, "id": "", "name": f"{c['name']} ({c['pop']:,} people)",
            "kind": "consumer", "tab": 5,
            "res": round(0.18 + 0.55 * (c["pop"] / popmax) ** (1 / 3), 4),
            "src": f"GeoNames cities15000 · {c['iso']}",
            "lat": round(c["lat"], 3), "lon": round(c["lon"], 3),
        })
        g = grid_by_iso2.get(c["iso"])
        if g is not None:
            edges.append({"s": g, "t": idx,
                          "w": round(0.18 + 0.5 * (c["pop"] / popmax) ** 0.5, 4)})
    print(f"  demand: {len(cities):,} city cohorts added")

    # ---- districts: first-level administrative regions ----------------
    # GeoNames publishes admin-1 codes without coordinates, so every district
    # landed on null island. The centroid of the settlements inside each one
    # is a real position and is already in hand.
    adm = load_admin1()
    cen = {}
    for c in cities:
        key = c["iso"] + "." + (c.get("adm") or "")
        s = cen.setdefault(key, [0.0, 0.0, 0])
        s[0] += c["lat"]; s[1] += c["lon"]; s[2] += 1
    placed_adm = 0
    for a in adm:
        idx = len(nodes)
        s = cen.get(a["code"])
        if s and s[2]:
            la, lo = s[0] / s[2], s[1] / s[2]
            placed_adm += 1
        else:
            la = lo = None            # no settlement in the set to locate it
        if la is None:
            continue                  # rather than stack it on null island
        nodes.append({
            "i": idx, "id": "", "name": f"{a['name']} ({a['iso']})",
            "kind": "district", "tab": 3, "res": 0.34,
            "src": f"GeoNames admin-1 division, centroid of {s[2]} settlements",
            "lat": round(la, 3), "lon": round(lo, 3),
        })
        g = grid_by_iso2.get(a["iso"])
        if g is not None:
            edges.append({"s": g, "t": idx, "w": 0.42})
    print(f"  grids: {placed_adm:,} districts placed at their settlement "
          f"centroid, {len(adm) - placed_adm:,} dropped for having none")

    # ---- events: instrumental seismic record --------------------------
    quakes = load_quakes()

    # An earthquake that is wired to nothing is a dot, not a node. The first
    # version added thirty thousand of them and connected none, which is
    # exactly why clicking one did nothing: it was not in the model at all.
    # Each one now reaches the infrastructure near it, found through a
    # one-degree spatial bucket so this stays linear rather than quadratic.
    # Reach grows with magnitude, because that is what magnitude means. 
    buckets = {}
    for i, n in enumerate(nodes):
        if n["kind"] in ("station", "consumer", "grid", "district", "market"):
            key = (int(n["lat"] // 2), int(n["lon"] // 2))
            buckets.setdefault(key, []).append(i)

    # A quake in open ocean with nothing inside its felt radius is a real
    # record that genuinely affects nothing. Keeping it makes the layer look
    # full and leaves seventy per cent of it inert, so the node is only
    # created once something has been found for it to reach.
    wired = 0
    for q in quakes:
        idx = len(nodes)
        pending = []
        # felt radius: about 60 km at magnitude 5.5, doubling every magnitude
        reach = 60.0 * (2.0 ** (q["mag"] - 5.5))
        rdeg = min(6.0, reach / 111.0)
        near, kb = [], (int(q["lat"] // 2), int(q["lon"] // 2))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                near += buckets.get((kb[0] + dy, kb[1] + dx), [])
        hits = 0
        for j in near:
            dlat = nodes[j]["lat"] - q["lat"]
            dlon = (nodes[j]["lon"] - q["lon"]) * math.cos(
                math.radians(q["lat"]))
            dist = math.hypot(dlat, dlon)
            if dist > rdeg:
                continue
            w = round(0.55 * (1.0 - dist / rdeg) *
                      min(1.0, (q["mag"] - 5.0) / 3.5), 4)
            if w < 0.02:
                continue
            pending.append({"s": idx, "t": j, "w": w})
            hits += 1
            if hits >= 12:          # a quake shakes its neighbourhood, not a continent
                break
        if not hits:
            continue                      # nothing to shake, so no node
        edges.extend(pending)
        wired += 1
        nodes.append({
            "i": idx, "id": "",
            "name": f"M{q['mag']:.1f} {q['place'] or 'earthquake'}",
            "kind": "event", "tab": 1,
            "res": round(min(0.92, 0.10 + 0.10 * (q["mag"] - 5.0)), 4),
            "src": f"USGS earthquake catalogue · {q['when']} · "
                   f"reaches {hits} nodes",
            "lat": round(q["lat"], 3), "lon": round(q["lon"], 3),
        })
    print(f"  events: {len(quakes):,} earthquakes, {wired:,} of them reaching "
          f"infrastructure within their felt radius")

    MLO = (19.536, -155.576)      # Mauna Loa Observatory
    for n in nodes:
        if n["kind"] == "climate" and not n.get("lat") and not n.get("lon"):
            n["lat"], n["lon"] = MLO
            n["src"] = (n.get("src", "") +
                        " · a global quantity, shown at Mauna Loa "
                        "Observatory, where the record is kept").strip(" ·")
    print("  climate: 2 global series pinned to Mauna Loa")

    # ---- markets: ports, where fuel physically changes hands ----------
    ports = load_ports()
    for pt in ports:
        idx = len(nodes)
        nodes.append({
            "i": idx, "id": "",
            "name": f"{pt['name']}" + (f" ({pt['country']})" if pt["country"] else ""),
            "kind": "market", "tab": 2,
            "res": PORT_W.get(pt["size"], 0.22),
            "src": "NGA World Port Index · "
                   + PORT_SIZE.get(pt["size"], "size not recorded"),
            "lat": round(pt["lat"], 3), "lon": round(pt["lon"], 3),
        })
        g = grid_by_iso2.get(pt["iso"])
        if g is not None:
            edges.append({"s": idx, "t": g, "w": PORT_W.get(pt["size"], 0.22)})
    print(f"  markets: {len(ports):,} ports added")

    # ---- brain: the anatomy, as structure only ------------------------
    allen = load_allen()
    struct = []
    for a in allen:
        struct.append({"n": f"{a['acr']} · {a['name']}", "xyz": a["xyz"]})
    print(f"  brain: {len(struct):,} Allen CCF structures drawn as anatomy")

    # ------------------------------------------------------------- emit ----
    lat, lon, kind, tab, res, name, src, ident, mw = ([] for _ in range(9))
    for n in nodes:
        lat.append(round(n.get("lat") or 0.0, 3))
        lon.append(round(n.get("lon") or 0.0, 3))
        kind.append(KINDS.index(n["kind"]))
        tab.append(int(n["tab"]))
        res.append(round(float(n["res"]), 3))
        name.append(n["name"])
        src.append(n.get("src", ""))
        ident.append(n["id"])
        mw.append(round(n.get("mw", 0.0), 1))

    # The provenance string is identical for every plant in a country and a
    # commissioning year, so it is stored once and referenced by index. Twenty
    # thousand copies of the same seventy characters is two thirds of the file.
    srcDict, seen, srcIdx = [], {}, []
    for s in src:
        if s not in seen:
            seen[s] = len(srcDict)
            srcDict.append(s)
        srcIdx.append(seen[s])
    print(f"  provenance strings: {len(srcDict):,} distinct of {len(src):,}")

    # Node ids are only used to look a node up; a plant's id carries no
    # information the index does not already carry, so they are dropped for
    # plants and kept where something references them.
    referenced = {b["id"] for b in brain}
    ident = [x if (not x.startswith("PP_") or x in referenced) else ""
             for x in ident]

    cnt_event = sum(1 for n in nodes if n["kind"] == "event")
    cnt_grid = sum(1 for n in nodes if n["kind"] in ("grid", "district"))
    idMap = {x: i for i, x in enumerate(ident) if x}
    tabs = json.loads(json.dumps(d["tabs"]))
    for t in tabs:
        if t["id"] == "markets":
            # the legend beside this already counts the layer's nodes; a
            # number here that counted only the ports (2,896 beside 3,627)
            # read as a disagreement (2026-09-05)
            t["sub"] = "ports, price benchmarks and fuel supplies"
        if t["id"] == "events":
            t["sub"] = f"{cnt_event:,} recorded events"
        if t["id"] == "demand":
            t["sub"] = "settlements and consumer groups"   # same reason as markets
        if t["id"] == "grids":
            t["sub"] = f"{cnt_grid:,} systems and districts"
        if t["id"] == "plants":
            t["sub"] = f"{len(plants):,} units, {len({p['country'] for p in plants})} countries"
        if t["id"] == "mind":
            t["sub"] = f"{len(brain)} behavioural channels"

    
    payload = {
        "kinds": KINDS, "tabs": tabs, "scenarios": d["scenarios"],
        "n": len(nodes),
        "lat": lat, "lon": lon, "kind": kind, "tab": tab, "res": res,
        "name": name, "srcDict": srcDict, "src": srcIdx,
        # ids only exist where something references them, and capacity only
        # exists for plants; both are stored as sparse maps rather than as
        # hundred-thousand-long arrays of blanks and zeroes
        "idMap": {k: v for k, v in idMap.items()},
        "mwMap": {str(i): m for i, m in enumerate(mw) if m > 0},
        "es": [e["s"] for e in edges], "et": [e["t"] for e in edges],
        "ew": [round(float(e["w"]), 4) for e in edges],
        "coast": coastlines(),
        "brain": brain,
        # Anatomy, drawn and hoverable but carrying no weight and no edge.
        # It is scenery with a real coordinate, and it is kept out of the node
        # arrays so that nothing can mistake it for part of the model.
        "anatomy": struct,
        "co2": d.get("co2", []), "temp": d.get("temp", []),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("window.ATLAS=")
        json.dump(payload, fh, separators=(",", ":"), ensure_ascii=False)
        fh.write(";\n")

    by_tab = {}
    for t in tab:
        by_tab[t] = by_tab.get(t, 0) + 1
    print(f"\n  {'tab':22s}{'nodes':>8s}")
    for i, t in enumerate(tabs):
        print(f"  {t['name']:22s}{by_tab.get(i, 0):8,d}")
    print(f"\n  {len(nodes):,} nodes · {len(edges):,} edges")
    print(f"  written: {OUT} ({os.path.getsize(OUT)/1024:.0f} kB)")


if __name__ == "__main__":
    main()
