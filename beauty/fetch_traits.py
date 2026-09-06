"""
Fetch the two open bird datasets and reduce each to the columns the model
reads. Both are CC BY 4.0, pinned by hash, and stay whole in data/raw/,
which the code archive skips; the slim tables ship.

  AVONET (Tobias et al. 2022, Ecology Letters 25:581-597), sheet
  AVONET1_BirdLife: 11,009 species on the HBW-BirdLife v5 taxonomy with
  body mass, range size and family.        -> data/avonet_slim.csv

  Santangeli et al. 2023 (npj Biodiversity 2:20), the data and scripts
  deposit: mean rated attractiveness per species and sex from the
  iratebirds project, keyed to the same BirdLife v5 names.
                                           -> data/attractiveness_slim.csv

The Santangeli file also carries a Red List category column as the authors
had it in 2021. It is not copied into the slim table: the page's threat
column comes from the reader's own Red List token (fetch_iucn.py), and
build_beauty.py reads the 2021 column straight from the raw zip only as a
labelled fallback when no token is set.

Run:  python3 fetch_traits.py
"""

import csv
import hashlib
import io
import os
import sys
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
DATA = os.path.join(HERE, "data")
sys.path.insert(0, HERE)
from netutil import UA  # noqa: E402

SOURCES = {
    "avonet.xlsx": ("https://ndownloader.figshare.com/files/34480856",
                    "eb645e83dddb40f1654a3e8d721998dbca76eff540231b7b809267c1e96f8d3e"),
    "santangeli_2023.zip": ("https://ndownloader.figshare.com/files/42156828",
                            "53bdf95cff5eb1bba074c65e0ec5b3182a9e661bafe7b00cc51723ac225e80d1"),
}
AVONET_OUT = os.path.join(DATA, "avonet_slim.csv")
ATTR_OUT = os.path.join(DATA, "attractiveness_slim.csv")
SANT_CSV = "Santangeli_et_al_data_and_scripts/monsterALL2_2_2023.csv"


def fetch():
    os.makedirs(RAW, exist_ok=True)
    for name, (url, sha) in SOURCES.items():
        path = os.path.join(RAW, name)
        if not os.path.exists(path):
            print(f"  downloading {url}")
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=300) as r, open(path, "wb") as fh:
                fh.write(r.read())
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if h != sha:
            sys.exit(f"  SHA-256 mismatch for {name}\n    got      {h}\n    expected {sha}\n"
                     f"  The pinned deposit has changed; nothing was written.")
        print(f"  {name} verified")


def slim_avonet():
    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(RAW, "avonet.xlsx"), read_only=True)
    ws = wb["AVONET1_BirdLife"]
    rows = ws.iter_rows(values_only=True)
    hdr = list(next(rows))
    ix = {h: i for i, h in enumerate(hdr)}
    cols = ["species", "family", "order", "mass_g", "range_km2", "centroid_lat", "migration"]
    n = 0
    with open(AVONET_OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            if not r[ix["Species1"]]:
                continue
            w.writerow([r[ix["Species1"]], r[ix["Family1"]], r[ix["Order1"]],
                        r[ix["Mass"]], r[ix["Range.Size"]], r[ix["Centroid.Latitude"]],
                        r[ix["Migration"]]])
            n += 1
    print(f"  {n:,} species -> {os.path.relpath(AVONET_OUT, HERE)}")


def slim_attractiveness():
    z = zipfile.ZipFile(os.path.join(RAW, "santangeli_2023.zip"))
    r = csv.DictReader(io.TextIOWrapper(z.open(SANT_CSV), encoding="utf-8"))
    acc = {}
    for row in r:
        name = row["sciName_HBWBLv5"]
        if not name or name == "NA":
            continue
        try:
            v = float(row["attractiveness_mean"])
        except ValueError:
            continue
        acc.setdefault(name, []).append(v)
    with open(ATTR_OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["species", "attractiveness", "n_sex_rows"])
        for name in sorted(acc):
            vals = acc[name]
            w.writerow([name, f"{sum(vals) / len(vals):.4f}", len(vals)])
    print(f"  {len(acc):,} species -> {os.path.relpath(ATTR_OUT, HERE)}")


if __name__ == "__main__":
    from netutil import Lock
    with Lock("traits", HERE):
        fetch()
        slim_avonet()
        slim_attractiveness()
