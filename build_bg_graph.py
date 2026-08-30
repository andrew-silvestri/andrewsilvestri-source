"""
The sitewide background graph, generated from the live atlas payload instead
of hand-placed coordinates.

Previously the node/edge pattern in style.css's body::before was drawn from
positions I typed in by hand - it looked like a graph but wasn't one. This
script picks a real seed node, walks outward through the atlas's real edges
(site/assets/atlas-data.js) a few hops, and projects the resulting real
connected subgraph's real coordinates onto a small SVG tile. Every position,
every edge and every colour here traces back to the live model, the same
house rule that governs every number in prose.

The seed is deliberately a market node (a Brent-crude-style price benchmark
tends to be one of the most connected node kinds, per HANDOFF.md's fan-in
notes), so the walk actually finds enough real neighbours in a couple of
hops to fill a small tile.

Run:  python3 build_bg_graph.py
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "assets", "atlas-data.js")
CSS = os.path.join(HERE, "site", "style.css")

TILE = 900
TARGET_NODES = 16
HOPS = 3

# Same palette as build_throughlines.py / build_propagation_diagram.py, and
# the site's own --acc/--cool/--moss for kinds that predate KCOL there.
KCOL = {"sun": "8b7ff2", "insolation": "e8c98f", "weather": "4f9d84",
        "climate": "cfd6f0", "event": "d86a86", "market": "4f9d84",
        "supply": "6f7fd8", "grid": "5aa8d8", "station": "8b7ff2",
        "district": "5c6a8c", "consumer": "8b93b0", "psych": "a98fd8"}
DEFAULT_COL = "8b93b0"


def load():
    raw = open(DATA, encoding="utf-8").read()
    return json.loads(raw[raw.index("=") + 1: raw.rindex(";")])


def build_adjacency(D):
    adj = {}
    for a, b in zip(D["es"], D["et"]):
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    return adj


def pick_seed(D, adj):
    kinds = D["kinds"]
    kind = D["kind"]
    best, best_deg = None, -1
    for i, k in enumerate(kind):
        if kinds[k] != "market":
            continue
        deg = len(adj.get(i, ()))
        if deg > best_deg:
            best, best_deg = i, deg
    return best


def walk(adj, seed, limit):
    seen = {seed}
    order = [seed]
    frontier = [seed]
    for _ in range(HOPS):
        nxt = []
        for node in frontier:
            for nb in adj.get(node, ()):
                if nb not in seen:
                    seen.add(nb)
                    order.append(nb)
                    nxt.append(nb)
                    if len(order) >= limit:
                        return order
        frontier = nxt
        if not frontier:
            break
    return order


def project(lon, lat):
    x = (lon + 180) / 360 * TILE
    y = (90 - lat) / 180 * TILE
    return round(x, 1), round(y, 1)


def heat_curve_svg():
    """A faint echo of heat.html's own break-even chart: gas cost flat at
    $5.13/MMBtu, electric cost linear in price, calibrated to the two real
    points already in the page's prose - the stated break-even (1.53c,
    $5.13) and today's real operating point (6.5c, $20.00). Not a claimed
    figure, a decorative trace, but every number in it is one already
    published on that page."""
    gas = 5.13
    x0, y0 = 1.53, 5.13
    x1, y1 = 6.5, 20.00
    slope = (y1 - y0) / (x1 - x0)
    W, H = 900, 260
    xmax, ymax = 8.0, 24.0

    def pt(price, cost):
        return price / xmax * W, H - cost / ymax * H

    gx0, gy = pt(0, gas)
    gx1, _ = pt(xmax, gas)
    ex0, ey0 = pt(0, gas - slope * x0)
    ex1, ey1 = pt(xmax, gas - slope * x0 + slope * xmax)
    cx, cy = pt(x0, y0)
    ox, oy = pt(x1, y1)
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' "
        f"viewBox='0 0 {W} {H}'>"
        f"<g fill='none' stroke-opacity='.15' stroke-width='2'>"
        f"<path stroke='%234f9d84' d='M{gx0:.1f} {gy:.1f} L{gx1:.1f} {gy:.1f}'/>"
        f"<path stroke='%238b7ff2' d='M{ex0:.1f} {ey0:.1f} L{ex1:.1f} {ey1:.1f}'/>"
        f"</g>"
        f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='3.5' fill='%238b93b0' fill-opacity='.22'/>"
        f"<circle cx='{ox:.1f}' cy='{oy:.1f}' r='3.5' fill='%238b7ff2' fill-opacity='.22'/>"
        f"</svg>"
    )


def storage_curve_svg():
    """A faint echo of storage.html's duration-value curve: fit through the
    page's own three real points (2h/$98.1, 4h/$107.1, 8h/$111.0) with a
    saturating log form, sampled and drawn as a polyline. Approximate
    between the three real points, exact at none of them by construction
    of a two-point fit, but the qualitative bend - the actual claim the
    page makes - is real and the anchor points are the real numbers."""
    import math
    pts = [(2, 98.1), (4, 107.1), (8, 111.0)]
    b = (pts[1][1] - pts[0][1]) / (math.log(pts[1][0]) - math.log(pts[0][0]))
    a = pts[0][1] - b * math.log(pts[0][0])
    W, H = 900, 260
    xmax, ymin, ymax = 10.0, 90.0, 115.0

    def pt(dur, rev):
        return dur / xmax * W, H - (rev - ymin) / (ymax - ymin) * H

    xs = [0.3 + i * (xmax - 0.3) / 40 for i in range(41)]
    path = "M" + " L".join(
        f"{px:.1f} {py:.1f}"
        for px, py in (pt(x, a + b * math.log(x)) for x in xs)
    )
    dots = "".join(
        f"<circle cx='{pt(d, r)[0]:.1f}' cy='{pt(d, r)[1]:.1f}' r='3.5' "
        f"fill='%238b7ff2' fill-opacity='.22'/>"
        for d, r in pts
    )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' "
        f"viewBox='0 0 {W} {H}'>"
        f"<path fill='none' stroke='%238b7ff2' stroke-opacity='.15' "
        f"stroke-width='2' d='{path}'/>{dots}</svg>"
    )


RADIALS = (
    "radial-gradient(1100px 640px at 50% -8%,"
    "rgba(110, 128, 240, .075), transparent 70%),"
    "radial-gradient(900px 520px at 86% 6%,"
    "rgba(79, 157, 132, .05), transparent 68%)"
)


def write_curve_rule(css, class_name, svg, anchor):
    """A body-scoped override of body::before's third background layer, so
    a page with its own real curve shows THAT instead of the generic atlas
    graph, not both layered on top of each other."""
    block = (
        f"\nbody.{class_name}::before {{\n"
        f"  background: {RADIALS},\n"
        f"    url(\"data:image/svg+xml,{svg}\");\n"
        f"  background-repeat: no-repeat, no-repeat, no-repeat;\n"
        f"  background-position: 0 0, 0 0, center 120px;\n"
        f"  background-size: auto, auto, min(900px, 100%) auto;\n"
        f"}}\n"
    )
    marker = f"/* @generated:{class_name} */"
    pattern = re.compile(
        re.escape(marker) + r".*?/\* @end:" + re.escape(class_name) + r" \*/",
        re.S)
    replacement = f"{marker}{block}/* @end:{class_name} */"
    if pattern.search(css):
        return pattern.sub(replacement, css)
    return css.replace(anchor, anchor + "\n" + replacement)


def main():
    D = load()
    adj = build_adjacency(D)
    seed = pick_seed(D, adj)
    nodes = walk(adj, seed, TARGET_NODES)
    node_set = set(nodes)

    pos = {i: project(D["lon"][i], D["lat"][i]) for i in nodes}
    kinds = D["kinds"]
    col = {i: KCOL.get(kinds[D["kind"][i]], DEFAULT_COL) for i in nodes}

    edges = []
    seen_pairs = set()
    for a, b in zip(D["es"], D["et"]):
        if a in node_set and b in node_set and a != b:
            pair = (min(a, b), max(a, b))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                edges.append(pair)

    lines = "".join(
        f"<line x1='{pos[a][0]}' y1='{pos[a][1]}' "
        f"x2='{pos[b][0]}' y2='{pos[b][1]}'/>"
        for a, b in edges
    )
    circles = "".join(
        f"<circle cx='{pos[i][0]}' cy='{pos[i][1]}' r='2.6' "
        f"fill='%23{col[i]}'/>"
        for i in nodes
    )
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{TILE}' "
        f"height='{TILE}' viewBox='0 0 {TILE} {TILE}'>"
        f"<g fill='none' stroke='%238b93b0' stroke-width='1' "
        f"stroke-opacity='.16'>{lines}</g>"
        f"<g fill-opacity='.28'>{circles}</g></svg>"
    )

    css = open(CSS, encoding="utf-8").read()
    # Matches both the hand-written first version (percent-encoded %3C/%3E)
    # and every regenerated one after (this script writes literal <>, which
    # every current browser accepts fine inside a url() data URI).
    new_css, n = re.subn(
        r"url\(\"data:image/svg\+xml,(?:%3C|<)svg.*?"
        r"(?:%3C|<)/svg(?:%3E|>)\"\)",
        f'url("data:image/svg+xml,{svg}")', css, count=1, flags=re.S)
    if n == 0:
        raise SystemExit("could not find the background SVG in style.css - "
                          "has its marker changed?")

    new_css = write_curve_rule(
        new_css, "bg-curve-heat", heat_curve_svg(),
        anchor="@media (prefers-color-scheme: light) { body::before { opacity: .5; } }")
    new_css = write_curve_rule(
        new_css, "bg-curve-storage", storage_curve_svg(),
        anchor="/* @end:bg-curve-heat */")

    open(CSS, "w", encoding="utf-8").write(new_css)

    kind_names = D["kinds"]
    seed_kind = kind_names[D["kind"][seed]]
    print(f"  seed: node {seed} ({seed_kind}), "
          f"walked {HOPS} hops to {len(nodes)} real nodes, "
          f"{len(edges)} real edges among them")
    print(f"  wrote background into {os.path.relpath(CSS, HERE)}")


if __name__ == "__main__":
    main()
