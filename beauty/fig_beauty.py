"""
The three figures for site/beauty.html, drawn from outputs/beauty_payload.json.

  beauty_fig1_gap.png        five vertebrate classes: share of threatened
                             species against share of papers, a slope chart
  beauty_fig2_category.png   papers per bird species by Red List category,
                             raw and adjusted, with bootstrap intervals
  beauty_fig3_terms.png      what the full model's fit depends on: drop-one
                             change in R-squared per term, ranked

Every colour, size and face comes from sitefig.py. No species is named in
any figure and no species-level point is drawn: the Red List's terms leave
category-per-species unrestricted for use but not for redistribution, and
a figure of 9,000 labelled points would be a table. Each figure is audited
for text that overlaps, runs off the canvas or falls under the size floor,
and the build prints the count, which must be 0.

Run:  python3 fig_beauty.py
"""

import json
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
import sitefig                                              # noqa: E402
from sitefig import (ACC, DIM, FAINT, FS_2, FS_1, INK, MOSS, NOTES, PLOT,  # noqa: E402
                     RULE, fig_size, row_aspect)
from fig_floor import floor_problems                        # noqa: E402

PAYLOAD = os.path.join(HERE, "outputs", "beauty_payload.json")
OUT = os.path.join(ROOT, "site", "assets")


def audit(fig):
    """Text that overlaps other text, runs off the canvas or is under the
    size floor, plus the grid checks. The idiom is fig_food.py's: every
    Text object is enumerated explicitly."""
    fig.canvas.draw()
    ren = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    title_ids = {id(t) for ax in fig.axes for t in sitefig.titles(ax)}
    problems_grid = sitefig.grid_problems(fig)
    items = [t for t in fig.texts if t.get_text().strip()]
    for ax in fig.axes:
        for t in sitefig.titles(ax) + [ax.xaxis.label, ax.yaxis.label] + list(ax.texts):
            if t.get_text().strip():
                items.append(t)
        if ax.axison:
            x0, x1 = sorted(ax.get_xlim())
            y0, y1 = sorted(ax.get_ylim())
            for tk, lo, hi in ((ax.xaxis, x0, x1), (ax.yaxis, y0, y1)):
                if not tk.get_visible():
                    continue
                for loc, lab in zip(tk.get_ticklocs(), tk.get_ticklabels()):
                    if lo - 1e-9 <= loc <= hi + 1e-9 and \
                            lab.get_text().strip() and lab.get_visible():
                        items.append(lab)
        lg = ax.get_legend()
        if lg:
            items += [x for x in lg.get_texts() if x.get_text().strip()]
    boxes = []
    for t in items:
        try:
            boxes.append((t.get_text()[:30], t.get_window_extent(renderer=ren)))
        except Exception:                                    # noqa: BLE001
            pass
    bad = []
    for lab, b in boxes:
        if b.x0 < -1 or b.y0 < -1 or b.x1 > W + 1 or b.y1 > H + 1:
            bad.append(f"off canvas: {lab!r}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (la, a), (lb, b) = boxes[i], boxes[j]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0)
            oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ox > 0 and oy > 0:
                fr = ox * oy / min(a.width * a.height, b.width * b.height)
                if fr > 0.15:
                    bad.append(f"overlap {fr:.0%}: {la!r} / {lb!r}")
    bad += floor_problems(fig, [(t, id(t) in title_ids) for t in items])
    return bad + problems_grid


def emit(fig, name):
    bad = audit(fig)
    sitefig.save(fig, os.path.join(OUT, name), close=False)
    plt.close(fig)
    flag = "  LAYOUT: " + "; ".join(bad[:3]) if bad else ""
    print(f"  {name:26s} {len(bad)} layout problems{flag}")
    return len(bad)


def bare(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(RULE)
    ax.tick_params(colors=DIM, labelsize=FS_2)


def spread(ys, gap):
    """Label positions nudged apart, in place order, so none sit closer than
    gap; the points themselves are not moved."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    out = list(ys)
    for a, b in zip(order, order[1:]):
        if out[b] - out[a] < gap:
            out[b] = out[a] + gap
    return out


def fig1(P):
    rows = sorted(P["groups"]["rows"], key=lambda r: -r["share_threatened"])
    ver = re.search(r"\d{4}-\d", P["groups"]["source_table"])
    fig, ax = plt.subplots(figsize=fig_size(NOTES, PLOT))
    ax.set_xlim(-1.5, 1.95)
    top = max(max(r["share_threatened"], r["share_works"]) for r in rows) * 1.12
    ax.set_ylim(-top * 0.02, top)
    ly = spread([r["share_threatened"] for r in rows], top * 0.12)
    ry = spread([r["share_works"] for r in rows], top * 0.12)
    for r, yl, yr in zip(rows, ly, ry):
        up = r["share_works"] >= r["share_threatened"]
        col = ACC if up else MOSS
        ax.plot([0, 1], [r["share_threatened"], r["share_works"]], color=col, lw=2.2, zorder=3)
        ax.plot([0, 1], [r["share_threatened"], r["share_works"]], "o", color=col, ms=6, zorder=4)
        ax.text(-0.06, yl, f"{r['group']}  {r['share_threatened']:.0%}", ha="right", va="center",
                fontsize=FS_1, color=INK)
        ax.text(-0.06, yl - top * 0.03, f"{r['pct_evaluated']:.0f}% of the class assessed",
                ha="right", va="top", fontsize=FS_2, color=DIM)
        ax.text(1.06, yr, f"{r['share_works']:.0%}", ha="left", va="center", fontsize=FS_1, color=INK)
        ax.text(1.06, yr - top * 0.03, f"{r['works_per_threatened']:.0f} papers per threatened species",
                ha="left", va="top", fontsize=FS_2, color=DIM)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["share of threatened\nvertebrate species", "share of papers\nnaming the class"],
                       fontsize=FS_1, color=INK)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    bare(ax)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0)
    sitefig.panel(ax, "Where the threatened species are, and where the papers are")
    fig.text(0.01, 0.01, f"Threatened species: IUCN Red List {ver.group(0) if ver else ''}, Table 1a. Papers: "
             f"OpenAlex works {P['groups']['works_years']} whose title or abstract\nnames the class, "
             "biology or environment topics. Rising: more of the papers than of the threatened species.",
             fontsize=FS_2, color=DIM, ha="left", va="bottom")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.2)
    return emit(fig, "beauty_fig1_gap.png")


def fig2(P):
    cats = P["categories"]
    names = [P["category_names"][c].replace(" ", "\n") for c in cats]
    raw = [P["raw_by_category"][c]["typical"] for c in cats]
    adj = [P["model_confounders"]["adjusted"][c] for c in cats]
    ci_raw = [P["bootstrap"]["raw"][c] for c in cats]
    ci_adj = [P["bootstrap"]["conf_adj"][c] for c in cats]
    x = np.arange(len(cats))
    fig, ax = plt.subplots(figsize=fig_size(NOTES, PLOT))
    for xi, v, ci in zip(x - 0.12, raw, ci_raw):
        ax.plot([xi, xi], ci, color=DIM, lw=1.4, zorder=2)
    for xi, v, ci in zip(x + 0.12, adj, ci_adj):
        ax.plot([xi, xi], ci, color=ACC, lw=1.4, zorder=2)
    ax.plot(x - 0.12, raw, "o", mfc="white", mec=DIM, mew=1.6, ms=7, zorder=3, label="as counted")
    ax.plot(x + 0.12, adj, "o", color=ACC, ms=7, zorder=3,
            label="holding family, body mass, range size and\nyears since description fixed")
    hi = max(max(c[1] for c in ci_raw + ci_adj), max(raw + adj))
    for xi, v in zip(x - 0.12, raw):
        ax.text(xi - 0.06, v, f"{v:.1f}", ha="right", va="center", fontsize=FS_2, color=DIM)
    for xi, v in zip(x + 0.12, adj):
        ax.text(xi + 0.06, v, f"{v:.1f}", ha="left", va="center", fontsize=FS_2, color=ACC)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=FS_2, color=INK)
    ax.set_ylim(0, hi * 1.25)
    ax.set_ylabel("papers per species, 2015–2024 (typical)", fontsize=FS_2, color=DIM)
    ax.grid(axis="y", color=FAINT, lw=0.8)
    ax.set_axisbelow(True)
    bare(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=FS_2, labelcolor=INK, handletextpad=0.6)
    sitefig.panel(ax, f"Papers per bird species by Red List category, n = {P['n']['modelled']:,}")
    fig.text(0.01, 0.01, "Typical: back-transformed mean of log(1 + papers). Whiskers: 95% bootstrap "
             f"intervals, {P['n_boot']} resamples.\nRed List {P['red_list_version']}; "
             "Data Deficient, Extinct and Extinct in the Wild species left out.",
             fontsize=FS_2, color=DIM, ha="left", va="bottom")
    fig.subplots_adjust(left=0.1, right=0.98, top=0.9, bottom=0.24)
    return emit(fig, "beauty_fig2_category.png")


def fig3(P):
    M = P["model_full"]
    terms = sorted(M["terms"], key=lambda t: M["drop_r2"][t])
    vals = [M["drop_r2"][t] for t in terms]
    cis = [P["bootstrap"]["full_drop"][t] for t in terms]
    labels = [P["term_labels"][t] for t in terms]
    y = np.arange(len(terms))
    fig, ax = plt.subplots(figsize=fig_size(NOTES, row_aspect(len(terms), row_px=44)))
    cols = [MOSS if t == "category" else ACC for t in terms]
    ax.barh(y, vals, color=cols, height=0.58, zorder=3)
    for yi, ci in zip(y, cis):
        ax.plot(ci, [yi, yi], color=INK, lw=1.2, zorder=4)
    xmax = max(max(c[1] for c in cis), max(vals)) * 1.3
    for yi, v, ci in zip(y, vals, cis):
        ax.text(ci[1] + xmax * 0.015, yi, f"{v:.3f}", va="center", ha="left", fontsize=FS_2, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=FS_1, color=INK)
    ax.set_xlim(0, xmax)
    ax.set_xlabel("fall in R² when the term is dropped from the full model", fontsize=FS_2, color=DIM)
    ax.grid(axis="x", color=FAINT, lw=0.8)
    ax.set_axisbelow(True)
    bare(ax)
    ax.tick_params(axis="y", length=0)
    sitefig.panel(ax, f"What the fit depends on (R² = {M['r2']:.2f})")
    fig.text(0.01, 0.01, f"Whiskers: 95% bootstrap intervals, {P['n_boot']} resamples. "
             "Family enters as fixed effects.", fontsize=FS_2, color=DIM, ha="left", va="bottom")
    fig.subplots_adjust(left=0.3, right=0.97, top=0.86, bottom=0.2)
    return emit(fig, "beauty_fig3_terms.png")


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    sitefig.style()
    bad = fig1(P) + fig2(P) + fig3(P)
    print(f"  {bad} layout problem(s) in total")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
