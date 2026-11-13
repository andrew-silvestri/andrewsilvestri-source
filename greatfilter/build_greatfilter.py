"""
Build outputs/payload.json for greatfilter.html from sources.py.

Three computations, each small enough to read:

1. The chain. The wait before each step, measured from the previous step's date (the first from the start of
   the habitable window), and the share of the window already used.

2. The hard-steps model (Carter 1983; Hanson 1998; Watson 2008). Each step is a wait drawn from an exponential
   distribution with its own mean. Keep only the histories in which every step finishes inside the window T.
   In those histories, every hard step (mean much longer than T) takes about T/(n+1), whatever its mean, and so
   does the time left over at the end. Sampling: a history in which all steps finish inside T has every wait
   below T, so each wait is drawn from its exponential cut off at T (inverse-CDF), and a history is kept when
   the waits sum to T or less. This gives the same conditional distribution as plain rejection, which keeps
   about 4 histories in a billion for these means. known_answers() checks the sampler on two cases with an
   exact answer.

3. The Sandberg, Drexler & Ord (2018) prior. Draw every Drake factor from the paper's Table 1 ranges
   (log-uniform), with the rate of abiogenesis log-normal over 50 orders of magnitude, and count the share of
   draws in which the expected number of civilizations in the galaxy, N, is below one.

Run:  python build_greatfilter.py
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sources as S  # noqa: E402

OUT = os.path.join(HERE, "outputs", "payload.json")


# ------------------------------------------------------------------ chain ---
def chain():
    W = S.WINDOW
    T = W["start_ga"] + W["end_gyr"]
    prev, rows = W["start_ga"], []
    for s in S.STEPS:
        rows.append({"key": s["key"], "best": s["best"], "wait": round(prev - s["best"], 3)})
        prev = s["best"]
    waits = [r["wait"] for r in rows]
    return {"T": round(T, 3), "used": round(W["start_ga"] / T, 4), "rows": rows,
            "wait_min": min(waits), "wait_max": max(waits), "wait_mean": round(sum(waits) / len(waits), 3),
            "longest": max(rows, key=lambda r: r["wait"])["key"]}


# -------------------------------------------------------------- hard steps ---
def hard_steps(means, T, n_target, seed):
    """Mean duration of each step, and of the time left after the last, over histories that finish within T."""
    rng = np.random.default_rng(seed)
    means = np.asarray(means, float)
    cap = -np.expm1(-T / means)                 # P(wait <= T) for each step
    kept, drawn = [], 0
    while sum(len(k) for k in kept) < n_target:
        u = rng.random((400_000, len(means)))
        w = -means * np.log1p(-u * cap)          # exponential cut off at T
        ok = w.sum(1) <= T
        kept.append(w[ok])
        drawn += len(w)
    w = np.concatenate(kept)[:n_target]
    left = T - w.sum(1)
    mean = w.mean(0)
    sd = w.std(0)
    return {"T": T, "means": means.tolist(), "dur": [round(float(x), 4) for x in mean],
            "sd": [round(float(x), 4) for x in sd], "left": round(float(left.mean()), 4),
            "p95": [round(float(x), 4) for x in np.percentile(w, 95, axis=0)],
            "accept": round(len(w) / drawn, 5), "n": int(len(w)),
            "flat": round(T / (int((means > T).sum()) + 1), 4)}


def known_answers():
    """Two cases with an exact answer. n equal hard steps: each takes T/(n+1). Hanson 1998, Table 1 case (a
    step with mean 1 in a window of 1, then three of mean 1000 ... see w2-03): skipped here; equal steps test
    the property the page states."""
    out = []
    for n in (3, 4, 5):
        r = hard_steps([1e4] * n, 1.0, 120_000, 7 + n)
        out.append({"n": n, "dur": r["dur"], "left": r["left"], "expect": round(1 / (n + 1), 4)})
    return out


# --------------------------------------------------------------------- SDO ---
def sdo():
    d = S.SDO
    rng = np.random.default_rng(d["seed"])
    n = d["n"]

    def lu(a, b):
        return rng.uniform(np.log10(a), np.log10(b), n)
    lnR = rng.normal(0.0, d["lnR_sd_dex"] * np.log(10), n)
    # f_l = 1 - exp(-lambda); for very small lambda f_l ~ lambda, so work in log10
    fl = -np.expm1(-np.exp(np.clip(lnR, -700, 700)))
    log10fl = np.where(lnR < -30, lnR / np.log(10), np.log10(np.maximum(fl, 1e-300)))
    l10N = (lu(*d["R*"]) + lu(*d["fp"]) + lu(*d["ne"]) + log10fl + lu(*d["fi"]) + lu(*d["fc"]) + lu(*d["L"]))
    return {"p_alone": round(float((l10N < 0).mean()), 4), "median_log10N": round(float(np.median(l10N)), 2),
            "p_univ": round(float((l10N < -10).mean()), 4), "n": n}


def main():
    P = {"chain": chain()}
    P["hard"] = hard_steps(S.HARD["means_gyr"], P["chain"]["T"], S.HARD["n_target"], S.HARD["seed"])
    P["known"] = known_answers()
    P["sdo"] = sdo()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1)
        f.write("\n")
    print(json.dumps(P, indent=1))


if __name__ == "__main__":
    main()
