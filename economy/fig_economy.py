"""
The four figures for site/economy.html, drawn from outputs/economy_payload.json.

  economy_fig1_elasticity.png   what a per cent is worth, against pace, and
                                the same thing as minutes saved
  economy_fig2_transfer.png     the measured transfer beside the modelled one
  economy_fig3_product.png      3000 m speed against each term and the product
  economy_fig4_drift.png        what two hours of running does to all three

Every colour, size and face comes from sitefig.py. Each figure is audited for
text that overlaps, runs off the canvas or falls under the site's size floor,
and for grid faults; the build prints the count and it must be 0.

Run:  python3 fig_economy.py
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import sitefig                                                  # noqa: E402
from sitefig import (ACC, BG, COOL, DIM, FAINT, FS_2, INK, MOSS, NOTES,   # noqa: E402
                     PLOT, ROSE, RULE, SLATE, WIDE, fig_size)
from fig_floor import floor_problems                            # noqa: E402
import model as M                                               # noqa: E402

PAYLOAD = os.path.join(HERE, "outputs", "economy_payload.json")
OUT = os.path.join(ROOT, "site", "assets")


def audit(fig):
    """Text that overlaps other text, runs off the canvas or is under the size
    floor, plus the grid checks. The enumeration is explicit because findobj
    returns tick artists that were never drawn."""
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
        except Exception:                                        # noqa: BLE001
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
    print(f"  {name:32s} {len(bad)} layout problems{flag}")
    return len(bad)


def pace_label(v):
    """A marathon finish as h:mm, for a speed axis a runner can read."""
    s = int(round(M.marathon_seconds(v)))
    return f"{s // 3600}:{(s % 3600) // 60:02d}"


# A reader knows their finish time, not their speed in metres per second, so
# every pace axis on this page carries a second scale in marathon times. The
# ticks are chosen as round-ish finishes rather than round speeds.
TIME_TICKS = (2.70, 3.30, 4.10, 5.20)


def marathon_axis(ax, lo, hi):
    top = ax.secondary_xaxis("top")
    top.set_xticks(list(TIME_TICKS))
    top.set_xticklabels([pace_label(v) for v in TIME_TICKS], fontsize=FS_2)
    top.tick_params(colors=DIM, length=3)
    top.set_xlabel("the same pace, as a marathon finish", fontsize=FS_2,
                   color=DIM, labelpad=5)
    ax.set_xlim(lo, hi)
    return top


# ------------------------------------------------------------- figure 1 ----
def fig_elasticity(P):
    """The page's central fact. Left: the elasticity against pace, with every
    published curve, so the band is visible and the crossing is labelled.
    Right: the same thing as minutes off a marathon, because per cent of speed
    is not what a runner feels."""
    E = P["elasticity"]
    grid = E["grid_ms"]
    fig, axes = plt.subplots(1, 2, figsize=fig_size(NOTES, PLOT))

    ax = axes[0]
    lo = [b[0] for b in E["spread_band"]]
    hi = [b[1] for b in E["spread_band"]]
    ax.fill_between(grid, lo, hi, color=FAINT, lw=0, zorder=1)
    for key, c in E["curves"].items():
        if c["primary"]:
            continue
        ax.plot(grid, c["elasticity"], color=SLATE, lw=1.0, alpha=.75, zorder=2)
    prim = next(c for c in E["curves"].values() if c["primary"])
    ax.plot(grid, prim["elasticity"], color=ACC, lw=2.0, zorder=4)
    ax.axhline(1.0, color=RULE, lw=1, ls=(0, (3, 3)), zorder=1)
    x = E["crossing_ms"]
    ax.plot([x], [1.0], "o", ms=5, color=INK, zorder=5)
    ax.annotate(f"worth exactly itself\nat a {pace_label(x)} marathon",
                (x, 1.0), xytext=(10, 26), textcoords="offset points",
                fontsize=FS_2, color=INK, ha="left",
                arrowprops=dict(arrowstyle="-", color=RULE, lw=1))
    ax.text(grid[8], 1.34, "worth more than itself", fontsize=FS_2, color=DIM)
    ax.text(grid[-2], 0.56, "worth less  ", fontsize=FS_2, color=DIM, ha="right")
    ax.set_xlabel("pace, metres per second")
    ax.set_ylabel("per cent of speed per per cent of economy")
    ax.set_ylim(0.5, 1.5)
    ax.grid(alpha=.18)
    marathon_axis(ax, grid[0], grid[-1])
    sitefig.panel(ax, "five published cost curves")

    ax = axes[1]
    rows = P["paces"]["rows"]
    key = f"{P['paces']['headline_saving']:.2f}"
    vs = [r["v_ms"] for r in rows]
    saved = [r["gain"][key]["saved_s"] / 60.0 for r in rows]
    pct = [r["gain"][key]["speed_pct"] for r in rows]
    ax.plot(vs, saved, color=MOSS, lw=2.0, marker="o", ms=4, zorder=3)
    for v, sv, pc in zip(vs, saved, pct):
        if v in (2.60, 4.00, 5.72):
            right = v > 5.0
            ax.annotate(f"{pc:.1f}% of speed", (v, sv),
                        xytext=(-8 if right else 14, 18),
                        textcoords="offset points", fontsize=FS_2,
                        color=INK, ha="right" if right else "left")
    ax.set_xlabel("pace, metres per second")
    ax.set_ylabel("minutes off a marathon")
    ax.set_ylim(2.0, 14.5)
    ax.grid(alpha=.18)
    marathon_axis(ax, grid[0], grid[-1])
    sitefig.panel(ax, "a 4% saving, as time")

    fig.tight_layout(w_pad=1.8)
    sitefig.centre(fig)
    return emit(fig, "economy_fig1_elasticity.png")


# ------------------------------------------------------------- figure 2 ----
def fig_transfer(P):
    """Two routes to one number. A small figure, because the point is only
    that the intervals overlap."""
    T = P["transfer"]
    fig, ax = plt.subplots(figsize=fig_size(NOTES, 16 / 5))
    meas, mod = T["measured"], T["modelled"]

    ax.plot([meas["lo"], meas["hi"]], [1, 1], color=ACC, lw=2.4,
            solid_capstyle="butt", zorder=2)
    ax.plot([meas["value"]], [1], "o", ms=7, color=ACC, zorder=3)
    ax.plot([mod["value"]], [0], "D", ms=7, color=MOSS, zorder=3)

    ax.text(meas["value"], 1.30, f"{meas['value']:.2f}", ha="center",
            fontsize=FS_2, color=ACC)
    ax.text(mod["value"], -0.42, f"{mod['value']:.2f}", ha="center",
            fontsize=FS_2, color=MOSS)
    ax.text((meas["lo"] + meas["hi"]) / 2, 0.60,
            "the published interval, taken at its widest",
            va="center", ha="center", fontsize=FS_2, color=DIM)

    ax.set_yticks([0, 1])
    ax.set_yticklabels(["modelled, from the cost curve",
                        "measured, from added shoe mass"], fontsize=FS_2)
    ax.set_ylim(-0.8, 1.7)
    ax.set_xlim(0.30, 1.30)
    ax.axvline(1.0, color=RULE, lw=1, ls=(0, (3, 3)), zorder=1)
    ax.text(1.0, 1.62, "  what a reader assumes", fontsize=FS_2, color=DIM,
            va="top", ha="left")
    ax.set_xlabel("per cent of race time per per cent of metabolic cost")
    ax.grid(alpha=.18, axis="x")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    sitefig.centre(fig)
    return emit(fig, "economy_fig2_transfer.png")


# ------------------------------------------------------------- figure 3 ----
def fig_product(P):
    """The decomposition's real content: the product predicts, its terms do
    not. Four panels of the same twenty runners."""
    L = P["lanferdini"]
    pts = L["points"]
    C = L["correlations"]
    fig, axes = plt.subplots(1, 4, figsize=fig_size(NOTES, 2.7), sharey=True)
    speed = [p["speed_ms"] for p in pts]
    series = [
        ("ceiling", [p["ceiling"] for p in pts], "VO$_2$max, ml/kg/min", ACC),
        ("fraction", [100 * p["fraction"] for p in pts], "fraction held, %", COOL),
        ("economy", [p["cost"] for p in pts], "cost, ml/kg/km", ROSE),
        ("product_max", [p["product"] * 1000 / 60 for p in pts],
         "ceiling ÷ cost, m/s", MOSS),
    ]
    for ax, (key, xs, xlab, col) in zip(axes, series):
        ax.scatter(xs, speed, s=22, color=col, alpha=.8, edgecolor="none", zorder=3)
        ax.set_xlabel(xlab)
        ax.grid(alpha=.18)
        r = C[key]["r"]
        sitefig.panel(ax, f"r = {r:+.2f}")
    axes[0].set_ylabel("3000 m speed, m/s")
    fig.tight_layout(w_pad=1.2)
    sitefig.centre(fig)
    return emit(fig, "economy_fig3_product.png")


# ------------------------------------------------------------- figure 4 ----
def fig_drift(P):
    """Nothing holds still. Left: the three terms after 90 and 120 minutes of
    running. Right: the share of critical speed a runner holds, against how
    long they are out there."""
    Z = P["looked_up"]["zanini_2025"]["value"]
    H = P["looked_up"]["hunter_2025"]["value"]
    S = P["looked_up"]["smyth_2020"]["value"]
    fig, axes = plt.subplots(1, 2, figsize=fig_size(NOTES, PLOT))

    ax = axes[0]
    t = [0, 90, 120]
    econ = [0, Z["economy_worse_pct_at_90min"], Z["economy_worse_pct_at_120min"]]
    peak = [0, -Z["vo2peak_fall_pct"][0], -Z["vo2peak_fall_pct"][1]]
    thr = [0,
           100 * (Z["threshold_speed_kmh"][1] / Z["threshold_speed_kmh"][0] - 1),
           100 * (Z["threshold_speed_kmh"][2] / Z["threshold_speed_kmh"][0] - 1)]
    # Peak uptake and threshold speed fall by very nearly the same amount, so
    # the two lines land on top of each other at 120 minutes. That coincidence
    # is worth seeing, so they are kept on one axis and separated by dash and
    # by a label offset rather than by moving either line.
    for ys, col, name, dash, dy in (
            (econ, ROSE, "cost of a kilometre", "-", 0),
            (peak, ACC, "peak oxygen uptake", "-", 9),
            (thr, COOL, "threshold speed", (0, (4, 2)), -11)):
        ax.plot(t, ys, color=col, lw=2.0, ls=dash, marker="o", ms=4, zorder=3)
        ax.annotate(name, (t[-1], ys[-1]), xytext=(8, dy),
                    textcoords="offset points", fontsize=FS_2, color=col,
                    va="center", ha="left")
    ax.axhline(0, color=RULE, lw=1, zorder=1)
    ax.set_xlim(-6, 232)
    ax.set_xticks([0, 90, 120])
    ax.set_xlabel("minutes of running")
    ax.set_ylabel("change from fresh, %")
    ax.grid(alpha=.18)
    sitefig.panel(ax, f"n = {Z['n']}, two hours of running")

    ax = axes[1]
    mins = [150, 360]
    share = [100 * S["at_150_min"], 100 * S["at_360_min"]]
    ax.plot(mins, share, color=MOSS, lw=2.0, marker="o", ms=5, zorder=3)
    ax.axhline(100 * S["share_of_critical_speed_overall"], color=RULE, lw=1,
               ls=(0, (3, 3)), zorder=1)
    ax.text(128, 100 * S["share_of_critical_speed_overall"] + 1.1,
            f"all finishers, {100 * S['share_of_critical_speed_overall']:.1f}%",
            fontsize=FS_2, color=DIM, ha="left")
    for m, s in zip(mins, share):
        low = s < 85
        ax.annotate(f"{s:.1f}%", (m, s),
                    xytext=(-6 if low else 6, -14 if low else 10),
                    textcoords="offset points", fontsize=FS_2, color=INK,
                    ha="right" if low else "left")
    ax.set_xlim(120, 400)
    ax.set_xticks([150, 240, 360])
    ax.set_xticklabels(["2:30", "4:00", "6:00"])
    ax.set_ylim(74, 98)
    ax.set_xlabel("finish time")
    ax.set_ylabel("share of critical speed held, %")
    ax.grid(alpha=.18)
    sitefig.panel(ax, "over 25,000 marathons")

    fig.tight_layout(w_pad=2.4)
    sitefig.centre(fig)
    return emit(fig, "economy_fig4_drift.png")


def main():
    sitefig.style()
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    bad = 0
    bad += fig_elasticity(P)
    bad += fig_transfer(P)
    bad += fig_product(P)
    bad += fig_drift(P)
    print(f"  {bad} layout problems in total")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
