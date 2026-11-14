"""Depth-resolved CO2 retention from Siegel, DeVries, Doney & Bell (2021).

Source data: "CO2 sequestration fractions", figshare article 15228690,
DOI 10.6084/m9.figshare.15228690 (CC0), file fseq_OCIM2_48L.nc
(3,336,577,442 bytes, md5 a2a751b591c9ac15fa3ac57cbe406015).
Paper: Siegel D.A., DeVries T., Doney S.C., Bell T. (2021) Environ. Res. Lett.
16, 104003, doi:10.1088/1748-9326/ac0be0.

What the file holds (inspected 2026-11-07):
  fseq  (time=1001, cell=405386) float64, chunks (35, 14479)
        fraction of CO2 injected at an ocean grid cell still sequestered
        (not yet returned to the surface/atmosphere) t years after injection.
        Row i is year i (0..1000); the `time` dimension carries no values,
        the authors' plot script states the range is 0-1000 yr.
  MASK, AREA, VOL, DEPTH, LAT, LON, mean_seq_time  (depth=48, lon=180, lat=91)
        MASK == 1 marks ocean (405,386 cells = length of fseq's cell axis);
        the NetCDF 'description' attribute says the reverse and is wrong.
  Cell order: ocean cells taken from MASK in MATLAB column-major order over
  (lat, lon, depth), i.e. C-order over the NetCDF's (depth, lon, lat) array.
  So each depth level is a contiguous block of cells.

Weighting: within an OCIM2 depth level every cell has the same thickness
(VOL/AREA is constant per level, checked at run time), so area weighting and
volume weighting are identical within a level. We weight by cell AREA: the
question is "inject at a random point of ocean at this depth", which is an
area question. Rows with weighting == "none" give plain cell statistics
(each 2x2 degree cell counts once, which over-weights high latitudes).

Usage (the NetCDF may be a local path or the figshare URL; with a URL only
the needed byte ranges are fetched):
  python siegel_retention.py --nc <path-or-url> [--times 25 50 100 200]
         [--out data/siegel2021_retention_by_depth.csv]
         [--halflife-depths 208 2100]   # paper check, reads full curves
"""
import argparse
import os
import sys

import h5py
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from httprange import HTTPRangeFile  # noqa: E402

FIGSHARE_URL = "https://ndownloader.figshare.com/files/41280609"
DEFAULT_OUT = os.path.join(HERE, "data", "siegel2021_retention_by_depth.csv")
DEFAULT_CACHE = os.path.join(HERE, "data", "raw", "siegel2021")


def open_nc(src):
    """h5py handle on a local file or (via HTTP range requests) the URL."""
    if src.startswith("http"):
        return h5py.File(HTTPRangeFile(src), "r")
    return h5py.File(src, "r")


def load_grid(h):
    """Per-ocean-cell level index, depth and area, in fseq's cell order."""
    mask = h["MASK"][:] == 1                      # (48, 180, 91), True = ocean
    area = h["AREA"][:]
    vol = h["VOL"][:]
    depth = h["DEPTH"][:]
    n_cells = h["fseq"].shape[1]
    if mask.sum() != n_cells:
        raise SystemExit(f"MASK ocean count {mask.sum()} != fseq cells {n_cells}")
    # Uniform thickness within each level => area weight == volume weight.
    thick = np.where(mask, vol / area, np.nan)
    spread = np.nanmax(thick, axis=(1, 2)) - np.nanmin(thick, axis=(1, 2))
    if np.nanmax(spread) > 1e-6:
        raise SystemExit("layer thickness varies within a level; revisit weighting")
    level = np.broadcast_to(np.arange(mask.shape[0])[:, None, None], mask.shape)
    return {
        "level": level[mask],                     # C-order == fseq cell order
        "depth": depth[mask],
        "area": area[mask],
        "level_depth": np.array([depth[k][mask[k]][0] for k in range(mask.shape[0])]),
    }


def fseq_rows(h, times, cache_dir):
    """fseq[t, :] for each t, cached as .npy so re-runs need no network."""
    os.makedirs(cache_dir, exist_ok=True)
    out = {}
    for t in times:
        p = os.path.join(cache_dir, f"fseq_t{t:04d}.npy")
        if os.path.exists(p):
            out[t] = np.load(p)
        else:
            print(f"  reading fseq row t={t} ...", flush=True)
            out[t] = h["fseq"][t, :]
            np.save(p, out[t])
    return out


def wquantile(v, w, qs):
    """Weighted quantiles (midpoint cumulative-weight interpolation)."""
    i = np.argsort(v)
    v, w = v[i], w[i]
    cw = (np.cumsum(w) - 0.5 * w) / w.sum()
    return np.interp(qs, cw, v)


def stats_table(grid, rows):
    recs = []
    for t, f in rows.items():
        for k, d in enumerate(grid["level_depth"]):
            sel = grid["level"] == k
            v, a = f[sel], grid["area"][sel]
            for wname, w in (("area", a), ("none", np.ones_like(a))):
                p10, p50, p90 = wquantile(v, w, [0.1, 0.5, 0.9])
                recs.append(dict(depth_m=round(float(d), 1), t_years=t,
                                 mean_fraction=float(np.sum(v * w) / w.sum()),
                                 p10=p10, p50=p50, p90=p90,
                                 n_cells=int(sel.sum()), weighting=wname))
    return pd.DataFrame(recs).sort_values(["weighting", "t_years", "depth_m"])


def halflife(h, grid, depth_m, cache_dir):
    """Per-cell time (yr) at which fseq first falls to 0.5 at the level
    nearest depth_m. Cells still above 0.5 at 1000 yr are censored (the file
    stops at 1000 yr; the paper ran to 5000 yr)."""
    k = int(np.argmin(np.abs(grid["level_depth"] - depth_m)))
    idx = np.flatnonzero(grid["level"] == k)
    lo, hi = idx[0], idx[-1] + 1
    assert hi - lo == idx.size, "level cells not contiguous"
    p = os.path.join(cache_dir, f"fseq_level{k:02d}.npy")
    if os.path.exists(p):
        F = np.load(p)
    else:
        print(f"  reading full curves for level {k} ({idx.size} cells) ...", flush=True)
        F = h["fseq"][:, lo:hi]
        np.save(p, F)
    below = F <= 0.5
    censored = ~below.any(axis=0)
    j = np.argmax(below, axis=0)                  # first year at/below 0.5
    j = np.clip(j, 1, None)
    cols = np.arange(F.shape[1])
    f0, f1 = F[j - 1, cols], F[j, cols]
    with np.errstate(divide="ignore", invalid="ignore"):
        th = (j - 1) + np.where(f0 != f1, (f0 - 0.5) / (f0 - f1), 0.0)
    th = np.where(censored, 1000.0, th)
    a = grid["area"][lo:hi]
    return dict(level=k, depth=grid["level_depth"][k], n=idx.size,
                mean_area=float(np.sum(th * a) / a.sum()),
                sd_area=float(np.sqrt(np.sum(a * (th - np.sum(th * a) / a.sum()) ** 2) / a.sum())),
                median_area=float(wquantile(th, a, [0.5])[0]),
                censored_frac=float(a[censored].sum() / a.sum()))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--nc", default=FIGSHARE_URL, help="local path or URL of fseq_OCIM2_48L.nc")
    ap.add_argument("--times", type=int, nargs="+", default=[25, 50, 100, 200])
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--cache", default=DEFAULT_CACHE)
    ap.add_argument("--halflife-depths", type=float, nargs="*", default=[])
    args = ap.parse_args()

    h = open_nc(args.nc)
    grid = load_grid(h)
    nt = h["fseq"].shape[0]
    if any(t < 0 or t >= nt for t in args.times):
        raise SystemExit(f"times must be within 0..{nt - 1} yr")
    # Sanity: at t=0 every interior cell holds all its CO2 (f=1); the top
    # level (0-10 m) is the model's surface boundary, where f=0 by definition.
    r0 = fseq_rows(h, [0], args.cache)[0]
    top = grid["level"] == 0
    print(f"fseq t=0: level 0 min/max {r0[top].min():.3f}/{r0[top].max():.3f} (expect 0), "
          f"interior min/max {r0[~top].min():.6f}/{r0[~top].max():.6f} (expect 1)")
    if r0[top].max() != 0 or r0[~top].min() != 1:
        raise SystemExit("t=0 row does not match the boundary/initial condition")

    df = stats_table(grid, fseq_rows(h, args.times, args.cache))
    df.to_csv(args.out, index=False, float_format="%.4f", lineterminator=chr(10))   # LF: trap 32
    print(f"wrote {args.out} ({len(df)} rows)")

    # Paper check: area-weighted mean and sd at 50 yr, levels 208 m and 2100 m.
    if 50 in args.times:
        f50 = fseq_rows(h, [50], args.cache)[50]
        for dm in (208, 530, 1022, 2100, 3083):
            k = int(np.argmin(np.abs(grid["level_depth"] - dm)))
            sel = grid["level"] == k
            v, a = f50[sel], grid["area"][sel]
            m = np.sum(v * a) / a.sum()
            sd = np.sqrt(np.sum(a * (v - m) ** 2) / a.sum())
            print(f"check t=50 level {grid['level_depth'][k]:.0f} m: mean {m:.3f} sd {sd:.3f} "
                  f"share of area >0.95: {a[v > 0.95].sum() / a.sum():.3f}")
    for dm in args.halflife_depths:
        r = halflife(h, grid, dm, args.cache)
        print(f"check half-life level {r['depth']:.0f} m: area-mean {r['mean_area']:.0f} yr "
              f"(sd {r['sd_area']:.0f}), area-median {r['median_area']:.0f} yr, "
              f"censored at 1000 yr: {r['censored_frac']:.3f} of area")


if __name__ == "__main__":
    main()
