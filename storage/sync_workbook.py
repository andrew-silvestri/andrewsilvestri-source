"""Write model.py's 4-hour dispatch into storage_arbitrage.xlsx, and keep the
Summary sheet's formulas on model.py's definitions.

Why this exists: until 2026-10-21 nothing produced the workbook. It shipped in
storage-code.zip carrying an older price year (prices up to $322/MWh away from
outputs/dispatch_4h.csv) and its own definitions - cycling cost on discharge
only, cycles divided by E rather than E*sqrt(RTE) - so it read 110.2 gross and
104.4 net $/kW-yr while the page and model.py said 107.1 net (QA substance
audit, AUDIT_SUBSTANCE.md, storage section).

    python model.py           # writes outputs/dispatch_4h.csv
    python sync_workbook.py   # writes it into the workbook
    python sync_workbook.py --check   # exit 1 if the workbook is behind the csv
"""
import copy
import csv
import os
import sys

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(HERE, "storage_arbitrage.xlsx")
CSV = os.path.join(HERE, "outputs", "dispatch_4h.csv")
RTE = 0.86  # model.optimize's default; the LP splits it as sqrt per leg

D = "Dispatch!$D$2:$D$8761"
C = "Dispatch!$C$2:$C$8761"
FORMULAS = {
    # Cycling cost is charged on both legs, half the rate each, as in the LP
    # objective (model.py: c_deg * 0.5 * (d + c)).
    "A11": "Cycling cost ($)",
    "B11": f"=B6*0.5*(SUM({D})+SUM({C}))",
    # Equivalent full cycles on the storage side: AC discharge / (E * sqrt(RTE)).
    "B10": "=B9/(B4*B5*SQRT(B7))",
    "A6": "Cycling cost ($/MWh throughput, half per leg)",
    "A7": "Round-trip efficiency",
    "B7": RTE,
    # model.py's fig5 sums gross revenue over 730-hour blocks, not calendar months.
    "A18": "Gross revenue by 730-hour block ($), as in fig5",
}


def rows():
    with open(CSV, newline="") as f:
        r = list(csv.reader(f))
    return [[int(x[0])] + [float(v) for v in x[1:]] for x in r[1:]]


def main(check):
    data = rows()
    wb = openpyxl.load_workbook(XLSX)
    ws = wb["Dispatch"]
    sm = wb["Summary"]
    behind = []
    for i, row in enumerate(data, start=2):
        for j, v in enumerate(row, start=1):
            cell = ws.cell(row=i, column=j)
            if cell.value != v:
                behind.append(cell.coordinate)
                cell.value = v
    for k, v in FORMULAS.items():
        if sm[k].value != v:
            behind.append("Summary!" + k)
            sm[k].value = v
    if sm["B7"].fill != sm["B6"].fill:
        sm["B7"].fill = copy.copy(sm["B6"].fill)
    print(f"{len(data)} dispatch rows; {len(behind)} cell(s) behind the csv")
    if check:
        return 1 if behind else 0
    if behind:
        wb.save(XLSX)
        print("wrote", XLSX)
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
