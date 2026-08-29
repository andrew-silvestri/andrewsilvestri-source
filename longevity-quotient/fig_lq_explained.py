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
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
from matplotlib.patches import Circle    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")

# Site palette. No amber anywhere: these figures sit on a violet page.
INK = "#e3e6f2"
DIM = "#8b93b0"
FAINT = "#232a45"
BG = "#0b0f1c"
ACC = "#8b7ff2"       # violet, for what was observed
COOL = "#5aa8d8"      # blue
MOSS = "#4f9d84"      # green
ROSE = "#d86a86"      # rose, for falling short

SUBJECTS = ["Human", "Greenland shark", "African bush elephant"]


def style():
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG,
        "savefig.facecolor": BG,
        "text.color": INK, "axes.labelcolor": INK,
        "xtick.color": DIM, "ytick.color": DIM,
        "axes.edgecolor": FAINT, "grid.color": FAINT,
        "font.size": 10.5,
        "font.family": ["DejaVu Sans"],
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

    fig = plt.figure(figsize=(12.4, 8.2))
    # The header strip is reserved rather than hoped for: three lines of text
    # at the top of a figure will happily sit on the first row of axes unless
    # the layout is told they exist.
    gs = fig.add_gridspec(
        3, 3, height_ratios=[1.45, 1.0, 0.40],
        hspace=0.42, wspace=0.15,
        left=0.078, right=0.975, top=0.775, bottom=0.055)

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
                fontsize=14, color=INK)
        ax.text(0, 2.44,
                f"{kg:,.0f} kg" if kg >= 1 else f"{r['mass_g']:,.0f} g",
                ha="center", va="top", fontsize=11.5, color=DIM)
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
                ha="center", fontsize=10.5, color=DIM)
        ax.text(1, obs[i] + ymax * 0.035, f"{obs[i]:.0f} yr", ha="center",
                fontsize=11.5, color=colours[i] if good else ROSE)

        ax.set_xticks([0, 1])
        ax.set_xticklabels(["predicted\nfrom mass", "actually\nobserved"],
                           fontsize=10, color=DIM)
        ax.set_ylim(0, ymax)
        ax.set_xlim(-0.62, 1.62)
        for s in ("top", "right", "bottom"):
            ax.spines[s].set_visible(False)
        ax.spines["left"].set_color(FAINT)
        ax.tick_params(axis="x", length=0)
        if i == 0:
            ax.set_ylabel("maximum lifespan (years)", fontsize=10.5,
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
                fontsize=23, color=col, transform=ax.transAxes)
        verdict = (f"lives {lq[i]:.1f} times longer than its size predicts"
                   if lq[i] >= 1.05 else
                   f"lives {1 / lq[i]:.1f} times shorter than its size "
                   f"predicts" if lq[i] <= 0.95 else
                   "lives about exactly as long as its size predicts")
        ax.text(0.5, 0.10, verdict, ha="center", va="center",
                fontsize=10.5, color=DIM, transform=ax.transAxes)

    fig.text(0.078, 0.972, "What a longevity quotient is",
             fontsize=18, color=INK, ha="left", va="top")
    fig.text(0.078, 0.925,
             "Mass rises left to right, and so does the prediction, because "
             "the fit can only go up. What the animals do is not monotonic.",
             fontsize=11.5, color=DIM, ha="left", va="top")
    fig.text(0.078, 0.888,
             "The quotient is what is left once size has been divided out.",
             fontsize=11.5, color=DIM, ha="left", va="top")
    fig.text(0.078, 0.848,
             f"predicted lifespan  =  10^({a:.3f} + {b:.3f} × log\u2081\u2080 "
             "mass in grams)          LQ  =  observed \u00f7 predicted",
             fontsize=11.5, color=COOL, ha="left", va="top",
             family="DejaVu Sans")

    out = path or os.path.join(OUT, "fig0_lq_explained.png")
    bad = audit(fig)
    fig.savefig(out, dpi=170)
    plt.close(fig)
    if bad:
        print("  LAYOUT PROBLEMS")
        for line in bad:
            print("    " + line)
    return out, list(zip([r["name"] for r in picked], pred, obs, lq)), bad


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
    for ax in fig.axes:
        for t in [ax.title, ax.xaxis.label, ax.yaxis.label] + list(ax.texts):
            if t.get_text().strip():
                items.append(t)
        if ax.axison:
            for t in ax.get_xticklabels() + ax.get_yticklabels():
                if t.get_text().strip() and t.get_visible():
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
    return out


if __name__ == "__main__":
    import build_lq
    rows, summary = build_lq.build()
    out, table, bad = explain(rows, summary)
    print("\n  " + out)
    print(f"  {'species':24s} {'predicted':>10s} {'observed':>10s} {'LQ':>7s}")
    for name, p, o, q in table:
        print(f"  {name:24s} {p:10.1f} {o:10.1f} {q:7.2f}")
    print(f"\n  layout audit: {len(bad)} problem(s)")
    raise SystemExit(1 if bad else 0)
