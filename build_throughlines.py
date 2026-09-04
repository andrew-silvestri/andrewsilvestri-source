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
import textwrap

import matplotlib
from sitefig import BG, INK, DIM, RULE, FAINT, ACC, COOL, MOSS, ROSE, SLATE, DISTRICT, SUPPLY, PSYCH, SUN, INSOL, GOLD, GREY, VIOLET, BLUE, GREEN, WARM, ARROW, ONE_WAY_COL, TWO_WAY_COL, NODE_COL, WARM2, KCOL, CYCLE, FS_2, FS_1, FS0, FS1, FS2, FONT, MONO, NOTES, PROSE, CARD, THUMB, fig_size, save, WIDE, PLOT, SQUARE, TALL, row_aspect, panel  # noqa: E402,F401
import sitefig  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy.sparse as sp
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from fig_floor import floor_problems

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "assets", "atlas-data.js")
OUT = os.path.join(HERE, "site", "assets", "energy_model_throughlines.png")

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


def style():
    """The typographic scale from figstyle.py (site/downloads/heat-code.zip,
    lines ~68-88) - the house scale, and the only figure set on the site that
    already reads well at web width. Only the sizes are pulled in here: every
    label on this sheet is hand-placed with its own ax.text/fig.text call and
    sets its own color, so rcParams cannot reach most of it the way it does a
    normal axes-driven chart. What rcParams *does* reach - default tick and
    label sizes on the few plain axes below - is worth setting anyway so
    nothing silently falls back to matplotlib's own (smaller) default.
    """
    sitefig.style(); plt.rcParams.update({
        "font.size": FS_1,
        "font.family": FONT,
        "axes.titlesize": FS0,
        "axes.labelsize": FS_1,
        "xtick.labelsize": FS_1,
        "ytick.labelsize": FS_1,
        "legend.fontsize": FS_1,
    })


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
    title_ids = {id(ax.title) for ax in fig.axes}
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
        if not ax.axison:
            # ax.axis("off") - used by every diagram panel on this sheet -
            # hides the frame and ticks visually but does not set
            # xaxis.get_visible()/yaxis.get_visible() to False, so their
            # (never-drawn) default tick labels were being measured as real
            # text and reported as colliding with whatever a diagram actually
            # placed at that same data position. ax.axison is the flag
            # axis("off") does set, and is what build_atlas_figures.py's
            # audit() already checks for this exact reason.
            continue
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
    problems += floor_problems(fig, [(t, id(t) in title_ids) for t in items])
    return problems


def main():
    style()
    D = load()
    kind = [D["kinds"][k] for k in D["kind"]]
    nm = D["name"]
    ids = {k: int(v) for k, v in D["idMap"].items()}
    run, A = engine(D)
    counts = collections.Counter(kind)

    # 15.5in used to put the on-screen factor (pt * 1140 / (72 * width)) at
    # ~1.02 - a 7.2pt label landed at 7.4px, under the 11px floor. 11x12.4
    # keeps the aspect ratio and raises the factor to ~1.44.
    # Height went from 12.4 to 13.3 on top of that. Width alone fixed the
    # floor, but narrowing from 15.5in also narrowed panel B's row pitch in
    # absolute terms without anything giving its wrapped two-line node
    # labels more room, and shrank the band between the two grids below it
    # until a wrapped label's second line and the next panel's title pad
    # were nearly touching. The extra 0.9in funds both fixes below; it
    # can't come out of panel A's or C-F's own share because both already
    # audit clean at their current size.
    fig = plt.figure(figsize=fig_size(PROSE, 0.55), facecolor=BG)
    # Two grids rather than one. The upper panels are diagrams that start at
    # the left edge; the lower panels are charts whose category labels live
    # outside the axes and need the margin. Sharing one grid put those labels
    # off the canvas.
    # height_ratios used to be [1.05, 1.0] - almost even. Panel A is a row of
    # single-line boxes; panel B packs a title, four rows of paired
    # value/route-name text and two-line wrapped node names into the same
    # span, and its bottom row's second label line was landing on the value
    # of the row below. [0.845, 1.0] hands B about 25% more of this grid's
    # pixels than before (verified against A: a first attempt that shrank
    # A's own ratio to buy this, at the old figure height, put A's row-box
    # text into itself - A needs to keep its old *absolute* height, not
    # just a bigger slice of a fixed pie, which is why the figure grew
    # instead). Stretching row_y's pitch without this would have just
    # spread the same crowding over more data units for no gain.
    gs = fig.add_gridspec(2, 1, height_ratios=[1.3, 1.0],
                          hspace=0.30, left=0.050, right=0.975,
                          top=0.965, bottom=0.523)
    # bottom raised from 0.045: panel E's rotated x tick labels sit right at
    # the figure's bottom edge, and the smaller canvas left no room under
    # them once their size came up to the floor.
    # top dropped from 0.500 to 0.450: panel B's bottom row wraps to two
    # lines whose second line hangs below the y=0 edge of B's own axes by
    # design (the label is anchored near the row, not clipped to the
    # panel), and at 0.500 that overflow ran straight into C/D's title pad.
    # The gap between the two grids is now ~70pt, enough for that overflow
    # plus a clearly visible gap plus the title's own pad and line height.
    gsb = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0],
                          hspace=0.55, wspace=0.42, left=0.135,
                          right=0.965, top=0.450, bottom=0.085)


    # ---- A: the layer chain --------------------------------------------
    ax = fig.add_subplot(gs[0, 0])
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 34)
    ax.axis("off")
    sitefig.panel(ax, "A.  The layers, and what carries between them")

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
                fontsize=FS_2, fontweight="bold", zorder=3)
        ax.text(x, y - 1.3, f"{counts[k]:,}", ha="center", va="center",
                color=DIM, fontsize=FS_2, zorder=3)
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
    sitefig.panel(axb, "B.  The strongest route out of four starting points")

    starts = [("SUN_TSI", "The sun"), ("WX_ENSO", "El Nino"),
              ("MKT_BRENT", "The oil price"), ("CLIMATE_SYS", "The climate")]
    row_y = [88, 60, 32, 4]
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
        # The row title used to sit in its own band above the marker row,
        # which is what collided with the wrapped node name of the row above
        # it once that name stopped fitting on one line. Giving the title its
        # own lane to the left of x=16 - clear of every marker in every row -
        # lets it share the marker row's own y instead, freeing the vertical
        # room the wrapped label actually needs.
        axb.text(0, y, title, color=INK, fontsize=FS_1, fontweight="bold",
                 va="center")
        # The route used to run its last marker out to x=100, the axis's own
        # right edge, and the wrapped two-line label anchored there had
        # nowhere to run but off the figure. Stopping short leaves it room.
        start_x, end_x = 16, 86
        step = (end_x - start_x) / max(len(route) - 1, 1)
        for j, n in enumerate(route):
            x = start_x + j * step
            axb.scatter([x], [y], s=95, color=KCOL.get(kind[n], DIM),
                        zorder=3, edgecolors=BG, linewidths=1.2)
            # Used to truncate to 40 chars with an ellipsis at 8.2pt, which
            # threw away the one piece of information the label exists for.
            # Wrapping keeps the full name.
            label = "\n".join(textwrap.wrap(
                nm[n], width=20, max_lines=2, placeholder=" …"))
            axb.text(x, y - 3.5, label, color=DIM, fontsize=FS_2,
                     ha="left", va="top", linespacing=1.2)
            axb.text(x, y + 3.0, f"{st[n]:+.3f}", color=INK, fontsize=FS_2,
                     ha="left", va="bottom")
            if j + 1 < len(route):
                axb.annotate("", xy=(x + step - 2.0, y), xytext=(x + 1.4, y),
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
    axc.barh(range(len(vals)), vals, color=SLATE, alpha=0.9, height=0.62)
    axc.set_yticks(range(len(vals)))
    axc.set_yticklabels(labs, color=DIM, fontsize=FS_2)
    for i, v in enumerate(vals):
        axc.text(v + 0.012, i, f"{v:.2f}", va="center", color=DIM,
                 fontsize=FS_2)
    axc.set_xlim(0, max(vals) * 1.22)
    axc.set_xlabel("heaviest single link between the layers", color=DIM,
                   fontsize=FS_2)
    sitefig.panel(axc, "C.  The links that carry the most")
    for sp_ in axc.spines.values():
        sp_.set_color(RULE)
    axc.tick_params(colors=DIM, labelsize=FS_2)
    axc.grid(axis="x", alpha=0.14)
    axc.set_axisbelow(True)

    # ---- D: one change, step by step ------------------------------------
    axd = fig.add_subplot(gsb[0, 1])
    axd.set_facecolor(BG)
    st, hist = run({ids["MKT_BRENT"]: 0.9})
    idx = {k: np.array([i for i, kk in enumerate(kind) if kk == k])
           for k in LABEL}
    # Eight near-identical thin lines behind a two-column 8.4pt legend meant
    # only one was ever identifiable. Which two (or more) actually carry the
    # story is a question about this scenario's numbers, not a guess: pick by
    # final value rather than assuming which layer matters, because for a
    # large oil supply loss it is Fuel supply that dominates the panel, not
    # the plant layer a first guess might reach for.
    series_by_k = {}
    for k, ii in idx.items():
        if len(ii) == 0:
            continue
        series = [float(np.abs(h[ii]).mean()) for h in hist]
        if max(series) < 1e-4:
            continue
        series_by_k[k] = series

    ranked = sorted(series_by_k.items(), key=lambda kv: kv[1][-1],
                     reverse=True)
    HILITE = [ranked[0][0]] if ranked else []
    if len(ranked) > 1:
        HILITE.append(ranked[1][0])
    # A third line only earns a name if it is clearly its own thing rather
    # than the top of the muted bunch: it has to still be a sizeable fraction
    # of the #2 line, and at least twice whatever comes after it. Here that
    # excludes market/consumer/district/station/psych, which finish within a
    # tight band of each other and would read as one line no matter which of
    # them got picked.
    if len(ranked) > 3:
        third, fourth = ranked[2][1][-1], ranked[3][1][-1]
        second = ranked[1][1][-1]
        if second > 0 and third / second > 0.3 and \
                (fourth <= 0 or third / fourth > 2.0):
            HILITE.append(ranked[2][0])

    last_x = len(hist) - 1
    end_pts, all_vals = {}, []
    for k, series in series_by_k.items():
        all_vals += series
        if k in HILITE:
            axd.plot(range(len(series)), series, color=KCOL[k],
                     linewidth=2.1, zorder=3)
            end_pts[k] = series[-1]
        else:
            axd.plot(range(len(series)), series, color=DIM, alpha=0.4,
                     linewidth=1.0, zorder=1)

    # Direct-label the highlighted lines at their right-hand end instead of a
    # legend. Where two finish close enough together to collide, nudge them
    # apart rather than let the names overlap.
    span = (max(all_vals) - min(all_vals)) if all_vals else 1.0
    ends = sorted(end_pts.items(), key=lambda kv: kv[1])
    for i in range(len(ends) - 1):
        if ends[i + 1][1] - ends[i][1] < 0.05 * span:
            mid = (ends[i][1] + ends[i + 1][1]) / 2
            ends[i] = (ends[i][0], mid - 0.035 * span)
            ends[i + 1] = (ends[i + 1][0], mid + 0.035 * span)
    axd.set_xlim(0, last_x * 1.30)
    for k, y in ends:
        axd.text(last_x * 1.04, y, LABEL[k], color=KCOL[k], fontsize=FS_2,
                 va="center", ha="left", fontweight="bold")

    axd.set_xlabel("step", color=DIM, fontsize=FS_2)
    axd.set_ylabel("mean absolute effect in the layer", color=DIM,
                   fontsize=FS_2)
    sitefig.panel(axd, "D.  A large oil supply loss, step by step")
    for sp_ in axd.spines.values():
        sp_.set_color(RULE)
    axd.tick_params(colors=DIM, labelsize=FS_2)
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
    # magma/inferno was the only off-palette figure on the site. This ramp is
    # built from the site's own palette instead: the dark page ground through
    # the two violet-blue accents used everywhere else. A plain sequential
    # ramp still leaves "very small" and "exactly zero" looking the same, so
    # true-zero cells get their own marker below rather than relying on the
    # reader to tell two shades of near-black apart.
    seq_cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "site_seq", [BG, SLATE, ACC])
    im = axe.imshow(M, aspect="auto", cmap=seq_cmap,
                    norm=matplotlib.colors.PowerNorm(0.45))
    # A 5x9 block of these at the old size read louder than the data beside
    # it - a solid field of marks draws the eye before the color does, which
    # is backwards for a mark that means "nothing happened here". Smaller,
    # thinner and part-transparent so it still reads as absence up close.
    zero_r, zero_c = np.where(M <= 1e-9)
    if len(zero_r):
        axe.scatter(zero_c, zero_r, marker="x", s=8, color=DIM, alpha=0.5,
                    linewidths=0.7, zorder=3)
    axe.set_xticks(range(len(order)))
    # Kept close to the old 7.2pt rather than jumping to the scale used
    # elsewhere: 12 rotated labels share one narrow column, and the floor only
    # needs 7.64pt here (this panel's labels are not read as headings).
    axe.set_xticklabels([SHORT[k] for k in order], rotation=90, ha="center",
                        color=DIM, fontsize=FS_2,
                        rotation_mode="anchor")
    axe.set_yticks(range(len(names)))
    axe.set_yticklabels(names, color=DIM, fontsize=FS_2)
    sitefig.panel(axe, "E.  Which kind of change reaches which layer")
    cb = fig.colorbar(im, ax=axe, fraction=0.036, pad=0.02)
    cb.set_label("mean absolute effect", color=DIM, fontsize=FS_2)
    cb.ax.tick_params(colors=DIM, labelsize=FS_2)
    cb.outline.set_edgecolor(RULE)
    for sp_ in axe.spines.values():
        sp_.set_color(RULE)
    axe.tick_params(colors=DIM)
    # A short caption under the panel instead of folding this into the
    # colorbar's own label, which was already rotated and cramped enough
    # without an eight-word aside stapled onto the end of it.
    axe.annotate("×  =  exact zero, not missing data", xy=(0, 0),
                 xycoords="axes fraction", xytext=(0, -0.40),
                 textcoords="axes fraction", color=DIM, fontsize=FS_2,
                 ha="left", va="top", annotation_clip=False)

    # ---- F: the chain in words ------------------------------------------
    axf = fig.add_subplot(gsb[1, 1])
    axf.set_facecolor(BG)
    axf.axis("off")
    axf.set_xlim(0, 100)
    axf.set_ylim(0, 100)
    sitefig.panel(axf, "F.  The same chain, in words")
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
    # A fixed 8.7-unit step per caption fit the old 17.5in-tall canvas at
    # 9pt. On the smaller canvas the same step ran captions into each other
    # the moment one needed a second line, and matplotlib's own wrap=True
    # wraps to the axes box, not to a spacing this loop knows about, so it
    # cannot see that coming. Wrapping the text here, and spacing by how many
    # lines it actually produced, keeps every caption clear of its neighbours
    # regardless of length. The floor only asks for 7.64pt at this figure
    # width; 7.8pt is used because eleven captions do not fit at the site's
    # normal body size in this panel's height.
    # LINE_H/GAP are in this panel's data units (ylim is 0-100), not points,
    # so they only hold their physical size if this panel's own pixel height
    # is held constant. Widening the gap above panels C/D shrank gsb's own
    # share of the (taller) figure a little more than the figure grew, which
    # left F about 6% shorter in pixels than when 5.7/1.2 were tuned -
    # enough for a caption's last line to touch the one below it. Scaled up
    # by that same ~6% (1.453 old pt/data-unit over 1.371 new) instead of
    # re-tuned from scratch, so the physical spacing on the page is
    # unchanged from what already read clean.
    FBODY, LINE_H, GAP = FS_2, 6.05 * FS_2 / 7.8, 1.3 * FS_2 / 7.8   # caption body at the site floor, line pitch scaled with it
    wrapped = [textwrap.wrap(txt, width=60) or [txt] for _, txt in steps]
    y = 97
    for (k, _), lines in zip(steps, wrapped):
        h = len(lines) * LINE_H
        axf.add_patch(FancyBboxPatch(
            (0, y - 2.2), 3.0, 3.4,
            boxstyle="round,pad=0.1,rounding_size=0.3",
            linewidth=0, facecolor=KCOL[k], zorder=2))
        axf.text(5.0, y, "\n".join(lines), color=DIM, fontsize=FBODY,
                 va="top", linespacing=1.2)
        y -= h + GAP

    for ax_ in fig.axes:
        ax_.set_facecolor(BG)

    problems = audit(fig)
    # dpi is raised only to keep the bitmap's pixel count close to what it was
    # at the old, wider figsize - it has no effect on the on-screen CSS size
    # the floor check above is about, and was never touched to fix legibility.
    sitefig.save(fig, OUT, close=False)
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
