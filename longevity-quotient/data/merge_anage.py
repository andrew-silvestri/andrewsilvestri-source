"""
Merge AnAge into the curated table.

The curated animals.csv is small and hand-checked: every row carries a wild
maximum AND a captive maximum, which is the comparison this project is built
around. AnAge is large and machine-readable but carries one longevity figure per
species. Neither is a substitute for the other, so this merges them rather than
replacing one with the other.

    python3 load_anage.py     # AnAge  -> animals_anage.csv
    python3 merge_anage.py    # both   -> animals_merged.csv + a conflict report

Then point build_lq.py at the merged file:

    python3 build_lq.py --data data/animals_merged.csv

## The rules, and why

1. **Curated rows win.** A species in both tables keeps its curated row. The
   curated row was checked by hand, distinguishes wild from captive, and
   excludes disputed records that AnAge sometimes carries.

2. **AnAge fills gaps, never overwrites.** If a curated row has no captive
   figure and AnAge has one whose specimen was captive, the gap is filled and
   the row is marked as such. A curated row's existing numbers are never
   replaced.

3. **Everything AnAge has that the curated table does not is added outright.**
   This is where the species count actually grows.

4. **Disagreements are reported, not silently resolved.** Where both tables have
   a longevity for the same species and they differ by more than a factor of
   `TOLERANCE`, the pair is written to the conflict report for you to look at.
   A factor-of-two disagreement usually means one of the two is a different
   subspecies, a disputed record, or a units error.

5. **Duplicate scientific names are preserved.** The honey bee appears twice in
   the curated table, as queen and as worker, on purpose: same genome, tenfold
   difference in lifespan. Matching on scientific name alone would collapse
   them, so any curated name appearing more than once is locked and AnAge is
   never merged into it.

6. **Colonial flags survive.** AnAge has no notion of a colony, so its rows
   arrive flagged `no`. Curated colonial flags are kept.

## What the merge does not fix

It does not give a wild figure to the ~4,000 species arriving from AnAge. They
land with a captive maximum and an empty wild column, which is honest but means
the wild-against-captive view stays thin outside the curated core. It also does
not reconcile taxonomy: AnAge's class and order names occasionally differ from
the curated table's (Artiodactyla against Cetartiodactyla, for one), which shows
up as two group rows that ought to be one. `--check-taxonomy` lists those.
"""

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CURATED = os.path.join(HERE, "animals.csv")
ANAGE = os.path.join(HERE, "animals_anage.csv")
OUT = os.path.join(HERE, "animals_merged.csv")
REPORT = os.path.join(HERE, "merge_report.txt")

COLS = ["common_name", "scientific_name", "kingdom", "phylum", "class",
        "order", "family", "genus", "mass_g", "wild_yr", "captive_yr",
        "colonial", "quality", "note"]

TOLERANCE = 2.0     # report longevity disagreements beyond this factor
MASS_TOLERANCE = 3.0  # and mass disagreements beyond this one


def key(name):
    return " ".join(name.strip().lower().split())


def read(path, label):
    if not os.path.exists(path):
        sys.exit(f"{label} not found at {path}\n"
                 "Run load_anage.py first." if "anage" in path.lower()
                 else f"{label} not found at {path}")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    missing = [c for c in COLS if c not in (rows[0] if rows else {})]
    if missing:
        sys.exit(f"{label} is missing columns: {missing}\n"
                 "Both files must use the 14-column schema.")
    return rows


def as_float(v):
    v = (v or "").strip()
    try:
        return float(v) if v else None
    except ValueError:
        return None


def ratio(a, b):
    if not a or not b:
        return None
    return max(a, b) / min(a, b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--curated", default=CURATED)
    ap.add_argument("--anage", default=ANAGE)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check-taxonomy", action="store_true",
                    help="list taxon names that differ between the two tables")
    args = ap.parse_args()

    cur = read(args.curated, "curated table")
    ana = read(args.anage, "AnAge export")

    # Names appearing more than once in the curated table are castes or
    # morphs of one species and must not be merged into.
    counts = {}
    for r in cur:
        counts[key(r["scientific_name"])] = \
            counts.get(key(r["scientific_name"]), 0) + 1
    locked = {k for k, n in counts.items() if n > 1}

    by_name = {}
    for r in cur:
        by_name.setdefault(key(r["scientific_name"]), []).append(r)

    merged = [dict(r) for r in cur]
    index = {key(r["scientific_name"]): r for r in merged
             if key(r["scientific_name"]) not in locked}

    added, filled, conflicts, skipped_locked = [], [], [], []

    for a in ana:
        k = key(a["scientific_name"])
        if k in locked:
            skipped_locked.append(a["scientific_name"])
            continue
        target = index.get(k)
        if target is None:
            merged.append({c: a.get(c, "") for c in COLS})
            added.append(a["scientific_name"])
            continue

        # Same species in both. Compare, then fill gaps only.
        a_life = as_float(a["captive_yr"]) or as_float(a["wild_yr"])
        c_life = max([v for v in (as_float(target["wild_yr"]),
                                  as_float(target["captive_yr"])) if v],
                     default=None)
        r = ratio(a_life, c_life)
        if r and r > TOLERANCE:
            conflicts.append((target["common_name"], a["scientific_name"],
                              "longevity", c_life, a_life, r))
        rm = ratio(as_float(a["mass_g"]), as_float(target["mass_g"]))
        if rm and rm > MASS_TOLERANCE:
            conflicts.append((target["common_name"], a["scientific_name"],
                              "body mass", as_float(target["mass_g"]),
                              as_float(a["mass_g"]), rm))

        if not target["captive_yr"].strip() and a["captive_yr"].strip():
            target["captive_yr"] = a["captive_yr"]
            target["note"] = (target["note"] + "; captive figure from AnAge"
                              ).lstrip("; ")
            filled.append((target["common_name"], "captive"))
        elif not target["wild_yr"].strip() and a["wild_yr"].strip():
            target["wild_yr"] = a["wild_yr"]
            target["note"] = (target["note"] + "; wild figure from AnAge"
                              ).lstrip("; ")
            filled.append((target["common_name"], "wild"))

    for r in merged:
        r.setdefault("colonial", "no")
        if not r["colonial"].strip():
            r["colonial"] = "no"

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(merged)

    # ---- report ---------------------------------------------------------
    lines = []
    add = lines.append
    add(f"curated  : {len(cur)} species")
    add(f"AnAge    : {len(ana)} species")
    add(f"merged   : {len(merged)} species  "
        f"(+{len(added)} new, {len(filled)} gaps filled)")
    add("")
    if skipped_locked:
        add(f"{len(skipped_locked)} AnAge rows skipped because the curated "
            f"table holds more than one row under that name")
        for s in sorted(set(skipped_locked)):
            add(f"    {s}  (castes or morphs kept separate)")
        add("")
    if filled:
        add(f"gaps filled from AnAge ({len(filled)}):")
        for n, which in filled[:25]:
            add(f"    {n:34s} {which}")
        if len(filled) > 25:
            add(f"    … and {len(filled)-25} more")
        add("")
    if conflicts:
        add(f"DISAGREEMENTS worth reviewing ({len(conflicts)}) — "
            f"curated value kept in every case:")
        add(f"    {'species':34s} {'field':10s} {'curated':>10s} "
            f"{'AnAge':>10s} {'factor':>7s}")
        for name, sci, field, c, a, r in sorted(conflicts,
                                                key=lambda x: -x[5])[:40]:
            add(f"    {name[:33]:34s} {field:10s} {c:10.4g} {a:10.4g} "
                f"{r:6.1f}x")
        if len(conflicts) > 40:
            add(f"    … and {len(conflicts)-40} more")
        add("")

    counts_by_class = {}
    for r in merged:
        counts_by_class[r["class"]] = counts_by_class.get(r["class"], 0) + 1
    add("merged table by class:")
    for k in sorted(counts_by_class, key=lambda k: -counts_by_class[k])[:15]:
        add(f"    {k or '(blank)':24s} {counts_by_class[k]}")
    n_pair = sum(1 for r in merged
                 if r["wild_yr"].strip() and r["captive_yr"].strip())
    add("")
    add(f"{n_pair} species carry BOTH a wild and a captive figure "
        f"({100*n_pair/len(merged):.0f}% of the merged table).")
    add("That subset is the only one where the wild-against-captive view "
        "means anything.")

    if args.check_taxonomy:
        add("")
        add("taxonomy names present in only one of the two tables:")
        for rank in ("phylum", "class", "order"):
            c = {r[rank] for r in cur if r[rank]}
            a = {r[rank] for r in ana if r[rank]}
            only_c, only_a = sorted(c - a), sorted(a - c)
            if only_c or only_a:
                add(f"  {rank}:")
                if only_c:
                    add(f"    curated only: {', '.join(only_c[:12])}")
                if only_a:
                    add(f"    AnAge only  : {', '.join(only_a[:12])}")

    text = "\n".join(lines)
    open(REPORT, "w", encoding="utf-8").write(text + "\n")
    print(text)
    print(f"\nwritten: {args.out}")
    print(f"report : {REPORT}")
    print("\nRebuild the model against it with:")
    print(f"    python3 build_lq.py --data {os.path.relpath(args.out, os.path.dirname(HERE))}")


if __name__ == "__main__":
    main()
