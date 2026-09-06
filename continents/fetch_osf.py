"""Fetch the four future scenarios from OSF 8NEQ4 and derive the mask set.

Source
------
Davies, H.S., Green, J.A.M. and Duarte, J.C. (2020). Back to the future II:
tidal evolution of four supercontinent scenarios. Earth System Dynamics
11(1), 291-299, doi:10.5194/esd-11-291-2020. Data at OSF project 8NEQ4,
doi:10.17605/OSF.IO/8NEQ4, CC0 1.0 Universal, stated in the paper's data
availability section: "The data is freely available to use according to the
CC0 1.0 license."

The zip is never extracted. Its fifty members total about 400 MB unpacked,
and every one of them is a 1440 x 721 float depth field plus an int mask of
which only the mask is wanted. Members are read one at a time straight out of
the archive, normalised, gated, and packed to a bit-packed npz of about
0.7 MB, which is what the build and the download actually use. Nothing on
any machine ever holds the 400 MB, which also keeps the twelve repo copies
that tests/test_generators.py makes from becoming five gigabytes.

Writes
------
data/future_masks.npz      50 bit-packed land masks, committed
data/osf_provenance.json   the pin, the header table, the gate results, and
                           the negative control, committed

Run:  python3 fetch_osf.py [--force]
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
import urllib.request
import zipfile
from datetime import date, timezone, datetime

import numpy as np

import otis_grid as og

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw", "osf_8neq4_grids.zip")
MASKS = os.path.join(HERE, "data", "future_masks.npz")
PROV = os.path.join(HERE, "data", "osf_provenance.json")

URL = "https://osf.io/download/k6cbj/"
SHA256 = "222a5bbdc8a73f47d8b5163f8d807bc0c2724af0f586d5b4776cc4b384f019ba"
SIZE = 4509458

SCENARIOS = ("pun", "novon", "aurn", "amn")
NAMES = {"pun": "Pangaea Ultima", "novon": "Novopangaea",
         "aurn": "Aurica", "amn": "Amasia"}
EXPECT_AGES = {
    "pun": tuple(list(range(0, 241, 20)) + [250]),
    "aurn": tuple(list(range(0, 241, 20)) + [250]),
    "novon": tuple(range(0, 201, 20)),
    "amn": tuple(range(0, 201, 20)),
}
KNOWN_LONS = ((-180.0, 180.0), (0.0, 360.0))
NAIVE_FLOOR = 25.0          # gate A4, per cent


def download(force=False):
    if os.path.exists(RAW) and not force:
        return False
    os.makedirs(os.path.dirname(RAW), exist_ok=True)
    print(f"  downloading {URL}")
    with urllib.request.urlopen(URL, timeout=300) as r, open(RAW, "wb") as f:
        f.write(r.read())
    return True


def members(z):
    """{scenario: {age: member name}} for the fifty grid files."""
    out = {}
    for info in z.infolist():
        m = re.search(r"(pun|novon|aurn|amn)1_(\d+)$", info.filename)
        if m and not info.is_dir():
            out.setdefault(m.group(1), {})[int(m.group(2))] = info.filename
    return out


def gate_a5(z, mem, headers):
    """The archive is the shape the paper describes."""
    problems = []
    total = sum(len(v) for v in mem.values())
    if total != 50:
        problems.append(f"expected 50 grid members, found {total}")
    for s in SCENARIOS:
        got = tuple(sorted(mem.get(s, {})))
        if got != EXPECT_AGES[s]:
            problems.append(f"{s}: ages {got} != {EXPECT_AGES[s]}")
    for key, h in sorted(headers.items()):
        if (h["n"], h["m"]) != (1440, 721):
            problems.append(f"{key}: shape {(h['n'], h['m'])} != (1440, 721)")
        if tuple(h["lats"]) != (-90.0, 90.0):
            problems.append(f"{key}: lat range {h['lats']} != (-90, 90)")
        if tuple(h["lons"]) not in KNOWN_LONS:
            problems.append(
                f"{key}: longitude convention {h['lons']} is neither of the "
                "two known ones. A third convention means the release changed; "
                "recheck every area number before widening this.")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="re-download even if the archive is present")
    args = ap.parse_args()

    fetched = download(args.force)
    raw_bytes = open(RAW, "rb").read()
    digest = hashlib.sha256(raw_bytes).hexdigest()
    print(f"  {os.path.basename(RAW)}  {len(raw_bytes):,} bytes  sha256 {digest[:16]}...")
    if len(raw_bytes) != SIZE or digest != SHA256:
        sys.exit("; ".join([
            "fetch_osf: the archive is not the pinned one",
            f"expected {SIZE:,} bytes sha256 {SHA256}",
            f"got {len(raw_bytes):,} bytes sha256 {digest}",
            "the deposit changed, so re-pin deliberately and rerun every "
            "gate: a new release can harmonise the longitude conventions, "
            "which would make the page account of the trap false",
        ]))

    z = zipfile.ZipFile(io.BytesIO(raw_bytes))
    mem = members(z)

    headers, packed, shapes = {}, {}, {}
    t0_norm, t0_naive = {}, {}
    for s in SCENARIOS:
        for age, name in sorted(mem[s].items()):
            g = og.read_grid(z.read(name))
            key = f"{s}_{age}"
            headers[key] = {"n": g["n"], "m": g["m"], "lats": list(g["lats"]),
                            "lons": list(g["lons"]), "spacing": g["spacing"]}
            gn = og.normalise(g)
            mask = og.land_mask(gn)
            shapes[key] = mask.shape
            packed[key] = np.packbits(mask)
            if age == 0:
                t0_norm[s] = gn
                # see otis_grid._self_test: the trap is assuming the
                # convention, so the control forces the header and leaves
                # the array untouched
                t0_naive[s] = dict(g, lons=(-180.0, 180.0), rolled=False)

    problems = gate_a5(z, mem, headers)
    if problems:
        for p in problems:
            print("  A5 FAIL " + p)
        sys.exit("fetch_osf: gate A5 failed; nothing written.")
    print(f"  A5  ok    50 members, ages as published, all 1440x721, "
          f"{sum(1 for h in headers.values() if tuple(h['lons']) == (0.0, 360.0))}"
          f" of 50 declare 0..360")

    rows = og.anchor_check(t0_norm)
    for r in rows:
        print(f"  {r[0]}  {'ok  ' if r[4] else 'FAIL'}  {r[1]}")
        print(f"        threshold {r[2]}   measured {r[3]}")

    # A4, the negative control. The gate that catches the longitude trap has
    # to be shown failing on the un-normalised read, or it is not known to
    # work. If a future release harmonises the conventions this fires, and
    # the page's paragraph about the trap must be rewritten rather than
    # silently becoming false.
    w = og.cell_weights(t0_naive["pun"])
    naive_worst = max(
        og.disagreement_percent(og.land_mask(t0_naive[a]),
                                og.land_mask(t0_naive[b]), w)
        for i, a in enumerate(SCENARIOS) for b in SCENARIOS[i + 1:])
    naive_probe_fail = sum(
        1 for g in t0_naive.values() for p in og.PROBES
        if og.sample(g, p[1], p[2]) != p[3])
    a4_ok = naive_worst >= NAIVE_FLOOR and naive_probe_fail > 0
    print(f"  A4  {'ok  ' if a4_ok else 'FAIL'}  negative control: the naive "
          f"read still manufactures a disagreement")
    print(f"        threshold >= {NAIVE_FLOOR} %   measured {naive_worst:.2f} % "
          f"and {naive_probe_fail} of {len(t0_naive) * len(og.PROBES)} probes wrong")
    if not a4_ok:
        sys.exit(
            "fetch_osf: gate A4 failed. The naive read no longer manufactures "
            "a disagreement, which means the deposit's longitude conventions "
            "changed. The page's account of the trap is now false and must be "
            "rewritten before this build is allowed to proceed.")

    if not all(r[4] for r in rows):
        sys.exit("fetch_osf: anchor check failed; nothing written.")

    np.savez_compressed(MASKS, shape=np.array(shapes[f"pun_0"]),
                        **{k: v for k, v in packed.items()})
    prov = {
        "source": "OSF 8NEQ4, doi:10.17605/OSF.IO/8NEQ4",
        "paper": ("Davies, H.S., Green, J.A.M. and Duarte, J.C. (2020). Back "
                  "to the future II: tidal evolution of four supercontinent "
                  "scenarios. Earth System Dynamics 11(1), 291-299, "
                  "doi:10.5194/esd-11-291-2020."),
        "licence": "CC0 1.0 Universal",
        "url": URL, "sha256": digest, "bytes": len(raw_bytes),
        "fetched": datetime.now(timezone.utc).date().isoformat(),
        "downloaded_this_run": fetched,
        "headers": headers,
        "declared_0_360": sorted(k for k, h in headers.items()
                                 if tuple(h["lons"]) == (0.0, 360.0)),
        "ages": {s: list(EXPECT_AGES[s]) for s in SCENARIOS},
        "gate_rows": [{"id": r[0], "what": r[1], "threshold": r[2],
                       "measured": r[3], "passed": bool(r[4])} for r in rows],
        "negative_control": {
            "id": "A4",
            "what": ("the four t=0 grids read without normalising, which is "
                     "what assuming a convention rather than reading it gives"),
            "threshold": f">= {NAIVE_FLOOR} % of the surface",
            "naive_max_disagreement_pct": round(naive_worst, 2),
            "normalised_max_disagreement_pct": round(
                float(rows[2][3].split()[0]), 2),
            "probes_wrong": naive_probe_fail,
            "probes_total": len(t0_naive) * len(og.PROBES),
            "passed": bool(a4_ok),
        },
        "land_pct_t0": {s: round(og.land_percent(g), 3)
                        for s, g in sorted(t0_norm.items())},
        "polar_cut_deg": og.POLAR_CUT,
    }
    json.dump(prov, open(PROV, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print(f"\n  wrote {os.path.relpath(MASKS, HERE)}  "
          f"{os.path.getsize(MASKS):,} bytes  (50 masks, from ~400 MB unpacked)")
    print(f"  wrote {os.path.relpath(PROV, HERE)}  "
          f"{os.path.getsize(PROV):,} bytes")


if __name__ == "__main__":
    main()
