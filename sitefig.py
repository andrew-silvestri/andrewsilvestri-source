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
    CSS px at its own aspect, quantised. For the home-page mosaic
    (build_thumbnails.py), whose 16:9 tiles letterbox in CSS on the figure's
    own ground.

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
