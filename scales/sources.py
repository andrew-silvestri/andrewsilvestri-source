"""Readers for the scales page. Each reads a hash-checked raw file (netfetch.verified), so the data on the
page are read out of the publishers' own files, not typed.

metabolism()        Hatton et al. (2019) Data/Metabolism.csv as a list of dicts (8,098 rows), from the Zenodo zip.
stars()             Eker et al. (2018) table1: [(name, mass Msun, radius Rsun, Teff K, remark)], all 586 rows.
energy_per_capita() OWID primary energy per person: {entity: {year: kWh a year}}.
owid_meta()         the OWID metadata dict (titles, sources, last update).
county_gdp(year)    BEA CAGDP1 line 1 (GDP, thousand current dollars): {5-digit county FIPS: value}.
msa_population(year) Census CBSA estimates: ({CBSA: (name, population)} for metropolitan areas,
                    {CBSA: [county FIPS]}).
flat(name)          a PDF's text, whitespace collapsed.
quote(name, p)      the match of a regular expression in a source; raises if absent.
"""
import csv
import io
import json
import re
import zipfile

import pymupdf

from netfetch import verified

_cache = {}


def flat(name):
    if name not in _cache:
        p, _ = verified(name)
        t = " ".join(pg.get_text() for pg in pymupdf.open(p))
        _cache[name] = re.sub(r"\s+", " ", t).strip()
    return _cache[name]


def quote(name, pattern):
    m = re.search(pattern, flat(name))
    if not m:
        raise LookupError(f"{name}: no match for {pattern!r}")
    return m


def metabolism():
    p, _ = verified("hatton_link_scaling.zip")
    with zipfile.ZipFile(p) as z:
        raw = z.read("Link-scaling/Data/Metabolism.csv")
    return list(csv.DictReader(io.StringIO(raw.decode("latin-1"))))


def stars():
    p, _ = verified("eker2018_table1.tsv")
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln and not ln.startswith("#")]
    head = lines[0].split("\t")
    out = []
    for ln in lines[3:]:          # header, units, dashes
        r = dict(zip(head, ln.split("\t")))
        out.append((r["Name"].strip(), float(r["Mass"]), float(r["Rad"]), float(r["Teff"]), r["Remark"].strip()))
    return out


def energy_per_capita():
    p, _ = verified("owid_energy_per_capita.csv")
    out = {}
    for r in csv.DictReader(open(p, encoding="utf-8")):
        out.setdefault(r["entity"], {})[int(r["year"])] = float(r["total_energy_supply_per_capita_kwh"])
    return out


def owid_meta():
    p, _ = verified("owid_energy_per_capita.json")
    return json.loads(p.read_text(encoding="utf-8"))


def county_gdp(year):
    p, _ = verified("bea_cagdp1.zip")
    with zipfile.ZipFile(p) as z:
        name = [n for n in z.namelist() if n.startswith("CAGDP1__ALL_AREAS")][0]
        text = z.read(name).decode("latin-1")
    rows = csv.reader(io.StringIO(text))
    head = next(rows)
    col = head.index(str(year))
    out = {}
    for r in rows:
        if len(r) <= col or r[4].strip() != "1":
            continue
        fips = r[0].strip(' "')
        if fips.isdigit() and not fips.endswith("000"):
            try:
                out[fips] = float(r[col])
            except ValueError:     # (D) suppressed, (NA)
                pass
    return out


def msa_population(year):
    p, _ = verified("census_cbsa_2023.csv")
    rows = list(csv.DictReader(open(p, encoding="latin-1")))
    msa = {r["CBSA"]: (r["NAME"], float(r[f"POPESTIMATE{year}"]))
           for r in rows if r["LSAD"].startswith("Metropolitan")}
    counties = {c: [] for c in msa}
    for r in rows:
        if r["LSAD"].startswith("County") and r["CBSA"] in counties:
            counties[r["CBSA"]].append(r["STCOU"])
    return msa, counties
