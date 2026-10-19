"""Reconcile the RRC's Texas Permian against EIA's Permian region, by month.

The two do not measure the same thing, so agreement is not expected; what is
asked is whether their ratio is stable enough that one can stand for the
other's shape. They differ in three ways, each named so a residual can be
read against it:
- area: RRC districts 7C, 08, 8A are Texas only; EIA's region adds four New
  Mexico counties (DPR RegionCounties) and draws Texas by county, not district;
- stage: RRC is Form PR production at the lease (gross); STEO 5a is marketed
  (gross less repressuring, vented and flared, and nonhydrocarbon gases
  removed, per EIA's definition);
- lag: RRC's latest months are incomplete until late reports arrive, so the
  last `RRC_LAG` months are left out.

Run:  python reconcile.py        prints the table STAGE1.md quotes
"""
import statistics as st

import sources

RRC_LAG = 6  # months at the end of the RRC series left out as still filling in


def ratio_table(num, den):
    keys = sorted(set(num) & set(den))
    return {k: num[k] / den[k] for k in keys}


def summary(r):
    v = list(r.values())
    return {"n": len(v), "first": min(r), "last": max(r), "mean": st.fmean(v),
            "sd": st.pstdev(v), "min": min(v), "max": max(v)}


def rrc_settled():
    rrc = sources.rrc_permian()
    keys = sorted(rrc)
    return {k: rrc[k] for k in keys[:-RRC_LAG]}


def by_year(r):
    out = {}
    for (y, _m), v in r.items():
        out.setdefault(y, []).append(v)
    return {y: (st.fmean(v), min(v), max(v), len(v)) for y, v in sorted(out.items())}


def main():
    rrc = rrc_settled()
    steo = sources.steo_permian()
    dpr = sources.dpr_permian()
    print("STEO release", sources.steo_release())
    print("RRC settled through", max(rrc), "(raw through", max(sources.rrc_permian()), ")")
    for name, den in (("RRC / STEO marketed", steo), ("RRC / DPR total", dpr)):
        r = ratio_table(rrc, den)
        s = summary(r)
        print(f"\n{name}: n={s['n']} {s['first']}..{s['last']} mean={s['mean']:.4f} "
              f"sd={s['sd']:.4f} range {s['min']:.4f}..{s['max']:.4f}")
        for y, (m, lo, hi, n) in by_year(r).items():
            print(f"  {y}  mean {m:.4f}  range {lo:.4f}..{hi:.4f}  n={n}")
    r = ratio_table(steo, dpr)
    s = summary(r)
    print(f"\nSTEO / DPR (EIA against itself): n={s['n']} mean={s['mean']:.4f} sd={s['sd']:.4f} "
          f"range {s['min']:.4f}..{s['max']:.4f}")


if __name__ == "__main__":
    main()
