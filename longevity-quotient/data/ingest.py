"""
Merge every trait database that carries a lifespan into one table.

The model needs two numbers per species: an adult body mass and a maximum
observed lifespan. Mass is easy and lifespan is not, and that asymmetry decides
the shape of this file. There are body-mass databases with tens of thousands of
species in them. There is no lifespan database with tens of thousands of
species in it, because a maximum lifespan requires somebody to have watched an
animal until it died, and for most of the 2.24 million described species
nobody has.

So the sources fall into two roles:

  LIFESPAN SOURCES set the size of the final table. Every species here starts
  as a record in one of them.

  MASS SOURCES only fill gaps. A species with a lifespan and no mass is
  useless to an allometry; a species with a mass and no lifespan is not a
  record at all. AVONET's eleven thousand birds add nothing except where a bird
  already has a lifespan and is missing a weight.

Precedence, highest first. A species found in several sources takes its numbers
from the best one and records the rest as corroboration rather than averaging
them, because averaging a careful record with a careless one produces a number
that belongs to neither.

  1. the hand-checked seed table          verified individually
  2. AnAge                                curated from primary literature
  3. the Amniote life-history database    peer-reviewed compilation
  4. PanTHERIA / AmphiBIO / FishBase      compilations, class-specific

Grades follow that order and drive the regression weights. AnAge carries its
own quality field and it is honoured rather than overridden.

Run:  python3 ingest.py            report only
      python3 ingest.py --apply    write animals_merged.csv
"""

import argparse
import csv
import json
import io
import math
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
SEED = os.path.join(HERE, "animals.csv")
OUT = os.path.join(HERE, "animals_merged.csv")
PROV = os.path.join(HERE, "..", "outputs", "provenance.csv")
REPORT = os.path.join(HERE, "..", "outputs", "ingest_report.json")

FIELDS = ["common_name", "scientific_name", "kingdom", "phylum", "class",
          "order", "family", "genus", "mass_g", "wild_yr", "captive_yr",
          "colonial", "quality", "note"]

# Highest precedence first. The index is the tie-break.
ORDER = ["seed", "anage", "amniote", "pantheria", "amphibio", "fishbase"]

# Six sources, six taxonomies, all of them defensible. Folded here rather than
# at read time, because the merged table is itself a published artefact - it
# ships in the download - and a file that calls the same class Teleostei in one
# row and Actinopterygii in the next is a file that will be split into two
# groups by whoever reads it next.
try:
    sys.path.insert(0, os.path.dirname(HERE))
    from build_lq import CLASS_SYNONYM, ORDER_SYNONYM
except Exception:                                        # noqa: BLE001
    CLASS_SYNONYM, ORDER_SYNONYM = {}, {}

CITATION = {
    "seed": "Hand-checked records, sourced individually on the page.",
    "anage": "Tacutu et al., Nucleic Acids Research 46:D1083, 2018. "
             "AnAge build 15.",
    "amniote": "Myhrvold et al., Ecology 96:3109, 2015. Amniote "
               "life-history database.",
    "pantheria": "Jones et al., Ecology 90:2648, 2009. PanTHERIA.",
    "amphibio": "Oliveira et al., Scientific Data 4:170123, 2017. AmphiBIO.",
    "fishbase": "Froese & Pauly, FishBase, v25.04 snapshot. CC BY-NC.",
    "avonet": "Tobias et al., Ecology Letters 25:581, 2022. AVONET "
              "(body mass only).",
}


def num(v):
    """A number, or None. Every one of these files marks 'no value' its own
    way, and -999 read as a mass is the kind of thing that quietly bends a
    regression rather than crashing it."""
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        if v in ("", "NA", "na", "NaN", "-999", "-999.0", "null", "."):
            return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f) or f <= 0 or f == -999:
        return None
    return f


def rec(source, sci, cls="", order="", family="", genus="", common="",
        mass=None, wild=None, captive=None, quality="C", phylum="Chordata",
        kingdom="Animalia", colonial=False, note=""):
    sci = " ".join(str(sci).split())
    return dict(source=source, scientific_name=sci, common_name=common or "",
                kingdom=kingdom, phylum=phylum, class_=cls.strip(),
                order=order.strip(), family=family.strip(),
                genus=(genus or sci.split(" ")[0]).strip(),
                mass_g=mass, wild_yr=wild, captive_yr=captive,
                quality=quality, colonial=colonial, note=note)


# ------------------------------------------------------------------ seed ----
def load_seed():
    out = []
    with open(SEED, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out.append(rec("seed", r["scientific_name"], r["class"],
                           r["order"], r["family"], r["genus"],
                           r["common_name"], num(r["mass_g"]),
                           num(r["wild_yr"]), num(r["captive_yr"]),
                           r["quality"], r["phylum"], r["kingdom"],
                           r.get("colonial", "no").strip().lower() == "yes",
                           r.get("note", "")))
    return out


# ----------------------------------------------------------------- AnAge ----
# AnAge grades its own records and that grading is better informed than
# anything this file could infer. 'high' means the maximum is from a verified
# individual; 'questionable' means the source is a secondary compilation.
ANAGE_GRADE = {"high": "A", "acceptable": "B", "questionable": "C",
               "low": "C"}


def load_anage():
    src = None
    for name in ("anage_data.txt", "anage_dataset.zip"):
        p = os.path.join(RAW, name)
        if not os.path.exists(p):
            continue
        if name.endswith(".zip"):
            with zipfile.ZipFile(p) as z:
                m = [n for n in z.namelist()
                     if n.lower().endswith(".txt") and "anage" in n.lower()]
                if m:
                    src = z.read(m[0]).decode("utf-8", "replace")
        else:
            src = open(p, encoding="utf-8", errors="replace").read()
        break
    if src is None:
        return []

    out = []
    for r in csv.DictReader(io.StringIO(src), delimiter="\t"):
        life = num(r.get("Maximum longevity (yrs)"))
        if life is None:
            continue
        # 'Adult weight (g)' is the life-history field and is well populated;
        # 'Body mass (g)' belongs to the metabolic-rate block and is sparse.
        # Reading the wrong one costs about four thousand species.
        mass = num(r.get("Adult weight (g)")) or num(r.get("Body mass (g)"))
        origin = (r.get("Specimen origin") or "").strip().lower()
        wild = life if origin == "wild" else None
        cap = life if origin in ("captivity", "captive") else None
        if wild is None and cap is None:      # origin unknown or 'unknown'
            wild = life
        grade = ANAGE_GRADE.get((r.get("Data quality") or "").strip().lower(),
                                "C")
        out.append(rec("anage", f"{r['Genus']} {r['Species']}",
                       r.get("Class", ""), r.get("Order", ""),
                       r.get("Family", ""), r.get("Genus", ""),
                       r.get("Common name", ""), mass, wild, cap, grade,
                       r.get("Phylum", "Chordata"),
                       r.get("Kingdom", "Animalia")))
    return out


# --------------------------------------------------------------- amniote ----
def load_amniote():
    p = os.path.join(RAW, "amniote.csv")
    if not os.path.exists(p):
        return []
    out = []
    with open(p, newline="", encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            life = num(r.get("maximum_longevity_y"))
            if life is None:
                continue
            mass = (num(r.get("adult_body_mass_g"))
                    or num(r.get("female_body_mass_g"))
                    or num(r.get("male_body_mass_g"))
                    or num(r.get("no_sex_body_mass_g")))
            sp = (r.get("species") or "").strip()
            if not sp or sp.lower() in ("sp.", "sp"):
                continue
            out.append(rec("amniote", f"{r['genus']} {sp}", r.get("class", ""),
                           r.get("order", ""), r.get("family", ""),
                           r.get("genus", ""), r.get("common_name", ""),
                           mass, life, None, "B"))
    return out


# ------------------------------------------------------------- PanTHERIA ----
def load_pantheria():
    p = os.path.join(RAW, "pantheria.txt")
    if not os.path.exists(p):
        return []
    out = []
    with open(p, newline="", encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            months = num(r.get("17-1_MaxLongevity_m"))
            if months is None:
                continue
            out.append(rec("pantheria", r.get("MSW05_Binomial", ""),
                           "Mammalia", r.get("MSW05_Order", ""),
                           r.get("MSW05_Family", ""),
                           r.get("MSW05_Genus", ""), "",
                           num(r.get("5-1_AdultBodyMass_g")),
                           months / 12.0, None, "B"))
    return out


# -------------------------------------------------------------- AmphiBIO ----
def load_amphibio():
    p = os.path.join(RAW, "amphibio.zip")
    if not os.path.exists(p):
        return []
    with zipfile.ZipFile(p) as z:
        name = [n for n in z.namelist() if n.endswith("AmphiBIO_v1.csv")]
        if not name:
            return []
        txt = z.read(name[0]).decode("latin-1")
    out = []
    for r in csv.DictReader(io.StringIO(txt)):
        life = num(r.get("Longevity_max_y"))
        if life is None:
            continue
        out.append(rec("amphibio", r.get("Species", ""), "Amphibia",
                       r.get("Order", ""), r.get("Family", ""), "", "",
                       num(r.get("Body_mass_g")), life, None, "C"))
    return out


# -------------------------------------------------------------- FishBase ----
def load_fishbase():
    """FishBase keeps maximum age in three places and they disagree.

    The species table has a curated LongevityWild. popchar holds per-population
    maxima recorded with the specimen. popgrowth holds the tmax used to fit
    growth curves. The largest of the three is taken, because every one of them
    is a maximum and the largest verified maximum is the quantity the model
    wants - but the whole class is graded C, because a fish aged by counting
    rings on a scale and a Greenland shark aged by radiocarbon in its eye lens
    are not the same measurement and should not carry the same weight.
    """
    try:
        import pandas as pd
    except ImportError:
        print("  fishbase: pandas not available, skipped")
        return []
    sp_p = os.path.join(RAW, "fishbase_species.parquet")
    if not os.path.exists(sp_p):
        return []
    sp = pd.read_parquet(sp_p)

    age, wt = {}, {}

    def bump(d, k, v):
        v = num(v)
        if v is not None and (k not in d or v > d[k]):
            d[k] = v

    for p, code, cols in (
            ("fishbase_popchar.parquet", "Speccode", ("tmax", "Wmax")),
            ("fishbase_popgrowth.parquet", "Speccode", ("tmax", None))):
        path = os.path.join(RAW, p)
        if not os.path.exists(path):
            continue
        df = pd.read_parquet(path)
        if code not in df.columns:
            continue
        acol, wcol = cols
        if acol in df.columns:
            for s, v in zip(df[code], df[acol]):
                bump(age, s, v)
        if wcol and wcol in df.columns:
            for s, v in zip(df[code], df[wcol]):
                bump(wt, s, v)

    for s, v in zip(sp["SpecCode"], sp.get("LongevityWild")):
        bump(age, s, v)
    for s, v in zip(sp["SpecCode"], sp.get("Weight")):
        bump(wt, s, v)

    # Taxonomy. The species table carries only a family code; without the
    # family table every fish arrives with a blank order, and a blank order is
    # a group of six hundred species called "" sitting at the top of the
    # rank comparison.
    fam = {}
    fp = os.path.join(RAW, "fishbase_families.parquet")
    if os.path.exists(fp):
        fdf = pd.read_parquet(fp)
        for c, f_, o_, cl in zip(fdf["FamCode"], fdf["Family"], fdf["Order"],
                                 fdf["Class"]):
            fam[c] = (str(f_ or "").strip(), str(o_ or "").strip(),
                      str(cl or "").strip())

    # Length-weight coefficients, for the thousand fish that have been aged
    # but never weighed. FishBase publishes W = a * L^b per species with L in
    # centimetres and W in grams; using it recovers those species at the cost
    # of a modelled mass rather than a measured one. They are marked as such
    # and graded C, so they populate the table without steering the fit.
    lw = {}
    ep = os.path.join(RAW, "fishbase_estimate.parquet")
    if os.path.exists(ep):
        edf = pd.read_parquet(ep)
        for c, a_, b_, L in zip(edf["SpecCode"], edf["a"], edf["b"],
                                edf["MaxLengthTL"]):
            a_, b_, L = num(a_), num(b_), num(L)
            if a_ and b_ and L:
                lw[c] = a_ * (L ** b_)

    out = []
    for _, r in sp.iterrows():
        code = r["SpecCode"]
        life = age.get(code)
        if life is None:
            continue
        g, s = str(r.get("Genus", "")).strip(), str(r.get("Species", "")).strip()
        if not g or not s:
            continue
        mass, note = wt.get(code), ""
        if mass is None and code in lw:
            mass = lw[code]
            note = ("mass estimated from maximum length by FishBase's "
                    "length-weight relationship, not weighed")
        f_, o_, cl = fam.get(r.get("FamCode"), ("", "", "Actinopterygii"))
        out.append(rec("fishbase", f"{g} {s}", cl or "Actinopterygii", o_, f_,
                       g, str(r.get("FBname") or "").strip(), mass, life,
                       None, "C", note=note))
    return out


# ------------------------------------------------- mass-only gap fillers ----
def mass_index():
    """Species -> body mass, from sources that carry no lifespan.

    These never create a record. They only rescue one that has a lifespan and
    is missing its mass, which is otherwise a species thrown away for the lack
    of a number somebody else already measured.
    """
    idx = {}

    def put(sci, m, src):
        m = num(m)
        sci = " ".join(str(sci).split())
        if m and sci and sci not in idx:
            idx[sci] = (m, src)

    p = os.path.join(RAW, "avonet.xlsx")
    if os.path.exists(p):
        try:
            import pandas as pd
            av = pd.read_excel(p, sheet_name="AVONET1_BirdLife")
            sc = "Species1" if "Species1" in av.columns else av.columns[0]
            for s, m in zip(av[sc], av["Mass"]):
                put(s, m, "avonet")
        except Exception as e:                      # noqa: BLE001
            print(f"  avonet: skipped ({e})")

    for r in load_pantheria():
        put(r["scientific_name"], r["mass_g"], "pantheria")
    for r in load_amniote():
        put(r["scientific_name"], r["mass_g"], "amniote")
    return idx


# ----------------------------------------------------------------- merge ----
def merge(apply=False):
    loaders = [("seed", load_seed), ("anage", load_anage),
               ("amniote", load_amniote), ("pantheria", load_pantheria),
               ("amphibio", load_amphibio), ("fishbase", load_fishbase)]

    pulled, all_rows = {}, []
    for name, fn in loaders:
        rows = fn()
        pulled[name] = len(rows)
        all_rows += rows
        print(f"  {name:10s} {len(rows):7,} records with a lifespan")

    masses = mass_index()
    print(f"  {'mass index':10s} {len(masses):7,} species with a body mass "
          f"(gap filling only)")

    # one record per species, best source wins
    rank = {s: i for i, s in enumerate(ORDER)}

    # A binomial is not always one record. The seed carries a honey bee worker
    # and a honey bee queen: same genome, same species name, lifespans a factor
    # of thirty apart, and the contrast between them is one of the more
    # interesting things in the table. Keying on the binomial alone silently
    # ate one of the two. Where the seed deliberately holds several rows for a
    # species, each keeps its own identity and the bulk sources merge into the
    # first of them.
    seed_dupes = set()
    seen_seed = set()
    for r in all_rows:
        if r["source"] != "seed":
            continue
        n = r["scientific_name"].lower()
        if n in seen_seed:
            seed_dupes.add(n)
        seen_seed.add(n)

    def key_of(r):
        n = r["scientific_name"].lower()
        if n in seed_dupes and r["source"] == "seed":
            return n + "|" + r["common_name"].lower()
        return n

    best, seen_in = {}, {}
    for r in all_rows:
        k = key_of(r)
        if not k or " " not in k:
            continue
        seen_in.setdefault(k, set()).add(r["source"])
        cur = best.get(k)
        if cur is None or rank[r["source"]] < rank[cur["source"]]:
            best[k] = r

    # fill the gaps: taxonomy from any source that has it, mass from anywhere
    by_species = {}
    for r in all_rows:
        by_species.setdefault(key_of(r), []).append(r)

    filled_mass, filled_tax, dropped_nomass, estimated = 0, 0, 0, 0
    final = []
    for k, r in best.items():
        sibs = by_species[k]
        for field in ("class_", "order", "family", "genus", "common_name",
                      "phylum"):
            if not r[field]:
                for s in sibs:
                    if s[field]:
                        r[field] = s[field]
                        filled_tax += 1
                        break
        if r["mass_g"] is None:
            for s in sibs:
                if s["mass_g"]:
                    r["mass_g"] = s["mass_g"]
                    filled_mass += 1
                    break
        if r["mass_g"] is None:
            hit = masses.get(r["scientific_name"])
            if hit:
                r["mass_g"] = hit[0]
                r["mass_src"] = hit[1]
                filled_mass += 1
        if r["mass_g"] is None:
            dropped_nomass += 1
            continue
        if "estimated from maximum length" in (r["note"] or ""):
            estimated += 1
        r["sources"] = sorted(seen_in[k])
        final.append(r)

    renamed = 0
    for r in final:
        if r["class_"] in CLASS_SYNONYM:
            r["class_"] = CLASS_SYNONYM[r["class_"]]
            renamed += 1
        if r["order"] in ORDER_SYNONYM:
            r["order"] = ORDER_SYNONYM[r["order"]]
            renamed += 1
    if renamed:
        print(f"  {renamed:,} taxon names folded onto the canonical set")

    final.sort(key=lambda r: (r["class_"], r["scientific_name"]))

    print(f"\n  {len(best):,} distinct species carried a lifespan")
    print(f"  {filled_mass:,} had their mass filled from another source")
    print(f"  {filled_tax:,} taxonomy fields filled from another source")
    print(f"  {estimated:,} carry a mass modelled from length, not weighed")
    print(f"  {dropped_nomass:,} dropped: a lifespan but no mass anywhere")
    print(f"  {len(final):,} species in the merged table\n")

    grades, classes, srcs = {}, {}, {}
    for r in final:
        grades[r["quality"]] = grades.get(r["quality"], 0) + 1
        classes[r["class_"] or "?"] = classes.get(r["class_"] or "?", 0) + 1
        srcs[r["source"]] = srcs.get(r["source"], 0) + 1
    print("  grade:  " + "  ".join(f"{k} {v:,}" for k, v in
                                   sorted(grades.items())))
    print("  source: " + "  ".join(f"{k} {v:,}" for k, v in
                                   sorted(srcs.items(), key=lambda kv: -kv[1])))
    print("  class:  " + "  ".join(f"{k} {v:,}" for k, v in
                                   sorted(classes.items(),
                                          key=lambda kv: -kv[1])[:10]))

    if not apply:
        print("\n  report only. Re-run with --apply.")
        return final

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in final:
            w.writerow({
                "common_name": r["common_name"] or r["scientific_name"],
                "scientific_name": r["scientific_name"],
                "kingdom": r["kingdom"] or "Animalia",
                "phylum": r["phylum"] or "Chordata",
                "class": r["class_"], "order": r["order"],
                "family": r["family"], "genus": r["genus"],
                "mass_g": f"{r['mass_g']:.6g}",
                "wild_yr": f"{r['wild_yr']:.6g}" if r["wild_yr"] else "",
                "captive_yr": (f"{r['captive_yr']:.6g}"
                               if r["captive_yr"] else ""),
                "colonial": "yes" if r["colonial"] else "no",
                "quality": r["quality"],
                "note": r["note"],
            })
    print(f"  wrote {OUT}")

    os.makedirs(os.path.dirname(PROV), exist_ok=True)
    with open(PROV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["scientific_name", "taken_from", "grade",
                    "corroborating_sources", "mass_from"])
        for r in final:
            w.writerow([r["scientific_name"], r["source"], r["quality"],
                        ";".join(s for s in r["sources"]
                                 if s != r["source"]),
                        r.get("mass_src", r["source"])])
    print(f"  wrote {os.path.normpath(PROV)}")

    # The page is generated from this, so what a reader sees under "where the
    # data comes from" is the merge's own accounting rather than a number
    # somebody typed and forgot to update.
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump({
            "pulled": pulled,
            "kept_by_source": srcs,
            "grades": grades,
            "classes": classes,
            "mass_index": len(masses),
            "species_with_a_lifespan": len(best),
            "mass_filled": filled_mass,
            "mass_modelled_from_length": estimated,
            "dropped_no_mass": dropped_nomass,
            "final": len(final),
            "citations": CITATION,
        }, fh, indent=2)
    print(f"  wrote {os.path.normpath(REPORT)}")
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not os.path.isdir(RAW):
        sys.exit(f"no raw/ directory at {RAW}")
    merge(a.apply)
