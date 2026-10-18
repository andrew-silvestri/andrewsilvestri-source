"""What a gas meter's error is worth: orifice meters, a system of them, and Monte Carlo.

The meter equation is ISO 5167-2 with the Reader-Harris/Gallagher discharge
coefficient (`rhg` below, checked against `fluids` in checks/check_rhg.py),
Z and kappa from NIST's GERG-2008 and the heating value from NIST's GrossHv
(aga8lib.py). Uncertainty is propagated by Monte Carlo after JCGM 101:2008,
with the adaptive stopping rule of its 7.9.4.

The design and every default's source are in 03 RESEARCH/meter/PLAN.md;
SOURCES below repeats each default's origin beside the number so this file
can be read alone. Nothing here comes from any company's data: the system is
synthetic and labelled so on the page.

How an error is drawn (PLAN 2). Each error component k has a natural unit (a
fraction of transmitter span, kelvin, a relative error) and a shared
fraction f_k in [0, 1]. For meter i,

    e_ik = u_k * ( sqrt(f_k) * z_k(class of i) + sqrt(1 - f_k) * w_ik )

with z drawn once per class (or once for every meter) and w per meter; z and
w are unit-variance normal or rectangular as the source states. The error is
converted to its effect at each meter in that meter's own units, so a shared
cause need not cancel between meters that sit at different points of their
spans or pressures. That conversion is the reason a shared error can survive
in an imbalance at all: with every error relative, the exponents of the meter
equation are fixed and a shared error cancels by construction (the plan
review's finding 2; `--break relative` in test_meter.py restores that form).
"""
import math
from dataclasses import dataclass, field, replace

import numpy as np

from aga8lib import AGA8, NIST, R_GERG

# ---------------------------------------------------------------- constants
PSI = 6.894757293168361          # kPa per psi
P_BASE = 14.73 * PSI             # kPa, 14.73 psia, the US base used here
T_BASE = (60.0 - 32.0) / 1.8 + 273.15   # K, 60 F
MU = 1.1e-5                      # Pa s, ASSUMPTION; only Re_D uses it (test: +/-50%)
DAYS = 365.0

# The five AGA8 example gases, mole percent, from NIST AGA8 TESTDATA/Tables.xls
# rows 8-17 (test_meter.py checks these against the fetched workbook).
GASES = {
    "Gulf Coast": {"methane": 96.5222, "nitrogen": 0.2595, "CO2": 0.5956, "ethane": 1.8186,
                   "propane": 0.4596, "ibutane": 0.0977, "butane": 0.1007, "ipentane": 0.0473,
                   "pentane": 0.0324, "hexane": 0.0664},
    "Amarillo": {"methane": 90.6724, "nitrogen": 3.1284, "CO2": 0.4676, "ethane": 4.5279,
                 "propane": 0.828, "ibutane": 0.1037, "butane": 0.1563, "ipentane": 0.0321,
                 "pentane": 0.0443, "hexane": 0.0393},
    "Ekofisk": {"methane": 85.9063, "nitrogen": 1.0068, "CO2": 1.4954, "ethane": 8.4919,
                "propane": 2.3015, "ibutane": 0.3486, "butane": 0.3506, "ipentane": 0.0509,
                "pentane": 0.048, "hexane": 0.0},
    "High N2": {"methane": 81.441, "nitrogen": 13.465, "CO2": 0.985, "ethane": 3.3,
                "propane": 0.605, "ibutane": 0.1, "butane": 0.104, "ipentane": 0.0,
                "pentane": 0.0, "hexane": 0.0},
    "High CO2": {"methane": 81.212, "nitrogen": 5.702, "CO2": 7.585, "ethane": 4.303,
                 "propane": 0.895, "ibutane": 0.151, "butane": 0.152, "ipentane": 0.0,
                 "pentane": 0.0, "hexane": 0.0},
}

# Standard relative uncertainty of each measured mole fraction, percent (k = 1):
# Sutan 2012 (NSFMW), Table 9 "Combined Relative Uncertainty", an EXAMPLE budget
# for one GC; its expanded values in Table 10 are exactly twice these. Its
# neo-pentane row has no component here. Components it does not list get none.
COMP_U = {"methane": 0.0412, "nitrogen": 1.0534, "CO2": 0.3593, "ethane": 0.3647,
          "propane": 0.2738, "ibutane": 0.5590, "butane": 0.4063, "ipentane": 0.7403,
          "pentane": 0.9001, "hexane": 1.4977}

# Transmitter figures, Yokogawa EJX110A (dp, M capsule, URL 100 kPa) and
# EJX510A (absolute pressure) general specifications.
DP_REF = 0.0004                  # +/-0.04% of span, reference accuracy
DP_AMB_SPAN, DP_AMB_URL = 0.0004, 0.00009   # +/-(0.04% span + 0.009% URL) per 28 C
DP_URL = 100.0                   # kPa
DP_STATIC = 0.00075              # +/-0.075% of span per 6.9 MPa (1000 psi), a span (gain) effect
P_REF = 0.0004                   # +/-0.04% of span
# Temperature: IEC 60751 class A via GHI; Rosemount 3144P; Ingram (DNV GL) 2014.
T_SENSOR = (0.15, 0.002)         # +/-(0.15 + 0.002 |t|) C
T_XMTR = 0.12                    # +/-0.12 C
T_INSTALL = 0.5                  # +/-0.5 C
D_BORE = 0.0005                  # +/-0.05% (ISO 5167-2 5.1.8.3 roundness limit, used as a bound: ASSUMPTION)
D_PIPE = 0.0025                  # +/-0.25%, ASSUMPTION (no open figure)
Z_U_REF = 0.0005                 # 0.1% gas-region density (GERG-2008 authors) taken as k = 2: ASSUMPTION
SQ3 = math.sqrt(3.0)


def cd_u(beta):
    """Standard (k = 1) relative uncertainty of C: ISO 5167-2 as quoted by Emerson, Re_D > 1e4.
    0.5% for beta <= 0.6, (1.667 beta - 0.5)% above; expanded at k = 2, so halved."""
    beta = np.asarray(beta, float)
    return np.where(beta <= 0.6, 0.005, (1.667 * beta - 0.5) / 100.0) / 2.0


# ---------------------------------------------------------------- the meter equation
def rhg(beta, D, Re, L1, L2):
    """Reader-Harris/Gallagher C, ISO 5167-2 form (equal to fluids to 1e-16, check_rhg.py)."""
    A = (19000.0 * beta / Re) ** 0.8
    M2 = 2.0 * L2 / (1.0 - beta)
    b4 = beta ** 4
    C = (0.5961 + 0.0261 * beta ** 2 - 0.216 * b4 * b4
         + 0.000521 * (1e6 * beta / Re) ** 0.7
         + (0.0188 + 0.0063 * A) * beta ** 3.5 * (1e6 / Re) ** 0.3
         + (0.043 + 0.080 * np.exp(-10 * L1) - 0.123 * np.exp(-7 * L1)) * (1 - 0.11 * A) * b4 / (1 - b4)
         - 0.031 * (M2 - 0.8 * M2 ** 1.1) * beta ** 1.3)
    small = D < 0.07112
    return C + np.where(small, 0.011 * (0.75 - beta) * (2.8 - D / 0.0254), 0.0)


def taps_L(taps, D):
    if taps == "flange":
        return 0.0254 / D, 0.0254 / D
    if taps == "corner":
        return 0.0, 0.0
    if taps == "D":
        return 1.0, 0.47
    raise ValueError(taps)


def mass_flow(d, D, dp, p1, T1, MW, Z1, kappa, L1, L2, c_err=0.0, mu=MU, iters=60):
    """Mass flow, kg/s. d, D m; dp, p1 kPa; T1 K; MW g/mol. Arrays broadcast.
    C is iterated with Re_D to 1e-12. c_err multiplies C (the equation's error)."""
    beta = d / D
    rho1 = p1 * 1e3 * MW * 1e-3 / (Z1 * R_GERG * T1)
    eps = 1.0 - (0.351 + 0.256 * beta ** 4 + 0.93 * beta ** 8) * (1.0 - ((p1 - dp) / p1) ** (1.0 / kappa))
    k = (np.pi / 4.0) * d * d * eps * np.sqrt(2.0 * rho1 * dp * 1e3) / np.sqrt(1.0 - beta ** 4)
    C = np.full(np.broadcast(k, c_err).shape, 0.6)
    for _ in range(iters):
        qm = C * k
        Re = 4.0 * qm / (np.pi * D * mu)
        C_new = rhg(beta, D, Re, L1, L2) * (1.0 + c_err)
        if np.max(np.abs(C_new / C - 1.0)) < 1e-13:
            C = C_new
            break
        C = C_new
    else:
        raise RuntimeError("C / Re_D did not converge")
    return C * k, Re, C


# ---------------------------------------------------------------- gas and meters
def composition(name):
    x = np.zeros(21)
    for c, v in GASES[name].items():
        x[NIST.index(c)] = v
    return x / x.sum()


@dataclass
class Meter:
    name: str
    role: str            # "R" receipt or "D" delivery
    D: float             # m, internal pipe diameter
    beta: float
    p1: float            # kPa absolute, upstream tap
    T1: float            # K
    span_dp: float       # kPa
    dp: float = 0.0      # kPa, operating point (receipts set; deliveries solved)
    share: float = 0.0   # deliveries: share of total receipts
    taps: str = "flange"

    @property
    def d(self):
        return self.beta * self.D


@dataclass
class State:
    """Everything about a meter at its true operating point that the MC needs."""
    m: Meter
    Z1: float
    Zb: float
    MW: float            # g/mol
    HN: float            # kJ/mol
    kappa: float
    qm: float            # kg/s
    Re: float
    C: float
    J: np.ndarray = field(default=None, repr=False)   # d ln(MW, Z1, Zb, HN) / d e_c, shape 4 x 21


def gas_props(aga, x, T1, p1):
    return dict(Z1=aga.z(T1, p1, x), Zb=aga.z(T_BASE, P_BASE, x), MW=aga.molar_mass(x),
                HN=aga.hv(x), kappa=aga.kappa(T1, p1, x))


def jacobian(aga, x, T1, p1, h=1e-3):
    """d ln(MW, Z1, Zb, HN) / d e_c, where component c is measured as x_c (1 + e_c) and the
    composition renormalised. Central differences on the reference code.
    h = 1e-3, the size of the errors it linearises: at 1e-5 a step moves Z by ~1e-8, under
    what GERG-2008's density solve resolves, and the Z columns came out as noise
    (linearisation error 0.5 of the term at 1e-4; 2e-3 at 1e-3 and 1e-2; test_meter)."""
    J = np.zeros((4, 21))
    for c in range(21):
        if x[c] == 0:
            continue
        out = []
        for s in (+h, -h):
            xx = x.copy()
            xx[c] *= 1 + s
            xx /= xx.sum()
            out.append([math.log(aga.molar_mass(xx)), math.log(aga.z(T1, p1, xx)),
                        math.log(aga.z(T_BASE, P_BASE, xx)), math.log(aga.hv(xx))])
        J[:, c] = (np.array(out[0]) - np.array(out[1])) / (2 * h)
    return J


def solve_dp(aga, m, x, target_mol_s):
    """dp (kPa) at which meter m passes target_mol_s of gas x, by secant on sqrt(dp)."""
    g = gas_props(aga, x, m.T1, m.p1)
    L1, L2 = taps_L(m.taps, m.D)

    def mol(dp):
        qm, _, _ = mass_flow(m.d, m.D, dp, m.p1, m.T1, g["MW"], g["Z1"], g["kappa"], L1, L2)
        return float(qm) / (g["MW"] * 1e-3)
    a, b = 0.1 * m.span_dp, 0.9 * m.span_dp
    fa, fb = mol(a) - target_mol_s, mol(b) - target_mol_s
    for _ in range(100):
        c = b - fb * (b - a) / (fb - fa)
        fc = mol(c) - target_mol_s
        if abs(fc) < 1e-14 * target_mol_s:
            return c
        a, fa, b, fb = b, fb, c, fc
    raise RuntimeError(f"{m.name}: dp did not converge")


def build_system(meters, gas="Gulf Coast", aga=None):
    """Nominal states. Receipts run at their stated dp; each delivery's dp is solved so the
    deliveries take the receipts' total moles in their stated shares (true balance exact)."""
    aga = aga or AGA8()
    x = composition(gas)
    states = []
    total = 0.0
    for m in meters:
        if m.role != "R":
            continue
        g = gas_props(aga, x, m.T1, m.p1)
        L1, L2 = taps_L(m.taps, m.D)
        qm, Re, C = mass_flow(m.d, m.D, m.dp, m.p1, m.T1, g["MW"], g["Z1"], g["kappa"], L1, L2)
        states.append(State(m, **g, qm=float(qm), Re=float(Re), C=float(C)))
        total += float(qm) / (g["MW"] * 1e-3)
    shares = sum(m.share for m in meters if m.role == "D")
    for m in meters:
        if m.role != "D":
            continue
        dp = solve_dp(aga, m, x, total * m.share / shares)
        m2 = replace(m, dp=dp)
        g = gas_props(aga, x, m2.T1, m2.p1)
        L1, L2 = taps_L(m2.taps, m2.D)
        qm, Re, C = mass_flow(m2.d, m2.D, dp, m2.p1, m2.T1, g["MW"], g["Z1"], g["kappa"], L1, L2)
        states.append(State(m2, **g, qm=float(qm), Re=float(Re), C=float(C)))
    for s in states:
        s.J = jacobian(aga, x, s.m.T1, s.m.p1)
        if not (1e4 <= s.Re and 0.2 <= s.m.beta <= 0.75 and s.m.D >= 0.07112):
            raise ValueError(f"{s.m.name}: outside the range the Cd uncertainty applies to "
                             f"(Re_D {s.Re:.3g}, beta {s.m.beta}, D {s.m.D})")
        # inside the transmitter's span, and p2/p1 >= 0.75 (ISO 5167-2's expansibility range)
        if not (0.1 <= s.m.dp / s.m.span_dp <= 1.0 and s.m.dp / s.m.p1 <= 0.25):
            raise ValueError(f"{s.m.name}: dp {s.m.dp:.3g} kPa is outside 10-100% of its "
                             f"{s.m.span_dp} kPa span or above 25% of p1")
    return states, x


# Default system: SYNTHETIC, every value an ASSUMPTION (shown as a table on the page).
# Twelve receipt meters on 4-inch runs feed three delivery meters, one on a
# 12-inch run and two on 8-inch runs (internal diameters 102.3, 304.8, 202.7 mm).
# Receipts sit at a higher pressure and higher in their dp spans than deliveries,
# so the shared terms that depend on span and pressure have something to act on.
def default_meters():
    ms = []
    for i in range(12):
        ms.append(Meter(f"R{i + 1}", "R", D=0.1023, beta=0.50, p1=800 * PSI, T1=T_BASE + 10 / 1.8,
                        span_dp=50.0, dp=25.0 + 2.0 * (i % 4)))
    for i, (share, D) in enumerate(((0.5, 0.3048), (0.3, 0.2027), (0.2, 0.2027))):
        ms.append(Meter(f"D{i + 1}", "D", D=D, beta=0.55, p1=400 * PSI, T1=T_BASE,
                        span_dp=50.0, share=share))
    return ms


# ---------------------------------------------------------------- error components
@dataclass
class Comp:
    """One error component. kind: how the drawn number acts at a meter."""
    name: str
    group: str           # the input it belongs to, for reporting
    kind: str            # "dp_kpa", "dp_gain", "p_kpa", "T_K", "rel_C", "rel_d", "rel_D", "comp", "zeq"
    dist: str            # "normal" or "rect" (unit variance either way)
    f: float             # shared fraction
    redraw: str          # "interval" (recalibrated) or "period" (held)
    by_class: bool = False
    class_key: str = "beta"   # "beta": (taps, beta band); "role": receipts vs deliveries


def default_comps(f=None, c_class="beta"):
    """c_class: how the shared part of C is grouped. "beta" shares it among meters of one
    tap type and beta band (the RHG equation's bias depends on beta); "role" shares it among
    receipt meters and, separately, among delivery meters (two ends built or calibrated
    apart). Neither grouping is sourced; the page shows what each does."""
    f = dict(f or {})
    g = lambda k, d: f.get(k, d)   # noqa: E731
    return [
        Comp("dp reference", "dp", "dp_kpa", "rect", g("dp", 0.0), "interval"),
        Comp("dp ambient", "dp", "dp_kpa", "rect", g("dp", 0.0), "interval"),
        Comp("dp static span", "dp", "dp_gain", "rect", g("dp", 0.0), "interval"),
        Comp("p reference", "p1", "p_kpa", "rect", g("p1", 0.0), "interval"),
        Comp("T sensor", "T1", "T_K", "rect", g("T1", 0.0), "interval"),
        Comp("T transmitter", "T1", "T_K", "rect", g("T1", 0.0), "interval"),
        Comp("T installation", "T1", "T_K", "rect", g("T1", 0.0), "interval"),
        Comp("C", "C", "rel_C", "normal", g("C", 0.0), "period", by_class=True, class_key=c_class),
        Comp("bore d", "d", "rel_d", "rect", g("d", 0.0), "period"),
        Comp("pipe D", "D", "rel_D", "rect", g("D", 0.0), "period"),
        Comp("composition", "composition", "comp", "normal", g("composition", 0.0), "interval"),
        Comp("Z equation", "Z", "zeq", "normal", 1.0, "period"),
    ]


GROUPS = ["C", "dp", "p1", "T1", "d", "D", "composition", "Z"]


def _unit(rng, dist, shape):
    if dist == "normal":
        return rng.standard_normal(shape)
    return rng.uniform(-SQ3, SQ3, shape)


def _scale(c, s):
    """Standard uncertainty of component c at meter state s, in the component's own unit."""
    m = s.m
    if c.name == "dp reference":
        return DP_REF * m.span_dp / SQ3
    if c.name == "dp ambient":
        return (DP_AMB_SPAN * m.span_dp + DP_AMB_URL * DP_URL) / SQ3
    if c.name == "dp static span":
        return DP_STATIC * (m.p1 / (1000 * PSI)) / SQ3
    if c.name == "p reference":
        return P_REF * 1.5 * m.p1 / SQ3
    if c.name == "T sensor":
        return (T_SENSOR[0] + T_SENSOR[1] * abs(m.T1 - 273.15)) / SQ3
    if c.name == "T transmitter":
        return T_XMTR / SQ3
    if c.name == "T installation":
        return T_INSTALL / SQ3
    if c.name == "C":
        return float(cd_u(m.beta))
    if c.name == "bore d":
        return D_BORE / SQ3
    if c.name == "pipe D":
        return D_PIPE / SQ3
    if c.name in ("composition", "Z equation"):
        return 1.0
    raise KeyError(c.name)


def _class_of(s, key="beta"):
    if key == "role":
        return (s.m.role,)
    return (s.m.taps, int(s.m.beta * 10 + 1e-9))


# ---------------------------------------------------------------- one batch
def simulate(states, x, comps, K, rng, intervals=4, relative_only=False, scale=1.0, mu=MU):
    """K Monte Carlo trials of the system over one period of `intervals` calibration intervals.

    Returns a dict of arrays over trials: relative imbalance in base volume and in energy
    (measured receipts minus measured deliveries, over true throughput, period mean) and the
    relative error of total measured receipts, base volume.
    `relative_only` converts every error to a relative error applied identically at every
    meter with the same exponent (the v1 model; for test_meter's break). `scale` multiplies
    every u (0 gives the zero-uncertainty test)."""
    n = len(states)
    T = intervals
    zu = np.array([s.Zb for s in states])
    D = np.array([s.m.D for s in states])
    d = np.array([s.m.d for s in states])
    dp = np.array([s.m.dp for s in states])
    p1 = np.array([s.m.p1 for s in states])
    T1 = np.array([s.m.T1 for s in states])
    Z1 = np.array([s.Z1 for s in states])
    Zb = zu
    MW = np.array([s.MW for s in states])
    HN = np.array([s.HN for s in states])
    kap = np.array([s.kappa for s in states])
    L = [taps_L(s.m.taps, s.m.D) for s in states]
    L1 = np.array([a for a, _ in L])
    L2 = np.array([b for _, b in L])
    role = np.array([1.0 if s.m.role == "R" else -1.0 for s in states])
    def classes_for(key):
        cl = [_class_of(s, key) for s in states]
        return np.array([sorted(set(cl)).index(c) for c in cl]), len(set(cl))

    # true flows (the same in every interval)
    qm_true = np.array([s.qm for s in states])
    n_true = qm_true / (MW * 1e-3)
    vb_true = n_true * Zb * R_GERG * T_BASE / (P_BASE * 1e3)
    e_true = n_true * HN * 1e3
    through_v = vb_true[role > 0].sum()
    through_e = e_true[role > 0].sum()

    shape = (K, T, n)
    e = {k: np.zeros(shape) for k in ("dp", "p1", "T1", "C", "d", "D")}
    gain = np.zeros(shape)
    dln = np.zeros((4,) + shape)       # ln MW, ln Z1, ln Zb, ln HN
    comp_u = np.array([COMP_U.get(c, 0.0) / 100.0 for c in NIST])

    def draw(c, per):
        """Unit draws with sharing, shape (K, T, per). Held components repeat over T."""
        Tn = T if c.redraw == "interval" else 1
        if c.by_class:
            cls_idx, ncls = classes_for(c.class_key)
            z = _unit(rng, c.dist, (K, Tn, ncls))[:, :, cls_idx]
        else:
            z = _unit(rng, c.dist, (K, Tn, 1))
        w = _unit(rng, c.dist, (K, Tn, per))
        u = math.sqrt(c.f) * z + math.sqrt(1.0 - c.f) * w
        return np.broadcast_to(u, (K, T, per)) if Tn == 1 else u

    for c in comps:
        if c.kind == "comp":
            # one unit draw per component per meter; f shares it across meters
            for j in range(21):
                if comp_u[j] == 0 or x[j] == 0:
                    continue
                u = draw(c, n) * comp_u[j] * scale
                for r in range(4):
                    dln[r] += u * np.array([s.J[r, j] for s in states])
            continue
        if c.kind == "zeq":
            a = Z_U_REF / (1.0 - z_ref())
            u = draw(c, n) * a * scale
            if relative_only:      # v1: one relative error, the same at every Z
                dln[1] += u * (1.0 - z_ref())
                dln[2] += u * (1.0 - z_ref())
            else:
                dln[1] += u * (1.0 - Z1)
                dln[2] += u * (1.0 - Zb)
            continue
        sc = np.array([_scale(c, s) for s in states]) * scale
        # relative_only (v1's form, test_meter's break): every meter gets the same
        # relative error from a shared cause, as if all sat at the system's mean
        # span fraction, pressure and temperature.
        ref = (lambda v: np.full(n, v.mean())) if relative_only else (lambda v: v)
        if relative_only:
            sc = np.full(n, sc.mean())
        u = draw(c, n) * sc
        if c.kind == "dp_kpa":
            e["dp"] += u / ref(dp)
        elif c.kind == "dp_gain":
            gain += u
        elif c.kind == "p_kpa":
            e["p1"] += u / ref(p1)
        elif c.kind == "T_K":
            e["T1"] += u / ref(T1)
        elif c.kind == "rel_C":
            e["C"] += u
        elif c.kind == "rel_d":
            e["d"] += u
        elif c.kind == "rel_D":
            e["D"] += u
    e["dp"] = e["dp"] + gain

    qm_meas, _, _ = mass_flow(d * (1 + e["d"]), D * (1 + e["D"]), dp * (1 + e["dp"]),
                              p1 * (1 + e["p1"]), T1 * (1 + e["T1"]), MW * np.exp(dln[0]),
                              Z1 * np.exp(dln[1]), kap, L1, L2, c_err=e["C"], mu=mu)
    MWm = MW * np.exp(dln[0])
    n_meas = qm_meas / (MWm * 1e-3)
    vb_meas = n_meas * Zb * np.exp(dln[2]) * R_GERG * T_BASE / (P_BASE * 1e3)
    en_meas = n_meas * HN * np.exp(dln[3]) * 1e3
    imb_v = (vb_meas * role).sum(axis=2).mean(axis=1) / through_v
    imb_e = (en_meas * role).sum(axis=2).mean(axis=1) / through_e
    rec_v = (vb_meas * (role > 0)).sum(axis=2).mean(axis=1) / through_v - 1.0
    return {"imb_v": imb_v, "imb_e": imb_e, "rec_v": rec_v}


_Z_REF = None


def z_ref(aga=None):
    """Z of the Gulf Coast gas at 60 F, 1200 psia: where u_Z = Z_U_REF (PLAN 2.1)."""
    global _Z_REF
    if _Z_REF is None:
        aga = aga or AGA8()
        _Z_REF = aga.z(T_BASE, 1200 * PSI, composition("Gulf Coast"))
    return _Z_REF


# ---------------------------------------------------------------- JCGM 101 7.9.4
def tolerance(u, ndig=2):
    """Numerical tolerance of 7.9.2: u written c x 10^l, c an ndig-digit integer; delta = 10^l / 2.
    u is rounded to ndig significant digits FIRST: 0.9998 at ndig 3 is 1.00 = 100 x 10^-2,
    delta 0.005. Taking the exponent before rounding gave 0.0005 there, ten times too fine."""
    if u == 0:
        return 0.0
    e = math.floor(math.log10(abs(u)))
    r = round(abs(u), -(e - (ndig - 1)))
    l = math.floor(math.log10(r)) - (ndig - 1)
    return 0.5 * 10.0 ** l


def summarise(y, p=0.95):
    lo, hi = np.quantile(y, [(1 - p) / 2, (1 + p) / 2])   # probabilistically symmetric interval
    return {"mean": float(y.mean()), "u": float(y.std(ddof=1)), "low": float(lo), "high": float(hi)}


def adaptive(run_batch, keys, p=0.95, ndig=2, K=None, max_batches=400, min_batches=5):
    """JCGM 101:2008 7.9.4. run_batch(K) returns a dict of arrays; every key in `keys` is a
    reported result. Batches of K = max(ceil(100/(1-p)), 1e4) until, for every key and each of
    mean, u, low and high, twice the standard deviation of the AVERAGE over batches
    (s^2 = sum (r_b - r_bar)^2 / (h (h - 1))) is below the 7.9.2 tolerance of that key's u.
    7.9.4 allows a stop at h = 2; a standard deviation from two batches is itself very
    uncertain, and the default system did stop there on its first run, so the default is
    at least five batches. More trials, never fewer, so it cannot loosen the rule."""
    K = K or max(math.ceil(100 / (1 - p)), 10 ** 4)
    batches = {k: [] for k in keys}
    pooled = {k: [] for k in keys}
    for h in range(1, max_batches + 1):
        out = run_batch(K)
        for k in keys:
            batches[k].append(summarise(out[k], p))
            pooled[k].append(out[k])
        if h < max(2, min_batches):
            continue
        done = True
        for k in keys:
            allv = np.concatenate(pooled[k])
            delta = tolerance(float(allv.std(ddof=1)), ndig)
            for stat in ("mean", "u", "low", "high"):
                v = np.array([b[stat] for b in batches[k]])
                s = math.sqrt(((v - v.mean()) ** 2).sum() / (h * (h - 1)))
                if 2 * s >= delta:
                    done = False
        if done:
            break
    else:
        raise RuntimeError("7.9.4 did not stabilise")
    res = {}
    for k in keys:
        allv = np.concatenate(pooled[k])
        r = summarise(allv, p)
        r["delta"] = tolerance(r["u"], ndig)
        r["trials"] = len(allv)
        r["batches"] = h
        res[k] = r
    return res
