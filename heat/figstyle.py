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

import matplotlib
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import fig_floor
from sitefig import BG, INK, DIM, RULE, FAINT, ACC, COOL, MOSS, ROSE, SLATE, DISTRICT, SUPPLY, PSYCH, SUN, INSOL, GOLD, GREY, VIOLET, BLUE, GREEN, WARM, ARROW, ONE_WAY_COL, TWO_WAY_COL, NODE_COL, WARM2, KCOL, CYCLE, FS_2, FS_1, FS0, FS1, FS2, FONT, MONO, NOTES, PROSE, CARD, THUMB, fig_size, save, WIDE, PLOT, SQUARE, TALL, row_aspect, panel  # noqa: E402,F401
import sitefig  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt

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


def finish(fig, path, title=None, subtitle=None):
    # Titles and subtitles are no longer drawn (2026-09-04): the page heading
    # above the figure and the caption under it carry that. The arguments are
    # kept so the callers need not change.
    title = subtitle = None
    """Save with a consistent header block above the axes.

    The header is placed by reserving a strip at the top of the figure and
    telling the layout engine not to use it. Writing a title with suptitle and
    hoping is what produces the collisions this module exists to prevent: the
    engine does not know the text is there, lays the axes out into the full
    height, and the two meet.
    """
    if not title:
        # No header strip to reserve, but the collision audit still has to run
        # here - skipping it whenever a caller omits title and subtitle left
        # every such figure unaudited on every run, silently. Both lines above
        # force title to None, so this branch is EVERY figure this module has
        # ever saved: all five heat figures reported nothing, and every
        # "0 layout problems" ever recorded for them - the app run, the site
        # sweep, every build since 2026-09-04 - came from a check that never
        # executed. storage/figstyle.py carries the same fix and the same
        # reason; the two files diverged when only one of them was repaired.
        #
        # AFTER save, not before, and that is not a style choice. audit() draws
        # twice to let constrained layout settle, and on a constrained-layout
        # figure those draws move things: calling it first rewrote
        # fig3_costgap_contour.png to bytes that differ from the published
        # file, so the repair itself would have moved a figure on a live page.
        # Auditing after also measures the figure that actually shipped rather
        # than a state on the way to it. storage/figstyle.py audits first and
        # has the same exposure; it is left alone here because that is its own
        # figure to move and its own decision.
        sitefig.save(fig, path, close=False)
        audit(fig, path)
        plt.close(fig)
        return

    # Reserve height in figure fractions: one line for the title, one more for
    # a subtitle if there is one, plus breathing room.
    h = fig.get_size_inches()[1]
    strip = (0.42 if subtitle else 0.28) / h
    try:
        fig.get_layout_engine().set(rect=(0, 0, 1, 1 - strip))
    except AttributeError:                       # older matplotlib
        fig.subplots_adjust(top=1 - strip)

    fig.text(0.028, 0.995, title, fontsize=FS0, color=INK, ha="left",
             va="top", weight="medium")
    if subtitle:
        fig.text(0.028, 0.995 - (0.235 / h), subtitle, fontsize=FS_1,
                 color=DIM, ha="left", va="top")
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
        # sitefig.titles(ax), never ax.title. ax.title is only the CENTRE
        # title; sitefig.panel() sets a left-aligned one and matplotlib keeps
        # that in ax._left_title, so an audit reading ax.title sees no panel
        # label at all and passes a sheet whose label sits on a legend. That is
        # trap 21, and it shipped once already on energy_model_chart.png. Both
        # figstyle modules had it until 2026-09-11; neither heat nor storage
        # draws a panel label today, so nothing was escaping - the first
        # multi-panel figure either one gained would have gone unchecked.
        for _t in sitefig.titles(ax):
            add(_t, is_title=True)
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
    for txt, bb, _, _obj, _t in items:
        if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > W + 1 or bb.y1 > H + 1:
            bad.append(f"off canvas: {txt!r}")
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            t1, b1, k1 = items[i][:3]
            t2, b2, k2 = items[j][:3]
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
    # the other way a figure fails its reader - type too small to read at the
    # width the figure is drawn for. Same item enumeration, so it cannot
    # disagree with the checks above about what text is on the page.
    # storage/figstyle.py has had this since it was written; heat never
    # imported fig_floor at all, so the two files disagreed about what an
    # audit is.
    bad += fig_floor.floor_problems(fig, [(obj, title) for _, _, _, obj, title in items])
    name = os.path.basename(path)
    if bad:
        print(f"  LAYOUT  {name}")
        for b in bad[:5]:
            print(f"            {b}")
    PROBLEMS.extend(f"{name}: {b}" for b in bad)
    return bad


# Every problem every audit() found this run, as "figure.png: what".
PROBLEMS = []


def verdict():
    """The exit status for a builder run: 0 only if every figure audited clean.

    audit() printed its findings and returned them, and finish() dropped the
    return value on the floor, so a run whose output carried five LAYOUT blocks
    still exited 0. That is trap 26 in its purest form, and it means every
    "must report 0 layout problems" in HANDOFF section 4, 5 and 7 has been a
    claim about output a human reads rather than an assertion anything made.
    A figure builder now fails when its own audit fails.
    """
    print(f"  {len(PROBLEMS)} layout problem(s) in total")
    for p in PROBLEMS[:10]:
        print("    " + p)
    return 1 if PROBLEMS else 0


# The narrow render's name, and the one place the "-phone" spelling lives.
# storage/figstyle.py carries the same helper; the page's <source srcset> has to
# name exactly this file and a typo there is a figure that silently never loads.
def phone_path(path):
    return path[:-4] + "-phone.png" if path.endswith(".png") else path + "-phone"


# A label that no longer fits its own axis at a narrower width. Wrapping changes
# where the words break and not which words they are, so it is mechanical
# rather than a rewrite - section 1 bans changing what a page says, and this
# does not. 26 characters is the measured setting: over the 28 figures at 350 it
# was the only global lever that cleared a figure outright, and this is that
# figure. It is applied per figure rather than globally because the same sweep
# made four other figures worse.
def wrap_label(text, cols=26):
    import textwrap
    if not text or "\n" in text or len(text) <= cols:
        return text
    return "\n".join(textwrap.wrap(text, cols))


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
