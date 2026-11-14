"""The public files the algae page reads, fetched into algae/data/raw/ and recorded in data/fetched.json.

Global Carbon Budget 2025 (Friedlingstein et al. 2026, Earth Syst. Sci. Data 18, 3211-3288,
doi:10.5194/essd-18-3211-2026), CC BY 4.0
- gcb2025.xlsx: Global_Carbon_Budget_2025_v1.0.xlsx from the ICOS Carbon Portal (object
  qSjPBsV1drZnYdH-yCJMmkGn). The portal serves the file once its licence is accepted; the
  CpLicenseAcceptedFor cookie is what the licence page sets. No account.

Siegel, DeVries, Doney and Bell (2021), Environ. Res. Lett. 16, 104003, CC BY 4.0
- Not fetched here: iopscience.iop.org refuses scripted requests, so the build checks the article's
  printed figures as typed constants with their page reference (build_algae.PRINTED). The data file (fseq_OCIM2_48L.nc, 3.3 GB, CC0, figshare 15228690) is not downloaded:
  siegel_retention.py reads only the rows it needs with HTTP range requests.

Run:  python fetch_public.py [name ...]
"""
from netfetch import fetch

ICOS = "qSjPBsV1drZnYdH-yCJMmkGn"
FILES = {
    "gcb2025.xlsx": ("https://data.icos-cp.eu/objects/" + ICOS, {"Cookie": "CpLicenseAcceptedFor=" + ICOS}),
}

if __name__ == "__main__":
    import sys
    only = sys.argv[1:]
    for name, (url, headers) in FILES.items():
        if not only or name in only:
            p = fetch(url, name, headers=headers)
            if p.stat().st_size < 50000:
                raise SystemExit(f"{name}: {p.stat().st_size} bytes, not the document")
