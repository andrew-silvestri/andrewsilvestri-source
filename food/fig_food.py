"""
The four figures for site/food.html, drawn from outputs/food_payload.json.

  food_fig1_plane.png    raw and prepared foods in fat-sugar space, two panels
  food_fig2_null.png     the permutation null against the observed count
  food_fig3_pairs.png    the same food raw and prepared, in fat-sodium space
  food_fig4_groups.png   share of foods meeting any rule, by SR food group

Every colour, size and face comes from sitefig.py. Thresholds are lines with
a labelled crossing, never a filled region. Each figure is audited for text
that overlaps, runs off the canvas or falls under the site's size floor, and
for grid faults; the build prints the count and it must be 0.

Run:  python3 fig_food.py
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
import sitefig                                              # noqa: E402
from sitefig import (ACC, BG, DIM, FAINT, FS_2, INK, MOSS, NOTES, PLOT,    # noqa: E402
                     RULE, SLATE, WIDE, fig_size, row_aspect)
from fig_floor import floor_problems                        # noqa: E402

PAYLOAD = os.path.join(HERE, "outputs", "food_payload.json")
OUT = os.path.join(ROOT, "site", "assets")


def audit(fig):
    """Text that overlaps other text, runs off the canvas or is under the
    size floor, plus the grid checks. Copied from build_atlas_figures.py:
    every Text object is enumerated explicitly, because findobj returns
    ticks that were never drawn."""
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
    bad += floor_problems(fig, [(t, id(t) in title_ids) for t in items])
    return bad + problems_grid


def emit(fig, name):
    bad = audit(fig)
    sitefig.save(fig, os.path.join(OUT, name), close=False)
    plt.close(fig)
    flag = "  LAYOUT: " + "; ".join(bad[:3]) if bad else ""
    print(f"  {name:24s} {len(bad)} layout problems{flag}")
    return len(bad)


def label_points(ax, pts, ren, taken=None, dx=6, dy=4):
    """Annotate (x, y, text) points last, against settled axes, with a plate
    the panel colour behind each; a label that would land on one already
    placed, or leave the axes, is dropped rather than stacked. The idiom is
    build_lq.py's."""
    taken = taken if taken is not None else []
    box = ax.get_window_extent(renderer=ren)

    def clear(bb):
        return not any(bb.overlaps(o) for o in taken) and bb.x0 >= box.x0 \
            and bb.x1 <= box.x1 and bb.y1 <= box.y1

    for x, y, text in pts:
        px, py = ax.transData.transform((x, y))
        right = px > (box.x0 + box.x1) / 2
        # the near side first, then the far side, then drop
        sides = (("right", -dx), ("left", dx)) if right else (("left", dx), ("right", -dx))
        for ha, ddx in sides:
            t = ax.annotate(text, (x, y), fontsize=FS_2, color=INK,
                            xytext=(ddx, dy), textcoords="offset points", ha=ha,
                            bbox=dict(boxstyle="round,pad=0.16", facecolor=BG, edgecolor="none"))
            bb = t.get_window_extent(renderer=ren)
            if clear(bb):
                taken.append(bb)
                break
            t.remove()
    return taken


def load_items():
    import csv
    rows = list(csv.DictReader(open(os.path.join(HERE, "outputs", "items.csv"), encoding="utf-8")))
    for r in rows:
        for k in ("kcal", "fat_pct_kcal", "sugar_pct_kcal", "sodium_pct_wt"):
            r[k] = float(r[k])
    return rows


# ------------------------------------------------------------- figure 1 ----
def fig_plane(P, items):
    floor = P["kcal_floor"]
    fs = P["rules"]["FS"]
    fx, fy = fs["fat_pct_kcal"], fs["sugar_pct_kcal"]
    fig, axes = plt.subplots(1, 2, figsize=fig_size(NOTES, PLOT), sharey=True)
    for ax, cls, col in ((axes[0], "raw", ACC), (axes[1], "prepared", MOSS)):
        G = [r for r in items if r["cls"] == cls and r["kcal"] >= floor]
        ax.plot([0, 100], [100, 0], color=FAINT, lw=1, zorder=1)
        ax.scatter([r["fat_pct_kcal"] for r in G], [r["sugar_pct_kcal"] for r in G],
                   s=9, color=col, alpha=.55, edgecolor="none", zorder=2)
        ax.axvline(fx, color=RULE, lw=1, ls=(0, (3, 3)), zorder=1)
        ax.axhline(fy, color=RULE, lw=1, ls=(0, (3, 3)), zorder=1)
        n_in = P["observed"][cls]["FS"]
        ax.text(97, 92, f"{n_in:,} of {len(G):,}\nabove both lines", ha="right", va="top",
                fontsize=FS_2, color=DIM, zorder=4)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_xlabel("fat, % of energy")
        ax.grid(alpha=.18)
        sitefig.panel(ax, f"{cls}, n = {len(G):,}")
    axes[0].set_ylabel("sugar, % of energy")
    fig.tight_layout(w_pad=1.5)
    fig.canvas.draw()
    ren = fig.canvas.get_renderer()
    hm = P["human_milk"]
    axes[0].scatter([hm["fat_pct_kcal"]], [hm["sugar_pct_kcal"]], s=42, facecolor="none",
                    edgecolor=INK, lw=1.2, zorder=3)
    pts = [(hm["fat_pct_kcal"], hm["sugar_pct_kcal"], "human milk")]
    pts += [(d["fat_pct_kcal"], d["sugar_pct_kcal"], d["label"]) for d in P["named_raw"]]
    label_points(axes[0], pts, ren)
    label_points(axes[1], [(d["fat_pct_kcal"], d["sugar_pct_kcal"], d["label"])
                           for d in P["named_prepared"]], ren)
    sitefig.centre(fig)
    return emit(fig, "food_fig1_plane.png")


# ------------------------------------------------------------- figure 2 ----
def fig_null(P):
    fig, axes = plt.subplots(1, 2, figsize=fig_size(NOTES, WIDE))
    for ax, cls, col in ((axes[0], "raw", ACC), (axes[1], "prepared", MOSS)):
        c = P["null_permutation"][cls]["FS"]["counts"]
        obs = P["observed"][cls]["FS"]
        lo, hi = min(c + [obs]), max(c + [obs])
        pad = max(3, (hi - lo) // 8)
        bins = range(lo - pad, hi + pad + 2)
        ax.hist(c, bins=bins, color=SLATE, alpha=.8, edgecolor="none")
        ax.axvline(obs, color=col, lw=1.8)
        ax.text(obs, ax.get_ylim()[1] * .96, f" observed {obs:,}", ha="left", va="top",
                fontsize=FS_2, color=col)
        m = P["null_permutation"][cls]["FS"]["mean"]
        ax.text(m, ax.get_ylim()[1] * .84, f"shuffled, mean {m:.0f} ", ha="right" if obs < m else "left",
                va="top", fontsize=FS_2, color=DIM)
        ax.set_xlabel("foods above both lines")
        ax.grid(alpha=.18, axis="y")
        sitefig.panel(ax, cls)
    axes[0].set_ylabel(f"shuffles, of {P['n_perm']:,}")
    fig.tight_layout(w_pad=1.5)
    sitefig.centre(fig)
    return emit(fig, "food_fig2_null.png")


# ------------------------------------------------------------- figure 3 ----
def fig_pairs(P):
    R = P["rules"]["FSOD"]
    fx, fy = R["fat_pct_kcal"], R["sodium_pct_wt"]
    FLOOR = 0.005
    fig, ax = plt.subplots(figsize=fig_size(NOTES, PLOT))
    ax.set_yscale("log")
    flips = [p for p in P["pairs"] if not p["raw_FSOD"] and p["prep_FSOD"]]
    moved = [p for p in P["pairs"] if not p["raw_HPF"] and p["prep_HPF"]]
    still = [p for p in P["pairs"] if p not in moved]
    for p in still:
        (x0, y0), (x1, y1) = p["raw"], p["prepared"]
        ax.plot([x0, x1], [max(y0, FLOOR), max(y1, FLOOR)], color=RULE, lw=.8, alpha=.6, zorder=1)
    ax.scatter([p["raw"][0] for p in P["pairs"]],
               [max(p["raw"][1], FLOOR) for p in P["pairs"]], s=8, color=ACC, alpha=.7,
               edgecolor="none", zorder=3)
    ax.scatter([p["prepared"][0] for p in still],
               [max(p["prepared"][1], FLOOR) for p in still], s=8, color=SLATE, alpha=.7,
               edgecolor="none", zorder=2)
    for p in moved:
        (x0, y0), (x1, y1) = p["raw"], p["prepared"]
        ax.annotate("", (x1, max(y1, FLOOR)), (x0, max(y0, FLOOR)),
                    arrowprops=dict(arrowstyle="-|>", color=MOSS, lw=1.3, shrinkA=2, shrinkB=2),
                    zorder=4)
    ax.scatter([p["prepared"][0] for p in moved],
               [max(p["prepared"][1], FLOOR) for p in moved], s=16, color=MOSS,
               edgecolor="none", zorder=5)
    ax.axhline(fy, color=RULE, lw=1, ls=(0, (3, 3)), zorder=1)
    ax.axvline(fx, color=RULE, lw=1, ls=(0, (3, 3)), zorder=1)
    ax.text(99, fy, f"sodium {fy:.2f}% ", ha="right", va="bottom", fontsize=FS_2, color=DIM)
    ax.text(fx, 5.5, f" fat {fx}%", ha="left", va="top", fontsize=FS_2, color=DIM)
    ax.set_xlim(0, 100)
    ax.set_ylim(FLOOR * .8, 6)
    ax.set_yticks([0.01, 0.03, 0.1, 0.3, 1, 3])
    ax.set_yticklabels(["0.01", "0.03", "0.1", "0.3", "1", "3"])
    ax.set_xlabel("fat, % of energy")
    ax.set_ylabel("sodium, % by weight")
    ax.grid(alpha=.18, which="major")
    # a key, in words, hung inside the empty upper-left
    ax.scatter([], [], s=14, color=ACC, label="raw")
    ax.plot([], [], color=RULE, lw=.8, label="cooked plain: stays")
    ax.plot([], [], color=MOSS, lw=1.3, label="canned, breaded, packed in salt: crosses")
    ax.legend(fontsize=FS_2, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.canvas.draw()
    ren = fig.canvas.get_renderer()
    seen, pts = set(), []
    for p in sorted(moved, key=lambda p: -(p["prepared"][1] - p["raw"][1])):
        base = p["base"].split(",")[0].lower()
        if base in seen:
            continue
        seen.add(base)
        prep = p["prep"].replace("cooked, ", "").split(",")[0]
        pts.append((p["prepared"][0], max(p["prepared"][1], FLOOR), f"{base}, {prep}"))
    label_points(ax, pts, ren)
    return emit(fig, "food_fig3_pairs.png")


# ------------------------------------------------------------- figure 4 ----
SHORT_GROUP = {
    "Meals, Entrees, and Side Dishes": "Meals, entrees and sides",
    "Sausages and Luncheon Meats": "Sausages and luncheon meats",
    "Soups, Sauces, and Gravies": "Soups, sauces and gravies",
    "Legumes and Legume Products": "Legumes",
    "Vegetables and Vegetable Products": "Vegetables",
    "Nut and Seed Products": "Nuts and seeds",
    "Finfish and Shellfish Products": "Fish and shellfish",
    "Lamb, Veal, and Game Products": "Lamb, veal and game",
    "American Indian/Alaska Native Foods": "American Indian / Alaska Native",
    "Fruits and Fruit Juices": "Fruits and fruit juices",
    "Dairy and Egg Products": "Dairy and eggs",
    "Cereal Grains and Pasta": "Cereal grains and pasta",
}


def fig_groups(P):
    G = P["groups"]
    n = len(G)
    fig, ax = plt.subplots(figsize=fig_size(NOTES, row_aspect(n, row_px=22)))
    ys = list(range(n))[::-1]
    prepared = set(P["prepared_groups"])
    for y, g in zip(ys, G):
        col = MOSS if g["group"] in prepared else SLATE
        ax.plot([0, 100 * g["share_hpf"]], [y, y], color=FAINT, lw=1, zorder=1)
        ax.scatter([100 * g["share_hpf"]], [y], s=34, color=col, edgecolor="none", zorder=3)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{SHORT_GROUP.get(g['group'], g['group'].replace(' Products', ''))}  ({g['n']:,})"
                        for g in G])
    ax.set_ylim(-0.8, n - 0.2)
    ax.set_xlim(0, 100)
    ax.set_xlabel("foods meeting any rule, % of the group")
    ax.grid(alpha=.18, axis="x")
    ax.tick_params(axis="y", length=0)
    ax.scatter([], [], s=34, color=MOSS, label="a group the page counts as prepared")
    ax.scatter([], [], s=34, color=SLATE, label="other groups")
    ax.legend(fontsize=FS_2, frameon=False, loc="lower right")
    fig.tight_layout()
    return emit(fig, "food_fig4_groups.png")


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    items = load_items()
    sitefig.style()
    bad = fig_plane(P, items) + fig_null(P) + fig_pairs(P) + fig_groups(P)
    print(f"  {bad} layout problems in all")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
