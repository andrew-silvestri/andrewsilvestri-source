"""
The on-screen-size floor every figure generator's own audit() checks, in
addition to the overlap and off-canvas checks each already had.

For a figure rendered in the site's `wide` track (1140 CSS px):

    on_screen_px = pt * 1140 / (72 * figsize_width_inches)

`dpi` does not appear on the right-hand side. It sets how many bitmap pixels
sit behind each CSS pixel, which changes how crisp the type looks on a
retina screen and changes nothing else about how big a reader sees it - it
cannot turn an unreadable label into a readable one. The only two levers that
do anything here are the point size and the figure's width in inches, so
those are the only two things this checks, and this is the one place the
arithmetic lives rather than four copies of it that drift.

Target: 11px for anything a reader has to read, 13px for a panel title.

Import `floor_problems` and call it from inside a generator's existing
audit() with the same list of text artists that audit() already assembled
for the overlap check - one enumeration, not two passes that can disagree
about what is actually on the page.
"""

WIDE_TRACK_PX = 1140
MIN_PX = 11.0
MIN_TITLE_PX = 13.0


def on_screen_px(pt, figsize_w_in):
    """What a `pt`-sized label in a figure `figsize_w_in` inches wide, placed
    in the site's wide (1140px) track, actually measures on screen."""
    return pt * WIDE_TRACK_PX / (72.0 * figsize_w_in)


def floor_problems(fig, items):
    """items: iterable of (text_artist, is_title). Returns problem strings in
    the same shape the callers already print, so they can be appended
    directly onto the overlap/off-canvas list.
    """
    w_in = fig.get_size_inches()[0]
    bad = []
    seen = set()
    for t, is_title in items:
        txt = t.get_text().strip()
        if not txt:
            continue
        key = id(t)
        if key in seen:
            continue
        seen.add(key)
        size = t.get_fontsize()
        px = on_screen_px(size, w_in)
        floor = MIN_TITLE_PX if is_title else MIN_PX
        if px < floor - 1e-6:
            kind = "title" if is_title else "label"
            bad.append(f"under floor ({kind}): {txt[:30]!r} "
                       f"{size:g}pt -> {px:.1f}px (needs {floor:.0f})")
    return bad
