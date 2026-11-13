"""ASHRAE Global Thermal Comfort Database II (v2.1, Zenodo 4993952, CC BY 4.0).

Does the indoor temperature people call "just right" move with the outdoor
climate they have been living in?  Bins indoor air temperature (ta) at 1 C,
computes preference shares and mean thermal sensation per bin, and estimates
three "set point" temperatures per subgroup:

  T_wc    warmer = cooler crossover (linear interpolation on 1 C bins, n>=200)
  T_logit same crossover from a logistic fit of P(warmer | wants a change) on ta
  T_ts0   mean thermal sensation = 0 (interpolation on 1 C bins, n>=200)
  T_ncpk  peak of share "no change" (weighted quadratic on bins within +-4 C
          of the modal-max bin)

95% CIs: cluster bootstrap, resampling buildings (building_id) with
replacement within each subgroup, B reps.  Implemented as integer row weights.

Run:  python analyse_ashrae.py [B]   (reads data/raw, writes outputs/; B defaults to 1000)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
OUT = HERE / "outputs"
MEAS = RAW / "db_measurements_v2.1.0.csv.gz"
META = RAW / "db_metadata.csv"
MIN_N = 200
B = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
SEED = 20261107
PREF = {"warmer": 1, "no change": 0, "cooler": -1}


def adaptive(t_out):
    """de Dear & Brager 2002, Energy & Buildings 34:549-561, Eq. 1 (NV bldgs,
    mean monthly outdoor dry-bulb; stated range 10-33 C)."""
    return 0.31 * np.asarray(t_out, float) + 17.8


# ---------------------------------------------------------------- load
def load():
    d = pd.read_csv(MEAS, low_memory=False, na_values=["NA"])
    m = pd.read_csv(META)
    counts = {"rows_raw": len(d)}
    d = d.merge(m[["building_id", "climate", "building_type", "cooling_type",
                   "database", "country", "quality_assurance"]],
                on="building_id", how="left")
    d = d[d["ta"].notna()]
    counts["rows_with_ta"] = len(d)
    d = d[d["thermal_preference"].isin(PREF)]
    counts["rows_ta_and_preference"] = len(d)
    d = d.copy()
    d["pref"] = d["thermal_preference"].map(PREF).astype(int)
    d["bin"] = np.floor(d["ta"]).astype(int)
    counts["buildings"] = d["building_id"].nunique()
    counts["rows_with_t_mot_isd"] = int(d["t_mot_isd"].notna().sum())
    counts["rows_with_t_out"] = int(d["t_out"].notna().sum())
    counts["rows_with_sensation"] = int(d["thermal_sensation"].notna().sum())
    counts["rows_with_top"] = int(d["top"].notna().sum())
    return d, counts


# ---------------------------------------------------------------- stats
def bin_stats(bins, pref, ts, w, lo, hi):
    """Weighted per-bin stats.  bins already offset to 0..K-1."""
    K = hi - lo + 1
    n = np.bincount(bins, w, K)
    nw = np.bincount(bins, w * (pref == 1), K)
    nc = np.bincount(bins, w * (pref == -1), K)
    nn = np.bincount(bins, w * (pref == 0), K)
    ok = ~np.isnan(ts)
    tsn = np.bincount(bins[ok], w[ok], K)
    tss = np.bincount(bins[ok], w[ok] * ts[ok], K)
    with np.errstate(invalid="ignore", divide="ignore"):
        return dict(n=n, w=nw / n, c=nc / n, nc=nn / n,
                    ts=tss / tsn, n_ts=tsn)


def crossing(x, y, n, direction):
    """x where y crosses 0 between consecutive points; direction +1 means
    y goes - to +, -1 means + to -.  If several, take the pair with most n."""
    best, bestn = np.nan, -1
    for i in range(len(x) - 1):
        a, b = y[i], y[i + 1]
        if np.isnan(a) or np.isnan(b):
            continue
        if (direction > 0 and a < 0 <= b) or (direction < 0 and a > 0 >= b):
            tot = n[i] + n[i + 1]
            if tot > bestn:
                bestn = tot
                best = x[i] + (x[i + 1] - x[i]) * (0 - a) / (b - a)
    return best


def nc_peak(x, y, n):
    if len(x) < 3:
        return np.nan
    k = int(np.argmax(y))
    sel = np.abs(x - x[k]) <= 4
    if sel.sum() < 3:
        return np.nan
    c = np.polyfit(x[sel], y[sel], 2, w=np.sqrt(n[sel]))
    if c[0] >= 0:
        return np.nan
    v = -c[1] / (2 * c[0])
    return v if x[sel].min() <= v <= x[sel].max() else np.nan


def logit_cross(t, y, w):
    """Weighted logistic P(y=1) = 1/(1+exp(-(b0+b1 t))); returns -b0/b1."""
    if w.sum() < 50 or len(np.unique(y[w > 0])) < 2:
        return np.nan
    tc = t - 24.0
    X = np.column_stack([np.ones_like(tc), tc])
    beta = np.zeros(2)
    for _ in range(50):
        p = 1 / (1 + np.exp(-(X @ beta)))
        W = w * p * (1 - p)
        H = X.T @ (X * W[:, None])
        g = X.T @ (w * (y - p))
        try:
            step = np.linalg.solve(H, g)
        except np.linalg.LinAlgError:
            return np.nan
        beta += step
        if np.abs(step).max() < 1e-8:
            break
    if beta[1] >= 0:  # warmer must become less likely as ta rises
        return np.nan
    return 24.0 - beta[0] / beta[1]


def estimates(g, w):
    lo, hi = int(g["bin"].min()), int(g["bin"].max())
    bins = g["bin"].to_numpy() - lo
    pref = g["pref"].to_numpy()
    ts = g["thermal_sensation"].to_numpy(float)
    s = bin_stats(bins, pref, ts, w, lo, hi)
    x = np.arange(lo, hi + 1) + 0.5
    keep = s["n"] >= MIN_N
    xk = x[keep]
    out = {
        "T_wc": crossing(xk, (s["w"] - s["c"])[keep], s["n"][keep], -1),
        "T_ncpk": nc_peak(xk, s["nc"][keep], s["n"][keep]),
    }
    kt = s["n_ts"] >= MIN_N
    out["T_ts0"] = crossing(x[kt], s["ts"][kt], s["n_ts"][kt], +1)
    ch = pref != 0
    out["T_logit"] = logit_cross(g["ta"].to_numpy()[ch],
                                 (pref[ch] == 1).astype(float), w[ch])
    return out, s, x, keep


def run_group(name, g, rng, tout_col="t_mot_isd"):
    g = g.reset_index(drop=True)
    w0 = np.ones(len(g))
    est, s, x, keep = estimates(g, w0)
    bids = g["building_id"].to_numpy()
    ub, inv = np.unique(bids, return_inverse=True)
    boot = {k: [] for k in est}
    for _ in range(B):
        draw = rng.integers(0, len(ub), len(ub))
        cnt = np.bincount(draw, minlength=len(ub)).astype(float)
        e, *_ = estimates(g, cnt[inv])
        for k in e:
            boot[k].append(e[k])
    tout = g[tout_col]
    rows = []
    for k, v in est.items():
        bv = np.array(boot[k])
        ok = ~np.isnan(bv)
        lo, hi = (np.percentile(bv[ok], [2.5, 97.5]) if ok.sum() > 20
                  else (np.nan, np.nan))
        inr = (bool(keep.any()) and not np.isnan(v)
               and x[keep].min() - 0.5 <= v <= x[keep].max() + 0.5)
        rows.append(dict(group=name, metric=k, estimate=v, ci_lo=lo, ci_hi=hi,
                         in_bin_range=inr,
                         boot_ok=int(ok.sum()), boot_B=B, n=len(g),
                         n_buildings=len(ub),
                         bins_used=f"{x[keep].min()-0.5:.0f}-{x[keep].max()+0.5:.0f}"
                         if keep.any() else "",
                         tout_col=tout_col,
                         tout_mean=tout.mean(), tout_median=tout.median(),
                         adaptive_pred_at_mean=float(adaptive(tout.mean()))
                         if tout.notna().any() else np.nan))
    tab = pd.DataFrame(dict(group=name, ta_bin_lo=x - 0.5, ta_bin_hi=x + 0.5,
                            n=s["n"].astype(int), included=keep,
                            share_no_change=s["nc"], share_warmer=s["w"],
                            share_cooler=s["c"], mean_sensation=s["ts"],
                            n_sensation=s["n_ts"].astype(int)))
    return rows, tab, boot


def main():
    rng = np.random.default_rng(SEED)
    d, counts = load()
    print("counts", counts)
    nv = d["cooling_type"] == "naturally ventilated"
    ac = d["cooling_type"] == "air conditioned"
    tm, to = d["t_mot_isd"], d["t_out"]
    groups = [
        ("all", d, "t_mot_isd"),
        ("tmot<10", d[tm < 10], "t_mot_isd"),
        ("tmot10-25", d[(tm >= 10) & (tm <= 25)], "t_mot_isd"),
        ("tmot>25", d[tm > 25], "t_mot_isd"),
        ("tout<10", d[to < 10], "t_out"),
        ("tout>25", d[to > 25], "t_out"),
        ("season=winter", d[d["season"] == "winter"], "t_mot_isd"),
        ("season=summer", d[d["season"] == "summer"], "t_mot_isd"),
        ("NV,tmot<10", d[nv & (tm < 10)], "t_mot_isd"),
        ("NV,tmot>25", d[nv & (tm > 25)], "t_mot_isd"),
        ("AC,tmot<10", d[ac & (tm < 10)], "t_mot_isd"),
        ("AC,tmot>25", d[ac & (tm > 25)], "t_mot_isd"),
        ("noRP884,tmot<10", d[(d["database"] != 1.0) & (tm < 10)], "t_mot_isd"),
        ("noRP884,tmot>25", d[(d["database"] != 1.0) & (tm > 25)], "t_mot_isd"),
    ]
    # operative-temperature sensitivity: rebin on top where present
    dt = d[d["top"].notna()].copy()
    dt["ta"] = dt["top"]
    dt["bin"] = np.floor(dt["ta"]).astype(int)
    groups += [("TOP,tmot<10", dt[dt["t_mot_isd"] < 10], "t_mot_isd"),
               ("TOP,tmot>25", dt[dt["t_mot_isd"] > 25], "t_mot_isd")]

    allrows, tabs, boots = [], [], {}
    for name, g, col in groups:
        r, t, b = run_group(name, g, rng, col)
        allrows += r
        tabs.append(t)
        boots[name] = b
        print(name, len(g), {x["metric"]: round(x["estimate"], 2) for x in r})

    # differences hot - cold with paired-free CI (independent bootstraps)
    diffs = []
    for hot, cold in [("tmot>25", "tmot<10"), ("tout>25", "tout<10"),
                      ("season=summer", "season=winter"),
                      ("NV,tmot>25", "NV,tmot<10"), ("AC,tmot>25", "AC,tmot<10"),
                      ("noRP884,tmot>25", "noRP884,tmot<10"),
                      ("TOP,tmot>25", "TOP,tmot<10")]:
        for k in boots[hot]:
            h, c = np.array(boots[hot][k]), np.array(boots[cold][k])
            dd = h - c
            ok = ~np.isnan(dd)
            eh = [r for r in allrows if r["group"] == hot and r["metric"] == k][0]
            ec = [r for r in allrows if r["group"] == cold and r["metric"] == k][0]
            lo, hi = (np.percentile(dd[ok], [2.5, 97.5]) if ok.sum() > 20
                      else (np.nan, np.nan))
            diffs.append(dict(group=f"{hot} minus {cold}", metric=k,
                              estimate=eh["estimate"] - ec["estimate"],
                              ci_lo=lo, ci_hi=hi, boot_ok=int(ok.sum()),
                              boot_B=B, n=eh["n"] + ec["n"],
                              n_buildings=eh["n_buildings"] + ec["n_buildings"],
                              tout_col=eh["tout_col"],
                              tout_mean=eh["tout_mean"] - ec["tout_mean"],
                              adaptive_pred_at_mean=eh["adaptive_pred_at_mean"]
                              - ec["adaptive_pred_at_mean"]))

    # adaptive-model comparison: 3 C bins of t_mot_isd, logistic crossover
    adapt, slopes, abo = [], [], {}
    nr = d["database"] != 1.0
    subsets = [("all", d), ("NV", d[nv]), ("all_noRP884", d[nr]),
               ("NV_noRP884", d[nv & nr])]
    for label, sub in subsets:
        s = sub[sub["t_mot_isd"].notna()]
        edges = np.arange(-6, 34, 3)
        for a, b_ in zip(edges[:-1], edges[1:]):
            g = s[(s["t_mot_isd"] >= a) & (s["t_mot_isd"] < b_)]
            if len(g) < 500:
                continue
            r, _, bt = run_group(f"{label},tmot[{a},{b_})", g, rng)
            for x in r:
                if x["metric"] in ("T_logit", "T_wc", "T_ts0"):
                    x["subset"] = label
                    x["tmot_lo"], x["tmot_hi"] = a, b_
                    adapt.append(x)
                    abo[(label, a, x["metric"])] = (x["tout_mean"],
                                                    x["estimate"],
                                                    np.array(bt[x["metric"]]),
                                                    x["in_bin_range"])
    # OLS slope of the set-point estimate on mean t_mot across outdoor bins,
    # CI from the per-bin cluster bootstraps (independent across bins)
    for label, _ in subsets:
        for met in ("T_logit", "T_wc", "T_ts0"):
            # only outdoor bins whose estimate lies inside their own data
            items = [v for k, v in abo.items()
                     if k[0] == label and k[2] == met and v[3]]
            xs = np.array([i[0] for i in items])
            ys = np.array([i[1] for i in items])
            okp = ~np.isnan(ys)
            if okp.sum() < 3:
                continue
            c = np.polyfit(xs[okp], ys[okp], 1)
            bs = []
            for rep in range(B):
                yr = np.array([i[2][rep] for i in items])
                ok = ~np.isnan(yr) & (yr > 10) & (yr < 40)
                if ok.sum() >= 3:
                    bs.append(np.polyfit(xs[ok], yr[ok], 1)[0])
            lo, hi = (np.percentile(bs, [2.5, 97.5]) if len(bs) > 20
                      else (np.nan, np.nan))
            slopes.append(dict(subset=label, metric=met, slope=c[0],
                               intercept=c[1], slope_ci_lo=lo, slope_ci_hi=hi,
                               n_outdoor_bins=int(okp.sum()),
                               tmot_range=f"{xs[okp].min():.1f}-{xs[okp].max():.1f}",
                               ref_slope=0.31, ref_intercept=17.8))
    out = pd.DataFrame(allrows + diffs)
    out.to_csv(OUT / "ashrae_crossovers.csv", index=False, float_format="%.3f", lineterminator="\n")
    pd.concat(tabs).to_csv(OUT / "ashrae_bins_by_group.csv", index=False, lineterminator="\n",
                           float_format="%.4f")
    tabs[0].to_csv(OUT / "ashrae_bins_all.csv", index=False, lineterminator="\n",
                   float_format="%.4f")
    pd.DataFrame(adapt).to_csv(OUT / "ashrae_adaptive_bins.csv", index=False, lineterminator="\n",
                               float_format="%.3f")
    sl = pd.DataFrame(slopes)
    sl.to_csv(OUT / "ashrae_adaptive_slopes.csv", index=False, lineterminator="\n",
              float_format="%.3f")
    pd.Series(counts).to_csv(OUT / "ashrae_counts.csv", header=["value"], lineterminator="\n")
    pd.set_option("display.width", 250)
    print(out.drop(columns=["boot_B"]).to_string())
    print(pd.DataFrame(adapt)[["group", "metric", "estimate", "ci_lo", "ci_hi",
                               "n", "n_buildings", "tout_mean",
                               "adaptive_pred_at_mean"]].to_string())
    print(sl.to_string())


if __name__ == "__main__":
    main()
