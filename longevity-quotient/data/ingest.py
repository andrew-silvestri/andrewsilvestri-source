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
import re
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
          "unknown_yr", "colonial", "quality", "note"]

# Three lifespan columns, not two. wild_yr and captive_yr hold maxima whose
# source says where the record-holder lived. unknown_yr holds a maximum the
# source reports without saying - which is every Amniote, PanTHERIA and
# AmphiBIO figure, every FishBase figure not taken from its LongevityWild
# field, and AnAge rows whose "Specimen origin" is unknown. Until 2026-09-04
# all of those were written into wild_yr, so 63% of what the visualiser drew
# as a wild maximum was nothing of the kind. Captive maxima run longer than
# wild ones, so the mislabelling inflated exactly the quotient the page is
# about. A number the source did not label is not relabelled here either.

def origin_of(r):
    """Which of the three lifespan columns a record fills: 'wild', 'captive',
    'wild+captive', or 'unrecorded' (possibly combined). This is what the
    provenance file and the page report, so the reader can count how much of
    the wild column is actually wild."""
    parts = [k for k, col in (("wild", "wild_yr"), ("captive", "captive_yr"),
                              ("unrecorded", "unknown_yr")) if r.get(col)]
    return "+".join(parts) or "none"


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
        kingdom="Animalia", colonial=False, note="", unknown=None):
    sci = " ".join(str(sci).split())
    # AnAge marks a missing common name with the literal string -999, and two
    # of its names carry stray <b> tags; both reached the visualiser's labels
    # and the download until 2026-09-04. A missing name is an empty string.
    common = re.sub(r"<[^>]+>", "", str(common or "")).strip()
    if common in ("-999", "-999.0", "NA", "null"):
        common = ""
    return dict(source=source, scientific_name=sci, common_name=common,
                kingdom=kingdom, phylum=phylum, class_=cls.strip(),
                order=order.strip(), family=family.strip(),
                genus=(genus or sci.split(" ")[0]).strip(),
                mass_g=mass, wild_yr=wild, captive_yr=captive,
                unknown_yr=unknown,
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
                           r.get("note", ""),
                           unknown=num(r.get("unknown_yr"))))
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
        # Origin unknown (121 rows in build 15) used to be written as wild.
        # It is not wild; it is unrecorded, and it goes in that column.
        unknown = life if (wild is None and cap is None) else None
        grade = ANAGE_GRADE.get((r.get("Data quality") or "").strip().lower(),
                                "C")
        out.append(rec("anage", f"{r['Genus']} {r['Species']}",
                       r.get("Class", ""), r.get("Order", ""),
                       r.get("Family", ""), r.get("Genus", ""),
                       r.get("Common name", ""), mass, wild, cap, grade,
                       r.get("Phylum", "Chordata"),
                       r.get("Kingdom", "Animalia"), unknown=unknown))
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
                           mass, None, None, "B", unknown=life))
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
                           None, None, "B", unknown=months / 12.0))
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
                       num(r.get("Body_mass_g")), None, None, "C",
                       unknown=life))
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

    # LongevityWild is the one FishBase field that says where the fish lived.
    # The per-population tmax fields do not (growth studies include farmed
    # stock), so a maximum taken from them is recorded as origin unrecorded.
    age_wild = {}
    for s, v in zip(sp["SpecCode"], sp.get("LongevityWild")):
        bump(age, s, v)
        bump(age_wild, s, v)
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
        from_wild = age_wild.get(code) == life
        # A missing FBname is a float NaN, which is truthy, so `or ""` let it
        # through as the common name "nan" on 144 fish (QA 2026-10-22).
        fb = r.get("FBname")
        common = "" if fb is None or fb != fb else str(fb).strip()
        out.append(rec("fishbase", f"{g} {s}", cl or "Actinopterygii", o_, f_,
                       g, common, mass,
                       life if from_wild else None, None, "C", note=note,
                       unknown=None if from_wild else life))
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


# ----------------------------------------------------------- corrections ----
# Values a source carries that are not what the column says they are (D-29
# items 4 and 9, D-56 b). Each entry names the source record it changes and
# why; nothing here supplies a figure of its own. A dropped lifespan leaves the
# record in place as a donor of names, taxonomy and mass, so the species takes
# its lifespan from the next source in precedence that has an observed one. A
# dropped mass is refilled from another source of the same species by the
# ordinary gap filling below.
CORRECTIONS = [
    dict(source="seed", sci="Proteus anguinus", drop=("wild_yr", "captive_yr"),
         why="the hand-checked table's 100 years is the projected maximum "
             "of Voituron et al., Biology Letters 7:105, 2011 (about 102 "
             "years), and its 68 is their mean adult lifespan in a "
             "laboratory population; neither is an observed maximum, so the "
             "species takes its lifespan from the next source in precedence "
             "that records one"),
    dict(source="anage", sci="Proteus anguinus", drop=("wild_yr",
                                                       "captive_yr",
                                                       "unknown_yr"),
         why="AnAge's 102 years is the same projection (Voituron et al. "
             "2011), not an observed age"),
    dict(source="seed", sci="Furcifer labordi", drop=("mass_g",),
         why="the hand-checked table's 25 g cites no source; AnAge and "
             "Amniote both give 8.73 g"),
]


def apply_corrections(rows):
    """Apply CORRECTIONS in place; return the notes keyed by binomial."""
    notes, hit = {}, set()
    for c in CORRECTIONS:
        for r in rows:
            if r["source"] == c["source"] and r["scientific_name"] == c["sci"]:
                for f in c["drop"]:
                    r[f] = None
                if "mass_g" in c["drop"]:
                    r["mass_dropped"] = True
                hit.add((c["source"], c["sci"]))
                notes.setdefault(c["sci"].lower(), []).append(c["why"])
    missing = [(c["source"], c["sci"]) for c in CORRECTIONS
               if (c["source"], c["sci"]) not in hit]
    if missing:
        sys.exit(f"corrections that matched no record: {missing}")
    return notes


def has_life(r):
    return any(r.get(k) for k in ("wild_yr", "captive_yr", "unknown_yr"))


# ---------------------------------------------------------- synonym pairs ----
# Six sources, several taxonomies, and a genus that one source has moved and
# another has not: Geochelone sulcata in Amniote is Centrochelys sulcata in
# AnAge. Keyed on the binomial alone, the same tortoise was two records, and
# where both were grade A or B it entered the fits twice (D-29 item 4). Two
# binomials are one species when either of two rules joins them, and the rule
# is applied to the loaded records, not to a list typed here:
#
#   1. same common name and epithet. Both names carry the same common name
#      (case and punctuation aside) in the same class, and their species
#      epithets agree once the Latin gender ending is set aside (sulcata /
#      sulcata, dorsata / dorsatum, fuscus / fusca) or, for epithets of six
#      letters or more, differ by a single letter (sibilatrix / sibillatrix).
#   2. AVONET's crosswalks. AVONET maps every BirdLife species one-to-one onto
#      eBird and BirdTree names where the taxonomies agree; a pair linked by a
#      one-to-one match is one bird under two names (Cacatua / Lophochroa
#      leadbeateri). A match that splits or lumps species is not used.
#
# Neither rule joins two names that one source carries as separate records:
# a source that lists both treats them as two species. The merged record is
# the one the precedence order picks, under that record's own name, and the
# other names are kept in its note and in outputs/synonyms.csv.
CROSSWALK_1TO1 = {"1BL to 1eBird", "1BL to 1eBird*", "1BL to 1BT"}
SYNONYMS_OUT = os.path.join(HERE, "..", "outputs", "synonyms.csv")


def common_key(s):
    s = re.sub(r"[^a-z' ]", " ", str(s or "").lower().replace("’", "'"))
    return " ".join(s.split())


def epithet_stem(sci):
    ep = sci.split(" ")[1].lower() if " " in sci else ""
    for suf in ("ae", "um", "us", "is", "a", "e", "i", "os", "on"):
        if ep.endswith(suf) and len(ep) - len(suf) >= 3:
            return ep[: -len(suf)]
    return ep


def one_letter_apart(a, b):
    """True when two epithets differ by one inserted, dropped or changed
    letter: the spelling variants sibilatrix / sibillatrix, duquesnei /
    duquesnii, melanoramphos / melanorhamphos."""
    if a == b or abs(len(a) - len(b)) > 1:
        return a == b
    if len(a) > len(b):
        a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    return a[i + (len(a) == len(b)):] == b[i + 1:]


def epithets_agree(a, b):
    ea = a.split(" ")[1].lower() if " " in a else ""
    eb = b.split(" ")[1].lower() if " " in b else ""
    return epithet_stem(a) == epithet_stem(b) or (
        min(len(ea), len(eb)) >= 6 and one_letter_apart(ea, eb))


def crosswalk_links():
    """One-to-one name pairs from AVONET's two crosswalk sheets."""
    p = os.path.join(RAW, "avonet.xlsx")
    if not os.path.exists(p):
        return []
    try:
        import pandas as pd
        xl = pd.ExcelFile(p)
    except Exception as e:                              # noqa: BLE001
        print(f"  avonet crosswalk: skipped ({e})")
        return []
    birdlife = {" ".join(str(s).split()) for s in
                pd.read_excel(xl, "AVONET1_BirdLife")["Species1"]}
    out = []
    for sheet in xl.sheet_names:
        if "crosswalk" not in sheet:
            continue
        df = pd.read_excel(xl, sheet)
        other = [c for c in df.columns if c.startswith("Species")
                 and c != "Species1"][0]
        for a, b, mt in zip(df["Species1"], df[other], df["Match.type"]):
            if not (isinstance(a, str) and isinstance(b, str)):
                continue
            a, b = " ".join(a.split()), " ".join(b.split())
            # b must not be a BirdLife species in its own right, or the
            # "one-to-one" row is half of a lump
            if mt in CROSSWALK_1TO1 and a != b and b not in birdlife:
                out.append((a, b, "AVONET " + sheet.split(" ")[0]
                            .replace("�", "-")))
    return out


def synonym_groups(rows, rank):
    """{binomial (lower): accepted binomial (lower)} for every name merged
    into another, and the pairs that joined them."""
    info = {}
    for r in rows:
        n = r["scientific_name"].lower()
        if " " not in n:
            continue
        d = info.setdefault(n, {"sources": set(), "common": set(),
                                "cls": set(), "sci": r["scientific_name"]})
        d["sources"].add(r["source"])
        if r["common_name"]:
            d["common"].add(common_key(r["common_name"]))
        c = r["class_"].strip()
        if c:
            d["cls"].add(CLASS_SYNONYM.get(c, c))

    links = []
    by_common = {}
    for n, d in info.items():
        for c in d["common"]:
            if c:
                by_common.setdefault(c, []).append(n)
    for c, names in by_common.items():
        names = sorted(set(names))
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if (epithets_agree(a, b)
                        and info[a]["cls"] & info[b]["cls"]):
                    links.append((a, b, "same common name and epithet"))
    for a, b, why in crosswalk_links():
        a, b = a.lower(), b.lower()
        if a in info and b in info:
            links.append((a, b, why))

    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            x = parent[x]
        return x

    used = []
    for a, b, why in links:
        if info[a]["sources"] & info[b]["sources"]:
            continue                    # one source lists both: two species
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
        used.append((a, b, why))

    comps = {}
    for n in {x for a, b, _ in used for x in (a, b)}:
        comps.setdefault(find(n), []).append(n)

    def best_rank(n):
        return min(rank[s] for s in info[n]["sources"])

    to = {}
    for members in comps.values():
        acc = min(members, key=lambda n: (best_rank(n), n))
        for n in members:
            if n != acc:
                to[n] = acc
    return to, used, info


# ----------------------------------------------------------------- merge ----
# D-29 item 8: genus Sebastes was filed under Sebastidae by the hand-checked
# table and FishBase and under Scorpaenidae by AnAge, so the rockfishes were
# split across two families and carried the Scorpaenidae figure. A genus
# listed here takes one family for all its species: the family that the
# highest-precedence source filing any member of the genus gives it.
ONE_FAMILY_GENERA = ("Sebastes",)


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

    corrected = apply_corrections(all_rows)

    # one record per species, best source wins
    rank = {s: i for i, s in enumerate(ORDER)}
    syn_to, syn_links, syn_info = synonym_groups(all_rows, rank)
    print(f"  {len(syn_to):,} binomials merged into another as synonyms "
          f"({len(syn_links):,} links)")

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
        n = syn_to.get(n, n)
        if n in seed_dupes and r["source"] == "seed":
            return n + "|" + r["common_name"].lower()
        return n

    best, seen_in = {}, {}
    for r in all_rows:
        k = key_of(r)
        if not k or " " not in k:
            continue
        seen_in.setdefault(k, set()).add(r["source"])
        # A record whose lifespan a correction removed is not a lifespan
        # record; it stays a donor of names, taxonomy and mass.
        if not has_life(r):
            continue
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
                    if r.get("mass_dropped"):
                        r["mass_src"] = s["source"]
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
        base = k.split("|")[0]
        extra = []
        others = sorted(syn_info[n]["sci"] for n, a in syn_to.items()
                        if a == base)
        if others:
            extra.append("also listed as " + ", ".join(others))
        extra += corrected.get(base, [])
        if extra:
            r["note"] = "; ".join(([r["note"]] if r["note"] else []) + extra)
        final.append(r)

    # one family per listed genus, from the highest-precedence source
    regenus = 0
    for g in ONE_FAMILY_GENERA:
        src = sorted((rank[x["source"]], x["family"]) for x in all_rows
                     if x["genus"] == g and x["family"])
        if not src:
            continue
        fam = src[0][1]
        for r in final:
            if r["genus"] == g and r["family"] != fam:
                r["family"] = fam
                regenus += 1
        print(f"  genus {g}: one family, {fam} ({regenus} records refiled)")
    split = {}
    for r in final:
        split.setdefault((r["class_"], r["genus"]), set()).add(r["family"])
    split = sorted(g for g, f in split.items() if len(f) > 1)
    print(f"  {len(split)} other genera are still filed under more than one "
          f"family by their sources (not refiled)")

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

    grades, classes, srcs, origins = {}, {}, {}, {}
    for r in final:
        o = origin_of(r)
        origins[o] = origins.get(o, 0) + 1
        grades[r["quality"]] = grades.get(r["quality"], 0) + 1
        classes[r["class_"] or "?"] = classes.get(r["class_"] or "?", 0) + 1
        srcs[r["source"]] = srcs.get(r["source"], 0) + 1
    print("  grade:  " + "  ".join(f"{k} {v:,}" for k, v in
                                   sorted(grades.items())))
    print("  source: " + "  ".join(f"{k} {v:,}" for k, v in
                                   sorted(srcs.items(), key=lambda kv: -kv[1])))
    print("  origin: " + "  ".join(f"{k} {v:,}" for k, v in
                                   sorted(origins.items(),
                                          key=lambda kv: -kv[1])))
    print("  class:  " + "  ".join(f"{k} {v:,}" for k, v in
                                   sorted(classes.items(),
                                          key=lambda kv: -kv[1])[:10]))

    if not apply:
        print("\n  report only. Re-run with --apply.")
        return final

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
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
                "unknown_yr": (f"{r['unknown_yr']:.6g}"
                               if r.get("unknown_yr") else ""),
                "colonial": "yes" if r["colonial"] else "no",
                "quality": r["quality"],
                "note": r["note"],
            })
    print(f"  wrote {OUT}")

    os.makedirs(os.path.dirname(PROV), exist_ok=True)
    with open(PROV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["scientific_name", "taken_from", "grade",
                    "corroborating_sources", "mass_from", "origin"])
        for r in final:
            w.writerow([r["scientific_name"], r["source"], r["quality"],
                        ";".join(s for s in r["sources"]
                                 if s != r["source"]),
                        r.get("mass_src", r["source"]), origin_of(r)])
    print(f"  wrote {os.path.normpath(PROV)}")

    # Every name merged into another, the rule that joined it, and the record
    # that survived: the list the page's count of merged names is read from.
    kept = {r["scientific_name"].lower(): r for r in final}
    with open(SYNONYMS_OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["merged_name", "kept_as", "rule", "merged_name_sources",
                    "kept_record_source"])
        seen_pair = set()
        for a, b, why in sorted(syn_links):
            for n in (a, b):
                acc = syn_to.get(n)
                if acc is None or (n, acc, why) in seen_pair:
                    continue
                seen_pair.add((n, acc, why))
                w.writerow([syn_info[n]["sci"], syn_info[acc]["sci"], why,
                            ";".join(sorted(syn_info[n]["sources"])),
                            kept[acc]["source"] if acc in kept else ""])
    print(f"  wrote {os.path.normpath(SYNONYMS_OUT)}")

    # The page is generated from this, so what a reader sees under "where the
    # data comes from" is the merge's own accounting rather than a number
    # somebody typed and forgot to update.
    with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({
            "pulled": pulled,
            "kept_by_source": srcs,
            "grades": grades,
            "origins": origins,
            "classes": classes,
            "mass_index": len(masses),
            "species_with_a_lifespan": len(best),
            "mass_filled": filled_mass,
            "mass_modelled_from_length": estimated,
            "dropped_no_mass": dropped_nomass,
            "synonyms_merged": len(syn_to),
            "corrections": [{"source": c["source"], "species": c["sci"],
                             "dropped": list(c["drop"]), "why": c["why"]}
                            for c in CORRECTIONS],
            "one_family_genera": list(ONE_FAMILY_GENERA),
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
