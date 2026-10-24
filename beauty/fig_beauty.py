"""
The figures for site/beauty.html, drawn from outputs/beauty_payload.json.

  beauty_fig0_records.png    the hero (R5, D-32): for the typical bird in each
  (+ -phone.png at 350)      Red List category, everything a search for its
                             name returns against research alone
  beauty_fig1_gap.png        five vertebrate classes: share of threatened
                             species against share of research works
  beauty_fig2_category.png   research works per bird species by Red List
                             category, raw and adjusted, with bootstrap intervals
  beauty_fig3_terms.png      what the full model's fit depends on: drop-one
                             change in R-squared per term, ranked

beauty_fig4_strata.png (the topic-field test) was retired with the test on
2026-10-24: QA found the non-research records are filed under every topic
field, so the field could not separate paperwork from research (D-32).

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
# An audit line carries the text of what it found, and this tree's figures are
# full of characters a Windows console's default code page cannot encode:
# U+2212 in heat's colourbar label, U+2192 in the allocation figure's. Printing
# one raises UnicodeEncodeError and the builder dies REPORTING a problem, after
# auditing some of its figures and before auditing the rest. The crash needs a
# finding to appear, so a clean tree hides it entirely.
# Measured 2026-09-12: heat/model.py reported 1 of 7 figures and crashed;
# climate-cost/build_allocation_figure.py still crashed on U+2192 after the
# heat fix. Same fix and same reason as tests/test_generators.py and
# build_layer_diagram.py.
if hasattr(sys, "stdout") and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
import sitefig                                              # noqa: E402
from sitefig import (ACC, DIM, FAINT, FS_2, FS_1, INK, MOSS, NOTES, PHONE, PLOT,  # noqa: E402
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
    """Five classes: share of threatened species against share of research.

    Labels are one line each and joined to their dots by a leader whenever
    spread() has had to move them. Until 2026-10-24 the labels were two lines,
    spread() moved them up to clear each other and nothing tied them back, so
    the amphibian label sat beside the reptile dot's height and two right-hand
    values shared one dot (found by R5's skeptical-reader review). The audit
    cannot see that: a label beside the wrong point is not text on text.
    """
    rows = sorted(P["groups"]["rows"], key=lambda r: -r["share_threatened"])
    ver = re.search(r"\d{4}-\d", P["groups"]["source_table"])
    fig, ax = plt.subplots(figsize=fig_size(NOTES, PLOT))
    ax.set_xlim(-1.5, 2.4)
    top = max(max(r["share_threatened"], r["share_works"]) for r in rows) * 1.08
    ax.set_ylim(-top * 0.04, top)
    gap = top * 0.075
    ly = spread([r["share_threatened"] for r in rows], gap)
    ry = spread([r["share_works"] for r in rows], gap)
    for r, yl, yr in zip(rows, ly, ry):
        up = r["share_works"] >= r["share_threatened"]
        col = ACC if up else MOSS
        y0, y1 = r["share_threatened"], r["share_works"]
        ax.plot([0, 1], [y0, y1], color=col, lw=2.2, zorder=3)
        ax.plot([0, 1], [y0, y1], "o", color=col, ms=6, zorder=4)
        ax.plot([-0.02, -0.12], [y0, yl], color=col, lw=0.8, zorder=2)
        ax.plot([1.02, 1.12], [y1, yr], color=col, lw=0.8, zorder=2)
        ax.text(-0.15, yl, f"{r['group']} {r['share_threatened']:.0%}  ({r['pct_evaluated']:.0f}% assessed)",
                ha="right", va="center", fontsize=FS_2, color=INK)
        ax.text(1.15, yr, f"{r['share_works']:.0%}  ({r['works_per_threatened']:.0f} per threatened species)",
                ha="left", va="center", fontsize=FS_2, color=INK)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["share of threatened\nvertebrate species", "share of research\nworks naming the class"],
                       fontsize=FS_1, color=INK)
    ax.set_yticks([])
    bare(ax)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0)
    sitefig.panel(ax, "Five vertebrate classes")
    fig.text(0.01, 0.01, f"Threatened species: IUCN Red List {ver.group(0) if ver else ''}, Table 1a. Research "
             f"works: OpenAlex {P['groups']['works_years']}, title or abstract\nnames the class, "
             "biology or environment topics, research record types only.\n"
             "Blue: more of the research than of the threatened species. Five points, no model:\n"
             "the between-class picture, not what this page tests within birds.",
             fontsize=FS_2, color=DIM, ha="left", va="bottom")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.27)
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
            label="family, mass, range, age and rated attractiveness held fixed")
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
    ax.set_ylabel("research works per species,\n2015-2024 (typical)", fontsize=FS_2, color=DIM)
    ax.grid(axis="y", color=FAINT, lw=0.8)
    ax.set_axisbelow(True)
    bare(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=FS_2, labelcolor=INK,
              handletextpad=0.6)
    sitefig.panel(ax, "Research works per bird species by Red List category, n = %s"
                  % format(P["n"]["modelled"], ","))
    ms = P["mediated_share"]
    fig.text(0.01, 0.01,
             "Typical: back-transformed mean of log(1 + research works). Whiskers: 95%% "
             "bootstrap intervals,%s%s resamples of whole families. Red List %s; "
             "Data Deficient, Extinct and Extinct in the Wild species left out. The "
             "dotted%sline joins each category's adjusted value to the same with views "
             "held fixed;%swhich way attention and research cause each other is not known."
             % (NEWLINE, P["n_boot"], P["red_list_version"], NEWLINE, NEWLINE),
             fontsize=FS_2, color=DIM, ha="left", va="bottom")
    fig.subplots_adjust(left=0.12, right=0.98, top=0.9, bottom=0.34)
    return emit(fig, "beauty_fig2_category.png")


def fig3(P, width=NOTES):
    M = P["model_full"]
    terms = sorted(M["terms"], key=lambda t: M["drop_r2"][t])
    vals = [M["drop_r2"][t] for t in terms]
    cis = [P["bootstrap"]["full_drop"][t] for t in terms]
    labels = [P["term_labels"][t] for t in terms]
    y = np.arange(len(terms))
    fig, ax = plt.subplots(figsize=fig_size(
        width, row_aspect(len(terms), row_px=44, display_px=width)))
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
    fig.text(0.01, 0.01, f"Whiskers: 95% bootstrap intervals, {P['n_boot']} resamples of families. "
             "Family enters as fixed effects.", fontsize=FS_2, color=DIM, ha="left", va="bottom")
    fig.subplots_adjust(left=0.3, right=0.97, top=0.86, bottom=0.2)
    name = ("beauty_fig3_terms.png" if width == NOTES
            else "beauty_fig3_terms-phone.png")
    # THE SECOND RENDER IS A SECOND FIGURE, NOT A SCALED ONE. A 714px figure
    # served into a 350px column shows its 12pt floor at 5.9px, and dpi cannot
    # change that: what a reader sees is point size times served width over
    # authored width (fig_floor.py). <picture> picks between them and
    # tests/test_fig_floor.py measures the result at the served width.
    #
    # fit_ticks runs at BOTH widths and is a no-op at the one that already
    # passes - it tries the unchanged figure first and returns there. What it
    # applies at 350 is a margin, measured, judged by the same predicate
    # audit() uses. No label's words change at either width.
    did = sitefig.fit_ticks(ax, "y")
    if did != "unchanged":
        print(f"    fit_ticks {name}: {did}")
    return emit(fig, name)


def fig0(P, width=NOTES):
    """The hero: for the typical bird in each Red List category, everything
    a search returns against research alone.

    Both bars are the same model's adjusted typical counts (the total-effect
    terms; record_types.fits works_typed and research), so they are
    comparable with each other and with the page's headline. They are not
    stacked: typical values do not add, so research is drawn beside the
    total, not inside it. A first version stacked category AVERAGES by
    record type (R5, 2026-10-24) and was replaced before it shipped: the
    averages hardly differ between categories (11 research works for Least
    Concern, 13 for Critically Endangered), because a few famous common
    birds dominate them, so the figure argued against the headline it sat
    under. The page states that averages point in its text.
    """
    F = P["record_types"]["fits"]
    cats = P["categories"]
    tot = [F["works_typed"]["adjusted"][c] for c in cats]
    res = [F["research"]["adjusted"][c] for c in cats]
    phone = width == PHONE
    fig, ax = plt.subplots(figsize=fig_size(width, row_aspect(
        len(cats), row_px=82 if phone else 64, display_px=width, header_px=150 if phone else 110)))
    y = np.arange(len(cats))[::-1].astype(float)
    xmax = max(tot) * 1.16
    for yi, c, t, r in zip(y, cats, tot, res):
        ax.barh(yi + 0.13, t, height=0.24, color=RULE, zorder=3)
        ax.barh(yi - 0.13, r, height=0.24, color=ACC, zorder=3)
        ax.text(t + xmax * 0.012, yi + 0.13, f"{t:.0f}", ha="left", va="center", fontsize=FS_2, color=DIM)
        ax.text(r + xmax * 0.012, yi - 0.13, f"{r:.1f}", ha="left", va="center", fontsize=FS_2, color=ACC)
        ax.text(0, yi + 0.3, P["category_names"][c], ha="left", va="bottom",
                fontsize=FS_2 if phone else FS_1, color=INK)
    ax.set_ylim(-0.5, len(cats) - 0.3)
    ax.set_xlim(0, xmax)
    ax.set_yticks([])
    ax.set_xlabel("per species, 2015-2024, typical bird" + (NEWLINE if phone else " ")
                  + "(family, size, range, age, rated attractiveness held equal)", fontsize=FS_2, color=DIM)
    ax.grid(axis="x", color=FAINT, lw=0.8)
    ax.set_axisbelow(True)
    bare(ax)
    ax.spines["left"].set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=RULE), plt.Rectangle((0, 0), 1, 1, color=ACC)]
    ax.legend(handles, ["everything a search for its name returns", "research only"],
              loc="lower left", bbox_to_anchor=(0, 1.0), ncol=1 if phone else 2, frameon=False,
              fontsize=FS_2, labelcolor=INK, handlelength=1.0, handletextpad=0.5,
              columnspacing=1.4, borderaxespad=0.2)
    fig.text(0.01, 0.01, "OpenAlex works whose title or abstract names the species;" + (NEWLINE if phone else " ")
             + "research = research record types." + NEWLINE + "n = %s birds; Red List %s."
             % (format(P["n"]["modelled"], ","), P["red_list_version"]),
             fontsize=FS_2, color=DIM, ha="left", va="bottom")
    fig.subplots_adjust(left=0.03, right=0.97, top=0.8 if phone else 0.84,
                        bottom=0.25 if phone else 0.22)
    return emit(fig, "beauty_fig0_records.png" if not phone else "beauty_fig0_records-phone.png")


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    sitefig.style()
    # NO SECOND RENDER YET, AND THE `width` PARAMETER IS NOT DEAD CODE.
    # fit_ticks clears the term and strata tick labels at 350 with a 10%
    # margin and no wrapping, but three OTHER artist classes are still off
    # canvas there - the x axis label, the panel() label, the fig.text
    # footnote, and on fig4 four hand-placed value annotations. A lever
    # governs one artist class, so these two are not conversions yet; what
    # the parameter carries is the width the lever and tests/test_fit_ticks.py
    # drive them at, and it changes nothing at NOTES (the shipped PNGs are
    # byte-identical with it in place).
    bad = fig0(P) + fig0(P, PHONE) + fig1(P) + fig2(P) + fig3(P)
    print(f"  {bad} layout problem(s) in total")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
