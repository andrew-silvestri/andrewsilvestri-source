"""Fetch the small, stable inputs: ITRF2020-PMM, PB2002, and NNR-MORVEL56.

The first two are a few hundred kilobytes, are served openly, and are
committed verbatim. The third is the awkward one.

NNR-MORVEL56, AND WHY IT IS EXTRACTED RATHER THAN COPIED
--------------------------------------------------------
Argus, D.F., Gordon, R.G. and DeMets, C. (2011). Geologically current motion
of 56 plates relative to the no-net-rotation reference frame. Geochemistry,
Geophysics, Geosystems 12(11), Q11001, doi:10.1029/2011GC003751.

The authors' own site is gone: www.geology.wisc.edu resolves but refuses
connections, and geoscience.wisc.edu returns 404 for the MORVEL path. What
survives there in the Internet Archive publishes the pole table as a JPEG,
which cannot be read by anything. The widely used machine-readable copy is a
transcription inside a third-party Python package (MintPy), and a page whose
central argument rests on someone else's retyping of a dead table is a page
with an unchecked number in it.

So the table is extracted from the paper itself, and then checked against
MintPy's independent transcription of the same table. Two people typing the
same numbers from the same source and agreeing is weak evidence; two
independent readings of the source agreeing is the check that is available,
and it is the same principle the rest of this build runs on. The paper also
carries the 95 per cent uncertainties, which MintPy's transcription drops
and which the page needs in order not to overstate the comparison.

Note the licence. MORVEL's own citation page says: "No restrictions are
placed on non-commercial uses of graphics or results from this web site. The
authors retain all commercial rights." That is not an open licence, and the
page says so.

Writes
------
data/ITRF2020-PMM.dat, data/ITRF2020-PMM-residuals.dat   committed verbatim
data/PB2002_boundaries.json                              committed verbatim
data/nnr_morvel56.csv                                    extracted, committed
data/static_provenance.json

Run:  python3 fetch_static.py
"""
import csv
import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RAW = os.path.join(DATA, "raw")

VERBATIM = {
    "ITRF2020-PMM.dat":
        "https://itrf.ign.fr/docs/solutions/itrf2020/ITRF2020-PMM.dat",
    "ITRF2020-PMM-residuals.dat":
        "https://itrf.ign.fr/docs/solutions/itrf2020/ITRF2020-PMM-residuals.dat",
    "PB2002_boundaries.json":
        "https://raw.githubusercontent.com/fraxen/tectonicplates/master/"
        "GeoJSON/PB2002_boundaries.json",
}
ARGUS_PDF = "https://www.eps.mcgill.ca/~courses/c350/ProbSets/Argus_2011_G3.pdf"
MINTPY = ("https://raw.githubusercontent.com/insarlab/MintPy/main/src/mintpy/"
          "objects/euler_pole.py")
MORVEL_CSV = os.path.join(DATA, "nnr_morvel56.csv")
PROV = os.path.join(DATA, "static_provenance.json")

# gate: the extraction must match MintPy's independent transcription
POLE_TOL_DEG = 0.01          # pole position
RATE_TOL_DEG_MYR = 0.001     # rotation rate


def grab(url, dst, timeout=180):
    if os.path.exists(dst):
        return open(dst, "rb").read()
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    print(f"  downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "continents/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
    open(dst, "wb").write(b)
    return b


def extract_morvel(pdf_path):
    """Table 1 of Argus et al. 2011, page 5 of the PDF.

    Rows read as: name, two-letter abbreviation, pole latitude, pole
    longitude, "rate +/- sigma", RMS velocity, area in steradians.
    """
    try:
        import pymupdf
    except ImportError:
        sys.exit("fetch_static: pymupdf is needed to read Table 1 out of the "
                 "paper. pip install pymupdf, or keep the committed "
                 "data/nnr_morvel56.csv, which is what the build reads.")
    doc = pymupdf.open(pdf_path)
    txt = "\n".join(doc[p].get_text() for p in range(3, min(7, doc.page_count)))
    txt = txt.replace("−", "-").replace("‐", "-")
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    num = re.compile(r"^-?\d+\.\d+$")
    rows, i = [], 0
    while i < len(lines) - 6:
        if (re.fullmatch(r"[a-z]{2}", lines[i + 1]) and num.match(lines[i + 2])
                and num.match(lines[i + 3]) and "±" in lines[i + 4]):
            w, sig = [x.strip() for x in lines[i + 4].split("±")]
            rows.append({"name": lines[i], "abbrev": lines[i + 1],
                         "pole_lat": float(lines[i + 2]),
                         "pole_lon": float(lines[i + 3]),
                         "rate_deg_myr": float(w),
                         "sigma95_deg_myr": float(sig),
                         "rms_mm_yr": float(lines[i + 5]),
                         "area_steradian": float(lines[i + 6])})
            i += 7
        else:
            i += 1
    return rows


def mintpy_table(text):
    blk = text[text.index("NNR_MORVEL56_PMM = {"):]
    blk = blk[:blk.index("\n}")]
    out = {}
    for m in re.finditer(r"Tag\(\s*'(\w+)'\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)"
                         r"\s*,\s*(-?[\d.]+)\s*\)", blk):
        out[m.group(1).lower()] = (float(m.group(2)), float(m.group(3)),
                                   float(m.group(4)))
    return out


def main():
    digests = {}
    for name, url in VERBATIM.items():
        b = grab(url, os.path.join(DATA, name))
        digests[name] = hashlib.sha256(b).hexdigest()
        print(f"  {name:30} {len(b):>9,} bytes")

    pdf = os.path.join(RAW, "Argus_2011_G3.pdf")
    b = grab(ARGUS_PDF, pdf)
    digests["Argus_2011_G3.pdf"] = hashlib.sha256(b).hexdigest()
    rows = extract_morvel(pdf)
    if len(rows) < 20:
        sys.exit(f"fetch_static: only {len(rows)} rows parsed from Table 1; "
                 "the PDF's layout changed. Nothing written.")

    mp_text = grab(MINTPY, os.path.join(RAW, "mintpy_euler_pole.py")).decode()
    mp = mintpy_table(mp_text)
    digests["mintpy_euler_pole.py"] = hashlib.sha256(
        mp_text.encode()).hexdigest()

    # The gate. MintPy renames Nubia to nu to avoid colliding with North
    # Bismarck; the paper calls it nb. Everything else matches by abbrev.
    alias = {"nb": "nu"}
    checked, bad = 0, []
    for r in rows:
        key = alias.get(r["abbrev"], r["abbrev"])
        if key not in mp:
            continue
        la, lo, w = mp[key]
        checked += 1
        if (abs(la - r["pole_lat"]) > POLE_TOL_DEG
                or abs(lo - r["pole_lon"]) > POLE_TOL_DEG
                or abs(w - r["rate_deg_myr"]) > RATE_TOL_DEG_MYR):
            bad.append(f"{r['name']}: paper "
                       f"{r['pole_lat']}/{r['pole_lon']}/{r['rate_deg_myr']} "
                       f"vs MintPy {la}/{lo}/{w}")
    if bad:
        for x in bad:
            print("  MORVEL FAIL " + x)
        sys.exit("fetch_static: the table extracted from the paper disagrees "
                 "with MintPy's independent transcription. One of the two is "
                 "wrong and neither can be trusted until that is resolved. "
                 "Nothing written.")
    print(f"  MORVEL  ok    {len(rows)} plates from Table 1 of the paper; "
          f"{checked} cross-checked against MintPy to "
          f"{POLE_TOL_DEG} deg and {RATE_TOL_DEG_MYR} deg/Myr")

    with open(MORVEL_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    json.dump({
        "itrf": {"citation": ("Altamimi, Z., Metivier, L., Rebischung, P., "
                              "Collilieux, X., Chanard, K. and Barneoud, J. "
                              "(2023). ITRF2020 Plate Motion Model. "
                              "Geophysical Research Letters 50(24), "
                              "e2023GL106373, doi:10.1029/2023GL106373."),
                 "licence": "none stated"},
        "pb2002": {"citation": ("Bird, P. (2003). An updated digital model of "
                                "plate boundaries. Geochemistry, Geophysics, "
                                "Geosystems 4(3), 1027, "
                                "doi:10.1029/2001GC000252."),
                   "licence": "none stated; cite the paper"},
        "morvel": {"citation": ("Argus, D.F., Gordon, R.G. and DeMets, C. "
                                "(2011). Geologically current motion of 56 "
                                "plates relative to the no-net-rotation "
                                "reference frame. Geochemistry, Geophysics, "
                                "Geosystems 12(11), Q11001, "
                                "doi:10.1029/2011GC003751."),
                   "table": "Table 1, page 5 of the PDF",
                   "extracted_rows": len(rows),
                   "cross_checked_against": MINTPY,
                   "cross_checked_rows": checked,
                   "pole_tol_deg": POLE_TOL_DEG,
                   "rate_tol_deg_myr": RATE_TOL_DEG_MYR,
                   "licence": ("not an open licence. The MORVEL site's own "
                               "citation page: 'No restrictions are placed on "
                               "non-commercial uses of graphics or results "
                               "from this web site. The authors retain all "
                               "commercial rights.'"),
                   "host_note": ("the authors' site is unreachable and its "
                                 "own copy of this table is a JPEG, which is "
                                 "why the paper is the source here")},
        "sha256": digests,
        "fetched": datetime.now(timezone.utc).date().isoformat(),
    }, open(PROV, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print(f"  wrote data/nnr_morvel56.csv  {len(rows)} plates")


if __name__ == "__main__":
    main()
