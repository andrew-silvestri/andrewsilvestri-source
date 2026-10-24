"""
Checks on data/skylines.json against the archived raw pulls it came from.

Each check exists because the payload shipped until 2026-10-24 failed it
(QA, D-31), and each --break puts back the specific thing that went wrong,
not a generic fault (HANDOFF trap 38). Every check is recomputed here from
data/raw/, by code written apart from build_skylines.py, so a filter that
stops working in the builder cannot also stop working in the test (trap 20).

  standing   every tower on every wheel is standing: Wikidata gives it no
             demolition date and no demolished / proposed / unfinished /
             under-construction class or state, and OpenStreetMap maps a
             standing building for it.
             --break standing  puts the destroyed North Tower of the World
                               Trade Center (Q11235, 417 m) back on New York
  building   no mast, TV tower or observation tower on a wheel, and every
             tower inside its city's own Wikidata item.
             --break mast      puts the Raszyn radio transmitter (Q489426,
                               335 m, 18 km outside Warsaw) back as Warsaw's
                               tallest
  once       no building drawn twice.
             --break dup       draws Warsaw's Varso a second time, as the
                               old payload drew "Varso" and "Varso Tower"
  loudness   the meter carries height, so each city's tallest tower is its
             loudest bar and no bar is louder than its own tower.
             --break angle     feeds the meter elevation angle again, the
                               mapping that made the tallest tower quieter
                               than a nearer, shorter one in 17 of 27 cities
  rebuild    build_skylines.py, run on the archived pulls, reproduces the
             payload exactly, and the payload names the pulls it came from.
             --break rebuild   changes one stored height by a metre

Run:  python test_skylines.py           all checks, exit 1 on any failure
      python test_skylines.py --break standing|mast|dup|angle|rebuild
"""

import argparse
import copy
import gzip
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
PAYLOAD = os.path.join(HERE, "data", "skylines.json")

# Held a second time, apart from build_skylines.py, on purpose (trap 16).
GONE_CLASSES = {"Q19860854", "Q56556915", "Q57644089", "Q96084375", "Q811683",
                "Q124835105", "Q64728694", "Q25447168", "Q12372814",
                "Q21514702", "Q1570262", "Q12377751", "Q1441983"}
GONE_STATES = {"Q12377751", "Q56556915", "Q811683", "Q97317113", "Q30108381"}
MAST_CLASSES = {"Q12518", "Q11166728", "Q1440300", "Q1068623", "Q1798641",
                "Q1440476", "Q797765", "Q853854", "Q81917", "Q274153",
                "Q5191724", "Q815448", "Q200334", "Q685204", "Q72926449",
                "Q213643", "Q39715", "Q1601458", "Q13416228"}
GROUP_CLASSES = {"Q1497364", "Q118896406", "Q27556845", "Q4298922"}
HIGH_CLASSES = {"Q11303", "Q18142", "Q2304397", "Q104829543", "Q1021645",
                "Q13402009", "Q27686", "Q15622489", "Q134570257", "Q47012103",
                "Q11755959"}

fails = 0


def say(ok, label, detail=""):
    global fails
    print(("  ok    " if ok else "  FAIL  ") + label +
          ("   " + detail if detail else ""))
    if not ok:
        fails += 1


def dist_m(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c)
    h = (math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) *
         math.sin(math.radians(d - b) / 2) ** 2)
    return 2 * 6371000.0 * math.asin(min(1.0, math.sqrt(h)))


def q(u):
    return u.rsplit("/", 1)[-1]


def raw_facts(wd):
    """qid -> what Wikidata says about it, per city."""
    out = {}
    for city, c in wd["cities"].items():
        for f in c["facts"]:
            r = out.setdefault((city, q(f["b"]["value"])),
                               {"cls": set(), "state": set(), "dem": False,
                                "in": False, "coord": None})
            if "cls" in f:
                r["cls"].add(q(f["cls"]["value"]))
            if "state" in f:
                r["state"].add(q(f["state"]["value"]))
            r["dem"] |= "dem" in f
            r["in"] |= f["inCity"]["value"] == "true"
        for h in c["heights"]:
            k = (city, q(h["b"]["value"]))
            m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)",
                         h["coord"]["value"])
            if k in out and m and out[k]["coord"] is None:
                out[k]["coord"] = (float(m.group(2)), float(m.group(1)))
    return out


def _dead(t):
    return (t.get("building") in ("construction", "proposed", "demolished")
            or t.get("building:part") in ("construction", "proposed")
            or "construction" in t or "proposed" in t or "demolished" in t)


def _num(v):
    m = re.match(r"\s*([\d.]+)", v or "")
    if not m:
        return None
    try:
        x = float(m.group(1))
    except ValueError:
        return None
    return x * 0.3048 if ("ft" in v or "'" in v) else x


def _key(s):
    s = re.sub(r"\b(the|tower|towers|building|torre|tour|turm|wieza)\b", " ",
               (s or "").lower())
    return re.sub(r"[^\w]+", "", s)


def core(wd, city, qid_, coord):
    """Outside by P131+, but located only in places the city is itself in
    (its county or state), and within 3 km of the city's coordinate."""
    from fetch_wikidata import CITIES
    anc = [r["ancestor"]["value"] == "true"
           for r in wd.get("located", {}).get("cities", {}).get(city, {})
           .get("rows", []) if q(r["b"]["value"]) == qid_]
    _, lat, lon = CITIES[city]
    return bool(anc) and all(anc) and dist_m(lat, lon, *coord) <= 3000


def linked_to(osm, city, qid_):
    return any(qid_ in re.split(r"[;,\s]+", e.get("tags", {})
                                .get("wikidata", ""))
               for e in osm["cities"][city]["linked"])


def osm_standing(osm, city, qid_, name, coord, h):
    """Does OSM map a standing building for this item? Its own wikidata link
    first; a link only to a building under construction is a no. Otherwise a
    standing building within 120 m agreeing on height (20%), storeys (3.5 m
    each, 30%) or name."""
    c = osm["cities"][city]
    links = [e.get("tags", {}) for e in c["linked"]
             if qid_ in re.split(r"[;,\s]+", e.get("tags", {})
                                 .get("wikidata", ""))]
    if links:
        return any(not _dead(t) for t in links)
    me = _key(name)
    for e in c["near"]:
        t, ce = e.get("tags", {}), e.get("center")
        if not ce or _dead(t) or (t.get("wikidata") and qid_ not in
                                  t.get("wikidata")):
            continue
        if dist_m(coord[0], coord[1], ce["lat"], ce["lon"]) > 120:
            continue
        oh, lv = _num(t.get("height")), _num(t.get("building:levels"))
        if ((oh and abs(oh - h) <= 0.2 * h) or
                (lv and abs(3.5 * lv - h) <= 0.3 * h) or
                (len(me) >= 4 and any(_key(t.get(k)) == me for k in
                                      ("name", "name:en", "alt_name",
                                       "official_name") if t.get(k)))):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--break", dest="brk",
                    choices=["standing", "mast", "dup", "angle", "rebuild"])
    a = ap.parse_args()
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    src = P.get("sources", {})
    wpath = os.path.join(RAW, src.get("wikidata", "?"))
    opath = os.path.join(RAW, src.get("osm", "?"))
    say(os.path.exists(wpath) and os.path.exists(opath),
        "the payload names archived pulls that exist",
        f"{src.get('wikidata')} + {src.get('osm')}")
    wd = json.load(open(wpath, encoding="utf-8"))
    with gzip.open(opath, "rb") as fh:
        osm = json.loads(fh.read().decode("utf-8"))
    F = raw_facts(wd)
    isb = {q(r["cls"]["value"]): r["isBuilding"]["value"] == "true"
           for r in wd["classes"]}
    C = {c["city"]: c for c in P["cities"]}
    orig = copy.deepcopy(P)

    if a.brk == "standing":
        ny = C["New York"]
        ny["ring"].append([0.0, 0.0, 1.0, 417.0, "World Trade Center", 1973,
                           200.0, "Q11235"])
    if a.brk == "mast":
        w = C["Warsaw"]
        w["ring"].append([0.0, 0.0, 18.3, 335.0, "Raszyn radio transmitter",
                          1949, 225.0, "Q489426"])
    if a.brk == "dup":
        w = C["Warsaw"]
        v = next(r for r in w["ring"] if "Varso" in r[4])
        w["ring"].append(list(v[:4]) + ["Varso"] + list(v[5:7]) +
                         ["Q28320872"])
    if a.brk == "angle":
        for c in P["cities"]:
            n = len(c["ring"])
            half = max(1.2, 0.5 * 360.0 / n)
            pr = [0.0] * 360
            for r in c["ring"]:
                for i in range(math.floor(r[0] - half),
                               math.ceil(r[0] + half) + 1):
                    pr[i % 360] = max(pr[i % 360], r[1])
            c["rprof"] = pr

    # standing, building, in city
    bad_stand, bad_mast, bad_out, n = [], [], [], 0
    for c in P["cities"]:
        for r in c["ring"]:
            n += 1
            f = F.get((c["city"], r[7]))
            if f is None:
                bad_stand.append(f"{c['city']}: {r[4]} not in the raw pull")
                continue
            if (f["dem"] or f["cls"] & GONE_CLASSES or f["state"] & GONE_STATES
                    or not osm_standing(osm, c["city"], r[7], r[4],
                                     f["coord"], r[3])):
                bad_stand.append(f"{c['city']}: {r[4]} ({r[7]})")
            if ((not any(isb.get(x) for x in f["cls"]) and
                 not f["cls"] & GROUP_CLASSES) or
                    (f["cls"] & MAST_CLASSES and not f["cls"] & HIGH_CLASSES)):
                bad_mast.append(f"{c['city']}: {r[4]} ({r[7]})")
            if not f["in"] and not core(wd, c["city"], r[7], f["coord"]):
                bad_out.append(f"{c['city']}: {r[4]} ({r[7]})")
    say(not bad_stand, f"standing: all {n} wheel towers stand "
        "(Wikidata and OSM)", "; ".join(bad_stand[:5]))
    say(not bad_mast, "building: no mast, TV or observation tower",
        "; ".join(bad_mast[:5]))
    say(not bad_out, "in city: every tower inside its city's own item",
        "; ".join(bad_out[:5]))

    # once
    dups = []
    for c in P["cities"]:
        rs = c["ring"]
        ids = [r[7] for r in rs]
        if len(set(ids)) != len(ids):
            dups.append(f"{c['city']}: a QID twice")
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                fi, fj = F.get((c["city"], rs[i][7])), F.get((c["city"],
                                                              rs[j][7]))
                if not fi or not fj or not fi["coord"] or not fj["coord"]:
                    continue
                d = dist_m(*fi["coord"], *fj["coord"])
                # two items OSM links to two different buildings are two
                # buildings (10 and 15 Hudson Yards share one coordinate)
                both = (linked_to(osm, c["city"], rs[i][7]) and
                        linked_to(osm, c["city"], rs[j][7]))
                if ((d < 30 and abs(rs[i][3] - rs[j][3]) <= 0.05 * rs[i][3]
                     and not both) or
                        (_key(rs[i][4]) and _key(rs[i][4]) == _key(rs[j][4])
                         and d < 300)):
                    dups.append(f"{c['city']}: {rs[i][4]} / {rs[j][4]}")
    say(not dups, "once: no building drawn twice", "; ".join(dups[:5]))

    # loudness follows height
    quiet = []
    for c in P["cities"]:
        n_ = len(c["ring"])
        top = max(c["ring"], key=lambda r: r[3])
        k = int(round(top[0])) % 360
        if abs(max(c["rprof"]) - top[3]) > 0.06 or abs(c["rprof"][k] -
                                                       top[3]) > 0.06:
            quiet.append(c["city"])
            continue
        for r in c["ring"]:
            if c["rprof"][int(round(r[0])) % 360] + 0.06 < r[3]:
                quiet.append(c["city"])
                break
    say(not quiet, "loudness: each city's tallest tower is its loudest bar",
        f"{len(quiet)} cities fail: " + ", ".join(quiet[:6]) if quiet else "")

    # rebuild
    if a.brk == "rebuild":
        P = copy.deepcopy(orig)
        P["cities"][0]["ring"][0][3] += 1.0
    elif a.brk:
        P = orig
    sys.path.insert(0, HERE)
    import build_skylines as B
    out, gone, _ = _quiet(B)
    same = (json.dumps(out, sort_keys=True) ==
            json.dumps(P["cities"], sort_keys=True))
    say(same, "rebuild: the archived pulls reproduce the payload exactly")
    say([g[0] for g in gone] == [d["city"] for d in P["dropped"]],
        "rebuild: the dropped cities match", ", ".join(g[0] for g in gone))

    print(f"\n  {'all checks passed' if not fails else str(fails) + ' failed'}")
    sys.exit(1 if fails else 0)


def _quiet(B):
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return B.build(apply=False)


if __name__ == "__main__":
    main()
