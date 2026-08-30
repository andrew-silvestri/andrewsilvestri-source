"""
The throughlines figure: how a change travels from the sun to a household.

Everything on this sheet is read out of site/assets/atlas-data.js and computed
with the same propagation the atlas runs, so the figure cannot describe a model
other than the published one.

Panels:
    A  the layers and the links between them, with live counts
    B  the strongest computed route out of four different starting points
    C  the links that carry the most weight
    D  one change, step by step, by layer
    E  which prepared change reaches which layer
    F  the chain in words

Layout is checked rather than eyeballed: audit() walks every Text on the
canvas and reports anything that overlaps or falls outside the figure.

Run:  python3 build_throughlines.py
"""

import collections
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy.sparse as sp
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "assets", "atlas-data.js")
OUT = os.path.join(HERE, "site", "assets", "energy_model_throughlines.png")

BG, INK, DIM = "#0a0d18", "#e3e6f2", "#8b93b0"
FAINT, RULE = "#151b30", "#232a45"
KCOL = {"sun": "#f2d98b", "insolation": "#e8c98f", "weather": "#4f9d84",
        "climate": "#cfd6f0", "event": "#d86a86", "market": "#4f9d84",
        "supply": "#6f7fd8", "grid": "#5aa8d8", "station": "#8b7ff2",
        "district": "#5c6a8c", "consumer": "#8b93b0", "psych": "#a98fd8"}
SHORT = {"sun": "Sun", "insolation": "Insolation", "weather": "Weather",
         "climate": "Climate", "event": "Event", "market": "Market",
         "supply": "Fuel", "grid": "Grid", "station": "Plant",
         "district": "District", "consumer": "Consumer",
         "psych": "Behaviour"}
SHORTCAT = {"Universe & Earth, exogenous": "Universe & Earth",
            "Technology improvement & buildout": "Technology",
            "Climate goal meetings": "Climate goals",
            "Country policy changes": "Country policy",
            "Energy makeup evolution": "Energy makeup",
            "People & cognition": "People", "Global pandemics": "Pandemics",
            "Natural disasters": "Disasters"}
LABEL = {"sun": "Sun", "insolation": "Insolation", "weather": "Weather",
         "climate": "Climate", "event": "Recorded event",
         "market": "Market and port", "supply": "Fuel supply",
         "grid": "National grid", "station": "Power station",
         "district": "District", "consumer": "Consumer group",
         "psych": "Behaviour"}


def load():
    raw = open(DATA, encoding="utf-8").read()
    return json.loads(raw[raw.index("=") + 1:raw.rindex(";")])


def engine(D):
    """The published propagation, in sparse linear algebra."""
    N = D["n"]
    s = np.asarray(D["es"], dtype=np.int64)
    t = np.asarray(D["et"], dtype=np.int64)
    w = np.asarray(D["ew"], dtype=float)
    kind = [D["kinds"][k] for k in D["kind"]]
    RANK = {"sun": 0, "insolation": 1, "weather": 2, "climate": 3, "event": 4}
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
    deg = np.zeros(N)
    np.add.at(deg, t, np.abs(fw))
    np.add.at(deg, s[~one], np.abs(bw[~one]))
    deg[deg == 0] = 1.0
    fw = fw / deg[t]
    bw[~one] = bw[~one] / deg[s[~one]]
    A = sp.csr_matrix((np.concatenate([fw, bw[~one]]),
                       (np.concatenate([t, s[~one]]),
                        np.concatenate([s, t[~one]]))), shape=(N, N))
    damp = 1.0 - np.asarray(D["res"], dtype=float) * 0.6

    def run(shocks, rounds=60):
        b = np.zeros(N)
        for i, v in shocks.items():
            b[i] = v
        st = b.copy()
        hist = [st.copy()]
        for r in range(1, rounds + 1):
            nx = (1 - 0.95) * st + 0.95 * np.tanh(b + damp * A.dot(st))
            d = np.abs(nx - st).max()
            st = nx
            hist.append(st.copy())
            if d < 1e-5:
                break
        return st, hist
    return run, A


def audit(fig):
    """
    Titles and tick labels are not in ax.texts. A first version of this checked
    only ax.texts and fig.texts, reported a clean sheet, and shipped a figure
    whose subtitle sat on top of a panel heading and whose longest y labels ran
    off the left edge. Anything drawn as text is collected here.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    items, problems = [], []
    for ax in fig.axes:
        for tx in ax.texts:
            if tx.get_text().strip():
                items.append(tx)
        if ax.title.get_text().strip():
            items.append(ax.title)
        # matplotlib keeps Text objects for ticks outside the axis limits and
        # never draws them. Counting those reports failures that are not on
        # the page, so only ticks inside the limits are considered.
        x0, x1 = sorted(ax.get_xlim())
        y0, y1 = sorted(ax.get_ylim())
        for axis, lo, hi in ((ax.xaxis, x0, x1), (ax.yaxis, y0, y1)):
            # a hidden axis keeps its label objects, and they sit exactly on
            # the labels of the axis it was twinned from
            if not axis.get_visible():
                continue
            for loc, lab in zip(axis.get_ticklocs(), axis.get_ticklabels()):
                if lo - 1e-9 <= loc <= hi + 1e-9 and lab.get_text().strip() \
                        and lab.get_visible():
                    items.append(lab)
        for lab in (ax.xaxis.label, ax.yaxis.label):
            if lab.get_text().strip():
                items.append(lab)
        # legend entries are their own artists and are easy to run off the
        # edge, which is exactly what a legend outside the axes does
        lg = ax.get_legend()
        if lg is not None:
            for lab in lg.get_texts():
                if lab.get_text().strip():
                    items.append(lab)
    for tx in fig.texts:
        if tx.get_text().strip():
            items.append(tx)
    boxes = []
    W, H = fig.canvas.get_width_height()
    for tx in items:
        bb = tx.get_window_extent(renderer=r)
        boxes.append((tx, bb))
        if bb.x0 < -2 or bb.y0 < -2 or bb.x1 > W + 2 or bb.y1 > H + 2:
            problems.append(f"off canvas: {tx.get_text()[:36]!r}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][1], boxes[j][1]
            if a.x1 > b.x0 and b.x1 > a.x0 and a.y1 > b.y0 and b.y1 > a.y0:
                problems.append(
                    f"overlap: {boxes[i][0].get_text()[:22]!r} / "
                    f"{boxes[j][0].get_text()[:22]!r}")
    return problems


def main():
    D = load()
    kind = [D["kinds"][k] for k in D["kind"]]
    nm = D["name"]
    ids = {k: int(v) for k, v in D["idMap"].items()}
    run, A = engine(D)
    counts = collections.Counter(kind)

    fig = plt.figure(figsize=(15.5, 17.5), facecolor=BG)
    # Two grids rather than one. The upper panels are diagrams that start at
    # the left edge; the lower panels are charts whose category labels live
    # outside the axes and need the margin. Sharing one grid put those labels
    # off the canvas.
    gs = fig.add_gridspec(2, 1, height_ratios=[1.05, 1.0],
                          hspace=0.30, left=0.050, right=0.975,
                          top=0.895, bottom=0.545)
    gsb = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0],
                          hspace=0.55, wspace=0.42, left=0.135,
                          right=0.965, top=0.500, bottom=0.045)

    fig.text(0.055, 0.978, "Throughlines: from the sun to the mind",
             color=INK, fontsize=21, fontweight="bold", va="top")
    fig.text(0.055, 0.951,
             "Every number on this sheet is read from the published model and "
             "computed with the propagation the atlas runs.",
             color=DIM, fontsize=11.5, va="top")

    # ---- A: the layer chain --------------------------------------------
    ax = fig.add_subplot(gs[0, 0])
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 34)
    ax.axis("off")
    ax.set_title("A.  The layers, and what carries between them", color=INK,
                 fontsize=13, loc="left", pad=8)

    # a clean left-to-right chain: no crossing arrows, so no label collisions
    chain = [("sun", 6, 25), ("insolation", 20, 25), ("weather", 20, 8),
             ("climate", 34, 8), ("event", 48, 8), ("market", 34, 25),
             ("supply", 48, 25), ("grid", 62, 17), ("station", 62, 30),
             ("district", 76, 17), ("consumer", 90, 17), ("psych", 90, 4)]
    at = {}
    for k, x, y in chain:
        w, h = 11.5, 5.6
        ax.add_patch(FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.25,rounding_size=0.4",
            linewidth=1.2, edgecolor=KCOL[k], facecolor=FAINT, zorder=2))
        ax.text(x, y + 1.0, LABEL[k], ha="center", va="center", color=INK,
                fontsize=9.6, fontweight="bold", zorder=3)
        ax.text(x, y - 1.3, f"{counts[k]:,}", ha="center", va="center",
                color=DIM, fontsize=9.0, zorder=3)
        at[k] = (x, y, w, h)

    links = [("sun", "insolation"), ("insolation", "grid"),
             ("weather", "climate"), ("climate", "event"),
             ("climate", "grid"), ("event", "grid"),
             ("market", "supply"), ("supply", "grid"),
             ("station", "grid"), ("grid", "district"),
             ("district", "consumer"), ("district", "psych"),
             ("psych", "consumer")]
    for a, b in links:
        xa, ya, wa, ha = at[a]
        xb, yb, wb, hb = at[b]
        pa = (xa + wa / 2, ya) if xb > xa else (xa, ya - ha / 2)
        pb = (xb - wb / 2, yb) if xb > xa else (xb, yb + hb / 2)
        if abs(xb - xa) < 1:
            pa, pb = (xa, ya - ha / 2), (xb, yb + hb / 2)
        ax.add_patch(FancyArrowPatch(
            pa, pb, arrowstyle="-|>", mutation_scale=11,
            linewidth=1.0, color=RULE, zorder=1,
            connectionstyle="arc3,rad=0.12"))

    # ---- B: strongest routes -------------------------------------------
    axb = fig.add_subplot(gs[1, 0])
    axb.set_facecolor(BG)
    axb.axis("off")
    axb.set_xlim(0, 100)
    axb.set_ylim(0, 100)
    axb.set_title("B.  The strongest route out of four starting points",
                  color=INK, fontsize=13, loc="left", pad=8)

    starts = [("SUN_TSI", "The sun"), ("WX_ENSO", "El Nino"),
              ("MKT_BRENT", "The oil price"), ("CLIMATE_SYS", "The climate")]
    row_y = [86, 62, 38, 12]
    for (ident, title), y in zip(starts, row_y):
        if ident not in ids:
            continue
        st, _ = run({ids[ident]: 1.0})
        cur, route, seen = ids[ident], [ids[ident]], {ids[ident]}
        for _ in range(4):
            col = A[:, cur].tocoo()
            nxt, best = None, -1.0
            for i, v in zip(col.row, col.data):
                if i in seen:
                    continue
                if abs(st[i]) > best:
                    best, nxt = abs(st[i]), int(i)
            if nxt is None:
                break
            route.append(nxt)
            seen.add(nxt)
            cur = nxt
        axb.text(0, y + 11.5, title, color=INK, fontsize=11,
                 fontweight="bold", va="center")
        step = 100.0 / max(len(route), 1)
        for j, n in enumerate(route):
            x = j * step + 2
            axb.scatter([x], [y], s=95, color=KCOL.get(kind[n], DIM),
                        zorder=3, edgecolors=BG, linewidths=1.2)
            label = nm[n]
            if len(label) > 40:
                label = label[:39].rsplit(" ", 1)[0].rstrip() + "…"
            axb.text(x, y - 7, label, color=DIM, fontsize=8.2,
                     ha="left", va="center", rotation=0)
            axb.text(x, y + 4.5, f"{st[n]:+.3f}", color=INK, fontsize=8.4,
                     ha="left", va="center")
            if j + 1 < len(route):
                axb.annotate("", xy=(x + step - 2.5, y), xytext=(x + 1.6, y),
                             arrowprops=dict(arrowstyle="-|>", color=RULE,
                                             linewidth=1.0))

    # ---- C: heaviest links ---------------------------------------------
    axc = fig.add_subplot(gsb[0, 0])
    axc.set_facecolor(BG)
    pair = collections.defaultdict(float)
    for a, b, w in zip(D["es"], D["et"], D["ew"]):
        pair[(kind[a], kind[b])] = max(pair[(kind[a], kind[b])], abs(w))
    top = sorted(pair.items(), key=lambda kv: -kv[1])[:9][::-1]
    labs = [f"{SHORT[a]} → {SHORT[b]}" for (a, b), _ in top]
    vals = [v for _, v in top]
    axc.barh(range(len(vals)), vals, color="#5a63c8", alpha=0.9, height=0.62)
    axc.set_yticks(range(len(vals)))
    axc.set_yticklabels(labs, color=DIM, fontsize=9)
    for i, v in enumerate(vals):
        axc.text(v + 0.012, i, f"{v:.2f}", va="center", color=DIM,
                 fontsize=8.6)
    axc.set_xlim(0, max(vals) * 1.22)
    axc.set_xlabel("heaviest single link between the layers", color=DIM,
                   fontsize=9.5)
    axc.set_title("C.  The links that carry the most", color=INK,
                  fontsize=13, loc="left", pad=8)
    for sp_ in axc.spines.values():
        sp_.set_color(RULE)
    axc.tick_params(colors=DIM, labelsize=8.6)
    axc.grid(axis="x", alpha=0.14)
    axc.set_axisbelow(True)

    # ---- D: one change, step by step ------------------------------------
    axd = fig.add_subplot(gsb[0, 1])
    axd.set_facecolor(BG)
    st, hist = run({ids["MKT_BRENT"]: 0.9})
    idx = {k: np.array([i for i, kk in enumerate(kind) if kk == k])
           for k in LABEL}
    for k, ii in idx.items():
        if len(ii) == 0:
            continue
        series = [float(np.abs(h[ii]).mean()) for h in hist]
        if max(series) < 1e-4:
            continue
        axd.plot(range(len(series)), series, color=KCOL[k], linewidth=1.7,
                 label=LABEL[k])
    axd.set_xlabel("step", color=DIM, fontsize=9.5)
    axd.set_ylabel("mean absolute effect in the layer", color=DIM,
                   fontsize=9.5)
    axd.set_title("D.  A large oil supply loss, step by step", color=INK,
                  fontsize=13, loc="left", pad=8)
    axd.legend(frameon=False, fontsize=8.4, labelcolor=DIM, ncol=2)
    for sp_ in axd.spines.values():
        sp_.set_color(RULE)
    axd.tick_params(colors=DIM, labelsize=8.6)
    axd.grid(alpha=0.14)
    axd.set_axisbelow(True)

    # ---- E: which change reaches which layer ----------------------------
    axe = fig.add_subplot(gsb[1, 0])
    axe.set_facecolor(BG)
    # One row per scenario is sixty rows. The categories are the structure the
    # catalogue has, so each row is the mean over the scenarios in a category:
    # what that whole family of change does to each layer.
    cats = D.get("scenarioCats", [])
    rows, names = [], []
    order = [k for k in ["sun", "insolation", "weather", "climate", "event",
                         "market", "supply", "grid", "station", "district",
                         "consumer", "psych"] if len(idx[k])]
    for c in cats:
        ks = [k for k, v in D["scenarios"].items() if v.get("cat") == c["id"]]
        if not ks:
            continue
        acc = np.zeros(len(order))
        used = 0
        for k in ks:
            sh = {ids[i]: a for i, a in D["scenarios"][k]["shocks"].items()
                  if i in ids}
            if not sh:
                continue
            stt, _ = run(sh)
            acc += np.array([float(np.abs(stt[idx[kk]]).mean())
                             for kk in order])
            used += 1
        if used:
            rows.append(acc / used)
            names.append(SHORTCAT.get(c["label"], c["label"]))
    M = np.array(rows)
    im = axe.imshow(M, aspect="auto", cmap="magma",
                    norm=matplotlib.colors.PowerNorm(0.45))
    axe.set_xticks(range(len(order)))
    axe.set_xticklabels([SHORT[k] for k in order], rotation=68, ha="right",
                        color=DIM, fontsize=7.2,
                        rotation_mode="anchor")
    axe.set_yticks(range(len(names)))
    axe.set_yticklabels(names, color=DIM, fontsize=8.6)
    axe.set_title("E.  Which kind of change reaches which layer",
                  color=INK,
                  fontsize=13, loc="left", pad=8)
    cb = fig.colorbar(im, ax=axe, fraction=0.036, pad=0.02)
    cb.set_label("mean absolute effect", color=DIM, fontsize=8.6)
    cb.ax.tick_params(colors=DIM, labelsize=7.8)
    cb.outline.set_edgecolor(RULE)
    for sp_ in axe.spines.values():
        sp_.set_color(RULE)
    axe.tick_params(colors=DIM)

    # ---- F: the chain in words ------------------------------------------
    axf = fig.add_subplot(gsb[1, 1])
    axf.set_facecolor(BG)
    axf.axis("off")
    axf.set_xlim(0, 100)
    axf.set_ylim(0, 100)
    axf.set_title("F.  The same chain, in words", color=INK, fontsize=13,
                  loc="left", pad=8)
    steps = [
        ("sun", "The sun delivers %.2f W/m2, measured." %
         next(float(nm[i].split()[-2]) for i in range(len(nm))
              if kind[i] == "sun")),
        ("insolation", "Orbital geometry sets how much of it arrives at each "
                       "latitude."),
        ("weather", "El Nino and the NAO move the temperature and the "
                    "demand."),
        ("climate", "Carbon dioxide and the temperature anomaly set the slow "
                    "state."),
        ("market", "Prices and ports carry cost between countries."),
        ("supply", "Each country's fuel supply is weighted by its real "
                   "share of the power."),
        ("grid", "Grids feel the cost of the fuels they burn."),
        ("station", "Plants feed their grid; the group shares one budget."),
        ("district", "Districts carry the population GeoNames records."),
        ("consumer", "Households and industry receive the cost and use "
                     "less."),
        ("psych", "Behaviour decides how much less."),
    ]
    y = 96
    for k, txt in steps:
        axf.add_patch(FancyBboxPatch(
            (0, y - 3.3), 3.0, 4.6,
            boxstyle="round,pad=0.1,rounding_size=0.3",
            linewidth=0, facecolor=KCOL[k], zorder=2))
        axf.text(5.0, y - 1.0, txt, color=DIM, fontsize=9.0, va="center",
                 wrap=True)
        y -= 8.7

    for ax_ in fig.axes:
        ax_.set_facecolor(BG)

    problems = audit(fig)
    fig.savefig(OUT, dpi=135, facecolor=BG)
    plt.close(fig)
    print(f"  wrote {os.path.basename(OUT)}")
    if problems:
        print(f"  {len(problems)} layout problem(s):")
        for p in problems[:12]:
            print("     " + p)
    else:
        print("  0 layout problems")
    return len(problems)


if __name__ == "__main__":
    main()
