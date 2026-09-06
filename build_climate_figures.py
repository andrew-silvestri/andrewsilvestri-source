"""
Figures for the climate research pages.

Two diagrams, both drawn from published numbers rather than sketched:

  nitrogen_fixation.png   what the legume symbiosis does now, what the four
                          engineering routes are trying to change, and how
                          far each one has actually got.
  running_shoe.png        a running shoe in side profile with every part
                          named by the polymer it is made of, and what
                          happens to each at end of life.

Every number on a figure is either a published value with the source named
in the page prose, or a stated stoichiometry. Nothing is estimated silently.

Run:  python3 build_climate_figures.py
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
from matplotlib.patches import (FancyArrowPatch, FancyBboxPatch,  # noqa: E402
                                Circle, Polygon, Ellipse, Rectangle)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site", "assets")

# the site palette, same constants the other figure builders hold
BG, INK, DIM = "#0a0d18", "#e3e6f2", "#8b93b0"
FAINT, RULE = "#151b30", "#232a45"
ACC, COOL, GREEN = "#8b7ff2", "#65B2CC", "#4f9d84"
WARN, GOLD = "#d86a86", "#e8c98f"


def audit(fig):
    """Report text that overlaps other text or runs off the canvas. Every
    Text object is enumerated explicitly, because findobj returns tick
    objects that were never drawn and whose boxes are meaningless."""
    fig.canvas.draw()
    ren = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    items = [t for t in fig.texts if t.get_text().strip()]
    for ax in fig.axes:
        for t in [ax.title, ax.xaxis.label, ax.yaxis.label] + list(ax.texts):
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
            boxes.append((t.get_text()[:34], t.get_window_extent(renderer=ren)))
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
    return bad


def save(fig, name):
    bad = audit(fig)
    fig.savefig(os.path.join(OUT, name), dpi=150, facecolor=BG)
    plt.close(fig)
    print(f"  {name:26s} {'OK' if not bad else 'LAYOUT: ' + '; '.join(bad[:3])}")
    return bad


def panel(ax, title, sub=None):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.text(0, 103, title, color=INK, fontsize=12.5, fontweight="600",
            va="bottom", ha="left")
    if sub:
        ax.text(0, 98.5, sub, color=DIM, fontsize=9.2, va="top", ha="left")


def box(ax, xmid, ymid, text, fc=FAINT, ec=RULE, tc=INK, fs=8.6,
        weight="400"):
    """A labelled box, drawn as the text's own bounding box.

    Two earlier versions took an explicit height and centred the text in
    it. Both let long labels hang out of short boxes, and the layout audit
    never saw it, because the audit compares text against other text and a
    box is not text. Guessing a line height in axis units failed again the
    moment the figure aspect changed. Letting matplotlib draw the box *as*
    the text's bbox removes the guess: the box cannot be the wrong size for
    its contents, at any figure size.
    """
    ax.text(xmid, ymid, text, color=tc, fontsize=fs, ha="center",
            va="center", zorder=3, fontweight=weight, linespacing=1.55,
            bbox=dict(boxstyle="round,pad=0.75", fc=fc, ec=ec, lw=1.0))


def arrow(ax, p0, p1, color=DIM, lw=1.2, style="-|>", rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, color=color,
                                 lw=lw, linestyle=ls, mutation_scale=11,
                                 shrinkA=2, shrinkB=2, zorder=1,
                                 connectionstyle=f"arc3,rad={rad}"))


# ------------------------------------------------------- nitrogen fixation --
def fig_nitrogen():
    fig = plt.figure(figsize=(11.6, 7.4), facecolor=BG)
    gs = fig.add_gridspec(2, 1, height_ratios=[0.66, 1.0],
                          left=0.045, right=0.975, top=0.845, bottom=0.055,
                          hspace=0.40)

    fig.text(0.045, 0.965, "Nitrogen fixation, and the four ways to move it",
             color=INK, fontsize=19, fontweight="600", va="top")
    fig.text(0.045, 0.925,
             "What a legume already does, what industry does instead, and "
             "where each engineering route has actually got to.",
             color=DIM, fontsize=10.6, va="top")

    # ---- panel 1: the symbiosis as it works today ----------------------
    ax = fig.add_subplot(gs[0])
    panel(ax, "1  ·  What the bean already does",
          "Rhizobia inside root nodules run nitrogenase; the plant pays for "
          "it in sugar. Both halves are the point.")

    # the root itself, drawn small and to one side: it is the subject, not
    # the diagram
    ax.plot([6, 6], [16, 74], color="#6b5a44", lw=3.4, solid_capstyle="round",
            zorder=2)
    for yy in (62, 48, 34):
        ax.add_patch(Ellipse((9.2, yy), 6.4, 4.2, angle=-18,
                             fc="#c0788a", ec="#8f4f60", lw=1.0, zorder=3))
    ax.text(6, 80, "legume root", color=DIM, fontsize=8.4, ha="center")
    ax.text(6, 10, "nodules", color=DIM, fontsize=8.4, ha="center")

    # a single left-to-right chain, so nothing has to cross anything
    box(ax, 32, 78, "N$_2$ from air\n78% of the atmosphere, and inert",
        fc="#0f1626", fs=8.3)
    box(ax, 32, 38,
        "Plant photosynthate\n~4–6 g carbon per g nitrogen fixed",
        fc="#0f1626", fs=8.3)
    box(ax, 63, 58,
        "Nitrogenase, inside the nodule\n\n"
        "N$_2$ + 8H$^+$ + 8e$^-$ + 16 ATP  $\\rightarrow$  2NH$_3$ + H$_2$",
        fc="#101c1a", ec=GREEN, fs=8.2)
    box(ax, 91, 58,
        "Ammonia,\nto the plant\n\nand a residue\nfor the crop\nthat follows",
        fc="#0f1626", fs=8.3)

    # Arrows run from inside one box to inside the next and sit at a lower
    # zorder, so the boxes clip them. Endpoints that merely aim at a box
    # edge float in space the moment the text metrics change; endpoints
    # buried under the boxes cannot.
    arrow(ax, (38, 74), (60, 62), color=COOL, rad=0.16)
    arrow(ax, (38, 42), (60, 54), color=GOLD, rad=-0.16)
    arrow(ax, (70, 58), (88, 58), color=GREEN)

    # the constraint that governs every route below
    ax.text(58, 16, "Oxygen destroys nitrogenase. The nodule buys its hypoxia "
                    "with leghaemoglobin —\nwhich is why this is hard to move "
                    "anywhere else.",
            color=WARN, fontsize=8.2, ha="center", va="center",
            linespacing=1.6)

    # ---- panel 2: the four routes --------------------------------------
    ax2 = fig.add_subplot(gs[1])
    panel(ax2, "2  ·  The four routes, and how far each has got",
          "Ordered by how much has to be invented. Everything below is "
          "published work, not proposals.")

    routes = [
        ("A. Edit the legume's own\nregulation",
         "Nodule number is capped by the plant\n(CLE peptide → SUNN/NARK "
         "autoregulation)\nand switched off by soil nitrate (NLP).\n"
         "CRISPR knockouts lift both caps.",
         "Demonstrated in model legumes;\nbean editing now routine via\n"
         "hairy-root transformation",
         GREEN, 0.86),
        ("B. Give cereals the\nsymbiosis",
         "Chimeric receptors (MtNFP–ZmMYR1,\nMtLYK3–ZmCERK1) let a cereal see\n"
         "the Nod factor; SHR–SCR drives cortical\ncell division.",
         "Rice signals back; nodule-like\nstructures form in legumes only.\n"
         "No functioning nodule on a cereal",
         COOL, 0.45),
        ("C. Put nif genes in the\nplant itself",
         "Move the nitrogenase cluster into\nmitochondria or chloroplasts, which\n"
         "can supply the hypoxia and the ATP.",
         "Individual Nif proteins expressed\nand assembled in pieces.\n"
         "No plant fixes N$_2$ this way",
         ACC, 0.28),
        ("D. Engineer the bacteria,\nnot the plant",
         "Free-living or associative microbes\nedited to keep fixing nitrogen when\n"
         "fertiliser is present.",
         "Commercial products sold for\nmaize; contribution per acre\nis "
         "contested and modest",
         GOLD, 0.62),
    ]
    x = 1.0
    for name, how, state, col, frac in routes:
        w = 23.2
        ax2.add_patch(FancyBboxPatch((x, 8), w, 78,
                                     boxstyle="round,pad=0.6,rounding_size=2",
                                     fc="#0d1322", ec=RULE, lw=1.0, zorder=1))
        ax2.text(x + w / 2, 80, name, color=col, fontsize=9.4,
                 fontweight="600", ha="center", va="center", linespacing=1.5)
        ax2.text(x + w / 2, 60, how, color=INK, fontsize=7.7, ha="center",
                 va="center", linespacing=1.6)
        ax2.text(x + w / 2, 34, state, color=DIM, fontsize=7.5, ha="center",
                 va="center", linespacing=1.6)
        # how far along, as a bar rather than a claim
        ax2.add_patch(Rectangle((x + 2.6, 15), w - 5.2, 2.6, fc=FAINT,
                                ec="none", zorder=2))
        ax2.add_patch(Rectangle((x + 2.6, 15), (w - 5.2) * frac, 2.6, fc=col,
                                ec="none", zorder=3))
        ax2.text(x + w / 2, 11.2, "distance travelled, schematic",
                 color=DIM, fontsize=6.6, ha="center", va="center")
        x += w + 1.4

    save(fig, "nitrogen_fixation.png")


# ------------------------------------------------------------ running shoe --
# The materials, and the colour each is drawn in. Kept in one place because
# the legend, the shoe drawings and the end-of-life panel must agree; three
# separate colour lists would drift apart on the first edit.
MAT = {
    "mesh":    ("#5aa8d8", "Engineered mesh upper — polyester, often recycled"),
    "tpu":     ("#8b7ff2", "TPU overlays, heel counter, eyestays"),
    "eva":     ("#4f9d84", "EVA midsole foam — ethylene-vinyl acetate"),
    "peba":    ("#e0736f", "PEBA / supercritical foam — the fast, light one"),
    "tpufoam": ("#c98fd8", "eTPU midsole foam — expanded polyurethane beads"),
    "plate":   ("#e8c98f", "Carbon-fibre plate"),
    "rubber":  ("#6c7488", "Outsole rubber — carbon or blown"),
    "mono":    ("#8b7ff2", "One polymer family throughout — TPU"),
}


def shoe(ax, x0, y0, w, h, layers, plate=False, lugs=False, label="",
         mono=False):
    """One running shoe in side profile, toe to the right.

    The outline is sampled from functions rather than placed by hand: the
    stack height falls from heel to forefoot by a real drop, the toe springs
    up, and the upper is a single curve over the instep. Drawing it this way
    means the three shoes differ only in the numbers that actually differ
    between them, which is the point of putting them side by side.
    """
    import numpy as np
    n = 160
    t = np.linspace(0, 1, n)                      # 0 heel, 1 toe
    xs = x0 + t * w

    heel_h, fore_h = layers["heel"], layers["fore"]
    # Ground line: flat under the foot, springing up only in the last fifth
    # at the toe. An earlier version applied the spring across half the
    # length, which tilted the whole shoe and made it read as a doorstop.
    bot = (0.02 + 0.16 * np.clip((t - 0.84) / 0.16, 0, 1) ** 2.2) * h
    smooth = t * t * (3 - 2 * t)                  # smoothstep, heel to toe
    stack = (heel_h + (fore_h - heel_h) * smooth) * h
    # round the sole off at both ends rather than cutting it square
    edge = np.clip(np.minimum(t / 0.05, (1 - t) / 0.045), 0, 1) ** 0.5
    stack = stack * (0.35 + 0.65 * edge)
    top = bot + stack

    def band(lo_f, hi_f, colour, z=2):
        lo = bot + stack * lo_f
        hi = bot + stack * hi_f
        ax.fill_between(xs, y0 + lo, y0 + hi, color=colour, lw=0, zorder=z)

    # outsole, then whatever foams the shoe carries, in order. The
    # single-polymer shoe has no rubber: its outsole is a harder grade of
    # the same polymer, which is the entire point of it.
    band(0.0, 0.18, MAT["mono" if mono else "rubber"][0], z=3)
    cuts = layers["foams"]                        # [(fraction, material), ...]
    lo = 0.18
    for frac, mat in cuts:
        band(lo, lo + frac * 0.82, MAT[mat][0])
        lo += frac * 0.82
    if plate:
        pf = 0.18 + 0.82 * 0.42
        ax.plot(xs, y0 + bot + stack * pf, color=MAT["plate"][0], lw=1.9,
                zorder=4, solid_capstyle="round")
    if lugs:
        for k in range(9):
            xk = x0 + w * (0.08 + k * 0.098)
            ax.add_patch(Rectangle((xk, y0 + 0.005 * h), w * 0.045,
                                   0.055 * h, fc=MAT["rubber"][0], ec="none",
                                   zorder=4))

    # The upper: a tall ankle collar at the heel falling away along the
    # instep to a low, rounded toe box, and closing to nothing at both ends
    # so the shoe has a back and a front rather than two vertical cuts.
    # Collar, lace throat, toe box — the same three terms the interactive
    # model uses, so the flat figure and the 3D one are the same shoe.
    up = (0.34 - 0.10 * t
          + 0.50 * np.exp(-((t - 0.14) / 0.11) ** 2)
          - 0.16 * np.exp(-((t - 0.48) / 0.16) ** 2)
          + 0.06 * np.exp(-((t - 0.80) / 0.14) ** 2)) * h
    up *= np.clip(t / 0.06, 0, 1) ** 0.5             # round the heel back
    up *= np.clip((1 - t) / 0.055, 0, 1) ** 0.4      # round the toe
    ax.fill_between(xs, y0 + top, y0 + top + up,
                    color=MAT["mono" if mono else "mesh"][0],
                    lw=0, zorder=2, alpha=0.95)
    # The heel counter wraps the bottom of the collar, not all of it, and
    # the toe bumper follows the same outline instead of standing proud of
    # it, which is what made the toe hook upward.
    hc = (t < 0.15) & (not mono)
    ax.fill_between(xs[hc], y0 + top[hc], y0 + top[hc] + up[hc] * 0.62,
                    color=MAT["tpu"][0], lw=0, zorder=3)
    tb = (t > 0.93) & (not mono)
    ax.fill_between(xs[tb], y0 + top[tb], y0 + top[tb] + up[tb],
                    color=MAT["tpu"][0], lw=0, zorder=3)
    # the bonded seam every one of these shoes has
    ax.plot(xs, y0 + top, color="#0a0d18", lw=0.9, zorder=5)

    ax.text(x0 + w / 2, y0 - 0.20 * h, label, color=INK, fontsize=8.6,
            ha="center", va="top", fontweight="600")


def fig_shoe():
    import numpy as np
    fig = plt.figure(figsize=(11.6, 8.2), facecolor=BG)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 0.78],
                          left=0.045, right=0.975, top=0.86, bottom=0.05,
                          hspace=0.36)

    fig.text(0.045, 0.968, "What a running shoe is made of, and why that is "
                           "the recycling problem",
             color=INK, fontsize=18.5, fontweight="600", va="top")
    fig.text(0.045, 0.928,
             "Four constructions in side profile. In the first three every "
             "layer is a different polymer, bonded to the next.\nThe fourth "
             "is the alternative: one polymer family, welded like to like.",
             color=DIM, fontsize=10.4, va="top", linespacing=1.5)

    ax = fig.add_subplot(gs[0])
    panel(ax, "")
    ax.set_ylim(0, 100)

    # Stack heights are in units of the drawing height, and they carry the
    # real proportions: a racer's stack is near the 40 mm World Athletics
    # limit and a trail shoe sits lower than a daily trainer. The four
    # constructions are the four in the interactive model, in the same order.
    shoe(ax, 1, 52, 21, 40,
         {"heel": 0.34, "fore": 0.25, "foams": [(1.0, "eva")]},
         label="Daily trainer\nEVA midsole")
    shoe(ax, 26, 52, 21, 40,
         {"heel": 0.46, "fore": 0.36,
          "foams": [(0.62, "peba"), (0.38, "eva")]}, plate=True,
         label="Racing shoe\nPEBA + carbon plate")
    shoe(ax, 51, 52, 21, 40,
         {"heel": 0.30, "fore": 0.24,
          "foams": [(0.55, "tpufoam"), (0.45, "eva")]}, lugs=True,
         label="Trail shoe\neTPU and EVA, lugs")
    shoe(ax, 76, 52, 21, 40,
         {"heel": 0.32, "fore": 0.25, "foams": [(1.0, "mono")]}, mono=True,
         label="Single-polymer\none family, welded")

    # one legend, shared, since the colours are shared
    for i, key in enumerate(["mesh", "tpu", "eva", "peba", "tpufoam",
                             "plate", "rubber", "mono"]):
        col, name = MAT[key]
        cx = 2 + (i % 2) * 49
        cy = 24 - (i // 2) * 6.0
        ax.add_patch(Rectangle((cx, cy), 2.4, 2.4, fc=col, ec="none",
                               zorder=3))
        ax.text(cx + 3.6, cy + 1.2, name, color=DIM, fontsize=8.3,
                va="center", ha="left")

    # ---- panel 2: end of life -----------------------------------------
    ax2 = fig.add_subplot(gs[1])
    panel(ax2, "At end of life",
          "A shoe is not one material with contaminants. It is six or seven "
          "polymers, bonded, none of which shares a recycling stream.")

    cols = [
        ("What happens now",
         "Most pairs are landfilled or\nburned. The MIT life-cycle study\n"
         "puts a pair at ~13.6 kg CO$_2$e,\nwith more than two thirds of it\n"
         "in manufacturing, not materials.",
         WARN),
        ("Why separation fails",
         # Per SHOE, not per pair. Cheah et al. 2013 (J Clean Prod 44:18-29):
         # "a single shoe can contain 65 discrete parts that require 360
         # processing steps for assembly". This figure and running-shoes.html
         # both said "per pair" until 2026-09-05, from citing the MIT press
         # release rather than the paper. Neither ships any more; corrected
         # anyway, because a wrong number in a retired file is a wrong number
         # someone later trusts.
         "65 discrete parts and 360-odd\nprocessing steps per shoe. Foam is\n"
         "glued to rubber, mesh is welded to\nTPU. No economical process\n"
         "separates them at scale.",
         WARN),
        ("What recycling means here",
         "Take-back schemes slice a shoe into\nthree coarse streams and grind\n"
         "each for track surfaces and matting.\nThat is downcycling: the crumb\n"
         "cannot become a shoe again.",
         GOLD),
        ("The fourth shoe",
         "One polymer family, welded like to\nlike, no adhesive — so the whole\n"
         "shoe is a single feedstock. Built and\nworn in beta programmes, never\n"
         "released as an ordinary product.",
         GREEN),
    ]
    x = 1.0
    for title, body, col in cols:
        w = 23.2
        ax2.add_patch(FancyBboxPatch((x, 6), w, 74,
                                     boxstyle="round,pad=0.6,rounding_size=2",
                                     fc="#0d1322", ec=RULE, lw=1.0, zorder=1))
        ax2.text(x + w / 2, 70, title, color=col, fontsize=9.4,
                 fontweight="600", ha="center", va="center")
        ax2.text(x + w / 2, 38, body, color=INK, fontsize=7.7, ha="center",
                 va="center", linespacing=1.7)
        x += w + 1.4

    save(fig, "running_shoe.png")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("  building climate research figures")
    fig_nitrogen()
    fig_shoe()
