"""
Every input in the climate-cost process graph, checked against the unit its
receiving process declares.

The bug this exists for: the two car delivery stages shipped a vehicle mass of
`1.4` and `1.6` in a field the engine reads in kilograms. The value was in
tonnes. Nothing failed - the leg was simply a thousandth of its size for a
month - because no check ever asked "is 1.4 a plausible number of kilograms
for a car?" This asks that for every input, every time.

The check is a band per declared unit: the range a per-functional-unit amount
(or a per-process-unit amount) can plausibly take. Bands are deliberately
wide - three or four orders of magnitude - so they never argue with a
modelling choice; they only catch a number that is in the wrong unit, which
is off by a thousand or more. A value that lands outside its band is either a
unit slip or needs a comment in the band table saying why it is not.

Run:  python3 tests/test_units.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CC = os.path.join(os.path.dirname(HERE), "climate-cost")
sys.path.insert(0, os.path.join(CC, "data"))
from processes import PROCESSES, PRODUCTS, TRANSPORT  # noqa: E402

# Plausible amount of an input, per functional unit of a PRODUCT stage, keyed
# by the unit the input process declares. Functional units are 1 kg of food,
# 100 km / 100 passenger-km of travel, one garment for life.
STAGE_BANDS = {
    "km":                 (1, 5000),        # a transport mode used as an input
    "kg N applied":       (1e-4, 1),
    "kg N":               (1e-4, 1),
    "kg P2O5":            (1e-4, 0.1),
    "kg active":          (1e-5, 0.01),
    "kWh":                (0.005, 50),      # 18 kWh/100 km for the EV is the top
    "hectare-season":     (1e-6, 0.01),
    "litre":              (0.005, 50),
    "kg":                 (0.001, 500000),  # airframes are 42-180 t, amortised
    "kg gas":             (0.01, 2),
    "kg gas burned":      (0.01, 2),
    "kg of vehicle":      (500, 500000),    # 1.4 t car to 400 t train, amortised
    "kWh of capacity":    (5, 200),
    "1,000 km":           (0.005, 1),
    "1,000 vehicle-km":   (0.005, 1),
    "passenger-km":       (1, 1000),
    "kg fibre":           (0.05, 5),
    "kg fabric":          (0.05, 5),
    "garment":            (0.5, 10),
    "kg waste":           (0.05, 5),
    "kg fuel":            (0.5, 10),
}

# Plausible amount of an input per ONE unit of a PROCESS, keyed the same way.
PROCESS_BANDS = {
    "kg gas":             (0.05, 5),
    "kg N":               (0.05, 5),
    "litre":              (0.05, 500),      # tillage: 95 L diesel per hectare
    "kg":                 (0.01, 5),
    "kWh":                (0.1, 100),       # a battery pack: 55 kWh per kWh
    "kg N applied":       (0.01, 1),
    "kg active":          (0.001, 0.1),
}

# Stage-level multipliers, from the engine's reading of them.
FREIGHT_KG = (0.05, 20000)   # a t-shirt with its carton, up to a bus
AMORTISE = (1e-9, 1e-2)      # functional unit over a lifetime


def unit_of(pid):
    return "km" if pid in TRANSPORT else PROCESSES[pid]["unit"]


def main():
    bad, n = [], 0
    for pk, pp in PRODUCTS.items():
        for st in pp["stages"]:
            for cid, amt, _al in st["inputs"]:
                n += 1
                u = unit_of(cid)
                if u not in STAGE_BANDS:
                    bad.append(f"{pk}/{st['id']}/{cid}: no band for unit {u!r}")
                    continue
                lo, hi = STAGE_BANDS[u]
                if not lo <= amt <= hi:
                    bad.append(f"{pk}/{st['id']}/{cid}: {amt:g} [{u}] outside "
                               f"{lo:g}-{hi:g} per {pp['unit']}")
            if "freight_kg" in st:
                n += 1
                if not FREIGHT_KG[0] <= st["freight_kg"] <= FREIGHT_KG[1]:
                    bad.append(f"{pk}/{st['id']}: freight_kg {st['freight_kg']:g} "
                               f"is not kilograms")
            if "amortise" in st:
                n += 1
                if not AMORTISE[0] <= st["amortise"] <= AMORTISE[1]:
                    bad.append(f"{pk}/{st['id']}: amortise {st['amortise']:g} "
                               f"is not a functional unit over a lifetime")
    for pid, pr in PROCESSES.items():
        for cid, amt, _al in pr.get("inputs", []):
            n += 1
            u = unit_of(cid)
            if u not in PROCESS_BANDS:
                bad.append(f"{pid}/{cid}: no band for unit {u!r}")
                continue
            lo, hi = PROCESS_BANDS[u]
            if not lo <= amt <= hi:
                bad.append(f"{pid}/{cid}: {amt:g} [{u}] outside {lo:g}-{hi:g} "
                           f"per {pr['unit']}")
    # every process that is not a transport mode declares a unit and a
    # non-negative-or-explained direct term
    for pid, pr in PROCESSES.items():
        if not pr.get("unit"):
            bad.append(f"{pid}: no unit")
    print(f"  {n} inputs and multipliers checked against their declared unit: "
          f"{'ok' if not bad else 'FAIL'}")
    for b in bad:
        print("    " + b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
