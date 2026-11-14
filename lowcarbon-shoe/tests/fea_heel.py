"""Simulated midsole compression by finite element analysis (scikit-fem).

Model: axisymmetric layered disc (outsole / midsole / sockliner) on a rigid floor,
compressed by a rigid flat circular striker. Each foam layer is non-linear elastic:
the secant modulus of every element is set from its own compressive strain on the
material's published stress-strain curve (materials.py) and the solve is repeated
until the striker force converges (deformation-theory secant iteration). Small-
strain kinematics: an approximation at 50-70 % strain, stated in RESULTS.md.

Cases (all SIMULATED, none physical):
  drop    ASTM F1976-style impact: 8.5 kg striker, 5 J at contact, 45 mm flat
          striker (the F1614 striker size; F1976's is not in the open scope).
          Peak force from the energy balance 5 J + m g d = integral F dd.
  heel    runner heel strike: 70 kg, 1.12 body weights on the heel (Pedar data,
          3.33 m/s rearfoot strikers, research/w1-11), rigid 28 mm-radius heel.
  fore    forefoot: 1.75 body weights over a 40 mm-radius disc.
Self-checks: (1) a = R and nu = 0 must reproduce the 1-D column force
sigma(d/H) * pi R^2; (2) doubling a foam's stress must raise the drop peak force.

Run: python fea_heel.py  -> results/fea.json
"""
import json
import math
import os
import sys

import numpy as np
from skfem import (Basis, BilinearForm, ElementTriP0, ElementTriP2, ElementVector,
                   MeshTri, asm, condense, solve)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import materials as M  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.81
BODY_KG = 70.0


@BilinearForm
def axi(u, v, w):
    r = w.x[0]
    E, nu = w["E"], w["nu"]
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    eu = [u.grad[0][0], u.grad[1][1], u.value[0] / r, u.grad[0][1] + u.grad[1][0]]
    ev = [v.grad[0][0], v.grad[1][1], v.value[0] / r, v.grad[0][1] + v.grad[1][0]]
    tr = eu[0] + eu[1] + eu[2]
    s = [lam * tr + 2 * mu * eu[0], lam * tr + 2 * mu * eu[1], lam * tr + 2 * mu * eu[2], mu * eu[3]]
    return (s[0] * ev[0] + s[1] * ev[1] + s[2] * ev[2] + s[3] * ev[3]) * r


def grid(R, a, layers, nr=28, nz_per_mm=1.0):
    rr = np.unique(np.concatenate([np.linspace(0, a, int(nr * a / R) + 2),
                                   a + (R - a) * np.linspace(0, 1, max(4, int(nr * (R - a) / R)) + 1) ** 1.3,
                                   [a * 0.97, a * 1.03]]))
    rr = rr[rr <= R + 1e-9]
    zs, z = [0.0], 0.0
    for t, _ in layers:
        n = max(2, int(round(t * nz_per_mm)))
        zs.extend(list(z + t * np.linspace(0, 1, n + 1)[1:]))
        z += t
    return MeshTri.init_tensor(rr, np.array(zs)), z


class Model:
    """layers: list of (thickness_mm, material) bottom to top. material is
    ('lin', E, nu) or ('foam', stress_fn, nu)."""

    def __init__(self, R, a, layers, nr=28, nz_per_mm=1.0):
        self.mesh, self.H = grid(R, a, layers, nr, nz_per_mm)
        self.R, self.a, self.layers = R, a, layers
        self.ib = Basis(self.mesh, ElementVector(ElementTriP2()))
        self.b0 = Basis(self.mesh, ElementTriP0())
        zc = self.mesh.p[1, self.mesh.t].mean(axis=0)
        self.layer_of = np.zeros(self.mesh.t.shape[1], int)
        z = 0.0
        for i, (t, _) in enumerate(layers):
            self.layer_of[(zc >= z - 1e-9) & (zc < z + t + 1e-9)] = i
            z += t
        nq = self.ib.X.shape[1]
        self.nq = nq
        x = self.ib.doflocs
        self.dof_r = self.ib.nodal_dofs[0] if False else None
        dr = np.arange(self.ib.N)[0::2]
        dz = np.arange(self.ib.N)[1::2]
        tol = 1e-9
        floor = np.abs(x[1]) < tol
        top = np.abs(x[1] - self.H) < tol
        axis = np.abs(x[0]) < tol
        punch = top & (x[0] <= a + tol)
        self.fix = np.unique(np.concatenate([
            np.where(floor)[0],                                  # bonded to the floor
            np.where(punch)[0],                                  # bonded to the striker
            np.where(axis & (np.arange(self.ib.N) % 2 == 0))[0],  # u_r = 0 on the axis
        ]))
        self.punch_z = np.where(punch & (np.arange(self.ib.N) % 2 == 1))[0]
        assert np.all(x[1][dz] == x[1][dz])

    def fields(self, eps_c):
        E = np.zeros(self.mesh.t.shape[1])
        nu = np.zeros_like(E)
        for i, (t, m) in enumerate(self.layers):
            sel = self.layer_of == i
            if m[0] == "lin":
                E[sel], nu[sel] = m[1], m[2]
            else:
                E[sel] = M.secant_modulus(m[1], eps_c[sel])
                nu[sel] = m[2]
        return np.repeat(E[:, None], self.nq, 1), np.repeat(nu[:, None], self.nq, 1)

    def solve(self, delta, eps0=None, iters=40, tol=2e-3):
        eps_c = np.zeros(self.mesh.t.shape[1]) if eps0 is None else eps0.copy()
        F_old = None
        for it in range(iters):
            E, nu = self.fields(eps_c)
            K = asm(axi, self.ib, E=E, nu=nu)
            x = np.zeros(self.ib.N)
            x[self.punch_z] = -delta
            u = solve(*condense(K, x=x, D=self.fix))
            F = -2 * math.pi * (K @ u)[self.punch_z].sum()
            uf = self.ib.interpolate(u)
            ezz = uf.grad[1][1].mean(axis=1)
            new = np.clip(-ezz, 0.0, 0.92)
            eps_c = 0.5 * eps_c + 0.5 * new if it > 2 else new
            if F_old is not None and abs(F - F_old) <= tol * max(abs(F), 1.0):
                break
            F_old = F
        self.last_u, self.last_eps = u, eps_c
        return F, eps_c, it + 1

    def stresses(self, u):
        """Element-mean von Mises stress (MPa) at the last state."""
        E, nu = self.fields(self.last_eps)
        E, nu = E[:, 0], nu[:, 0]
        uf = self.ib.interpolate(u)
        r = self.ib.global_coordinates().value[0]
        err = uf.grad[0][0].mean(1)
        ezz = uf.grad[1][1].mean(1)
        ett = (uf.value[0] / r).mean(1)
        grz = (uf.grad[0][1] + uf.grad[1][0]).mean(1)
        lam = E * nu / ((1 + nu) * (1 - 2 * nu))
        mu = E / (2 * (1 + nu))
        tr = err + ezz + ett
        srr, szz, stt, srz = lam * tr + 2 * mu * err, lam * tr + 2 * mu * ezz, lam * tr + 2 * mu * ett, mu * grz
        vm = np.sqrt(0.5 * ((srr - szz) ** 2 + (szz - stt) ** 2 + (stt - srr) ** 2) + 3 * srz ** 2)
        return vm, szz

    def curve(self, d_max, n=24):
        ds = np.linspace(0, d_max, n + 1)
        Fs, eps = [0.0], None
        for d in ds[1:]:
            F, eps, _ = self.solve(d, eps)
            Fs.append(F)
        return ds, np.array(Fs)

    def load_to(self, F_target, d_hi):
        lo, hi = 0.0, d_hi
        F_hi, _, _ = self.solve(hi)
        while F_hi < F_target:
            hi *= 1.5
            F_hi, _, _ = self.solve(hi)
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            F, eps, _ = self.solve(mid)
            if abs(F - F_target) < 0.005 * F_target:
                break
            lo, hi = (mid, hi) if F < F_target else (lo, mid)
        vm, szz = self.stresses(self.last_u)
        return mid, F, eps, vm, szz


def drop_peak(ds, Fs, energy_J=5.0, mass=8.5):
    W = np.concatenate([[0], np.cumsum(0.5 * (Fs[1:] + Fs[:-1]) * np.diff(ds))]) / 1000.0  # J
    need = energy_J + mass * G * ds / 1000.0
    idx = np.where(W >= need)[0]
    if len(idx) == 0:
        return None, None
    i = idx[0]
    f = (need[i - 1] - W[i - 1]) / ((W[i] - W[i - 1]) - (need[i] - need[i - 1]))
    d = ds[i - 1] + f * (ds[i] - ds[i - 1])
    return float(np.interp(d, ds, Fs)), float(d)


LC1_DENSITY = 200.0  # kg/m3, design value (lca/params.py etpu_density); Aimar's eTPU curve scaled by (rho/240)^2
SHOES = {
    "baseline": dict(outsole=(3.0, ("lin", 5.0, 0.45)),
                     foam=lambda e: M.foam_stress("EVA_F1", e), nu=0.20,
                     label="Baseline: EVA foam midsole, carbon-rubber outsole"),
    "lc1": dict(outsole=(1.5, ("lin", 25.0, 0.45)),
                foam=lambda e: M.foam_stress("ETPU_F3", e, density=LC1_DENSITY), nu=0.25,
                label="LC-1: expanded-TPU midsole at 200 kg/m3, 1.5 mm solid TPU outsole skin"),
}
HEEL_MID, FORE_MID, SOCK = 26.0, 17.0, 4.0


def layers_for(shoe, mid):
    s = SHOES[shoe]
    return [s["outsole"], (mid, ("foam", s["foam"], s["nu"])), (SOCK, ("foam", s["foam"], s["nu"]))]


def self_check_1d():
    """a = R, nu = 0, one foam layer: FE force must equal sigma(d/H) pi R^2."""
    fn = lambda e: M.foam_stress("EVA_F1", e)  # noqa: E731
    m = Model(20.0, 20.0, [(20.0, ("foam", fn, 0.0))], nr=10)
    out = []
    for d in (4.0, 8.0, 12.0):
        F, _, _ = m.solve(d)
        F1 = float(fn(np.array([d / 20.0]))[0]) * math.pi * 20.0 ** 2
        out.append(dict(delta_mm=d, fe_N=round(F, 1), column_N=round(F1, 1), err_pct=round(100 * (F / F1 - 1), 2)))
    return out


def lattice_scan(target_N, Es, n=2.0, C1=1.0, phis=None):
    """Printed TPU gyroid (Gibson-Ashby model) in place of LC-1's foam: simulated 5 J
    drop peak for a grid of relative densities phi. The peak is U-shaped in phi:
    too sparse and the lattice bottoms out (no peak found within 26 mm, reported
    as None), too dense and it is stiff. Reports the phi range within 15 % of
    target_N. (A bisection was tried first and mis-read bottoming-out as
    stiffness; a scan shows both sides.)"""
    phis = phis if phis is not None else [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    rows = []
    for phi in phis:
        fn = lambda e, p=phi: M.lattice_stress(e, p, Es=Es, C1=C1, n=n)  # noqa: E731
        m = Model(38.0, 22.5, [SHOES["lc1"]["outsole"], (HEEL_MID, ("foam", fn, 0.05)),
                               (SOCK, ("foam", lambda e: M.foam_stress("ETPU_F3", e, density=LC1_DENSITY), 0.25))],
                  nr=16, nz_per_mm=0.6)
        ds, Fs = m.curve(26.0, 13)
        pk, d = drop_peak(ds, Fs)
        rows.append(dict(phi=phi, drop_peak_N=None if pk is None else round(pk, 0),
                         within_15pct=bool(pk is not None and abs(pk / target_N - 1) <= 0.15)))
    ok = [r["phi"] for r in rows if r["within_15pct"]]
    return dict(Es_MPa=Es, n=n, C1=C1, scan=rows, phi_within_15pct=[min(ok), max(ok)] if ok else None)


def main():
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    res = dict(method=__doc__.strip().splitlines()[0], body_mass_kg=BODY_KG,
               rate_factor=M.RATE, self_check_1d=self_check_1d(), cases={})
    curves = {}
    for shoe in SHOES:
        m = Model(38.0, 22.5, layers_for(shoe, HEEL_MID))
        ds, Fs = m.curve(24.0, 24)
        Fp, dp = drop_peak(ds, Fs)
        curves[shoe] = (ds, Fs)
        mh = Model(38.0, 28.0, layers_for(shoe, HEEL_MID))
        d_h, F_h, eps_h, vm_h, szz_h = mh.load_to(1.12 * BODY_KG * G, 8.0)
        foam = mh.layer_of >= 1
        mf = Model(50.0, 40.0, layers_for(shoe, FORE_MID))
        d_f, F_f, eps_f, vm_f, _ = mf.load_to(1.75 * BODY_KG * G, 5.0)
        foamf = mf.layer_of >= 1
        res["cases"][shoe] = dict(
            label=SHOES[shoe]["label"],
            drop_5J=dict(peak_force_N=round(Fp, 0), peak_g=round(Fp / (8.5 * G), 1), deflection_mm=round(dp, 2)),
            heel_1p12BW=dict(load_N=round(F_h, 0), deflection_mm=round(d_h, 2),
                             max_foam_strain=round(float(eps_h[foam].max()), 3),
                             max_foam_vonmises_MPa=round(float(vm_h[foam].max()), 3),
                             max_outsole_vonmises_MPa=round(float(vm_h[~foam].max()), 3)),
            forefoot_1p75BW=dict(load_N=round(F_f, 0), deflection_mm=round(d_f, 2),
                                 max_foam_strain=round(float(eps_f[foamf].max()), 3),
                                 max_foam_vonmises_MPa=round(float(vm_f[foamf].max()), 3)),
            curve=dict(delta_mm=[round(x, 2) for x in ds], force_N=[round(x, 1) for x in Fs]),
        )
        print(shoe, res["cases"][shoe]["drop_5J"], res["cases"][shoe]["heel_1p12BW"], res["cases"][shoe]["forefoot_1p75BW"])
    b, l = res["cases"]["baseline"]["drop_5J"]["peak_force_N"], res["cases"]["lc1"]["drop_5J"]["peak_force_N"]
    res["lc1_vs_baseline_drop_pct"] = round(100 * (l / b - 1), 1)
    # check 2: a stiffer foam must give a higher peak (instrument moves with its input)
    m2 = Model(38.0, 22.5, [SHOES["baseline"]["outsole"],
                            (HEEL_MID, ("foam", lambda e: 2 * M.foam_stress("EVA_F1", e), 0.2)),
                            (SOCK, ("foam", lambda e: 2 * M.foam_stress("EVA_F1", e), 0.2))])
    ds2, Fs2 = m2.curve(24.0, 24)
    res["check_stiffer_foam_peak_N"] = round(drop_peak(ds2, Fs2)[0], 0)
    sweep = []
    for rate in (1.0, 1.5, 2.0, 3.7, 5.0):
        for dens in (190.0, 200.0, 220.0, 240.0):
            pk = {}
            for shoe, fn in (("baseline", lambda e, r=rate: M.foam_stress("EVA_F1", e, rate=r)),
                             ("lc1", lambda e, r=rate, d=dens: M.foam_stress("ETPU_F3", e, density=d, rate=r))):
                if shoe == "baseline" and dens != 190.0:
                    pk[shoe] = sweep[-1]["baseline_N"] if sweep and sweep[-1]["rate"] == rate else None
                    if pk[shoe] is not None:
                        continue
                nu = SHOES[shoe]["nu"]
                m = Model(38.0, 22.5, [SHOES[shoe]["outsole"], (HEEL_MID, ("foam", fn, nu)), (SOCK, ("foam", fn, nu))],
                          nr=20, nz_per_mm=0.8)
                ds, Fs = m.curve(26.0, 20)
                pk[shoe] = drop_peak(ds, Fs)[0]
            sweep.append(dict(rate=rate, etpu_density=dens, baseline_N=round(pk["baseline"], 0), lc1_N=round(pk["lc1"], 0),
                              diff_pct=round(100 * (pk["lc1"] / pk["baseline"] - 1), 1)))
            print(sweep[-1])
    res["t4_sweep"] = sweep
    res["published_F1976_5J_range_N"] = [809, 1259]
    res["published_F1976_source"] = ("Pisciotta & Shorten, F1976 at 5 J, 9.7-15.1 g, as reported by Fuss 2025; "
                                     "research/w2-08-fea-inputs.md item 8")
    with open(os.path.join(HERE, "results", "fea.json"), "w", newline="\n") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "cases"}, indent=1))


def main_lattice():
    """Home-print lattice: relative density that matches the baseline drop peak,
    for solid TPU modulus 8 / 14.5 / 30 MPa (research/w2-08: published 8-85 MPa).
    Coarser mesh than main(); writes results/fea_lattice.json."""
    with open(os.path.join(HERE, "results", "fea.json")) as f:
        b = json.load(f)["cases"]["baseline"]["drop_5J"]["peak_force_N"]
    out = dict(target_peak_N=b, model="Gibson-Ashby open-cell elastomer (materials.lattice_stress), C1 = 1, n = 2",
               rows=[lattice_scan(b, Es) for Es in (8.0, 14.5, 30.0)])
    with open(os.path.join(HERE, "results", "fea_lattice.json"), "w", newline="\n") as f:
        json.dump(out, f, indent=1)
    print(out)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "lattice":
        main_lattice()
    else:
        main()
