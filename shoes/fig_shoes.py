"""
The four figures for site/shoes.html, drawn from outputs/shoes_payload.json.

  shoes_f1_measurements.png  every published advanced-footwear comparison,
                             as a dot with its standard deviation where one
                             was published and nothing where one was not
  shoes_f2_spread.png        the study means against the published individual
                             ranges, on ONE axis
  shoes_f3_mass.png          the per-100 g rule and the trial that contradicts
                             it, on a linear axis
  shoes_f4_time.png          the laboratory range through the assumed transfer,
                             against the two observed race intervals

Every colour, size and face comes from sitefig.py. Each figure is audited for
text that overlaps, runs off the canvas or falls under the site's size floor;
the build prints the count and it must be 0.

WHY THERE IS NO INTERACTIVE HERE, AND NO SHOE.
The project this replaced shipped a three.js exploded view of four shoe
archetypes. Stage 1 booted it in headless Chromium rather than reading it,
and photographed the opening state and the same model turned about 90
degrees: rotating it reveals no part the opening view does not already show,
it becomes less legible rather than more, and it does not read as a shoe from
any angle - the opening view reads as a chaise longue. The frames are in
03 RESEARCH/shoe/autopsy/. A code review passed that model; a screenshot did
not. So the moving picture is not rebuilt, and the argument here is a spread,
which is a still picture.

F2 IS THE HERO AND IT IS ONE AXES, DELIBERATELY.
Its two registers - the study means above, the individual ranges below -
share a single x-axis in a single Axes with a divider drawn between them,
rather than being two stacked subplots. Two subplots read as two charts, and
no audit on this site can catch "reads as two charts"; one Axes cannot
develop that fault. The fallback, if it ever stops cohering, is named in the
write-up: a single band with each individual range as a translucent extent
drawn behind its own study's mean dot.

FOOTNOTES SIT AT THE FIGURE'S LEFT EDGE.
Starting them at the axes' left margin cost 175-240px of a 714px canvas and
ran three of the four off the right-hand side. At 12px a line has room for
roughly 100 characters from x=0.045; keep them under that.

Run:  python3 fig_shoes.py
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
from matplotlib.lines import Line2D                          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
import sitefig                                               # noqa: E402
from sitefig import (ACC, BG, DIM, FAINT, FS_2, INK, MOSS, NOTES,   # noqa: E402
                     RULE, SLATE, fig_size, row_aspect)
from fig_floor import floor_problems                         # noqa: E402

PAYLOAD = os.path.join(HERE, "outputs", "shoes_payload.json")
OUT = os.path.join(ROOT, "site", "assets")

# The study -> colour map is data/studies.py's, carried through the payload.
# The figures never name a colour for a study themselves: one mapping, one
# place, because the figure this replaced kept its colours in three.
COLOURS = {"acc": ACC, "moss": MOSS, "slate": SLATE}


def audit(fig):
    """Text that overlaps other text, runs off the canvas or is under the
    size floor, plus the grid checks. The enumeration is
    build_atlas_figures.py's: every Text object explicitly, because findobj
    returns ticks that were never drawn."""
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
        except Exception:                                     # noqa: BLE001
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


def emit(fig, name):
    bad = audit(fig)
    sitefig.save(fig, os.path.join(OUT, name), close=False)
    plt.close(fig)
    flag = "  LAYOUT: " + "; ".join(bad[:3]) if bad else ""
    print(f"  {name:28s} {len(bad)} layout problems{flag}")
    return len(bad)


def bare(ax):
    """Spines off except the one the reader reads against."""
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_yticks([])
    ax.tick_params(axis="x", length=3, colors=DIM)
    ax.xaxis.set_ticks_position("bottom")


# ---------------------------------------------------------------- figure 1 --
def fig_measurements(P):
    """One row per published comparison: a dot at the point estimate, a bar
    for the standard deviation where the paper published one, and nothing
    where it did not.

    The bare rows are as much the finding as the spread is. No interval is
    ever drawn that a paper did not publish, and a standard deviation is
    never called a confidence interval; test_shoes.py asserts both against
    the drawn artists rather than against the intention.
    """
    rows = P["aft"]
    n = len(rows)
    s = P["spread"]
    w, h = fig_size(NOTES, row_aspect(n, row_px=34, header_px=132))
    fig, ax = plt.subplots(figsize=(w, h))
    fig.subplots_adjust(left=0.245, right=0.735, top=0.90, bottom=0.175)

    ax.set_xlim(0, 5.0)
    ax.set_ylim(n - 0.4, -1.5)
    bare(ax)
    ax.set_xticks([0, 1, 2, 3, 4, 5])
    ax.set_xticklabels(["0", "1", "2", "3", "4", "5%"], fontsize=FS_2)
    for gx in (1, 2, 3, 4, 5):
        ax.axvline(gx, color=FAINT, lw=0.8, zorder=0)

    left = ax.get_yaxis_transform()          # x in axes fraction, y in data
    for i, r in enumerate(rows):
        col = COLOURS[r["colour"]]
        if r["dispersion"] == "sd":
            ax.hlines(i, r["effect_pct"] - r["sd_pct"],
                      r["effect_pct"] + r["sd_pct"],
                      color=col, lw=2.2, alpha=0.55, zorder=2)
        ax.scatter([r["effect_pct"]], [i], s=34, color=col, zorder=3,
                   edgecolors=BG, linewidths=0.7)
        ax.text(-0.02, i, r["label"], transform=left, ha="right", va="center",
                fontsize=FS_2, color=INK)
        ax.text(1.02, i, f"{r['short']} · n={r['n']}", transform=left,
                ha="left", va="center", fontsize=FS_2, color=DIM)

    # Column headings as furniture, not as a panel label: this is a
    # single-panel figure, and those carry no title (see sitefig.panel).
    ax.text(-0.02, -1.15, "study", transform=left, ha="right", va="center",
            fontsize=FS_2, color=DIM)
    ax.text(1.02, -1.15, "comparison", transform=left, ha="left",
            va="center", fontsize=FS_2, color=DIM)
    ax.text(0.5, -1.15, "change in the energy cost of running", transform=left,
            ha="center", va="center", fontsize=FS_2, color=DIM)

    fig.text(0.045, 0.028,
             f"Bars are the standard deviation, for the {s['n_with_sd']} "
             f"comparisons that published one.\nThe other {s['n_without']} "
             f"published a mean and nothing else, and are a dot alone.",
             fontsize=FS_2, color=DIM, va="bottom", linespacing=1.5)
    return emit(fig, "shoes_f1_measurements.png")


# ---------------------------------------------------------------- figure 2 --
def fig_spread(P):
    """The hero. Study means above, published individual ranges below, one
    x-axis, one Axes, a divider between.

    Colour names the study; the row label names who was tested. The two Knopp
    rows are one paper and the two Barnes and Kilding rows another, which is
    why each pair shares a colour, and Barnes and Kilding's own point
    estimates carry that colour in the band above, so a reader can follow one
    study from its tight mean to its wide individuals.
    """
    means = P["aft"]
    ind = P["individual"]["rows"]
    n_ind = len(ind)

    w, h = fig_size(NOTES, 1.95)
    fig, ax = plt.subplots(figsize=(w, h))
    fig.subplots_adjust(left=0.33, right=0.965, top=0.95, bottom=0.19)

    lo_x, hi_x = -13.0, 13.0
    band_top = 6.4
    ax.set_xlim(lo_x, hi_x)
    ax.set_ylim(-n_ind - 0.7, band_top)
    bare(ax)
    ax.set_xticks([-10, -5, 0, 5, 10])
    ax.set_xticklabels(["-10", "-5", "0", "+5", "+10%"], fontsize=FS_2)

    # zero, emphasised: it is the line three of the four ranges cross
    ax.axvline(0, color=INK, lw=1.1, zorder=1)

    # ---- upper register: a stacked dot plot of the study means -------------
    # Dots stack where they would collide, so density is a count rather than
    # jitter, which would be position carrying no meaning.
    plot_px = (0.965 - 0.33) * w * 72.0
    bin_w = (hi_x - lo_x) * 7.5 / plot_px
    counts = {}
    for r in sorted(means, key=lambda d: d["effect_pct"]):
        b = round((r["effect_pct"] - lo_x) / bin_w)
        k = counts.get(b, 0)
        counts[b] = k + 1
        ax.scatter([r["effect_pct"]], [2.15 + k * 0.42], s=30,
                   color=COLOURS[r["colour"]], zorder=3,
                   edgecolors=BG, linewidths=0.7)

    left = ax.get_yaxis_transform()
    ax.text(-0.025, 3.0, f"the {P['spread']['n']} study means",
            transform=left, ha="right", va="center", fontsize=FS_2, color=INK)
    ax.text(-0.025, 2.2, f"{P['spread']['lo']:.1f}% to {P['spread']['hi']:.1f}%",
            transform=left, ha="right", va="center", fontsize=FS_2, color=DIM)

    ax.axhline(1.35, color=RULE, lw=0.9, zorder=1)

    # ---- lower register: the published individual ranges -------------------
    # The caption for this register clears the first bar by a full row: at
    # 24.6px per unit the earlier 0.35 gap was 9px and the audit caught it.
    for i, r in enumerate(ind):
        y = -i - 0.5
        ax.hlines(y, r["lo"], r["hi"], color=COLOURS[r["colour"]], lw=6.0,
                  alpha=0.85, zorder=2, capstyle="butt")
        ax.text(-0.025, y, f"{r['group']}, n={r['n']}", transform=left,
                ha="right", va="center", fontsize=FS_2, color=INK)

    ax.text(-0.025, 1.05, "individual runners, where", transform=left,
            ha="right", va="center", fontsize=FS_2, color=INK)
    ax.text(-0.025, 0.55, "a study reported them", transform=left,
            ha="right", va="center", fontsize=FS_2, color=INK)

    key = [Line2D([], [], color=ACC, lw=6, label="Barnes & Kilding 2019"),
           Line2D([], [], color=MOSS, lw=6, label="Knopp et al. 2023"),
           Line2D([], [], marker="o", ls="none", color=SLATE, markersize=6,
                  label="other studies")]
    lg = ax.legend(handles=key, loc="upper right", ncol=1, frameon=False,
                   handlelength=1.5, fontsize=FS_2)
    for t in lg.get_texts():
        t.set_color(DIM)

    fig.text(0.045, 0.025,
             f"Colour names the study: two rows sharing one come from one "
             f"paper.\n{P['individual']['n_spanning_zero']} of "
             f"{P['individual']['n']} published ranges cross zero; the widest "
             f"is {P['individual']['widest']:.1f} points.",
             fontsize=FS_2, color=DIM, va="bottom", linespacing=1.5)
    return emit(fig, "shoes_f2_spread.png")


# ---------------------------------------------------------------- figure 3 --
def fig_mass(P):
    """The per-100 g rule and the trial that contradicts it.

    Drawn as magnitudes of worsening, which is why the axis says "worsening":
    the payload keeps the sign convention - a mass row is negative because
    adding mass hurts - and the absolute value is taken once, here, with the
    axis label carrying the meaning.

    Linear, deliberately. A log axis would compress a gap of six to nine
    times into something that looks like ordinary disagreement, and the size
    of that gap is the whole reason the figure exists.
    """
    rows = [m for m in P["mass"] if m["measures"] != "time"]
    rows.sort(key=lambda m: abs(m["effect_pct"]))
    n = len(rows)
    w, h = fig_size(NOTES, row_aspect(n, row_px=44, header_px=150))
    fig, ax = plt.subplots(figsize=(w, h))
    fig.subplots_adjust(left=0.30, right=0.735, top=0.88, bottom=0.30)

    ax.set_xlim(0, 11.2)
    ax.set_ylim(n - 0.45, -0.65)
    bare(ax)
    ax.set_xticks([0, 2, 4, 6, 8, 10])
    ax.set_xticklabels(["0", "2", "4", "6", "8", "10%"], fontsize=FS_2)
    for gx in (2, 4, 6, 8, 10):
        ax.axvline(gx, color=FAINT, lw=0.8, zorder=0)

    left = ax.get_yaxis_transform()
    for i, m in enumerate(rows):
        v = abs(m["effect_pct"])
        col = ACC if m["study"] == "hoogkamer2016" else MOSS
        if m["ci_pct"] is not None:
            lo, hi = sorted(abs(c) for c in m["ci_pct"])
            ax.hlines(i, lo, hi, color=col, lw=2.4, alpha=0.6, zorder=2)
            ax.vlines([lo, hi], i - 0.13, i + 0.13, color=col, lw=1.4, zorder=2)
            tag = f"{v:.2f}%  95% CI {lo:.2f}–{hi:.2f}"
        else:
            tag = f"{v:.2f}%  ×{m['ratio_to_rule']:.1f} the rule"
        ax.scatter([v], [i], s=36, color=col, zorder=3, edgecolors=BG,
                   linewidths=0.7)
        ax.text(-0.025, i, m["label"], transform=left, ha="right",
                va="center", fontsize=FS_2, color=INK)
        ax.text(-0.025, i + 0.30, m["short"], transform=left, ha="right",
                va="center", fontsize=FS_2, color=DIM)
        ax.text(1.03, i, tag, transform=left, ha="left", va="center",
                fontsize=FS_2, color=DIM)

    ax.text(0.5, -0.5, "worsening per 100 g added per shoe", transform=left,
            ha="center", va="center", fontsize=FS_2, color=DIM)
    fig.text(0.045, 0.04,
             "Both are peer-reviewed and neither is retracted. The interval "
             "on the first row\nis the only confidence interval published "
             "anywhere in this table.",
             fontsize=FS_2, color=DIM, va="bottom", linespacing=1.5)
    return emit(fig, "shoes_f3_mass.png")


# ---------------------------------------------------------------- figure 4 --
def fig_time(P):
    """The laboratory range carried through the transfer coefficient, against
    the two intervals observed in actual races.

    Solid means measured. The outlined bar is derived through an assumption
    and is drawn differently for that reason alone: the coefficient was
    measured for added mass over 3000 m in trained men, and applying it to
    advanced footwear over a marathon has never been tested.

    The overlap is consistency, not confirmation. The race estimates are
    observational - runners chose their own shoes and the fastest adopted
    them first - so they cannot validate the coefficient, and the figure's
    own footnote says so rather than leaving it to the caption.
    """
    pred = P["predicted"]
    rows = [dict(lo=pred["lo"], hi=pred["hi"],
                 label="predicted from the laboratory range",
                 sub="through the transfer coefficient", assumed=True)]
    for r in P["race"]:
        rows.append(dict(lo=r["lo"], hi=r["hi"], label=r["short"],
                         sub="marathon finishing times", assumed=False))
    n = len(rows)

    w, h = fig_size(NOTES, row_aspect(n, row_px=44, header_px=150))
    fig, ax = plt.subplots(figsize=(w, h))
    fig.subplots_adjust(left=0.335, right=0.775, top=0.88, bottom=0.30)

    ax.set_xlim(0, 3.6)
    ax.set_ylim(n - 0.45, -0.65)
    bare(ax)
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xticklabels(["0", "1", "2", "3%"], fontsize=FS_2)
    for gx in (1, 2, 3):
        ax.axvline(gx, color=FAINT, lw=0.8, zorder=0)

    left = ax.get_yaxis_transform()
    for i, r in enumerate(rows):
        if r["assumed"]:
            ax.hlines(i, r["lo"], r["hi"], color=ACC, lw=1.3, ls=(0, (4, 2)),
                      zorder=2)
            ax.vlines([r["lo"], r["hi"]], i - 0.16, i + 0.16, color=ACC,
                      lw=1.3, zorder=2)
            tag = f"{r['lo']:.1f} – {r['hi']:.1f}%  assumed"
        else:
            ax.hlines(i, r["lo"], r["hi"], color=ACC, lw=6.5, alpha=0.85,
                      zorder=2, capstyle="butt")
            tag = f"{r['lo']:.1f} – {r['hi']:.1f}%"
        ax.text(-0.025, i, r["label"], transform=left, ha="right",
                va="center", fontsize=FS_2, color=INK)
        ax.text(-0.025, i + 0.30, r["sub"], transform=left, ha="right",
                va="center", fontsize=FS_2, color=DIM)
        ax.text(1.03, i, tag, transform=left, ha="left", va="center",
                fontsize=FS_2, color=DIM)

    ax.text(0.5, -0.5, "faster, as race time", transform=left, ha="center",
            va="center", fontsize=FS_2, color=DIM)
    fig.text(0.045, 0.04,
             "The dashed row is derived, not measured. The solid rows are "
             "observational: runners\nchose their own shoes and the fastest "
             "adopted first, so this is consistency, not proof.",
             fontsize=FS_2, color=DIM, va="bottom", linespacing=1.5)
    return emit(fig, "shoes_f4_time.png")


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    sitefig.style()
    bad = fig_measurements(P) + fig_spread(P) + fig_mass(P) + fig_time(P)
    print(f"  {bad} layout problems in all")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
