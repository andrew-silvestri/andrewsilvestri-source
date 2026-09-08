"""The atlas's nine layers, drawn as bands: the home-page hero, and the
picture above atlas.html's layer table.

What it shows. Nine horizontal bands, one per layer of the published model,
in the order of the table on atlas.html, each with its node count. On the
right, every link that runs one way: a single-headed arc from the layer that
pushes to the layer that is pushed. On the left, every link that runs both
ways: a double-headed arc. A dashed rule sits between Events and Markets,
and every arc that crosses it is single-headed and points down, because that
is the model's one structural rule: sun 0, insolation 1, weather 2, climate
3, event 4, everything else 5, and an edge is two-way only within a rank
(HANDOFF.md section 6). An arc's stroke is the number of links it stands for,
on a log scale, so a two-edge link between climate and the markets is a
hairline and the 66,000 district-to-behavior links are the heaviest stroke.
The one forced crossing is stated in the foot, so a reader who notices it
finds it was noticed first.

What is read, and from where. Nothing on the sheet is typed in:

- Node counts per layer are sums over the payload's kinds
  (site/assets/atlas-data.js), and are checked against the numbers
  update_atlas_pages.py writes into the table, so the figure and the table
  cannot disagree.
- Which links exist, and how many edges each stands for, are counted from
  the payload's edge list, kind by kind, and folded to layers. The first
  version of this file hand-typed thirteen kind-level links and missed eight
  that the payload carries (event-to-station, 23,320 edges; event-to-consumer,
  22,025; grid-to-consumer, 34,006; market-to-grid, 2,855; and four small
  ones). A hand-typed link list is a claim the payload can falsify.
- The rank table is parsed out of site/assets/atlas-app.js, the engine of
  record, the way build_propagation_diagram.py parses the step fraction.
  The sheet fails loudly if any cross-rank edge in the payload runs from a
  higher rank to a lower one, or if two kind-level edges between the same two
  layers disagree about direction, because either is a modelling change a
  figure must not paper over.

Three renders. The band layout is one-dimensional, so it survives a narrow
column by being drawn again at that column's width rather than scaled: 1140
CSS px for the wide track on atlas.html, 714 for the text track on the home
page (the hero sits on the measure, so the page keeps one left edge), and 350
for a phone (390 minus main's padding). All at one point per pixel and two
bitmap pixels per point (sitefig); every label clears the 12 px floor in each.
The node counts are labels only: the home page's model chart already draws
them as bars on a log scale one scroll below, and this figure's job is
direction and rank.

Layout is checked, not eyeballed: audit() walks every Text for overlap,
off-canvas and the type floor, checks that what a band holds fits inside it,
that no arc reaches outside its column, and that the band order is the one
with the fewest arc crossings of any (one, forced by the payload).

Run:  python build_layer_diagram.py            # writes into site/assets/
      python build_layer_diagram.py --out DIR  # a review render elsewhere
"""
import collections
import itertools
import json
import math
import os
import re
import sys
import textwrap

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                    # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle          # noqa: E402
from matplotlib.path import Path                                   # noqa: E402

import sitefig                                                     # noqa: E402
from sitefig import (BG, CARD_FILL, INK, DIM, RULE, FAINT, ONE_WAY_COL,   # noqa: E402
                     TWO_WAY_COL, FS_2, FS_1, MONO, PROSE, PHONE, fig_size)
from fig_floor import floor_problems                               # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "assets", "atlas-data.js")
APP = os.path.join(HERE, "site", "assets", "atlas-app.js")
# Two renders, not three. The 714 "notes" render existed for the home page,
# which was this figure's only consumer at that width; since 2026-09-06 the home
# page's first screen is a live canvas (site/assets/hero.js) and nothing asks
# for 714 any more. Retired here rather than left building an unreferenced file:
# a generator that writes something nothing reads is how one goes stale, and
# deleting the PNG while OUT still named it would turn tests/test_generators.py
# red instead.
#
# THE 350 "phone" RENDER STAYS AND IS NOT ORPHANED. atlas.html carries
#   <source media="(max-width: 760px)" srcset="assets/atlas_layers-phone.png">
# so after the home page stopped using it, that page is its only consumer - and
# a phone render on a page whose other render is 1140 wide looks like a leftover
# unless someone says otherwise. This is someone saying otherwise.
OUT = {"wide": os.path.join(HERE, "site", "assets", "atlas_layers.png"),
       "phone": os.path.join(HERE, "site", "assets", "atlas_layers-phone.png")}

# The table's grouping (update_atlas_pages.py, atlas_page()): nine displayed
# layers over the model's twelve kinds. The counts are never taken from here;
# they are summed from the payload and then checked against the table
# generator's own stats().
#
# The order is the table's for the four sources, whose order is their rank.
# Below the rule the table's order (markets, grids, plants, demand,
# behavior) carries no meaning, and drawn that way the arcs cross nine
# times: events fan out to four layers, and every arc from above into grids
# has to cut through that fan unless grids sits beyond it. No order is
# clean: climate pushes both grids and the markets, events pushes both, and
# space pushes only grids, so one crossing is forced whichever comes first.
# audit() tries every order of the block and requires this one to reach the
# minimum, which is one crossing, between the two-edge climate-to-markets
# hairline and events-to-grids. A payload that makes a better order
# possible, or that makes the minimum worse than one, fails the build so a
# human reorders rather than shipping a tangle.
LAYERS = [("Space", ["sun", "insolation"]),
          ("Weather", ["weather"]),
          ("Climate", ["climate"]),
          ("Events", ["event"]),
          ("Demand", ["consumer"]),
          ("Power plants", ["station"]),
          ("Markets and fuel", ["market", "supply"]),
          ("Grids", ["grid", "district"]),
          ("Behavior", ["psych"])]
GROUP_OF = {k: g for g, ks in LAYERS for k in ks}
TABLE_KEY = {"Space": "space", "Weather": "weather", "Climate": "climate",
             "Events": "event", "Markets and fuel": "market", "Grids": "grid",
             "Power plants": "station", "Demand": "consumer",
             "Behavior": "psych"}

# Geometry per render, in CSS px (the axes are in px, one point per px).
GEOM = {
    "wide": dict(W=PROSE, top=14, pitch=58, band=44, rank_gap=34,
                 left=200, col=580, sub=True, legend_h=110),
    "phone": dict(W=PHONE, top=10, pitch=46, band=38, rank_gap=26,
                  left=66, col=210, sub=False, legend_h=148),
}


def load():
    raw = open(DATA, encoding="utf-8").read()
    return json.loads(raw[raw.index("=") + 1:raw.rindex(";")])


def rank_from_app():
    """The exogeneity rank table, parsed from the engine of record."""
    s = open(APP, encoding="utf-8").read()
    m = re.search(r"var RANK\s*=\s*\{([^}]*)\}", s)
    if not m:
        raise SystemExit("atlas-app.js: could not find var RANK = {...}")
    rank = {k.strip(): int(v) for k, v in re.findall(r"(\w+)\s*:\s*(\d+)", m.group(1))}
    default = re.search(r"return r === undefined \? (\d+) : r", s)
    if not default:
        raise SystemExit("atlas-app.js: could not find the default rank")
    return rank, int(default.group(1))


def fmt(n):
    return f"{n:,}"


def structure(D):
    """Counts per layer, and the layer-level links with the edges each
    stands for, from the payload alone."""
    rank_tbl, default = rank_from_app()
    rank = lambda k: rank_tbl.get(k, default)  # noqa: E731
    kinds = D["kinds"]
    kind = [kinds[k] for k in D["kind"]]
    kc = collections.Counter(kind)
    unknown = set(kc) - set(GROUP_OF)
    if unknown:
        raise SystemExit(f"payload has kinds the table does not group: {sorted(unknown)}")
    counts = {g: sum(kc[k] for k in ks) for g, ks in LAYERS}
    kind_counts = {g: [(k, kc[k]) for k in ks] for g, ks in LAYERS}

    pair = collections.Counter()
    for s, t in zip(D["es"], D["et"]):
        pair[(kind[s], kind[t])] += 1

    one_way, two_way = collections.Counter(), collections.Counter()
    for (a, b), n in pair.items():
        ga, gb = GROUP_OF[a], GROUP_OF[b]
        if ga == gb:
            continue
        if rank(a) == rank(b):
            two_way[frozenset((ga, gb))] += n
        else:
            if rank(a) > rank(b):
                raise SystemExit(f"payload edge {a}->{b} runs from rank {rank(a)} "
                                 f"to rank {rank(b)}: a higher rank pushing a lower one "
                                 f"is not the model this figure draws")
            one_way[(ga, gb)] += n
    for key in two_way:
        a, b = tuple(key)
        if (a, b) in one_way or (b, a) in one_way:
            raise SystemExit(f"layers {a} / {b} are joined by both a one-way and a "
                             f"two-way kind-level edge: the grouping needs a human")
    order = [g for g, _ in LAYERS]
    idx = {g: i for i, g in enumerate(order)}
    links = [dict(a=a, b=b, n=n, one=True) for (a, b), n in one_way.items()]
    links += [dict(a=min(k, key=idx.get), b=max(k, key=idx.get), n=n, one=False)
              for k, n in two_way.items()]
    rank_of_layer = {g: {rank(k) for k in ks} for g, ks in LAYERS}
    return dict(counts=counts, kind_counts=kind_counts, links=links, order=order,
                n=D["n"], edges=len(D["es"]), ranks=rank_of_layer, default=default)


def check_against_table(counts):
    """The table on atlas.html is written by update_atlas_pages.py from the
    same payload; the two must agree to the node."""
    sys.path.insert(0, HERE)
    import update_atlas_pages
    s = update_atlas_pages.stats()
    bad = [(g, counts[g], s[TABLE_KEY[g]]) for g in counts if counts[g] != s[TABLE_KEY[g]]]
    if bad:
        raise SystemExit(f"figure and table disagree: {bad}")


def stroke(n):
    """Line width for a link standing for n edges: log scale, 2 -> 0.7 px,
    66,000 -> 3.4 px."""
    return 0.5 + 0.6 * math.log10(max(n, 1))


# ---------------------------------------------------------------- drawing --
BOXED, ARCS = [], []


def arc(ax, x0, ya, yb, side, bulge, lw, col, two):
    """A D-shaped arc from (x0, ya) to (x0, yb) on `side` (+1 right, -1
    left), reaching side * 0.75 * bulge from x0. Heads point into the bands."""
    cx = x0 + side * bulge
    path = Path([(x0, ya), (cx, ya), (cx, yb), (x0, yb)],
                [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
    ax.add_patch(FancyArrowPatch(path=path, arrowstyle="<|-|>" if two else "-|>",
                                 mutation_scale=8 + 1.6 * lw, linewidth=lw,
                                 color=col, zorder=2, shrinkA=0, shrinkB=0,
                                 capstyle="round"))
    ARCS.append((x0 + side * 0.75 * bulge, side))


def draw(S, which):
    g = GEOM[which]
    W, top, pitch, band = g["W"], g["top"], g["pitch"], g["band"]
    order, counts, links = S["order"], S["counts"], S["links"]
    x_col0 = g["left"]
    x_col1 = g["left"] + g["col"]
    right = W - x_col1

    # band centres, with the rank gap after the last one-way source
    src_ranks = S["default"]
    y, ys = top + band / 2, {}
    for i, name in enumerate(order):
        ys[name] = y
        y += pitch
        if i + 1 < len(order) and S["ranks"][order[i + 1]] == {src_ranks} \
                and S["ranks"][name] != {src_ranks}:
            y_rule = y - (pitch - band) / 2 + g["rank_gap"] / 2
            y += g["rank_gap"]
    y_bands_end = y - (pitch - band)
    H = y_bands_end + 12 + g["legend_h"]

    fig = plt.figure(figsize=(W / 72.0, H / 72.0))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")

    # ---- bands ------------------------------------------------------------
    for name in order:
        yc = ys[name]
        ax.add_patch(Rectangle((x_col0, yc - band / 2), g["col"], band, linewidth=1.0,
                               edgecolor=RULE, facecolor=CARD_FILL, zorder=1))
        pad = 10
        if g["sub"]:
            t1 = ax.text(x_col0 + pad, yc - 6, name, color=INK, fontsize=FS_1,
                         fontweight="bold", ha="left", va="center", zorder=3)
            t2 = ax.text(x_col1 - pad, yc - 6, f"{fmt(counts[name])} nodes",
                         color=DIM, fontsize=FS_1, fontfamily=MONO, ha="right", va="center", zorder=3)
        else:
            t1 = ax.text(x_col0 + pad, yc - 8, name, color=INK, fontsize=FS_1,
                         fontweight="bold", ha="left", va="center", zorder=3)
            t2 = ax.text(x_col0 + pad, yc + 9, f"{fmt(counts[name])} nodes",
                         color=DIM, fontsize=FS_2, fontfamily=MONO, ha="left", va="center", zorder=3)
        inside = [t1, t2]
        if g["sub"]:
            sub = " · ".join(f"{k} {fmt(n)}" for k, n in S["kind_counts"][name])
            inside.append(ax.text(x_col0 + pad, yc + 10, sub, color=DIM, fontsize=FS_2,
                                  fontfamily=MONO, ha="left", va="center", zorder=3))
        for t in inside:
            BOXED.append((t, (x_col0, yc - band / 2, x_col1, yc + band / 2)))

    # ---- the rank rule ----------------------------------------------------
    ax.plot([0, W], [y_rule, y_rule], color=DIM, linewidth=0.8, linestyle=(0, (4, 4)), zorder=0)
    ax.text(x_col1 - 10, y_rule - 3,
            "everything above this line pushes and is never pushed back" if which == "wide"
            else "above: pushes, never pushed back",
            color=DIM, fontsize=FS_2, fontfamily=MONO, ha="right", va="bottom", zorder=3,
            bbox=dict(facecolor=BG, edgecolor="none", pad=1.5))

    # ---- arcs --------------------------------------------------------------
    # attachment points per band and side, ordered so nested arcs never
    # cross at the band edge: upward arcs above downward ones, nearer
    # target first on the way up, farther first on the way down
    ends = collections.defaultdict(list)
    for L in links:
        side = 1 if L["one"] else -1
        for me, other in ((L["a"], L["b"]), (L["b"], L["a"])):
            ends[(me, side)].append((ys[other] > ys[me], -ys[other], id(L), other))
    attach = {}
    for (me, side), lst in ends.items():
        lst.sort()
        n = len(lst)
        for i, (_, _, lid, other) in enumerate(lst):
            off = 0 if n == 1 else (i - (n - 1) / 2) * min(9, (band - 12) / (n - 1))
            attach[(lid, me)] = ys[me] + off
    span_max = max(abs(ys[L["a"]] - ys[L["b"]]) for L in links)
    for L in sorted(links, key=lambda L: abs(ys[L["a"]] - ys[L["b"]])):
        side = 1 if L["one"] else -1
        room = (right if side > 0 else x_col0) - 10
        span = abs(ys[L["a"]] - ys[L["b"]])
        bulge = (room / 0.75) * (0.18 + 0.82 * span / span_max)
        x0 = x_col1 + 2 if side > 0 else x_col0 - 2
        arc(ax, x0, attach[(id(L), L["a"])], attach[(id(L), L["b"])], side, bulge,
            stroke(L["n"]), ONE_WAY_COL if L["one"] else TWO_WAY_COL, not L["one"])

    # ---- legend and foot ------------------------------------------------
    ly = y_bands_end + 12 + 14
    nmin_l = min(L["n"] for L in links); nmax_l = max(L["n"] for L in links)
    x = x_col0
    cross = crossings(S, order)
    if which == "wide":
        ax.add_patch(FancyArrowPatch((x, ly), (x + 44, ly), arrowstyle="-|>", mutation_scale=12,
                                     linewidth=1.6, color=ONE_WAY_COL, shrinkA=0, shrinkB=0))
        ax.text(x + 54, ly, "pushes one way", color=DIM, fontsize=FS_2, va="center", ha="left")
        x = x_col0 + 190
        ax.add_patch(FancyArrowPatch((x, ly), (x + 44, ly), arrowstyle="<|-|>", mutation_scale=12,
                                     linewidth=1.6, color=TWO_WAY_COL, shrinkA=0, shrinkB=0))
        ax.text(x + 54, ly, "trades back and forth", color=DIM, fontsize=FS_2, va="center", ha="left")
        x = x_col0 + 420
        for i, n in enumerate((nmin_l, 1000, nmax_l)):
            ax.plot([x + i * 34, x + i * 34 + 24], [ly, ly], color=DIM, linewidth=stroke(n),
                    solid_capstyle="round")
        ax.text(x + 110, ly, f"width: the links an arc stands for, {fmt(nmin_l)} to {fmt(nmax_l)}, log scale",
                color=DIM, fontsize=FS_2, va="center", ha="left")
        ly2 = ly + 24
        foot = [f"{fmt(S['n'])} nodes in nine layers, {fmt(S['edges'])} links, read from the published model."]
        if cross:
            a, b, c, d = cross[0]
            foot.append(f"Bands are ordered to minimise crossings; one is unavoidable, "
                        f"because {a} and {c} each drive both {b} and {d}.")
        for line in foot:
            ax.text(x_col0, ly2, line, color=DIM, fontsize=FS_2, fontfamily=MONO, va="center", ha="left")
            ly2 += 20
    else:
        ax.add_patch(FancyArrowPatch((x, ly), (x + 34, ly), arrowstyle="-|>", mutation_scale=11,
                                     linewidth=1.6, color=ONE_WAY_COL, shrinkA=0, shrinkB=0))
        ax.text(x + 42, ly, "pushes one way", color=DIM, fontsize=FS_2, va="center", ha="left")
        ly += 20
        ax.add_patch(FancyArrowPatch((x, ly), (x + 34, ly), arrowstyle="<|-|>", mutation_scale=11,
                                     linewidth=1.6, color=TWO_WAY_COL, shrinkA=0, shrinkB=0))
        ax.text(x + 42, ly, "trades back and forth", color=DIM, fontsize=FS_2, va="center", ha="left")
        ly2 = ly + 20
        text = [f"arc width: the links it stands for, log scale. "
                f"{fmt(S['n'])} nodes, {fmt(S['edges'])} links."]
        if cross:
            a, b, c, d = cross[0]
            text.append(f"One crossing is unavoidable: {a} and {c} each drive both {b} and {d}.")
        # mono at FS_2 is 0.6 em per character; wrap to the width there is
        fx = 10 if which == "phone" else x_col0
        width_chars = int((W - fx - 10) / (0.6 * FS_2))
        for para in text:
            for line in textwrap.wrap(para, width_chars):
                ax.text(fx, ly2, line, color=DIM, fontsize=FS_2, fontfamily=MONO, va="center", ha="left")
                ly2 += 18
    return fig, ax, dict(W=W, H=H, x_col0=x_col0, x_col1=x_col1, ys=ys)


# ------------------------------------------------------------------ audit --
def audit(fig, ax, geo, S):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    items = [t for t in ax.texts if t.get_text().strip()]
    Wc, Hc = fig.canvas.get_width_height()
    boxes, problems = [], []
    for t in items:
        bb = t.get_window_extent(renderer=r)
        boxes.append((t, bb))
        if bb.x0 < -2 or bb.y0 < -2 or bb.x1 > Wc + 2 or bb.y1 > Hc + 2:
            problems.append(f"off canvas: {t.get_text()[:36]!r}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][1], boxes[j][1]
            if a.x1 > b.x0 and b.x1 > a.x0 and a.y1 > b.y0 and b.y1 > a.y0:
                problems.append(f"overlap: {boxes[i][0].get_text()[:22]!r} / {boxes[j][0].get_text()[:22]!r}")
    problems += floor_problems(fig, [(t, False) for t in items])
    inv = ax.transData.inverted()
    for t, (x0, y0, x1, y1) in BOXED:
        bb = t.get_window_extent(renderer=r).transformed(inv)
        # y is inverted on this axis: bb.y0 is the lower screen edge (larger value)
        lo, hi = min(bb.y0, bb.y1), max(bb.y0, bb.y1)
        if bb.x0 < x0 + 2 or bb.x1 > x1 - 2 or lo < y0 + 1 or hi > y1 - 1:
            problems.append(f"spills its band: {t.get_text()[:30]!r}")
    for reach, side in ARCS:
        if (side > 0 and reach > geo["W"] - 2) or (side < 0 and reach < 2):
            problems.append(f"arc reaches off canvas ({reach:.0f}px)")
    # two arcs on one side cross when their spans interleave; the block
    # below the rule must be in the best order there is, and that order must
    # be nearly clean
    order = S["order"]
    n_src = sum(1 for g in order if S["ranks"][g] != {S["default"]})
    best = min(crossings(S, order[:n_src] + list(p)) for p in itertools.permutations(order[n_src:]))
    mine = crossings(S, order)
    if len(mine) > len(best) or len(mine) > 1:
        problems.append(f"{len(mine)} arc crossing(s), best order has {len(best)}: "
                        + "; ".join(f"{a}-{b} / {c}-{d}" for a, b, c, d in mine))
    return problems


def crossings(S, order):
    idx = {g: i for i, g in enumerate(order)}
    out = []
    for side in (True, False):
        spans = sorted((min(idx[L["a"]], idx[L["b"]]), max(idx[L["a"]], idx[L["b"]]))
                       for L in S["links"] if L["one"] == side)
        for i in range(len(spans)):
            for j in range(i + 1, len(spans)):
                (a, b), (c, d) = spans[i], spans[j]
                if a < c < b < d:
                    out.append((order[a], order[b], order[c], order[d]))
    return out

    return problems


def main():
    # --out DIR renders into another folder for review, leaving site/ alone
    if "--out" in sys.argv:
        d = sys.argv[sys.argv.index("--out") + 1]
        for k in OUT:
            OUT[k] = os.path.join(d, os.path.basename(OUT[k]))
    sitefig.style()
    D = load()
    S = structure(D)
    check_against_table(S["counts"])
    total = 0
    for which in ("wide", "phone"):
        BOXED.clear(); ARCS.clear()
        fig, ax, geo = draw(S, which)
        problems = audit(fig, ax, geo, S)
        size = sitefig.save(fig, OUT[which])
        print(f"  wrote {os.path.basename(OUT[which])}  {geo['W']}x{geo['H']:.0f} css px, {size // 1024} KB, "
              f"{len(problems)} layout problem(s)" + (":" if problems else ""))
        for p in problems[:20]:
            print("     " + p)
        total += len(problems)
    one = sorted((L for L in S["links"] if L["one"]), key=lambda L: -L["n"])
    two = sorted((L for L in S["links"] if not L["one"]), key=lambda L: -L["n"])
    print("  one-way: " + ", ".join(f"{L['a']}->{L['b']} {fmt(L['n'])}" for L in one))
    print("  two-way: " + ", ".join(f"{L['a']}<->{L['b']} {fmt(L['n'])}" for L in two))
    return total


if __name__ == "__main__":
    raise SystemExit(0 if main() == 0 else 1)
