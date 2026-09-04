"""
The atlas layer diagram: what the nine-layer model looks like, at last.

atlas.html spends a table and four paragraphs describing nine layers, their
node counts, and which links between them run one way versus both ways - and
never shows a picture of it. This is that picture, sized for the site's own
1140px `wide` track rather than folded into a corner of a poster, and it goes
directly above that same table (h2 "The nine layers"), so it has to count out
to nine boxes or it will visibly disagree with the thing it sits next to.

It is not drawn from scratch. Panel A of build_throughlines.py already lays
out a version of this diagram - but at the model's twelve internal *kinds*,
not the page's nine displayed *layers*. The table folds three kind pairs
together: Space is sun plus insolation (1 + 18 = 19, the table's own number),
Markets and fuel is market plus supply (2,902 + 725 = 3,627), and Grids is
grid plus district (214 + 3,332 = 3,546). The other six kinds map to a layer
one-for-one. A first version of this file reproduced panel A's twelve boxes
verbatim and stuck a "nine layers" title on top of them - which is exactly
the silent disagreement this file exists to avoid. This version groups the
same way the table does, and proves the grouping by computing every group's
count as a live sum over its constituent kinds rather than asserting it.

Two things this adds that a plain box-and-arrow copy of panel A would not:

1. **One-way vs. two-way, drawn rather than only argued.** The page's prose
   says a recorded earthquake can move a grid but no grid ever causes an
   earthquake - climate and events only push forward. That claim is a
   structural fact of the published propagation (build_throughlines.py's
   `engine()`, and atlas-app.js's own run loop): every kind is given a rank,
   sun < insolation < weather < climate < event < everything else, and the
   model only ever lets a lower rank push a higher one, never the reverse.
   Everything left at the default rank (markets, grids, plants, districts,
   consumers, behaviour) trades an influence back and forth. That rank table
   is reproduced here directly from the engine, and a link between two
   *groups* is only ever called one-way if every kind-level link it stands in
   for agrees - checked in code (see `group_links()`), not assumed. One-way
   links get a single arrowhead in one colour; two-way links get a filled
   head on both ends in a second, brighter colour, so the distinction survives
   being scaled down to the page's 1140px display width and does not depend
   on a reader noticing arrowhead count alone.
2. **Nothing here is typed in.** Every count on every box is read live out of
   site/assets/atlas-data.js - the same payload every other generator on this
   site loads - so a box's number, or the table's, cannot drift from the
   published model without this figure changing too.

Run:  python3 build_layer_diagram.py
"""

import collections
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from fig_floor import floor_problems

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "assets", "atlas-data.js")
OUT = os.path.join(HERE, "site", "assets", "atlas_layers.png")

BG, INK, DIM = "#0b0f1c", "#e3e6f2", "#8b93b0"
FAINT = "#151b30"
ONE_WAY_COL = "#4a5580"    # muted slate - a link that only pushes forward
TWO_WAY_COL = "#7fa8e0"    # brighter, cooler blue - a link that trades back

# The propagation's own rank table (build_throughlines.py's engine(), which
# mirrors atlas-app.js's run loop): a lower rank can push a higher one, never
# the other way, and everything left at the default rank trades back and
# forth with everything else at that same rank.
RANK = {"sun": 0, "insolation": 1, "weather": 2, "climate": 3, "event": 4}

# The published propagation's links, at kind level - the same thirteen edges
# panel A of build_throughlines.py draws.
KIND_LINKS = [("sun", "insolation"), ("insolation", "grid"),
              ("weather", "climate"), ("climate", "event"),
              ("climate", "grid"), ("event", "grid"),
              ("market", "supply"), ("supply", "grid"),
              ("station", "grid"), ("grid", "district"),
              ("district", "consumer"), ("district", "psych"),
              ("psych", "consumer")]

# The table's own grouping (site/atlas.html, "The nine layers"): which kinds
# roll up into which displayed layer.
GROUP_OF = {"sun": "space", "insolation": "space",
            "weather": "weather", "climate": "climate", "event": "events",
            "market": "markets", "supply": "markets",
            "grid": "grids", "district": "grids",
            "station": "plants", "consumer": "demand", "psych": "behaviour"}

GLABEL = {"space": "Space", "weather": "Weather", "climate": "Climate",
          "events": "Events", "markets": "Markets and fuel",
          "grids": "Grids", "plants": "Power plants", "demand": "Demand",
          "behaviour": "Behaviour"}

GCOL = {"space": "#f2d98b", "weather": "#4f9d84", "climate": "#cfd6f0",
        "events": "#d86a86", "markets": "#6f7fd8", "grids": "#5aa8d8",
        "plants": "#8b7ff2", "demand": "#8b93b0", "behaviour": "#a98fd8"}

# Position for each of the nine group boxes, x in [0,100], y in [0,36]. The
# four exogenous layers (space, weather, climate, events) sit apart from the
# five that trade back and forth, so the one-way/two-way split reads visually
# as two neighbourhoods before a reader even looks at an arrowhead.
# Space's only link is insolation into the grid, which is the longest edge on
# the sheet. Ordering the top row markets-space-plants keeps that edge clear
# of every other box: laid out left to right as space-markets-plants it ran
# underneath the markets box, which hid it completely and left the space layer
# looking connected to nothing.
YMAX = 38.5

POS = {"markets": (8, 27), "space": (28, 33), "plants": (48, 33),
       "weather": (24, 6), "climate": (42, 6), "events": (60, 6),
       "grids": (60, 19), "demand": (82, 19), "behaviour": (82, 5)}


def style():
    plt.rcParams.update({
        "font.size": 12.5,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Selawik", "DejaVu Sans", "Arial"],
    })


def load():
    raw = open(DATA, encoding="utf-8").read()
    return json.loads(raw[raw.index("=") + 1:raw.rindex(";")])


def group_links():
    """Fold the thirteen kind-level links down to the nine group boxes.

    A link internal to one group (sun->insolation, market->supply,
    grid->district) disappears - it is now inside a single box. Every
    surviving link is checked, not assumed: if the kind-level links that map
    onto the same group pair ever disagreed about one-way vs. two-way, that
    is a modelling change this figure needs to know about, so it fails loudly
    instead of silently picking one.
    """
    verdict = {}
    for a, b in KIND_LINKS:
        ga, gb = GROUP_OF[a], GROUP_OF[b]
        if ga == gb:
            continue
        one_way = RANK.get(a, 5) != RANK.get(b, 5)
        key = (ga, gb)
        if key in verdict and verdict[key] != one_way:
            raise SystemExit(
                f"group link {ga}->{gb} is one-way on one kind-level edge "
                f"and two-way on another - the grouping in GROUP_OF no "
                f"longer matches a single propagation direction and needs "
                f"a human to look at it, not a figure that guesses.")
        verdict[key] = one_way
    return list(verdict.items())


def edge_points(a_pos, b_pos):
    """Where a straight-ish connector should touch each box's edge, picking
    the horizontal or vertical pair of edges depending on which way the two
    centres are mostly offset. Handles either box being left/right/above/
    below the other, unlike a formula that only works for one layout."""
    xa, ya, wa, ha = a_pos
    xb, yb, wb, hb = b_pos
    dx, dy = xb - xa, yb - ya
    if abs(dx) >= abs(dy):
        if dx >= 0:
            return (xa + wa / 2, ya), (xb - wb / 2, yb)
        return (xa - wa / 2, ya), (xb + wb / 2, yb)
    if dy >= 0:
        return (xa, ya + ha / 2), (xb, yb - hb / 2)
    return (xa, ya - ha / 2), (xb, yb + hb / 2)


def audit(fig):
    """Same walk build_throughlines.py's audit() does: every Text object on
    the canvas, checked for running off the canvas, overlapping another one,
    or falling under the site's on-screen type floor."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    title_ids = {id(ax.title) for ax in fig.axes}
    items, problems = [], []
    for ax in fig.axes:
        for tx in list(ax.texts) + [ax.title]:
            if tx.get_text().strip():
                items.append(tx)
        lg = ax.get_legend()
        if lg is not None:
            for lab in lg.get_texts():
                if lab.get_text().strip():
                    items.append(lab)
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
    problems += floor_problems(fig, [(t, id(t) in title_ids) for t in items])
    problems += box_problems()
    return problems


def box_problems(gutter=2.0):
    """The text audit above cannot see this figure's real furniture. Its nodes
    are patches, not Text, so two boxes drawn on top of each other pass every
    check while reading as one merged box - which is exactly what happened
    when space and markets were placed sixteen units apart and each was
    fifteen and a half wide. Checked in data units, against POS, so it holds
    however the figure is later resized."""
    w, h, out = 15.5, 7.2, []
    names = list(POS)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            (ax_, ay), (bx, by) = POS[names[i]], POS[names[j]]
            dx, dy = abs(ax_ - bx) - w, abs(ay - by) - h
            if dx < gutter and dy < gutter:
                out.append(f"boxes too close: {names[i]} / {names[j]} "
                           f"(gap {max(dx, dy):.1f} < {gutter})")
    # Spacing is only half the question: a box can be clear of every other box
    # and still be cut off by the canvas edge, which is how the top row lost
    # its border the first time this layout moved.
    for n, (x, y) in POS.items():
        if y + h / 2 > YMAX - 0.4 or y - h / 2 < 0.4:
            out.append(f"box off canvas: {n} (y {y}, ylim {YMAX})")
    return out


def main():
    style()
    D = load()
    kind = [D["kinds"][k] for k in D["kind"]]
    kind_counts = collections.Counter(kind)
    # Every group's count is a live sum over its constituent kinds - never a
    # number copied from the table, so it cannot silently drift from it.
    counts = {g: sum(kind_counts[k] for k, gg in GROUP_OF.items() if gg == g)
              for g in GLABEL}

    # 11.4in wide puts the on-screen factor (pt * 1140 / (72 * width)) at
    # ~1.39, comfortably above the 1.02 that made panel A's box labels read
    # small as a sub-panel of a poster.
    fig = plt.figure(figsize=(11.4, 6.9), facecolor=BG)
    ax = fig.add_axes([0.035, 0.065, 0.93, 0.70])
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, YMAX)
    ax.axis("off")

    fig.text(0.035, 0.965, "The nine layers, and what carries between them",
              color=INK, fontsize=19, fontweight="bold", va="top")
    fig.text(0.035, 0.912,
              "Every count below is read live from the published model, "
              "grouped the same way the table beneath this figure is: Space,\n"
              "Markets and fuel, and Grids each merge two of the payload's "
              "twelve node kinds. One arrowhead pushes forward only; two "
              "trade back and forth.",
              color=DIM, fontsize=11.0, va="top", linespacing=1.4)

    at = {}
    for g, (x, y) in POS.items():
        w, h = 15.5, 7.2
        ax.add_patch(FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.25,rounding_size=0.5",
            linewidth=1.6, edgecolor=GCOL[g], facecolor=FAINT, zorder=2))
        ax.text(x, y + 1.6, GLABEL[g], ha="center", va="center", color=INK,
                fontsize=12.5, fontweight="bold", zorder=3)
        n = counts[g]
        ax.text(x, y - 1.8, f"{n:,} node" + ("" if n == 1 else "s"),
                ha="center", va="center", color=DIM, fontsize=10.8, zorder=3)
        at[g] = (x, y, w, h)

    for (ga, gb), one_way in group_links():
        pa, pb = edge_points(at[ga], at[gb])
        col = ONE_WAY_COL if one_way else TWO_WAY_COL
        style_ = "-|>" if one_way else "<|-|>"
        ax.add_patch(FancyArrowPatch(
            pa, pb, arrowstyle=style_,
            mutation_scale=16 if one_way else 20,
            linewidth=1.7 if one_way else 2.1,
            color=col, alpha=0.95, zorder=1,
            connectionstyle="arc3,rad=0.12"))

    # ---- legend: two example arrows, drawn the same way the real ones are,
    # rather than a synthetic marker matplotlib's own legend() would draw --
    lx0, ly = 4, -3.8
    ax.add_patch(FancyArrowPatch((lx0, ly), (lx0 + 10, ly), arrowstyle="-|>",
                                  mutation_scale=16, linewidth=1.7,
                                  color=ONE_WAY_COL))
    ax.text(lx0 + 12.5, ly, "one-way  —  space, weather, climate and "
            "events only push forward", color=DIM,
            fontsize=10.8, va="center", ha="left")
    ly2 = -8.0
    ax.add_patch(FancyArrowPatch((lx0, ly2), (lx0 + 10, ly2),
                                  arrowstyle="<|-|>", mutation_scale=20,
                                  linewidth=2.1, color=TWO_WAY_COL))
    ax.text(lx0 + 12.5, ly2, "two-way  —  markets and fuel, grids, power "
            "plants, demand and behaviour trade back and forth",
            color=DIM, fontsize=10.8, va="center", ha="left")
    ax.set_ylim(-11.0, YMAX)

    problems = audit(fig)
    fig.savefig(OUT, dpi=160, facecolor=BG)
    plt.close(fig)
    print(f"  wrote {os.path.basename(OUT)}")
    if problems:
        print(f"  {len(problems)} layout problem(s):")
        for p in problems[:20]:
            print("     " + p)
    else:
        print("  0 layout problems")
    return len(problems)


if __name__ == "__main__":
    raise SystemExit(0 if main() == 0 else 1)
