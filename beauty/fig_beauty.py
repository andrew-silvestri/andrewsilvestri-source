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
NEWLINE = chr(10)
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


def hi_room(vals):
    """A label offset scaled to the data, so a value sits clear of its own
    whisker at any magnitude rather than at a hard-coded number of units."""
    return (max(vals) - min(vals)) * 0.045


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
    sitefig.panel(ax, "What the literature says")
    fig.text(0.01, 0.01, f"Threatened species: IUCN Red List {ver.group(0) if ver else ''}, Table 1a. Papers: "
             f"OpenAlex works {P['groups']['works_years']} whose title or abstract\nnames the class, "
             "biology or environment topics. Rising: more of the papers than of the threatened species.\n"
             "FIVE POINTS, NO MODEL, AND NOT WHAT THIS PAGE TESTS - it is the between-class "
             "picture the literature describes.\nEverything below is within ONE class, birds, "
             "where the pattern runs the other way.",
             fontsize=FS_2, color=DIM, ha="left", va="bottom")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.28)
    return emit(fig, "beauty_fig1_gap.png")


def fig2(P):
    """Raw, total and direct, one row per Red List category.

    Two moves, and the page reads them as two different things. Raw to
    total is the reversal: holding family, mass, range and description year
    fixed does not collapse the gap, it widens it. Total to direct is the
    share of that advantage running through public attention, and its
    DIRECTION is assumed rather than shown - a cross-section with a
    single-timepoint mediator cannot order threat -> attention -> research
    against research -> better article -> views.
    """
    cats = P["categories"]
    names = [P["category_names"][c].replace(" ", NEWLINE) for c in cats]
    raw = [P["raw_by_category"][c]["typical"] for c in cats]
    tot = [P["model_noviews"]["adjusted"][c] for c in cats]
    dirc = [P["model_full"]["adjusted"][c] for c in cats]
    ci_raw = [P["bootstrap"]["raw"][c] for c in cats]
    # the TOTAL point needs the TOTAL model's interval. It carried
    # bootstrap["full_adj"] until 2026-09-09, which put the Critically
    # Endangered point at 48.1 outside its own whisker, because that key
    # is the full model's spread around a different estimate. The audit
    # cannot see this: a point outside its interval is not text on text.
    ci_tot = [P["bootstrap"]["noviews_adj"][c] for c in cats]
    x = np.arange(len(cats))
    fig, ax = plt.subplots(figsize=fig_size(NOTES, PLOT))
    for xi, ci in zip(x - 0.26, ci_raw):
        ax.plot([xi, xi], ci, color=DIM, lw=1.4, zorder=2)
    for xi, ci in zip(x, ci_tot):
        ax.plot([xi, xi], ci, color=ACC, lw=1.4, zorder=2)
    for xi, lo, hi_ in zip(x, dirc, tot):
        ax.plot([xi + 0.04, xi + 0.24], [hi_, lo], color=MOSS, lw=1.0, ls=":", zorder=2)
    ax.plot(x - 0.26, raw, "o", mfc="white", mec=DIM, mew=1.6, ms=7, zorder=3,
            label="as counted")
    ax.plot(x, tot, "o", color=ACC, ms=7, zorder=3,
            label="family, mass, range and years since description held fixed")
    ax.plot(x + 0.26, dirc, "s", color=MOSS, ms=6, zorder=3,
            label="the same, and Wikipedia views held fixed too")
    hi = max(max(c[1] for c in ci_raw + ci_tot), max(raw + tot + dirc))
    off = hi_room(raw + tot + dirc)
    for xi, v, ci in zip(x - 0.26, raw, ci_raw):
        ax.text(xi, ci[1] + off, "%.1f" % v, ha="center", va="bottom",
                fontsize=FS_2, color=DIM)
    for xi, v, ci in zip(x, tot, ci_tot):
        ax.text(xi, ci[1] + off, "%.1f" % v, ha="center", va="bottom",
                fontsize=FS_2, color=ACC)
    for xi, v in zip(x + 0.26, dirc):
        ax.text(xi + 0.08, v, "%.1f" % v, ha="left", va="center",
                fontsize=FS_2, color=MOSS)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=FS_2, color=INK)
    ax.set_xlim(-0.72, len(cats) - 0.28)
    ax.set_ylim(0, hi * 1.42)
    ax.set_ylabel("papers per species, 2015-2024 (typical)", fontsize=FS_2, color=DIM)
    ax.grid(axis="y", color=FAINT, lw=0.8)
    ax.set_axisbelow(True)
    bare(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=FS_2, labelcolor=INK,
              handletextpad=0.6)
    sitefig.panel(ax, "Papers per bird species by Red List category, n = %s"
                  % format(P["n"]["modelled"], ","))
    ms = P["mediated_share"]
    fig.text(0.01, 0.01,
             "Typical: back-transformed mean of log(1 + papers). Whiskers: 95%% "
             "bootstrap intervals, %s resamples. Red List %s;%s"
             "Data Deficient, Extinct and Extinct in the Wild species left out. The "
             "dotted drop is the share of the advantage%s"
             "that runs through public attention: %.0f%% at Near Threatened, %.0f%% at "
             "Critically Endangered. Its direction is ASSUMED."
             % (P["n_boot"], P["red_list_version"], NEWLINE, NEWLINE,
                100 * ms["NT"], 100 * ms["CR"]),
             fontsize=FS_2, color=DIM, ha="left", va="bottom")
    fig.subplots_adjust(left=0.1, right=0.98, top=0.9, bottom=0.30)
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


def fig4(P):
    """The Red List coefficient inside OpenAlex topic fields.

    Tests whether the effect is made of papers ABOUT the listing. The rule
    - minimum cell, primary stratum, failure threshold - was committed in
    PRESPEC_topics_2026-09-09.md before any topic data existed, and the
    strata that FAIL the cell floor are drawn as named gaps carrying their
    Critically Endangered cell count, never as points. A reader must be able
    to see what was excluded and why without being able to read a value off
    it.
    """
    S = P.get("strata", {})
    if not S.get("available"):
        return 0
    order = ["13", "19", "11", "23", "28", "24", "27"]
    fields = S["fields"]
    rows = [f for f in order if f in fields]
    labels = {"11": "Agricultural and\nBiological Sciences",
              "13": "Biochemistry, Genetics\nand Molecular Biology",
              "19": "Earth and\nPlanetary Sciences",
              "23": "Environmental Science",
              "24": "Immunology and\nMicrobiology",
              "27": "Medicine", "28": "Neuroscience"}
    y = np.arange(len(rows))[::-1]
    fig, ax = plt.subplots(figsize=fig_size(NOTES, row_aspect(len(rows), row_px=52)))
    floor = S["rule"]["cr_floor"]
    ax.axvline(floor, color=MOSS, lw=1.2, ls="--", zorder=2)
    ticks = []
    for yi, fid in zip(y, rows):
        rec = fields[fid]
        prone = rec["artefact_prone"]
        ticks.append(labels[fid])
        if not rec["reportable"]:
            ax.text(0.02, yi, "below the cell floor - CR n = %d, not interpreted"
                    % rec["cells"]["CR"], fontsize=FS_2, color=DIM,
                    ha="left", va="center", style="italic")
            continue
        cr = rec["category"]["CR"]
        col = MOSS if prone else ACC
        ax.plot([cr["lo"], cr["hi"]], [yi, yi], color=col, lw=1.6, zorder=3)
        ax.plot([cr["coef"]], [yi], "o", color=col, ms=7, zorder=4)
        note = "  %+.3f" % cr["coef"]
        if rec["role"] == "primary":
            note += "   PRIMARY"
        elif rec["role"] == "positive_control":
            note += "   positive control"
        ax.text(cr["hi"] + 0.03, yi, note, fontsize=FS_2, color=INK,
                ha="left", va="center")
    ax.set_yticks(y)
    ax.set_yticklabels(ticks, fontsize=FS_2, color=INK)
    ax.set_xlim(-0.05, 1.95)
    ax.set_xlabel("Critically Endangered vs Least Concern, log(1 + papers in that field)",
                  fontsize=FS_2, color=DIM)
    ax.grid(axis="x", color=FAINT, lw=0.8)
    ax.set_axisbelow(True)
    bare(ax)
    ax.tick_params(axis="y", length=0)
    sitefig.panel(ax, "Does it survive where a status review cannot go?")
    fig.text(0.01, 0.01,
             "Brown: fields carrying conservation writing. Blue: fields that cannot.%s"
             "Whiskers: HC1 95%% intervals. Rule fixed before the data existed (%s):%s"
             "minimum %d species per category, primary field Biochemistry/Genetics,%s"
             "dashed line the %+.2f floor. Three fields fail it, named without a value."
             % (NEWLINE, S["rule"]["prespec"], NEWLINE,
                S["rule"]["min_cell_per_category"], NEWLINE, floor),
             fontsize=FS_2, color=DIM, ha="left", va="bottom")
    fig.subplots_adjust(left=0.28, right=0.97, top=0.88, bottom=0.30)
    return emit(fig, "beauty_fig4_strata.png")


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    sitefig.style()
    bad = fig1(P) + fig2(P) + fig3(P) + fig4(P)
    print(f"  {bad} layout problem(s) in total")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
