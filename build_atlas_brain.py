"""
Give the behavior layer measured inputs.

The behavior layer had 24 channels and no way in. Nothing fed them; they only
fed 1,142 consumer groups. So a run could push behavior out into the world and
nothing in the world could ever push back on behavior, and every district was
coupled to it identically. That is the part worth fixing.

What is measured here, from GeoNames cities15000 (34,068 settlements above
fifteen thousand people, with coordinates, population and first-level
administrative code):

    population of each first-level administrative area
    concentration of that population, as a Herfindahl index over its
      settlements: 1.0 means one city holds everyone, small means the
      population is spread across many towns

Most of the atlas districts are real GeoNames admin-1 divisions carrying their
own name and country code. Those are joined to the settlement data on their
administrative code, which is an exact join and not a spatial guess. The
remainder are synthetic fillers for countries where the original build could
not resolve real divisions; they get no population and no behavior link,
because inventing one is the thing this file exists to avoid.

WHAT IS NOT HERE, AND WHY.

The request was to weight each district's behavior by the value set of its
voting bloc. I did not build that, because the data to build it honestly does
not exist. The World Values Survey and European Values Study measure the two
Inglehart-Welzel dimensions at national level for roughly 120 countries.
Subnational value data exists for a handful of countries and not at the
resolution of a United States congressional or state district. Assigning a
value set to a district would mean interpolating national averages onto
geography and presenting the result as measurement, which is the one thing this
project does not do. The concentration figure below is a population statistic
and is not a claim about anyone's politics.

One modelling choice IS made and is flagged rather than hidden: concentration
is used as the coupling strength between a district and the behavior layer.
That a more concentrated population couples more strongly to shared behavior
is a hypothesis, not a measurement. It is marked assumed in the provenance,
alongside the consumer-response values.

Run:  python3 build_atlas_brain.py            report only
      python3 build_atlas_brain.py --apply
"""

import argparse
import collections
import io
import json
import math
import os
import re
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "assets", "atlas-data.js")
RAW = os.path.join(HERE, "..", "19 Atlas v6", "raw")


def haversine(a1, o1, a2, o2):
    r = math.pi / 180.0
    dla = (a2 - a1) * r
    dlo = (o2 - o1) * r
    h = (math.sin(dla / 2) ** 2
         + math.cos(a1 * r) * math.cos(a2 * r) * math.sin(dlo / 2) ** 2)
    return 6371.0 * 2 * math.asin(min(1.0, math.sqrt(h)))


def iso2_to_iso3():
    m = {}
    with open(os.path.join(RAW, "countryInfo.txt"), encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) > 1 and f[0] and f[1]:
                m[f[0]] = f[1]
    return m


def admin_areas():
    """
    Real first-level administrative areas, with the population, centroid and
    concentration of the settlements GeoNames records inside each.
    """
    iso3 = iso2_to_iso3()
    z = zipfile.ZipFile(os.path.join(RAW, "cities15000.zip"))
    name = z.namelist()[0]
    by = collections.defaultdict(list)
    for line in io.TextIOWrapper(z.open(name), encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        if len(f) < 15:
            continue
        try:
            pop = int(f[14])
            la, lo = float(f[4]), float(f[5])
        except ValueError:
            continue
        cc, a1 = f[8], f[10]
        if not cc or not a1 or pop <= 0:
            continue
        by[(iso3.get(cc, cc), a1)].append((la, lo, pop))

    out = {}
    for key, cities in by.items():
        tot = sum(c[2] for c in cities)
        if tot <= 0:
            continue
        clat = sum(c[0] * c[2] for c in cities) / tot
        clon = sum(c[1] * c[2] for c in cities) / tot
        herf = sum((c[2] / tot) ** 2 for c in cities)
        out[key] = dict(pop=tot, lat=clat, lon=clon, herf=herf,
                        n=len(cities))
    return out


def load():
    raw = open(DATA, encoding="utf-8").read()
    return raw[:raw.index("=") + 1], json.loads(
        raw[raw.index("=") + 1:raw.rindex(";")])


def main(apply=False):
    head, D = load()
    kinds = D["kinds"]
    kind = [kinds[k] for k in D["kind"]]
    n0, e0 = D["n"], len(D["es"])

    areas = admin_areas()
    print(f"  {len(areas):,} real administrative areas with settlement data, "
          f"{sum(a['pop'] for a in areas.values()):,} people")

    # index the areas by country so a district only matches inside its own
    by_iso = collections.defaultdict(list)
    for (iso, a1), a in areas.items():
        by_iso[iso].append((a1, a))

    districts = [i for i, k in enumerate(kind) if k == "district"]
    psych = [i for i, k in enumerate(kind) if k == "psych"]
    print(f"  {len(districts):,} districts in the model, "
          f"{len(psych)} behavior channels")

    srcd = D["srcDict"]

    def src_id(s):
        if s not in srcd:
            srcd.append(s)
        return srcd.index(s)

    # The districts are of two sorts. 2,761 are real GeoNames admin-1
    # divisions and carry their own name and country code -- "Dubai (AE)".
    # The rest are synthetic fillers, "USA district 3", for countries where
    # the build could not resolve real divisions.
    #
    # A first version of this matched every district to the nearest area
    # centroid inside its country. It matched 565 of 3,332 and the worst match
    # was 1,234 km away, which is not a match, it is a guess with a number
    # attached. The named districts do not need guessing: admin1CodesASCII.txt
    # maps a division name and country to its code, and the code is the key
    # the settlement data is already grouped by. Exact join, or nothing.
    a1_by_name = {}
    with open(os.path.join(RAW, "admin1CodesASCII.txt"), encoding="utf-8") as fh:
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) < 2:
                continue
            code = f[0]                      # e.g. "AE.03"
            if "." not in code:
                continue
            cc, a1 = code.split(".", 1)
            a1_by_name[(cc, f[1].strip().lower())] = a1
            if len(f) > 2 and f[2].strip():
                a1_by_name.setdefault((cc, f[2].strip().lower()), a1)

    iso3 = iso2_to_iso3()
    matched, exact, synthetic, unmatched = {}, 0, 0, 0
    for di in districts:
        nm = D["name"][di]
        m = re.match(r"^(.*) \(([A-Z]{2})\)$", nm)
        if m:
            cc = m.group(2)
            a1 = a1_by_name.get((cc, m.group(1).strip().lower()))
            a = areas.get((iso3.get(cc, cc), a1)) if a1 else None
            if a:
                matched[di] = (a1, a)
                exact += 1
            else:
                unmatched += 1
            continue
        synthetic += 1

    print(f"  named districts joined on their administrative code: {exact:,}")
    print(f"  named districts with no settlement data: {unmatched:,}")
    print(f"  synthetic districts, left alone: {synthetic:,}")

    # record what was measured on the node, and wire it into the brain
    added = 0
    popmap = D.get("popMap") or {}
    for di, (a1, a) in matched.items():
        popmap[str(di)] = int(a["pop"])
        D["name"][di] = f"{D['name'][di]} ({a['pop']:,} people, " \
                        f"{a['n']} settlements)"
        D["src"][di] = src_id(
            f"GeoNames cities15000 · {a1} · {a['n']} settlements")
        for pi in psych:
            # the weight IS the measured concentration
            D["es"].append(int(di))
            D["et"].append(int(pi))
            D["ew"].append(round(float(a["herf"]), 6))
            added += 1
    D["popMap"] = popmap

    hs = sorted(a["herf"] for a in areas.values())
    print(f"  concentration across areas: median {hs[len(hs)//2]:.3f}, "
          f"range {hs[0]:.3f} to {hs[-1]:.3f}")
    print(f"\n  links {e0:,} -> {len(D['es']):,}  (+{added:,} district to "
          f"behavior)")
    assert len(D["es"]) == len(D["et"]) == len(D["ew"])
    assert D["n"] == n0

    if not apply:
        print("\n  report only. Re-run with --apply.")
        return
    open(DATA, "w", encoding="utf-8").write(
        head + json.dumps(D, separators=(",", ":")) + ";")
    print("  written")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
