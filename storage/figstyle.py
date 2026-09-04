"""
Shared figure style.

Every figure on the site is read on a dark page at about 1,100 pixels wide,
often on a phone. That imposes three rules the default matplotlib style breaks:

  1. Nothing overlaps. Labels are placed by the layout engine, not by hand at
     hard-coded data coordinates, because a hand-placed annotation is correct
     for exactly one set of numbers and collides the moment the numbers move.
  2. Type is large enough to survive being scaled down. Ten-point axis labels
     in a 8-inch figure become illegible at 1,100 pixels.
  3. One idea per panel. A ten-panel figure at web width is ten unreadable
     panels.

Call `use()` once at import. Call `finish(fig, path)` instead of savefig to get
consistent margins and a transparent-friendly background.
"""

import os
import sys

import matplotlib
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from sitefig import BG, INK, DIM, RULE, FAINT, ACC, COOL, MOSS, ROSE, SLATE, DISTRICT, SUPPLY, PSYCH, SUN, INSOL, GOLD, GREY, VIOLET, BLUE, GREEN, WARM, ARROW, ONE_WAY_COL, TWO_WAY_COL, NODE_COL, WARM2, KCOL, CYCLE, FS_2, FS_1, FS0, FS1, FS2, FONT, MONO, NOTES, PROSE, CARD, THUMB, fig_size, save, WIDE, PLOT, SQUARE, TALL, row_aspect, panel  # noqa: E402,F401
import sitefig  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fig_floor

# The site palette, so figures sit on the page rather than on top of it.
# Matches site/style.css's :root custom properties exactly - this module's
# colors had drifted from an older brass/gold palette while the live site
# moved to violet/blue, so figures regenerated from here were mismatched
# against the page around them until this was brought back in sync.


def use():
    sitefig.style(); plt.rcParams.update({
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "savefig.facecolor": BG,
        "figure.constrained_layout.use": True,
        "figure.constrained_layout.h_pad": 0.08,
        "figure.constrained_layout.w_pad": 0.08,

        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "xtick.color": DIM,
        "ytick.color": DIM,

        "axes.edgecolor": RULE,
        "axes.linewidth": 0.9,
        "axes.grid": True,
        "grid.color": RULE,
        "grid.alpha": 0.55,
        "grid.linewidth": 0.7,

        "axes.spines.top": False,
        "axes.spines.right": False,

        "font.size": FS_1,
        # Match the site, which sets its UI text in the system sans
        # stack. Named as a list so this still renders sensibly on a
        # machine without Segoe UI rather than falling back to boxes.
        "font.family": FONT,
        "axes.titlesize": FS0,
        "axes.titleweight": "medium",
        "axes.labelsize": FS_1,
        "xtick.labelsize": FS_1,
        "ytick.labelsize": FS_1,
        "legend.fontsize": FS_1,
        "legend.frameon": False,

        "lines.linewidth": 2.2,
        "lines.solid_capstyle": "round",
        "axes.prop_cycle": matplotlib.cycler(color=CYCLE),

        "savefig.dpi": 150,
        "figure.dpi": 110,
    })


def finish(fig, path, title=None, subtitle=None, footnote=None):
    # Titles and subtitles are no longer drawn (2026-09-04): the page heading
    # above the figure and the caption under it carry that; a title inside the
    # frame at body size read as a third heading. The arguments are kept so
    # the callers need not change. Footnotes stay, as figure furniture.
    title = subtitle = None
    """Save with a consistent header block above the axes, and optionally a
    footnote block below it.

    Both are placed by reserving a strip at the top/bottom of the figure and
    telling the layout engine not to use it. Writing a title with suptitle and
    hoping is what produces the collisions this module exists to prevent: the
    engine does not know the text is there, lays the axes out into the full
    height, and the two meet. A hand-placed footnote inside axes space would
    fail the same way, so it gets the same reserved-strip treatment as the
    title rather than being trusted to just fit.
    """
    if not title and not footnote:
        # No header/footer strip to reserve, but the collision/floor audit
        # still has to run here - skipping it whenever a caller omits title
        # and footnote left every such figure (including this one, before
        # this fix) unaudited on every run, silently.
        audit(fig, path)
        sitefig.save(fig, path, close=False)
        plt.close(fig)
        return

    # Reserve height in figure fractions: one line for the title, one more for
    # a subtitle if there is one, plus breathing room. Footnote height scales
    # with its line count, since callers pass anywhere from one line to a
    # short paragraph.
    h = fig.get_size_inches()[1]
    top_strip = (0.42 if subtitle else 0.28) / h if title else 0.0
    if footnote:
        # wrap to the figure's own width: at one point per pixel a line of
        # FS_1 text holds about width_px / (0.56 * FS_1) characters
        import textwrap
        cols = max(40, int(fig.get_size_inches()[0] * 72 / (FS_2 * 0.62)))
        footnote = "\n".join(textwrap.fill(p, cols) for p in footnote.split("\n"))
    n_lines = footnote.count("\n") + 1 if footnote else 0
    bottom_strip = (0.20 + 0.22 * n_lines) / h if footnote else 0.0   # FS_1 lines at 1.5 spacing, plus the tick labels above
    try:
        fig.get_layout_engine().set(rect=(0, bottom_strip, 1, 1 - top_strip))
    except AttributeError:                       # older matplotlib
        fig.subplots_adjust(top=1 - top_strip, bottom=bottom_strip)

    if title:
        fig.text(0.028, 0.995, title, fontsize=FS0, color=INK, ha="left",
                 va="top", weight="medium")
        if subtitle:
            fig.text(0.028, 0.995 - (0.235 / h), subtitle, fontsize=FS_1,
                     color=DIM, ha="left", va="top")
    if footnote:
        fig.text(0.028, 0.012, footnote, fontsize=FS_2, color=DIM, fontfamily=MONO,
                 ha="left", va="bottom", linespacing=1.5)
    audit(fig, path)
    sitefig.save(fig, path, close=False)
    plt.close(fig)


def audit(fig, path):
    """Report any text in this figure that collides with other text or runs
    off the canvas.

    This lives at save time on purpose. A figure is only correct for the
    numbers it was drawn with, so the check has to run every time the numbers
    change, not once when someone remembers to look.
    """
    # Two passes: constrained layout settles on the second, and measuring
    # before it settles produces phantom collisions.
    fig.canvas.draw()
    fig.canvas.draw()
    r = fig.canvas.get_renderer()

    # Enumerate text explicitly rather than with findobj. findobj returns tick
    # label objects that matplotlib keeps for values outside the current view
    # limits and never draws — a y axis stopping at 7.28 still owns a Text
    # reading "8", parked above the axes, reporting itself visible. Measuring
    # those invents collisions that are not on the page.
    items = []

    def add(obj, tick=False, is_title=False):
        try:
            if obj is None or not obj.get_visible() or not obj.get_text().strip():
                return
            bb = obj.get_window_extent(renderer=r)
        except Exception:
            return
        if bb.width <= 1 or bb.height <= 1:
            return
        items.append((obj.get_text().strip()[:40], bb, tick, obj, is_title))

    for tx in fig.texts:
        add(tx)
    for ax in fig.axes:
        add(ax.title, is_title=True)
        add(ax.xaxis.label)
        add(ax.yaxis.label)
        for tx in ax.texts:
            add(tx)
        leg = ax.get_legend()
        if leg is not None:
            for tx in leg.get_texts():
                add(tx)
        for axis, getter in ((ax.xaxis, ax.get_xticks),
                             (ax.yaxis, ax.get_yticks)):
            lo, hi = sorted(axis.get_view_interval())
            locs = getter()
            labels = axis.get_ticklabels()
            for loc, lab in zip(locs, labels):
                if lo - 1e-9 <= loc <= hi + 1e-9:      # only ticks on the page
                    add(lab, tick=True)

    W, H = fig.canvas.get_width_height()
    bad = []
    for txt, bb, _, _obj, _title in items:
        if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > W + 1 or bb.y1 > H + 1:
            bad.append(f"off canvas: {txt!r}")
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            t1, b1, k1, _, _ = items[i]
            t2, b2, k2, _, _ = items[j]
            if k1 and k2:
                continue
            w = min(b1.x1, b2.x1) - max(b1.x0, b2.x0)
            h = min(b1.y1, b2.y1) - max(b1.y0, b2.y0)
            if w <= 0 or h <= 0:
                continue
            frac = (w * h) / min(b1.width * b1.height, b2.width * b2.height)
            if frac > 0.12:
                bad.append(f"{int(frac*100)}% overlap: {t1!r} x {t2!r}")
    # The overlap/off-canvas checks above catch layout collisions; this catches
    # the other way a figure fails its reader - type too small to read once
    # the site scales this figure down to its 1140px wide track. Same item
    # enumeration, so it can't disagree with the checks above about what text
    # is actually on the page.
    bad += fig_floor.floor_problems(fig, [(obj, title) for _, _, _, obj, title in items])
    if bad:
        name = os.path.basename(path)
        print(f"  LAYOUT  {name}")
        for b in bad[:5]:
            print(f"            {b}")
    return bad


def note(ax, text, loc="upper left"):
    """A caption inside the axes, placed by the legend machinery so it cannot
    collide with the data."""
    from matplotlib.offsetbox import AnchoredText
    at = AnchoredText(text, loc=loc, prop=dict(size=FS_1, color=DIM),
                      frameon=True, borderpad=0.5)
    at.patch.set_facecolor(BG)
    at.patch.set_edgecolor(RULE)
    at.patch.set_alpha(0.92)
    ax.add_artist(at)
    return at
