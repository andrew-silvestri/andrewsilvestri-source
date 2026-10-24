"""Build site/meter-app.html: app_template.html with engine.js and the gas table inlined.

The gas table is what the browser cannot compute: GERG-2008's Z and kappa at
the meter's upstream conditions, and the composition Jacobian of ln Z1, on a
(T, p) grid for each of NIST's five AGA8 example gases, plus the base-state
values (Zb, molar mass, heating value and their Jacobians), which do not
depend on T1 or p1. All from the NIST reference code through aga8lib.

ln Z1 and kappa sit on a fine grid (5 F x 10 psia) read by biquadratic
(three-point Lagrange) interpolation; the composition Jacobian on a coarse
grid (10 F x 25 psia) read bilinearly, since it only scales a term that is
itself a small fraction of the budget. The grid is accepted only if the
interpolated Z1 reproduces the reference code at every fine-cell midpoint to
1e-5 (PLAN 6) and kappa to 1e-4 relative; the build fails otherwise.
Measured 2026-10-18: bilinear on the coarse grid missed Z by 3e-4 and
biquadratic on it by 4.7e-5 (Ekofisk, 35 F, 1412 psia); this grid gives 6.6e-6.
kappa's bound is looser because it enters only through the expansibility
factor, where a 1e-4 relative error moves the flow by about 1e-7.

Writes outputs/app_table.json (read by tests/test_parity_meter.py too) and
site/meter-app.html.
Run:  python build_app.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

import model as M
from aga8lib import AGA8, NIST

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TABLE = HERE / "outputs" / "app_table.json"
APP = ROOT / "site" / "meter-app.html"
TEMPLATE = HERE / "app_template.html"
T_F = list(range(30, 131, 10))                # Jacobian grid, F
P_PSIA = list(range(50, 1501, 25))            # Jacobian grid, psia
T_F_FINE = list(range(30, 131, 5))            # Z1 and kappa grid
P_PSIA_FINE = list(range(50, 1501, 10))
MID_TOL, KAPPA_TOL = 1e-5, 1e-4


def table_for(aga, name):
    x = M.composition(name)
    Ts = [(t - 32) / 1.8 + 273.15 for t in T_F]
    Ps = [p * M.PSI for p in P_PSIA]
    Tf = [(t - 32) / 1.8 + 273.15 for t in T_F_FINE]
    Pf = [p * M.PSI for p in P_PSIA_FINE]
    lnZ = [[math.log(aga.z(T, P, x)) for P in Pf] for T in Tf]
    kap = [[aga.kappa(T, P, x) for P in Pf] for T in Tf]
    JZ1 = [None] * 21
    # one Jacobian call per grid point, all components at once
    grid_J = [[M.jacobian(aga, x, T, P) for P in Ps] for T in Ts]
    for c in range(21):
        if x[c] == 0 or M.COMP_U.get(NIST[c], 0) == 0:
            continue
        JZ1[c] = [[float(grid_J[i][j][1, c]) for j in range(len(Ps))] for i in range(len(Ts))]
    Jb = M.jacobian(aga, x, Ts[0], Ps[0])
    g = M.gas_props(aga, x, Ts[0], Ps[0])
    return {"name": name, "x": x.tolist(), "T": Ts, "p": Ps, "Tf": Tf, "pf": Pf,
            "lnZ1": lnZ, "kappa": kap, "JZ1": JZ1,
            "Zb": g["Zb"], "MW": g["MW"], "HN": g["HN"], "Jb": Jb.tolist(),
            "compU": [M.COMP_U.get(c, 0.0) / 100 for c in NIST]}


def interp(tab, key, T, P):
    Ts, Ps = tab["T"], tab["p"]
    i = min(max(0, np.searchsorted(Ts, T) - 1), len(Ts) - 2)
    j = min(max(0, np.searchsorted(Ps, P) - 1), len(Ps) - 2)
    u = (T - Ts[i]) / (Ts[i + 1] - Ts[i])
    v = (P - Ps[j]) / (Ps[j + 1] - Ps[j])
    g = tab[key]
    return ((1 - u) * (1 - v) * g[i][j] + u * (1 - v) * g[i + 1][j]
            + (1 - u) * v * g[i][j + 1] + u * v * g[i + 1][j + 1])


def _lag(xs, i, t):
    a, b, c = xs[i - 1], xs[i], xs[i + 1]
    return [(t - b) * (t - c) / ((a - b) * (a - c)), (t - a) * (t - c) / ((b - a) * (b - c)),
            (t - a) * (t - b) / ((c - a) * (c - b))]


def _nearest(xs, t):
    i = min(range(len(xs)), key=lambda k: abs(xs[k] - t))
    return min(max(i, 1), len(xs) - 2)


def quad(tab, key, T, P):
    """Biquadratic interpolation on the fine grid; engine.js's quad() is the same arithmetic."""
    Ts, Ps, g = tab["Tf"], tab["pf"], tab[key]
    if not (Ts[0] <= T <= Ts[-1] and Ps[0] <= P <= Ps[-1]):
        raise ValueError("outside the gas table")
    i, j = _nearest(Ts, T), _nearest(Ps, P)
    wt, wp = _lag(Ts, i, T), _lag(Ps, j, P)
    return sum(wt[a] * wp[b] * g[i - 1 + a][j - 1 + b] for a in range(3) for b in range(3))


def midpoint_error(aga, tab):
    x = np.array(tab["x"])
    worst_z = worst_k = 0.0
    for i in range(len(tab["Tf"]) - 1):
        for j in range(len(tab["pf"]) - 1):
            T = (tab["Tf"][i] + tab["Tf"][i + 1]) / 2
            P = (tab["pf"][j] + tab["pf"][j + 1]) / 2
            worst_z = max(worst_z, abs(math.exp(quad(tab, "lnZ1", T, P)) - aga.z(T, P, x)))
            worst_k = max(worst_k, abs(quad(tab, "kappa", T, P) / aga.kappa(T, P, x) - 1))
    return worst_z, worst_k


def main():
    # RETIRED FROM site/ 2026-10-23 (R3): site/meter.html and site/meter-app.html are redirect
    # stubs to lostgas.html, written by lostgas/redirects.py. Writing the old page or app back
    # would undo that; this script stays for the archive, and values() still feeds lostgas.html.
    raise SystemExit("meter: the page and the app were replaced by lostgas.html (R3); see lostgas/redirects.py")
    aga = AGA8()
    tables, fails = [], 0
    for name in M.GASES:
        tab = table_for(aga, name)
        ez, ek = midpoint_error(aga, tab)
        ok = ez < MID_TOL and ek < KAPPA_TOL
        fails += not ok
        print(f"  {'OK  ' if ok else 'FAIL'} {name}: worst midpoint error Z {ez:.1e}, kappa (relative) {ek:.1e}")
        tables.append(tab)
    TABLE.parent.mkdir(exist_ok=True)
    # The app opens on the page's own system and the first row of its table (C
    # independent at every meter). Its controls alone cannot express that system
    # (receipts at four operating points, deliveries 50/30/20 on two pipe sizes),
    # which is why the app once opened at 95 MMcf/d and 0.12% against the page's
    # 101 and 0.18% (Q2). tests/test_parity_meter.py check 4 holds them together.
    data = {"z_ref": M.z_ref(aga), "T_F": T_F, "p_psia": P_PSIA, "gases": tables,
            "page_system": [{"name": m.name, "role": m.role, "D": m.D, "beta": m.beta, "p1": m.p1,
                             "T1": m.T1, "span_dp": m.span_dp, "dp": m.dp, "share": m.share,
                             "taps": m.taps} for m in M.default_meters()],
            "page_row": {"key": "fC0", "C": 0.0, "cls": "beta"}}
    with open(TABLE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, separators=(",", ":"))
        f.write("\n")
    print(f"wrote {TABLE} ({TABLE.stat().st_size / 1024:.0f} kB)")
    if TEMPLATE.exists():
        payload = json.loads((HERE / "outputs" / "payload.json").read_text(encoding="utf-8"))
        t = TEMPLATE.read_text(encoding="utf-8")
        t = t.replace("/*ENGINE*/", (HERE / "engine.js").read_text(encoding="utf-8"))
        t = t.replace("/*TABLE*/null", json.dumps(data, separators=(",", ":")))
        from update_page import cents        # half up, as the page does
        t = t.replace("{{price_med}}", cents(payload["price"]["median"]))
        t = t.replace("{{price_months}}", f"{payload['price']['first']} to {payload['price']['last']}")
        left = sorted(set(__import__("re").findall(r"{{(\w+)}}", t)))
        if left:
            print(f"FAIL: template placeholders without a value: {left}")
            return 1
        with open(APP, "w", encoding="utf-8", newline="\n") as f:
            f.write(t)
        print(f"wrote {APP} ({APP.stat().st_size / 1024:.0f} kB)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
