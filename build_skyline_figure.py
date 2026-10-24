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
import matplotlib.pyplot as plt   # noqa: E402

import sitefig                    # noqa: E402
from sitefig import ACC, DIM, FAINT, FS_1, FS_2, INK, MOSS, NOTES, PHONE, SQUARE, WIDE, fig_size  # noqa: E402
from fig_floor import floor_problems  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "site", "skyline-app.html")
OUT = os.path.join(HERE, "site", "assets", "skyline_towers.png")
OUT_PHONE = os.path.join(HERE, "site", "assets", "skyline_towers-phone.png")
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


def draw(city, towers):
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
    ax.text(0.995, 0.97, f"{CITY} · {city['n']} towers of {int(D_MIN)} m or more · played in {key}",
            transform=ax.transAxes, ha="right", va="top", fontsize=FS_2, color=DIM,
            fontfamily=sitefig.MONO)
    fig.tight_layout()
    return fig


def draw_phone(city, towers):
    """The 350 render, a second figure rather than a scaled one (Stage A,
    2026-10-18). Eight upright bars in a 350px column leave about 38px for each
    tower's name, so here the bars lie down: names on the left, tallest at the
    top, the same towers, heights and words. The caption runs two lines, split
    at its second middle dot, because on one line it is wider than the
    column."""
    fig, ax = plt.subplots(figsize=fig_size(PHONE, SQUARE))
    ys = list(range(len(towers)))[::-1]
    ax.barh(ys, [t["h"] for t in towers], height=0.62, color=ACC, zorder=2)
    for y, t in zip(ys, towers):
        ax.text(t["h"] + 8, y, f"{t['h']:.0f} m", ha="left", va="center",
                fontsize=FS_2, color=DIM)
    ax.set_yticks(ys)
    ax.set_yticklabels([t["n"] for t in towers],
                       fontsize=FS_2, color=DIM)
    ax.set_xlabel("height (m)", fontsize=FS_1, color=DIM)
    ax.set_xlim(0, max(t["h"] for t in towers) * 1.22)
    ax.set_xticks([0, 200, 400, 600])
    ax.grid(axis="x", color=FAINT, alpha=0.7, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    key = city["key"]["label"]
    fig.text(0.98, 0.985, f"{CITY} · {city['n']} towers of {int(D_MIN)} m or more\nplayed in {key}",
             ha="right", va="top", fontsize=FS_2, color=DIM, fontfamily=sitefig.MONO)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    return fig


def main():
    sitefig.style()
    city, towers = load()
    total = 0
    for fig, out in ((draw(city, towers), OUT), (draw_phone(city, towers), OUT_PHONE)):
        problems = audit(fig)
        sitefig.save(fig, out, close=False)
        plt.close(fig)
        print(f"  wrote {os.path.basename(out)}")
        print(f"  {len(problems)} layout problem(s)" + ("" if not problems else ":"))
        for p in problems[:8]:
            print("    ", p)
        total += len(problems)
    # Asserts on its own audit, as every figure builder does since 2026-09-12
    # (phase2/STATE.md: a builder that cannot fail on its findings cannot be
    # gated on them).
    if total:
        raise SystemExit(f"build_skyline_figure: {total} layout problem(s)")


D_MIN = 80.0   # the app's own minHeight; read below so the label cannot drift


if __name__ == "__main__":
    _s = open(APP, encoding="utf-8").read()
    _m = re.search(r'const D = JSON\.parse\("(.*?)"\);', _s, re.S)
    D_MIN = json.loads(json.loads('"' + _m.group(1) + '"'))["minHeight"]
    main()
