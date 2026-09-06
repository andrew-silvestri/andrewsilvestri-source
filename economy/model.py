"""
The physics this page is about: what a per cent of running economy is worth.

Marathon speed is the product of three terms - the aerobic ceiling, the
fraction of it a runner can hold, and the oxygen cost of covering a metre:

    speed = VO2max * F / C

which is Joyner's 1991 form. Improving any term by p multiplies through, so
three gains of p give (1+p)^2/(1-p) - 1 rather than 3p. That difference is
this page's null: it is 0.37 percentage points at p = 3%.

What is not a rounding error is the step from a metabolic saving to a speed.
The oxygen cost of running rises faster than speed does, and the air a runner
pushes costs energy in proportion to the cube of speed, so holding a saving of
x per cent buys less than x per cent of speed - except at slow paces, where it
buys slightly more. Kipp, Kram and Hoogkamer 2019 give six published
cost-of-running curves with Pugh's air term added; this module solves them.

Everything here is arithmetic over published coefficients. Nothing is fitted,
smoothed or tuned, because a refitted curve is exactly how this page would
acquire a number that is not in any paper.

Units, kept explicit because mixing them silently is the failure mode:
    v      m/s
    VO2    ml O2 per kg per minute, GROSS (resting included)
    cost   ml O2 per kg per km
    time   seconds
"""

MARATHON_M = 42195.0

# ---------------------------------------------------------------------------
# The cost-of-running curves.
#
# Kipp S, Kram R, Hoogkamer W (2019), Frontiers in Physiology 10:79,
# doi:10.3389/fphys.2019.00079, PMC6378703, CC BY. Equations 1-6, transcribed
# from the PMC full text on 2026-09-05 and checked against the three results
# the paper states (see check_paper_numbers()).
#
# Each is VO2 (ml/kg/min) = a3 v^3 + a2 v^2 + a1 v + a0, with v in m/s. The
# cubic term is Pugh's air resistance, VO2 (l/min) = 0.00354 * Ap * v^3, for
# the paper's reference runner: 58 kg, 1.71 m, projected frontal area
# 0.45 m^2. Equation 5 is overground and carries its own, larger, air term.
#
# Signs matter. Two of these have positive linear terms that are easy to
# transcribe as negative, which would put the elasticity on the wrong side of
# 1; test_economy.py asserts the sign of the result rather than the digits.
CURVES = {
    "batliner": {
        "coef": (0.02724, 1.5355, 1.5354, 15.661),
        "label": "Batliner 2018, quadratic",
        "note": "the curve Kipp et al. prefer, and the one this page uses",
        "primary": True,
    },
    "leger": {
        "coef": (0.02724, 0.0, 11.39, 2.209),
        "label": "Leger & Mercier 1984, linear",
        "note": "linear in speed, so its curvature comes only from the air term",
        "primary": False,
    },
    "black": {
        "coef": (0.02724, 1.9128, 3.2483, 25.806),
        "label": "Black 2018",
        "note": "",
        "primary": False,
    },
    "kipp2018": {
        "coef": (0.02724, 1.7321, 0.538, 18.91),
        "label": "Kipp 2018",
        "note": "",
        "primary": False,
    },
    "batliner_linear": {
        "coef": (0.02724, 0.0, 12.2, 1.11),
        "label": "Batliner 2018, linear fit",
        "note": "the same data forced straight, for comparison",
        "primary": False,
    },
}

CURVE_SOURCE = ("Kipp, Kram & Hoogkamer, Frontiers in Physiology 10:79, 2019, "
                "doi:10.3389/fphys.2019.00079")
REFERENCE_RUNNER = {"mass_kg": 58, "height_m": 1.71, "frontal_area_m2": 0.45,
                    "source": CURVE_SOURCE}

# Tam et al. 2012's overground curve is Kipp's equation 5. It is kept out of
# CURVES because its air term (0.0537) is not Pugh's and its shape is not
# comparable with the treadmill curves on the same axes; the page names it in
# prose instead.

PUGH_AIR = {"coef_per_area": 0.00354, "area_m2": 0.45,
            "source": "Pugh, Journal of Physiology 207:823, 1970, as applied by "
                      "Kipp, Kram & Hoogkamer 2019"}


def vo2(v, curve="batliner"):
    """Gross VO2 in ml/kg/min at speed v (m/s)."""
    a3, a2, a1, a0 = CURVES[curve]["coef"]
    return a3 * v ** 3 + a2 * v * v + a1 * v + a0


def dvo2(v, curve="batliner"):
    """d(VO2)/dv, ml/kg/min per m/s."""
    a3, a2, a1, _ = CURVES[curve]["coef"]
    return 3 * a3 * v * v + 2 * a2 * v + a1


def cost_per_km(v, curve="batliner"):
    """Gross oxygen cost in ml/kg/km at speed v."""
    return vo2(v, curve) * 1000.0 / (v * 60.0)


def drag_share(v, curve="batliner"):
    """Share of gross VO2 that is the air term at speed v."""
    a3 = CURVES[curve]["coef"][0]
    return a3 * v ** 3 / vo2(v, curve)


def elasticity(v, curve="batliner"):
    """d ln v / d ln VO2 at speed v: the per cent of speed bought by one per
    cent of metabolic saving, in the limit of a small saving.

    Below about 3 m/s this exceeds 1 and above it falls away, which is the
    page's central fact: the discount is a fast runner's problem."""
    return vo2(v, curve) / (v * dvo2(v, curve))


def speed_for_saving(v, saving, curve="batliner"):
    """Speed a runner holds after a metabolic saving of `saving` (0.04 = 4%).

    Solves (1 - saving) * VO2(v') = VO2(v) by Newton's method from v. This is
    the finite version of elasticity(); the two agree to about 0.01 pp at the
    savings this page discusses, and the finite one is what gets published,
    because it is what the paper computes."""
    target = vo2(v, curve) / (1.0 - saving)
    x = v
    for _ in range(60):
        step = (vo2(x, curve) - target) / dvo2(x, curve)
        x -= step
        if abs(step) < 1e-12:
            break
    return x


def speed_gain(v, saving, curve="batliner"):
    """Fractional speed gain from a metabolic saving."""
    return speed_for_saving(v, saving, curve) / v - 1.0


def marathon_seconds(v):
    return MARATHON_M / v


def hms(seconds):
    s = int(round(seconds))
    return f"{s // 3600}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def ms(seconds):
    """A duration under an hour, as m:ss - used for time saved."""
    s = int(round(seconds))
    return f"{s // 60}:{s % 60:02d}"


# ---------------------------------------------------------------------------
# The transfer coefficient, measured.
#
# Hoogkamer W, Kipp S, Spiering BA, Kram R (2016), Medicine & Science in
# Sports & Exercise 48(11):2175-2180, doi:10.1249/MSS.0000000000001012,
# PMID 27327023. n = 18 men who race 5 km under 20 minutes. Adding 100 g per
# shoe raised metabolic rate 1.11% and 3000 m race time 0.78%; the ratio is
# how much of a metabolic change reaches the clock.
#
# Kipp et al. 2019 reproduce that 0.78% from their equation 2 at the speed
# the race was run, 4.79 m/s. So the agreement between the measured transfer
# and the modelled elasticity is stated in the literature, not claimed here;
# this module recomputes both.
HOOGKAMER_2016 = {
    "metabolic_pct": 1.11, "metabolic_ci": (0.88, 1.35),
    "time_pct": 0.78, "time_ci": (0.52, 1.04),
    "n": 18, "distance_m": 3000, "race_speed_ms": 4.79,
    "source": ("Hoogkamer, Kipp, Spiering & Kram, Medicine & Science in Sports & "
               "Exercise 48(11):2175-2180, 2016, doi:10.1249/MSS.0000000000001012"),
    "speed_source": ("Kipp, Kram & Hoogkamer 2019, which reproduces this result "
                     "from equation 2 at 4.79 m/s"),
}


def transfer_measured():
    """0.78 / 1.11, with the ratio's range taken across the two published
    confidence intervals. The interval is the widest the published bounds
    allow, not a variance estimate: the two effects were measured on the same
    runners and their covariance is not reported."""
    H = HOOGKAMER_2016
    point = H["time_pct"] / H["metabolic_pct"]
    lo = H["time_ci"][0] / H["metabolic_ci"][1]
    hi = H["time_ci"][1] / H["metabolic_ci"][0]
    return {"value": point, "lo": lo, "hi": hi,
            "n": H["n"], "speed_ms": H["race_speed_ms"], "source": H["source"]}


def transfer_modelled(curve="batliner"):
    """The elasticity at the speed Hoogkamer's 3000 m race was run, which is
    the modelled counterpart of transfer_measured()."""
    v = HOOGKAMER_2016["race_speed_ms"]
    return {"value": elasticity(v, curve), "speed_ms": v, "curve": curve,
            "source": CURVE_SOURCE}


# ---------------------------------------------------------------------------
# The null: compounding.
def product_vs_sum(p):
    """Three terms each improved by p. The ceiling and the fraction multiply;
    economy is a divisor, so it enters as 1/(1-p).

    Returns the product's total gain, the additive gain, and the gap."""
    product = (1 + p) ** 2 / (1 - p) - 1
    return {"p": p, "product": product, "sum": 3 * p, "gap": product - 3 * p}


def compounding_table(ps=(0.01, 0.02, 0.03, 0.05), baseline_seconds=3 * 3600):
    rows = []
    for p in ps:
        r = product_vs_sum(p)
        t_prod = baseline_seconds / (1 + r["product"])
        t_sum = baseline_seconds / (1 + r["sum"])
        r.update({"time_product_s": t_prod, "time_sum_s": t_sum,
                  "gap_s": t_sum - t_prod})
        rows.append(r)
    return rows


# ---------------------------------------------------------------------------
def check_paper_numbers(tol=0.02):
    """The three results Kipp et al. state in their text, recomputed.

    This is the check that matters. Every other number on the page is derived
    from these coefficients, so a single mistyped digit would move all of them
    together and quietly. Reproducing the paper's own published percentages
    from the transcribed coefficients is what proves the transcription.

    Returns (ok, rows). Tolerance is in percentage points."""
    cases = [
        (2.60, 0.01, 1.17, "a 1% saving at 2.60 m/s"),
        (5.72, 0.01, 0.65, "a 1% saving at 5.72 m/s"),
        (5.72, 0.04, 2.64, "a 4% saving at 5.72 m/s"),
    ]
    rows, ok = [], True
    for v, saving, stated, label in cases:
        got = 100 * speed_gain(v, saving)
        good = abs(got - stated) <= tol
        ok = ok and good
        rows.append({"label": label, "v": v, "saving": saving,
                     "stated_pct": stated, "computed_pct": got,
                     "diff_pp": got - stated, "ok": good})
    return ok, rows
