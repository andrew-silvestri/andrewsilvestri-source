"""Break the gate before trusting it: agreeing with a published model at a
plate's own stations does not pin that plate's rotation.

The gate under test was going to be, in one line: a fitted rotation must
reproduce ITRF2020-PMM's velocities at that plate's stations to better than
1.5 mm/yr. That is a check on a summary statistic, and a summary statistic
does not pin the parameters behind it.

Here is why. Fitting a plate is least squares on

    v = omega x r

over the stations. If the stations cover a small patch, the matrix is badly
conditioned: there is a direction in rotation-vector space along which omega
can be moved a long way while barely moving any velocity inside the patch.
The smallest right singular vector of the design matrix IS that direction.
Move along it and the gate cannot tell.

This script does exactly that, for every plate, and reports how far the
rotation can be pushed while the station-level check still passes. It writes
nothing. It exists so the two gates that replace the single one have a
measured reason to exist.

Run:  python3 break_b1.py
"""
import numpy as np

import plates as P

STATION_GATE = 1.5      # mm/yr, the check being broken


def main():
    st = [s for s in P.load_stations()
          if s["dur"] >= P.MIN_YEARS and s["sve"] <= P.MAX_SIGMA
          and s["svn"] <= P.MAX_SIGMA and s["plate"] in P.ITRF_CODE]
    bp = P.boundary_points()
    d = P.distance_to_boundary([s["lat"] for s in st],
                               [s["lon"] for s in st], bp)
    by = {}
    for s, dd in zip(st, d):
        if dd > P.FAR_KM:
            by.setdefault(s["plate"], []).append(s)

    print("How far can a plate's rotation be wrong while still agreeing with")
    print("ITRF2020-PMM at every one of that plate's own stations?")
    print("")
    print(f"{'plate':13} {'n':>5} {'extent':>13} {'cond':>8} "
          f"{'d omega':>9} {'at stns':>9} {'over plate':>11}")
    print(f"{'':13} {'':>5} {'deg lat x lon':>13} {'A':>8} "
          f"{'deg/Myr':>9} {'mm/yr':>9} {'mm/yr':>11}")
    print("-" * 78)

    worst = None
    for code in sorted(by, key=lambda c: -len(by[c])):
        s = by[code]
        if len(s) < P.MIN_STATIONS:
            continue
        omega, kept, _dropped, _it = P.fit_with_exclusions(s)
        la = [x["lat"] for x in kept]
        lo = [x["lon"] for x in kept]
        A = P.design(la, lo)
        # the direction omega can move in without the stations noticing
        _u, sv, vt = np.linalg.svd(A, full_matrices=False)
        weak = vt[-1]
        cond = sv[0] / sv[-1]

        # scale it until the station-level check is just about to fail
        lo_s, hi_s = 0.0, 1.0
        for _ in range(60):
            mid = (lo_s + hi_s) / 2.0
            trial = omega + mid * weak * np.linalg.norm(omega)
            e1, n1 = P.velocity(trial, la, lo)
            e2, n2 = P.velocity(omega, la, lo)
            if np.median(np.hypot(e1 - e2, n1 - n2)) < STATION_GATE:
                lo_s = mid
            else:
                hi_s = mid
        trial = omega + lo_s * weak * np.linalg.norm(omega)

        e1, n1 = P.velocity(trial, la, lo)
        e2, n2 = P.velocity(omega, la, lo)
        at_stn = float(np.median(np.hypot(e1 - e2, n1 - n2)))
        pla, plo = P.plate_area_sample(kept)
        e1, n1 = P.velocity(trial, pla, plo)
        e2, n2 = P.velocity(omega, pla, plo)
        over = float(np.percentile(np.hypot(e1 - e2, n1 - n2), 95))
        d_om = float(np.linalg.norm(P.deg_per_myr(trial - omega)))
        rate = P.pole_of(omega)[2]

        ext = (max(la) - min(la), max(lo) - min(lo))
        print(f"{P.PLATE_NAME[code]:13} {len(kept):5d} "
              f"{ext[0]:6.0f} x{ext[1]:5.0f} {cond:8.0f} "
              f"{d_om:9.3f} {at_stn:9.2f} {over:11.1f}")
        if worst is None or d_om / rate > worst[1]:
            worst = (code, d_om / rate, d_om, rate, at_stn, over, len(kept))

    code, frac, d_om, rate, at_stn, over, n = worst
    print("")
    print(f"Worst case: {P.PLATE_NAME[code]}, {n} stations.")
    print(f"  Its rotation can be moved {d_om:.3f} deg/Myr - {frac * 100:.0f} "
          f"per cent of the plate's own rate of {rate:.3f} - while the median")
    print(f"  velocity difference at its own stations stays {at_stn:.2f} mm/yr,")
    print(f"  under the {STATION_GATE} mm/yr gate. Over the plate's extent the "
          f"same change is {over:.0f} mm/yr.")
    print("")
    print(f"So the station-level check passes on a rotation wrong by "
          f"{frac * 100:.0f} per cent of its")
    print("own magnitude. It is kept, because it is the right check for a")
    print("contaminated station, and the gate on the parameters is added")
    print("beside it:")
    print("  B1a  the rotation VECTOR against ITRF2020-PMM's, in deg/Myr.")
    print("       This is the one that pins the plate.")
    print("  B1b  velocity sampled over the stations' full extent rather than")
    print("       at the stations. Supplementary: the extent of a receiver")
    print("       network is still not the extent of a plate, and without")
    print("       plate polygons this page cannot claim otherwise.")


if __name__ == "__main__":
    main()
