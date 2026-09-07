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
from sitefig import BG, INK, DIM, RULE, FAINT, ACC, COOL, MOSS, ROSE, SLATE, DISTRICT, SUPPLY, PSYCH, SUN, INSOL, GOLD, GREY, VIOLET, BLUE, GREEN, WARM, ARROW, ONE_WAY_COL, TWO_WAY_COL, NODE_COL, WARM2, KCOL, CYCLE, FS_2, FS_1, FS0, FS1, FS2, FONT, MONO, NOTES, PROSE, CARD, THUMB, fig_size, save, WIDE, PLOT, SQUARE, TALL, row_aspect, panel  # noqa: E402,F401
import sitefig  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from build_throughlines import (BG, DIM, INK, KCOL, LABEL, RULE, SHORT,
                                audit, engine, style)
from build_layer_diagram import rank_from_app
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "assets", "atlas-data.js")
OUT = os.path.join(HERE, "site", "assets", "energy_model_chart.png")

ORDER = ["sun", "insolation", "weather", "climate", "event", "market",
         "supply", "grid", "station", "district", "consumer", "psych"]


def main():
    style()
    raw = open(DATA, encoding="utf-8").read()
    D = json.loads(raw[raw.index("=") + 1:raw.rindex(";")])
    kind = [D["kinds"][k] for k in D["kind"]]
    counts = collections.Counter(kind)
    ids = {k: int(v) for k, v in D["idMap"].items()}
    run, _ = engine(D)

    # 14.4in put the on-screen factor (pt * 1140 / (72 * width)) at ~1.10 -
    # the 8.0pt donut legend landed at 8.8px, under the 11px floor. 10.2x6.1
    # keeps the aspect ratio and raises the factor to ~1.55, clearing every
    # label already on this sheet without touching a single fontsize=.
    # Height went from 6.1 to 6.6 on top of that: narrowing the figure while
    # leaving the header text at the same fontsize meant the title+subtitle
    # block took a bigger bite out of a shorter canvas, and gs's old
    # top=0.845 didn't move to compensate - the subtitle and the right
    # panel's title ("Where the numbers come from") ended up in the same
    # horizontal band, and the left panel's title sat almost flush under
    # the subtitle. The extra 0.5in, spent below via gs's top=, buys a
    # header strip tall enough for both lines of text plus a clear gap
    # before any panel title starts.
    fig = plt.figure(figsize=fig_size(NOTES, 0.95), facecolor=BG)
    # 714 px wide: room on the left for the longest kind label at 12 px,
    # and under the donut for its two-column legend
    # The donut's legend hangs below its axes, seven lines of it, and at
    # hspace=0.6 the last line ("everything else") sat on the lower-right
    # panel's label. The audit did not see it because it read only the
    # centre title slot (sitefig.titles() fixed that, 2026-09-04); the
    # upper row is now taller and the gap wider so the legend clears.
    # THE GRID. Two columns, each an axes of the same width with a gutter of
    # the same width on its left for tick labels (both columns carry a row
    # of long y labels: the kinds at top left, the categories at bottom
    # right). The donut's legend hangs under the donut, centred on it. Then
    # sitefig.centre() measures the content and centres the whole sheet;
    # the margins below are only a starting point. Until 2026-09-05 this was
    # a GridSpec with left=0.2 and a legend anchored 0.42 axes-widths to the
    # left of the donut: the content sat 23px right of centre and the donut
    # 40px right of its key, and no audit measured either - the third fault
    # on this figure, and the same cause as the first two: assembled by
    # hand, off the system the other sheets use.
    # The numbers, in CSS px of a 714 canvas: a label gutter of 95 on the
    # left of each column (the widest y label is about 90), an axes of 239
    # in each, a 30 gap: 8 + 95 + 239 + 30 + 95 + 239 = 706. So left =
    # 103/714, wspace = (30 + 95)/239, right = 706/714; the second column's
    # gutter lives inside the wspace. The donut legend hangs under the
    # donut, centred, and its names are cut to fit the column (below).
    gs = fig.add_gridspec(2, 2, hspace=0.95, wspace=0.52, height_ratios=[1.12, 1],
                          left=0.144, right=0.989, top=0.94, bottom=0.08)


    # ---- what the model contains ---------------------------------------
    ax = fig.add_subplot(gs[0, 0])
    ks = [k for k in ORDER if counts[k]]
    vals = [counts[k] for k in ks]
    # Twelve kinds is more than the palette can separate: coloured one hue
    # per kind, climate at near-black read as a different sort of thing
    # rather than one more kind. The bars now carry the one distinction the
    # model itself makes between kinds, the same one the layer diagram
    # draws: the kinds that push and are never pushed back (the ranked ones
    # in atlas-app.js) against the kinds that trade back and forth.
    sources = set(rank_from_app()[0])
    ax.barh(range(len(ks)), vals,
            color=[ONE_WAY_COL if k in sources else TWO_WAY_COL for k in ks],
            height=0.66, alpha=0.92)
    # under the axes, not inside them: inside, the key's colour patches sat
    # on the "18" of insolation, which text-against-text audits cannot see
    ax.legend([Patch(color=ONE_WAY_COL), Patch(color=TWO_WAY_COL)],
              ["pushes one way", "trades back and forth"], loc="upper center",
              bbox_to_anchor=(0.5, -0.26), frameon=False, fontsize=FS_2,
              labelcolor=DIM, handlelength=1.2, ncol=1)   # centred on its panel, like the donut's
    ax.set_yticks(range(len(ks)))
    ax.set_yticklabels([LABEL[k] for k in ks], fontsize=FS_2)
    ax.set_xscale("log")
    ax.set_xlim(0.7, max(vals) * 9)
    for i, v in enumerate(vals):
        ax.text(v * 1.25, i, f"{v:,}", va="center", color=DIM, fontsize=FS_2)
    ax.set_xlabel("nodes (log scale)", color=DIM, fontsize=FS_2)
    sitefig.panel(ax, "What the model contains")
    ax.invert_yaxis()

    # ---- where the numbers come from ------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    src = collections.Counter()
    for i in range(D["n"]):
        s = D["srcDict"][D["src"][i]]
        # 26 characters cut "WRI Global Power Plant Database" to "...Dat";
        # under the donut there is room for the whole name
        # 30 characters: the legend hangs centred under the donut, so its
        # width is the column's, and the longest name must fit that
        name = s.split("·")[0].strip().split(",")[0]
        src[name if len(name) <= 24 else name[:23] + "…"] += 1
    top = src.most_common(6)
    other = sum(src.values()) - sum(v for _, v in top)
    labs = [f"{k} — {v:,}" for k, v in top]
    vals2 = [v for _, v in top]
    if other:
        labs.append(f"everything else — {other:,}")
        vals2.append(other)
    cols = [ACC, COOL, MOSS, ROSE, SLATE,
            PSYCH, SUPPLY, DISTRICT][:len(vals2)]
    w, _ = ax2.pie(vals2, colors=cols, startangle=90,
                   wedgeprops=dict(width=0.42, edgecolor=BG, linewidth=1.4))
    # under the donut, not beside it: beside it the longest source name ran
    # off the right edge of the sheet
    ax2.legend(w, labs, loc="upper center", bbox_to_anchor=(0.5, -0.02),
               frameon=False, fontsize=FS_2, labelcolor=DIM, ncol=1)
    sitefig.panel(ax2, "Where the numbers\ncome from")

    # ---- link weights ----------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    ew = np.asarray(D["ew"], dtype=float)
    ax3.hist(ew[ew > 0], bins=46, color=MOSS, alpha=0.9, label="positive")
    if (ew < 0).any():
        ax3.hist(ew[ew < 0], bins=24, color=ROSE, alpha=0.9,
                 label="negative")
    ax3.set_yscale("log")
    # matplotlib offers decades well outside the data on a log count axis,
    # and those labels land outside the panel. Bound the axis to the data.
    hi = max(np.histogram(ew[ew > 0], bins=46)[0].max(), 1)
    ax3.set_ylim(0.8, hi * 3)
    ax3.set_xlabel("link weight", color=DIM, fontsize=FS_2)
    ax3.set_ylabel("links", color=DIM, fontsize=FS_2)
    sitefig.panel(ax3, "Link weights")
    ax3.legend(frameon=False, fontsize=FS_2, labelcolor=DIM)

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
        ax4.scatter(reach, [i] * len(reach), s=26, color=SLATE,
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
                        fontsize=FS_2)
    ax4.set_xscale("log")
    ax4.set_xlim(0.7, max(max(r[1]) for r in rows) * 4)
    ax4.set_xlabel("nodes moved past 0.02 (log scale)", color=DIM,
                   fontsize=FS_2)     # fits the 239px column; the long form ran off the canvas
    sitefig.panel(ax4, f"How far the {len(D['scenarios'])} prepared\nchanges travel")

    for a in (ax, ax3, ax4):
        a.set_facecolor(BG)
        a.grid(axis="x", alpha=0.15, which="both")
        a.set_axisbelow(True)
        a.tick_params(colors=DIM, labelsize=FS_2)
        for s in a.spines.values():
            s.set_color(RULE)
    ax2.set_facecolor(BG)

    sitefig.centre(fig)
    problems = audit(fig)
    # dpi raised to keep the bitmap's pixel count close to what it was at the
    # old, wider figsize - it has no effect on the on-screen CSS size the
    # floor check above is about, and was never touched to fix legibility.
    sitefig.save(fig, OUT, close=False)
    plt.close(fig)
    print(f"  wrote {os.path.basename(OUT)}")
    print("  0 layout problems" if not problems
          else f"  {len(problems)} layout problem(s): " + "; ".join(problems[:8]))
    return len(problems)


if __name__ == "__main__":
    main()
