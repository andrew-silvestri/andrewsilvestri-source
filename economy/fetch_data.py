"""
The two open cohorts this page computes over, verified by hash.

Both are supplementary files of CC BY papers, so both ship inside
economy-code.zip and a reader does not need to download anything to
reproduce the page. This script exists to prove that what ships is what the
publisher published:

  data/lanferdini_2020_table1.xlsx
      Lanferdini et al., Frontiers in Physiology 11:979, 2020,
      doi:10.3389/fphys.2020.00979, PMC7419685, CC BY 4.0. Supplementary
      Table 1: 20 male recreational runners with VO2max, both ventilatory
      thresholds, running economy at 12 and 16 km/h, energy cost, velocity at
      VO2max and a 3000 m time. The only open file carrying all three terms of
      the performance model and a race result for the same person.

  data/vickers_2016_master.xlsx
      Vickers & Vertosick, BMC Sports Science, Medicine and Rehabilitation
      8:26, 2016, doi:10.1186/s13102-016-0052-y, PMC5000509, CC BY 4.0.
      Additional file 2: 2,303 recreational runners with self-reported times
      at six distances, course difficulty, training volume, sex, age and BMI.

Springer serves its supplement to a script, so that one is re-downloaded and
checked. Frontiers and PMC both refuse one - PMC answers a scripted request
for the file with an HTML page - so the Lanferdini table is verified in place
and DATA_SOURCES.md records the manual step. A file whose hash has moved
stops the build rather than being computed on.

Run:  python3 fetch_data.py
"""

import hashlib
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

MAILTO = "dasilvestri12@gmail.com"
AGENT = f"andrewsilvestri.com economy figures ({MAILTO})"

SOURCES = {
    "lanferdini_2020_table1.xlsx": {
        "sha256": "5dc3d118b545b8858593077519f3c814ae1cce98eb68d86e5effb42f4783c53a",
        "url": None,              # see the module docstring
        "landing": "https://www.frontiersin.org/articles/10.3389/fphys.2020.00979/full"
                   "#supplementary-material",
        "cite": "Lanferdini et al., Frontiers in Physiology 11:979, 2020, "
                "doi:10.3389/fphys.2020.00979, CC BY 4.0",
    },
    "vickers_2016_master.xlsx": {
        "sha256": "efee4d95613f10280082ebe4b44bbfce327594c0d7552b10995e51c39088ff22",
        "url": "https://static-content.springer.com/esm/"
               "art%3A10.1186%2Fs13102-016-0052-y/MediaObjects/"
               "13102_2016_52_MOESM2_ESM.xlsx",
        "landing": "https://bmcsportsscimedrehabil.biomedcentral.com/articles/"
                   "10.1186/s13102-016-0052-y",
        "cite": "Vickers & Vertosick, BMC Sports Science, Medicine and "
                "Rehabilitation 8:26, 2016, doi:10.1186/s13102-016-0052-y, CC BY 4.0",
    },
}


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as fh:
        fh.write(r.read())


def main():
    os.makedirs(DATA, exist_ok=True)
    bad = []
    for name, s in SOURCES.items():
        path = os.path.join(DATA, name)
        if not os.path.exists(path) and s["url"]:
            print(f"  downloading {name}")
            download(s["url"], path)
        if not os.path.exists(path):
            bad.append(f"{name} is missing and the publisher does not serve it to a "
                       f"script.\n    Download Supplementary Table 1 from {s['landing']}\n"
                       f"    and save it as data/{name}.")
            continue
        got = digest(path)
        if got != s["sha256"]:
            bad.append(f"SHA-256 mismatch for {name}\n      got      {got}\n"
                       f"      expected {s['sha256']}\n    The pinned file has "
                       f"changed; nothing was computed on it.")
            continue
        size = os.path.getsize(path)
        print(f"  {name:34s} {size:>9,} B  verified")
    if bad:
        sys.exit("\n  " + "\n  ".join(bad))
    print("  both cohorts verified")


if __name__ == "__main__":
    main()
