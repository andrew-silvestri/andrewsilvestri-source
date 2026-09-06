"""Fetch MIDAS GNSS station velocities from the Nevada Geodetic Laboratory.

Source
------
Blewitt, G., Kreemer, C., Hammond, W.C. and Gazeaux, J. (2016). MIDAS robust
trend estimator for accurate GPS station velocities without step detection.
Journal of Geophysical Research: Solid Earth 121(3), 2054-2068,
doi:10.1002/2015JB012552. NGL states no licence and asks for that citation.

Two files:
  midasfile      one row per station, velocities and uncertainties, IGS20
  platevel.all   NGL's station-to-plate assignment and its own model velocity

FRAME, WHICH IS A GATE
----------------------
The page compares this velocity field with ITRF2020-PMM. That comparison is
only legal because IGS20 is the IGS realisation of ITRF2020; if NGL ever
publishes at the same path in a different frame, every "agrees to under a
millimetre a year" number on the page becomes a frame offset presented as
agreement, and nothing downstream would notice. So the frame is asserted
from the URL and recorded in the provenance (gate B7).

THE PIN IS NOT A BLOCKER
------------------------
NGL rebuilds midasfile weekly. A stale hash is therefore not an error, it is
a fact about which snapshot the page was built from. On mismatch this script
says so and exits without writing, rather than silently recomputing the page
on a different Earth. The build never reads data/raw; it reads the committed
data/stations.csv, so a reader without the 7 MB download still reproduces
every number.

Writes
------
data/stations.csv        all 21,910 stations, committed
data/ngl_provenance.json the pin and the frame, committed

Run:  python3 fetch_ngl.py [--repin]
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
RAWDIR = os.path.join(HERE, "data", "raw")
OUT = os.path.join(HERE, "data", "stations.csv")
PROV = os.path.join(HERE, "data", "ngl_provenance.json")

BASE = "https://geodesy.unr.edu/gps_timeseries/IGS20/midas/"
FILES = {"midasfile": "midasfile", "platevel.all": "platevel.all"}
FRAME = "IGS20"
FRAME_NOTE = ("IGS20 is the IGS realisation of ITRF2020, which is what makes "
              "the comparison with ITRF2020-PMM a comparison of models rather "
              "than of reference frames.")
# The pin lives in data/ngl_pin.json rather than here, so that moving the
# page to a new NGL snapshot is a diff in a data file that a reviewer can see,
# not an edit inside a script. Written by --repin.
PIN = os.path.join(HERE, "data", "ngl_pin.json")


def pinned():
    return json.load(open(PIN, encoding="utf-8")) if os.path.exists(PIN) else {}


def fetch(name, force=False):
    dst = os.path.join(RAWDIR, name)
    if os.path.exists(dst) and not force:
        return dst
    os.makedirs(RAWDIR, exist_ok=True)
    url = BASE + FILES[name]
    print(f"  downloading {url}")
    with urllib.request.urlopen(url, timeout=600) as r, open(dst, "wb") as f:
        f.write(r.read())
    return dst


def load_plates(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        f = line.split()
        if len(f) >= 2:
            out[f[0]] = f[1]
    return out


def parse_midas(path, plates):
    """Columns are NGL's own, from midas.readme.txt, not reverse-engineered:
    9-11 east/north/up velocity in m/yr, 12-14 their uncertainties, 25-27
    latitude, longitude and height. One-based there, zero-based here."""
    rows = []
    for line in open(path, encoding="utf-8"):
        f = line.split()
        if len(f) < 27:
            continue
        try:
            lon = (float(f[-2]) + 180.0) % 360.0 - 180.0
            rows.append({
                "sta": f[0],
                "lat": round(float(f[-3]), 6),
                "lon": round(lon, 6),
                "ve": f[8], "vn": f[9], "sve": f[11], "svn": f[12],
                "dur_yr": f[4],
                "ngl_plate": plates.get(f[0], ""),
            })
        except ValueError:
            continue
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repin", action="store_true",
                    help="accept the current files and rewrite the pins")
    ap.add_argument("--force", action="store_true", help="re-download")
    args = ap.parse_args()

    if FRAME not in BASE:
        sys.exit("fetch_ngl: gate B7 failed. The download path no longer "
                 f"names {FRAME}. Every comparison with ITRF2020-PMM on this "
                 "page assumes that frame; stop and check before proceeding.")

    digests, paths = {}, {}
    for name in FILES:
        p = fetch(name, args.force)
        paths[name] = p
        digests[name] = hashlib.sha256(open(p, "rb").read()).hexdigest()
        print(f"  {name:14} {os.path.getsize(p):>10,} bytes  "
              f"sha256 {digests[name][:16]}...")

    have = pinned()
    stale = [n for n in FILES if digests[n] != have.get(n, {}).get("sha256")]
    if stale and not args.repin:
        print("")
        for n in stale:
            was = have.get(n, {}).get("sha256", "(never pinned)")
            print(f"  {n}: pinned {was[:16]}..., got {digests[n][:16]}...")
        sys.exit(
            "fetch_ngl: these files are not the pinned snapshot. NGL rebuilds "
            "midasfile weekly, so this is expected on a fresh download and is "
            "not corruption. Nothing was written. Either keep the committed "
            "data/stations.csv, which is what the build reads, or rerun with "
            "--repin to move the page to this snapshot and re-run every gate.")

    if stale:
        json.dump({n: {"sha256": digests[n],
                       "bytes": os.path.getsize(paths[n]),
                       "url": BASE + FILES[n],
                       "pinned_on": datetime.now(timezone.utc).date().isoformat()}
                   for n in FILES},
                  open(PIN, "w", encoding="utf-8"), indent=1, sort_keys=True)
        print(f"  re-pinned to this snapshot in {os.path.relpath(PIN, HERE)}")

    rows = parse_midas(paths["midasfile"], load_plates(paths["platevel.all"]))
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["sta", "lat", "lon", "ve", "vn",
                                          "sve", "svn", "dur_yr", "ngl_plate"])
        w.writeheader()
        w.writerows(rows)

    json.dump({
        "source": BASE,
        "citation": ("Blewitt, G., Kreemer, C., Hammond, W.C. and Gazeaux, J. "
                     "(2016). MIDAS robust trend estimator for accurate GPS "
                     "station velocities without step detection. Journal of "
                     "Geophysical Research: Solid Earth 121(3), 2054-2068, "
                     "doi:10.1002/2015JB012552."),
        "licence": "none stated; NGL asks for the citation above",
        "frame": FRAME, "frame_note": FRAME_NOTE,
        "sha256": digests,
        "fetched": datetime.now(timezone.utc).date().isoformat(),
        "stations": len(rows),
        "stations_with_plate": sum(1 for r in rows if r["ngl_plate"]),
    }, open(PROV, "w", encoding="utf-8"), indent=1, sort_keys=True)

    print(f"\n  wrote data/stations.csv  {len(rows):,} stations, "
          f"{os.path.getsize(OUT):,} bytes")
    print(f"  B7  ok    frame {FRAME}: {FRAME_NOTE}")


if __name__ == "__main__":
    main()
