"""Build sub3/outputs/payload.json from the Berlin Marathon results, 1999-2025.

Input: data/raw/berlin_1999_2025.csv (fetch_public.py; Zenodo 10.5281/zenodo.19342683, CC BY 4.0), checked
against data/fetched.json before it is read. Only year, sex, age group, the halfway split, the 5-km splits
and the net finish time are read; names never leave the raw file.

A finisher is a row with a finish time. "Sub-3" is a net time under 3:00:00 (10,800 s). The halfway band
the page follows is 1:28:30 to 1:29:59 (5,310 to 5,399 s): an even second half from there finishes
between 2:57:00 and 2:59:58, so these are runners on pace for a sub-3 with less than three minutes in hand.

Every figure the page prints is in the payload, with the counts behind it, so the page generator does no
arithmetic on raw data and tests/test_sub3.py can recompute the headline figures from the raw file.

Run:  python build_sub3.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from fetch_public import verified  # noqa: E402

OUT = HERE / "outputs" / "payload.json"
SUB3 = 10800
BAND = (5310, 5400)                      # halfway 1:28:30 to 1:29:59
SPLITS = ["5km", "10km", "15km", "20km", "half", "25km", "30km", "35km", "40km", "final"]
KM = [5, 10, 15, 20, 21.0975, 25, 30, 35, 40, 42.195]
PACE3 = SUB3 / 42.195                    # seconds per km for exactly 3:00:00

# Race days (no race in 2020). Source: the race's list of past editions, cross-checked against
# en.wikipedia.org/wiki/List_of_winners_of_the_Berlin_Marathon. Every date is in summer time (CEST, UTC+2).
DATES = {1999: "1999-09-26", 2000: "2000-09-10", 2001: "2001-09-30", 2002: "2002-09-29", 2003: "2003-09-28",
         2004: "2004-09-26", 2005: "2005-09-25", 2006: "2006-09-24", 2007: "2007-09-30", 2008: "2008-09-28",
         2009: "2009-09-20", 2010: "2010-09-26", 2011: "2011-09-25", 2012: "2012-09-30", 2013: "2013-09-29",
         2014: "2014-09-28", 2015: "2015-09-27", 2016: "2016-09-25", 2017: "2017-09-24", 2018: "2018-09-16",
         2019: "2019-09-29", 2021: "2021-09-26", 2022: "2022-09-25", 2023: "2023-09-24", 2024: "2024-09-29",
         2025: "2025-09-21"}
DWD = "stundenwerte_TU_00433_19510101_20251231_hist.zip"


def race_morning():
    """Mean air temperature at Berlin-Tempelhof, 09:00 to 13:00 local time, on each race day.

    DWD's parameter file says the station's hourly values are in UTC from 1 February 1995, so local
    09:00 to 13:00 (UTC+2) is the five readings stamped 07 to 11."""
    import io
    import zipfile
    z = zipfile.ZipFile(verified(DWD))
    meta = z.read("Metadaten_Parameter_tu_stunde_00433.txt").decode("latin-1")
    if "19950201;20010401;Berlin-Tempelhof;TT_TU" not in meta or meta.count("Stundenwerte in UTC") < 2:
        raise SystemExit("DWD parameter file no longer says UTC from 1995; check the time reference")
    name = next(n for n in z.namelist() if n.startswith("produkt_tu_stunde"))
    d = pd.read_csv(io.BytesIO(z.read(name)), sep=";", skipinitialspace=True, na_values=[-999, "-999"])
    d = d.set_index(pd.to_datetime(d.MESS_DATUM.astype(str), format="%Y%m%d%H"))
    out = {}
    for y, day in DATES.items():
        stamps = [pd.Timestamp(day) + pd.Timedelta(hours=h) for h in range(7, 12)]
        t = d.TT_TU.reindex(stamps)
        if t.isna().any():
            raise SystemExit(f"DWD: missing hourly temperature on {day}")
        out[y] = round(float(t.mean()), 2)
    return out


def seconds(col):
    t = col.fillna("").str.split(":", expand=True)
    if t.shape[1] < 3:
        return pd.Series(np.nan, index=col.index)
    s = pd.to_numeric(t[0], errors="coerce") * 3600 + pd.to_numeric(t[1], errors="coerce") * 60 + \
        pd.to_numeric(t[2], errors="coerce")
    return s.where(s > 0)


def load():
    p = verified("berlin_1999_2025.csv")
    d = pd.read_csv(p, sep=";", dtype=str, usecols=["year", "sex", "age_category"] + SPLITS)
    out = pd.DataFrame({"year": d.year.astype(int), "sex": d.sex, "age": d.age_category})
    for c in SPLITS:
        out[c] = seconds(d[c])
    return out, len(d)


def vdot(dist_m, t_s):
    """Daniels and Gilbert (1979): the VO2 a pace costs over the fraction of VO2max a race of that length allows."""
    v, t = dist_m / (t_s / 60), t_s / 60
    vo2 = -4.60 + 0.182258 * v + 0.000104 * v * v
    frac = 0.8 + 0.1894393 * np.exp(-0.012778 * t) + 0.2989558 * np.exp(-0.1932605 * t)
    return vo2 / frac


def equivalent(dist_m, target):
    """The time over dist_m with the same VDOT, by bisection."""
    lo, hi = 60.0, 30000.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if vdot(dist_m, mid) > target else (lo, mid)
    return (lo + hi) / 2


def repeaters():
    """Runners in the halfway band who had already finished an earlier Berlin under 3:00.

    The file has no runner ID, so a runner is linked across years by name, nationality and sex, held only
    in memory; any such key that appears twice in one year is dropped from the linking, so two people of
    the same name are not counted as one. Only the two counts and shares leave this function."""
    d = pd.read_csv(verified("berlin_1999_2025.csv"), sep=";", dtype=str,
                    usecols=["year", "sex", "name", "nation", "half", "final"])
    d = pd.DataFrame({"year": d.year.astype(int), "half": seconds(d.half), "final": seconds(d.final),
                      "key": d.name.str.lower().str.strip() + "|" + d.nation.fillna("") + "|" + d.sex})
    d = d[d.final.notna()]
    twice = d.groupby(["year", "key"]).size()
    d = d[~d.key.isin({k for (_, k), n in twice.items() if n > 1})]
    first_sub3 = d[d.final < SUB3].groupby("key").year.min()
    d["before"] = d.key.map(first_sub3).lt(d.year)
    B = d[(d.half >= BAND[0]) & (d.half < BAND[1])]
    out = {}
    for flag, g in B.groupby("before"):
        out["had" if flag else "not"] = {"n": int(len(g)), "share": share(g.final < SUB3)}
    out["dropped_keys"] = int(len({k for (_, k), n in twice.items() if n > 1}))
    return out


def r(x, k=4):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), k)


def share(mask):
    return r(100 * mask.mean(), 3) if len(mask) else None


def build():
    D, rows = load()
    F = D[D.final.notna()].copy()
    F["s3"] = F.final < SUB3
    P = {"source": {"rows": rows, "finishers": int(len(F)), "first": int(F.year.min()), "last": int(F.year.max()),
                    "years": sorted(int(y) for y in F.year.unique()),
                    "sexes": {k: int(v) for k, v in F.sex.value_counts().items()}}}

    # --- how rare: by year, by sex
    yr = []
    for y, g in F.groupby("year"):
        m, w = g[g.sex == "M"], g[g.sex == "W"]
        yr.append({"year": int(y), "n": int(len(g)), "sub3": int(g.s3.sum()), "share": share(g.s3),
                   "m_n": int(len(m)), "m_sub3": int(m.s3.sum()), "m_share": share(m.s3),
                   "w_n": int(len(w)), "w_sub3": int(w.s3.sum()), "w_share": share(w.s3)})
    P["by_year"] = yr
    P["all"] = {"n": int(len(F)), "sub3": int(F.s3.sum()), "share": share(F.s3),
                "m_share": share(F[F.sex == "M"].s3), "w_share": share(F[F.sex == "W"].s3),
                "w_sub3": int(F[F.sex == "W"].s3.sum()), "m_sub3": int(F[F.sex == "M"].s3.sum())}

    # --- the halfway band
    H = F[F.half.notna() & (F.final > F.half)].copy()
    P["with_half"] = int(len(H))
    B = H[(H.half >= BAND[0]) & (H.half < BAND[1])].copy()
    fin_min = B.final / 60
    bins = []
    lo, hi = 177, 210                     # 1-minute bins from 2:57 to 3:30, then one tail bin
    for a in range(lo, hi):
        n = int(((fin_min >= a) & (fin_min < a + 1)).sum())
        bins.append({"a": a, "b": a + 1, "n": n})
    tail = int((fin_min >= hi).sum())
    under = int((fin_min < lo).sum())     # ran the second half faster than 1:28:30 allows -- a few
    P["band"] = {
        "lo": BAND[0], "hi": BAND[1], "n": int(len(B)), "sub3": int(B.s3.sum()), "share": share(B.s3),
        "m_n": int((B.sex == "M").sum()), "m_share": share(B[B.sex == "M"].s3),
        "w_n": int((B.sex == "W").sum()), "w_share": share(B[B.sex == "W"].s3),
        "miss5": share((B.final >= SUB3) & (B.final < SUB3 + 300)),
        "miss10": share((B.final >= SUB3) & (B.final < SUB3 + 600)),
        "over15": share(B.final >= SUB3 + 900),
        "over30": share(B.final >= SUB3 + 1800),
        "median_final": r(B.final.median(), 1),
        "bins": bins, "tail_from": hi, "tail": tail, "under_from": lo, "under": under,
        "by_year": [{"year": int(y), "n": int(len(g)), "share": share(g.s3)} for y, g in B.groupby("year")],
        "recent": None,
    }
    rec = B[B.year >= 2019]
    P["band"]["recent"] = {"from": 2019, "n": int(len(rec)), "share": share(rec.s3)}

    # --- chance of a sub-3 by halfway time, one-minute bins
    cur = []
    for a in range(80, 92):
        g = H[(H.half >= a * 60) & (H.half < (a + 1) * 60)]
        cur.append({"a": a, "b": a + 1, "n": int(len(g)), "sub3": int(g.s3.sum()), "share": share(g.s3)})
    P["curve"] = cur

    # --- the near misses: finishers in 3:00:00 to 3:04:59, and where their halfway was
    N = H[(H.final >= SUB3) & (H.final < SUB3 + 300)]
    P["near"] = {"n": int(len(N)), "half_under_90": share(N.half < 5400),
                 "half_under_89": share(N.half < 5340)}

    # --- where the time goes: for the band, median time per segment against even 3:00 pace
    seg = []
    full = B.dropna(subset=["5km", "10km", "15km", "20km", "25km", "30km", "35km", "40km"])
    for grp, g in (("made", full[full.s3]), ("missed", full[~full.s3])):
        prev_t, prev_k, rows_ = 0.0, 0.0, []
        for c, k in zip(SPLITS, KM):
            if c == "half":
                continue
            seg_s = (g[c] - (g[prev_c] if prev_k else 0)) if prev_k else g[c]
            pace = seg_s / (k - prev_k)
            rows_.append({"from": prev_k, "to": k, "pace_median": r(pace.median(), 2),
                          "lost_vs_even_median": r(((pace - PACE3) * (k - prev_k)).median(), 1)})
            prev_c, prev_k = c, k
        seg.append({"group": grp, "n": int(len(g)), "segments": rows_,
                    "behind_at": {c: r((g[c] - PACE3 * k).median(), 1) for c, k in zip(SPLITS, KM)}})
    P["segments"] = seg

    # --- second-half slowdown by finishing band, all finishers with a halfway split
    H["slow"] = (H.final - 2 * H.half) / H.half * 100
    bands = [(0, 180, "under 3:00"), (180, 210, "3:00 to 3:29"), (210, 240, "3:30 to 3:59"),
             (240, 270, "4:00 to 4:29"), (270, 300, "4:30 to 4:59"), (300, 999, "5:00 or more")]
    P["slowdown"] = []
    for a, b, lab in bands:
        g = H[(H.final >= a * 60) & (H.final < b * 60)]
        P["slowdown"].append({"label": lab, "n": int(len(g)), "median_pct": r(g.slow.median(), 2),
                              "neg_split": share(g.slow < 0)})
    s3 = H[H.s3]
    P["sub3_runners"] = {"n": int(len(s3)), "neg_split": share(s3.slow < 0),
                         "half_under_88": share(s3.half < 5280), "median_half": r(s3.half.median(), 1),
                         "median_final": r(s3.final.median(), 1)}

    # --- weather: race-morning temperature against the halfway band's success, by year
    T = race_morning()
    if sorted(T) != P["source"]["years"]:
        raise SystemExit("race dates and result years differ")
    wy = [{"year": x["year"], "temp": T[x["year"]], "n": x["n"], "share": x["share"]} for x in P["band"]["by_year"]]
    tt = np.array([w["temp"] for w in wy]); ss = np.array([w["share"] for w in wy])
    slope = np.polyfit(tt, ss, 1)[0]
    P["weather"] = {"years": wy, "pearson": r(np.corrcoef(tt, ss)[0, 1], 3), "slope_pts_per_c": r(slope, 3),
                    "hottest": int(wy[int(np.argmax(tt))]["year"]), "coolest": int(wy[int(np.argmin(tt))]["year"]),
                    "median_final": {str(y): r(F[F.year == y].final.median(), 1) for y in (2024, 2025)}}

    # --- the counter-check: runners in the band who had broken 3:00 at an earlier Berlin
    P["repeat"] = repeaters()

    # --- the ladder: share of all finishers under each threshold
    P["ladder"] = []
    for t in (10800, 10200, 9000, 8160, 7170):
        vd = vdot(42195, t)
        P["ladder"].append({"sec": t, "n": int((F.final < t).sum()), "share": share(F.final < t),
                            "m": int(((F.final < t) & (F.sex == "M")).sum()),
                            "w": int(((F.final < t) & (F.sex == "W")).sum()),
                            "pace_km": r(t / 42.195, 2), "vdot": r(vd, 2),
                            "half_eq": r(equivalent(21097.5, vd), 0), "tenk_eq": r(equivalent(10000, vd), 0)})

    # --- the 2024 and 2025 races (the page's weather paragraph)
    P["y2024_2025"] = {str(y): next(x for x in yr if x["year"] == y) for y in (2024, 2025)}
    return P


def main():
    P = build()
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1, sort_keys=True)
        f.write("\n")
    b = P["band"]
    print(f"finishers {P['all']['n']:,}; sub-3 {P['all']['sub3']:,} ({P['all']['share']:.2f}%)")
    print(f"halfway 1:28:30-1:29:59: n={b['n']:,}, sub-3 {b['share']:.1f}% (men {b['m_share']:.1f}%, women "
          f"{b['w_share']:.1f}%); missed by <5 min {b['miss5']:.1f}%, >=15 min {b['over15']:.1f}%; "
          f"since 2019 {b['recent']['share']:.1f}% (n={b['recent']['n']:,})")
    print("by year:", ", ".join(f"{x['year']} {x['share']:.0f}%" for x in b["by_year"]))
    print("curve:", ", ".join(f"{c['a']}' {c['share']:.0f}% (n={c['n']})" for c in P["curve"]))
    print(f"near misses 3:00-3:04:59: n={P['near']['n']:,}, half under 1:30 {P['near']['half_under_90']:.1f}%")
    for s in P["segments"]:
        print(s["group"], s["n"], {k: v for k, v in s["behind_at"].items()})
    for s in P["slowdown"]:
        print(f"  {s['label']}: n={s['n']:,} median slowdown {s['median_pct']:.1f}%, negative split {s['neg_split']:.1f}%")
    print("repeat:", P["repeat"])
    print(f"sub-3 runners: negative split {P['sub3_runners']['neg_split']:.1f}%")


if __name__ == "__main__":
    main()
