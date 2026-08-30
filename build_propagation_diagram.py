"""
One clean diagram of the propagation step described in model.html sec4.4 -
zoomed in on a single node, rather than a network. The throughlines figure
already shows the step-by-step route through the whole system; this shows
what happens at one node on one step, so the equation in the prose has a
picture to point at.

Symbolic, not data-driven: the drivers, weights and node are generic (A, B,
C; w1, w2, w3), because this illustrates the shape of the calculation, not a
measured instance of it. No number here is asserted as real; the real
numbers for link weights and inertia are the tables already on model.html.

Layout is checked rather than eyeballed: audit() (same routine as
build_throughlines.py) walks every Text on the canvas and reports anything
that overlaps or falls outside the figure.

Run:  python3 build_propagation_diagram.py
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site", "assets", "model_propagation_step.png")

BG, INK, DIM = "#0a0d18", "#e3e6f2", "#8b93b0"
RULE = "#232a45"
DRIVER_COL = ["#8b7ff2", "#5aa8d8", "#4f9d84"]
NODE_COL = "#8b7ff2"


def audit(fig):
    """Same routine as build_throughlines.py: walk every Text actually drawn
    and report overlaps or anything off the canvas."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    items, problems = [], []
    for ax in fig.axes:
        for tx in ax.texts:
            if tx.get_text().strip():
                items.append(tx)
        if ax.title.get_text().strip():
            items.append(ax.title)
    for tx in fig.texts:
        if tx.get_text().strip():
            items.append(tx)
    boxes = []
    W, H = fig.canvas.get_width_height()
    for tx in items:
        bb = tx.get_window_extent(renderer=r)
        boxes.append((tx, bb))
        if bb.x0 < -2 or bb.y0 < -2 or bb.x1 > W + 2 or bb.y1 > H + 2:
            problems.append(f"off canvas: {tx.get_text()[:36]!r}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][1], boxes[j][1]
            if a.x1 > b.x0 and b.x1 > a.x0 and a.y1 > b.y0 and b.y1 > a.y0:
                problems.append(
                    f"overlap: {boxes[i][0].get_text()[:22]!r} / "
                    f"{boxes[j][0].get_text()[:22]!r}")
    return problems


def arrow(ax, p0, p1, color=RULE, lw=1.3, style="-|>", shrink=0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, color=color,
                                  linewidth=lw, mutation_scale=11,
                                  shrinkA=shrink, shrinkB=shrink, zorder=2))


def box(ax, cx, cy, w, h, label, sub, fill=BG, edge=RULE):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                 boxstyle="round,pad=0.02,rounding_size=0.06",
                                 linewidth=1.1, edgecolor=edge,
                                 facecolor=fill, zorder=3))
    ax.text(cx, cy + 0.10, label, color=INK, fontsize=12.5, ha="center",
            va="center", zorder=4)
    if sub:
        ax.text(cx, cy - 0.20, sub, color=DIM, fontsize=8.6, ha="center",
                va="center", zorder=4)


def step_tag(ax, cx, y, n, text):
    ax.text(cx, y, f"{n}", color=DIM, fontsize=8.2, ha="center", va="top",
            fontweight="bold", zorder=4)
    ax.text(cx, y - 0.30, text, color=DIM, fontsize=8.2, ha="center",
            va="top", zorder=4)


def main():
    fig = plt.figure(figsize=(11.2, 4.6), facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, 4.6)
    ax.axis("off")
    ax.set_facecolor(BG)

    cy = 2.15
    drivers = [(0.95, cy + 1.15), (0.95, cy), (0.95, cy - 1.15)]
    labels = ["driver A", "driver B", "driver C"]
    for (dx, dy), col, lab, w in zip(drivers, DRIVER_COL, labels,
                                      ["w₁", "w₂", "w₃"]):
        ax.add_patch(Circle((dx, dy), 0.34, facecolor=col, edgecolor="none",
                             zorder=3))
        ax.text(dx, dy - 0.58, lab, color=DIM, fontsize=8.6, ha="center",
                va="center", zorder=4)
        mx, my = 2.55, cy
        arrow(ax, (dx + 0.32, dy), (mx - 0.62, my + (dy - cy) * 0.28),
              color=RULE, shrink=1)
        ax.text((dx + mx) / 2 - 0.25, (dy + cy) / 2 + 0.18 * (1 if dy > cy
                else (-1 if dy < cy else 0)) + 0.05, w, color=DIM,
                fontsize=8.2, ha="center", va="center", zorder=4)

    box(ax, 2.85, cy, 1.55, 0.95, "weighted\nmean", None)
    arrow(ax, (3.62, cy), (4.55, cy), shrink=2)
    step_tag(ax, 4.08, 0.85, 1, "take the weighted\nmean of drivers")

    box(ax, 5.55, cy, 1.85, 0.95, "× (1 − inertia)", None)
    arrow(ax, (6.47, cy), (7.35, cy), shrink=2)
    step_tag(ax, 6.90, 0.85, 2, "damp by the\nnode's inertia")

    ax.add_patch(FancyArrowPatch((7.90, 3.85), (7.90, cy + 0.55),
                                  arrowstyle="-|>", color=DIM, linewidth=1.1,
                                  linestyle=(0, (2, 2)), mutation_scale=10,
                                  zorder=2))
    ax.text(7.90, 4.05, "applied change, if any", color=DIM, fontsize=8.2,
            ha="center", va="bottom", zorder=4)
    box(ax, 7.90, cy, 1.35, 0.95, "tanh", None)
    step_tag(ax, 7.90, 0.85, 3, "apply the change,\nsquash with tanh")

    arrow(ax, (8.58, cy), (9.45, cy), shrink=2)
    ax.add_patch(Circle((9.95, cy), 0.46, facecolor=NODE_COL,
                         edgecolor="none", zorder=3))
    ax.text(9.95, cy, "new\neffect", color="#0a0d18", fontsize=8.2,
            ha="center", va="center", fontweight="bold", zorder=4)
    step_tag(ax, 9.95, 0.85, 4, "move the node most\nof the way there")

    ax.text(0.0, 4.45, "One node, one step", color=INK, fontsize=13,
            ha="left", va="top", fontweight="medium", zorder=4)
    ax.text(11.2, 4.45, "model.html §4.4", color=DIM, fontsize=8.6,
            ha="right", va="top", zorder=4)

    problems = audit(fig)
    fig.savefig(OUT, dpi=150, facecolor=BG)
    plt.close(fig)
    print(f"  wrote {os.path.basename(OUT)}")
    if problems:
        print(f"  {len(problems)} layout problem(s):")
        for p in problems[:12]:
            print("     " + p)
    else:
        print("  0 layout problems")
    return len(problems)


if __name__ == "__main__":
    main()
