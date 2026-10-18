"""Known-answer check: compressibility Z from the NIST AGA8 reference code, and CoolProp.

Three tiers, strongest first.

1. NIST's own test programs (AGA8CODE/C/GERG2008_test_01.cpp, Detail_test_01.cpp):
   one 21-component mixture at 400 K and 50,000 kPa, Z to 1e-8, GERG-2008 and
   DETAIL. Exact known answers. GATE.

2. NIST's TESTDATA/Test Data.xls, sheet "Natural Gas Calculations": pressure at
   stated (T, d) for some 200 mixtures, GERG-2008 and DETAIL, along each
   mixture's saturation boundary. Two things about that file, both measured
   here (STAGE1.md has the commands):
   - its gas numbers do not index the compositions sheet one-to-one. MAPPING
     below was found by fitting and is stated as such;
   - it was computed with REFPROP 9.1, not with this code, and does not
     reproduce bit-for-bit: up to 7.7e-5 in the gas phase and 1e-4 to 1e-1
     toward the liquid side and for the gases that identify with no
     composition at all.
   So the gate is on the gas phase (d <= 5 mol/L, where a meter runs) of the
   gases that identify, at TOL_REF; and on the number that identify
   (MIN_IDENT), because a broken composition mapping drops gases out of the
   comparison rather than failing it. The --break run shows exactly that: the
   "beyond" count stays 0 and the identification floor is what fails. GATE.

3. The metering region: the five AGA8 example gases of NIST's Tables.xls at
   32-150 F and 14.73-1200 psia, CoolProp's HEOS mixture route (documented as
   GERG-2008) against the reference GERG-2008, and DETAIL against GERG-2008.
   REPORTED, with --coolprop also CoolProp against the tier-2 table points.
   CoolProp's disagreement decides which route the model uses; it is not a
   pass/fail, because a library differing from the reference is a finding.

The compiled library is built from the NIST C++ outside this repository (see
STAGE1.md): set METER_AGA8_DLL, or it is looked for at
../03 RESEARCH/meter/vendor/build/aga8.dll from the repo root.

--break exchanges hydrogen and helium in every composition (the NIST code
orders them 15 and 20; the test sheet puts them 20 and 16), the error the two
column orders invite. It must exit 1.
"""
import ctypes
import json
import os
import sys
from pathlib import Path

import numpy as np
import xlrd

BREAK = "--break" in sys.argv
WITH_COOLPROP = "--coolprop" in sys.argv   # slow (about an hour); the gate does not need it
ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT.parent / "03 RESEARCH" / "meter" / "vendor"
DLL = Path(os.environ.get("METER_AGA8_DLL", VENDOR / "build" / "aga8.dll"))
TESTDATA = VENDOR / "AGA8" / "TESTDATA"

# The test sheet's column order, and where each column goes in the NIST code's
# order (1 methane ... 14 n-decane, 15 hydrogen, 16 oxygen, 17 CO, 18 water,
# 19 H2S, 20 helium, 21 argon; GERG2008.cpp lines 55-75). The sheet lists the
# last seven differently: H2S, helium, water, oxygen, argon, hydrogen, CO.
SHEET = ["methane", "nitrogen", "CO2", "ethane", "propane", "ibutane", "butane",
         "ipentane", "pentane", "hexane", "heptane", "octane", "nonane", "decane",
         "H2S", "helium", "water", "oxygen", "argon", "hydrogen", "CO"]
NIST = ["methane", "nitrogen", "CO2", "ethane", "propane", "ibutane", "butane",
        "ipentane", "pentane", "hexane", "heptane", "octane", "nonane", "decane",
        "hydrogen", "oxygen", "CO", "water", "H2S", "helium", "argon"]
COOLPROP = {"methane": "Methane", "nitrogen": "Nitrogen", "CO2": "CarbonDioxide",
            "ethane": "Ethane", "propane": "n-Propane", "ibutane": "IsoButane",
            "butane": "n-Butane", "ipentane": "Isopentane", "pentane": "n-Pentane",
            "hexane": "n-Hexane", "heptane": "n-Heptane", "octane": "n-Octane",
            "nonane": "n-Nonane", "decane": "n-Decane", "H2S": "HydrogenSulfide",
            "helium": "Helium", "water": "Water", "oxygen": "Oxygen", "argon": "Argon",
            "hydrogen": "Hydrogen", "CO": "CarbonMonoxide"}
R_GERG = 8.314472   # GERG2008.cpp:665
R_DETAIL = 8.31451  # Detail.cpp:524

# Six significant figures in the table: half a unit in the sixth place is
# 5e-6 relative at worst for a leading 1, so the reference must sit inside it.
TOL_TABLE = 5.0e-6

# The table was computed with REFPROP 9.1 (the sheet says so) and does not
# reproduce bit-for-bit under the AGA8 reference code: measured 2026-10-18 on
# the identified gases' gas-phase points, worst 7.65e-5 (GERG) and 4.38e-5
# (DETAIL), p99 2.9e-5 and 1.9e-5, growing toward the liquid side. TOL_REF is
# that disagreement rounded up to the next decade. It is the reference's own
# tolerance against its own published table, and CoolProp is judged against it.
TOL_REF = 1.0e-4
D_GAS = 5.0        # mol/L; 1200 psia at 60 F is about 4 mol/L for these gases
IDENT = 2.0e-5     # a gas "identifies" when its three lowest-density points do
MIN_IDENT = {"gerg": 171, "detail": 122}   # measured 2026-10-18; a drop means the mapping broke


def swap(x):
    """--break: hydrogen and helium exchanged in the NIST-ordered vector."""
    x = list(x)
    if BREAK:
        i, j = NIST.index("hydrogen"), NIST.index("helium")
        x[i], x[j] = x[j], x[i]
    return x


def nist_vector(sheet_row):
    x = np.zeros(21)
    for name, v in zip(SHEET, sheet_row):
        x[NIST.index(name)] = v
    return np.array(swap(x / x.sum()))


class Ref:
    def __init__(self, path):
        self.lib = ctypes.CDLL(str(path))
        self.lib.setup()
        D = ctypes.c_double
        for f in ("p_gerg", "p_detail"):
            getattr(self.lib, f).argtypes = [D, D, ctypes.POINTER(D), ctypes.POINTER(D), ctypes.POINTER(D)]
        for f in ("d_gerg", "d_detail"):
            getattr(self.lib, f).argtypes = [D, D, ctypes.POINTER(D), ctypes.POINTER(D)]
            getattr(self.lib, f).restype = ctypes.c_int

    def _x(self, x):
        return (ctypes.c_double * 21)(*x)

    def p(self, which, T, d, x):
        P, Z = ctypes.c_double(), ctypes.c_double()
        getattr(self.lib, "p_" + which)(T, d, self._x(x), ctypes.byref(P), ctypes.byref(Z))
        return P.value / 1000.0, Z.value          # MPa

    def z_tp(self, which, T, P_kPa, x):
        D = ctypes.c_double()
        err = getattr(self.lib, "d_" + which)(T, P_kPa, self._x(x), ctypes.byref(D))
        if err:
            raise RuntimeError(f"{which} density failed, ierr {err}")
        return P_kPa / (D.value * T * (R_GERG if which == "gerg" else R_DETAIL))


def coolprop_state(x):
    import CoolProp.CoolProp as CP
    names = [COOLPROP[NIST[i]] for i in range(21) if x[i] > 0]
    fr = [x[i] for i in range(21) if x[i] > 0]
    st = CP.AbstractState("HEOS", "&".join(names))
    st.set_mole_fractions(fr)
    return st


_STATES = {}


def coolprop_p(x, T, d, key):
    # Building a 10-20 component HEOS state costs seconds; build one per mixture.
    import CoolProp.CoolProp as CP
    if key not in _STATES:
        _STATES[key] = coolprop_state(x)
    st = _STATES[key]
    st.update(CP.DmolarT_INPUTS, d * 1000.0, T)
    return st.p() / 1e6


# The calculations sheet numbers its gases 2-202; the compositions sheet has
# rows 2-201. The two do not line up one-to-one, and the sheets do not say how
# they map. Found by fitting (2026-10-18, STAGE1.md "Identifying the test
# gases"): for each tabulated gas, the composition row that reproduces its
# three lowest-density points under the reference code. 171 of 198 gases
# identify within 2e-5 and they fall into three runs:
MAPPING = ((2, 25, 0), (26, 63, -1), (64, 202, -2))   # (first gas, last gas, row offset)


def comp_row(gas):
    for a, b, off in MAPPING:
        if a <= gas <= b:
            return gas + off
    raise KeyError(gas)


def load_table():
    wb = xlrd.open_workbook(str(TESTDATA / "Test Data.xls"))
    comp = wb.sheet_by_name("Natural Gas Compositions")
    assert [c.value for c in comp.row(0)] == SHEET, "composition columns are not in the order this check assumes"
    # "Gases are identified by the row number, and start at 2 and end at 201"
    # (the sheet's own note): spreadsheet row g is xlrd row g - 1.
    mixes = {}
    for r in range(1, comp.nrows):
        v = [c.value for c in comp.row(r)]
        if all(isinstance(t, float) for t in v):
            mixes[r + 1] = [float(t) for t in v]
    assert len(mixes) == 200 and mixes[201][0] == 100.0, "gas 201 should be pure methane"
    calc = wb.sheet_by_name("Natural Gas Calculations")
    hdr = [c.value for c in calc.row(10)]
    assert hdr[:5] == ["Gas #", "T (K)", "d (mol/l)", "", "P (MPa)"] and hdr[9] == "P (MPa)", hdr
    rows = []
    for r in range(11, calc.nrows):
        v = [c.value for c in calc.row(r)]
        if v[0] == "" or v[1] == "" or v[2] == "":
            continue
        rows.append((int(v[0]), float(v[1]), float(v[2]),
                     float(v[4]) if v[4] not in ("", 0.0) else None,
                     float(v[9]) if v[9] not in ("", 0.0) else None))
    return mixes, rows


def rel(a, b):
    return abs(a - b) / abs(b)


# NIST's own test programs (AGA8CODE/C/*_test_01.cpp): one 21-component mixture
# at 400 K and 50,000 kPa, Z to 1e-8. Inputs and reference values copied from
# those files. These are exact known answers; the table below is a wide sweep.
NIST_X = [0.77824, 0.02, 0.06, 0.08, 0.03, 0.0015, 0.003, 0.0005, 0.00165, 0.00215, 0.00088,
          0.00024, 0.00015, 0.00009, 0.004, 0.005, 0.002, 0.0001, 0.0025, 0.007, 0.001]
NIST_Z = {"gerg": 1.174690666383717, "detail": 1.173801364147326}


def envelope(ref, which, T, d, x, P):
    """What the table's own rounding allows: T is printed to 0.001 K, P to ~6 figures.
    Near saturation P(T) is steep, so the T rounding alone can move P by far more than
    its last digit; the reference code's own dP/dT sets how far."""
    dPdT = abs(ref.p(which, T + 5e-4, d, x)[0] - ref.p(which, T - 5e-4, d, x)[0]) / 2
    return (dPdT + 5e-6 + TOL_TABLE * abs(P)) / abs(P)


def main():
    if not DLL.exists():
        print(f"FAIL: reference library not found at {DLL}")
        return 1
    ref = Ref(DLL)
    fails = 0
    tag = "  [--break: hydrogen and helium swapped]" if BREAK else ""

    for which in ("gerg", "detail"):
        z = ref.z_tp(which, 400.0, 50000.0, swap(NIST_X))
        ok = abs(z - NIST_Z[which]) <= 1e-8
        fails += not ok
        print(f"  {'OK  ' if ok else 'FAIL'} NIST test point, {which}: Z {z:.15f} vs {NIST_Z[which]:.15f}")

    mixes, rows = load_table()
    pts = {}
    for gas, T, d, Pg, Pd in rows:
        x = nist_vector(mixes[comp_row(gas)])
        for which, P in (("gerg", Pg), ("detail", Pd)):
            if P is not None:
                pts.setdefault((which, gas), []).append((d, T, P, x))
    print(f"{len(rows)} tabulated points over {len({r[0] for r in rows})} gas numbers{tag}")
    for which in ("gerg", "detail"):
        devs, ident = [], 0
        for (w, gas), v in pts.items():
            if w != which:
                continue
            v = sorted(v, key=lambda t: t[0])
            # identified: the three lowest-density points reproduce to IDENT
            if max(rel(ref.p(which, T, d, x)[0], P) for d, T, P, x in v[:3]) > IDENT:
                continue
            ident += 1
            devs += [(rel(ref.p(which, T, d, x)[0], P), gas, T, d) for d, T, P, x in v if d <= D_GAS]
        if not devs:
            fails += 1
            print(f"  FAIL {which}: no tabulated gas identifies; the composition mapping is wrong")
            continue
        w = max(devs)
        over = sum(1 for t in devs if t[0] > TOL_REF)
        ok = over == 0 and ident >= MIN_IDENT[which]
        fails += not ok
        print(f"  {'OK  ' if ok else 'FAIL'} NIST {which} code vs its table: {ident} gases identify"
              f" (floor {MIN_IDENT[which]}); {len(devs)} gas-phase points (d <= {D_GAS} mol/L);"
              f" worst {w[0]:.2e} (gas {w[1]}, {w[2]} K, {w[3]} mol/L); {over} beyond {TOL_REF:g}")
        if which == "gerg":
            gerg_pts = [(gas, T, d, P, x) for (ww, gas), v in pts.items() if ww == "gerg"
                        for d, T, P, x in v if d <= D_GAS and gas in {t[1] for t in devs}]

    if WITH_COOLPROP:
        cp, cp_failed = [], []
        for gas, T, d, P, x in gerg_pts:
            try:
                cp.append((rel(coolprop_p(x, T, d, gas), P), gas, T, d))
            except Exception as e:  # noqa: BLE001 - reported, counted
                cp_failed.append((gas, str(e)[:90]))
        a = np.array([c[0] for c in cp])
        w = max(cp)
        print(f"  REPORT CoolProp HEOS vs the same GERG table points: {len(a)} points; worst {w[0]:.2e}"
              f" (gas {w[1]}, {w[2]} K, {w[3]} mol/L); median {np.median(a):.2e};"
              f" {int((a > TOL_REF).sum())} beyond {TOL_REF:g}; {len(cp_failed)} points CoolProp could not evaluate")
        if cp_failed:
            print("         first CoolProp failure:", cp_failed[0])

    # The metering region: the five AGA8 example gases in NIST's Tables.xls and its
    # T, P grid widened to six pressures. Reference code against itself (DETAIL vs
    # GERG) and CoolProp against the reference.
    wb = xlrd.open_workbook(str(TESTDATA / "Tables.xls"))
    s = wb.sheet_by_name("Tables")
    names = ["Gulf Coast", "Amarillo", "Ekofisk", "High N2", "High CO2"]
    comp_rows = {"Methane": "methane", "Nitrogen": "nitrogen", "CO2": "CO2", "Ethane": "ethane",
                 "Propane": "propane", "i-Butane": "ibutane", "n-Butane": "butane",
                 "i-Pentane": "ipentane", "n-Pentane": "pentane", "n-Hexane": "hexane"}
    gases = {n: np.zeros(21) for n in names}
    for r in range(7, 17):
        for k, n in enumerate(names):
            gases[n][NIST.index(comp_rows[s.cell(r, 1).value])] = float(s.cell(r, 3 + k).value) / 100.0
    import CoolProp.CoolProp as CP
    region = {"coolprop_vs_ref": [], "detail_vs_gerg": []}
    for n, x in gases.items():
        x = x / x.sum()
        st = coolprop_state(x)
        for TF in (32.0, 60.0, 100.0, 150.0):
            T = (TF - 32.0) / 1.8 + 273.15
            for psia in (14.73, 100.0, 300.0, 600.0, 900.0, 1200.0):
                P = psia * 6.894757293168361      # kPa
                zg = ref.z_tp("gerg", T, P, x)
                st.update(CP.PT_INPUTS, P * 1000.0, T)
                region["coolprop_vs_ref"].append((rel(st.compressibility_factor(), zg), n, TF, psia))
                region["detail_vs_gerg"].append((rel(ref.z_tp("detail", T, P, x), zg), n, TF, psia))
    for key, label in (("coolprop_vs_ref", "CoolProp vs NIST GERG-2008, Z"),
                       ("detail_vs_gerg", "NIST DETAIL vs NIST GERG-2008, Z")):
        w = max(region[key])
        print(f"  REPORT metering region, {label}: worst {w[0]:.2e} ({w[1]}, {w[2]:g} F, {w[3]:g} psia)"
              f" over {len(region[key])} points")
    print(f"{fails} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
