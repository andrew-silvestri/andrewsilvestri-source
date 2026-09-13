"""The one place the figures' palette, face, scale and geometry live.

Every figure builder imports its colours, its font and its sizes from here,
so the figures and the pages cannot drift apart the way they did before
2026-09-04, when the same five constants sat in six files. If style.css
changes a token, change it here and re-run the builders.

Geometry rule. A figure is drawn at the CSS width it is displayed at, one
point per CSS pixel: fig_size(714, 3/2) is 714 CSS px wide, so a label at
FS_1 (14.5 pt) is 14.5 px on screen, the same as a caption. It is saved at
144 dpi, two bitmap pixels per CSS pixel, for retina screens. The old rule
(fig_floor.py) that on-screen px = pt * 1140 / (72 * inches) still holds and
now reduces to pt, which is the point.

Display widths (CSS px at the 1440 shell, from style.css):
  NOTES   714   the text column on pages with marginalia: heat, storage,
                climate-cost, longevity, skyline, desktop, index
  PROSE  1140   the wide track on prose pages: model, atlas
  CARD   1082   a library card's inner width
  THUMB   542   a mosaic thumbnail at two pixels per CSS pixel
  PHONE   350   the whole column at 390px (main's 20px padding each side),
                for a figure that carries a narrow variant instead of
                relying on the lightbox
"""
import os

import matplotlib
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")

# ---- palette: Yacht club, 2026-09-04 (PALETTE_TRIAL_2026-09-04.md) -------
BG = "#F2F0EF"          # the page's ground
CARD_FILL = "#FAF9F8"   # --card: a step up from the ground, for a box on a diagram
INK = "#241E1A"         # text; imported near-black from the brown
DIM = "#625C57"         # ticks, muted labels
RULE = "#BBBDBC"        # axes, grid
FAINT = "#D9D8D6"       # the lightest hairline, faint fills
ACC = "#245F73"         # deep blue: the primary series
COOL = "#4A8AA0"        # blue tint: the secondary series
MOSS = "#733E24"        # brown: the second hue (gas, wild, mass allocation)
ROSE = "#A9724F"        # brown tint: warnings, negatives, events
SLATE = "#7F8A8F"       # grey-blue
DISTRICT = "#A3A5A4"    # light grey
SUPPLY = "#3F7A8C"      # deeper blue tint
PSYCH = "#B08A63"       # tan
SUN = "#733E24"
INSOL = "#A9724F"
GOLD = "#8C5A32"
GREY = "#7F8A8F"
VIOLET = SUPPLY         # names the old builders used, kept so they still read
BLUE = ACC
GREEN = MOSS
WARM = ROSE
ARROW = SLATE
ONE_WAY_COL = SLATE
TWO_WAY_COL = COOL
NODE_COL = ACC
WARM2 = ROSE

KCOL = {"sun": SUN, "insolation": INSOL, "weather": MOSS, "climate": INK,
        "event": ROSE, "market": MOSS, "supply": SUPPLY, "grid": SLATE,
        "station": ACC, "district": DISTRICT, "consumer": COOL, "psych": PSYCH}
CYCLE = [ACC, MOSS, COOL, ROSE, SUPPLY, PSYCH, SLATE, GOLD]

# ---- the type scale, from style.css ---------------------------------------
FS_2, FS_1, FS0, FS1, FS2 = 12, 14.5, 17.5, 21, 25
FONT = "IBM Plex Sans"
MONO = "IBM Plex Mono"

# ---- aspect: chosen by what the figure holds, never defaulted -------------
# A figure is as tall as its content needs and no taller. Lines, few-category
# bars and anything monotone are WIDE; scatters, contours and heat-maps whose
# two axes carry information are PLOT; a ranking or a row chart is as tall as
# its rows (row_aspect()); a multi-panel sheet composes its own. Pass the constant
# to fig_size() as the aspect (width / height).
WIDE = 16 / 9          # a line, two or three bars, a duration curve
PLOT = 1.45            # scatter, contour, heat-map, a two-panel pair
SQUARE = 1.0           # a donut, a map
TALL = 0.75            # a 25-40 row ranking


def row_aspect(n, row_px=24, display_px=None, header_px=90):
    """Aspect for a chart of n horizontal rows at row_px CSS px per row."""
    display_px = display_px or NOTES
    return display_px / (n * row_px + header_px)


# ---- titles: a figure carries none; a sheet labels its panels ---------------
# The page heading above a figure and the caption under it already say what
# it is, so a single-panel figure has no title and no subtitle. A multi-panel
# sheet keeps a short label per panel, set as furniture rather than prose.
def panel(ax, text, pad=6):
    """A panel label: mono, FS_1, muted, left-aligned above the axes.

    The only way a panel may be labelled. save() refuses a figure carrying
    an axes title that did not come through here, because on 2026-09-04
    three panels on the atlas figures were still set with ax.set_title() in
    the sans face, inside the pass that made this rule."""
    t = ax.set_title(text, loc="left", pad=pad, fontsize=FS_1, color=DIM, fontfamily=MONO)
    t._sitefig_panel = True
    return t


def titles(ax):
    """Every title artist an axes can carry that has text. matplotlib keeps
    three - centre, left, right - and ax.title is only the centre one, so an
    audit that reads ax.title never sees a panel() label (loc="left") and
    passes a sheet whose panel label sits on a legend. Read this instead."""
    out = []
    for t in (ax.title, getattr(ax, "_left_title", None), getattr(ax, "_right_title", None)):
        if t is not None and t.get_text().strip():
            out.append(t)
    return out


def unlabelled_panels(fig):
    """Axes titles that did not come through panel(): the drift save() refuses."""
    return [t.get_text() for ax in fig.axes for t in titles(ax)
            if not getattr(t, "_sitefig_panel", False)]


# ---- the grid: a multi-panel sheet is centred, and its panels share edges --
# A sheet's axes are placed by a GridSpec, but what a reader sees is the
# content: axes plus their tick labels, plus any legend hung outside them.
# GridSpec margins are guesses about that content, and every guess on this
# site was wrong the same way: energy_model_chart.png sat 23px right of
# centre in its own canvas with its donut 40px right of its key, and
# climate_allocation_bases.png, redrawn the same night, 24px right
# (2026-09-05). So: lay the panels out, then call centre(fig), which
# measures the content and moves the whole grid so the margins are equal;
# and audits call grid_problems(fig), which fails a sheet whose stacked
# panels do not share column edges, whose content is off-centre, or whose
# legend under a panel is not centred on it.

def _content_bbox(fig, r):
    """The union of every axes' tight box and every legend, in canvas px."""
    from matplotlib.transforms import Bbox
    boxes = []
    for ax in fig.axes:
        if not ax.get_visible():
            continue
        boxes.append(ax.get_tightbbox(renderer=r))
        lg = ax.get_legend()
        if lg is not None:
            boxes.append(lg.get_window_extent(renderer=r))
    # fig.texts (a foot note at fixed figure coordinates) are furniture, not
    # the grid: they do not move with subplots_adjust and a left-aligned
    # note would pin the union's left edge, so they are not measured here.
    return Bbox.union(boxes)


def centre(fig, exclude_fig_texts=True):
    """Shift the subplot grid so the sheet's content is centred left-right in
    the canvas. Call after every panel and legend is placed and before the
    audit and save. Only the horizontal margins move; the vertical layout is
    the builder's."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W = fig.canvas.get_width_height()[0]

    def off():
        bb = _content_bbox(fig, fig.canvas.get_renderer())
        return (W / 2) - (bb.x0 + bb.x1) / 2

    shift_px = off()
    # a subplot grid moves with its margins; axes placed by add_axes(), or
    # under a layout engine, do not, so those are moved one by one
    sp = fig.subplotpars
    fig.subplots_adjust(left=sp.left + shift_px / W, right=sp.right + shift_px / W)
    fig.canvas.draw()
    rest = off()
    if abs(rest) > 0.5:
        try:
            fig.set_layout_engine("none")
        except Exception:
            pass
        for ax in fig.axes:
            p = ax.get_position()
            ax.set_position([p.x0 + rest / W, p.y0, p.width, p.height])
        fig.canvas.draw()
    return shift_px


def grid_problems(fig, tol=3.0, colourbar_px=30):
    """The assertions that would have caught the model chart. For a figure
    with more than one axes: (1) two panels whose x-ranges overlap - one above
    the other - share their left and right edges within tol px, so the sheet
    has columns; (2) the content is centred in the canvas within tol; (3) a
    legend hung outside a panel, below it, is centred on that panel within
    tol. Axes narrower than colourbar_px are colourbars and are skipped."""
    axes = [ax for ax in fig.axes if ax.get_visible()]
    if len(axes) < 2:
        return []
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W = fig.canvas.get_width_height()[0]
    out = []
    boxes = [(ax, ax.get_window_extent(renderer=r)) for ax in axes]
    panels = [(ax, b) for ax, b in boxes if b.width >= colourbar_px]
    for i in range(len(panels)):
        for j in range(i + 1, len(panels)):
            a, b = panels[i][1], panels[j][1]
            overlap_x = min(a.x1, b.x1) - max(a.x0, b.x0)
            overlap_y = min(a.y1, b.y1) - max(a.y0, b.y0)
            if overlap_x > 0 and overlap_y <= 0:      # stacked, not side by side
                same = abs(a.x0 - b.x0) <= tol and abs(a.x1 - b.x1) <= tol
                # a full-width row over a column is a grid too (the
                # throughlines sheet: panels A and B over C and D)
                spans = (a.x0 <= b.x0 + tol and a.x1 >= b.x1 - tol) or \
                        (b.x0 <= a.x0 + tol and b.x1 >= a.x1 - tol)
                if not (same or spans):
                    out.append(f"grid: stacked panels do not share a column: "
                               f"{a.x0:.0f}-{a.x1:.0f} over {b.x0:.0f}-{b.x1:.0f}")
    bb = _content_bbox(fig, r)
    off = (bb.x0 + bb.x1) / 2 - W / 2
    if abs(off) > tol:
        out.append(f"grid: content off-centre by {off:+.1f}px (margins {bb.x0:.0f} left, {W - bb.x1:.0f} right)")
    for ax, b in panels:
        lg = ax.get_legend()
        if lg is None:
            continue
        lb = lg.get_window_extent(renderer=r)
        if lb.y1 <= b.y0 + tol:                        # hung below the panel
            if abs((lb.x0 + lb.x1) / 2 - (b.x0 + b.x1) / 2) > tol:
                out.append(f"grid: legend under a panel is off its centre by "
                           f"{(lb.x0 + lb.x1) / 2 - (b.x0 + b.x1) / 2:+.1f}px")
    return out


# ---- display widths --------------------------------------------------------
NOTES, PROSE, CARD, THUMB, PHONE = 714, 1140, 1082, 542, 350
DPI = 144


def fonts():
    """Register the site's faces with matplotlib from fonts/ (OFL, see the
    licence beside them). Called by style(); safe to call twice."""
    if not os.path.isdir(FONT_DIR):
        raise RuntimeError("fonts/ is missing: the figures must use the site's face")
    for f in os.listdir(FONT_DIR):
        if f.endswith((".otf", ".ttf")):
            font_manager.fontManager.addfont(os.path.join(FONT_DIR, f))


def style(extra=None):
    """rcParams for every builder. Builders may pass their own layout keys."""
    fonts()
    rc = {
        "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
        "text.color": INK, "axes.labelcolor": INK, "axes.titlecolor": INK,
        "xtick.color": DIM, "ytick.color": DIM,
        "axes.edgecolor": RULE, "grid.color": RULE, "grid.alpha": 0.7,
        "font.family": FONT, "font.size": FS_1,
        "axes.titlesize": FS_1, "axes.labelsize": FS_1,   # titles are panel labels, see panel()
        "xtick.labelsize": FS_2, "ytick.labelsize": FS_2, "legend.fontsize": FS_2,
        "figure.dpi": 72, "savefig.dpi": DPI,
        "axes.prop_cycle": matplotlib.cycler(color=CYCLE),
    }
    if extra:
        rc.update(extra)
    matplotlib.rcParams.update(rc)


def wrap_label(text, cols=26):
    """An axis label that no longer fits its own axis at a narrower width.

    Wrapping changes where the words break, not which words they are, so it is
    mechanical rather than a rewrite - section 1 of the Phase 2 packet bans
    changing what a page says, and this does not.

    Lives here because four builders need it. heat/figstyle.py had the first
    copy on 2026-09-12 and now delegates to this one; a helper whose constant
    is a measurement should have exactly one place to be wrong.

    THE TWO COLUMN COUNTS, AND WHAT EACH WAS MEASURED AGAINST. They are not
    interchangeable and neither is a default:

      26  HORIZONTAL labels - an x axis label, or a colourbar's. Measured over
          all 28 figures re-rendered at 350 on 2026-09-12: of every global
          lever tried, wrapping at 26 was the only one that cleared a figure
          outright (heat's fig3_costgap_contour), and the same sweep made four
          other figures worse. Applied per figure, never as a rule.
      11  ROTATED labels - a y axis label, which overflows along the figure's
          SHORT axis. Measured on storage's fig1_prices at 350 on 2026-09-13,
          where 26 returned "Mean price [$/MWh]" unchanged (18 characters) and
          the audit still reported it off canvas. 11 clears it.

    SUPERSEDED BY fit_label, 2026-09-13. The trigger below fired four times
    in one session - lq_orders, heat's fig5_emissions_parity, and heat's
    fig1 and fig4 - so the count was replaced by a measurement. This is kept
    for heat's fig3_costgap_contour, which it already sizes correctly and
    which is not worth re-deriving and re-publishing to prove a point. New
    labels go to fit_label.

    THE TRIGGER: A THIRD COLUMN COUNT MEANS THIS PARAMETER IS THE WRONG SHAPE.
    A character count is a stand-in for a width, and this tree has a history
    with that: STATE.md's pattern 1 is estimating text dimensions instead of
    measuring them, and every instance found has been wrong. The app run's
    `(name.length + 6) * 6.6` was the same mistake with the multiplier written
    down; a wrap column is the same mistake with the multiplier implied. Both
    numbers above survive only because a figure's own audit() catches the
    misses - they are not measurements of the label being wrapped.

    So: **if a third figure needs a column count that is neither 26 nor 11,
    do not add it.** Replace the count with a measurement - the label's
    rendered extent, from get_window_extent at the size the figure will be
    saved at, against the extent of the axis it runs along. The precedent is
    longevity's label gutter (5ac8b2b): guessed at 58px, measured at 78px,
    identical at every viewport, and the guess was the whole of what was
    wrong. Two constants with their conditions recorded is acceptable. Three
    is the tree saying the parameter is the wrong shape.
    """
    import textwrap
    if not text or "\n" in text or len(text) <= cols:
        return text
    return "\n".join(textwrap.wrap(text, cols))


# ---- fit_label: measured against the audit's own predicate -----------------
# NO CACHE, AND THE SPEC ASKED FOR ONE. The instruction was to cache the
# measurement by string, which is right when what you measure is a string's
# rendered extent. Once the acceptance test became the audit's own predicate
# - is this box inside the canvas, does it hit any other text - the verdict
# stopped being a property of the string and became one of the whole figure:
# the same label passes on one figure and fails on the next. A cache keyed by
# string would be wrong across figures and useless within one, where each
# candidate is tried once. Stated rather than left as an empty dict with a
# docstring about caching.

def _boxes(fig, renderer, skip=None):
    """Every drawn text's box, the way each builder's audit() enumerates them:
    fig.texts, the titles through titles(), the axis labels, ax.texts, the tick
    labels inside the view limits, and the legend's entries. Never findobj,
    which returns ticks that were never drawn (trap 4)."""
    out = []
    for tx in fig.texts:
        if tx is not skip and tx.get_text().strip():
            out.append(tx)
    for ax in fig.axes:
        for tx in titles(ax) + [ax.xaxis.label, ax.yaxis.label] + list(ax.texts):
            if tx is not skip and tx.get_text().strip():
                out.append(tx)
        if ax.axison:
            x0, x1 = sorted(ax.get_xlim())
            y0, y1 = sorted(ax.get_ylim())
            for axis, lo, hi in ((ax.xaxis, x0, x1), (ax.yaxis, y0, y1)):
                if not axis.get_visible():
                    continue
                for loc, lab in zip(axis.get_ticklocs(), axis.get_ticklabels()):
                    if lo - 1e-9 <= loc <= hi + 1e-9 and lab is not skip \
                            and lab.get_text().strip() and lab.get_visible():
                        out.append(lab)
        lg = ax.get_legend()
        if lg:
            out += [x for x in lg.get_texts()
                    if x is not skip and x.get_text().strip()]
    boxes = []
    for tx in out:
        try:
            boxes.append(tx.get_window_extent(renderer=renderer))
        except Exception:                                         # noqa: BLE001
            pass
    return boxes


def fit_label(ax, which, text, overlap=0.15):
    """Wrap an axis label so it neither runs off the canvas nor lands on other
    text - or fail, saying what it tried.

    A LABEL ROTATED 90 DEGREES HAS TWO CONSTRAINTS THAT PULL OPPOSITE WAYS. The
    text runs along the axis; the LINE COUNT stacks perpendicular to it. So
    wrapping trades one overflow for the other, and this tree has one example of
    each:

      storage's "Mean price [$/MWh]" was too long ALONG the axis. Two lines
      halved that and it cleared, spending width it had to spare.
      heat's "Emissions  [kgCO2 / MMBtu delivered]" was already two lines and
      too WIDE. Wrapping it further made it wider still and put it into the
      legend.

    Same lever, opposite directions - which is why no single column count could
    be right, and why wrap_label's 26 and 11 were never two values of one
    number. They were two different constraints, each measured once and then
    used as if it were the other's default.

    THE ACCEPTANCE TEST IS THE AUDIT'S OWN PREDICATE, NOT A RECONSTRUCTION OF
    IT. The first version of this computed the room from the axes box and the
    tick labels and compared extents against it; it rejected the storage label
    that the real figure passes, because a y label may legitimately run past
    the axes into the figure's margins and the audit only cares about the
    CANVAS. So each candidate is applied, drawn, and judged by exactly what
    audit() asks: is this label's box inside the canvas, and does it overlap
    any other drawn text by more than `overlap`. A lever judged by a
    paraphrase of the gate is a lever that can pass while the gate fails.

    Candidates run from unwrapped to narrow and the FIRST that passes wins -
    the fewest lines, which spends the least room perpendicular to the text.

    IT FAILS RATHER THAN RETURNING THE LEAST-BAD WRAP. A label that fits in
    neither direction is a figure whose layout needs changing, and quietly
    picking the closest miss is how a lever becomes the thing that hid the
    problem. The ValueError names the label and every candidate tried.

    Call after the axes are drawn and sized, with the figure at the size it
    will be saved at: the canvas it measures against is the canvas the saved
    figure has.
    """
    import textwrap
    label = ax.yaxis.label if which == "y" else ax.xaxis.label
    fig = ax.figure
    keep = label.get_text()

    def bad(candidate):
        """(off_canvas, overlaps) for this candidate, measured after a draw."""
        label.set_text(candidate)
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        W, H = fig.canvas.get_width_height()
        b = label.get_window_extent(renderer=r)
        off = b.x0 < -1 or b.y0 < -1 or b.x1 > W + 1 or b.y1 > H + 1
        hits = 0
        for o in _boxes(fig, r, skip=label):
            ox = min(b.x1, o.x1) - max(b.x0, o.x0)
            oy = min(b.y1, o.y1) - max(b.y0, o.y0)
            if ox > 0 and oy > 0:
                area = min(b.width * b.height, o.width * o.height)
                if area > 0 and (ox * oy) / area > overlap:
                    hits += 1
        return off, hits

    seen, tried = set(), []
    for cols in [len(text)] + list(range(len(text) - 1, 3, -1)):
        cand = text if cols >= len(text) else "\n".join(textwrap.wrap(text, cols))
        if cand in seen:
            continue
        seen.add(cand)
        off, hits = bad(cand)
        tried.append((cand.count("\n") + 1, "off" if off else "-", hits))
        if not off and not hits:
            return cand
    label.set_text(keep)
    fig.canvas.draw()
    raise ValueError(
        "fit_label: %r fits nowhere on this axis. Tried %d wraps; "
        "(lines, off-canvas, overlaps) = %s. A label that fits in neither "
        "direction is a layout to change, not a wrap to tune."
        % (text, len(tried), tried[:6]))


def fit_ticks(ax, which="y", overlap=0.15):
    """Fit an axis's TICK LABELS, or fail saying what was tried.

    fit_label's sibling, and scoped the same way: it governs exactly one artist
    class. The audit names four - hand-placed ax.text, tick labels, axis labels,
    and legend collisions - and a lever aimed at the wrong one either raises on
    something that was never the complaint or returns quietly having changed
    nothing, which is indistinguishable from a tree with no problem (trap 27).

    SAME CONTRACT AS fit_label, AND THE FIRST CLAUSE IS TRAP 37:

      - the acceptance test is audit()'s own predicate, called directly on the
        drawn figure. Not a restatement of it.
      - it RAISES when no candidate satisfies the predicate. It never returns
        the least-bad one.
      - two constraints at once, because tick labels have the geometry problem
        rotated labels do: the extent ALONG the axis (crowding between
        neighbouring ticks) and the extent PERPENDICULAR to it (running off the
        canvas) trade against each other. Wrapping a y tick shortens it
        horizontally and makes it taller, so it buys off-canvas with crowding;
        widening the margin buys off-canvas with plot area. Both counts are
        reported when it raises.

    CANDIDATES, ALL PRESENTATION AND NONE OF THEM CONTENT. Wrapping changes
    where words break; a margin moves the axes. Neither changes what a label
    says. TICK THINNING IS DELIBERATELY NOT IN THE SET: on a categorical axis
    dropping every other tick removes a category a reader can currently read,
    which is removal of reachable content and escalates rather than being a
    lever's to take. Four of the five axes this was built for are categorical -
    term names, strata, allocation bases, species names - so thinning is not
    available on them even in principle. The fifth, continents_fig3_rigidity,
    is NUMERIC: 0.1, 1, 10, 100 on a log axis, where thinning would drop a
    decade a reader can currently read off the grid. Same answer, different
    reason, and the distinction is written down because "they are all
    categorical" was said out loud before the ticks were looked at.

    Returns a short description of what it applied, for the caller's comment.
    """
    import textwrap
    axis = ax.yaxis if which == "y" else ax.xaxis
    fig = ax.figure
    fig.canvas.draw()

    def labels():
        return [l for l in (axis.get_ticklabels() or [])
                if l.get_visible() and l.get_text().strip()]

    original = [l.get_text() for l in labels()]
    locs = list(axis.get_ticklocs())
    base_pos = ax.get_position().bounds
    if not original:
        return "no tick labels"

    def apply(cols, margin):
        ax.set_position(list(base_pos))
        if margin:
            x0, y0, w, h = base_pos
            if which == "y":
                ax.set_position([x0 + margin, y0, max(0.05, w - margin), h])
            else:
                ax.set_position([x0, y0 + margin, w, max(0.05, h - margin)])
        text = original if cols is None else \
            ["\n".join(textwrap.wrap(s, cols)) or s for s in original]
        if which == "y":
            ax.set_yticks(locs)
            ax.set_yticklabels(text)
        else:
            ax.set_xticks(locs)
            ax.set_xticklabels(text)
        fig.canvas.draw()

    def judge():
        r = fig.canvas.get_renderer()
        W, H = fig.canvas.get_width_height()
        mine = [(l, l.get_window_extent(renderer=r)) for l in labels()]
        others = _boxes(fig, r)
        off = sum(1 for _, b in mine
                  if b.x0 < -1 or b.y0 < -1 or b.x1 > W + 1 or b.y1 > H + 1)
        hits = 0
        for i, (_, b) in enumerate(mine):
            for o in others:
                if abs(o.x0 - b.x0) < 1e-6 and abs(o.y0 - b.y0) < 1e-6:
                    continue                       # itself
                ox = min(b.x1, o.x1) - max(b.x0, o.x0)
                oy = min(b.y1, o.y1) - max(b.y0, o.y0)
                if ox > 0 and oy > 0:
                    area = min(b.width * b.height, o.width * o.height)
                    if area > 0 and (ox * oy) / area > overlap:
                        hits += 1
        return off, hits

    longest = max(len(s) for s in original)
    # Least invasive first: no change, then margin alone, then wrapping alone,
    # then both. Fewer lines and a smaller margin spend less of the figure.
    plan = [(None, 0.0)]
    plan += [(None, m) for m in (0.03, 0.06, 0.10, 0.14)]
    wraps = [c for c in (longest - 2, 18, 14, 12, 10, 8) if 4 <= c < longest]
    plan += [(c, 0.0) for c in wraps]
    plan += [(c, m) for m in (0.03, 0.06, 0.10) for c in wraps]

    tried, seen = [], set()
    for cols, margin in plan:
        key = (cols, round(margin, 3))
        if key in seen:
            continue
        seen.add(key)
        apply(cols, margin)
        off, hits = judge()
        tried.append((cols, round(margin, 2), off, hits))
        if off == 0 and hits == 0:
            return ("unchanged" if key == (None, 0.0) else
                    "wrap %s, margin %+.0f%%" % (cols or "none", margin * 100))
    apply(None, 0.0)
    raise ValueError(
        "fit_ticks: the %s tick labels fit nowhere on this axis. Tried %d "
        "candidates; (wrap cols, margin, off-canvas, overlaps) = %s. Off-canvas "
        "is the perpendicular constraint and overlaps the along-axis one; when "
        "both stay non-zero no wrap or margin resolves it and the figure's "
        "ARRANGEMENT is what has to change."
        % (which, len(tried), tried[:8]))


def fig_size(display_px, aspect):
    """figsize in inches for a figure displayed display_px CSS pixels wide,
    at one point per pixel: (w, h) with w = display_px / 72."""
    w = display_px / 72.0
    return (w, w / aspect)


def save(fig, path, close=True):
    """Save at two pixels per CSS pixel, then quantise to an 8-bit palette
    when that is smaller (it always is for a chart) and keep the smaller
    file. Returns the size in bytes."""
    import matplotlib.pyplot as plt
    bad = unlabelled_panels(fig)
    if bad:
        raise RuntimeError("panel label(s) not set through sitefig.panel(): "
                           + "; ".join(repr(b[:40]) for b in bad))
    fig.savefig(path, dpi=DPI, facecolor=BG)
    if close:
        plt.close(fig)
    try:
        from PIL import Image
        im = Image.open(path).convert("RGB")
        q = im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        tmp = path + ".q.png"
        q.save(tmp, optimize=True)
        if os.path.getsize(tmp) < os.path.getsize(path):
            os.replace(tmp, path)
        else:
            os.remove(tmp)
    except ImportError:
        pass
    return os.path.getsize(path)


def thumbnail(src, dst, width=THUMB):
    """A thumbnail of a rendered figure: the whole figure, scaled to `width`
    CSS px at its own aspect, quantised. It was written for the home-page
    mosaic, whose 16:9 tiles letterboxed in CSS on the figure's own ground;
    that mosaic and its builder were retired on 2026-09-06 when the home page
    became the hero canvas plus the index, so nothing calls this today
    (unpublished/build_thumbnails.py). Kept because it is a library function
    and the crop lesson below is the reason it exists at all.

    Never a crop. The first version of this cover-cropped to 3:2, and every
    card on the home page lost its right edge or its top and bottom - axis
    labels, the last bar, half a box - while the CSS looked innocent,
    because a 3:2 image in a 3:2 box is not cropped by object-fit: cover. A
    thumbnail that shows a slice is a different figure from the one the
    caption describes. (A fixed-canvas mode with fit and crop lived here for
    one day, 2026-09-04, for the project cards; the cards and the mode went
    together on 2026-09-05. If a fixed tile shape is wanted again, the page
    letterboxes; the asset stays whole.)"""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    w, h = im.size
    im = im.resize((width, round(h * width / w)), Image.LANCZOS)
    im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(dst, optimize=True)
    return os.path.getsize(dst)
