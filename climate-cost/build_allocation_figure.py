"""
The allocation figure on climate-cost.html, drawn from the model of record.

Two panels, one axis. Left: a kilogram of hard cheese, France to New York,
under every published way of splitting a dairy cow between her milk and her
meat. Right: a pair of leather shoes, Italy to New York, under every published
way of splitting a beef animal between its meat and its hide. Same model, same
engine, same scale; the only thing that changes between bars is the one number
on the contested edge.

The point of the pair: for the cheese the split *is* the answer (about 93% of
the kilogram sits on the herd stages; the figure prints the live value), for
the shoe it barely moves it (the hide is 9% of the pair). This replaces a video that claimed the shoe "nearly
tripled" under mass allocation. It did not; the video scaled the whole shoe by
the ratio of two factors, and no script in the repository could regenerate it.
That is why this file exists: the figure is built here, from `lca.py`, with
every alternative factor written next to the publication it comes from, and
the page names this script in its provenance.

The one framing of "how much it moves", used in the figure and on the page:

    spread = highest total / lowest total across the published bases shown.

Not adjacent bases, not economic-vs-physical only, not the default against
anything. Ambiguity about which two numbers a multiple refers to is exactly
what produced 11.65.

Run:  python3 build_allocation_figure.py          # writes site/assets/
      python3 build_allocation_figure.py --check  # numbers only, no file
"""
import os
import textwrap
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "data"))

import matplotlib                       # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt         # noqa: E402

import sitefig                          # noqa: E402
from sitefig import (MONO, BG, INK, DIM, RULE, FAINT, ACC, MOSS, COOL, SLATE,  # noqa: E402,F401
                     FS_2, FS_1, FS0, NOTES, fig_size, save)
from fig_floor import floor_problems    # noqa: E402
import lca                              # noqa: E402  the model of record; imported, not edited
from processes import PRODUCTS          # noqa: E402

OUT = os.path.join(ROOT, "site", "assets", "climate_allocation_bases.png")

# ---------------------------------------------------------------- bases ----
# Every factor here is quoted from a named publication. The one marked
# `default` is the value shipped in data/processes.py and must reproduce the
# published table exactly; the script refuses to draw if it does not.
#
# Cheese: Flysjo, Cederberg, Henriksson & Ledgard 2011, Int J Life Cycle
# Assess 16:420-430, Table 1 ("How does co-product handling affect the carbon
# footprint of milk?"), and IDF Bulletin 479/2015 pp. 35-36. The herd stages -
# enteric, feed, manure, milking - all carry the milk share; they move
# together because they are one decision.
CHEESE = dict(
    item="cheese", stages=("enteric", "feed", "manure", "dairy"),
    label="cheese, hard · 1 kg · France → New York\nthe cow split between milk and meat",
    bases=[
        ("system expansion, low",   0.63, "Flysjö 2011: 63–76%", False),
        ("system expansion, high",  0.76, "Flysjö 2011",             False),
        ("physical, IDF feed energy", 0.85, "Flysjö 2011, Sweden; IDF 2010 method", True),
        ("physical, IDF typical herd", 0.88, "IDF Bulletin 479 (2015) p. 35, BMR 0.02", False),
        ("economic",                0.92, "Flysjö 2011, New Zealand", False),
        ("protein",                 0.93, "Flysjö 2011, Sweden",      False),
        ("mass",                    0.98, "Flysjö 2011",              False),
        ("none: milk carries the cow", 1.00, "Flysjö 2011 reference case", False),
    ])

# Shoes: Lunesu, Correddu, Carta, Sechi, Farina & Pulina 2025, Animals
# 15(24):3546 ("Attributing Farm-to-Slaughter Emissions to Hides"): economic
# allocation "averaging 2.68% for 2023"; physical allocation "an average of
# 5.9% of live weight", range 4.2% (cull dairy cows) to 6.9% (semi-heavy young
# bulls). The model's own 2.2% is an assumption in the economic range and is
# drawn as the default; it is not a published value and is labelled so.
SHOES = dict(
    item="leather_shoes", stages=("hide",),
    label="shoes, leather · 1 pair · Italy → New York\nthe animal split between meat and hide",
    bases=[
        ("economic, model default", 0.022, "assumed", True),
        ("economic, 2023 mean",     0.027, "Lunesu et al. 2025",      False),
        ("physical, live-weight mean", 0.059, "Lunesu et al. 2025",   False),
        ("physical, live-weight max",  0.069, "Lunesu et al. 2025, young bulls", False),
    ])

# The numbers the page's table publishes for the two defaults. If the model
# no longer reproduces them the data has moved and the figure would be stale.
PUBLISHED = {"cheese": 13.18, "leather_shoes": 3.66}


def total_at(item, stages, share):
    """Run the model with the contested stages at `share`, restoring the
    data afterwards. `None` means the shipped value."""
    p = PRODUCTS[item]
    saved = {}
    try:
        for st in p["stages"]:
            if st["id"] in stages and share is not None:
                saved[st["id"]] = st["share"]
                st["share"] = share
        return lca.Model(item, p["default_origin"], p["default_dest"]).run()["total"]
    finally:
        for st in p["stages"]:
            if st["id"] in saved:
                st["share"] = saved[st["id"]]


def compute(panel):
    rows = []
    for label, share, source, default in panel["bases"]:
        t = total_at(panel["item"], panel["stages"], share)
        if default:
            shipped = total_at(panel["item"], panel["stages"], None)
            if abs(t - shipped) > 1e-9:
                raise SystemExit(f"{panel['item']}: the base marked default "
                                 f"({share}) is not the shipped share")
            if round(t, 2) != PUBLISHED[panel["item"]]:
                raise SystemExit(f"{panel['item']}: model gives {t:.2f}, page "
                                 f"table says {PUBLISHED[panel['item']]}; "
                                 "regenerate the table before this figure")
        rows.append((label, share, source, default, t))
    published = [r[4] for r in rows if r[2] != "assumed"]
    spread = max(published) / min(published)
    return rows, spread


# ------------------------------------------------------------------ draw ----
def draw(cheese, shoes, out):
    sitefig.style()
    # Drawn at the width it is shown: the text column of a notes page, 714px
    # (sitefig NOTES). Until 2026-09-05 this was fig_size(PROSE, 1.7), a
    # 1140px render squeezed to 714 on climate-cost.html, its 12px labels at
    # 7.5 on screen - the model chart's fault in reverse (PHASE4 A3). Two
    # panels side by side do not fit 714 with these labels, so they stack.
    w, h = fig_size(NOTES, 0.92)
    fig, axes = plt.subplots(2, 1, figsize=(w, h), sharex=True,
                             gridspec_kw=dict(hspace=0.62))
    texts = []
    xmax = 19.0     # room for the "15.4 kg" label at 714px

    for ax, (panel, (rows, spread)) in zip(axes, ((CHEESE, cheese), (SHOES, shoes))):
        n = len(rows)
        ys = list(range(n))[::-1]
        for y, (label, share, source, default, t) in zip(ys, rows):
            col = SLATE if source == "assumed" else (ACC if default else COOL)
            ax.barh(y, t, height=0.62, color=col, edgecolor="none")
            texts.append(ax.text(t + 0.18, y, f"{t:.1f} kg", va="center",
                                 ha="left", fontsize=FS_2, color=INK))
            # the factor, inside the bar when there is room, else after the number
            ftxt = f"{share*100:.1f}%" if share < 0.1 else f"{share*100:.0f}%"
            if t > 2.4:
                texts.append(ax.text(0.18, y, ftxt, va="center", ha="left",
                                     fontsize=FS_2, color=BG))
            else:
                texts.append(ax.text(t + 1.55, y, ftxt, va="center", ha="left",
                                     fontsize=FS_2, color=DIM))
        ax.set_yticks(ys)
        ax.set_yticklabels([r[0] for r in rows], fontsize=FS_2)
        ax.tick_params(axis="y", length=0, pad=6)
        ax.set_xlim(0, xmax)
        ax.set_xticks(range(0, int(xmax) + 1, 5))   # matplotlib's extra tick at 20 sat off the canvas
        ax.set_ylim(-0.7, n - 0.3)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(RULE)
        ax.set_xlabel("kg CO₂e per functional unit", fontsize=FS_2, color=DIM)
        ax.xaxis.grid(True, color=FAINT, linewidth=0.8)
        ax.set_axisbelow(True)
        # No figure title and no subtitle: the page heading and caption do that
        # job (sitefig: "a figure carries none; a sheet labels its panels").
        # A two-panel sheet keeps one short label per panel, set through
        # sitefig.panel() so it is the same furniture as every other sheet.
        sitefig.panel(ax, panel["label"], pad=10)
        texts += sitefig.titles(ax)
        texts.append(ax.text(1.0, -0.2, f"spread ×{spread:.2f}",
                             transform=ax.transAxes, ha="right", va="top",
                             fontsize=FS_1, color=INK))
        share_of = _stage_share(panel)
        texts.append(ax.text(0, -0.2, f"contested stage: {share_of:.0%} of the total",
                             transform=ax.transAxes, ha="left", va="top",
                             fontsize=FS_2, color=DIM))

    foot = ("Spread = highest ÷ lowest total across the published bases shown; the model’s assumed\n"
            "2.2% is drawn but not counted. Bars: the shipped default in dark blue, published alternatives\n"
            "in light blue; the shoe’s shipped 2.2% is an assumption and is grey. Milk–meat factors: Flysjö,\n"
            "Cederberg, Henriksson & Ledgard 2011, Int J LCA 16:420, Table 1; IDF Bulletin 479 (2015)\n"
            "pp. 35–36. Hide factors: Lunesu et al. 2025, Animals 15:3546. Every bar is one run of\n"
            "climate-cost/lca.py with that factor on the contested edge; drawn by build_allocation_figure.py.")
    texts.append(fig.text(0.045, 0.012, foot, fontsize=FS_2, color=DIM,
                          va="bottom", ha="left", linespacing=1.45))
    fig.subplots_adjust(left=0.30, right=0.975, top=0.94, bottom=0.30)
    sitefig.centre(fig)      # the margins above are a guess; this measures
    problems = audit(fig, texts)
    size = save(fig, out)
    return size, problems


def _stage_share(panel):
    p = PRODUCTS[panel["item"]]
    r = lca.Model(panel["item"], p["default_origin"], p["default_dest"]).run()
    return sum(s["total"] for s in r["spine"] if s["id"] in panel["stages"]) / r["total"]


def audit(fig, texts):
    """The sibling builders' checks: nothing under the on-screen floor,
    nothing off the canvas, no two labels on top of each other."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    items = [(t, t.get_fontsize() >= FS0) for t in texts]
    for ax in fig.axes:
        items += [(t, False) for t in ax.get_yticklabels() + ax.get_xticklabels()]
        items.append((ax.xaxis.label, False))
    problems = floor_problems(fig, items) + sitefig.grid_problems(fig)
    W, H = fig.get_size_inches() * fig.dpi
    boxes = []
    for t, _ in items:
        if not t.get_text().strip():
            continue
        b = t.get_window_extent(renderer=r)
        if b.x0 < -1 or b.y0 < -1 or b.x1 > W + 1 or b.y1 > H + 1:
            problems.append(f"off canvas: {t.get_text()[:30]!r}")
        boxes.append((b, t.get_text()[:30]))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][0], boxes[j][0]
            if a.overlaps(b) and boxes[i][1] != boxes[j][1]:
                problems.append(f"overlap: {boxes[i][1]!r} / {boxes[j][1]!r}")
    return problems


def main():
    cheese = compute(CHEESE)
    shoes = compute(SHOES)
    for name, (rows, spread) in (("cheese", cheese), ("shoes", shoes)):
        print(f"\n{name}: spread x{spread:.2f} (highest / lowest published)")
        for label, share, source, default, t in rows:
            print(f"  {label:30s} {share:6.3f}  {t:6.2f} kg   {source}"
                  f"{'   <- shipped default' if default else ''}")
    if "--check" in sys.argv:
        return 0
    size, problems = draw(cheese, shoes, OUT)
    print(f"\nwritten {OUT} ({size/1024:.0f} kB)")
    if problems:
        print("audit:")
        for p in problems:
            print("  " + p)
        return 1
    print("audit: 0 problems")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
