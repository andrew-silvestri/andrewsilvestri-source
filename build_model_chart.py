"""
The front-page overview of the model.

Read out of site/assets/atlas-data.js, in the site's own palette, so the chart
on the home page states the same figures as every other page.

Run:  python3 build_model_chart.py
"""

import collections
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from build_throughlines import (BG, DIM, INK, KCOL, LABEL, RULE, SHORT,
                                audit, engine)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "assets", "atlas-data.js")
OUT = os.path.join(HERE, "site", "assets", "energy_model_chart.png")

ORDER = ["sun", "insolation", "weather", "climate", "event", "market",
         "supply", "grid", "station", "district", "consumer", "psych"]


def main():
    raw = open(DATA, encoding="utf-8").read()
    D = json.loads(raw[raw.index("=") + 1:raw.rindex(";")])
    kind = [D["kinds"][k] for k in D["kind"]]
    counts = collections.Counter(kind)
    ids = {k: int(v) for k, v in D["idMap"].items()}
    run, _ = engine(D)

    fig = plt.figure(figsize=(14.4, 8.6), facecolor=BG)
    gs = fig.add_gridspec(2, 2, hspace=0.72, wspace=0.28,
                          left=0.115, right=0.955, top=0.845, bottom=0.085)

    fig.text(0.055, 0.955, "The world energy model", color=INK, fontsize=20,
             fontweight="600", va="top")
    fig.text(0.055, 0.905,
             f"{D['n']:,} nodes and {len(D['es']):,} weighted links. "
             f"Every parameter comes from a public data set.",
             color=DIM, fontsize=11.5, va="top")

    # ---- what the model contains ---------------------------------------
    ax = fig.add_subplot(gs[0, 0])
    ks = [k for k in ORDER if counts[k]]
    vals = [counts[k] for k in ks]
    ax.barh(range(len(ks)), vals, color=[KCOL[k] for k in ks], height=0.66,
            alpha=0.92)
    ax.set_yticks(range(len(ks)))
    ax.set_yticklabels([LABEL[k] for k in ks], fontsize=8.8)
    ax.set_xscale("log")
    ax.set_xlim(0.7, max(vals) * 9)
    for i, v in enumerate(vals):
        ax.text(v * 1.25, i, f"{v:,}", va="center", color=DIM, fontsize=8.4)
    ax.set_xlabel("nodes (log scale)", color=DIM, fontsize=9.5)
    ax.set_title("What the model contains", color=INK, fontsize=12.5,
                 loc="left", pad=8)
    ax.invert_yaxis()

    # ---- where the numbers come from ------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    src = collections.Counter()
    for i in range(D["n"]):
        s = D["srcDict"][D["src"][i]]
        src[s.split("·")[0].strip().split(",")[0][:26]] += 1
    top = src.most_common(6)
    other = sum(src.values()) - sum(v for _, v in top)
    labs = [f"{k} — {v:,}" for k, v in top]
    vals2 = [v for _, v in top]
    if other:
        labs.append(f"everything else — {other:,}")
        vals2.append(other)
    cols = ["#8b7ff2", "#5aa8d8", "#4f9d84", "#d86a86", "#6f7fd8",
            "#cfd6f0", "#a98fd8", "#5c6a8c"][:len(vals2)]
    w, _ = ax2.pie(vals2, colors=cols, startangle=90,
                   wedgeprops=dict(width=0.42, edgecolor=BG, linewidth=1.4))
    # under the donut, not beside it: beside it the longest source name ran
    # off the right edge of the sheet
    ax2.legend(w, labs, loc="upper center", bbox_to_anchor=(0.5, -0.02),
               frameon=False, fontsize=8.0, labelcolor=DIM, ncol=2)
    ax2.set_title("Where the numbers come from", color=INK, fontsize=12.5,
                  loc="left", pad=8)

    # ---- link weights ----------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    ew = np.asarray(D["ew"], dtype=float)
    ax3.hist(ew[ew > 0], bins=46, color="#4f9d84", alpha=0.9, label="positive")
    if (ew < 0).any():
        ax3.hist(ew[ew < 0], bins=24, color="#d86a86", alpha=0.9,
                 label="negative")
    ax3.set_yscale("log")
    # matplotlib offers decades well outside the data on a log count axis,
    # and those labels land outside the panel. Bound the axis to the data.
    hi = max(np.histogram(ew[ew > 0], bins=46)[0].max(), 1)
    ax3.set_ylim(0.8, hi * 3)
    ax3.set_xlabel("link weight", color=DIM, fontsize=9.5)
    ax3.set_ylabel("links", color=DIM, fontsize=9.5)
    ax3.set_title("Link weights", color=INK, fontsize=12.5, loc="left", pad=8)
    ax3.legend(frameon=False, fontsize=8.6, labelcolor=DIM)

    # ---- how far the prepared changes travel, by category ------------------
    # One bar per scenario was sixty bars in a panel that holds about ten.
    # The categories are the structure the catalogue actually has, so the
    # panel shows the span within each: the narrowest and widest reach, and
    # every scenario as a point between them.
    ax4 = fig.add_subplot(gs[1, 1])
    cats = D.get("scenarioCats", [])
    rows = []
    for c in cats:
        ks = [k for k, v in D["scenarios"].items() if v.get("cat") == c["id"]]
        if not ks:
            continue
        reach = []
        for k in ks:
            sh = {ids[i]: a for i, a in D["scenarios"][k]["shocks"].items()
                  if i in ids}
            if not sh:
                continue
            st, _ = run(sh)
            reach.append(max(int((np.abs(st) >= 0.02).sum()), 1))
        if reach:
            rows.append((c["label"], sorted(reach)))
    rows.sort(key=lambda r: max(r[1]))
    for i, (lab, reach) in enumerate(rows):
        ax4.plot([min(reach), max(reach)], [i, i], color=RULE, lw=3.0,
                 solid_capstyle="round", zorder=1)
        ax4.scatter(reach, [i] * len(reach), s=26, color="#5a63c8",
                    alpha=0.95, zorder=2, edgecolors=BG, linewidths=0.7)
    ax4.set_yticks(range(len(rows)))
    # The longest category name reaches across the gutter into the histogram
    # beside it. The audit compares text with text, not text with a plot area,
    # so it reported a clean sheet; these are shortened for the axis instead.
    SHORTCAT = {"Universe & Earth, exogenous": "Universe & Earth",
                "Technology improvement & buildout": "Technology",
                "Climate goal meetings": "Climate goals",
                "Country policy changes": "Country policy",
                "Energy makeup evolution": "Energy makeup",
                "People & cognition": "People",
                "Global pandemics": "Pandemics",
                "Natural disasters": "Disasters"}
    ax4.set_yticklabels([SHORTCAT.get(r[0], r[0]) for r in rows],
                        fontsize=8.4)
    ax4.set_xscale("log")
    ax4.set_xlim(0.7, max(max(r[1]) for r in rows) * 4)
    ax4.set_xlabel("nodes moved by more than 0.02 (log scale)", color=DIM,
                   fontsize=9.5)
    ax4.set_title(f"How far the {len(D['scenarios'])} prepared changes travel",
                  color=INK, fontsize=12.5, loc="left", pad=8)

    for a in (ax, ax3, ax4):
        a.set_facecolor(BG)
        a.grid(axis="x", alpha=0.15, which="both")
        a.set_axisbelow(True)
        a.tick_params(colors=DIM, labelsize=8.4)
        for s in a.spines.values():
            s.set_color(RULE)
    ax2.set_facecolor(BG)

    problems = audit(fig)
    fig.savefig(OUT, dpi=140, facecolor=BG)
    plt.close(fig)
    print(f"  wrote {os.path.basename(OUT)}")
    print("  0 layout problems" if not problems
          else f"  {len(problems)} layout problem(s): " + "; ".join(problems[:8]))
    return len(problems)


if __name__ == "__main__":
    main()
