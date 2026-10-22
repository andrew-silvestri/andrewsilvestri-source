"""Draw the lost-gas page's three figures from outputs/payload.json, each twice: at 714 CSS px for
the page and at 350 for the phone column (HANDOFF trap 22), straight into site/assets/.

  lauf_reporting   how the figure is reported, by year: at or below zero, exactly zero, negative,
                   whole numbers, repeated from the year before
  lauf_spread      operators' reported percentages by year, on all reports and on informative ones
  lauf_change      a system's change from one year to the next: reported, and measurement alone
                   (model.py) at the default assumptions and with every uncertainty doubled and tripled

Every figure ends in audit() (copied from takeaway/fig_takeaway.py, which copied meter's): nothing
under the 12px floor, nothing off the canvas, no two labels overlapping, no legend over data. The
builder exits 1 on any problem. No operator is named in any figure (packet rule).

Run:  python fig_lauf.py
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


def audit(fig, texts):
    """The sibling builders' checks (takeaway/fig_takeaway.py, meter/fig_meter.py)."""
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
            # a legend over plotted data hides it and no text check sees it (meter found this twice)
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


def pctfmt(ax):
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}%"))


def year_axis(ax, years, phone, pad):
    ax.set_xlim(years[0] - pad, years[-1] + pad)
    # the phone starts two years in: a tick at the axis's own start sits on the 0% label
    # (audit found it; takeaway's flaring figure met the same thing)
    t = list(range(years[0] + 2, years[-1] + 1, 5) if phone else range(years[0], years[-1] + 1, 3))
    ax.set_xticks(t, [str(v) for v in t])


def rule_mark(ax, P):
    ry = P["rule_year"]
    ax.axvline(ry - 0.5, color=RULE, lw=1, zorder=0)
    return ax.text(ry - 0.4, 0.98, "negatives allowed", transform=ax.get_xaxis_transform(), ha="left", va="top",
                   fontsize=FS_2, color=DIM)


def legend(ax, phone):
    if phone:
        ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.14), ncol=1, frameon=False, fontsize=FS_2)
    else:
        ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=FS_2)


# ----------------------------------------------------------------- figure 1
def reporting_fig(P, width, out):
    phone = width == PHONE
    R = P["reporting"]
    years = sorted(int(y) for y in R)
    x = np.array(years)

    def s(key, start=None):
        return np.array([100 * R[str(y)][key] if R[str(y)][key] is not None and (start is None or y >= start)
                         else np.nan for y in years])
    sitefig.style()
    fig = plt.figure(figsize=fig_size(width, 1.15 if phone else 16 / 9))
    ax = fig.add_axes([0.15, 0.40, 0.81, 0.54] if phone else [0.08, 0.16, 0.60, 0.76])
    ax.plot(x, s("at_or_below_zero"), color=INK, lw=2.2, marker="o", ms=3, label="At or below zero")
    ax.plot(x, s("zero"), color=MOSS, lw=1.6, label="Exactly zero")
    ax.plot(x, s("negative"), color=ACC, lw=1.6, label="Negative")
    ax.plot(x, s("whole_of_nonzero"), color=COOL, lw=1.4, ls=(0, (4, 2)), label="A whole number (of non-zero)")
    ax.plot(x, s("repeat_of_pairs", years[0] + 1), color=DIM, lw=1.4, ls=(0, (1, 2)), label="Same as the year before")
    texts = [rule_mark(ax, P)]
    year_axis(ax, years, phone, 0.3)
    ax.set_ylim(0, 40)
    pctfmt(ax)
    ax.set_ylabel("Share of reports")
    tidy(ax)
    legend(ax, phone)
    sitefig.centre(fig)
    problems = audit(fig, texts)          # before save(), which closes the figure
    return save(fig, out), problems


# ----------------------------------------------------------------- figure 2
def spread_fig(P, width, out):
    phone = width == PHONE
    D = P["distribution"]
    years = sorted(int(y) for y in D)
    x = np.array(years, float)
    sitefig.style()
    fig = plt.figure(figsize=fig_size(width, 1.15 if phone else 16 / 9))
    ax = fig.add_axes([0.15, 0.36, 0.81, 0.58] if phone else [0.08, 0.16, 0.60, 0.76])
    for key, col, dx, lab in (("all", MOSS, -0.18, "All reports"), ("informative", ACC, 0.18, "Not zero, whole or repeated")):
        q = {p: np.array([D[str(y)]["US"][key][p] for y in years]) for p in ("p10", "p25", "p50", "p75", "p90")}
        ax.vlines(x + dx, q["p10"], q["p90"], color=col, lw=1.2, alpha=0.6)
        ax.vlines(x + dx, q["p25"], q["p75"], color=col, lw=3.5 if phone else 6, alpha=0.9, label=lab)
        ax.plot(x + dx, q["p50"], ls="none", marker="_", ms=6 if phone else 9, mew=2, color=INK)
    ax.axhline(0, color=INK, lw=1)
    texts = [rule_mark(ax, P)]
    year_axis(ax, years, phone, 0.6)
    pctfmt(ax)
    ax.set_ylabel("Reported unaccounted for")
    tidy(ax)
    legend(ax, phone)
    sitefig.centre(fig)
    problems = audit(fig, texts)          # before save(), which closes the figure
    return save(fig, out), problems


# ----------------------------------------------------------------- figure 3
def change_fig(P, width, out):
    phone = width == PHONE
    last = str(max(int(y) for y in P["persistence"]))
    rows = [(f"Reported, {int(last) - 1} to {last}", P["persistence"][last]["change"], INK),
            ("Reported, not zero, whole or repeated", P["persistence"][last]["change_informative"], DIM)]
    for k, lab in (("1.0", "Measurement alone, defaults"), ("2.0", "Every uncertainty doubled"),
                   ("3.0", "Every uncertainty tripled")):
        rows.append((lab, P["model"]["scale_sweep"][k]["change"], ACC if k == "1.0" else MOSS))
    sitefig.style()
    fig = plt.figure(figsize=fig_size(width, 1.25 if phone else 16 / 9))
    ax = fig.add_axes([0.08, 0.20, 0.88, 0.74] if phone else [0.40, 0.16, 0.56, 0.76])
    texts = []
    n = len(rows)
    for i, (lab, q, col) in enumerate(rows):
        yv = n - 1 - i
        ax.hlines(yv, q["p10"], q["p90"], color=col, lw=1.4)
        ax.hlines(yv, q["p25"], q["p75"], color=col, lw=6 if phone else 9)
        ax.plot(q["p50"], yv, marker="|", ms=14, mew=2, color=RULE)
        if phone:
            texts.append(ax.text(0.0, yv + 0.30, lab, transform=ax.get_yaxis_transform(), ha="left", va="bottom",
                                 fontsize=FS_2, color=DIM))
    ax.axvline(0, color=RULE, lw=1, zorder=0)
    ax.set_ylim(-0.6, n - 0.1 if phone else n - 0.4)
    if phone:
        ax.set_yticks([])
    else:
        ax.set_yticks(range(n), [r[0] for r in rows][::-1])
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+g}" if v else "0"))
    ax.set_xlabel("Change in a system's figure, points")
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="x", lw=0.6)
    sitefig.centre(fig)
    problems = audit(fig, texts)          # before save(), which closes the figure
    return save(fig, out), problems


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    problems = []
    for name, fn in (("lauf_reporting", reporting_fig), ("lauf_spread", spread_fig), ("lauf_change", change_fig)):
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
