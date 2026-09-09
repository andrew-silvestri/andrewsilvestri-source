"""Draw 1,000 Least Concern birds MATCHED to the 1,837 non-LC modelled ones.

A random draw spends the same money and buys thinner cells. The topic test
is a within-stratum comparison, so the LC species have to sit in the strata
the non-LC species occupy rather than wherever LC birds happen to cluster.

Matched on covariates already on disk, so the matching costs nothing:
family, log10-mass bin (0.5 dex) and description-year decade. Exact
matching on the triple, filled in order of how rare each cell is, so the
scarce cells - which are the ones the non-LC set is unusual in - are served
before the common ones exhaust the pool.

Deterministic: the seed is build_beauty.SEED, and the output is sorted, so
two runs give the same list and the fetch is reproducible.

Writes data/lc_matched.csv (species, family, mass_bin, year_decade).
No network. Run before fetch_topics.py.

Run:  python3 match_lc.py [--n 1000]
"""

import argparse
import collections
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_beauty as B                                      # noqa: E402

OUT = os.path.join(HERE, "data", "lc_matched.csv")


def strata(m):
    """(family, half-dex mass bin, description decade) per species."""
    fam = m["family"].astype(str)
    mb = (np.floor(m["log_mass"] * 2) / 2).round(1)
    dec = ((B.REF_YEAR - m["years_described"]) // 10 * 10).astype(int)
    return list(zip(fam, mb, dec))


def main(n_want):
    _, m, _, _, _ = B.join()
    m = m.copy()
    m["stratum"] = strata(m)
    non_lc = m[m["category"] != "LC"]
    lc = m[m["category"] == "LC"]
    print(f"  modelled {len(m):,}   non-LC {len(non_lc):,}   LC pool {len(lc):,}")

    want = collections.Counter(non_lc["stratum"])
    pool = collections.defaultdict(list)
    for s, st in zip(lc["species"], lc["stratum"]):
        pool[st].append(s)
    for st in pool:
        pool[st].sort()

    rng = np.random.default_rng(B.SEED)
    # Rarest-first: a stratum with few LC candidates is served before a
    # common one, so scarcity is spent where it is scarce.
    order = sorted(want, key=lambda st: (len(pool.get(st, [])), str(st)))
    picked, short = [], []
    # First pass: up to the non-LC count in each stratum, proportionally
    # scaled to the sample size asked for.
    scale = n_want / max(len(non_lc), 1)
    for st in order:
        cand = pool.get(st, [])
        k = min(int(round(want[st] * scale)), len(cand))
        if k < int(round(want[st] * scale)):
            short.append((st, int(round(want[st] * scale)) - len(cand)))
        if k > 0:
            take = list(rng.choice(cand, size=k, replace=False))
            picked.extend(take)
            pool[st] = [s for s in cand if s not in set(take)]

    # Second pass: top up to n_want from the strata that still have LC
    # species, nearest-first by family then mass bin, so the top-up does not
    # drift the sample away from the strata being matched.
    if len(picked) < n_want:
        rest = [(st, s) for st in order for s in pool.get(st, [])]
        rest.sort(key=lambda t: (str(t[0]), t[1]))
        for st, s in rest:
            if len(picked) >= n_want:
                break
            picked.append(s)

    picked = sorted(set(picked))[:n_want]
    info = {s: st for s, st in zip(m["species"], m["stratum"])}
    lc_strata = set(lc["stratum"])
    empty = [st for st in want if st not in lc_strata]
    print(f"  matched LC drawn: {len(picked):,}")
    print(f"  non-LC strata: {len(want):,}; with NO LC bird at all: {len(empty):,} "
          f"({100 * len(empty) / len(want):.0f}%)")
    print(f"    exact family x mass-bin x decade is fine-grained, so many cells")
    print(f"    are empty by construction; the family-level match below is what")
    print(f"    the stratified fit actually leans on.")

    # How well did it match? Report, do not assert.
    got = collections.Counter(info[s] for s in picked)
    fam_w = collections.Counter(st[0] for st in non_lc["stratum"])
    fam_g = collections.Counter(st[0] for st in (info[s] for s in picked))
    tot_w, tot_g = sum(fam_w.values()), sum(fam_g.values())
    tvd = 0.5 * sum(abs(fam_w[f] / tot_w - fam_g.get(f, 0) / tot_g)
                    for f in set(fam_w) | set(fam_g))
    print(f"  family-share total variation distance, matched vs non-LC: {tvd:.3f}")
    print(f"    (0 = identical family mix; a random draw is reported below)")
    rnd = rng.choice(sorted(lc["species"]), size=min(n_want, len(lc)), replace=False)
    fam_r = collections.Counter(info[s][0] for s in rnd)
    tot_r = sum(fam_r.values())
    tvd_r = 0.5 * sum(abs(fam_w[f] / tot_w - fam_r.get(f, 0) / tot_r)
                      for f in set(fam_w) | set(fam_r))
    print(f"  same distance for a RANDOM draw of {len(rnd):,}: {tvd_r:.3f}")
    print(f"  -> matching {'helps' if tvd < tvd_r else 'DOES NOT HELP'}"
          f" ({tvd:.3f} vs {tvd_r:.3f})")

    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["species", "family", "mass_bin", "year_decade"])
        for s in picked:
            f_, mb, dec = info[s]
            w.writerow([s, f_, mb, dec])
    print(f"  -> {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    main(ap.parse_args().n)
