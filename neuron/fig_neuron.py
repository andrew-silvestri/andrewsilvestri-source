"""
The four figures for site/neuron.html, drawn from outputs/neuron_payload.json.

  neuron_fig1_span.png      every scale a drawing at true proportions must
                            hold at once, against what a figure can render
  neuron_fig2_pair.png      two real reconstructions: one with measured
                            thickness and almost no axon, one with a complete
                            axon and a single invented thickness
  neuron_fig3_tradeoff.png  reach against how coarse the recorded thickness
                            is, one point per sampled cell, coloured by method
  neuron_fig4_cascade.png   the five constraints, and what each one costs

Every colour, size and face comes from sitefig.py.

No figure here uses a z coordinate.  Figure 2 draws two projections through
swclib.load_xy(), which returns two columns, because the Allen file's z axis
is uncorrected slice geometry compressed by roughly a factor of two and the
archive ships no per-cell correction (see swclib and check 1 in
test_neuron.py).  Figure 2 also varies its line width only for the cell whose
radius column is a measurement; the other is drawn at one width because it
holds one value.

Each figure is audited for text that overlaps, runs off the canvas or falls
under the site's size floor, and for grid faults; figures 1 and 2 carry a
scale bar, which the shared audit cannot see, so they check their own.  The
build prints the count and it must be 0.

Run:  python3 fig_neuron.py
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
from matplotlib.collections import LineCollection   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import sitefig                                              # noqa: E402
from sitefig import (ACC, BG, DIM, FAINT, FS_2, INK, MOSS, NOTES, PLOT,  # noqa: E402
                     SLATE, fig_size, row_aspect)
from fig_floor import floor_problems                        # noqa: E402
import swclib                                               # noqa: E402

PAYLOAD = os.path.join(HERE, "outputs", "neuron_payload.json")
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


# The shared audit compares text against text and against the canvas. It does
# not see one drawn thing covering another (HANDOFF s8, trap 4), and figures 1
# and 2 both carry a scale bar, which is drawn rather than written. Rather
# than test for a collision after the fact, each panel reserves a strip that
# nothing else may enter, and this asserts the strip really is empty.
_STRIPS = []


def reserve_strip(ax, y_top, points, label):
    """Record that everything below y_top in `ax` belongs to the scale bar."""
    _STRIPS.append((ax, y_top, np.asarray(points, dtype=float), label))


def strip_problems():
    bad = []
    for ax, y_top, pts, label in _STRIPS:
        if len(pts) and (pts[:, 1] < y_top).any():
            n = int((pts[:, 1] < y_top).sum())
            bad.append("scale bar: %d drawn point(s) inside the reserved strip in %s"
                       % (n, label))
    return bad


def emit(fig, name):
    bad = audit(fig) + strip_problems()
    _STRIPS.clear()
    sitefig.save(fig, os.path.join(OUT, name), close=False)
    plt.close(fig)
    flag = "  LAYOUT: " + "; ".join(bad[:3]) if bad else ""
    print(f"  {name:26s} {len(bad)} layout problems{flag}")
    return len(bad)


def si(um):
    """A length, written the way the page writes it."""
    if um >= 1000:
        return "%g mm" % round(um / 1000.0, 1)
    if um >= 1:
        return "%g µm" % round(um, 1)
    return "%g µm" % round(um, 3)


# ------------------------------------------------------------------ fig 1 ---

def fig_span(P):
    """Every scale at once, against what a figure can actually render."""
    L, lu = P["ladder"], P["looked_up"]
    pair = P["pair"]
    al, ml = pair.get("allen"), pair.get("mouselight")

    marks = [
        (lu["spine_neck"]["value_um"], "a spine neck, by electron microscopy", MOSS),
        (L["thinnest_um"], "the thinnest axon, by electron microscopy", MOSS),
        (swclib.DIFFRACTION_UM, "what visible light can resolve", SLATE),
    ]
    if al and al.get("soma_diam_um"):
        marks.append((al["soma_diam_um"], "the soma of the cell in figure 2", ACC))
    if al:
        marks.append((al["reach_um"], "how far that cell's arbor reaches", ACC))
    if ml:
        marks.append((ml["reach_um"], "how far a whole-brain cell reaches", ACC))
        marks.append((ml["axon_um"], "the length of its axon, end to end", ACC))
    marks.sort(key=lambda m: m[0])

    n = len(marks)
    fig, ax = plt.subplots(figsize=fig_size(NOTES, row_aspect(n, row_px=30, header_px=118)))
    lo = min(m[0] for m in marks) / 3.0
    hi = max(m[0] for m in marks) * 3.0

    # what a figure can hold: three orders of magnitude, anchored at the top.
    # An assumption, and labelled as one on the page.
    band_hi = hi / 3.0
    band_lo = band_hi / 1000.0
    ax.axvspan(band_lo, band_hi, color=FAINT, alpha=.55, zorder=0, lw=0)

    ys = np.arange(n)[::-1]
    for (v, lab, col), y in zip(marks, ys):
        # No leader line: it has to pass under the value label to reach the
        # dot, and a plate to stop it striking through shows as a box against
        # the band. The log grid already carries the eye.
        ax.plot([v], [y], "o", ms=5.5, color=col, zorder=3)
        ax.annotate(" " + lab, (v, y), xytext=(7, 0), textcoords="offset points",
                    va="center", fontsize=FS_2, color=INK, zorder=4)
        ax.annotate(si(v), (v, y), xytext=(-7, 0), textcoords="offset points",
                    va="center", ha="right", fontsize=FS_2, color=DIM,
                    fontfamily="IBM Plex Mono", zorder=4)
    ax.set_xscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(-0.9, n - 0.3)
    ax.set_yticks([])
    ax.set_xlabel("micrometres, log scale")
    ax.grid(axis="x", alpha=.18, which="major")
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.annotate("about what one figure can hold, end to end",
                (band_lo * 1.25, -0.72), fontsize=FS_2, color=DIM, va="center")
    sitefig.panel(ax, "one cell spans %s orders of magnitude" % L["orders"])
    fig.tight_layout()
    sitefig.centre(fig)
    return emit(fig, "neuron_fig1_span.png")


# ------------------------------------------------------------------ fig 2 ---

def draw_cell(ax, path, vary_width, colour, base_lw=0.45):
    """One reconstruction, projected. Two columns in, never three."""
    xy = swclib.load_xy(path)                    # (N, 2): there is no z here
    idx, typ, xyz, rad, par = swclib.read_swc(path)
    pos = {int(i): k for k, i in enumerate(idx)}
    segs, widths = [], []
    for k in range(len(idx)):
        p = int(par[k])
        if p == -1 or p not in pos or int(typ[k]) == swclib.SOMA:
            continue
        j = pos[p]
        segs.append([xy[j], xy[k]])
        widths.append(2.0 * float(rad[k]))
    segs = np.asarray(segs, dtype=float)
    widths = np.asarray(widths, dtype=float)
    if vary_width:
        w = widths / max(np.median(widths), 1e-9)
        lw = np.clip(base_lw * w, 0.16, 2.4)
    else:
        # one value in the file, so one width on the page: varying it would
        # be drawing a number nobody measured
        lw = np.full(len(segs), base_lw)
    ax.add_collection(LineCollection(segs, linewidths=lw, colors=colour,
                                     capstyle="round", zorder=2))
    som = xyz[typ == swclib.SOMA][:, :2]
    if len(som):
        r = float(rad[typ == swclib.SOMA].mean())
        ax.add_patch(plt.Circle(som.mean(axis=0), r, color=colour, zorder=3, lw=0))
    return segs.reshape(-1, 2)


def fig_pair(P):
    """The two files, each at its own scale, each saying what it lacks."""
    pair = P["pair"]
    order = [("allen", ACC), ("mouselight", MOSS)]
    fig, axes = plt.subplots(1, 2, figsize=fig_size(NOTES, 1.28))
    for ax, (src, col) in zip(axes, order):
        d = pair.get(src)
        if not d:
            continue
        pts = draw_cell(ax, os.path.join(HERE, d["file"]), d["diam_measured"], col)
        ax.set_aspect("equal")
        # Equal aspect shrinks each box to fit its own data, so two panels of
        # different proportions end up different heights and their labels sit
        # at different heights with them. Anchor both boxes to the top of the
        # space they were given and the labels line up.
        ax.set_anchor("N")
        ax.axis("off")
        x0, x1 = pts[:, 0].min(), pts[:, 0].max()
        y0, y1 = pts[:, 1].min(), pts[:, 1].max()
        padx, pady = (x1 - x0) * .10 + 1, (y1 - y0) * .10 + 1
        # a strip below the drawing that belongs to the scale bar alone
        strip = (y1 - y0) * .17 + 1
        ax.set_xlim(x0 - padx, x1 + padx)
        ax.set_ylim(y0 - pady - strip, y1 + pady)
        reserve_strip(ax, y0 - pady, pts, src)

        span = x1 - x0
        step = 10.0 ** np.floor(np.log10(span * .45))
        bar = step if span * .45 / step < 2.2 else step * 2
        bx = x0 - padx * .1
        by = y0 - pady - strip * .55
        ax.plot([bx, bx + bar], [by, by], color=INK, lw=1.4, solid_capstyle="butt", zorder=5)
        ax.annotate(si(bar), ((bx + bx + bar) / 2, by), xytext=(0, 5),
                    textcoords="offset points", ha="center", va="bottom",
                    fontsize=FS_2, color=INK, fontfamily="IBM Plex Mono", zorder=5)
        if d["diam_measured"]:
            note = "%s widths" % f'{d["n_distinct_diam"]:,}'
        else:
            note = "one width"
        sitefig.panel(ax, "axon %s, %s" % (si(d["axon_um"]), note))
    # An equal-aspect drawing takes all the height it is given, and the panel
    # label sits above the axes, so these margins are set rather than fitted:
    # tight_layout let the taller cell fill the canvas and pushed its own label
    # off the top edge.
    fig.subplots_adjust(left=.015, right=.985, top=.88, bottom=.02, wspace=.06)
    sitefig.centre(fig)
    return emit(fig, "neuron_fig2_pair.png")


# ------------------------------------------------------------------ fig 3 ---

def fig_tradeoff(P):
    """Reach against how coarse the recorded thickness is."""
    S = P["scatter"]
    G = P["gradient"]
    fig, ax = plt.subplots(figsize=fig_size(NOTES, PLOT))
    for wb, col, lab in ((False, ACC, "slice and culture"),
                         (True, MOSS, "whole brain, in vivo")):
        g = [s for s in S if s["whole_brain"] == wb]
        if not g:
            continue
        ax.scatter([s["reach_um"] for s in g], [s["modal_share"] for s in g],
                   s=13, alpha=.55, c=col, linewidths=0,
                   label="%s, n = %d" % (lab, len(g)))
    ax.set_xscale("log")
    xs = [s["reach_um"] for s in S]
    ax.set_xlim(min(xs) * .7, max(xs) * 1.5)
    ax.set_ylim(-0.04, 1.06)
    ax.set_yticks([0, .25, .5, .75, 1])
    ax.set_yticklabels(["0", "25", "50", "75", "100%"])
    ax.set_xlabel("how far the arbor reaches from the soma (micrometres, log scale)")
    ax.set_ylabel("share of the drawn length at a single width")
    ax.grid(alpha=.18, which="major")
    ax.set_axisbelow(True)
    ax.legend(fontsize=FS_2, frameon=False, loc="lower right")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    sitefig.panel(ax, "%s, n = %s" % (G["verdict"], f'{G["n_cells"]:,}'))
    fig.tight_layout()
    sitefig.centre(fig)
    return emit(fig, "neuron_fig3_tradeoff.png")


# ------------------------------------------------------------------ fig 4 ---

def fig_cascade(P):
    """What each constraint costs, applied in the order the page states."""
    c = P["cascade"]
    labels = ["every reconstruction"] + [s["label"] for s in c["steps"]]
    counts = [c["n_total"]] + [s["n"] for s in c["steps"]]
    n = len(counts)
    fig, ax = plt.subplots(figsize=fig_size(NOTES, row_aspect(n, row_px=34, header_px=104)))
    ys = np.arange(n)[::-1]
    cols = [SLATE] + [ACC] * (n - 2) + [MOSS]
    ax.barh(ys, counts, height=.55, color=cols, zorder=2)
    for y, v in zip(ys, counts):
        ax.annotate(" " + f"{v:,}", (v, y), xytext=(5, 0), textcoords="offset points",
                    va="center", fontsize=FS_2, color=INK, fontfamily="IBM Plex Mono")
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=FS_2)
    ax.set_xscale("log")
    ax.set_xlim(50, max(counts) * 6)
    ax.set_xlabel("reconstructions (log scale)")
    ax.grid(axis="x", alpha=.18, which="major")
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    sitefig.panel(ax, "each line adds one requirement to the line above it")
    fig.tight_layout()
    sitefig.centre(fig)
    return emit(fig, "neuron_fig4_cascade.png")


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    sitefig.style()
    bad = fig_span(P) + fig_pair(P) + fig_tradeoff(P) + fig_cascade(P)
    print(f"  {bad} layout problem(s) in total")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
