"""The skyline page's one static figure: New York's eight tallest towers, by
height, as the bars the app plays.

Drawn from the app's own payload - the `D` object inlined in
site/skyline-app.html - so the bars are the same towers, at the same heights,
that the instrument sounds. Nothing here is typed in; if the app's data
changes, this changes with it. Replaces the Manim video that traced the same
eight bars (2026-09-04).

Run:  python3 build_skyline_figure.py
"""
import json
import os
import re
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402

import sitefig                    # noqa: E402
from sitefig import ACC, DIM, FAINT, FS_1, FS_2, INK, MOSS, NOTES, WIDE, fig_size  # noqa: E402
from fig_floor import floor_problems  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "site", "skyline-app.html")
OUT = os.path.join(HERE, "site", "assets", "skyline_towers.png")
CITY, TOP = "New York", 8


def load():
    s = open(APP, encoding="utf-8").read()
    m = re.search(r'const D = JSON\.parse\("(.*?)"\);', s, re.S)
    if not m:
        raise SystemExit("skyline-app.html no longer inlines its payload as JSON.parse(...)")
    D = json.loads(json.loads('"' + m.group(1) + '"'))
    city = next(c for c in D["cities"] if c["city"] == CITY)
    towers = sorted(city["towers"], key=lambda t: -t["h"])[:TOP]
    return city, towers


def audit(fig):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    items = []
    for ax in fig.axes:
        items += [t for t in ax.texts if t.get_text().strip()]
        items += [t for t in ax.get_xticklabels() + ax.get_yticklabels() if t.get_text().strip()]
        if ax.xaxis.label.get_text(): items.append(ax.xaxis.label)
        if ax.yaxis.label.get_text(): items.append(ax.yaxis.label)
    items += [t for t in fig.texts if t.get_text().strip()]
    boxes = [(t, t.get_window_extent(renderer=r)) for t in items]
    problems = []
    for t, bb in boxes:
        if bb.x0 < -2 or bb.y0 < -2 or bb.x1 > W + 2 or bb.y1 > H + 2:
            problems.append(f"off canvas: {t.get_text()[:36]!r}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][1], boxes[j][1]
            if a.x1 > b.x0 and b.x1 > a.x0 and a.y1 > b.y0 and b.y1 > a.y0:
                problems.append(f"overlap: {boxes[i][0].get_text()[:24]!r} / {boxes[j][0].get_text()[:24]!r}")
    problems += floor_problems(fig, [(t, False) for t in items])
    return problems


def main():
    sitefig.style()
    city, towers = load()
    fig, ax = plt.subplots(figsize=fig_size(NOTES, WIDE))
    xs = range(len(towers))
    ax.bar(xs, [t["h"] for t in towers], width=0.62, color=ACC, zorder=2)
    for x, t in zip(xs, towers):
        ax.text(x, t["h"] + 8, f"{t['h']:.0f} m", ha="center", va="bottom",
                fontsize=FS_2, color=DIM)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([textwrap.fill(t["n"], 11) for t in towers],
                       fontsize=FS_2, color=DIM)
    ax.set_ylabel("height (m)", fontsize=FS_1, color=DIM)
    ax.set_ylim(0, max(t["h"] for t in towers) * 1.16)
    ax.set_yticks([0, 200, 400, 600])   # the locator would also own a 700 above the frame
    ax.grid(axis="y", color=FAINT, alpha=0.7, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="x", length=0)
    key = city["key"]["label"]
    ax.text(0.995, 0.97, f"{CITY} · {city['n']} towers over {int(D_MIN)} m · played in {key}",
            transform=ax.transAxes, ha="right", va="top", fontsize=FS_2, color=DIM,
            fontfamily=sitefig.MONO)
    fig.tight_layout()
    problems = audit(fig)
    sitefig.save(fig, OUT, close=False)
    plt.close(fig)
    print(f"  wrote {os.path.basename(OUT)}")
    print(f"  {len(problems)} layout problem(s)" + ("" if not problems else ":"))
    for p in problems[:8]:
        print("    ", p)


D_MIN = 80.0   # the app's own minHeight; read below so the label cannot drift


if __name__ == "__main__":
    _s = open(APP, encoding="utf-8").read()
    _m = re.search(r'const D = JSON\.parse\("(.*?)"\);', _s, re.S)
    D_MIN = json.loads(json.loads('"' + _m.group(1) + '"'))["minHeight"]
    main()
