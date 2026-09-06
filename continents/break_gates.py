"""Break each gate on purpose and check the build refuses.

A gate that has never been seen to fail is not known to work, and that
applies to the gates themselves. This copies the project to a temporary
directory, damages one input in a way that produces a plausible wrong answer
rather than an error, runs build_continents.py, and checks that it exits
non-zero and writes no payload.

Nothing under the real tree is touched. Writes nothing anywhere except the
temporary copies, which it removes.

Run:  python3 break_gates.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))


# ---------------------------------------------------------------- damages

def roll_one_scenario(d):
    """A1: put Aurica back on the convention it was read off, un-normalised.

    This is the original trap, reproduced exactly: one scenario half a world
    out, every file still a valid grid, every number downstream still
    plausible.
    """
    p = os.path.join(d, "data", "future_masks.npz")
    z = dict(np.load(p))
    shape = tuple(int(v) for v in z["shape"])
    for k in list(z):
        if k.startswith("aurn_"):
            m = np.unpackbits(z[k])[:shape[0] * shape[1]].reshape(shape)
            z[k] = np.packbits(np.roll(m.astype(bool), shape[0] // 2, axis=0))
    np.savez_compressed(p, **z)
    return "one scenario rolled 180 degrees, as an un-normalised read gives"


def invert_mask(d):
    """A2: swap land for sea. Every map still draws; the world is inside out."""
    p = os.path.join(d, "data", "future_masks.npz")
    z = dict(np.load(p))
    shape = tuple(int(v) for v in z["shape"])
    for k in list(z):
        if k == "shape":
            continue
        m = np.unpackbits(z[k])[:shape[0] * shape[1]].reshape(shape)
        z[k] = np.packbits(~m.astype(bool))
    np.savez_compressed(p, **z)
    return "land and sea swapped in every scenario"


def harmonise_conventions(d):
    """A4: the negative control. Pretend a future release fixed the
    conventions, so the naive read no longer manufactures a disagreement.
    Every positive gate still passes; the page's account of the trap is now
    false and must be rewritten rather than quietly kept."""
    p = os.path.join(d, "data", "osf_provenance.json")
    j = json.load(open(p, encoding="utf-8"))
    j["negative_control"]["naive_max_disagreement_pct"] = 0.8
    json.dump(j, open(p, "w", encoding="utf-8"))
    return "the naive read no longer disagrees, so the trap is gone"


def nudge_itrf(d):
    """B1a: move one published pole a little. Velocities at the stations
    barely move; the rotation vector does. This is the failure break_b1.py
    showed the station-level check cannot see."""
    p = os.path.join(d, "data", "ITRF2020-PMM.dat")
    out = []
    for line in open(p, encoding="utf-8"):
        f = line.split()
        if len(f) == 4 and f[0] == "SOAM":
            v = [float(x.rstrip(",")) for x in f[1:]]
            v[2] += 0.05
            line = f"   SOAM  {v[0]:8.4f},  {v[1]:9.4f},  {v[2]:9.4f},\n"
        out.append(line)
    open(p, "w", encoding="utf-8").writelines(out)
    return "one published rotation vector moved 0.05 deg/Myr"


def swap_coordinates(d):
    """C2: the service starts returning lat,lon instead of lon,lat. Every
    distance stays plausible; every position is wrong. This is the one thing
    regime 2 has no external anchor for, and the age-0 identity is the only
    check that sees it."""
    p = os.path.join(d, "data", "gplates_cache.json")
    j = json.load(open(p, encoding="utf-8"))
    for k, v in j["responses"].items():
        if isinstance(v, list):
            j["responses"][k] = [None if q is None else [q[1], q[0]] for q in v]
    json.dump(j, open(p, "w", encoding="utf-8"))
    return "the service's coordinate order swapped"


def drop_contamination(d):
    """B4: the other negative control. Pretend the source file reassigned the
    Hawaiian stations, so the exclusion rule has nothing left to do. Every
    positive gate passes and the page still says the exclusion matters."""
    p = os.path.join(d, "data", "stations.csv")
    rows = open(p, encoding="utf-8").read().splitlines()
    out = [rows[0]]
    for r in rows[1:]:
        f = r.split(",")
        lat, lon, plate = float(f[1]), float(f[2]), f[8]
        if plate == "PA" and (18.5 <= lat <= 22.5 and -161 <= lon <= -154
                              or lat > 50 or f[0] == "ILSG"):
            continue
        out.append(r)
    open(p, "w", encoding="utf-8").write("\n".join(out) + "\n")
    return "every contaminated Pacific station removed from the input"


CASES = [
    ("A1", "named land/sea probes", roll_one_scenario),
    ("A2", "Earth's land fraction", invert_mask),
    ("A4", "negative control, longitude", harmonise_conventions),
    ("B1a", "rotation vector vs ITRF2020-PMM", nudge_itrf),
    ("B4", "negative control, Pacific", drop_contamination),
    ("C2", "identity at age 0", swap_coordinates),
]


def main():
    print("Each gate, broken on purpose. The build must refuse and write "
          "nothing.\n")
    print(f"  {'gate':5} {'what was damaged':52} {'build':>8} {'payload':>9}")
    print("  " + "-" * 78)
    bad = []
    for gid, _what, damage in CASES:
        d = tempfile.mkdtemp(prefix="break-gate-")
        try:
            proj = os.path.join(d, "continents")
            shutil.copytree(HERE, proj, ignore=shutil.ignore_patterns(
                "data", "__pycache__", "outputs"))
            shutil.copytree(os.path.join(HERE, "data"),
                            os.path.join(proj, "data"),
                            ignore=shutil.ignore_patterns("raw"))
            os.makedirs(os.path.join(proj, "outputs"), exist_ok=True)
            for f in ("sitefig.py", "fig_floor.py"):
                shutil.copy(os.path.join(ROOT, f), d)
            note = damage(proj)
            r = subprocess.run([sys.executable, "build_continents.py"],
                               cwd=proj, capture_output=True, text=True,
                               timeout=600)
            wrote = os.path.exists(os.path.join(
                proj, "outputs", "continents_payload.json"))
            ok = r.returncode != 0 and not wrote
            print(f"  {gid:5} {note[:52]:52} "
                  f"{'refused' if r.returncode else 'ACCEPTED':>8} "
                  f"{'none' if not wrote else 'WRITTEN':>9}")
            if not ok:
                bad.append(f"{gid}: the build did not refuse")
        finally:
            shutil.rmtree(d, ignore_errors=True)
    print("")
    if bad:
        print("FAIL")
        for b in bad:
            print("  - " + b)
        return 1
    print(f"ok - all {len(CASES)} gates refused a plausible wrong input")
    return 0


if __name__ == "__main__":
    sys.exit(main())
