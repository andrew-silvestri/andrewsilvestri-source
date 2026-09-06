"""
Year of description for each bird species: the year in the name's
authorship, e.g. "(Linnaeus, 1758)" -> 1758.

One call per species to the GBIF backbone name-match endpoint (free, no
key; the backbone is built from the Catalogue of Life and returns the full
scientific name with authorship). When GBIF has no exact match the
Catalogue of Life's ChecklistBank API (dataset 3LR, the latest COL release,
CC BY) is tried. A species neither resolves is recorded with no year and
left out of the model.

Writes data/description_years.csv: species, matched_name, authorship,
year, source (which register answered: gbif, col or none), fetched (the
date this script wrote the row; the build refuses a table without it).
Resumable.

Run:  python3 fetch_years.py
"""

import csv
import datetime as dt
import os
import re
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from netutil import get_json, check_header, trim_partial_row, Budget, Lock  # noqa: E402

SPECIES = os.path.join(HERE, "data", "avonet_slim.csv")
OUT = os.path.join(HERE, "data", "description_years.csv")
COLS = ["species", "matched_name", "authorship", "year", "source", "fetched"]
GBIF = "https://api.gbif.org/v1/species/match?kingdom=Animalia&class=Aves&rank=SPECIES&name="
COL = "https://api.checklistbank.org/dataset/3LR/nameusage/search?content=SCIENTIFIC_NAME&limit=3&q="
YEAR = re.compile(r"\b(1[6-9]\d\d|20[0-2]\d)\b")


def gbif_lookup(name):
    j = get_json(GBIF + urllib.parse.quote(name)) or {}
    if j.get("matchType") != "EXACT" or j.get("rank") != "SPECIES":
        return None
    full = j.get("scientificName", "")
    auth = full[len(j.get("canonicalName", name)):].strip() if full else ""
    m = YEAR.search(auth)
    return j.get("canonicalName", name), auth, m.group(1) if m else "", "gbif"


def col_lookup(name):
    j = get_json(COL + urllib.parse.quote(name)) or {}
    for hit in j.get("result", []):
        nm = hit.get("usage", {}).get("name", {})
        if nm.get("scientificName", "").lower() != name.lower():
            continue
        auth = nm.get("authorship", "") or ""
        m = YEAR.search(auth)
        return nm["scientificName"], auth, m.group(1) if m else "", "col"
    return None


def main():
    species = [r["species"] for r in csv.DictReader(open(SPECIES, encoding="utf-8"))]
    trim_partial_row(OUT)
    check_header(OUT, COLS)
    done = set()
    if os.path.exists(OUT):
        done = {r["species"] for r in csv.DictReader(open(OUT, encoding="utf-8"))}
    todo = [s for s in species if s not in done]
    print(f"  {len(species):,} species, {len(done):,} done, {len(todo):,} to fetch")
    new = not os.path.exists(OUT)
    n, missing = 0, 0
    today = dt.date.today().isoformat()
    with Lock("years", HERE) as lk, open(OUT, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(COLS)
        try:
            for s in todo:
                hit = gbif_lookup(s) or col_lookup(s)
                if hit and hit[2]:
                    w.writerow([s, *hit, today])
                else:
                    w.writerow([s, hit[0] if hit else "", hit[1] if hit else "", "", "none", today])
                    missing += 1
                n += 1
                lk.beat()
                if n % 500 == 0:
                    fh.flush()
                    print(f"  {n:,} fetched, {missing} without a year")
        except Budget as e:
            print(f"  stopped: {e}; re-run to continue")
    print(f"  {n:,} names looked up ({missing} without a year) -> {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()
