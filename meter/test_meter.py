"""Tests for the meter model. Exit 0 when all pass, 1 otherwise.

    python test_meter.py                 all tests
    python test_meter.py --break NAME    one deliberate defect; the run MUST exit 1

Each break re-introduces the defect its test exists for (HANDOFF traps 17,
26): the run fails with a non-zero exit, not a line to read.

  stage1      the Stage 1 known-answer checks run here, and their own --break
              runs must exit 1 too (a check nobody has seen fail is a claim)
  gases       a transcription slip in one example-gas mole fraction
  zero        a residual error left on with every uncertainty set to zero
  averaging   the per-meter part drawn shared (f = 1) where it should be
              independent: total throughput no longer averages as N^-1/2
  relative    v1's error model (the plan review's finding 2): every shared
              error relative and identical at every meter. The span and Z
              non-cancellation tests must fail
  jacobian    the composition Jacobian's step taken in the wrong direction
              (sign flip): linearisation against exact evaluation must fail
  adaptive    7.9.4 with the plain spread across batches instead of the
              standard deviation of their average (the plan review's
              finding 1): the stopping test must not accept it
"""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

import model as M
from aga8lib import AGA8, NIST

HERE = Path(__file__).resolve().parent
BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
fails = []


def check(name, ok, detail):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def only(group, f=0.0):
    return [c for c in M.default_comps({group: f}) if c.group == group]


def receipts_only(n, beta=0.5, dp=25.0, f=None):
    """n identical receipt meters into one delivery meter sized to take them."""
    ms = [M.Meter(f"R{i}", "R", D=0.1023, beta=beta, p1=800 * M.PSI, T1=M.T_BASE, span_dp=50.0, dp=dp)
          for i in range(n)]
    D = 0.1023 * math.sqrt(n) * 1.05
    ms.append(M.Meter("D", "D", D=max(D, 0.1023), beta=beta, p1=800 * M.PSI, T1=M.T_BASE,
                      span_dp=50.0, share=1.0))
    return ms


# ------------------------------------------------------------------ stage 1
def t_stage1():
    for script in ("check_rhg.py", "check_z.py"):
        args = [sys.executable, str(HERE / "checks" / script)]
        clean = subprocess.run(args, capture_output=True, text=True).returncode
        broke = subprocess.run(args + ["--break"], capture_output=True, text=True).returncode
        if BREAK == "stage1":
            broke = 0          # pretend the check's own break went unnoticed
        check(f"stage 1 {script}", clean == 0 and broke == 1, f"clean exit {clean}, --break exit {broke}")


# ------------------------------------------------------------------ gases
def t_gases():
    import xlrd
    path = HERE / "data" / "raw" / "aga8_tables.xls"
    s = xlrd.open_workbook(str(path)).sheet_by_name("Tables")
    rows = {"Methane": "methane", "Nitrogen": "nitrogen", "CO2": "CO2", "Ethane": "ethane",
            "Propane": "propane", "i-Butane": "ibutane", "n-Butane": "butane",
            "i-Pentane": "ipentane", "n-Pentane": "pentane", "n-Hexane": "hexane"}
    names = ["Gulf Coast", "Amarillo", "Ekofisk", "High N2", "High CO2"]
    gases = {k: dict(v) for k, v in M.GASES.items()}
    if BREAK == "gases":
        gases["Amarillo"]["ethane"] = 4.5297
    worst = 0.0
    for r in range(7, 17):
        comp = rows[s.cell(r, 1).value]
        for k, n in enumerate(names):
            worst = max(worst, abs(float(s.cell(r, 3 + k).value) - gases[n][comp]))
    check("example gases equal NIST Tables.xls", worst == 0.0, f"worst difference {worst:g} mol%")


# ------------------------------------------------------------------ zero
def t_zero(states, x):
    rng = np.random.default_rng(7)
    scale = 1e-6 if BREAK == "zero" else 0.0
    o = M.simulate(states, x, M.default_comps({"C": 0.5}), 200, rng, scale=scale)
    worst = max(float(np.abs(o[k]).max()) for k in ("imb_v", "imb_e"))
    check("zero uncertainty gives zero imbalance (volume, energy)", worst < 1e-12, f"worst |I| {worst:.2e}")


# ------------------------------------------------------------------ averaging
def t_averaging(aga):
    Ns = [1, 4, 16, 64]
    for f, want in ((0.0, -0.5), (1.0, 0.0)):
        f_used = 1.0 if (BREAK == "averaging" and f == 0.0) else f
        us = []
        for n in Ns:
            st, x = M.build_system(receipts_only(n), aga=aga)
            o = M.simulate(st, x, only("C", f_used), 20000, np.random.default_rng(n))
            us.append(o["rec_v"].std(ddof=1))
        slope = np.polyfit(np.log(Ns), np.log(us), 1)[0]
        check(f"total throughput vs N, C only, f = {f:g}", abs(slope - want) < 0.03,
              f"log-log slope {slope:+.3f} (want {want:+.1f}); u at N=1 {us[0]:.4%}, N=64 {us[-1]:.4%}")


# ------------------------------------------------------------------ cancellation
def t_cancellation(states, x):
    rel = BREAK == "relative"
    K = 20000
    # (a) a shared relative C error, all meters in one class, cancels to second order. Not
    # exactly: the error moves each meter's computed flow, so its Re_D, so RHG's C, by an
    # amount that depends on that meter's Re_D (measured: max |I| 5.7e-7 against u_C 2.5e-3)
    o = M.simulate(states, x, only("C", 1.0), K, np.random.default_rng(1), relative_only=rel)
    worst = float(np.abs(o["imb_v"]).max())
    check("shared C error, one class, cancels in the imbalance (to second order)",
          worst < 1e-3 * float(M.cd_u(0.5)), f"max |I| {worst:.2e}, bound {1e-3 * float(M.cd_u(0.5)):.1e}")

    # (a2) the same shared error grouped by role (receipts share one draw, deliveries
    # another): two independent common errors on equal totals, so u(I) = sqrt(2) u_C
    comps = [c for c in M.default_comps({"C": 1.0}, c_class="role") if c.group == "C"]
    if rel:
        comps = [c for c in M.default_comps({"C": 1.0}) if c.group == "C"]   # v1 had no grouping
    o = M.simulate(states, x, comps, K, np.random.default_rng(4), relative_only=rel)
    got, expect = o["imb_v"].std(ddof=1), math.sqrt(2) * float(M.cd_u(0.5))
    check("shared C error grouped by role does NOT cancel; u(I) = sqrt(2) u_C",
          abs(got / expect - 1) < 0.03, f"MC u(I) {got:.4e} vs analytic {expect:.4e}")

    vb = np.array([s.qm / (s.MW * 1e-3) * s.Zb * M.R_GERG * M.T_BASE / (M.P_BASE * 1e3) for s in states])
    role = np.array([1.0 if s.m.role == "R" else -1.0 for s in states])
    through = vb[role > 0].sum()

    # (b) a shared dp reference offset (% of span): effect span/dp at each meter, half in flow
    comps = [c for c in M.default_comps({"dp": 1.0}) if c.name == "dp reference"]
    o = M.simulate(states, x, comps, K, np.random.default_rng(2), relative_only=rel)
    u_dp = np.array([M._scale(comps[0], s) for s in states])
    # redrawn each of the period's calibration intervals, so the period mean divides by sqrt(4)
    expect = abs((role * vb * 0.5 * u_dp / np.array([s.m.dp for s in states])).sum()) / through / 2.0
    got = o["imb_v"].std(ddof=1)
    check("shared dp offset does NOT cancel; size as the span/dp algebra says",
          abs(got / expect - 1) < 0.03, f"MC u(I) {got:.3e} vs analytic {expect:.3e}")

    # (c) the Z equation's error, scaled by 1 - Z, does not cancel across pressures
    comps = [c for c in M.default_comps() if c.name == "Z equation"]
    o = M.simulate(states, x, comps, K, np.random.default_rng(3), relative_only=rel)
    a = M.Z_U_REF / (1 - M.z_ref())
    Z1 = np.array([s.Z1 for s in states])
    Zb = np.array([s.Zb for s in states])
    expect = abs((role * vb * a * ((1 - Zb) - 0.5 * (1 - Z1))).sum()) / through
    got = o["imb_v"].std(ddof=1)
    check("Z-equation error does NOT cancel across pressures; size as the (1 - Z) algebra says",
          abs(got / expect - 1) < 0.03, f"MC u(I) {got:.3e} vs analytic {expect:.3e}")


# ------------------------------------------------------------------ jacobian
def t_jacobian(aga, states, x):
    s = states[0]
    J = -s.J if BREAK == "jacobian" else s.J
    rng = np.random.default_rng(11)
    cu = np.array([M.COMP_U.get(c, 0.0) / 100 for c in NIST])
    errs, terms = [], []
    for _ in range(200):
        e = rng.standard_normal(21) * cu
        xx = x * (1 + e)
        xx /= xx.sum()
        exact = np.array([math.log(aga.molar_mass(xx)), math.log(aga.z(s.m.T1, s.m.p1, xx)),
                          math.log(aga.z(M.T_BASE, M.P_BASE, xx)), math.log(aga.hv(xx))])
        base = np.array([math.log(s.MW), math.log(s.Z1), math.log(s.Zb), math.log(s.HN)])
        lin = J @ e
        errs.append(np.abs(exact - base - lin))
        terms.append(np.abs(exact - base))
    err = np.max(errs, axis=0)
    term = np.std(terms, axis=0)
    ratio = float(np.max(err / term))
    check("composition Jacobian vs exact reference code, 200 draws", ratio < 1e-2,
          f"worst linearisation error / spread of the term {ratio:.2e} (MW, Z1, Zb, HN)")


# ------------------------------------------------------------------ adaptive
def t_adaptive(states, x):
    import inspect
    import textwrap
    adaptive = M.adaptive
    if BREAK == "adaptive":
        # mutate the stopping rule in memory: the plain spread across batches in place of
        # the standard deviation of their average
        src = textwrap.dedent(inspect.getsource(M.adaptive))
        old = "/ (h * (h - 1)))"
        assert src.count(old) == 1, "the mutation did not find its target"
        ns = dict(vars(M))
        exec(src.replace(old, "/ (h - 1))"), ns)
        adaptive = ns["adaptive"]
    # Known answer: normal data with u = 1.5, ndig = 2, so delta = 0.05 (1.5 = 15 x 10^-1).
    # Per batch of 1e4 the 95% endpoints scatter by about 0.04 (1.5 x 0.0267), so twice
    # the SD of their AVERAGE falls under delta within a few batches; twice the plain
    # spread (0.08) never does.
    # JCGM 101 7.9.2's own examples: 0.000 35 g at ndig 2 -> 0.000 005 g; at ndig 1 (0.000 4 g)
    # -> 0.000 05 g; 2 K at ndig 1 -> 0.5 K.
    ex = [(0.00035, 2, 0.000005), (0.0004, 1, 0.00005), (2.0, 1, 0.5)]
    got = [M.tolerance(u, n) for u, n, _ in ex]
    check("7.9.2 numerical tolerance, the standard's three examples",
          all(abs(g - w) < 1e-15 for g, (_, _, w) in zip(got, ex)), f"got {got}")
    rng = np.random.default_rng(4)
    try:
        r = adaptive(lambda K: {"y": 1.5 * rng.standard_normal(K)}, ["y"], ndig=2, max_batches=400)["y"]
        ok = r["batches"] < 400 and abs(r["mean"]) < r["delta"] and abs(r["u"] - 1.5) < r["delta"]
        detail = f"stopped at {r['batches']} batches; mean {r['mean']:+.4f}, u {r['u']:.4f}, delta {r['delta']}"
    except RuntimeError as e:
        ok, detail = False, str(e)
    check("7.9.4 on normal data (known u = 1.5)", ok, detail)
    if BREAK == "adaptive":
        return
    comps = M.default_comps({"C": 0.5})
    rng = np.random.default_rng(5)
    run = lambda K: M.simulate(states, x, comps, K, rng)   # noqa: E731
    r = M.adaptive(run, ["imb_v", "imb_e"])["imb_v"]
    check("7.9.4 stabilises on the default system", r["batches"] < 400,
          f"{r['batches']} batches, {r['trials']:,} trials, u(I) {r['u']:.4e}, delta {r['delta']:.1e}")
    rng = np.random.default_rng(6)
    r2 = M.adaptive(run, ["imb_v", "imb_e"], K=2 * 10 ** 4)["imb_v"]
    moved = max(abs(r2[s_] - r[s_]) for s_ in ("mean", "u", "low", "high"))
    check("doubling K moves no figure by more than its tolerance", moved <= r["delta"],
          f"largest move {moved:.1e} vs delta {r['delta']:.1e}")


# ------------------------------------------------------------------ viscosity
def t_mu(states, x):
    comps = M.default_comps({"C": 0.5})
    us = []
    for mu in (M.MU * 0.5, M.MU, M.MU * 1.5):
        o = M.simulate(states, x, comps, 20000, np.random.default_rng(9), mu=mu)   # same draws
        us.append(o["imb_v"].std(ddof=1))
    delta = M.tolerance(us[1])
    moved = max(abs(us[0] - us[1]), abs(us[2] - us[1]))
    check("viscosity +/-50% moves u(I) less than its printed precision", moved < delta,
          f"move {moved:.1e} vs delta {delta:.1e} (same random draws)")


def main():
    print(f"test_meter{'  [--break ' + BREAK + ']' if BREAK else ''}")
    aga = AGA8()
    states, x = M.build_system(M.default_meters(), aga=aga)
    tests = {"stage1": t_stage1, "gases": t_gases, "zero": lambda: t_zero(states, x),
             "averaging": lambda: t_averaging(aga), "relative": lambda: t_cancellation(states, x),
             "jacobian": lambda: t_jacobian(aga, states, x), "adaptive": lambda: t_adaptive(states, x),
             "mu": lambda: t_mu(states, x)}
    if BREAK and BREAK not in tests:
        print(f"unknown break {BREAK}; one of {list(tests)}")
        return 2
    for name, t in tests.items():
        if BREAK and name != BREAK:
            continue
        t()
    print(f"{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
