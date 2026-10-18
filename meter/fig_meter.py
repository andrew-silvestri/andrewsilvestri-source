"""Draw the meter page's three figures from outputs/payload.json, each twice:
at 714 CSS px for the page and at 350 for the phone column (HANDOFF trap 22),
straight into site/assets/.

  meter_budget       one meter's standard uncertainty, input by input
  meter_floor        what averages away with more meters and what does not
  meter_imbalance    the default system's imbalance, in the three C-sharing cases

Every figure ends in audit(): nothing under the 12px floor, nothing off the
canvas, no two labels overlapping, and a sheet's panels in columns. The
builder exits 1 on any problem.

Run:  python fig_meter.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # see build_allocation_figure.py

import matplotlib                        # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402

import sitefig                           # noqa: E402
from sitefig import (ACC, MOSS, COOL, DIM, INK, RULE, FAINT, FS_2, FS_1, NOTES, PHONE,  # noqa: E402
                     fig_size, save)
from fig_floor import floor_problems     # noqa: E402

PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ASSETS = os.path.join(ROOT, "site", "assets")

LABELS = {"C": "Discharge coefficient", "dp": "Differential pressure", "p1": "Static pressure",
          "T1": "Temperature", "d": "Bore diameter", "D": "Pipe diameter",
          "composition": "Gas composition", "Z": "Compressibility equation"}
CASES = [("fC0", COOL, "C errors independent"),
         ("fC1", MOSS, "C shared, both ends alike"),
         ("fC1r", ACC, "C shared, ends apart")]
SHORT = {"C": "Discharge coeff.", "dp": "Differential press.", "p1": "Static pressure",
         "T1": "Temperature", "d": "Bore diameter", "D": "Pipe diameter",
         "composition": "Composition", "Z": "Compressibility"}


def audit(fig, texts):
    """The sibling builders' checks (climate-cost/build_allocation_figure.py's shape)."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    items = [(t, False) for t in texts]
    for ax in fig.axes:
        items += [(t, True) for t in sitefig.titles(ax)]
        lo, hi = ax.get_xlim()
        items += [(t, False) for t in ax.get_xticklabels() if min(lo, hi) <= t.get_position()[0] <= max(lo, hi)]
        lo, hi = ax.get_ylim()
        items += [(t, False) for t in ax.get_yticklabels() if min(lo, hi) <= t.get_position()[1] <= max(lo, hi)]
        items += [(ax.xaxis.label, False), (ax.yaxis.label, False)]
        lg = ax.get_legend()
        if lg is not None:
            items += [(t, False) for t in lg.get_texts()]
    problems = floor_problems(fig, items) + sitefig.grid_problems(fig)
    W, H = fig.get_size_inches() * fig.dpi
    boxes = []
    for t, _ in items:
        if not t.get_text().strip() or not t.get_visible():
            continue
        b = t.get_window_extent(renderer=r)
        if b.x0 < -1 or b.y0 < -1 or b.x1 > W + 1 or b.y1 > H + 1:
            problems.append(f"off canvas: {t.get_text()[:30]!r}")
        boxes.append((b, t.get_text()[:30]))
    for ax in fig.axes:
        lg = ax.get_legend()
        if lg is not None:
            boxes.append((lg.get_window_extent(renderer=r), "legend"))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][0], boxes[j][0]
            if a.overlaps(b) and boxes[i][1] != boxes[j][1]:
                if "legend" in (boxes[i][1], boxes[j][1]):
                    # a legend's own entries sit inside its box: not a collision
                    other = boxes[j] if boxes[i][1] == "legend" else boxes[i]
                    if any(other[1] == t.get_text()[:30] for ax in fig.axes if ax.get_legend()
                           for t in ax.get_legend().get_texts()):
                        continue
                problems.append(f"overlap: {boxes[i][1]!r} / {boxes[j][1]!r}")
    return problems


def pct_axis(ax, axis="x"):
    f = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}%")
    (ax.xaxis if axis == "x" else ax.yaxis).set_major_formatter(f)


# ----------------------------------------------------------------- figure 1
def budget(P, width, out):
    s = P["single"]
    groups = sorted((g for g in LABELS), key=lambda g: s[g]["u"])
    n = len(groups) + 1
    sitefig.style()
    fig = plt.figure(figsize=fig_size(width, sitefig.row_aspect(n, row_px=30 if width == PHONE else 26,
                                                                display_px=width, header_px=70)))
    left = 0.42 if width == PHONE else 0.30
    ax = fig.add_axes([left, 0.16, 0.95 - left - (0.12 if width == PHONE else 0.10), 0.80])
    names = (SHORT if width == PHONE else LABELS)
    vals = [s[g]["u"] * 100 for g in groups] + [s["all"]["u"] * 100]
    labs = [names[g] for g in groups] + ["All together"]
    cols = [COOL] * len(groups) + [ACC]
    y = np.arange(n)
    ax.barh(y, vals, color=cols, height=0.62)
    ax.set_yticks(y, labs)
    texts = []
    for yi, v, g in zip(y, vals, groups + ["all"]):
        d = s[g]["delta"] * 100
        dec = max(0, -int(np.floor(np.log10(d))) if d > 0 else 3)
        texts.append(ax.text(v + max(vals) * 0.015, yi, f"{v:.{dec}f}%", va="center", fontsize=FS_2, color=INK))
    ax.set_xlim(0, max(vals) * 1.22)
    pct_axis(ax)
    ax.set_xlabel("Standard uncertainty of the meter's flow")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0)
    sitefig.centre(fig)
    problems = audit(fig, texts)
    size = save(fig, out)
    return size, problems


# ----------------------------------------------------------------- figure 2
def floor(P, width, out):
    sw = P["sweep"]
    N = np.array(sw["N"])
    sitefig.style()
    phone = width == PHONE
    fig = plt.figure(figsize=fig_size(width, 0.72 if phone else 1.15))
    l, r = (0.20, 0.95) if phone else (0.13, 0.97)
    axes = [fig.add_axes([l, 0.58, r - l, 0.33]), fig.add_axes([l, 0.12, r - l, 0.33])]
    texts = []
    for ax, key, lab in ((axes[0], "u_total", "A  Total measured throughput"),
                         (axes[1], "u_imb", "B  Receipts minus deliveries")):
        for fC, col, name in CASES:
            u = np.array([row[key] for row in sw[fC]]) * 100
            ax.plot(N, u, color=col, lw=2.2, marker="o", ms=4, label=name)
        ax.set_xscale("log")
        ax.set_xticks([1, 10, 100], ["1", "10", "100"])
        ax.set_ylim(0, None)
        pct_axis(ax, "y")
        sitefig.panel(ax, lab, pad=8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.grid(axis="y", lw=0.6)
    axes[1].set_xlabel("Number of receipt meters")
    axes[0].legend(loc="upper right", frameon=False, fontsize=FS_2)
    sitefig.centre(fig)
    problems = audit(fig, texts)
    size = save(fig, out)
    return size, problems


# ----------------------------------------------------------------- figure 3
def imbalance(P, width, out):
    sitefig.style()
    phone = width == PHONE
    fig = plt.figure(figsize=fig_size(width, 1.1 if phone else 16 / 8))
    ax = fig.add_axes([0.10 if not phone else 0.14, 0.20 if not phone else 0.24, 0.86 if not phone else 0.80,
                       0.72 if not phone else 0.62])
    for fC, col, name in CASES:
        h = P["system"][fC]["hist"]
        e = np.array(h["edges_pct"])
        c = np.array(h["counts"]) / h["n"] / np.diff(e)
        ax.stairs(c, e, color=col, lw=2.2, label=name)
    lo, hi = -1.0, 1.0
    ax.set_xlim(lo, hi)
    ax.set_ylim(0, None)
    ax.set_yticks([])
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    pct_axis(ax)
    ax.set_xlabel("Measured imbalance, energy, share of throughput")
    ax.axvline(0, color=RULE, lw=1)
    ax.legend(loc="upper right", frameon=False, fontsize=FS_2)
    sitefig.centre(fig)
    problems = audit(fig, [])
    size = save(fig, out)
    return size, problems


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    problems = []
    for name, fn in (("meter_budget", budget), ("meter_floor", floor), ("meter_imbalance", imbalance)):
        for width, suffix in ((NOTES, ""), (PHONE, "-phone")):
            out = os.path.join(ASSETS, f"{name}{suffix}.png")
            size, p = fn(P, width, out)
            print(f"written {out} ({size / 1024:.0f} kB)")
            problems += [f"{name}{suffix}: {x}" for x in p]
    if problems:
        print("audit:")
        for p in problems:
            print("  " + p)
        return 1
    print("audit: 0 problems")
    return 0


if __name__ == "__main__":
    sys.exit(main())
