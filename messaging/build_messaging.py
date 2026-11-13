"""Build messaging/outputs/payload.json from the tournament deposit and the transcribed tables.

1. Field effects (data/effects.csv): for each study, the share making the low-carbon choice without and with
   the change, in percent, as the paper prints it. The effect is the difference, in percentage points. The
   build stops if that difference is more than 0.5 points from the effect the paper itself prints (a model
   estimate can differ a little from the raw difference of the two shares; a typing error cannot hide).
2. Replication pairs (data/shrink.csv): a first or larger estimate and a later or smaller one, each in its
   own unit. The chart shows the later as a share of the first.
3. The 63-country tournament (Vlasceanu et al. 2024): each intervention against the control group, by OLS
   with country fixed effects, standard errors clustered by country (63 clusters, CR1). The build stops if
   any intervention's effect on the tree-planting task is more than 0.06 pages from the paper's own
   estimate (supplement Table S4, typed below with the table it comes from).
4. The kit (data/kit.csv): effect text with {placeholders} filled from the field effects, so a kit row
   cannot disagree with the chart.

Run:  python build_messaging.py
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sources as S  # noqa: E402

OUT = os.path.join(HERE, "outputs", "payload.json")

# Intervention names as the paper's Methods headings give them, in the deposit's codes.
ARMS = {
    "WorkTogetherNorm": "Working-together norms",
    "SystemJust": "System justification",
    "BindingMoral": "Binding moral foundations",
    "CollectAction": "Exposure to effective collective action",
    "FutureSelfCont": "Future self-continuity",
    "SciConsens": "Scientific consensus",
    "PsychDistance": "Decreasing psychological distance",
    "DynamicNorm": "Dynamic social norms",
    "PluralIgnorance": "Correcting pluralistic ignorance",
    "LetterFutureGen": "Letter to future generations",
    "NegativeEmotions": "Negative emotion",
}
# Vlasceanu et al. 2024, supplementary Table S4: posterior mean effect on WEPT pages, each arm against control.
PAPER_S4 = {"BindingMoral": 0.038, "SciConsens": 0.003, "DynamicNorm": -0.009, "SystemJust": -0.12,
            "PluralIgnorance": -0.165, "CollectAction": -0.185, "FutureSelfCont": -0.229,
            "LetterFutureGen": -0.365, "WorkTogetherNorm": -0.438, "PsychDistance": -0.51,
            "NegativeEmotions": -0.536}
S4_TOL = 0.06
EFFECT_TOL = 0.5


def num(s):
    return float(s) if s not in ("", None) else None


def field_effects():
    rows = []
    for r in S.table("effects.csv"):
        b, t, pe = num(r["baseline"]), num(r["treated"]), num(r["printed_effect"])
        d = t - b
        if abs(d - pe) > EFFECT_TOL:
            raise SystemExit(f"effects.csv {r['id']}: {t} - {b} = {d:.2f} points, the paper prints {pe}")
        rows.append({"id": r["id"], "o": int(r["o"]), "group": r["group"], "label": r["label"], "short": r["short"],
                     "setting": r["setting"], "outcome": r["outcome"], "n": int(r["n"]), "n_unit": r["n_unit"],
                     "design": r["design"], "measure": r["measure"], "baseline": b, "treated": t,
                     "effect": pe, "cite": r["cite"], "where": r["where"]})
    return rows


def shrink():
    out = []
    for r in S.table("shrink.csv"):
        f, l = float(r["first"]), float(r["later"])
        out.append({**{k: r[k] for k in ("id", "label", "first_label", "later_label", "unit", "cite", "where")},
                    "first": f, "later": l, "kept": l / f})
    return out


def ols_fe(rows, y):
    """Each arm minus control, with country fixed effects; SEs clustered by country (CR1)."""
    rows = [r for r in rows if r[y] not in ("", "nan") and not math.isnan(float(r[y]))]
    arms = list(ARMS)
    countries = sorted({r["country"] for r in rows})
    ci = {c: i for i, c in enumerate(countries)}
    n, k = len(rows), 1 + len(arms) + len(countries) - 1
    X = np.zeros((n, k))
    X[:, 0] = 1
    yv = np.empty(n)
    g = np.empty(n, dtype=int)
    for i, r in enumerate(rows):
        if r["cond"] in ARMS:
            X[i, 1 + arms.index(r["cond"])] = 1
        c = ci[r["country"]]
        if c:
            X[i, len(arms) + c] = 1
        yv[i] = float(r[y])
        g[i] = c
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ yv
    e = yv - X @ beta
    meat = np.zeros((k, k))
    for c in range(len(countries)):
        m = g == c
        s = X[m].T @ e[m]
        meat += np.outer(s, s)
    G = len(countries)
    V = XtX_inv @ meat @ XtX_inv * (G / (G - 1)) * ((n - 1) / (n - k))
    ctrl = [float(r[y]) for r in rows if r["cond"] == "Control"]
    res = {"n": n, "countries": G, "control_mean": sum(ctrl) / len(ctrl), "arms": {}}
    for j, a in enumerate(arms):
        b, se = beta[1 + j], math.sqrt(V[1 + j, 1 + j])
        res["arms"][a] = {"name": ARMS[a], "est": round(b, 4), "lo": round(b - 1.96 * se, 4),
                          "hi": round(b + 1.96 * se, 4)}
    return res


def tournament():
    rows = S.tournament()
    out = {"n": len(rows), "countries": len({r["country"] for r in rows})}
    for y in ("belief", "policy", "share", "wept"):
        out[y] = ols_fe(rows, y)
    for a in out["share"]["arms"].values():          # sharing: a 0/1 outcome, reported in percentage points
        for k in ("est", "lo", "hi"):
            a[k] = round(100 * a[k], 2)
    out["share"]["control_mean"] *= 100
    ctrl = [float(r["wept"]) for r in rows if r["cond"] == "Control"]
    out["wept_ctrl_any"] = sum(1 for v in ctrl if v >= 1) / len(ctrl)
    out["wept_ctrl_all8"] = sum(1 for v in ctrl if v == 8) / len(ctrl)
    off = {a: round(out["wept"]["arms"][a]["est"] - PAPER_S4[a], 3) for a in ARMS
           if abs(out["wept"]["arms"][a]["est"] - PAPER_S4[a]) > S4_TOL}
    if off:
        raise SystemExit(f"tree-task effects more than {S4_TOL} pages from the paper's Table S4: {off}")
    out["paper_s4"] = PAPER_S4
    return out


def kit(fx):
    by = {r["id"]: r for r in fx}
    food = [r["effect"] for r in fx if r["group"] == "food_default"]
    menu = [r["effect"] for r in fx if r["group"] == "menus"]
    fill = {"ebeling": f"{by['ebeling']['effect']:.0f}", "food_lo": f"{min(food):.0f}", "food_hi": f"{max(food):.0f}",
            "menu_lo": f"{min(menu):.0f}", "menu_hi": f"{max(menu):.0f}"}
    out = []
    for r in S.table("kit.csv"):
        if r["grade"] not in ("A", "B", "C"):
            raise SystemExit(f"kit.csv {r['id']}: grade {r['grade']!r} is not A, B or C")
        out.append({**r, "effect": r["effect"].format(**fill)})
    return out


def main():
    fx = field_effects()
    P = {"effects": fx, "shrink": shrink(), "tournament": tournament(), "kit": kit(fx),
         "literature_through": "2026-11"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1, ensure_ascii=False)
        f.write("\n")
    t = P["tournament"]
    print(f"payload: {len(fx)} field effects, {len(P['shrink'])} replication pairs, {len(P['kit'])} kit rows; "
          f"tournament n={t['n']} in {t['countries']} countries")
    for a, v in sorted(t["wept"]["arms"].items(), key=lambda kv: kv[1]["est"]):
        print(f"  WEPT {v['name']:42s} {v['est']:+.3f} [{v['lo']:+.3f}, {v['hi']:+.3f}]  paper {PAPER_S4[a]:+.3f}")


if __name__ == "__main__":
    main()
