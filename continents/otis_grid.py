"""Reader and anchor gate for the OTIS binary grids in OSF 8NEQ4.

The grids are the four future supercontinent scenarios of Davies, Green and
Duarte, "Back to the future II", Earth System Dynamics 11, 291-299, 2020,
CC0. Fifty files: Pangaea Ultima and Aurica at 0 to 250 Myr, Novopangaea and
Amasia at 0 to 200, all at 0.25 degrees, each carrying a depth field and a
land/sea mask.

WHY THIS FILE IS A GATE AND NOT JUST A READER
---------------------------------------------
The four scenarios are NOT on a common longitude convention. Pangaea Ultima
and Amasia declare -180..180; Novopangaea and Aurica declare 0..360. Read as
they come, two of the four sit 180 degrees out, and the four present-day
grids - which are all the same map of today's Earth - appear to disagree
about 32 per cent of the planet instead of 0.9. That 32 would have been this
page's headline: a fabricated number, computed from real files, with no
symptom visible anywhere downstream.

So the normalisation is driven by each file's own declared header, never by
a hardcoded roll, and it is followed by a gate that must pass before any
disagreement number is computed.

WHAT THE ANCHOR IS, AND WHAT IT IS NOT
--------------------------------------
The obvious anchor is that all four grids contain t = 0, today's Earth, so
they should agree with each other. That check is necessary and it is NOT
sufficient, and the distinction matters: all four pass through this one
reader, so any error common to all four - a shared roll, a transpose, a
latitude flip - leaves them agreeing with each other perfectly while every
map on the page is wrong. Mutual agreement cannot see an error it shares.

The anchors that can are the ones from outside the data: twelve named points
whose land-or-sea answer comes from an ordinary world map, and the Earth's
land fraction. Those are A1 and A2 below, and they are the load-bearing
checks. A3, mutual agreement, is labelled for what it is.

Run:  python3 otis_grid.py     (self-test against the committed masks)
"""
import numpy as np

# Twelve probes. Truth is what an ordinary world map says, which makes this
# an anchor from outside the dataset rather than a consistency check inside
# it. Eight are marked roll-sensitive: their answer differs from the answer
# 180 degrees away, so a rolled grid fails them. Points 9 to 12 are not
# roll-sensitive and are here to catch a latitude flip or an inverted mask
# instead. Every one sits well inside its feature, not on a coast, because
# a 0.25 degree grid disagrees with an atlas about coastlines.
#                name              lon     lat   land  roll-sensitive
PROBES = [
    ("Congo basin",              20.0,    0.0,  True,  True),
    ("central Brazil",          -60.0,  -10.0,  True,  True),
    ("Sahara",                    10.0,   20.0,  True,  True),
    ("central Siberia",          100.0,   60.0,  True,  True),
    ("central Australia",        135.0,  -25.0,  True,  True),
    ("Iranian plateau",           60.0,   30.0,  True,  True),
    ("north Pacific",           -140.0,   20.0,  False, True),
    ("Bay of Bengal",             90.0,   20.0,  False, True),
    ("Kansas",                  -100.0,   39.0,  True,  False),
    ("Gulf of Guinea",             0.0,    0.0,  False, False),
    ("south Indian Ocean",         80.0,  -30.0,  False, False),
    ("Southern Ocean",              0.0,  -55.0,  False, False),
]

EARTH_LAND_FRACTION = 29.2      # per cent of the surface; looked up
LAND_TOLERANCE = 0.5            # percentage points
MUTUAL_TOLERANCE = 1.5          # per cent of the surface
POLAR_CUT = 88.0                # degrees; see area_weights()


def read_grid(buf):
    """Parse one OTIS grid from bytes.

    Ported from grd_in.m, the MATLAB reader shipped in the same deposit.
    Big-endian throughout. Two departures from that reader, both deliberate:

    - grd_in.m carries `if lons(1) < 0 && lons(2) < 0 && dt > 0, lons =
      lons + 360`. That branch fires on none of the fifty files. An untested
      heuristic inside a loader is a misfire waiting for a future release,
      so it is gone; normalise() does the job explicitly instead.
    - The field grd_in.m prints as "Time step (sec)" holds 0.25 in every
      file. It is the grid spacing, and it is named that here.
    """
    off = 4
    n, m = (int(v) for v in np.frombuffer(buf, ">i4", 2, off))
    off += 8
    lats = np.frombuffer(buf, ">f4", 2, off).astype(float); off += 8
    lons = np.frombuffer(buf, ">f4", 2, off).astype(float); off += 8
    spacing = float(np.frombuffer(buf, ">f4", 1, off)[0]); off += 4
    nob = int(np.frombuffer(buf, ">i4", 1, off)[0]); off += 4
    off += 20 if nob == 0 else 8 * nob + 16
    hz = np.frombuffer(buf, ">f4", n * m, off).reshape((n, m), order="F")
    off += 4 * n * m + 8
    mz = np.frombuffer(buf, ">i4", n * m, off).reshape((n, m), order="F")
    return {"n": n, "m": m, "lons": tuple(lons), "lats": tuple(lats),
            "spacing": spacing, "hz": hz, "mz": mz}


def normalise(g):
    """Put a grid on a -180..180 longitude axis, using its own header.

    The roll is derived from what the file declares, never assumed. A file
    declaring anything other than the two known conventions is refused
    rather than guessed at.
    """
    lo0, lo1 = g["lons"]
    if abs(lo0 + 180.0) < 1e-3 and abs(lo1 - 180.0) < 1e-3:
        return dict(g, rolled=False)
    if abs(lo0) < 1e-3 and abs(lo1 - 360.0) < 1e-3:
        k = g["n"] // 2
        return dict(g, lons=(-180.0, 180.0), rolled=True,
                    hz=np.roll(g["hz"], k, axis=0),
                    mz=np.roll(g["mz"], k, axis=0))
    raise SystemExit(
        f"otis_grid: unknown longitude convention {g['lons']}. Two are known, "
        "-180..180 and 0..360. A third means the release changed and every "
        "area number on the page must be rechecked before this is widened.")


def axes(g):
    """Node axes. These are nodes, not cell centres.

    721 latitude nodes at exactly 0.25 degrees from -90 to +90
    (721 = 180/0.25 + 1), and 1440 periodic longitude nodes. An earlier
    version treated them as cells spanning the declared range and offset by
    half a cell, which gave 0.2497 degree spacing and an axis running
    -89.875 to 89.880 - shifted about 0.12 degrees and stretched 0.1 per
    cent, which biased every area weight and put the polar cut one row off.
    """
    lon = g["lons"][0] + 0.25 * np.arange(g["n"])
    lat = g["lats"][0] + 0.25 * np.arange(g["m"])
    return lon, lat


def land_mask(g):
    """True where the cell is land. OTIS uses 0 for land in mz."""
    return g["mz"] == 0


def area_weights(lat, polar_cut=POLAR_CUT):
    """Normalised area weights over a lon-invariant latitude axis.

    Cell area goes as cos(lat). Everything poleward of `polar_cut` is
    dropped: the scenarios' own paper says "the resulting maps were then
    given an artificial land mask 2 degrees wide on both poles to allow for
    numerical convergence", so those rows are a modelling convenience and
    counting them inflates every polar statistic.
    """
    w = np.cos(np.radians(lat)) * (np.abs(lat) <= polar_cut)
    return w / w.sum()


def cell_weights(g):
    """Per-cell area weights for a whole grid, summing to 1 over the grid.

    area_weights() normalises over the latitude axis alone; a sum over the
    2-D grid then runs over 1440 longitudes as well and comes out 1440 times
    too large. The gate caught that on its first run, which is the argument
    for the gate.
    """
    _, lat = axes(g)
    return (area_weights(lat) / g["n"])[None, :]


def sample(g, lon_deg, lat_deg):
    """Nearest-node land/sea answer at a point, on a normalised grid."""
    lon, lat = axes(g)
    i = int(round((float(lon_deg) - lon[0]) / 0.25)) % g["n"]
    j = int(round((float(lat_deg) - lat[0]) / 0.25))
    return bool(land_mask(g)[i, j])


def land_percent(g):
    """Area-weighted land as a per cent of the surface, poles excluded."""
    return float((land_mask(g) * cell_weights(g)).sum() * 100.0)


def disagreement_percent(a, b, w):
    """Area-weighted share of the surface two masks disagree about.

    `w` is a cell_weights(g) array, already divided by the longitude count.
    """
    return float(((a != b) * w).sum() * 100.0)


def anchor_check(t0_grids, strict=True):
    """Gate A. Returns a list of rows; raises if strict and any fails.

    t0_grids: {scenario: normalised grid at 0 Myr}.

    A1 and A2 are the anchors, because their truth comes from outside the
    data. A3 is mutual agreement between the four, which is necessary and
    not sufficient, and is labelled so. A6 checks the axis this file builds.
    """
    rows = []

    bad = []
    for name, g in sorted(t0_grids.items()):
        for pname, lo, la, want, _rs in PROBES:
            got = sample(g, lo, la)
            if got != want:
                bad.append((name, pname, lo, la, want, got,
                            g["lons"], g.get("rolled")))
    n_probe = len(t0_grids) * len(PROBES)
    rows.append(("A1", "named land/sea probes, truth from a world map",
                 f"{n_probe}/{n_probe} exact",
                 f"{n_probe - len(bad)}/{n_probe}", not bad))

    lands = {k: land_percent(g) for k, g in t0_grids.items()}
    ok2 = all(abs(v - EARTH_LAND_FRACTION) <= LAND_TOLERANCE
              for v in lands.values())
    rows.append(("A2", "area-weighted land at t=0, against Earth's own",
                 f"{EARTH_LAND_FRACTION} +/- {LAND_TOLERANCE} pp",
                 f"{min(lands.values()):.2f}-{max(lands.values()):.2f} %", ok2))

    keys = sorted(t0_grids)
    w = cell_weights(t0_grids[keys[0]])
    worst = 0.0
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            worst = max(worst, disagreement_percent(
                land_mask(t0_grids[keys[i]]), land_mask(t0_grids[keys[j]]), w))
    rows.append(("A3", "the four t=0 grids agree with each other "
                 "(necessary, NOT sufficient)",
                 f"<= {MUTUAL_TOLERANCE} %", f"{worst:.2f} %",
                 worst <= MUTUAL_TOLERANCE))

    g0 = t0_grids[keys[0]]
    lon, lat = axes(g0)
    ok6 = (abs(lat[0] + 90.0) < 1e-9 and abs(lat[-1] - 90.0) < 1e-9
           and abs(lat[1] - lat[0] - 0.25) < 1e-9
           and abs(lon[1] - lon[0] - 0.25) < 1e-9 and g0["n"] == 1440
           and g0["m"] == 721)
    rows.append(("A6", "node axes: 1440 x 721 at exactly 0.25 degrees",
                 "lat -90..+90 exact", f"{lat[0]:.2f}..{lat[-1]:.2f} "
                 f"step {lat[1] - lat[0]:.4f}", ok6))

    if strict and not all(r[4] for r in rows):
        for r in rows:
            print(f"  {r[0]}  {'ok  ' if r[4] else 'FAIL'}  {r[1]}")
            print(f"        threshold {r[2]}   measured {r[3]}")
        for row in bad[:40]:
            print("  A1 fail: scenario=%s probe=%s lon=%.1f lat=%.1f "
                  "expected=%s got=%s declared_lon=%s rolled=%s" % row)
        raise SystemExit(
            "otis_grid: anchor check failed. Nothing downstream may run. "
            "Read the failing rows above: the grids disagree with the world, "
            "not with each other.")
    return rows


def _self_test():
    import zipfile
    import os
    import re
    here = os.path.dirname(os.path.abspath(__file__))
    zp = os.path.join(here, "data", "raw", "osf_8neq4_grids.zip")
    if not os.path.exists(zp):
        raise SystemExit(f"run fetch_osf.py first; {zp} is missing")
    z = zipfile.ZipFile(zp)
    t0, naive = {}, {}
    for info in z.infolist():
        m = re.search(r"(pun|novon|aurn|amn)1_(\d+)$", info.filename)
        if m and int(m.group(2)) == 0:
            raw = read_grid(z.read(info.filename))
            t0[m.group(1)] = normalise(raw)
            # The trap is ASSUMING the convention, not reading it. So the
            # naive control forces every header to -180..180 and leaves the
            # array alone, which is exactly what a reader who never looked
            # at lons would get. Passing the real header here instead would
            # make sample() handle 0..360 by itself and the control would
            # pass trivially, which is how it was written the first time.
            naive[m.group(1)] = dict(raw, lons=(-180.0, 180.0), rolled=False)
    rows = anchor_check(t0)
    for r in rows:
        print(f"  {r[0]}  {'ok  ' if r[4] else 'FAIL'}  {r[1]}")
        print(f"        threshold {r[2]}   measured {r[3]}")
    print("\n  the same four grids read WITHOUT normalisation:")
    keys = sorted(naive)
    w = cell_weights(naive[keys[0]])
    worst = max(disagreement_percent(land_mask(naive[a]), land_mask(naive[b]), w)
                for i, a in enumerate(keys) for b in keys[i + 1:])
    bad = [(k, p[0]) for k, g in sorted(naive.items()) for p in PROBES
           if sample(g, p[1], p[2]) != p[3]]
    print(f"        mutual disagreement at t=0  {worst:.2f} %   "
          f"(normalised {rows[2][3]})")
    print(f"        probes failed               {len(bad)} of "
          f"{len(naive) * len(PROBES)}")
    per = {}
    for k, _ in bad:
        per[k] = per.get(k, 0) + 1
    for k in sorted(naive):
        print(f"          {k:6} {per.get(k, 0):2d} of {len(PROBES)} probes wrong")


if __name__ == "__main__":
    _self_test()
