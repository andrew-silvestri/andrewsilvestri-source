"""Write site/continents-app.html from app_template.html and the payload.

The reconstructions are precomputed and inlined. The app never queries the
GPlates Web Service: the service's default model is documented as liable to
change and named models' rotation files are updated in place, so a page whose
numbers move when someone else redeploys a server is not reproducible.

The reconstructed coastlines go to site/assets/continents-land.js rather
than inline. They are a couple of megabytes - far more than the positions -
and an external asset is cached, compressed on the wire and kept out of the
page's own weight. atlas-app.html loads its data the same way.

The payload carries only what the app draws - place, model, age, latitude and
longitude - not the whole build payload. Coordinates are rounded to two
decimals, which is about a kilometre and far finer than anything this app
claims. A model that places no crust at an age gets null, and the app renders
that as its own state rather than as an absence.

Run:  python3 build_app.py            report only
      python3 build_app.py --apply
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
APP = os.path.join(SITE, "continents-app.html")
LAND_SRC = os.path.join(HERE, "data", "land.json")
LAND_OUT = os.path.join(SITE, "assets", "continents-land.js")
TEMPLATE = os.path.join(HERE, "app_template.html")
PAYLOAD = os.path.join(HERE, "outputs", "continents_payload.json")


def app_payload(P):
    past = P["past"]
    return {
        "fetched": past["fetched"],
        "ages": past["ages"],
        "models": [{"name": m["name"], "oldest_ma": m["oldest_ma"]}
                   for m in past["models"]],
        "tracks": [{"place": t["place"], "lon": t["lon"], "lat": t["lat"],
                    "models": {m: {"lat": t["models"][m]["lat"],
                                   "lon": t["models"][m]["lon"]}
                               for m in [x["name"] for x in past["models"]]}}
                   for t in past["tracks"]],
    }


def write_land(apply=False):
    """Copy the coastline set out to the site as a plain script."""
    if not os.path.exists(LAND_SRC):
        return None
    land = json.load(open(LAND_SRC, encoding="utf-8"))
    head = ("/* Reconstructed coastlines for continents-app.html. Built by "
            "continents/build_app.py from data/land.json; do not edit. */")
    body = json.dumps(land, separators=(",", ":"), sort_keys=True)
    # window.LAND, not const LAND: a top-level const in a separate
    # script is a lexical binding, not a property of the window, so
    # anything inspecting the page from outside - the test does - can
    # see the app work and still not find the data.
    js = head + chr(10) + "window.LAND = " + body + ";" + chr(10)
    if apply:
        os.makedirs(os.path.dirname(LAND_OUT), exist_ok=True)
        open(LAND_OUT, "w", encoding="utf-8").write(js)
    return len(js), len(land["frames"]), land["models"]


def render(P):
    t = open(TEMPLATE, encoding="utf-8").read()
    data = app_payload(P)
    t = t.replace("{{fetched}}", data["fetched"])
    t = t.replace("{{payload}}", json.dumps(data, separators=(",", ":"),
                                            sort_keys=True))
    left = sorted(set(re.findall(r"{{(\w+)}}", t)))
    if left:
        raise SystemExit(f"app placeholders without a value: {left}")
    # the ?v= stamps bust_cache.py owns, if the app already ships
    if os.path.exists(APP):
        shipped = open(APP, encoding="utf-8").read()
        stamps = dict(re.findall(r'(?:href|src)="([^"?]+)\?v=([0-9a-f]+)"',
                                 shipped))

        def stamp(m):
            path = m.group(2)
            return (f'{m.group(1)}="{path}?v={stamps[path]}"'
                    if path in stamps else m.group(0))
        t = re.sub(r'(href|src)="([^"?]+\.(?:css|js))"', stamp, t)
    return t


def main(apply=False):
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    land = write_land(apply)
    if land is None:
        print("  no data/land.json; run fetch_land.py. The viewer will draw "
              "no continents.")
    else:
        n, frames, models = land
        print(f"  continents-land.js: {n:,} bytes, {frames} frames, "
              f"{len(models)} models ({', '.join(models)})")
    t = render(P)
    if os.path.exists(APP):
        old = open(APP, encoding="utf-8").read()
        print("  continents-app.html: " + ("unchanged" if old == t
                                           else "would change" if not apply
                                           else "rewritten"))
    else:
        print("  continents-app.html: new"
              + ("" if apply else " (not written)"))
    if apply:
        open(APP, "w", encoding="utf-8").write(t)
    print(f"  payload {len(json.dumps(app_payload(P), separators=(',', ':'))):,}"
          f" bytes inline, app {len(t):,} bytes")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
