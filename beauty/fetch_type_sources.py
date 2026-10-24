"""
Where the non-research record types come from: a spot check, not a census.

For 40 modelled species drawn at random (seed 7, from data/birds_open.csv),
one OpenAlex call per record type asks for the works of 2015-2024 whose
title or abstract names any of them, grouped by the source that published
each work. It is what lets the page say what a `dataset` or a
`reference-entry` is (GBIF downloads; Red List assessments and Birds of the
World accounts) as a measurement rather than as a reading of three examples.
Three calls, 10 credits each.

Writes data/type_sources.csv: type, source, works, of_type, species_sampled,
fetched. The key is read by name (OPENALEX_KEY) through envfile.py.
Run:  python fetch_type_sources.py
"""

import csv
import datetime as dt
import os
import random
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from netutil import get_json, polite  # noqa: E402
import envfile  # noqa: E402

SPECIES = os.path.join(HERE, "data", "birds_open.csv")
OUT = os.path.join(HERE, "data", "type_sources.csv")
N, SEED = 40, 7
TYPES = ("dataset", "reference-entry", "article")


def main():
    key = envfile.get("OPENALEX_KEY")
    sp = [r["species"] for r in csv.DictReader(open(SPECIES, encoding="utf-8"))]
    random.Random(SEED).shuffle(sp)
    q = " OR ".join(f'"{n}"' for n in sp[:N])
    today = dt.date.today().isoformat()
    rows = []
    for typ in TYPES:
        params = polite({"filter": f"title_and_abstract.search:{q},publication_year:2015-2024,type:{typ}",
                         "group_by": "primary_location.source.id"})
        if key:
            params["api_key"] = key
        j = get_json("https://api.openalex.org/works?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote))
        tot = int(j["meta"]["count"])
        for g in j["group_by"]:
            rows.append({"type": typ, "source": g["key_display_name"] or "(no source)", "works": int(g["count"]),
                         "of_type": tot, "species_sampled": N, "fetched": today})
        print(f"  {typ:16s} {tot:6,} works, {len(j['group_by'])} sources")
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"  -> {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()
