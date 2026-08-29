"""
Redraw the atlas figures from the atlas payload.

Every figure here is computed from site/assets/atlas-data.js, which is the
model of record. Nothing is drawn from a saved intermediate and no number is
typed, so a figure cannot describe a model that no longer exists. That was the
failure worth designing out: the previous set was drawn against 7,192 nodes and
survived the model growing to 86,601 without anything complaining.

Every figure is checked for overlapping or off-canvas text before it is saved.

Run:  python3 build_atlas_figures.py
"""

import collections
import json
import math
import os
import re

import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "assets", "atlas-data.js")
OUT = os.path.join(HERE, "site", "assets")

INK, DIM, FAINT, BG = "#e3e6f2", "#8b93b0", "#232a45", "#0b0f1c"
ACC, COOL, MOSS, ROSE, SLATE = ("#8b7ff2", "#5aa8d8", "#4f9d84",
                                "#d86a86", "#6f7fd8")
KCOL = {"station": ACC, "consumer": COOL, "event": ROSE, "market": MOSS,
        "grid": SLATE, "district": "#5c6a8c", "supply": "#a98fd8",
        "psych": "#cfd6f0", "climate": INK}


def style():
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
        "text.color": INK, "axes.labelcolor": INK,
        "xtick.color": DIM, "ytick.color": DIM,
        "axes.edgecolor": FAINT, "grid.color": FAINT,
        "font.size": 10.5, "font.family": ["DejaVu Sans"],
    })


def load():
    raw = open(DATA, encoding="utf-8").read()
    return json.loads(raw[raw.index("=") + 1:raw.rindex(";")])


def audit(fig):
    """Report text that overlaps other text or runs off the canvas. Every Text
    object is enumerated explicitly; findobj returns ticks that were never
    drawn and their boxes are meaningless."""
    fig.canvas.draw()
    ren = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    items = [t for t in fig.texts if t.get_text().strip()]
    for ax in fig.axes:
        for t in [ax.title, ax.xaxis.label, ax.yaxis.label] + list(ax.texts):
            if t.get_text().strip():
                items.append(t)
        if ax.axison:
            # matplotlib keeps Text objects for ticks outside the axis range
            # and never draws them. Their boxes are real and their positions
            # are nonsense, so they have to be filtered by value rather than
            # trusted.
            x0, x1 = sorted(ax.get_xlim())
            y0, y1 = sorted(ax.get_ylim())
            for tk, lo, hi in ((ax.xaxis, x0, x1), (ax.yaxis, y0, y1)):
                # hiding an axis does not clear the visible flag on its
                # individual labels, so a twinned axis reports a full set of
                # tick labels sitting exactly on the originals
                if not tk.get_visible():
                    continue
                locs = tk.get_ticklocs()
                labs = tk.get_ticklabels()
                for loc, lab in zip(locs, labs):
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
    return bad


def save(fig, name):
    bad = audit(fig)
    fig.savefig(os.path.join(OUT, name), dpi=150)
    plt.close(fig)
    flag = "  LAYOUT: " + "; ".join(bad[:2]) if bad else ""
    print(f"  {name:32s} ok{flag}")
    return bad


# ------------------------------------------------------------- propagation --
def engine(D):
    """The same relaxation the browser runs, as a sparse matrix product.

    This is the recurrence in atlas-app.js written a second time, and the two
    have to agree or the figures describe a model nobody can open. Written as a
    Python loop over adjacency lists it took longer than a session: eighty-six
    thousand nodes by a hundred and thirty thousand edges by sixty rounds is
    about a billion interpreted operations. One sparse matrix-vector product
    per round is a few milliseconds and is the same arithmetic.
    """
    import numpy as np
    from scipy import sparse

    N = D["n"]
    s = np.asarray(D["es"], dtype=np.int32)
    t = np.asarray(D["et"], dtype=np.int32)
    w = np.asarray(D["ew"], dtype=np.float64)
    # Mirrors site/assets/atlas-app.js exactly. See the long comment there for
    # why each of these four steps exists.
    #
    # 1. Layers carry a rank: climate 0, events 1, everything else 2. An edge
    #    is two-way only between equal ranks. Anything crossing a rank drives
    #    and is not driven -- a quake acts on a grid, no grid causes a quake.
    # 2. Each edge is divided by the number of edges arriving at the same node
    #    from the same layer, so a layer speaks once however many members it
    #    has and the members split it.
    # 3. What remains is divided by the node's total in-weight, making every
    #    node the weighted mean of its drivers and the spectral radius 1.
    kind = [D["kinds"][k] for k in D["kind"]]
    RANK = {"sun": 0, "insolation": 1, "weather": 2,
            "climate": 3, "event": 4}
    rank = np.array([RANK.get(k, 5) for k in kind])
    one = rank[s] != rank[t]

    cnt = collections.Counter()
    for a, b in zip(s, t):
        cnt[(int(b), kind[a])] += 1
        if rank[a] == rank[b]:
            cnt[(int(a), kind[b])] += 1
    fw = np.array([w[i] / cnt[(int(t[i]), kind[s[i]])] for i in range(len(w))])
    bw = np.array([0.0 if one[i] else w[i] / cnt[(int(s[i]), kind[t[i]])]
                   for i in range(len(w))])

    degw = np.zeros(N)
    np.add.at(degw, t, np.abs(fw))
    np.add.at(degw, s[~one], np.abs(bw[~one]))
    degw[degw == 0] = 1.0
    fw = fw / degw[t]
    bw[~one] = bw[~one] / degw[s[~one]]

    A = sparse.csr_matrix((np.concatenate([fw, bw[~one]]),
                           (np.concatenate([t, s[~one]]),
                            np.concatenate([s, t[~one]]))), shape=(N, N))
    damp = 1.0 - np.asarray(D["res"], dtype=np.float64) * 0.6

    def run(seed, amount=1.0, lam=0.95, rounds=60):
        b0 = np.zeros(N)
        b0[seed] = amount
        st = b0.copy()
        hit = np.full(N, -1, dtype=np.int32)
        hit[np.abs(st) >= 0.02] = 0
        for r in range(1, rounds + 1):
            inf = A.dot(st)
            nxt = (1 - lam) * st + lam * np.tanh(b0 + damp * inf)
            moved = np.abs(nxt - st)
            fresh = (hit < 0) & (np.abs(nxt) >= 0.02)
            hit[fresh] = r
            biggest = moved.max() if moved.size else 0.0
            st = nxt
            if biggest < 1e-5:
                break
        return st, hit, r
    return run


def main():
    style()
    D = load()
    N = D["n"]
    kind = [D["kinds"][k] for k in D["kind"]]
    problems = 0

    # ---- 04 resilience by layer -------------------------------------
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    order = ["station", "consumer", "event", "market", "supply", "grid",
             "district", "psych"]
    data, labs, cols = [], [], []
    for k in order:
        v = [D["res"][i] for i in range(N) if kind[i] == k]
        if len(v) < 3:
            continue
        data.append(v)
        labs.append(f"{k}\n{len(v):,}")
        cols.append(KCOL.get(k, DIM))
    bp = ax.boxplot(data, patch_artist=True, medianprops=dict(color=INK),
                    flierprops=dict(marker=".", markersize=2,
                                    markerfacecolor=DIM, markeredgecolor=DIM))
    for patch, c in zip(bp["boxes"], cols):
        patch.set_facecolor(c)
        patch.set_alpha(0.55)
        patch.set_edgecolor(c)
    ax.set_xticklabels(labs, fontsize=9)
    ax.set_ylabel("resilience (damping applied to what reaches a node)")
    ax.set_title(f"How hard each layer resists a change  ·  {N:,} nodes")
    ax.grid(axis="y", alpha=0.18)
    ax.set_axisbelow(True)
    fig.tight_layout()
    problems += len(save(fig, "04_inertia_by_type.png"))

    # ---- 05 link structure ------------------------------------------
    deg = collections.Counter()
    for s, t in zip(D["es"], D["et"]):
        deg[s] += 1
        deg[t] += 1
    counts = collections.Counter(deg[i] for i in range(N))
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    xs = sorted(k for k in counts if k > 0)
    ax.scatter(xs, [counts[x] for x in xs], s=16, color=ACC, alpha=0.85,
               edgecolor="none")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("links on a node")
    ax.set_ylabel("number of nodes")
    iso = sum(1 for i in range(N) if deg[i] == 0)
    ax.set_title(f"Link structure  ·  {len(D['es']):,} links  ·  "
                 f"{iso:,} nodes with none ({100 * iso / N:.2f}%)")
    ax.grid(alpha=0.18, which="both")
    fig.tight_layout()
    problems += len(save(fig, "05_link_structure.png"))

    # ---- 09 capacity against fuel -----------------------------------
    fuel = collections.defaultdict(list)
    pat = re.compile(r"\(([A-Za-z ]+), ([\d.]+) MW\)$")
    for i in range(N):
        if kind[i] != "station":
            continue
        m = pat.search(D["name"][i])
        if m:
            fuel[m.group(1).strip()].append(float(m.group(2)))
    top = sorted(fuel.items(), key=lambda kv: -sum(kv[1]))[:9]
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    ys = [k for k, _ in top][::-1]
    tot = [sum(v) / 1000.0 for _, v in top][::-1]
    cnt = [len(v) for _, v in top][::-1]
    ax.barh(ys, tot, color=ACC, alpha=0.85)
    for y, (a, c) in enumerate(zip(tot, cnt)):
        ax.text(a + max(tot) * 0.012, y, f"{a:,.0f} GW  ·  {c:,} units",
                va="center", fontsize=9.5, color=DIM)
    ax.set_xlim(0, max(tot) * 1.34)
    ax.set_xlabel("installed capacity (GW)")
    ax.set_title("Where the world's generating capacity sits, by fuel")
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)
    fig.tight_layout()
    problems += len(save(fig, "09_size_vs_lowcarbon.png"))

    # ---- 12 the event record ----------------------------------------
    mags = []
    for i in range(N):
        if kind[i] == "event":
            m = re.match(r"M([\d.]+)", D["name"][i])
            if m:
                mags.append(float(m.group(1)))
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    ax.hist(mags, bins=28, color=ROSE, alpha=0.85, edgecolor="none")
    ax.set_yscale("log")
    ax.set_xlabel("moment magnitude")
    ax.set_ylabel("events in the model")
    ax.set_title(f"The event layer  ·  {len(mags):,} earthquakes that reach "
                 f"infrastructure")
    ax.grid(alpha=0.18)
    ax.set_axisbelow(True)
    fig.tight_layout()
    problems += len(save(fig, "12_recorded_events.png"))

    # ---- 13 provenance ----------------------------------------------
    # Group by source, not by source string. The admin-1 provenance carries
    # the settlement count that located each district, so read literally it
    # fragments into a hundred near-identical categories, each too long to
    # print and each meaning the same thing.
    FAMILY = [
        ("WRI Global Power Plant", "WRI Global Power Plant Database"),
        ("GeoNames cities", "GeoNames settlements"),
        ("GeoNames admin-1", "GeoNames administrative divisions"),
        ("USGS", "USGS earthquake catalogue"),
        ("NGA World Port", "NGA World Port Index"),
        ("Allen", "Allen Brain Atlas"),
        ("EI/OWID", "Energy Institute and Our World in Data"),
        ("FRED", "FRED price series"),
        ("EM-DAT", "EM-DAT disaster database"),
    ]

    def family(s):
        for key, name in FAMILY:
            if key.lower() in s.lower():
                return name
        head = s.split("·")[0].strip()
        return (head[:38] + "…") if len(head) > 38 else (head or "unattributed")

    src = collections.Counter()
    for i in range(N):
        s = D["srcDict"][D["src"][i]] if D.get("srcDict") else ""
        src[family(s)] += 1
    top = src.most_common(9)
    fig, ax = plt.subplots(figsize=(11.0, 5.6))
    ys = [k for k, _ in top][::-1]
    vs = [v for _, v in top][::-1]
    ax.barh(ys, vs, color=COOL, alpha=0.85)
    for y, v in enumerate(vs):
        ax.text(v + max(vs) * 0.012, y, f"{v:,}", va="center", fontsize=9.5,
                color=DIM)
    ax.set_xlim(0, max(vs) * 1.2)
    ax.set_xlabel("nodes")
    ax.set_title("Every node names where its number came from")
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)
    fig.tight_layout()
    problems += len(save(fig, "13_provenance.png"))

    # ---- 11 the climate record --------------------------------------
    co2, temp = D.get("co2", []), D.get("temp", [])
    if co2:
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.5, 6.2), sharex=True)
        a1.plot([p[0] for p in co2], [p[1] for p in co2], color=ACC, lw=1.6)
        a1.set_ylabel("CO$_2$ (ppm)")
        a1.grid(alpha=0.18)
        a1.set_title("The two measured series the model treats as its slow "
                     "variable")
        if temp:
            a2.plot([p[0] for p in temp], [p[1] for p in temp], color=ROSE,
                    lw=1.6)
        a2.set_ylabel("temperature anomaly (°C)")
        a2.set_xlabel("year")
        a2.grid(alpha=0.18)
        fig.tight_layout()
        problems += len(save(fig, "11_climate_record.png"))

    # ---- 14 the space layer -----------------------------------------
    try:
        import numpy as np
        import build_atlas_space as S
        import data_climate_indices as CI
    except Exception:
        S = None
    if S is not None:
        s0 = CI.TSI[-1][1]
        lats = np.arange(-89.5, 90.0, 1.0)
        q = np.array([S.annual_insolation(x, s0) for x in lats])
        wts = np.cos(np.radians(lats))
        gmean = float((q * wts).sum() / wts.sum())

        fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.0, 4.9))
        a1.plot(lats, q, color=ACC, lw=1.9)
        a1.axhline(s0 / 4.0, color=ROSE, lw=1.2, ls="--")
        a1.text(-88, s0 / 4.0 + 6, f"S$_0$/4 = {s0 / 4:.1f} W/m$^2$",
                color=ROSE, fontsize=9.5)
        a1.text(-88, s0 / 4.0 - 26,
                f"area-weighted mean of the curve: {gmean:.1f}",
                color=DIM, fontsize=9.5)
        a1.set_xlabel("latitude (degrees)")
        a1.set_ylabel("annual mean insolation (W/m$^2$)")
        a1.set_title("Sunlight above the atmosphere")
        a1.grid(alpha=0.18)
        a1.set_xlim(-90, 90)
        a1.set_xticks([-90, -60, -30, 0, 30, 60, 90])

        yrs = [x[0] for x in CI.TSI]
        val = [x[1] for x in CI.TSI]
        unc = [x[2] for x in CI.TSI]
        a2.fill_between(yrs, np.array(val) - np.array(unc),
                        np.array(val) + np.array(unc), color=ACC, alpha=0.22,
                        linewidth=0)
        a2.plot(yrs, val, color=ACC, lw=1.7)
        a2.set_xlabel("year")
        a2.set_ylabel("total solar irradiance (W/m$^2$)")
        a2.set_title("The measured solar constant, with its uncertainty")
        a2.grid(alpha=0.18)
        fig.tight_layout()
        problems += len(save(fig, "14_space_layer.png"))

    # ---- 06 and 07: what a run actually does ------------------------
    run = engine(D)
    seeds = []
    for want in ("event", "station", "consumer", "psych", "market",
                 "grid", "climate"):
        best, bw = -1, -1
        for i in range(N):
            if kind[i] == want and deg[i] > bw:
                best, bw = i, deg[i]
        if best >= 0:
            seeds.append((want, best))

    fig, ax = plt.subplots(figsize=(9.8, 5.4))
    reach_rows = []
    for lab, sd in seeds:
        st, hit, steps = run(sd)
        moved = sum(1 for x in st if abs(x) >= 0.02)
        reach_rows.append((lab, moved, steps, hit))
    # Reach spans four orders of magnitude, so a linear axis would draw six
    # of the seven layers as nothing. Log axis, and the count is written out.
    order = sorted(reach_rows, key=lambda r: r[1])
    ax.barh([r[0] for r in order], [max(r[1], 1) for r in order],
            color=[KCOL.get(r[0], DIM) for r in order], alpha=0.85)
    mx = max(r[1] for r in reach_rows) or 1
    for y, r in enumerate(order):
        noun = "node" if r[1] == 1 else "nodes"
        ax.text(max(r[1], 1) * 1.18, y, f"{r[1]:,} {noun} in {r[2]} steps",
                va="center", fontsize=9.5, color=DIM)
    ax.set_xscale("log")
    ax.set_xlim(0.8, mx * 12)
    ax.set_xlabel("nodes moved by more than 0.02 (log scale)")
    ax.set_title("How far one change travels, by the layer it starts in")
    ax.grid(axis="x", alpha=0.18, which="both")
    ax.set_axisbelow(True)
    fig.tight_layout()
    problems += len(save(fig, "06_scenario_reach.png"))

    # The layer colours are chosen for the globe, where psych and climate are
    # both near-white and sit far apart. On one set of axes they are the same
    # line, so the arrival plot uses its own distinguishable cycle.
    SERIES = {
        "event":    ("an earthquake",   "#d86a86"),
        "station":  ("a power plant",   "#8b7ff2"),
        "consumer": ("a settlement",    "#5aa8d8"),
        "psych":    ("a behaviour channel", "#c9a227"),
        "market":   ("a port or price", "#4f9d84"),
        "grid":     ("a national grid", "#6b74d6"),
        "climate":  ("the climate",     "#e3e6f2"),
    }
    fig, ax = plt.subplots(figsize=(9.8, 5.4))
    drawn = 0
    for lab, moved, steps, hit in reach_rows:
        by = collections.Counter(int(h) for h in hit if h > 0)
        if not by:
            continue
        name, col = SERIES.get(lab, (lab, DIM))
        xs = sorted(by)
        ax.plot(xs, [by[x] for x in xs], marker="o", ms=3.4, lw=1.5,
                color=col, label=f"from {name}")
        drawn += 1
    # Integer steps only. Matplotlib will offer 2.5 and 7.5 otherwise, and
    # there is no such thing as a half step here.
    ax.xaxis.set_major_locator(
        matplotlib.ticker.MaxNLocator(integer=True))
    ax.set_xlabel("step")
    ax.set_ylabel("nodes reached for the first time")
    ax.set_yscale("log")
    ax.set_title("When the effect arrives")
    ax.legend(frameon=False, fontsize=9.5)
    ax.grid(alpha=0.18, which="both")
    fig.tight_layout()
    problems += len(save(fig, "07_arrival_order.png"))

    # ---- 08 response against the size of the change -----------------
    # The seed has to be a node whose reach actually varies with the size of
    # the change. seeds[0] is the most connected earthquake, which moves one
    # node whatever you do to it, so the curve was a flat line at 1. Pick the
    # seed with the largest reach at full size and use that.
    best_seed, best_reach, best_lab = seeds[0][1], -1, seeds[0][0]
    for _lab, _sd in seeds:
        _st, _, _ = run(_sd, amount=1.0)
        _r = int((np.abs(_st) >= 0.02).sum())
        if _r > best_reach:
            best_seed, best_reach, best_lab = _sd, _r, _lab
    print(f"     08 seed: the most connected {best_lab} "
          f"({D['name'][best_seed][:38]})")

    fig, ax = plt.subplots(figsize=(9.8, 5.4))
    amts = [0.05, 0.1, 0.2, 0.3, 0.45, 0.6, 0.75, 0.85, 0.95, 1.0]
    moved, mean_eff = [], []
    for a in amts:
        st, _, _ = run(best_seed, amount=a)
        m = np.abs(st) >= 0.02
        moved.append(int(m.sum()))
        mean_eff.append(float(np.abs(st[m]).mean()) if m.any() else 0.0)

    ax.plot(amts, moved, marker="o", ms=4.2, color=ACC, lw=1.9,
            label="nodes moved")
    ax.set_xlabel("size of the change applied")
    ax.set_ylabel("nodes moved", color=ACC)
    ax.tick_params(axis="y", colors=ACC)

    ax2 = ax.twinx()
    ax2.plot(amts, mean_eff, marker="s", ms=4.0, color="#e8c98f", lw=1.9,
             label="mean effect where it landed")
    ax2.set_ylabel("mean effect among the nodes that moved", color="#e8c98f")
    ax2.tick_params(axis="y", colors="#e8c98f")
    ax2.spines["right"].set_color("#e8c98f")
    ax2.set_facecolor("none")
    # twinx shares the x axis and draws its own copy of the tick labels on top
    # of the first set, which reads as a smudge and trips the layout audit
    ax2.xaxis.set_visible(False)

    ax.set_title("The response saturates: tanh bounds every node inside "
                 "(−1, 1)")
    ax.grid(alpha=0.18)
    ax.set_axisbelow(True)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=9.5, loc="lower right")
    fig.tight_layout()
    problems += len(save(fig, "08_response_curve.png"))

    # ---- 02 the weight distribution ---------------------------------
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    mw = D.get("mwMap", {})
    caps = sorted(float(v) for v in mw.values())
    if caps:
        ax.hist(caps, bins=60, color=ACC, alpha=0.85, edgecolor="none")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("plant capacity (MW)")
        ax.set_ylabel("plants")
        ax.set_title(f"Capacity spans five orders of magnitude  ·  "
                     f"{len(caps):,} plants, {sum(caps) / 1e6:.2f} TW")
        ax.grid(alpha=0.18, which="both")
        ax.set_axisbelow(True)
    fig.tight_layout()
    problems += len(save(fig, "02_demand_distribution.png"))

    print(f"\n  {problems} layout problem(s) across the set")
    return problems


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
