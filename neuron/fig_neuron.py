"""
The six figures for site/neuron.html, drawn from outputs/neuron_payload.json.

  neuron_fig1_span.png      every scale a drawing at true proportions must
                            hold at once, against what a figure can render
  neuron_fig2_pair.png      two real reconstructions at one scale - one with
                            measured thickness and almost no axon, one with a
                            complete axon and a single invented thickness -
                            and the small one's box opened at its own scale
  neuron_fig3_tradeoff.png  reach against how coarse the recorded thickness
                            is, one point per sampled cell, coloured by method
  neuron_fig4_cascade.png   the five constraints, and what each one costs
  neuron_fig5_ladder.png    one cell from the complete set at three scales,
                            each window boxed in the one before, at the
                            file's own widths throughout
  neuron_fig6_orders.png    what each constraint removes at each position,
                            over all 120 orders: the order-dependence that
                            the reorderable app used to show one order at
                            a time

Every colour, size and face comes from sitefig.py.  The panel boxes of
figures 2 and 5, and what a pixel means in them, come from build_neuron.py,
which computes the captions' "under one pixel" shares from the same boxes.

No figure here uses a z coordinate.  Figures 2 and 5 draw projections
through swclib.load_xy(), which returns two columns, because a slice file's
z axis is uncorrected slice geometry compressed by roughly a factor of two
and the archive ships no per-cell correction (see swclib and check 1 in
test_neuron.py).  Both draw a width only for a cell whose radius column is
a measurement, and then in data units, so it is the file's number at the
panel's scale; a cell holding one value is drawn as a hairline because
varying it would draw a number nobody measured.

Each figure is audited for text that overlaps, runs off the canvas or falls
under the site's size floor, and for grid faults; figures 1, 2 and 5 carry
a scale bar, which the shared audit cannot see, so they check their own.
The build prints the count and it must be 0.

Run:  python3 fig_neuron.py
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
from matplotlib.collections import (LineCollection, PolyCollection,    # noqa: E402
                                    EllipseCollection)
from matplotlib.patches import Rectangle                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import sitefig                                              # noqa: E402
from sitefig import (ACC, BG, DIM, FAINT, FS_2, INK, MOSS, NOTES, PLOT,  # noqa: E402
                     SLATE, fig_size, row_aspect)
from fig_floor import floor_problems                        # noqa: E402
import swclib                                               # noqa: E402
from build_neuron import STRIP_PX, HAIRLINE_PT, WINDOW_PAD  # noqa: E402

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
# not see one drawn thing covering another (HANDOFF s8, trap 4), and figures
# 1, 2 and 5 carry a scale bar, which is drawn rather than written. Rather
# than test for a collision after the fact, each panel reserves a strip that
# nothing else may enter, and this asserts the strip really is empty: either
# no drawn point lies in it, or, where a panel clips its drawing to a window,
# the window ends at or above it.
_STRIPS = []
_CLIPS = []


def reserve_strip(ax, y_top, points, label):
    """Record that everything below y_top in `ax` belongs to the scale bar."""
    _STRIPS.append((ax, y_top, np.asarray(points, dtype=float), label))


def reserve_clip(ax, clip_bottom, y_top, label):
    """Record that the drawing is clipped at clip_bottom, which must not be
    below the strip's top."""
    _CLIPS.append((ax, float(clip_bottom), float(y_top), label))


def strip_problems():
    bad = []
    for ax, y_top, pts, label in _STRIPS:
        if len(pts) and (pts[:, 1] < y_top).any():
            n = int((pts[:, 1] < y_top).sum())
            bad.append("scale bar: %d drawn point(s) inside the reserved strip in %s"
                       % (n, label))
    for ax, clip_bottom, y_top, label in _CLIPS:
        if clip_bottom < y_top - 1e-9:
            bad.append("scale bar: the clip window enters the reserved strip in %s" % label)
    return bad


def emit(fig, name):
    bad = audit(fig) + strip_problems()
    _STRIPS.clear()
    _CLIPS.clear()
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


# ------------------------------------------------------------ the renderer ---
# Figures 2 and 5 draw reconstructions, and they share one renderer so that a
# width means the same thing in both: the file's number, in data units, at
# whatever scale the panel happens to be.  The panel boxes come from
# build_neuron.py, where the "under one pixel" shares in the captions are
# computed from the same boxes.

HAIR_ALPHA = 0.55


def panel_axes(fig, box_css, fig_css):
    """An axes placed from a CSS-pixel box measured from the top-left."""
    x, y, w, h = box_css
    W, H = fig_css
    return fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])


def frame(ax, centre, upp, box_css):
    """Data limits such that one CSS pixel is `upp` micrometres, the drawing
    centred on `centre` in the top of the box and STRIP_PX kept below it for
    the scale bar.  Returns the strip's top edge in data units."""
    _, _, w, h = box_css
    draw_h = h - STRIP_PX
    cx, cy = float(centre[0]), float(centre[1])
    ax.set_xlim(cx - w * upp / 2, cx + w * upp / 2)
    ax.set_ylim(cy - draw_h * upp / 2 - STRIP_PX * upp, cy + draw_h * upp / 2)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    return cy - draw_h * upp / 2


def _quads(p, c, d):
    """One rectangle per segment, in data units, the segment's own diameter."""
    v = c - p
    n = np.linalg.norm(v, axis=1)
    n[n == 0] = 1.0
    perp = np.stack([-v[:, 1], v[:, 0]], axis=1) / n[:, None] * (d / 2.0)[:, None]
    return np.stack([p + perp, c + perp, c - perp, p - perp], axis=1)


def draw_true(ax, path, widths_measured, offset=(0.0, 0.0), clip=None):
    """One reconstruction, projected, at the file's own widths.

    Two columns in, never three.  Every segment is a hairline - the shape,
    HAIRLINE_PT wide, in a fainter tint - with, on top of it and only where
    the file's radius column is a measurement, a polygon in data units as
    wide as the segment's recorded diameter.  So a width is the file's
    number at whatever scale the panel is drawn at, and disappears under
    the hairline when it is thinner than a pixel.  A file holding one width
    gets the hairline alone: varying it would draw a number nobody
    measured.  Dendrite in ACC, axon in MOSS, the soma a disc of its radius.
    Returns the drawn neurite points, for the scale-bar audit.
    """
    xy = swclib.load_xy(path) + np.asarray(offset, dtype=float)   # (N, 2): there is no z here
    idx, typ, _, rad, par = swclib.read_swc(path)
    pos = {int(i): k for k, i in enumerate(idx)}
    P, C, D, T = [], [], [], []
    for k in range(len(idx)):
        p = int(par[k])
        if p == -1 or p not in pos or int(typ[k]) == swclib.SOMA:
            continue
        j = pos[p]
        P.append(xy[j]); C.append(xy[k]); D.append(2.0 * float(rad[k])); T.append(int(typ[k]))
    P, C = np.asarray(P, dtype=float), np.asarray(C, dtype=float)
    D, T = np.asarray(D, dtype=float), np.asarray(T)
    arts = []
    for is_axon, col in ((False, ACC), (True, MOSS)):
        sel = (T == swclib.AXON) == is_axon
        if not sel.any():
            continue
        hair = LineCollection(np.stack([P[sel], C[sel]], axis=1), linewidths=HAIRLINE_PT,
                              colors=col, alpha=HAIR_ALPHA, capstyle="round", zorder=2)
        ax.add_collection(hair)
        arts.append(hair)
        if widths_measured:
            poly = PolyCollection(_quads(P[sel], C[sel], D[sel]), facecolors=col,
                                  edgecolors="none", zorder=3)
            ax.add_collection(poly)
            arts.append(poly)
            # a disc at every joint, so a bend in a thick branch has no notch
            dots = EllipseCollection(D[sel], D[sel], np.zeros(int(sel.sum())), units="xy",
                                     offsets=C[sel], offset_transform=ax.transData,
                                     facecolors=col, edgecolors="none", zorder=3)
            ax.add_collection(dots)
            arts.append(dots)
    som = xy[typ == swclib.SOMA]
    if len(som):
        circ = plt.Circle(som.mean(axis=0), float(rad[typ == swclib.SOMA].mean()),
                          color=ACC, zorder=4, lw=0)
        ax.add_patch(circ)
        arts.append(circ)
    if clip is not None:
        for a in arts:
            a.set_clip_path(clip)
    return np.vstack([P, C]) if len(P) else xy


def nice(v):
    """The largest of 1, 2, 5 x 10^n not above v."""
    step = 10.0 ** np.floor(np.log10(v))
    for m in (5, 2, 1):
        if m * step <= v:
            return m * step
    return step


def scale_bar(ax, strip_top, upp, box_css, x_frac=0.02):
    """A bar in the reserved strip, its length the largest round number
    under 35% of the panel's width, labelled above it."""
    _, _, w, _ = box_css
    x0 = ax.get_xlim()[0] + w * upp * x_frac
    bar = nice(0.35 * w * upp)
    by = strip_top - STRIP_PX * upp * 0.72
    ax.plot([x0, x0 + bar], [by, by], color=INK, lw=1.4, solid_capstyle="butt",
            zorder=5, clip_on=False)
    ax.annotate(si(bar), (x0 + bar / 2, by), xytext=(0, 4), textcoords="offset points",
                ha="center", va="bottom", fontsize=FS_2, color=INK,
                fontfamily="IBM Plex Mono", zorder=5)
    return bar


def window_box(ax, centre, win, label):
    """The child panel's window, drawn as a box in its parent, with its letter."""
    cx, cy = float(centre[0]), float(centre[1])
    r = Rectangle((cx - win / 2, cy - win / 2), win, win, fill=False, ec=INK, lw=0.8, zorder=6)
    ax.add_patch(r)
    ax.annotate(label, (cx + win / 2, cy + win / 2), xytext=(3, 1), textcoords="offset points",
                ha="left", va="bottom", fontsize=FS_2, color=INK, fontfamily="IBM Plex Mono",
                zorder=6)
    return r


# ------------------------------------------------------------------ fig 2 ---

def fig_pair(P):
    """The two files at one scale, and the slice cell's box opened."""
    pair, G, L = P["pair"], P["pair_geometry"], P["layout"]
    css = L["pair_css"]
    al, ml = pair["allen"], pair["mouselight"]
    fig = plt.figure(figsize=fig_size(NOTES, css["fig"][0] / css["fig"][1]))

    # the shared frame: the whole-brain cell where the file puts it, the
    # slice cell translated to sit beside it, vertically centred on it
    ax = panel_axes(fig, css["shared"], css["fig"])
    ml_xy = swclib.load_xy(os.path.join(HERE, ml["file"]))
    al_xy = swclib.load_xy(os.path.join(HERE, al["file"]))
    ml_lo, ml_hi = ml_xy.min(axis=0), ml_xy.max(axis=0)
    al_lo, al_hi = al_xy.min(axis=0), al_xy.max(axis=0)
    shift = np.array([ml_hi[0] + G["gap_um"] - al_lo[0],
                      (ml_lo[1] + ml_hi[1]) / 2 - (al_lo[1] + al_hi[1]) / 2])
    lo = np.minimum(ml_lo, al_lo + shift)
    hi = np.maximum(ml_hi, al_hi + shift)
    upp = G["shared_um_per_px"]
    strip_top = frame(ax, (lo + hi) / 2, upp, css["shared"])
    pts = draw_true(ax, os.path.join(HERE, ml["file"]), ml["diam_measured"])
    pts2 = draw_true(ax, os.path.join(HERE, al["file"]), al["diam_measured"], offset=shift)
    pts = np.vstack([pts, pts2])
    reserve_strip(ax, strip_top, pts, "shared")
    scale_bar(ax, strip_top, upp, css["shared"])
    # the slice cell's window, as a box
    span = al_hi - al_lo
    win = float(span.max() * (1 + 2 * WINDOW_PAD))
    centre = (al_lo + al_hi) / 2 + shift
    window_box(ax, centre, win, "the box")
    sitefig.panel(ax, "both cells at one scale, %s per pixel" % si(upp))

    # the box, opened: the slice cell at its own scale, at its recorded widths
    ax2 = panel_axes(fig, css["own"], css["fig"])
    upp2 = G["own_um_per_px"]
    strip2 = frame(ax2, (al_lo + al_hi) / 2, upp2, css["own"])
    pts3 = draw_true(ax2, os.path.join(HERE, al["file"]), al["diam_measured"])
    reserve_strip(ax2, strip2, pts3, "own")
    scale_bar(ax2, strip2, upp2, css["own"])
    x0, x1 = ax2.get_xlim()
    ax2.add_patch(Rectangle((x0, strip2), x1 - x0, ax2.get_ylim()[1] - strip2, fill=False,
                            ec=INK, lw=0.8, zorder=6, clip_on=False))
    sitefig.panel(ax2, "the box, opened")
    sitefig.centre(fig)
    return emit(fig, "neuron_fig2_pair.png")


# ------------------------------------------------------------------ fig 5 ---

def fig_ladder(P):
    """One of the complete set at three scales, each window boxed in the
    one before, at the file's own widths throughout."""
    d, L = P["drawn"], P["layout"]
    css = L["ladder_css"]
    path = os.path.join(HERE, d["file"])
    W = d["windows"]
    fig = plt.figure(figsize=fig_size(NOTES, css["fig"][0] / css["fig"][1]))
    axes = {}
    for key in ("A", "B", "C"):
        w = W[key]
        ax = panel_axes(fig, css[key], css["fig"])
        strip_top = frame(ax, w["centre_um"], w["um_per_px"], css[key])
        # everything outside the window is clipped, so nothing can reach the
        # strip; the audit checks the window really ends above it
        x0, x1 = ax.get_xlim()
        y1 = ax.get_ylim()[1]
        clip = Rectangle((x0, strip_top), x1 - x0, y1 - strip_top, transform=ax.transData)
        pts = draw_true(ax, path, d["diam_measured"], clip=clip)
        if key == "A":
            reserve_strip(ax, strip_top, pts, "ladder A")
        else:
            reserve_clip(ax, strip_top, strip_top, "ladder " + key)
        scale_bar(ax, strip_top, w["um_per_px"], css[key])
        axes[key] = (ax, strip_top)
    # the boxes: B's window in A, C's in B
    for parent, child in (("A", "B"), ("B", "C")):
        window_box(axes[parent][0], W[child]["centre_um"], W[child]["window_um"][0], child)
    # the fourth order: an axon of the thinnest calibre in the literature,
    # drawn at its true width in C's strip beside the scale bar
    axC, stripC = axes["C"]
    upp = W["C"]["um_per_px"]
    _, _, wpx, _ = css["C"]
    em = P["ladder"]["thinnest_um"]
    x0 = axC.get_xlim()[0] + wpx * upp * 0.50
    ln = nice(0.30 * wpx * upp)
    by = stripC - STRIP_PX * upp * 0.72
    axC.add_patch(Rectangle((x0, by - em / 2), ln, em, color=DIM, lw=0, zorder=5, clip_on=False))
    axC.annotate("an axon %s wide, by electron microscopy" % si(em), (x0 + ln / 2, by),
                 xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                 fontsize=FS_2, color=DIM, zorder=5)
    sitefig.panel(axes["A"][0], "A  the whole cell, %s end to end" % si(d["extent_xy_um"]))
    sitefig.panel(axes["B"][0], "B  the box in A, %s across" % si(W["B"]["window_um"][0]))
    sitefig.panel(axes["C"][0], "C  the box in B, %s across" % si(W["C"]["window_um"][0]))
    sitefig.centre(fig)
    return emit(fig, "neuron_fig5_ladder.png")


# ------------------------------------------------------------------ fig 3 ---

def fig_tradeoff(P):
    """Reach against how coarse the recorded thickness is."""
    S = P["scatter"]
    G = P["gradient"]
    fig, ax = plt.subplots(figsize=fig_size(NOTES, PLOT))
    # Not ACC and MOSS here, deliberately. Figures 2 and 5 draw anatomy and
    # give ACC to dendrite and MOSS to axon; this figure sits between them
    # and colours *method*. On 2026-09-06 it used the same pair, which agreed
    # by accident in figure 2 (the slice cell is nearly all dendrite, the
    # whole-brain cell nearly all axon) and contradicted figure 5, where one
    # cell is both. So method gets a pair with no hue in it: INK for whole
    # brain and SLATE for slice and culture. Both clear the deslop palette
    # floor for a graphic on the figure ground (3.0:1 - INK 14.5, SLATE 3.1)
    # and against each other (4.65, which no two of the site's dark hues
    # manage), and lightness survives a colour-blind reader. SLATE is drawn
    # opaque because alpha would take it under the floor; INK goes on top.
    # Do not "restore" ACC/MOSS here (HANDOFF s8, trap 15).
    for wb, col, alpha, lab in ((False, SLATE, 1.0, "slice and culture"),
                                (True, INK, .8, "whole brain, in vivo")):
        g = [s for s in S if s["whole_brain"] == wb]
        if not g:
            continue
        ax.scatter([s["reach_um"] for s in g], [s["modal_share"] for s in g],
                   s=13, alpha=alpha, c=col, linewidths=0,
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


# ------------------------------------------------------------------ fig 6 ---

def fig_orders(P):
    """What each constraint removes, at every position, over all 120 orders."""
    oc = P["cascade"]["order_costs"]
    rows = oc["constraints"]
    n = len(rows)
    fig, ax = plt.subplots(figsize=fig_size(NOTES, row_aspect(n, row_px=44, header_px=118)))
    ys = np.arange(n)[::-1]
    # INK and SLATE, not ACC and MOSS: on this page those two are dendrite
    # and axon (figures 2 and 5), and figure 3 already gave up the pair for
    # the same reason. Nothing here is anatomy.
    for y, o in zip(ys, rows):
        ax.plot([100 * o["min"], 100 * o["max"]], [y, y], color=FAINT, lw=9,
                solid_capstyle="butt", zorder=1)
        ax.plot([100 * p["mean"] for p in o["by_position"]], [y] * n, "|", ms=9,
                color=SLATE, mew=1.2, zorder=2)
        ax.plot([100 * o["first"]], [y], "o", ms=7, color=INK, zorder=3)
        ax.plot([100 * o["last"]], [y], "o", ms=7, mfc=BG, mec=INK, mew=1.4, zorder=3)
    # a legend built by hand, so the band and the ticks appear in it too
    from matplotlib.lines import Line2D
    handles = [
        Line2D([], [], color=FAINT, lw=9, solid_capstyle="butt",
               label="every one of %d orders" % oc["n_orders"]),
        Line2D([], [], color=SLATE, marker="|", ms=9, mew=1.2, lw=0,
               label="mean at each position, first to fifth"),
        Line2D([], [], color=INK, marker="o", ms=7, lw=0, label="applied first"),
        Line2D([], [], mfc=BG, mec=INK, marker="o", ms=7, mew=1.4, lw=0, label="applied last"),
    ]
    ax.legend(handles=handles, fontsize=FS_2, frameon=False, loc="lower left")
    ax.set_yticks(ys)
    ax.set_yticklabels([o["label"] for o in rows], fontsize=FS_2)
    ax.set_xlim(-2, 102)
    ax.set_ylim(-0.7, n - 0.3)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0", "25", "50", "75", "100%"])
    ax.set_xlabel("share of what was left that the requirement removes")
    ax.grid(axis="x", alpha=.18, which="major")
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    sitefig.panel(ax, "cost by position, all %d orders" % oc["n_orders"])
    # tight_layout leaves the long tick labels to the left of the axes and
    # then centre() moves the grid by the labels' width, which pushes them
    # off the left edge; the margins are set instead.
    fig.subplots_adjust(left=.40, right=.97, top=.86, bottom=.17)
    sitefig.centre(fig)
    return emit(fig, "neuron_fig6_orders.png")


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    sitefig.style()
    bad = (fig_span(P) + fig_pair(P) + fig_tradeoff(P) + fig_cascade(P) + fig_ladder(P)
           + fig_orders(P))
    print(f"  {bad} layout problem(s) in total")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
