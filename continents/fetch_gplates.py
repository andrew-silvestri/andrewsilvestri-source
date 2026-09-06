"""Fetch reconstructed positions from the GPlates Web Service, once, to a cache.

Source
------
gws.gplates.org, EarthByte / University of Sydney, serving the same rotation
models EarthByte publishes on Zenodo. Each model is cited on the page; the
service itself is infrastructure, not a source.

WHY THIS IS CACHED AND PINNED
-----------------------------
The service's default model is documented as liable to change, and named
models' rotation files have been updated in place as recently as September
2025. A page whose numbers move when someone else redeploys a server is not
reproducible, so every model is named explicitly in every request, the whole
response set is committed, and the build never touches the network.

THE ONE KNOWN ANSWER THIS REGIME HAS
------------------------------------
Deep-time reconstructions contain nothing checkable about the deep past.
Seton et al. 2023 names uncertainty quantification as the field's own open
problem, and this page says so rather than inventing a check.

But there is one: at age 0 every model must hand back the point it was
given. That sounds trivial and is not. Points go out as "lon,lat" and come
back as [lon, lat], and nothing else in this project verifies that ordering.
If the service ever swaps it, Denver lands in the Indian Ocean, every
pairwise distance stays perfectly plausible, and the page publishes a
fabricated disagreement in the one regime that has no external anchor. Gate
C2 is eight requests and closes it.

Writes
------
data/gplates_cache.json    every response, the model list, the fetch date

Run:  python3 fetch_gplates.py [--resume]
"""
import argparse
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "gplates_cache.json")

BASE = "https://gws.gplates.org"
SENTINEL = 999.99          # what GWS returns where a model places no crust
R_KM = 6371.0088

# Model, and the oldest age it covers, from the service's documentation.
# Pinned: a model appearing or vanishing must be a deliberate change.
MODELS = (
    ("SETON2012", 200),
    ("MULLER2019", 250),
    ("ZAHIROVIC2022", 410),
    ("MATTHEWS2016_pmag_ref", 410),
    ("TORSVIKCOCKS2017", 540),
    ("MULLER2022", 1000),
    ("MERDITH2021", 1000),
    ("PALEOMAP", 1100),
)

AGES = tuple(range(0, 501, 10))

# Twelve places. The first six are the research set. Reykjavik and Honolulu
# are here to teach: Iceland is about 16 Myr old and the Big Island under 1,
# so if the models behave, every one of them should decline to place crust
# there beyond about 20 Ma. That is genuine AGREEMENT that the ground did not
# exist, and it is what makes Sydney's disagreement at 400 to 500 Ma legible
# as a disagreement rather than as a bug. Whether it actually happens is
# checked, not assumed - see report_no_crust().
PLACES = (
    ("Sydney",       151.21, -33.87),
    ("Nagpur",        79.09,  21.15),
    ("Denver",      -104.99,  39.74),
    ("Warsaw",        21.01,  52.23),
    ("Kinshasa",      15.27,  -4.44),
    ("Brasilia",     -47.88, -15.79),
    ("Reykjavik",    -21.94,  64.15),
    ("Honolulu",    -157.86,  21.31),
    ("Cairo",         31.24,  30.04),
    ("Beijing",      116.41,  39.90),
    ("Cape Town",     18.42, -33.93),
    ("Vancouver",   -123.12,  49.28),
)


def get(url, timeout=90):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def reconstruct(model, age):
    pts = ",".join(f"{lo},{la}" for _n, lo, la in PLACES)
    url = (BASE + "/reconstruct/reconstruct_points/?"
           + urllib.parse.urlencode({"points": pts, "time": age,
                                     "model": model}))
    return get(url)["coordinates"]


def is_sentinel(p):
    return (p is None or abs(p[0]) > 360.0 or abs(p[1]) > 90.0
            or abs(abs(p[0]) - SENTINEL) < 0.02)


def gc_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * R_KM * math.asin(min(1.0, math.sqrt(h)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true",
                    help="keep responses already cached")
    args = ap.parse_args()

    have = {}
    if args.resume and os.path.exists(CACHE):
        have = json.load(open(CACHE, encoding="utf-8")).get("responses", {})
        print(f"  resuming with {len(have)} responses already cached")

    listed = get(BASE + "/model/list/")
    want = {m.lower() for m, _ in MODELS}
    missing = sorted(want - {x.lower() for x in listed})
    if missing:
        sys.exit(
            f"fetch_gplates: gate C1 failed. The service no longer lists "
            f"{missing}. The model set is pinned deliberately; a model that "
            "appears or vanishes changes what the page compares. Re-pin and "
            "rerun every gate rather than widening this.")
    print(f"  C1  ok    {len(listed)} models listed, all {len(MODELS)} pinned "
          "ones present")

    todo = [(m, a) for m, oldest in MODELS for a in AGES
            if a <= oldest and f"{m}@{a}" not in have]
    print(f"  {len(todo)} requests to make, one per second")
    for k, (m, a) in enumerate(todo, 1):
        key = f"{m}@{a}"
        try:
            have[key] = reconstruct(m, a)
        except Exception as exc:                              # noqa: BLE001
            have[key] = {"error": str(exc)}
            print(f"    {key}: {exc}")
        if k % 40 == 0:
            print(f"    {k}/{len(todo)}")
        time.sleep(1.0)

    errors = sorted(k for k, v in have.items() if isinstance(v, dict))
    if errors:
        json.dump({"responses": have}, open(CACHE, "w", encoding="utf-8"))
        sys.exit(f"fetch_gplates: {len(errors)} requests failed, e.g. "
                 f"{errors[:3]}. Rerun with --resume; nothing else was written.")

    # C2: the identity at age 0, which is the only known answer here.
    worst, worst_where = 0.0, None
    for m, _oldest in MODELS:
        got = have[f"{m}@0"]
        for (name, lo, la), p in zip(PLACES, got):
            if is_sentinel(p):
                worst, worst_where = float("inf"), f"{m} {name} sentinel at age 0"
                continue
            d = gc_km((lo, la), p)
            if d > worst:
                worst, worst_where = d, f"{m} {name}"
    if not (worst <= 1.0):
        sys.exit(
            f"fetch_gplates: gate C2 failed. At age 0 a model did not return "
            f"the point it was given: worst {worst:.1f} km at {worst_where}. "
            "The most likely cause is that the service changed its coordinate "
            "order, in which case every distance this page computes is "
            "fabricated. Nothing was written.")
    print(f"  C2  ok    identity at age 0, worst of "
          f"{len(MODELS) * len(PLACES)}: {worst:.3f} km ({worst_where})")

    payload = {
        "service": BASE,
        "fetched": datetime.now(timezone.utc).date().isoformat(),
        "model_list": listed,
        "models": [{"name": m, "oldest_ma": o} for m, o in MODELS],
        "ages": list(AGES),
        "places": [{"name": n, "lon": lo, "lat": la} for n, lo, la in PLACES],
        "sentinel": SENTINEL,
        "identity_worst_km": round(worst, 6),
        "responses": have,
    }
    json.dump(payload, open(CACHE, "w", encoding="utf-8"), sort_keys=True)
    print(f"  wrote {os.path.relpath(CACHE, HERE)}  "
          f"{os.path.getsize(CACHE):,} bytes  {len(have)} responses")


if __name__ == "__main__":
    main()
