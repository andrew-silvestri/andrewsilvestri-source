"""Draw the takeaway page's three figures from outputs/payload.json, each twice:
at 714 CSS px for the page and at 350 for the phone column (HANDOFF trap 22),
straight into site/assets/.

  takeaway_capacity   pipeline capacity out of the basin, confirmed and expected
  takeaway_headroom   pipe added less gas added, since the reference month
  takeaway_flaring    Texas vented or flared share of gross withdrawals

Every figure ends in audit(): nothing under the 12px floor, nothing off the
canvas, no two labels overlapping, no legend over data. The builder exits 1
on any problem.

Run:  python fig_takeaway.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib                        # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402

import sitefig                           # noqa: E402
from sitefig import ACC, MOSS, COOL, DIM, INK, RULE, FS_2, NOTES, PHONE, fig_size, save   # noqa: E402
from fig_floor import floor_problems     # noqa: E402

PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ASSETS = os.path.join(ROOT, "site", "assets")


def yr(key):
    """'2024-08' -> 2024.583, the month's start on a decimal-year axis."""
    y, m = key.split("-")
    return int(y) + (int(m) - 1) / 12


def audit(fig, texts):
    """The sibling builders' checks (meter/fig_meter.py's shape)."""
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
            lb = lg.get_window_extent(renderer=r)
            boxes.append((lb, "legend"))
            # A legend over plotted data hides it and no text check sees it
            # (meter/fig_meter.py found this twice): lines and patches both.
            drawn = [(a, ax.transData.transform(np.column_stack(a.get_data()))) for a in ax.get_lines()]
            drawn += [(a, a.get_transform().transform(a.get_path().vertices)) for a in ax.patches]
            for coll in ax.collections:
                for path in coll.get_paths():
                    drawn.append((coll, coll.get_transform().transform(path.vertices)))
            for artist, pts in drawn:
                label = artist.get_label() or ""
                if label.startswith("_"):
                    continue
                inside = ((pts[:, 0] >= lb.x0) & (pts[:, 0] <= lb.x1) &
                          (pts[:, 1] >= lb.y0) & (pts[:, 1] <= lb.y1))
                if inside.any():
                    problems.append(f"legend over data: {label!r}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][0], boxes[j][0]
            if a.overlaps(b) and boxes[i][1] != boxes[j][1]:
                if "legend" in (boxes[i][1], boxes[j][1]):
                    other = boxes[j] if boxes[i][1] == "legend" else boxes[i]
                    if any(other[1] == t.get_text()[:30] for ax in fig.axes if ax.get_legend()
                           for t in ax.get_legend().get_texts()):
                        continue
                problems.append(f"overlap: {boxes[i][1]!r} / {boxes[j][1]!r}")
    return problems


def tidy(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", lw=0.6)


def year_ticks(ax, a, b, step):
    ticks = list(range(a, b + 1, step))
    ax.set_xticks(ticks, [str(t) for t in ticks])


# ----------------------------------------------------------------- figure 1
def capacity_fig(P, width, out):
    phone = width == PHONE
    cap = P["capacity"]
    keys = sorted(cap)
    x = np.array([yr(k) for k in keys] + [yr(keys[-1]) + 1 / 12])
    def col(f):
        v = np.array([cap[k][f] for k in keys])
        return np.append(v, v[-1])
    sitefig.style()
    fig = plt.figure(figsize=fig_size(width, 0.95 if phone else 16 / 9))
    ax = fig.add_axes([0.16, 0.30, 0.80, 0.62] if phone else [0.09, 0.16, 0.88, 0.76])
    ax.fill_between(x, col("lo"), col("hi"), step="post", color=MOSS, alpha=0.30, lw=0,
                    label="With expected lines")
    ax.fill_between(x, col("lo_confirmed"), col("hi_confirmed"), step="post", color=ACC, alpha=0.85, lw=0,
                    label="In service")
    last = yr(P["steo"]["last_historical"])
    ax.axvline(last, color=DIM, lw=1, ls=(0, (2, 2)))
    texts = [ax.text(last - 0.08, 0.96, "latest data", transform=ax.get_xaxis_transform(),
                     ha="right", va="top", fontsize=FS_2, color=DIM)]
    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(15, None)
    year_ticks(ax, 2023, int(x[-1]), 2 if phone else 1)
    ax.set_ylabel("Bcf/d")
    tidy(ax)
    if phone:
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=1, frameon=False, fontsize=FS_2)
    else:
        ax.legend(loc="lower right", frameon=False, fontsize=FS_2)
    sitefig.centre(fig)
    problems = audit(fig, texts)
    return save(fig, out), problems


# ----------------------------------------------------------------- figure 2
SHORT = {"Matterhorn Express Pipeline": "Matterhorn",
         "Gulf Coast Express Expansion": "GCX expansion",
         "Hugh Brinson Pipeline (formerly Warrior Pipeline) Phase I & II Phase I": "Hugh Brinson I"}


def headroom_fig(P, width, out):
    phone = width == PHONE
    H = P["H"]
    keys = sorted(H)
    x = np.array([yr(k) for k in keys])
    h = np.array([H[k] for k in keys])
    lo = np.array([P["H_band"]["k_lo"][k] for k in keys])
    hi = np.array([P["H_band"]["k_hi"][k] for k in keys])
    sitefig.style()
    fig = plt.figure(figsize=fig_size(width, 0.95 if phone else 16 / 9))
    ax = fig.add_axes([0.17, 0.30, 0.79, 0.60] if phone else [0.10, 0.16, 0.87, 0.74])
    ax.fill_between(x, np.minimum(lo, hi), np.maximum(lo, hi), color=COOL, alpha=0.35, lw=0,
                    label="Range of k")
    ax.plot(x, h, color=ACC, lw=2.2, marker="o", ms=3, label="Headroom at default k")
    ax.axhline(0, color=INK, lw=1)
    texts = []
    big = [e for e in P["entries"] if e["bcfd"] >= 0.5 and keys[0] <= e["month"] <= keys[-1]]
    for i, e in enumerate(big):
        xm = yr(e["month"])
        ax.axvline(xm, color=RULE, lw=1, zorder=0)
        if not phone:
            # a start in the right half is labelled to the left of its line, or the
            # last one runs off the canvas
            right = xm > (x[0] + x[-1]) / 2
            texts.append(ax.text(xm + (-0.03 if right else 0.03), 0.97 - 0.08 * (i % 2), SHORT.get(e["name"], e["name"]),
                                 transform=ax.get_xaxis_transform(), ha="right" if right else "left", va="top",
                                 fontsize=FS_2, color=DIM))
    ax.set_xlim(x[0] - 1 / 24, x[-1] + 1 / 24)
    pad = 0.3
    ax.set_ylim(min(lo.min(), hi.min(), h.min()) - pad, max(lo.max(), hi.max(), h.max()) + 0.9)
    ax.set_xticks([2025, 2026], ["2025", "2026"])
    ax.set_ylabel("Bcf/d")
    tidy(ax)
    if phone:
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=1, frameon=False, fontsize=FS_2)
    else:
        ax.legend(loc="lower left", frameon=False, fontsize=FS_2)
    sitefig.centre(fig)
    problems = audit(fig, texts)
    return save(fig, out), problems


# ----------------------------------------------------------------- figure 3
def flaring_fig(P, width, out):
    phone = width == PHONE
    f = P["flaring"]
    keys = sorted(f["share"])
    x = np.array([yr(k) for k in keys])
    s = np.array([f["share"][k] for k in keys]) * 100
    sitefig.style()
    fig = plt.figure(figsize=fig_size(width, 1.05 if phone else 16 / 9))
    ax = fig.add_axes([0.15, 0.20, 0.81, 0.72] if phone else [0.08, 0.16, 0.89, 0.76])
    ax.plot(x, s, color=MOSS, lw=1.6)
    for e in f["starts"]:
        if keys[0] <= e["month"] <= keys[-1]:
            ax.axvline(yr(e["month"]), color=ACC, lw=1.2, ls=(0, (3, 2)), zorder=0)
    ax.set_xlim(x[0], x[-1] + 1 / 12)
    ax.set_ylim(0, None)
    # from 2012 on the phone and 2010 on the page: a tick at the axis's own
    # start sits on the 0% label
    year_ticks(ax, 2012 if phone else 2010, int(x[-1]), 4 if phone else 2)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}%"))
    ax.set_ylabel("Share of gross withdrawals")
    tidy(ax)
    sitefig.centre(fig)
    problems = audit(fig, [])
    return save(fig, out), problems


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    problems = []
    for name, fn in (("takeaway_capacity", capacity_fig), ("takeaway_headroom", headroom_fig),
                     ("takeaway_flaring", flaring_fig)):
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
