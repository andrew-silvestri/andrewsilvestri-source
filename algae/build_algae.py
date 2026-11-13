"""Build outputs/payload.json for the algae page.

Inputs
- data/raw/gcb2025.xlsx (fetch_public.py; refused unless its SHA-1 matches data/fetched.json)
- data/siegel2021_retention_by_depth.csv (siegel_retention.py, from the CC0 OCIM2 file)
- params.py: published figures, each with its source

Before it writes anything, the build reproduces figures the sources print:
- GCB 2025: ocean sink 3.2 GtC a year, mean of 2015-2024 (Friedlingstein et al. 2026, abstract).
- Siegel 2021 p. 4: CO2 injected at 208 m, mean fraction left after 50 years 15 percent (sd 16 percent),
  a plain mean over grid cells; at 2,100 m "more than 95%" left after 50 years outside the
  Antarctic Polar Front (checked as the area median).

Run:  python build_algae.py
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import params as PR  # noqa: E402
from netfetch import verified  # noqa: E402

OUT = os.path.join(HERE, "outputs", "payload.json")
SIEGEL = os.path.join(HERE, "data", "siegel2021_retention_by_depth.csv")

PRINTED = {
    "gcb_ocean_2015_2024": (3.2, 0.05),       # GtC/yr, Friedlingstein et al. 2026 abstract
    "siegel_208m_50y_mean": (0.15, 0.02),     # Siegel 2021 p. 4, plain mean over cells
    "siegel_208m_50y_sd": (0.16, 0.03),
    "siegel_2100m_50y_median_min": 0.95,      # Siegel 2021 p. 4-5, "more than 95%"
}


def gcb():
    import pandas as pd
    path, row = verified("gcb2025.xlsx")
    d = pd.read_excel(path, sheet_name="Global Carbon Budget", header=None)
    h = d.index[d[0].astype(str).str.strip() == "Year"][0]
    t = d.iloc[h + 1:, :8].copy()
    t.columns = ["year", "fossil", "luc", "atm", "ocean", "land", "cement_sink", "imbalance"]
    t = t[pd.to_numeric(t.year, errors="coerce").notna()].astype(float)
    t["year"] = t.year.astype(int)
    t = t.set_index("year")
    last = int(t.index.max())
    resid = (t.fossil + t.luc - t.atm - t.ocean - t.land - t.cement_sink - t.imbalance).abs().max()
    if resid > 0.02:
        raise SystemExit(f"GCB budget identity fails by {resid:.3f} GtC")
    ocean10 = float(t.loc[last - 9:last, "ocean"].mean())
    want, tol = PRINTED["gcb_ocean_2015_2024"]
    if last != 2024 or abs(ocean10 - want) > tol:
        raise SystemExit(f"GCB ocean sink {last - 9}-{last} = {ocean10:.2f}, printed {want}")
    return {"last": last, "fossil": round(float(t.loc[last, "fossil"]), 2),
            "ocean10": round(ocean10, 2), "ocean_last": round(float(t.loc[last, "ocean"]), 2),
            "atm_last": round(float(t.loc[last, "atm"]), 2),
            "from": last - 9, "fetched": row["fetched"], "printed": want}


def siegel():
    rows = list(csv.DictReader(open(SIEGEL, encoding="utf-8")))
    for r in rows:
        for k in ("depth_m", "mean_fraction", "p10", "p50", "p90"):
            r[k] = float(r[k])
        r["t_years"] = int(r["t_years"])

    def pick(depth, t, w):
        c = [r for r in rows if r["t_years"] == t and r["weighting"] == w]
        return min(c, key=lambda r: abs(r["depth_m"] - depth))
    m, tol = PRINTED["siegel_208m_50y_mean"]
    r = pick(208, 50, "none")
    if abs(r["mean_fraction"] - m) > tol:
        raise SystemExit(f"Siegel 208 m 50 yr plain mean {r['mean_fraction']:.3f}, printed {m}")
    if pick(2100, 50, "area")["p50"] <= PRINTED["siegel_2100m_50y_median_min"]:
        raise SystemExit("Siegel 2,100 m 50 yr: area median not above 0.95")
    curve = [{"depth": round(r["depth_m"]), "mean": round(r["mean_fraction"], 3),
              "p10": round(r["p10"], 3), "p90": round(r["p90"], 3)}
             for r in rows if r["t_years"] == 100 and r["weighting"] == "area" and r["depth_m"] < 4000]
    curve.sort(key=lambda r: r["depth"])
    at = {d: round(pick(d, 100, "area")["mean_fraction"], 3) for d in (208, 530, 1022, 2100, 3083)}
    return {"curve": curve, "at100": at, "check_208_50": round(r["mean_fraction"], 3), "printed_208_50": m}


def funnels(S):
    out = []
    for f in PR.FUNNEL:
        f = dict(f)
        if f["key"] == "seaweed":
            rd = [S["at100"][1022], S["at100"][2100], f["ret_high"]]
            f["retained"] = rd
            f["held"] = tuple(round(100 * a * b * c, 1) for a, b, c in zip(f["from_air"], f["reach"], rd))
            f["shelf"] = round(100 * f["from_air"][1] * f["reach"][1] * S["at100"][208], 1)
        if f["key"] == "iron":
            f["held"] = tuple(round(e * r * (1 - x), 1) for e, r, x in zip(f["export"], f["ratio"], f["n2o"]))
        if f["key"] == "pondburied":
            f["held"] = tuple(round(100 * h * a * t - e, 1)
                              for h, a, t, e in zip(f["harvest"], f["from_air"], f["tomb"], f["energy"]))
        lo, c, hi = f["held"]
        if not lo <= c <= hi:
            raise SystemExit(f"{f['key']}: held100 not ordered {f['held']}")
        out.append(f)
    return out


def main():
    G = gcb()
    S = siegel()
    F = funnels(S)
    P = {"gcb": G, "siegel": S, "funnel": F, "costs": PR.COSTS, "record": PR.RECORD,
         "npp": {"ocean": PR.NPP_OCEAN, "macro": PR.NPP_MACRO, "land": PR.NPP_LAND, "sat": PR.NPP_SAT, "span": PR.NPP_SPAN,
                 "export": PR.EXPORT_100M, "flux1000": PR.FLUX_1000M, "burial": PR.BURIAL}}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1)
        f.write("\n")
    for x in F:
        print(f"  {x['label']:30s} held at 100 yr {x['held']}")
    print(f"  GCB {G['last']}: fossil {G['fossil']} GtC, ocean sink {G['from']}-{G['last']} {G['ocean10']} GtC/yr")
    print(f"  Siegel 100 yr retention {S['at100']}")


if __name__ == "__main__":
    main()
