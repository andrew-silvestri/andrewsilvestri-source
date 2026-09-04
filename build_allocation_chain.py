"""
One traced chain, before the calculator: the tomato's fertiliser goes four
levels deep.

climate-cost.html spends several paragraphs on life-cycle allocation and then
hands the reader a button. Before that, the page's own prose names an example
it never draws: "A tomato needs fertiliser, the fertiliser needs ammonia, the
ammonia needs natural gas, and getting that gas out of the ground leaks
methane. Four levels down, and every level is a real emission somewhere."
This figure is that sentence, drawn - the recursion claim, not the allocation
claim. Every number is pulled from the model of record rather than typed in -
climate-cost/lca.py's Model class, walking the same process graph
(climate-cost/data/processes.py) the interactive calculator runs.

The chain drawn here is:
    Tomato, field grown (the cultivation stage)          59.8 g CO2e
      -> Fertiliser (nitric acid and nitrate finishing)    5.27 g
        -> Ammonia synthesis (Haber-Bosch)                 3.20 g
          -> Natural gas extraction (where the methane leaks)  0.386 g

Four real levels, each smaller than the one above it, each with the physical
amount that flows down the edge (grams of nitrogen, then grams of gas). That
taper is the thing worth showing: "the branches have branches" is a claim
about depth, and depth is what a reader can count here.

This is deliberately *not* an allocation-compounding figure, and an earlier
version of this file tried to make it one by printing "alloc x1.00" on every
edge - technically true (none of nitric-acid finishing, ammonia synthesis or
gas extraction make a second product, so nothing on this particular chain is
shared away) but a label with no variation across three edges tells a reader
nothing, and the closing caption then had to spend three lines explaining why
the figure wasn't demonstrating what it looked like it was building up to.
That is a tell that the figure had the wrong job. The chain that actually
shows allocation shrinking a number - the leather shoe, 2.2% by economic
share against 7% by mass - is drawn elsewhere on this page, and this figure
now just points there in one line instead of impersonating it.

One honesty note that is still live here: lca.py's CUTOFF exists to keep the
calculator's printed "largest sources" table short, and at its shipped value
(0.15% of the product's total) it drops the natural-gas node on THIS
particular path before it ever gets built - the fertiliser route into ammonia
is a small share of an already-small cultivation stage. The number is real
(every process factor above it is exactly what the calculator uses); it just
does not survive the display cutoff at its default setting. This script
disables CUTOFF only for its own call into Model.run(), which asks the same
recursion to keep expanding one branch a little further - it changes nothing
about any process factor, allocation, or the page's own output. See trace()
below.

Run:  python3 build_allocation_chain.py
"""

import os
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from fig_floor import floor_problems

HERE = os.path.dirname(os.path.abspath(__file__))
CC = os.path.join(HERE, "climate-cost")
OUT = os.path.join(HERE, "site", "assets", "climate_chain_tomato.png")

sys.path.insert(0, CC)
sys.path.insert(0, os.path.join(CC, "data"))
import lca  # noqa: E402  the model of record; not edited, only imported

BG, INK, DIM = "#0b0f1c", "#e3e6f2", "#8b93b0"
FAINT, ARROW = "#151b30", "#4a5580"
MOSS, ROSE, VIOLET, BLUE = "#4f9d84", "#d86a86", "#8b7ff2", "#5aa8d8"


def style():
    plt.rcParams.update({
        "font.size": 11,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Selawik", "DejaVu Sans", "Arial"],
    })


def find(node, nid):
    """Depth-first search of a Model.run() node tree by process id."""
    if node["id"] == nid:
        return node
    for c in node["children"]:
        f = find(c, nid)
        if f is not None:
            return f
    return None


def trace():
    """Recompute the tomato's chain from lca.py directly - see the module
    docstring for why CUTOFF is disabled for this one call."""
    saved = lca.CUTOFF
    lca.CUTOFF = 0.0
    try:
        res = lca.Model("tomato_field", "ES", "US-TX").run()
    finally:
        lca.CUTOFF = saved
    cult = next(s for s in res["spine"] if s["id"] == "cultivation")
    fert = find(cult, "nitrate_fert")
    amm = find(fert, "ammonia") if fert else None
    gas = find(amm, "natgas_extraction") if amm else None
    if fert is None or amm is None or gas is None:
        raise SystemExit(
            "the tomato -> fertiliser -> ammonia -> natural gas chain is no "
            "longer in climate-cost/data/processes.py; refusing to draw a "
            "figure with an invented number in place of a missing one.")
    return res, cult, fert, amm, gas


def audit(fig):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    title_ids = {id(ax.title) for ax in fig.axes}
    items, problems = [], []
    for ax in fig.axes:
        for tx in list(ax.texts) + [ax.title]:
            if tx.get_text().strip():
                items.append(tx)
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
                    f"overlap: {boxes[i][0].get_text()[:24]!r} / "
                    f"{boxes[j][0].get_text()[:24]!r}")
    problems += floor_problems(fig, [(t, id(t) in title_ids) for t in items])
    return problems


def g(kg):
    """Grams of CO2e, formatted at a precision that shows the taper: three
    figures at the top of the chain, more where the number is this small."""
    v = kg * 1000.0
    if v >= 10:
        return f"{v:.1f} g"
    if v >= 1:
        return f"{v:.2f} g"
    return f"{v:.3f} g"


def main():
    style()
    res, cult, fert, amm, gas = trace()

    total = res["total"]
    cult_share = cult["total"] / total

    # Tall enough for the wrapped per-node captions (stage share, methane
    # note) below the boxes, plus one short closing line - not the taller
    # figure an earlier version needed to fit a three-line apology under it.
    fig = plt.figure(figsize=(11.0, 4.9), facecolor=BG)
    ax = fig.add_axes([0.02, 0.0984, 0.96, 0.5947])
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 42)
    ax.axis("off")

    fig.text(0.02, 0.967,
              "Four levels down: one tomato's fertiliser chain",
              color=INK, fontsize=18, fontweight="bold", va="top")
    fig.text(0.02, 0.897,
              "Traced live from climate-cost/lca.py - the same engine the "
              "calculator below runs - for 1 kg of field-grown tomato, Spain\n"
              "to Texas. Each edge carries the physical amount that flows "
              "into the next process; the total tapers by two orders of "
              "magnitude in three steps.",
              color=DIM, fontsize=10.8, va="top", linespacing=1.45)

    # A short bold title (must fit one line inside the box at this width)
    # plus a longer caption underneath, which has the box's full width to
    # wrap into rather than fighting the title for space.
    nodes = [
        ("Tomato, field grown", cult, MOSS,
         f"cultivation stage - {cult_share:.1%} of the {g(total)} "
         f"full farm-to-bin total"),
        ("Fertiliser", fert, BLUE, "nitric acid and nitrate finishing"),
        ("Ammonia synthesis", amm, VIOLET, "Haber-Bosch"),
        ("Natural gas extraction", gas, ROSE,
         "~1.5% of this is fugitive methane, at 82x CO2 over 20 years"),
    ]
    xs = [12, 38, 64, 90]
    y = 24
    w, h = 16.5, 22.0
    for (label, node, col, note), x in zip(nodes, xs):
        ax.add_patch(FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.3,rounding_size=0.6",
            linewidth=1.6, edgecolor=col, facecolor=FAINT, zorder=2))
        ax.text(x, y + 6.6, label, ha="center", va="top", color=INK,
                fontsize=10.8, fontweight="bold", zorder=3)
        ax.text(x, y - 3.0, g(node["total"]), ha="center", va="center",
                color=INK, fontsize=15.5, fontweight="bold", zorder=3)
        ax.text(x, y - 7.2, "CO2e per kg tomato", ha="center", va="center",
                color=DIM, fontsize=8.6, zorder=3)
        wrapped = "\n".join(textwrap.wrap(note, width=24))
        ha = "center"
        nx = x
        if x >= xs[-1]:
            # the last box has no room to its right for a centered note
            # wider than the box; anchor it to the box's own right edge
            # instead of letting it run past the canvas.
            ha, nx = "right", x + w / 2
        ax.text(nx, y - h / 2 - 2.2, wrapped, ha=ha, va="top",
                color=DIM, fontsize=8.8, linespacing=1.35, zorder=3)

    # Each edge carries the physical amount flowing into the next process -
    # what makes this a chain with branches, not a single multiplier. (An
    # earlier version also printed the allocation factor here; every one of
    # them is x1.00 on this particular chain, which is a fact with nothing
    # to show, so it is stated once in the closing line below instead of
    # repeated three times over the diagram.)
    edge_defs = [(fert, "N"), (amm, "N"), (gas, "gas")]
    for i, (child, unit) in enumerate(edge_defs):
        x0, x1 = xs[i] + w / 2, xs[i + 1] - w / 2
        ax.add_patch(FancyArrowPatch(
            (x0, y), (x1, y), arrowstyle="-|>", mutation_scale=17,
            linewidth=1.8, color=ARROW, zorder=1))
        amt = child["amount"] * 1000.0
        ax.text((x0 + x1) / 2, y + 3.6,
                f"{amt:.3g} g {unit}", ha="center", va="bottom",
                color=DIM, fontsize=9.2, zorder=3)

    fig.text(0.02, 0.11,
              "Allocation is x1.00 on every edge here - none of these three "
              "processes make a second product. The chain where it actually "
              "shrinks a number is the leather shoe, further down this page.",
              color=DIM, fontsize=9.4, va="top")

    problems = audit(fig)
    fig.savefig(OUT, dpi=170, facecolor=BG)
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
