"""
One figure that explains what a longevity quotient is.

The quotient is a simple idea buried under an unfamiliar word, and the fastest
way through is three animals of increasing size, because the argument only
works if you can see the sizes.

Body mass predicts lifespan. It is one of the most reliable relationships in
comparative biology and it runs across fourteen orders of magnitude, from a
rotifer to a bowhead whale. But it is a weak function - lifespan goes up
roughly as the sixth root of mass on this data set, so a thousandfold increase
in mass buys about a threefold increase in life. The prediction therefore rises
slowly and monotonically with size, and it has no choice about it: give the
regression a heavier animal and it returns a longer life, every time.

Reality is not monotonic, and that is the whole point. Between a human, a
Greenland shark and an elephant, mass rises by a factor of sixty-five and the
prediction rises politely along with it. What the animals actually do is go up,
up much further, and then fall back. The elephant is the heaviest of the three
and the least remarkable: it lives roughly the life its size buys, while the
shark, a fifth of its mass, beats its prediction eightfold.

These numbers move when the data behind them moves, which is why the figure is
drawn from the built model rather than typed. Widening the table from 417
species to 7,872 lowered the fitted intercept by a quarter, because the small
curated set over-sampled famous long-lived animals and the regression had been
quietly reading that bias as biology.

The quotient is the ratio between those two columns. It is the same
construction as Jerison's encephalisation quotient, which asks not how large a
brain is but how large it is for the body carrying it. Divide out the thing
everybody already knows, and look at what is left.

The three animals are drawn as spheres of the right relative volume, because
mass is what goes into the regression and a bar chart of masses spanning two
orders of magnitude tells you nothing you can see.

Run:  python3 fig_lq_explained.py
"""

import math
import os

import matplotlib
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from sitefig import BG, INK, DIM, RULE, FAINT, ACC, COOL, MOSS, ROSE, SLATE, DISTRICT, SUPPLY, PSYCH, SUN, INSOL, GOLD, GREY, VIOLET, BLUE, GREEN, WARM, ARROW, ONE_WAY_COL, TWO_WAY_COL, NODE_COL, WARM2, KCOL, CYCLE, FS_2, FS_1, FS0, FS1, FS2, FONT, MONO, NOTES, PROSE, CARD, THUMB, fig_size, save, WIDE, PLOT, SQUARE, TALL, row_aspect, panel  # noqa: E402,F401
import sitefig  # noqa: E402

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
import sys
if hasattr(sys, "stdout") and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
from matplotlib.patches import Circle    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")

# Site palette. No amber anywhere: these figures sit on a violet page.

SUBJECTS = ["Human", "Greenland shark", "African bush elephant"]


def style():
    sitefig.style(); plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG,
        "savefig.facecolor": BG,
        "text.color": INK, "axes.labelcolor": INK,
        "xtick.color": DIM, "ytick.color": DIM,
        "axes.edgecolor": FAINT, "grid.color": FAINT,
        "font.size": FS_1,
        "font.family": FONT,
    })


def explain(rows, summary, path=None):
    """Draw the explainer from the built model, so the numbers on it are the
    numbers the model actually holds rather than a transcription of them."""
    style()
    a = summary["global_fit"]["a"]
    b = summary["global_fit"]["b"]

    by_name = {r["name"]: r for r in rows}
    picked = [by_name[n] for n in SUBJECTS if n in by_name]
    if len(picked) < 3:
        raise SystemExit("explainer needs " + ", ".join(SUBJECTS))
    picked.sort(key=lambda r: r["mass_g"])

    colours = [COOL, MOSS, ACC]
    obs = [r["maximum"] for r in picked]
    pred = [10 ** (a + b * math.log10(r["mass_g"])) for r in picked]
    lq = [o / p for o, p in zip(obs, pred)]

    fig = plt.figure(figsize=fig_size(NOTES, 1.15))
    # The header strip is reserved rather than hoped for: three lines of text
    # at the top of a figure will happily sit on the first row of axes unless
    # the layout is told they exist.
    gs = fig.add_gridspec(
        3, 3, height_ratios=[1.45, 1.0, 0.55],
        hspace=0.42, wspace=0.15,
        left=0.078, right=0.975, top=0.82, bottom=0.04)

    # --- row 1: the animals, drawn as spheres of the right relative volume --
    # radius goes as the cube root of mass, since an animal is about the
    # density of water. The three axes share limits, so the sizes are
    # comparable across panels and not merely decorative.
    rmax = max(r["mass_g"] for r in picked) ** (1 / 3)
    for i, r in enumerate(picked):
        ax = fig.add_subplot(gs[0, i])
        rad = r["mass_g"] ** (1 / 3) / rmax
        ax.add_patch(Circle((0, rad), rad, facecolor=colours[i],
                            alpha=0.30, edgecolor=colours[i], lw=1.6))
        ax.set_xlim(-1.20, 1.20)
        # the largest sphere reaches y = 2.0, so the labels live above that
        ax.set_ylim(-0.10, 2.72)
        ax.set_aspect("equal")
        ax.axis("off")
        kg = r["mass_g"] / 1000.0
        ax.text(0, 2.70, r["name"], ha="center", va="top",
                fontsize=FS0, color=INK)
        ax.text(0, 2.44,
                f"{kg:,.0f} kg" if kg >= 1 else f"{r['mass_g']:,.0f} g",
                ha="center", va="top", fontsize=FS_1, color=DIM)
        ax.plot([-1.16, 1.16], [-0.06, -0.06], color=FAINT, lw=1)

    # --- row 2: what the allometry predicts, and what the animal does -------
    ymax = max(obs + pred) * 1.34
    for i, r in enumerate(picked):
        ax = fig.add_subplot(gs[1, i])
        ax.bar([0], [pred[i]], width=0.56, color="none",
               edgecolor=DIM, lw=1.5, linestyle="--")
        good = lq[i] >= 1
        ax.bar([1], [obs[i]], width=0.56,
               color=colours[i] if good else ROSE, alpha=0.92)

        ax.text(0, pred[i] + ymax * 0.035, f"{pred[i]:.0f} yr",
                ha="center", fontsize=FS_1, color=DIM)
        ax.text(1, obs[i] + ymax * 0.035, f"{obs[i]:.0f} yr", ha="center",
                fontsize=FS_1, color=colours[i] if good else ROSE)

        ax.set_xticks([0, 1])
        ax.set_xticklabels(["predicted\nfrom mass", "actually\nobserved"],
                           fontsize=FS_1, color=DIM)
        ax.set_ylim(0, ymax)
        ax.set_xlim(-0.62, 1.62)
        for s in ("top", "right", "bottom"):
            ax.spines[s].set_visible(False)
        ax.spines["left"].set_color(FAINT)
        ax.tick_params(axis="x", length=0)
        if i == 0:
            ax.set_ylabel("maximum lifespan (years)", fontsize=FS_1,
                          color=DIM)
        else:
            ax.set_yticklabels([])
        ax.grid(axis="y", alpha=0.16)
        ax.set_axisbelow(True)

    # --- row 3: the quotient itself ----------------------------------------
    for i, r in enumerate(picked):
        ax = fig.add_subplot(gs[2, i])
        ax.axis("off")
        good = lq[i] >= 1
        col = colours[i] if good else ROSE
        ax.text(0.5, 0.66, f"LQ {lq[i]:.2f}", ha="center", va="center",
                fontsize=FS2, color=col, transform=ax.transAxes)
        # two lines: a third of 714 px holds about 30 characters at FS_2
        verdict = (f"lives {lq[i]:.1f} times longer\nthan its size predicts"
                   if lq[i] >= 1.05 else
                   f"lives {1 / lq[i]:.1f} times shorter\nthan its size predicts" if lq[i] <= 0.95 else
                   "lives about exactly as long\nas its size predicts")
        ax.text(0.5, 0.22, verdict, ha="center", va="center",
                fontsize=FS_2, color=DIM, transform=ax.transAxes, linespacing=1.35)

    # header lines broken to the 714 px width by hand: at one point per
    # pixel a line of FS_1 holds about 85 characters
    fig.text(0.078, 0.955,
             f"predicted lifespan  =  10^({a:.3f} + {b:.3f} × log₁₀ mass in grams)\n"
             "LQ  =  observed ÷ predicted",
             fontsize=FS_1, color=COOL, ha="left", va="top", linespacing=1.4, fontfamily=MONO)

    out = path or os.path.join(OUT, "fig0_lq_explained.png")
    sitefig.centre(fig)      # the grid's margins are a guess; this measures (2026-09-05)
    bad = audit(fig)
    sitefig.save(fig, out, close=False)
    plt.close(fig)
    if bad:
        print("  LAYOUT PROBLEMS")
        for line in bad:
            print("    " + line)
    return out, list(zip([r["name"] for r in picked], pred, obs, lq)), bad


def explain_phone(rows, summary, path=None):
    """The 350 render: a second figure, not a scaled one (Stage A, 2026-10-18).

    The page's caption says mass rises LEFT TO RIGHT, so the three animals stay
    in three columns here, as in the 714; a stacked layout with an animal per
    row made that sentence false and was dropped. What changes is what each
    ~98px column can hold. The names wrap to two lines. The "predicted from
    mass" / "actually observed" bar labels, which collided under every pair of
    bars, become one legend under the formula. The quotient drops a step to
    FS1, and the verdicts wrap to three lines, both to fit the column. The
    y label wraps after "lifespan". Same numbers and words; the spheres keep
    one scale; the formula breaks after its "=", because on one line it is
    wider than the column.
    """
    from matplotlib.patches import Patch
    import textwrap
    style()
    a = summary["global_fit"]["a"]
    b = summary["global_fit"]["b"]

    by_name = {r["name"]: r for r in rows}
    picked = [by_name[n] for n in SUBJECTS if n in by_name]
    if len(picked) < 3:
        raise SystemExit("explainer needs " + ", ".join(SUBJECTS))
    picked.sort(key=lambda r: r["mass_g"])

    colours = [COOL, MOSS, ACC]
    obs = [r["maximum"] for r in picked]
    pred = [10 ** (a + b * math.log10(r["mass_g"])) for r in picked]
    lq = [o / p for o, p in zip(obs, pred)]

    fig = plt.figure(figsize=fig_size(sitefig.PHONE, 0.72))
    gs = fig.add_gridspec(
        3, 3, height_ratios=[1.35, 1.0, 0.75],
        hspace=0.30, wspace=0.12, left=0.19, right=0.985, top=0.80, bottom=0.03)

    rmax = max(r["mass_g"] for r in picked) ** (1 / 3)
    for i, r in enumerate(picked):
        ax = fig.add_subplot(gs[0, i])
        rad = r["mass_g"] ** (1 / 3) / rmax
        ax.add_patch(Circle((0, rad), rad, facecolor=colours[i],
                            alpha=0.30, edgecolor=colours[i], lw=1.6))
        ax.set_xlim(-1.20, 1.20)
        ax.set_ylim(-0.10, 3.50)
        ax.set_aspect("equal")
        ax.axis("off")
        kg = r["mass_g"] / 1000.0
        ax.text(0, 3.50, "\n".join(textwrap.wrap(r["name"], 12)),
                ha="center", va="top", fontsize=FS_1, color=INK,
                linespacing=1.15)
        # Stood on a line just above the largest sphere's top (2.0) rather
        # than hung from 2.30: hung, "4,000 kg" sat on the elephant.
        ax.text(0, 2.15,
                f"{kg:,.0f} kg" if kg >= 1 else f"{r['mass_g']:,.0f} g",
                ha="center", va="bottom", fontsize=FS_2, color=DIM)
        ax.plot([-1.16, 1.16], [-0.06, -0.06], color=FAINT, lw=1)

    ymax = max(obs + pred) * 1.30
    for i, r in enumerate(picked):
        ax = fig.add_subplot(gs[1, i])
        good = lq[i] >= 1
        col = colours[i] if good else ROSE
        ax.bar([0], [pred[i]], width=0.6, color="none",
               edgecolor=DIM, lw=1.5, linestyle="--")
        ax.bar([1], [obs[i]], width=0.6, color=col, alpha=0.92)
        ax.text(0, pred[i] + ymax * 0.035, f"{pred[i]:.0f} yr",
                ha="center", fontsize=FS_2, color=DIM)
        ax.text(1, obs[i] + ymax * 0.035, f"{obs[i]:.0f} yr",
                ha="center", fontsize=FS_2, color=col)
        ax.set_xticks([])
        ax.set_ylim(0, ymax)
        ax.set_xlim(-0.55, 1.55)
        for s in ("top", "right", "bottom"):
            ax.spines[s].set_visible(False)
        ax.spines["left"].set_color(FAINT)
        if i == 0:
            ax.set_ylabel("maximum lifespan\n(years)", fontsize=FS_2,
                          color=DIM)
        else:
            ax.set_yticklabels([])
        ax.grid(axis="y", alpha=0.16)
        ax.set_axisbelow(True)

    for i, r in enumerate(picked):
        ax = fig.add_subplot(gs[2, i])
        ax.axis("off")
        good = lq[i] >= 1
        col = colours[i] if good else ROSE
        ax.text(0.5, 0.92, f"LQ {lq[i]:.2f}", ha="center", va="top",
                fontsize=FS1, color=col, transform=ax.transAxes)
        verdict = (f"lives {lq[i]:.1f} times longer than its size predicts"
                   if lq[i] >= 1.05 else
                   f"lives {1 / lq[i]:.1f} times shorter than its size predicts" if lq[i] <= 0.95 else
                   "lives about exactly as long as its size predicts")
        ax.text(0.5, 0.0, "\n".join(textwrap.wrap(verdict, 15)),
                ha="center", va="bottom", fontsize=FS_2, color=DIM,
                transform=ax.transAxes, linespacing=1.25)

    fig.legend(handles=[
        Patch(facecolor="none", edgecolor=DIM, lw=1.5, linestyle="--",
              label="predicted from mass"),
        Patch(facecolor=DIM, alpha=0.6, label="actually observed")],
        loc="upper left", bbox_to_anchor=(0.02, 0.905), ncol=2,
        fontsize=FS_2, frameon=False, handlelength=1.2, columnspacing=1.0,
        handletextpad=0.5)
    fig.text(0.02, 0.995,
             f"predicted lifespan  =\n10^({a:.3f} + {b:.3f} × log₁₀ mass in grams)\n"
             "LQ  =  observed ÷ predicted",
             fontsize=FS_2, color=COOL, ha="left", va="top", linespacing=1.35,
             fontfamily=MONO)

    out = path or os.path.join(OUT, "fig0_lq_explained-phone.png")
    sitefig.centre(fig)
    bad = audit(fig)
    sitefig.save(fig, out, close=False)
    plt.close(fig)
    if bad:
        print("  LAYOUT PROBLEMS (350)")
        for line in bad:
            print("    " + line)
    return out, bad


def audit(fig):
    """Report text that overlaps other text, or that runs off the canvas.

    Every Text object is enumerated explicitly rather than harvested with
    findobj, because matplotlib keeps Text objects for ticks it never drew and
    those report nonsense boxes. Only what is actually on the figure counts.
    """
    fig.canvas.draw()
    ren = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()

    items = []
    for t in fig.texts:
        if t.get_text().strip():
            items.append(t)
    # legend text is a separate artist (HANDOFF trap 4); the 350 render has a
    # figure legend, the 714 has none
    for lg in list(fig.legends) + [ax.get_legend() for ax in fig.axes]:
        if lg is not None:
            items += [t for t in lg.get_texts() if t.get_text().strip()]
    for ax in fig.axes:
        for t in sitefig.titles(ax) + [ax.xaxis.label, ax.yaxis.label] + list(ax.texts):
            if t.get_text().strip():
                items.append(t)
        if ax.axison:
            # A locator (log-scale ones especially) keeps Text objects for
            # ticks just past each edge for its own bookkeeping; they report
            # get_visible()==True without ever being drawn on the page, and
            # counting them invents off-canvas failures that are not real.
            for axis, getter, labeler in (
                (ax.xaxis, ax.get_xticks, ax.get_xticklabels),
                (ax.yaxis, ax.get_yticks, ax.get_yticklabels)):
                lo, hi = sorted(axis.get_view_interval())
                for loc, t in zip(getter(), labeler()):
                    if lo - 1e-9 <= loc <= hi + 1e-9 and \
                            t.get_text().strip() and t.get_visible():
                        items.append(t)

    boxes = []
    for t in items:
        try:
            bb = t.get_window_extent(renderer=ren)
        except Exception:
            continue
        boxes.append((t.get_text().replace("\n", " ")[:34], bb))

    out = []
    for label, bb in boxes:
        if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > W + 1 or bb.y1 > H + 1:
            out.append(f"off canvas: {label!r}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (la, a), (lb, b) = boxes[i], boxes[j]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0)
            oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ox <= 0 or oy <= 0:
                continue
            area = ox * oy
            frac = area / min(a.width * a.height, b.width * b.height)
            if frac > 0.12:
                out.append(f"overlap {frac:.0%}: {la!r} / {lb!r}")
    # Text on a sphere. A patch is not text, so the checks above never saw
    # one: the first 350 render of the explainer set "4,000 kg" on the
    # elephant's circle and reported 0 problems (2026-10-18, HANDOFF trap 4).
    # Exact circle-against-box, so a label beside a circle's bounding square
    # but clear of the circle itself is not a finding.
    for ax in fig.axes:
        for p in ax.patches:
            if not isinstance(p, Circle):
                continue
            cx, cy = ax.transData.transform(p.center)
            r = abs(ax.transData.transform((p.center[0] + p.radius, 0))[0]
                    - ax.transData.transform((p.center[0], 0))[0])
            for label, bb in boxes:
                nx = min(max(cx, bb.x0), bb.x1)
                ny = min(max(cy, bb.y0), bb.y1)
                if (nx - cx) ** 2 + (ny - cy) ** 2 < r * r:
                    out.append(f"text on shape: {label!r}")
    out += sitefig.grid_problems(fig)     # columns shared, content centred (2026-09-05)
    return out


if __name__ == "__main__":
    import build_lq
    rows, summary = build_lq.build()
    out, table, bad = explain(rows, summary)
    out_phone, bad_phone = explain_phone(rows, summary)
    bad = bad + bad_phone
    print("\n  " + out + "\n  " + out_phone)
    print(f"  {'species':24s} {'predicted':>10s} {'observed':>10s} {'LQ':>7s}")
    for name, p, o, q in table:
        print(f"  {name:24s} {p:10.1f} {o:10.1f} {q:7.2f}")
    print(f"\n  layout audit: {len(bad)} problem(s)")
    raise SystemExit(1 if bad else 0)
