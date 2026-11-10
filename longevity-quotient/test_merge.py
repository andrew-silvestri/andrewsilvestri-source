"""
Checks on the merged table.

A merge of six databases fails quietly. Nothing crashes when the same animal
enters twice under two spellings, or when a lifespan in months is read as
years, or when a source that should only have filled a gap has silently
overwritten a hand-checked record. The table still builds, the regression still
runs, and the number on the page is wrong by an amount nobody can see.

So the things that would be invisible are measured.

Run:  python test_merge.py [--break nan|synonym|sebastes|manual|family|
                                      source|olm]
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
if "--break" in sys.argv and "nan" in sys.argv:
    # the shipped fault (QA 2026-10-22): a missing FishBase name read as "nan"
    for r in rows:
        if r["scientific_name"] == "Dolloidraco longedorsalis":
            r["common_name"] = "nan"
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
# A field that ingest.CORRECTIONS drops from a seed row, with its reason, is
# not expected to survive; a seed row left with no lifespan is not a record.
import ingest                                         # noqa: E402
dropped = {}
for c in ingest.CORRECTIONS:
    if c["source"] == "seed":
        dropped.setdefault(c["sci"].lower(), set()).update(c.get("drop", ()))
moved = []
by_pair = {(r["scientific_name"].strip().lower(),
            r["common_name"].strip().lower()): r for r in rows}
for s in seed:
    key = (s["scientific_name"].strip().lower(),
           s["common_name"].strip().lower())
    m = by_pair.get(key) or merged_by.get(s["scientific_name"].strip().lower())
    if not m:
        continue
    drop = dropped.get(key[0], set())
    if not [f for f in ("wild_yr", "captive_yr", "unknown_yr")
            if s.get(f, "").strip() and f not in drop]:
        continue                     # no lifespan left: not the record
    for f in ("mass_g", "wild_yr", "captive_yr", "quality"):
        if f in drop:
            continue
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

print("\n  Synonyms, one family per genus, recorded corrections (D-56 b)")
# Each check below is computed from the shipped tables, not from the list
# ingest.py writes, so a merge that silently stops merging is caught here.
table = list(csv.DictReader(open(os.path.join(HERE, "outputs", "lq_table.csv"),
                                 encoding="utf-8")))
if "--break" in sys.argv and "synonym" in sys.argv:
    # a merged-away copy back in the table and in the fits
    src = next(r for r in rows if r["scientific_name"] == "Centrochelys sulcata")
    rows.append(dict(src, scientific_name="Geochelone sulcata",
                     genus="Geochelone"))
    srct = next(r for r in table if r["sci"] == "Centrochelys sulcata")
    table.append(dict(srct, sci="Geochelone sulcata", genus="Geochelone"))
if "--break" in sys.argv and "sebastes" in sys.argv:
    for r in rows + table:
        if (r.get("scientific_name") or r.get("sci")) == "Sebastes borealis":
            r["family"] = "Scorpaenidae"
if "--break" in sys.argv and "manual" in sys.argv:
    # a hand-listed name back in the table as a record of its own
    src = next(r for r in rows if r["scientific_name"] == "Pristis pristis")
    rows.append(dict(src, scientific_name="Pristis perotteti"))
    srct = next(r for r in table if r["sci"] == "Pristis pristis")
    table.append(dict(srct, sci="Pristis perotteti"))
if "--break" in sys.argv and "family" in sys.argv:
    # one grouper filed apart from its genus again (D-92 c)
    for r in rows + table:
        if (r.get("scientific_name") or r.get("sci")) == "Epinephelus itajara":
            r["family"] = "Epinephelidae"
if "--break" in sys.argv and "olm" in sys.argv:
    # AmphiBIO's unsourced 12 years back in place of the projection
    for r in rows:
        if r["scientific_name"] == "Proteus anguinus":
            r["unknown_yr"] = "12"

# 1. The pairs D-29 item 4 named, at most one name each in the table.
named_pairs = [("Centrochelys sulcata", "Geochelone sulcata"),
               ("Apus melba", "Tachymarptis melba"),
               ("Tapirella bairdii", "Tapirus bairdii"),
               ("Hydrochoerus hydrochaeris", "Hydrochoeris hydrochaeris"),
               ("Cacatua leadbeateri", "Lophochroa leadbeateri")]
names_now = {r["scientific_name"] for r in rows}
both = [p for p in named_pairs if p[0] in names_now and p[1] in names_now]
ok(not both, "the audit's named synonym pairs are one record each",
   f"{len(named_pairs)} pairs" if not both else f"both present: {both}")

# 2. Rule one, re-run on the merged table itself: no two rows share a common
#    name, a class and a species epithet (gender ending or one letter aside).
grp = collections.defaultdict(list)
for r in rows:
    grp[(ingest.common_key(r["common_name"]), r["class"])].append(r)
again = []
for (cn, _), rs in grp.items():
    for i, a in enumerate(rs):
        for b in rs[i + 1:]:
            if (a["scientific_name"] != b["scientific_name"]
                    and ingest.epithets_agree(a["scientific_name"],
                                              b["scientific_name"])):
                again.append((a["scientific_name"], b["scientific_name"]))
ok(not again, "no two rows are one species by the common-name rule",
   f"{len(again)}: {again[:3]}" if again else "")

# 3. No merged name reaches the fits.
syn = list(csv.DictReader(open(os.path.join(HERE, "outputs", "synonyms.csv"),
                               encoding="utf-8")))
gone = {s["merged_name"] for s in syn}
fit = {r["sci"] for r in table
       if r["quality"] != "C" and r["colonial"] != "True"}
back = sorted((gone & fit) | {b for a, b in named_pairs
                              if a in fit and b in fit})
ok(syn and not back, "no merged synonym is in the fits",
   f"{len(gone)} names merged" if not back else f"in the fits: {back[:4]}")

# 4. One family for Sebastes, in the merged table and in the scored table.
fam = {r["family"] for r in rows if r["genus"] == "Sebastes"} | \
      {r["family"] for r in table if r["genus"] == "Sebastes"}
ok(fam == {"Sebastidae"}, "every Sebastes is filed under one family",
   f"families: {sorted(fam)}")

# 4b. D-92 c: one family for every genus, in both tables (a genus is keyed
#     with its class, as ingest.py keys it).
gfam = collections.defaultdict(set)
for r in rows:
    gfam[(r["class"], r["genus"])].add(r["family"])
for r in table:
    gfam[(r["class"], r["genus"])].add(r["family"])
split = sorted(g for g, f in gfam.items() if len(f) > 1)
refiled = list(csv.DictReader(open(os.path.join(HERE, "outputs",
                                                "genus_families.csv"),
                                   encoding="utf-8")))
ok(not split and len(refiled) >= 50,
   "every genus is filed under one family",
   f"{len(gfam):,} genera, {len(refiled)} refiled (outputs/genus_families.csv)"
   if not split else f"split: {split[:4]}")

# 4c. D-92 d: every hand-listed pair is one record under its kept name, and
#     its source says so: for a FishBase pair, the FishBase remark on the
#     merged name names the kept one as its senior synonym.
manual = list(csv.DictReader(open(ingest.SYNONYMS_MANUAL, encoding="utf-8")))
if "--break" in sys.argv and "source" in sys.argv:
    manual.append({"name_a": "Physeter catodon",
                   "name_b": "Physeter macrocephalus",
                   "kept": "Physeter macrocephalus",
                   "source": "FishBase species table, Remark of Physeter "
                             "catodon"})
tnames = {r["sci"] for r in table}
unmerged = []
for m in manual:
    gone_name = m["name_b"] if m["kept"] == m["name_a"] else m["name_a"]
    if (gone_name in names_now or gone_name in tnames
            or m["kept"] not in names_now or m["kept"] not in tnames):
        unmerged.append(gone_name)
ok(manual and not unmerged, "every hand-listed pair is one record, kept name",
   f"{len(manual)} pairs" if not unmerged else f"unmerged: {unmerged}")
import re                                             # noqa: E402
import pandas as pd                                   # noqa: E402
fb = pd.read_parquet(os.path.join(ingest.RAW, "fishbase_species.parquet"))
remark = {f"{g} {sp}": re.sub(r"<[^>]+>", "", str(rm)).lower()
          for g, sp, rm in zip(fb["Genus"], fb["Species"], fb["Remark"])}
unsourced = []
for m in manual:
    gone_name = m["name_b"] if m["kept"] == m["name_a"] else m["name_a"]
    if not m["source"].startswith("FishBase"):
        unsourced.append((gone_name, "no checker for this source"))
    elif not re.search(r"synonym\s+of\s+" + re.escape(m["kept"].lower()),
                       remark.get(gone_name, "")):
        unsourced.append((gone_name, "remark does not say so"))
ok(not unsourced, "each hand-listed pair is stated by the source it cites",
   "every FishBase remark checked" if not unsourced else f"{unsourced}")

# 5. The corrections hold in the output, not only in the code.
olm = merged_by.get("proteus anguinus", {})
olm_t = next((r for r in table if r["sci"] == "Proteus anguinus"), {})
# D-92 a: Voituron et al.'s projection, as AnAge gives it, at grade C, in the
# unrecorded column, with a note that opens by calling it a projection.
ok(olm and olm.get("unknown_yr") == "102" and not olm.get("wild_yr")
   and not olm.get("captive_yr") and olm.get("quality") == "C"
   and olm.get("note", "").startswith("a projection, not an observed age")
   and olm_t.get("quality") == "C",
   "the olm carries the projected maximum, marked and out of the fits",
   f"olm: {olm.get('unknown_yr')} yr, grade {olm.get('quality')}")
cham = merged_by.get("furcifer labordi", {})
ok(cham and float(cham["mass_g"]) == 8.73,
   "Labord's chameleon has the mass AnAge and Amniote record",
   f"{cham.get('mass_g')} g")
wal = [r for r in table if r["sci"] == "Macropus greyi"]
ok(wal and wal[0]["quality"] == "C" and "demoted to C" in wal[0]["note"]
   and "Macropus greyi" in summary["outlier_rule"]["demoted_by_name"],
   "the toolache wallaby is demoted, with its reason",
   wal[0]["note"][:60] if wal else "missing")

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

# A missing value read through pandas is a float NaN, which str() turns into
# the word "nan"; 144 fish carried it as their common name (QA 2026-10-22).
bad = [r["scientific_name"] for r in rows
       if r["common_name"].strip().lower() in ("nan", "none", "null")]
ok(not bad, "no common name is a missing value written out as a word",
   f"{len(bad)}: {bad[:3]}" if bad else "")

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
