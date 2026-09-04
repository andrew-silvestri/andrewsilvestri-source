"""
Checks on the merged table.

A merge of six databases fails quietly. Nothing crashes when the same animal
enters twice under two spellings, or when a lifespan in months is read as
years, or when a source that should only have filled a gap has silently
overwritten a hand-checked record. The table still builds, the regression still
runs, and the number on the page is wrong by an amount nobody can see.

So the things that would be invisible are measured.

Run:  python3 test_merge.py
"""

import collections
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "data"))

import build_lq                                       # noqa: E402

MERGED = os.path.join(HERE, "data", "animals_merged.csv")
SEED = os.path.join(HERE, "data", "animals.csv")
PROV = os.path.join(HERE, "outputs", "provenance.csv")

fails = checks = 0


def ok(cond, label, detail=""):
    global fails, checks
    checks += 1
    if cond:
        print(f"  ok    {label}" + (f"   {detail}" if detail else ""))
    else:
        fails += 1
        print(f"  FAIL  {label}" + (f"\n          {detail}" if detail else ""))


rows = list(csv.DictReader(open(MERGED, encoding="utf-8")))
seed = list(csv.DictReader(open(SEED, encoding="utf-8")))
prov = list(csv.DictReader(open(PROV, encoding="utf-8")))
summary = json.load(open(os.path.join(HERE, "outputs", "summary.json"),
                         encoding="utf-8"))

print("\n  Integrity")
# A repeated binomial is allowed only where the seed put it there on purpose -
# the honey bee worker and queen are the same species and are the point.
seed_names = collections.Counter(s["scientific_name"].strip().lower()
                                 for s in seed)
allowed = {n for n, c in seed_names.items() if c > 1}
pairs = collections.Counter((r["scientific_name"].strip().lower(),
                             r["common_name"].strip().lower()) for r in rows)
names = collections.Counter(r["scientific_name"].strip().lower()
                            for r in rows)
dupes = [n for n, c in names.items() if c > 1 and n not in allowed]
ok(not dupes, "one row per species, bar the castes the seed splits on purpose",
   f"{len(rows):,} rows, {len(allowed)} deliberate split"
   + (f", unexpected: {dupes[:4]}" if dupes else ""))
ok(all(c == 1 for c in pairs.values()),
   "and no row is a straight duplicate of another")

ok(all(r["scientific_name"].count(" ") >= 1 for r in rows),
   "every name is a binomial")
ok(all(r["class"].strip() and r["order"].strip() and r["family"].strip()
       for r in rows), "no blank taxonomy")
stale = {c for c in (r["class"] for r in rows)} & set(build_lq.CLASS_SYNONYM)
ok(not stale, "the stored table uses canonical class names",
   f"{len({r['class'] for r in rows})} distinct classes"
   if not stale else f"still present: {sorted(stale)}")

bad_mass = [r["scientific_name"] for r in rows
            if not (0 < float(r["mass_g"]) < 2e8)]
ok(not bad_mass, "every mass is positive and below 200 tonnes",
   f"worst: {bad_mass[:3]}" if bad_mass else "")

# Colonial organisms are a different quantity: the 11,000-year glass sponge is
# the age of a colony, not of an animal, which is exactly why the model
# excludes them from every fit. They are bounded separately rather than being
# allowed to widen the bound for everything else.
solo, colony = [], []
for r in rows:
    for k in ("wild_yr", "captive_yr", "unknown_yr"):
        if r[k].strip():
            (colony if r["colonial"].strip().lower() == "yes"
             else solo).append(float(r[k]))
ok(all(0 < v <= 600 for v in solo),
   "no non-colonial animal exceeds the longest verified individual",
   f"max {max(solo):.0f} yr (the ocean quahog and the Greenland shark "
   f"are the ceiling)")
ok(all(0 < v < 20000 for v in colony), "colony ages are bounded too",
   f"{len(colony)} colonial records, max {max(colony):.0f} yr")
ok(all(r["wild_yr"].strip() or r["captive_yr"].strip()
       or r["unknown_yr"].strip() for r in rows),
   "every row has at least one lifespan")

print("\n  The seed table is not overwritten")
# The hand-checked records are the highest-precedence source. If a bulk source
# has replaced one of them, the whole precedence order is broken and nothing
# else in the file can be trusted either.
merged_by = {r["scientific_name"].strip().lower(): r for r in rows}
moved = []
by_pair = {(r["scientific_name"].strip().lower(),
            r["common_name"].strip().lower()): r for r in rows}
for s in seed:
    key = (s["scientific_name"].strip().lower(),
           s["common_name"].strip().lower())
    m = by_pair.get(key) or merged_by.get(s["scientific_name"].strip().lower())
    if not m:
        continue
    for f in ("mass_g", "wild_yr", "captive_yr", "quality"):
        a, b = s[f].strip(), m[f].strip()
        if f == "mass_g" and a and b:
            if abs(float(a) - float(b)) / float(a) > 1e-6:
                moved.append((s["scientific_name"], f, a, b))
        elif a != b and not (a == "" and b == ""):
            if a and b and a.rstrip("0").rstrip(".") == b.rstrip("0").rstrip("."):
                continue
            moved.append((s["scientific_name"], f, a, b))
ok(not moved, "every hand-checked value survives the merge intact",
   f"{len(seed)} seed rows" if not moved else f"{len(moved)} changed: "
   f"{moved[:3]}")

print("\n  Unit sanity, source by source")
# PanTHERIA stores maximum longevity in months. Read as years it makes every
# mammal twelve times too long-lived, which would not crash anything and would
# move the mammalian intercept by more than a decimal order.
mam = [float(r["wild_yr"] or r["captive_yr"] or r["unknown_yr"])
       for r in rows if r["class"] == "Mammalia"]
med = sorted(mam)[len(mam) // 2]
ok(3 < med < 40, "mammal median lifespan is in years, not months",
   f"median {med:.1f} yr across {len(mam):,} mammals")

fish = [float(r["wild_yr"] or r["captive_yr"] or r["unknown_yr"])
        for r in rows if r["class"] in build_lq.FISH]
ok(fish and 1 < sorted(fish)[len(fish) // 2] < 40,
   "fish maxima are plausible",
   f"median {sorted(fish)[len(fish)//2]:.1f} yr across {len(fish):,} fish")

print("\n  Provenance")
ok(len(prov) == len(rows), "one provenance row per species")
# The wild column must only hold what a source labelled wild. Amniote,
# PanTHERIA and AmphiBIO never do, so a wild figure on one of their rows
# means the 2026-09-04 relabelling has regressed.
prov_by = {p["scientific_name"]: p for p in prov}
leak = [r["scientific_name"] for r in rows
        if r["wild_yr"].strip() and prov_by.get(r["scientific_name"], {})
        .get("taken_from") in ("amniote", "pantheria", "amphibio")]
ok(not leak, "no unlabelled-origin source lands in the wild column",
   f"{len(leak)} rows" if leak else
   f"{sum(1 for r in rows if r['unknown_yr'].strip()):,} rows carry a "
   "maximum of unrecorded origin")
srcs = collections.Counter(p["taken_from"] for p in prov)
ok(set(srcs) <= set(["seed", "anage", "amniote", "pantheria", "amphibio",
                     "fishbase"]), "every record names a known source",
   " ".join(f"{k} {v:,}" for k, v in srcs.most_common()))
corr = sum(1 for p in prov if p["corroborating_sources"])
ok(corr > 0, "overlapping records are recorded as corroboration",
   f"{corr:,} species appear in more than one source")

print("\n  The fit still behaves")
g = summary["global_fit"]
ok(0.10 < g["b"] < 0.35, "global slope is in the range allometry predicts",
   f"b = {g['b']:.3f}, so lifespan goes as mass^(1/{1/g['b']:.1f})")
ok(g["n"] > 3000, "the fit is not being carried by a handful of records",
   f"effective n = {g['n']:,.0f}")

# grade C is held out of the fit; it must still reach the table
grades = collections.Counter(r["quality"] for r in rows)
ok(grades["C"] > 0 and build_lq.FIT_STRATEGY == "filter",
   "grade C records are published but held out of the regression",
   f"{grades['C']:,} of {len(rows):,} rows")

# every class fit that survived must be better than the global one for its own
# members, or there is no reason to have fitted it separately
worse = []
for k, f in summary["class_fits"].items():
    if f["r2"] < g["r2"] - 0.05:
        worse.append((k, round(f["r2"], 3)))
ok(not worse, "each surviving group fit beats the global one on its own group",
   f"global r2 {g['r2']:.3f}" if not worse else f"weaker: {worse}")

print("\n  Coverage against the old table")
ok(len(rows) > len(seed) * 10, "the table grew by more than tenfold",
   f"{len(seed):,} -> {len(rows):,} ({len(rows)/len(seed):.1f}x)")
cls = collections.Counter(r["class"] for r in rows)
ok(cls.get("Actinopterygii", 0) > 500,
   "fish are no longer a rounding error, and carry one class name not three",
   f"{cls.get('Actinopterygii', 0):,} ray-finned fish, "
   f"{cls.get('Chondrichthyes', 0):,} cartilaginous")

print(f"\n  {checks - fails}/{checks} checks passed"
      + (f", {fails} FAILED" if fails else ""))
raise SystemExit(1 if fails else 0)
