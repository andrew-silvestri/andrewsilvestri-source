"""
Rebuild animals.csv from the AnAge database.

The curated animals.csv in this folder was compiled by hand because the
sandbox this project was built in cannot reach genomics.senescence.info. Your
own connection can. AnAge is the reference source for comparative longevity:
roughly 4,200 species with maximum longevity, adult body mass, and a data
quality grade already attached.

    1. Download https://genomics.senescence.info/species/dataset.zip into
       this folder. On Windows PowerShell, curl is an alias for
       Invoke-WebRequest and does not take curl's flags:

           Invoke-WebRequest https://genomics.senescence.info/species/dataset.zip -OutFile dataset.zip

       On macOS or Linux:

           curl -LO https://genomics.senescence.info/species/dataset.zip

    2. python3 load_anage.py

There is no unzip step; this script extracts anage_data.txt from dataset.zip
itself if it has not already been extracted.

Writes animals_anage.csv. Inspect it, then either point build_lq.py at it or
merge the rows you want into animals.csv.

Two schema details matter, and both are easy to get wrong.

**Mass.** AnAge carries two mass columns. `Body mass (g)` is the mass recorded
alongside a metabolic rate measurement and is blank for most species.
`Adult weight (g)` is the general adult mass and is populated far more widely.
This loader prefers Adult weight and falls back to Body mass. Reading only
`Body mass (g)` silently discards the large majority of the database.

**Wild against captive.** AnAge records one longevity figure per species, but it
also carries a `Specimen origin` column saying whether that record holder was
wild or captive. This loader routes the longevity into wild_yr or captive_yr on
that basis rather than assuming captivity. Records of unknown origin go to
captive_yr, since that is the conventional reading, and are marked in the note.

Even so, each species gets one number, not two. AnAge cannot give you a wild
figure and a captive figure for the same species, which is the comparison the
visualiser is built around; the paired values in the curated animals.csv came
from field studies, banding returns and mark-recapture work, species by species.
So rebuilding wholesale buys breadth and costs you the pairing. Merging — taking
AnAge's breadth and keeping the hand-checked pairs where they exist — is the
better move.
"""

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "anage_data.txt")
DST = os.path.join(HERE, "animals_anage.csv")

# AnAge quality grades mapped onto the grades used by this project.
QUALITY = {
    "acceptable": "A",
    "high": "A",
    "questionable": "C",
    "low": "C",
}

# AnAge's "Data quality" field records whether the *record* was verified. It
# says nothing about how many animals were watched. Those are different
# questions, and conflating them is what puts a Bassian thrush at four per cent
# of its predicted lifespan: one banded bird, correctly recorded, and utterly
# unrepresentative.
#
# Maximum longevity is an extreme-value statistic. Its expected value rises with
# the number of individuals observed, so a species followed by three people looks
# short-lived and a species followed by three thousand looks long-lived, with no
# biology involved. AnAge's "Sample size" field is the only handle on this, and
# a tiny or small sample is demoted to grade C so that build_lq.py keeps it out
# of the regressions while still displaying it.
SAMPLE_DEMOTE = {"tiny", "small"}


def find_source():
    """Locate anage_data.txt, extracting it from dataset.zip if needed.

    Saves the caller from having to unzip by hand, which on Windows means
    Expand-Archive rather than unzip and is an easy place to lose ten minutes.
    """
    if os.path.exists(SRC):
        return SRC

    zpath = os.path.join(HERE, "dataset.zip")
    if os.path.exists(zpath):
        import zipfile
        with zipfile.ZipFile(zpath) as zf:
            members = [n for n in zf.namelist()
                       if n.lower().endswith(".txt") and "anage" in n.lower()]
            if not members:
                members = [n for n in zf.namelist()
                           if n.lower().endswith(".txt")]
            if not members:
                raise SystemExit(
                    f"{zpath} contains no .txt file. Contents: "
                    + ", ".join(zf.namelist()[:10])
                )
            member = members[0]
            with zf.open(member) as src, open(SRC, "wb") as dst:
                dst.write(src.read())
            print(f"extracted {member} from dataset.zip")
        return SRC

    raise SystemExit(
        "Neither anage_data.txt nor dataset.zip found in this folder.\n\n"
        "Download the dataset first, then run this script again.\n"
        "  PowerShell:  Invoke-WebRequest "
        "https://genomics.senescence.info/species/dataset.zip "
        "-OutFile dataset.zip\n"
        "  macOS/Linux: curl -LO "
        "https://genomics.senescence.info/species/dataset.zip\n\n"
        "No need to unzip it; this script will do that itself."
    )


def main():
    find_source()

    kept, skipped, origins, samples, demoted = [], 0, {}, {}, 0
    with open(SRC, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            # Adult weight is populated far more widely than Body mass, which
            # is only recorded where a metabolic rate was also measured.
            mass = (row.get("Adult weight (g)") or "").strip() \
                or (row.get("Body mass (g)") or "").strip()
            life = (row.get("Maximum longevity (yrs)") or "").strip()
            if not mass or not life:
                skipped += 1
                continue
            try:
                mass_g, life_y = float(mass), float(life)
            except ValueError:
                skipped += 1
                continue
            if mass_g <= 0 or life_y <= 0:
                skipped += 1
                continue

            origin = (row.get("Specimen origin") or "").strip().lower()
            origins[origin or "(blank)"] = origins.get(origin or "(blank)", 0) + 1
            if "wild" in origin:
                wild_yr, captive_yr = life_y, ""
                note = "AnAge; record holder was wild"
            elif "captiv" in origin:
                wild_yr, captive_yr = "", life_y
                note = "AnAge; record holder was captive"
            else:
                wild_yr, captive_yr = "", life_y
                note = "AnAge; specimen origin not stated, assumed captive"

            grade = QUALITY.get(
                (row.get("Data quality") or "").strip().lower(), "B")
            sample = (row.get("Sample size") or "").strip().lower()
            samples[sample or "(blank)"] = samples.get(sample or "(blank)", 0) + 1
            if sample in SAMPLE_DEMOTE and grade != "C":
                grade = "C"
                demoted += 1
                note += "; sample size " + sample

            common = (row.get("Common name") or "").strip()
            genus = (row.get("Genus") or "").strip()
            species = (row.get("Species") or "").strip()
            kept.append({
                "common_name": common or f"{genus} {species}".strip(),
                "scientific_name": f"{genus} {species}".strip(),
                # AnAge carries the full hierarchy, so a merged table keeps
                # every rank the visualiser groups by.
                "kingdom": (row.get("Kingdom") or "Animalia").strip(),
                "phylum": (row.get("Phylum") or "").strip(),
                "class": (row.get("Class") or "").strip(),
                "order": (row.get("Order") or "").strip(),
                "family": (row.get("Family") or "").strip(),
                "genus": genus,
                "mass_g": mass_g,
                "wild_yr": wild_yr,
                "captive_yr": captive_yr,
                "colonial": "no",
                "quality": grade,
                "note": note,
            })

    cols = ["common_name", "scientific_name", "kingdom", "phylum", "class",
            "order", "family", "genus", "mass_g", "wild_yr", "captive_yr",
            "colonial", "quality", "note"]
    with open(DST, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(kept)

    print(f"{len(kept)} species written to {DST}")
    print(f"{skipped} rows skipped for missing mass or longevity")

    print("\nby class:")
    by_class = {}
    for r in kept:
        by_class[r["class"]] = by_class.get(r["class"], 0) + 1
    for k in sorted(by_class, key=lambda k: -by_class[k])[:12]:
        print(f"  {k or '(unclassified)':22s} {by_class[k]}")

    print("\nby sample size:")
    for k in sorted(samples, key=lambda k: -samples[k]):
        mark = "  -> demoted to grade C" if k in SAMPLE_DEMOTE else ""
        print(f"  {k:22s} {samples[k]}{mark}")
    print(f"\n{demoted} records demoted for small sample size. Maximum "
          f"longevity is an extreme-value statistic:\nit rises with how many "
          f"animals were watched, so a thinly-sampled species looks\n"
          f"short-lived for reasons that have nothing to do with ageing.")

    print("\nby specimen origin:")
    for k in sorted(origins, key=lambda k: -origins[k]):
        print(f"  {k:22s} {origins[k]}")
    n_wild = sum(1 for r in kept if r["wild_yr"])
    print(f"\n{n_wild} species carry a wild record, "
          f"{len(kept) - n_wild} a captive or unstated one.")

    # How much of the curated table AnAge can corroborate.
    cur = os.path.join(HERE, "animals.csv")
    if os.path.exists(cur):
        with open(cur, newline="", encoding="utf-8") as fh:
            mine = {r["scientific_name"].strip().lower()
                    for r in csv.DictReader(fh)}
        theirs = {r["scientific_name"].strip().lower() for r in kept}
        both = mine & theirs
        print(f"\n{len(both)} of the {len(mine)} curated species also appear "
              f"in AnAge; {len(mine - theirs)} do not.")
        if mine - theirs:
            print("  absent from AnAge: "
                  + ", ".join(sorted(mine - theirs)[:8])
                  + (" …" if len(mine - theirs) > 8 else ""))


if __name__ == "__main__":
    main()
