"""Euler-vector fitting for rigid plates, and the gates that guard it.

A plate's motion is a rotation about an axis through the Earth's centre. The
velocity at a site is

    v = omega x r                        (Altamimi et al. 2017, equation 1)

with omega the plate's angular velocity vector and r the site's geocentric
position. That form is linear in omega, so fitting a plate is weighted least
squares on the horizontal components. Neither DeMets et al. 2010 nor Argus
et al. 2011 states the formula - MORVEL has two numbered equations and this
is neither - so the citation is the ITRF paper.

WHY THERE ARE TWO GATES AND NOT ONE
-----------------------------------
The obvious check is that a fitted rotation reproduces a published model's
velocities at the plate's own stations. That is a summary statistic, and a
summary statistic does not pin the parameters behind it. A plate whose
stations cover a small patch constrains its rotation vector poorly: the
component of omega that points along the patch's own position vector barely
moves the velocities there at all. So a rotation can be wrong by a large
angle, agree with the published model everywhere a station happens to sit,
and disagree violently over the rest of the plate. break_b1.py demonstrates
exactly that, on India, using nothing but this module.

So the gate on the parameters (B1a, the rotation vectors themselves) is
separate from the gate on the consequences (B1b, velocities sampled over the
whole plate, not only where receivers are), and both must pass.

The second shape of the trap is one bad station. A weighted fit barely
notices a single outlier, so B1a and B1b can pass while the residual the
page quotes is ruined - ILSG on Salas y Gomez is filed under the Pacific,
sits on Nazca, and misses by 137.7 mm/yr. B2 is the gate for that.
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
R_EARTH = 6371008.8              # m, mean radius, IUGG

MIN_YEARS = 5.0                  # assumed; stated on the page
MAX_SIGMA = 0.0005               # m/yr on each horizontal component; assumed
FAR_KM = 500.0                   # assumed; see the distance-residual figure
MIN_STATIONS = 20

MAD_K = 5.0                      # exclusion rule
RESID_FLOOR = 2.0                # mm/yr
MAX_ITER = 8
MAX_DROP_FRACTION = 0.40

# NGL plate code -> ITRF2020-PMM plate code
ITRF_CODE = {"NA": "NOAM", "EU": "EURA", "AU": "AUST", "SA": "SOAM",
             "AF": "NUBI", "AN": "ANTA", "IN": "INDI", "SO": "SOMA",
             "PA": "PCFC", "AR": "ARAB"}
PLATE_NAME = {"NA": "North America", "EU": "Eurasia", "AU": "Australia",
              "SA": "South America", "AF": "Nubia", "AN": "Antarctica",
              "IN": "India", "SO": "Somalia", "PA": "Pacific",
              "AR": "Arabia"}


# ---------------------------------------------------------------- geometry

def unit(lat, lon):
    la, lo = np.radians(np.asarray(lat)), np.radians(np.asarray(lon))
    return np.column_stack([np.cos(la) * np.cos(lo),
                            np.cos(la) * np.sin(lo), np.sin(la)])


def basis(lat, lon):
    """Position vector in metres and the local east and north unit vectors."""
    la, lo = math.radians(lat), math.radians(lon)
    r = R_EARTH * np.array([math.cos(la) * math.cos(lo),
                            math.cos(la) * math.sin(lo), math.sin(la)])
    e = np.array([-math.sin(lo), math.cos(lo), 0.0])
    n = np.array([-math.sin(la) * math.cos(lo),
                  -math.sin(la) * math.sin(lo), math.cos(la)])
    return r, e, n


def skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])


def design(lat, lon):
    """Rows of the 2n x 3 matrix A with v_en = A omega, omega in rad/yr."""
    rows = []
    for la, lo in zip(np.atleast_1d(lat), np.atleast_1d(lon)):
        r, e, n = basis(float(la), float(lo))
        M = -skew(r)                       # omega x r = -[r]_x omega
        rows.append(e @ M)
        rows.append(n @ M)
    return np.array(rows)


def velocity(omega, lat, lon):
    """East and north velocity in mm/yr for a rotation in rad/yr."""
    A = design(lat, lon)
    v = A @ omega
    return v[0::2] * 1000.0, v[1::2] * 1000.0


def pole_of(omega):
    """(lat, lon, deg/Myr) for a rotation vector in rad/yr."""
    rate = float(np.linalg.norm(omega))
    return (math.degrees(math.asin(omega[2] / rate)),
            math.degrees(math.atan2(omega[1], omega[0])),
            math.degrees(rate) * 1e6)


def omega_of(pole_lat, pole_lon, rate_deg_myr):
    rate = math.radians(rate_deg_myr) / 1e6
    la, lo = math.radians(pole_lat), math.radians(pole_lon)
    return rate * np.array([math.cos(la) * math.cos(lo),
                            math.cos(la) * math.sin(lo), math.sin(la)])


def deg_per_myr(omega):
    """A rotation vector in rad/yr expressed as deg/Myr components."""
    return np.degrees(np.asarray(omega)) * 1e6


# -------------------------------------------------------------------- data

def load_stations(path=None):
    import csv
    path = path or os.path.join(HERE, "data", "stations.csv")
    out = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out.append({"sta": row["sta"], "lat": float(row["lat"]),
                        "lon": float(row["lon"]), "ve": float(row["ve"]),
                        "vn": float(row["vn"]), "sve": float(row["sve"]),
                        "svn": float(row["svn"]),
                        "dur": float(row["dur_yr"]),
                        "plate": row["ngl_plate"]})
    return out


def boundary_points(path=None):
    path = path or os.path.join(HERE, "data", "PB2002_boundaries.json")
    gj = json.load(open(path, encoding="utf-8"))
    pts = []
    for ft in gj["features"]:
        g = ft.get("geometry") or {}
        if g.get("type") == "LineString":
            pts.extend(g["coordinates"])
        elif g.get("type") == "MultiLineString":
            for ln in g["coordinates"]:
                pts.extend(ln)
    a = np.array([[p[0], p[1]] for p in pts], float)
    return unit(a[:, 1], a[:, 0])


def distance_to_boundary(lat, lon, bpts, chunk=512):
    """Great-circle km to the nearest PB2002 boundary VERTEX.

    Vertex, not nearest point on the segment: PB2002's vertices are closely
    spaced so the difference is small, but it is an overestimate where a
    segment is sparse and the page says so. Done on unit vectors, which is
    why it needs no dateline handling.
    """
    s = unit(lat, lon)
    out = np.empty(len(s))
    for i in range(0, len(s), chunk):
        d = np.clip(s[i:i + chunk] @ bpts.T, -1.0, 1.0)
        out[i:i + chunk] = np.arccos(d.max(axis=1)) * R_EARTH / 1000.0
    return out


def load_itrf(path=None):
    """ITRF2020-PMM.dat: omega_x, omega_y, omega_z in deg/Myr."""
    path = path or os.path.join(HERE, "data", "ITRF2020-PMM.dat")
    out = {}
    for line in open(path, encoding="utf-8"):
        f = line.replace(",", " ").split()
        if len(f) == 4 and f[0].isalpha() and len(f[0]) == 4:
            try:
                vals = [float(v) for v in f[1:]]
            except ValueError:
                continue
            out[f[0]] = np.radians(np.array(vals)) / 1e6
    return out


# ------------------------------------------------------------------ fitting

def fit(stations):
    """Weighted least squares for the rotation vector, rad/yr."""
    A, b, w = [], [], []
    for s in stations:
        r, e, n = basis(s["lat"], s["lon"])
        M = -skew(r)
        A.append(e @ M); b.append(s["ve"]); w.append(1.0 / s["sve"] ** 2)
        A.append(n @ M); b.append(s["vn"]); w.append(1.0 / s["svn"] ** 2)
    A, b, w = np.array(A), np.array(b), np.array(w)
    sw = np.sqrt(w)
    omega, *_ = np.linalg.lstsq(A * sw[:, None], b * sw, rcond=None)
    return omega, A, np.array(b)


def residuals(stations, omega):
    """Speed of the leftover at each station, mm/yr."""
    A = design([s["lat"] for s in stations], [s["lon"] for s in stations])
    b = np.empty(2 * len(stations))
    b[0::2] = [s["ve"] for s in stations]
    b[1::2] = [s["vn"] for s in stations]
    d = (b - A @ omega) * 1000.0
    return np.hypot(d[0::2], d[1::2])


def fit_with_exclusions(stations):
    """Iterated robust fit. Returns (omega, kept, dropped, iterations).

    The rule, which is what the page states rather than a list of station
    names: fit, then drop any station whose residual exceeds
    max(median + 5 MAD, 2 mm/yr), refit, and repeat until nothing is
    dropped, fewer than MIN_STATIONS remain, or MAX_ITER is reached.

    A list of names would be a hardcoded answer for today's contaminants,
    which is the same failure the gates exist to catch. The names are used
    only afterwards, as an assertion about what the rule found.
    """
    kept = list(stations)
    dropped, it = [], 0
    for it in range(1, MAX_ITER + 1):
        omega, _, _ = fit(kept)
        res = residuals(kept, omega)
        med = float(np.median(res))
        mad = float(np.median(np.abs(res - med)))
        cut = max(med + MAD_K * mad, RESID_FLOOR)
        bad = [i for i, r in enumerate(res) if r > cut]
        if not bad or len(kept) - len(bad) < MIN_STATIONS:
            break
        for i in sorted(bad, reverse=True):
            s = dict(kept[i])
            s["residual_mm_yr"] = float(res[i])
            s["iteration"] = it
            s["cut_mm_yr"] = cut
            dropped.append(s)
            kept.pop(i)
    omega, _, _ = fit(kept)
    return omega, kept, dropped, it


# ------------------------------------------------------------------- gates

def plate_area_sample(stations, n=2000, seed=7):
    """Points spread over the plate's own extent, not its receiver pattern.

    B1b samples the rotation's consequences here rather than at the
    stations, because a station set can be small and clustered while the
    plate is not, and it is over the rest of the plate that a wrong rotation
    shows up.
    """
    lat = np.array([s["lat"] for s in stations])
    lon = np.array([s["lon"] for s in stations])
    rng = np.random.default_rng(seed)
    la = rng.uniform(lat.min(), lat.max(), n)
    lo = rng.uniform(lon.min(), lon.max(), n)
    return la, lo


def compare_to_itrf(omega, itrf_omega, stations):
    """B1a on the parameters, B1b on the consequences over the plate."""
    d_omega = deg_per_myr(omega - itrf_omega)
    param = float(np.linalg.norm(d_omega))                      # deg/Myr
    la = [s["lat"] for s in stations]
    lo = [s["lon"] for s in stations]
    e1, n1 = velocity(omega, la, lo)
    e2, n2 = velocity(itrf_omega, la, lo)
    at_stations = float(np.median(np.hypot(e1 - e2, n1 - n2)))
    pla, plo = plate_area_sample(stations)
    e1, n1 = velocity(omega, pla, plo)
    e2, n2 = velocity(itrf_omega, pla, plo)
    over_plate = float(np.percentile(np.hypot(e1 - e2, n1 - n2), 95))
    return {"d_omega_deg_myr": param,
            "median_at_stations_mm_yr": at_stations,
            "p95_over_plate_mm_yr": over_plate}
