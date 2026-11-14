"""Readers for the messaging page. Each reads a hash-checked raw file (netfetch.verified), so the tournament
figures are computed from the authors' own deposit, and the transcribed tables are read with their sources.

tournament()   the 63-country tournament, one row per participant: condition, country, and the four
               outcomes as the authors score them (belief and policy support: the mean of a participant's
               answered items, 0-100; sharing: 1 if willing to share, 0 if not, missing for "I do not use
               social media"; WEPT: pages of the tree-planting task completed, 0-8). The 48 rows with no
               condition label are dropped, as the authors' code does.
table(name)    a tracked CSV in data/ as a list of dicts.
"""
import csv
import gzip
import os

from netfetch import HERE, RAW, verified

BELIEF = [f"Belief{i}" for i in range(1, 5)]
POLICY = [f"Policy{i}" for i in range(1, 10)]


def tournament():
    p, row = verified("data63.xlsx")
    cache = RAW / f"data63_{row['sha1'][:12]}.csv.gz"     # derived from the verified file; gitignored
    if not cache.exists():
        import pandas as pd
        df = pd.read_excel(p, sheet_name="data4joe (1)")
        df = df[df["condName"].notna()]
        out = pd.DataFrame({"cond": df["condName"], "country": df["Country"],
                            "belief": df[BELIEF].mean(axis=1, skipna=True),
                            "policy": df[POLICY].mean(axis=1, skipna=True),
                            "share": df["SHAREcc"], "wept": df["WEPTcc"]})
        out.to_csv(cache, index=False, compression="gzip")
    with gzip.open(cache, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def table(name):
    with open(os.path.join(HERE, "data", name), encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if not r[next(iter(r))].startswith("#")]
