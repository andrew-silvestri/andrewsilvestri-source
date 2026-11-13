"""
Build outputs/payload.json for site/origins.html.

Inputs, all public:
  outputs/ashrae_*.csv          written by analyse_ashrae.py from the ASHRAE Global Thermal Comfort
                                Database II v2.1.0 (Zenodo 4993952, CC BY 4.0), data/raw (gitignored)
  data/lost_city_marhys3.csv    the Lost City rows of the MARHYS Database 3.0 (PANGAEA 958978, CC BY 4.0),
                                cut from data/raw/MARHYS_DB_3_0.xlsx by marhys_lostcity.py
  data/timeline.csv             dated events, each row with its source and URL
  LADDER below                  membrane voltages, each with the paper or BioNumbers entry it comes from

Every number the page prints is computed here or read from these files; checks() stops the build if a
value moves outside what the page's words say about it.

Run:  python build_origins.py
"""
import csv
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
DATA = os.path.join(HERE, "data")

# CODATA 2018 exact values
R = 8.314462618        # J/(mol K)
F = 96485.33212        # C/mol


def nernst_mv_per_ph(t_c):
    """RT ln(10) / F, in mV per pH unit."""
    return 1000 * R * (t_c + 273.15) * math.log(10) / F


# Membrane voltages, magnitude in mV (lo, hi). Sign: inside negative for every row except the spike peak.
# Sources are the page's reference list; research/w2-02-voltage-ladder.md in the lane folder has the notes.
LADDER = [
    {"key": "mito", "label": "Mitochondrion, proton-motive force", "short": "mitochondrion",
     "lo": 160, "hi": 184, "mid": 172,
     "src": "BioNumbers 101103 (Mollica et al. 1998), perfused rat liver, 172 +/- 12 mV"},
    {"key": "plant", "label": "Plant leaf cell, outer membrane", "short": "leaf cell",
     "lo": 160, "hi": 180, "mid": 170, "src": "Reyer et al. 2020, PNAS, Arabidopsis mesophyll"},
    {"key": "ecoli", "label": "E. coli, membrane voltage only", "short": "E. coli",
     "lo": 126, "hi": 154, "mid": 140, "src": "Lo et al. 2007, Biophys J, -140 +/- 14 mV at pH 7"},
    {"key": "squid_ap", "label": "Squid nerve impulse, full swing", "short": "nerve spike",
     "lo": 80, "hi": 95, "mid": 90, "src": "Hodgkin & Huxley 1939, Nature, 80-95 mV at 20 C"},
    {"key": "squid_rest", "label": "Squid nerve at rest, 1939", "short": "nerve rest",
     "lo": 45, "hi": 50, "mid": 50, "src": "Hodgkin & Huxley 1939; Hodgkin & Katz 1949"},
]


def ashrae():
    def rows(name):
        with open(os.path.join(OUT, name), encoding="utf-8") as f:
            return list(csv.DictReader(f))
    counts = {r[""]: int(r["value"]) for r in rows("ashrae_counts.csv")}
    bins = [r for r in rows("ashrae_bins_all.csv") if r["included"] == "True"]
    cross = {(r["group"], r["metric"]): r for r in rows("ashrae_crossovers.csv")}
    slopes = {(r["subset"], r["metric"]): r for r in rows("ashrae_adaptive_slopes.csv")}
    b = [{"t": float(r["ta_bin_lo"]), "n": int(r["n"]), "nc": float(r["share_no_change"]),
          "w": float(r["share_warmer"]), "c": float(r["share_cooler"])} for r in bins]
    pk = max(b, key=lambda r: r["nc"])
    wc = cross[("all", "T_wc")]
    s_pref, s_neut = slopes[("all", "T_wc")], slopes[("all", "T_ts0")]
    s_nv = slopes[("NV", "T_wc")]
    f = lambda r, k: round(float(r[k]), 3)
    return {
        "votes": counts["rows_ta_and_preference"], "buildings": counts["buildings"],
        "rows_raw": counts["rows_raw"], "bins": b, "bin_lo": b[0]["t"], "bin_hi": b[-1]["t"] + 1,
        "min_n": min(r["n"] for r in b),
        "peak": {"t": pk["t"], "nc": pk["nc"]},
        "cross": {"t": f(wc, "estimate"), "lo": f(wc, "ci_lo"), "hi": f(wc, "ci_hi")},
        "slope_pref": {"v": f(s_pref, "slope"), "lo": f(s_pref, "slope_ci_lo"), "hi": f(s_pref, "slope_ci_hi"),
                       "range": s_pref["tmot_range"]},
        "slope_pref_nv": {"v": f(s_nv, "slope"), "lo": f(s_nv, "slope_ci_lo"), "hi": f(s_nv, "slope_ci_hi")},
        "slope_neut": {"v": f(s_neut, "slope"), "lo": f(s_neut, "slope_ci_lo"), "hi": f(s_neut, "slope_ci_hi"),
                       "range": s_neut["tmot_range"]},
        "ref_slope": f(s_pref, "ref_slope"),
        "at_18": [r for r in b if r["t"] == 18][0], "at_30": [r for r in b if r["t"] == 30][0],
    }


def vents():
    with open(os.path.join(DATA, "lost_city_marhys3.csv"), encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["Sample type [(HF,EM,SW,STD)]"] in ("HF", "EM")]

    def num(r, k):
        try:
            return float(r[k])
        except (TypeError, ValueError):
            return None
    ph = [num(r, "pH [[]]") for r in rows if num(r, "pH [[]]") is not None]
    t = [num(r, "T [°C]") for r in rows if num(r, "T [°C]") is not None]
    pure = [num(r, "pH [[]]") for r in rows
            if num(r, "pH [[]]") is not None and num(r, "Mg [mmol/kg]") is not None and num(r, "Mg [mmol/kg]") < 5]
    papers = sorted({r["Author (primary)"] + " " + r["Year of publication (primary)"]
                     for r in rows if num(r, "pH [[]]") is not None})
    return {"n_rows": len(rows), "n_ph": len(ph), "ph_med": round(st.median(ph), 2), "ph_min": min(ph),
            "ph_max": max(ph), "n_t": len(t), "t_med": round(st.median(t), 1), "t_min": min(t), "t_max": max(t),
            "pure_n": len(pure), "pure_min": min(pure), "pure_max": max(pure), "ph_papers": len(papers)}


def gradient(v):
    ocean, ocean_lo, ocean_hi = 6.6, 6.3, 7.2      # Krissansen-Totton et al. 2018, 4.0 Ga, median and 95% range
    s25, s37, s70 = (nernst_mv_per_ph(x) for x in (25, 37, 70))
    dph = v["ph_med"] - ocean
    return {"ocean": ocean, "ocean_lo": ocean_lo, "ocean_hi": ocean_hi,
            "s25": round(s25, 2), "s37": round(s37, 2), "s70": round(s70, 2), "dph": round(dph, 2),
            "mv25": round(s25 * dph), "mv70": round(s70 * dph),
            "lo": round(s25 * (v["ph_med"] - ocean_hi)), "hi": round(s70 * (v["ph_med"] - ocean_lo)),
            "kj": round(F * s25 * dph / 1000 / 1000, 1)}


def timeline():
    with open(os.path.join(DATA, "timeline.csv"), encoding="utf-8") as f:
        T = {r["event"]: r for r in csv.DictReader(f)}

    def g(prefix):
        r = [v for k, v in T.items() if k.startswith(prefix)]
        assert len(r) == 1, prefix
        return {"ma": float(r[0]["ma"]), "lo": float(r[0]["ma_lo"]), "hi": float(r[0]["ma_hi"])}
    ev = {"earth": g("Oldest solids"), "water": g("Oldest zircon"), "luca": g("LUCA"),
          "life": g("Oldest widely accepted"), "goe": g("Great Oxidation"), "euk": g("Oldest confident eukaryote"),
          "animals": g("Oldest accepted animals"), "brain": g("Oldest fossil brain"), "sapiens": g("Homo sapiens")}
    ev["gap"] = ev["life"]["ma"] - ev["brain"]["ma"]
    ev["gap_luca"] = ev["luca"]["ma"] - ev["brain"]["ma"]
    return ev


def field():
    # 150-200 mV across about 5 nm (Lane & Martin 2010 via BioNumbers 105801); air breaks down near 3 MV/m
    lo, hi = 0.150 / 5e-9, 0.200 / 5e-9
    return {"lo_mvm": round(lo / 1e6), "hi_mvm": round(hi / 1e6), "air": 3, "x_lo": round(lo / 3e6),
            "x_hi": round(hi / 3e6)}


def checks(P):
    a, g, v, t = P["ashrae"], P["gradient"], P["vents"], P["timeline"]
    c = [
        ("'about six in ten' at the peak: 0.55-0.65", 0.55 <= a["peak"]["nc"] <= 0.65),
        ("peak bin between 21 and 25 C", 21 <= a["peak"]["t"] <= 25),
        ("crossover 'about 23 C': 22.5-23.2", 22.5 <= a["cross"]["t"] <= 23.2),
        ("'half wanted warmer' at 18 C bin: 0.45-0.55", 0.45 <= a["at_18"]["w"] <= 0.55),
        ("'more than half wanted cooler' at 30 C bin", 0.5 < a["at_30"]["c"] < 0.7),
        ("neutral slope CI covers ASHRAE 55's 0.31", a["slope_neut"]["lo"] <= a["ref_slope"] <= a["slope_neut"]["hi"]),
        ("preference slope 'a sixth or less' of neutral slope", a["slope_pref"]["v"] <= a["slope_neut"]["v"] / 6),
        ("preference slope CI excludes the neutral slope", a["slope_pref"]["hi"] < a["slope_neut"]["lo"]),
        ("vent median pH 'about 10': 9.7-10.4", 9.7 <= v["ph_med"] <= 10.4),
        ("'roughly 200 mV' vent equivalent at 25 C: 180-240", 180 <= g["mv25"] <= 240),
        ("vent equivalent 'same order as a mitochondrion': within 0.7-1.5x of 172",
         0.7 <= g["mv25"] / 172 <= 1.5),
        ("'about 3 billion years' between accepted life and the oldest brain: 2,800-3,100 Myr",
         2800 <= t["gap"] <= 3100),
        ("'ten times or more' air breakdown", P["field"]["x_lo"] >= 10),
    ]
    bad = [n for n, ok in c if not ok]
    if bad:
        raise SystemExit("payload contradicts the page's words:\n  " + "\n  ".join(bad))
    return len(c)


def main():
    v = vents()
    P = {"ashrae": ashrae(), "vents": v, "gradient": gradient(v), "ladder": LADDER, "timeline": timeline(),
         "field": field()}
    n = checks(P)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "payload.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1, sort_keys=True)
        f.write("\n")
    print("payload.json written; %d checks passed" % n)
    print(json.dumps({k: P[k] for k in ("vents", "gradient", "field")}, indent=None))
    a = P["ashrae"]
    print("ashrae", a["votes"], a["buildings"], a["peak"], a["cross"], a["slope_pref"], a["slope_neut"],
          a["at_18"], a["at_30"])
    print("gap", P["timeline"]["gap"], P["timeline"]["gap_luca"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
