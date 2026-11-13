"""
Build outputs/payload.json for site/dissonance.html from the three tables in data/.

1. Eurobarometer. The EU27 share of respondents who say each of the 14 actions in the 2025 list (Special
   Eurobarometer 565, question QD6) applies to them. The chart uses the unrounded share (weighted count
   over weighted total, calculated by prepare step from Volume A); the page prints the published whole
   percent.
2. Tonnes. For each action, the median, 25th and 75th percentile of the per-person annual savings in
   Ivanova et al. (2020), supplementary sheet "options", over the rows of the option (or options) in
   MAP. Every row is one estimate, whatever its "Average/median/..." label: this reproduces the medians
   the paper prints (check_paper below; the build stops on a mismatch). One action, recycling, takes its
   value from Wynes and Nicholas (2017), table 1 (210 kg a year), because Ivanova's "Recycle" option
   holds three narrow cases and that same row (see MAP).
3. Meta and Yale 2023. Unweighted means over the 37 high-income countries asked: the share who have done
   each of six actions, and the barriers named by those who have not.

Run:  python build_dissonance.py
"""
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "outputs", "payload.json")

VAL = "Absolute carbon mitigation potential (tCO2eq/cap per year)"
OPT = "Aggregated consumption options"
DOM = "Consumption domain"

RECYCLE_WN_T = 0.210   # Wynes and Nicholas (2017), table 1: "Recycle 210" kg CO2e a year

# Values printed in the text of Ivanova et al. (2020). The paper prints one decimal and rounds 2.07 and
# 1.95 both to 2.0, so the build accepts a computed value within 0.075 of the printed one.
PAPER = [("Transport", "Live car-free", "median", 2.0),
         ("Transport", "One less flight (long return)", "median", 1.7),
         ("Transport", "Shift to BEV", "median", 2.0),
         ("Food", "Vegan diet", "median", 0.8),
         ("Housing", "Renewable electricity", "median", 1.6),
         ("Housing", "Produce renewable electricity", "median", 0.6),
         ("Housing", "Refurbishment and renovation", "mean", 0.9),
         ("Housing", "Smart metering", "mean", 0.2)]


def eu_rows(g):
    return g["Geographical context"].astype(str).str.strip() == "EU/Europe"


# code: (chart label, [(domain, option, row filter)], match, why)
MAP = {
    "QD6_13": ("Reduce waste and recycle", None, "loose",
               "Wynes and Nicholas (2017), recycling for a year"),
    "QD6_14": ("Cut down on disposable items", [("Food", "Less packaging", None)], "loose",
               "less packaging"),
    "QD6_6": ("Weigh energy use of appliances", [("Housing", "More efficient appliances", None)], "close",
              "more efficient appliances"),
    "QD6_3": ("Use alternatives to the car", [("Transport", "Shift to public transport", None),
                                              ("Transport", "Shift to active transport", None),
                                              ("Transport", "Car-pooling/sharing", None)], "loose",
              "shift to public transport, walking and cycling, or car sharing"),
    "QD6_12": ("Eat less meat", [("Food", "Less animal products", None)], "loose",
               "fewer animal products"),
    "QD6_4": ("Insulated the home", [("Housing", "Better thermal insulation", None)], "close",
              "better thermal insulation"),
    "QD6_11": ("Adapt long-distance travel", [("Transport", "Less transport by air", None)], "loose",
               "less air travel"),
    "QD6_7": ("Switched to a greener supplier", [("Housing", "Renewable electricity", eu_rows)], "loose",
              "renewable electricity, European estimates only"),
    "QD6_9": ("Installed energy controls", [("Housing", "Smart metering", None)], "close",
              "smart metering"),
    "QD6_10": ("Installed solar panels", [("Housing", "Produce renewable electricity", None)], "close",
               "produce renewable electricity"),
    "QD6_1": ("New car chosen for low fuel use", [("Transport", "Shift to a smaller car", None)], "loose",
              "shift to a smaller car"),
    "QD6_8": ("Installed a heat pump", [("Housing", "Heat pump", None)], "close", "heat pump"),
    "QD6_2": ("Bought an electric car", [("Transport", "Shift to BEV", None)], "close",
              "shift to a battery electric car"),
    "QD6_5": ("Bought a low-energy home", [("Housing", "Passive house", None)], "close", "passive house"),
}


def stats(x):
    x = np.asarray(x, dtype=float)
    return {"median": float(np.median(x)), "p25": float(np.percentile(x, 25)),
            "p75": float(np.percentile(x, 75)), "mean": float(x.mean()), "n": int(len(x))}


def load_iva():
    si = pd.read_csv(os.path.join(DATA, "ivanova2020_options.csv"))
    si = si[si[VAL].notna()].copy()
    for c in (OPT, DOM):
        si[c] = si[c].astype(str).str.strip()
    return si


def select(si, dom, opt, filt):
    g = si[(si[DOM] == dom) & (si[OPT] == opt)]
    if not len(g):
        raise SystemExit(f"no Ivanova rows for {dom} / {opt}")
    return g[filt(g)] if filt is not None else g


def check_paper(si):
    bad = []
    for dom, opt, stat, want in PAPER:
        got = stats(select(si, dom, opt, None)[VAL])[stat]
        if abs(got - want) > 0.075:
            bad.append(f"{opt} {stat}: paper {want}, computed {got:.3f}")
    if bad:
        raise SystemExit("Ivanova medians do not reproduce the paper:\n  " + "\n  ".join(bad))
    return len(PAPER)


def eurobarometer():
    eb = pd.read_csv(os.path.join(DATA, "eb_climate_2025.csv"), dtype=str)
    e = eb[eb.wave == "SP565_2025"].set_index("item_code")
    e23 = eb[eb.wave == "SP538_2023"].set_index("item_code")

    def num(code, col="eu27_pct"):
        return float(e.loc[code, col])
    head = {"very_serious": num("QD2_1"), "fairly_serious": num("QD2_2"), "serious": num("QD2_6"),
            "acted_6m": num("QD5_1"), "at_least_one": num("QD6_18"), "none": num("QD6_16"),
            "recycle_2023": float(e23.loc["QC6_14", "eu27_pct"]),
            "acted_6m_2023": float(e23.loc["QC5_1", "eu27_pct"])}
    q3 = pd.read_csv(os.path.join(DATA, "eb565_qd3ab.csv")).set_index("answer")
    head["n"] = int(q3.weighted_total.iloc[0])
    head["best_gov"] = round(100 * float(q3.loc["National governments", "published_share"]))
    head["best_you"] = round(100 * float(q3.loc["You personally", "published_share"]))
    if abs(head["very_serious"] + head["fairly_serious"] - head["serious"]) > 1:
        raise SystemExit("QD2 parts do not add to the published total")
    return e, head


def build():
    si = load_iva()
    n_checked = check_paper(si)
    e, head = eurobarometer()
    items = []
    for code, (label, sel, match, option) in MAP.items():
        if sel is None:
            s = {"median": RECYCLE_WN_T, "p25": None, "p75": None, "mean": RECYCLE_WN_T, "n": 1}
            n_src = 1
        else:
            g = pd.concat([select(si, d, o, f) for d, o, f in sel])
            s = stats(g[VAL])
            n_src = int(g["Authors"].astype(str).str.strip().nunique())
        items.append({"code": code, "label": label, "text": e.loc[code, "item_text_exact"],
                      "pct": int(e.loc[code, "eu27_pct"]), "pct_calc": float(e.loc[code, "eu27_pct_unrounded_calc"]),
                      "t": round(s["median"], 4), "p25": None if s["p25"] is None else round(s["p25"], 4),
                      "p75": None if s["p75"] is None else round(s["p75"], 4), "n": s["n"], "n_sources": n_src,
                      "match": match, "option": option})
    if len(items) != 14:
        raise SystemExit("expected the 14 actions of the 2025 list")

    by_share = sorted(items, key=lambda r: -r["pct_calc"])
    top, bot = by_share[:3], by_share[-3:]
    top_t = sum(r["t"] for r in top) / 3
    bot_t = sum(r["t"] for r in bot) / 3
    # adverse bounds: the three most reported at their 75th percentile (recycling has one value), the
    # three least reported at their 25th
    top_hi = sum((r["p75"] if r["p75"] is not None else r["t"]) for r in top) / 3
    bot_lo = sum(r["p25"] for r in bot) / 3
    pct = np.array([r["pct_calc"] for r in items])
    t = np.array([r["t"] for r in items])
    rho = float(np.corrcoef(pd.Series(pct).rank(), pd.Series(t).rank())[0, 1])
    by_t = sorted(items, key=lambda r: -r["t"])
    over_half = [r for r in items if r["t"] >= 0.5]

    head.update({
        "top3": [r["code"] for r in top], "bot3": [r["code"] for r in bot],
        "top3_t": top_t, "bot3_t": bot_t, "ratio": bot_t / top_t,
        "top3_t_hi": top_hi, "bot3_t_lo": bot_lo, "ratio_adverse": bot_lo / top_hi,
        "spearman": rho, "weighted_t": float((pct * t).sum() / pct.sum()), "unweighted_t": float(t.mean()),
        "top_by_t": [r["code"] for r in by_t[:3]],
        "over_half": [r["code"] for r in over_half],
        "over_half_max_pct": max(r["pct"] for r in over_half),
        "under_quarter_pct": [r["code"] for r in items if r["t"] < 0.25],
        "ivanova_rows": int(len(si)), "paper_checks": n_checked,
    })
    return {"items": items, "eb": head, "metayale": metayale(), "eu": owid_eu()}


def owid_eu():
    """The newest consumption-based CO2 per person for the EU27 (Global Carbon Budget via OWID): CO2
    only, not the other greenhouse gases, so it is a scale for the savings, not their denominator."""
    ow = pd.read_csv(os.path.join(DATA, "owid_eu27.csv"))
    c = ow[ow.consumption_co2_per_capita.notna()].sort_values("year").iloc[-1]
    return {"year": int(c.year), "consumption_t": float(c.consumption_co2_per_capita),
            "territorial_t": float(c.co2_per_capita)}


BARRIER_ITEMS = {"ev": "an electric car", "heatpump": "a heat pump", "solar": "rooftop solar",
                 "meat": "eating less meat"}


def metayale():
    my = pd.read_csv(os.path.join(DATA, "metayale2023_behaviour.csv"))
    n_c = my.country_code.nunique()
    out = {"countries": int(n_c), "adoption": {}, "barriers": {}}
    for v in ["food", "meat", "solar", "heatpump", "ev", "offsets"]:
        a = my[my.variable == f"adoption_{v}"]
        tab = a.pivot_table(index="country_code", columns="response", values="pct")
        if len(tab) != n_c:
            raise SystemExit(f"adoption_{v}: {len(tab)} countries, expected {n_c}")
        out["adoption"][v] = {"done": float(tab["I have done this"].mean()),
                              "want": float(tab["I have not done this but I want to"].mean()),
                              "na": float(tab["Not applicable"].mean())}
    for v in BARRIER_ITEMS:
        b = my[my.variable == f"barriers_{v}_haventadopted"]
        means = (b.groupby("response").pct.sum() / n_c).sort_values(ascending=False)
        out["barriers"][v] = [{"reason": k, "pct": float(x)} for k, x in means.head(3).items()]
    return out


def main():
    P = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(P, open(OUT, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
    h = P["eb"]
    print(f"payload: {len(P['items'])} actions, Ivanova paper checks {h['paper_checks']} OK")
    print(f"top3 {h['top3']} mean {h['top3_t']:.3f} t; bottom3 {h['bot3']} mean {h['bot3_t']:.3f} t; "
          f"ratio {h['ratio']:.2f}; adverse {h['ratio_adverse']:.2f}; spearman {h['spearman']:.2f}")
    print(f"share-weighted {h['weighted_t']:.3f} t, unweighted {h['unweighted_t']:.3f} t")


if __name__ == "__main__":
    main()
