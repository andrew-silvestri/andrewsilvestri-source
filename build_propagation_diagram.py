"""One node, one step: the propagation arithmetic of model.html section 4.4,
drawn as a worked example at a single node.

The throughlines sheet shows a change travelling through the whole system;
this shows what happens at one node on one step, so the list in the prose
has a picture to point at. It is worked with made-up numbers rather than
symbols alone, because a reader can check a number and cannot check a
letter: three drivers with effects and weights, the node's inertia, no
applied change, and the value at each stage. Nothing here is asserted as
real - the footnote says so - and the real weights and inertias are the
tables in section 5.

What is drawn is what atlas-app.js does (the engine of record):

    inflow = sum(w * s) / sum(|w|)                 the weighted mean
    target = tanh(change + (1 - 0.6 * inertia) * inflow)
    s_new  = s + LAM * (target - s)                most of the way there

Note the 0.6: the prose says "(1 - inertia)"; the code damps by
(1 - 0.6 * inertia). The figure follows the code (ATLAS_CLAIMS_TODO item 3
has the prose).

Layout is checked rather than eyeballed: audit() walks every Text on the
canvas and reports anything that overlaps or falls outside the figure.

Run:  python3 build_propagation_diagram.py
"""
import math
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402

import sitefig                                               # noqa: E402
from sitefig import ACC, COOL, MOSS, INK, DIM, RULE, FAINT, BG, CARD_FILL, FS_2, FS_1, FS0, MONO, PROSE, fig_size  # noqa: E402
from fig_floor import floor_problems                         # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site", "assets", "model_propagation_step.png")
APP = os.path.join(HERE, "site", "assets", "atlas-app.js")

# ---- the example ----------------------------------------------------------
DRIVERS = [("A", 0.60, 0.5, ACC), ("B", -0.20, 0.3, COOL), ("C", 0.40, 0.2, MOSS)]
INERTIA = 0.40
CHANGE = 0.0
S_OLD = 0.0


def lam_from_app():
    """The step fraction the engine actually uses, read from the source so
    the figure cannot drift from it."""
    s = open(APP, encoding="utf-8").read()
    m = re.search(r"\blam\s*=\s*([0-9.]+)", s)
    if not m:
        raise SystemExit("atlas-app.js: could not find the step fraction (lam = ...)")
    return float(m.group(1))


def audit(fig):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    items = [t for ax in fig.axes for t in ax.texts if t.get_text().strip()]
    items += [t for t in fig.texts if t.get_text().strip()]
    W, H = fig.canvas.get_width_height()
    boxes, problems = [], []
    for t in items:
        bb = t.get_window_extent(renderer=r)
        boxes.append((t, bb))
        if bb.x0 < -2 or bb.y0 < -2 or bb.x1 > W + 2 or bb.y1 > H + 2:
            problems.append(f"off canvas: {t.get_text()[:36]!r}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][1], boxes[j][1]
            if a.x1 > b.x0 and b.x1 > a.x0 and a.y1 > b.y0 and b.y1 > a.y0:
                problems.append(f"overlap: {boxes[i][0].get_text()[:22]!r} / {boxes[j][0].get_text()[:22]!r}")
    problems += floor_problems(fig, [(t, False) for t in items])
    for t, (x0, y0, x1, y1) in BOXED:
        bb = t.get_window_extent(renderer=r).transformed(fig.axes[0].transData.inverted())
        if bb.x0 < x0 + 0.06 or bb.x1 > x1 - 0.06 or bb.y0 < y0 + 0.04 or bb.y1 > y1 - 0.04:
            problems.append(f"spills its box: {t.get_text()[:30]!r}")
    return problems


def arrow(ax, p0, p1, color=RULE, lw=1.2, dashed=False):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", color=color, linewidth=lw,
                                 mutation_scale=11, shrinkA=0, shrinkB=0, zorder=2,
                                 linestyle=(0, (3, 3)) if dashed else "solid"))


def stage(ax, cx, cy, w, h, n, title, formula, value):
    """A stage box: number above, the operation in the site face, the
    arithmetic in mono, the running value in mono under it."""
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, linewidth=1.0,
                           edgecolor=RULE, facecolor=CARD_FILL, zorder=3))
    ax.text(cx - w / 2, cy + h / 2 + 0.12, f"{n}", color=DIM, fontsize=FS_2,
            fontfamily=MONO, ha="left", va="bottom", zorder=4)
    inside = [
        ax.text(cx, cy + 0.40, title, color=INK, fontsize=FS_1, ha="center", va="center",
                linespacing=1.25, zorder=4),
        ax.text(cx, cy - 0.16, formula, color=DIM, fontsize=FS_2, fontfamily=MONO,
                ha="center", va="center", zorder=4),
        ax.text(cx, cy - 0.48, value, color=ACC, fontsize=FS_2, fontfamily=MONO,
                ha="center", va="center", zorder=4)]
    # what a box holds must fit in it: the audit checks text against text,
    # and the first render of this sheet had three titles running through
    # their boxes' edges and into each other without a single overlap of
    # text on text (2026-09-04)
    for t in inside:
        BOXED.append((t, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)))


BOXED = []


def main():
    sitefig.style()
    lam = lam_from_app()
    # the arithmetic, once, so every number on the sheet comes from one place
    inflow = sum(w * s for _, s, w, _ in DRIVERS) / sum(abs(w) for _, _, w, _ in DRIVERS)
    damped = (1 - 0.6 * INERTIA) * inflow
    target = math.tanh(CHANGE + damped)
    s_new = S_OLD + lam * (target - S_OLD)

    fig = plt.figure(figsize=fig_size(PROSE, 2.7))
    W, H = fig.get_size_inches()
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    cy = H * 0.56

    # ---- drivers: three circles, each with its effect and its weight -------
    dx = 1.45
    ys = [cy + 1.25, cy, cy - 1.25]
    bx1, bw, bh = 4.75, 2.2, 1.55
    for (name, s, w, col), y in zip(DRIVERS, ys):
        ax.add_patch(Circle((dx, y), 0.30, facecolor=col, edgecolor="none", zorder=3))
        ax.text(dx, y, name, color=BG, fontsize=FS_1, ha="center", va="center", fontweight="bold", zorder=4)
        ax.text(dx - 0.42, y, f"s = {s:+.2f}", color=DIM, fontsize=FS_2, fontfamily=MONO,
                ha="right", va="center", zorder=4)
        arrow(ax, (dx + 0.34, y), (bx1 - bw / 2 - 0.05, cy + (y - cy) * 0.30))
        ax.text((dx + 0.34 + bx1 - bw / 2) / 2 - 0.1, (y + cy + (y - cy) * 0.30) / 2 + (0.16 if y != cy else 0.14),
                f"w = {w:.1f}", color=DIM, fontsize=FS_2, fontfamily=MONO, ha="center", va="bottom", zorder=4)
    ax.text(dx, cy - 1.25 - 0.55, "the node's drivers", color=DIM, fontsize=FS_2,
            ha="center", va="top", zorder=4)

    # ---- the four stages ------------------------------------------------------
    gap = 0.50
    xs = [bx1 + i * (bw + gap) for i in range(4)]
    stage(ax, xs[0], cy, bw, bh, 1, "weighted mean\nof the drivers", "sum(w·s) ÷ sum|w|", f"= {inflow:+.3f}")
    stage(ax, xs[1], cy, bw, bh, 2, "damped by the\nnode's inertia", "× (1 − 0.6·inertia)", f"= {damped:+.3f}")
    stage(ax, xs[2], cy, bw, bh, 3, "the change added,\nsquashed by tanh", "tanh(change + ·)", f"= {target:+.3f}")
    stage(ax, xs[3], cy, bw, bh, 4, "most of the\nway there", f"s + {lam:.2f}(target − s)", f"= {s_new:+.3f}")
    for a, b in zip(xs, xs[1:]):
        arrow(ax, (a + bw / 2, cy), (b - bw / 2 - 0.05, cy))
    # inertia and the previous effect, as small facts under their stages
    ax.text(xs[1], cy - bh / 2 - 0.14, f"inertia {INERTIA:.2f}", color=DIM, fontsize=FS_2,
            fontfamily=MONO, ha="center", va="top", zorder=4)
    ax.text(xs[3], cy - bh / 2 - 0.14, f"previous effect s = {S_OLD:+.2f}", color=DIM, fontsize=FS_2,
            fontfamily=MONO, ha="center", va="top", zorder=4)
    # the applied change, from above stage 3
    arrow(ax, (xs[2], cy + bh / 2 + 1.05), (xs[2], cy + bh / 2 + 0.05), color=DIM, dashed=True)
    ax.text(xs[2], cy + bh / 2 + 1.15, f"applied change, if any (here {CHANGE:.0f})", color=DIM,
            fontsize=FS_2, ha="center", va="bottom", zorder=4)

    # ---- the node, after the step ---------------------------------------------
    nx = xs[3] + bw / 2 + 1.0
    arrow(ax, (xs[3] + bw / 2, cy), (nx - 0.50, cy))
    ax.add_patch(Circle((nx, cy), 0.46, facecolor=ACC, edgecolor="none", zorder=3))
    ax.text(nx, cy, f"{s_new:+.2f}", color=BG, fontsize=FS_1, ha="center", va="center",
            fontweight="bold", fontfamily=MONO, zorder=4)
    ax.text(nx, cy - 0.62, "the node's\nnew effect", color=DIM, fontsize=FS_2,
            ha="center", va="top", zorder=4)

    # ---- footnote ---------------------------------------------------------------
    ax.text(0.18, 0.22,
            "A worked example with made-up numbers: three drivers, weights 0.5, 0.3 and 0.2, inertia 0.40, no applied change. "
            "The arithmetic is atlas-app.js's;\nthe real weights and inertias are the tables in section 5. "
            "The step repeats until no node moves more than 0.00001, and gives up at sixty.",
            color=DIM, fontsize=FS_2, fontfamily=MONO, ha="left", va="bottom", linespacing=1.4, zorder=4)

    problems = audit(fig)
    sitefig.save(fig, OUT, close=False)
    plt.close(fig)
    print(f"  wrote {os.path.basename(OUT)}   lam={lam}  inflow={inflow:+.3f} damped={damped:+.3f} target={target:+.3f} new={s_new:+.3f}")
    print(f"  {len(problems)} layout problem(s)" + ("" if not problems else ":"))
    for p in problems[:12]:
        print("     " + p)
    return len(problems)


if __name__ == "__main__":
    main()
