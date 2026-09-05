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
  THUMB   542   a 3:2 card or mosaic thumbnail at two pixels per CSS pixel
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
    """A panel label: mono, FS_1, muted, left-aligned above the axes."""
    ax.set_title(text, loc="left", pad=pad, fontsize=FS_1, color=DIM, fontfamily=MONO)


# ---- display widths --------------------------------------------------------
NOTES, PROSE, CARD, THUMB = 714, 1140, 1082, 542
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
    CSS px at its own aspect, quantised. For the mosaic and the home-page
    cards (build_thumbnails.py).

    Never a crop. The first version of this cover-cropped to 3:2, and every
    card on the home page lost its right edge or its top and bottom - axis
    labels, the last bar, half a box - while the CSS looked innocent, because
    a 3:2 image in a 3:2 box is not cropped by object-fit: cover. A thumbnail
    that shows a slice is a different figure from the one the caption
    describes. If a fixed tile shape is wanted, the page letterboxes
    (object-fit: contain on the figure's own ground colour); the asset stays
    whole."""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    w, h = im.size
    im = im.resize((width, round(h * width / w)), Image.LANCZOS)
    im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(dst, optimize=True)
    return os.path.getsize(dst)
