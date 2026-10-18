"""Read PERCENT_UNACC_GAS from PHMSA's gas distribution annual reports.

Field definition (Form PHMSA F 7100.1-1, Part G, in the data-fields PDF
inside the same ZIP): unaccounted-for gas as a percent of total consumption
for the 12 months ending June 30 of the report year,
    [(purchased + produced) - (customer use + company use + adjustments)]
    / (customer use + company use + adjustments) x 100.
Distribution operators only; PHMSA does not collect it for transmission or
gathering.

`load()` returns one dict per report (operator-year). Run directly, it prints
a per-year summary: report count, how many are negative, the 10th, 50th and
90th percentiles, the maximum, and the operator-type and commodity mix
(neither column exists before 2015).

Run:  python read_phmsa.py
"""
import collections
import io
import zipfile

import numpy as np
import openpyxl

from netfetch import verified

NAME = "annual_gas_distribution_2010_present.zip"
FIELD = "PERCENT_UNACC_GAS"


def load():
    path, _ = verified(NAME)
    z = zipfile.ZipFile(path)
    out = []
    for name in sorted(n for n in z.namelist() if n.startswith("annual_gas_distribution_") and n.endswith(".xlsx")):
        ws = openpyxl.load_workbook(io.BytesIO(z.read(name)), read_only=True).worksheets[0]
        it = ws.iter_rows(values_only=True)
        for r in it:   # two note rows precede the header
            if r and r[0] == "DATAFILE_AS_OF":
                hdr = list(r)
                break
        else:
            raise RuntimeError(f"{name}: no header row")
        for r in it:
            if r and r[1] is not None:
                out.append(dict(zip(hdr, r)))
    return out


def main():
    rows = load()
    by = collections.defaultdict(list)
    for r in rows:
        by[int(r["REPORT_YEAR"])].append(r)
    for y in sorted(by):
        rs = by[y]
        v = np.array([float(r[FIELD]) for r in rs if r.get(FIELD) not in (None, "")])
        ot = collections.Counter(r.get("OPERATOR_TYPE") for r in rs)
        cm = collections.Counter(r.get("COMMODITY") for r in rs)
        p10, p50, p90 = np.percentile(v, [10, 50, 90])
        print(f"{y}  reports {len(rs):5d}  with value {len(v):5d}  negative {int((v < 0).sum()):4d}  zero {int((v == 0).sum()):4d}"
              f"  p10/p50/p90 {p10:6.2f}/{p50:5.2f}/{p90:5.2f}  max {v.max():6.1f}"
              f"  natural-gas reports {cm.get('Natural Gas', 'n/a')}  operator types {len([k for k in ot if k])}")


if __name__ == "__main__":
    main()
