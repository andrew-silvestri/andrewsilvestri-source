"""House style for the site's Manim clips (R1, 2026-10-23).

Palette, fonts and timing for every clip on andrewsilvestri.com. Scenes do
`from house import *` and subclass HouseScene.

THIS FILE IMPORTS NOTHING FROM MANIM_WORKSPACE/shared OR ITS projects/.
That library is the summer 2026 internship's: its style.py is the employer's
palette by name, its data.py reads company workbooks, its mobjects.py draws a
company project's figure. CLAUDE.md "Employer material" forbids all of it
here. The workspace's .venv is used only as an interpreter for the public
manim package (render_clip.py says how). projects/site_bg/README.md in the
workspace records the same separation from August.

The palette is read from sitefig.py BY NAME, so the clips, the figures and
style.css stay one set of colours (HANDOFF section 4); nothing here types a
hex value.
"""
import os
import re

from manim import (Scene, Text, Axes, VGroup, config, UP, DOWN, LEFT, RIGHT)
import manimpango

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.dirname(HERE)


def _palette():
    src = open(os.path.join(PUB, "sitefig.py"), encoding="utf-8").read()
    out = {}
    for name in ("BG", "CARD_FILL", "INK", "DIM", "RULE", "FAINT", "ACC", "COOL", "MOSS", "ROSE"):
        m = re.search(r'^%s\s*=\s*"(#[0-9A-Fa-f]{6})"' % name, src, re.M)
        if not m:
            raise RuntimeError("house.py: sitefig.py has no %s; the clip palette follows sitefig by name" % name)
        out[name] = m.group(1)
    return out


PAL = _palette()
BG, INK, DIM, RULE, FAINT, ACC, MOSS = (PAL[k] for k in ("BG", "INK", "DIM", "RULE", "FAINT", "ACC", "MOSS"))

# IBM Plex, the site's faces (OFL, fonts/LICENSE-IBMPlex.txt), registered
# from the repo so a render does not depend on what the machine has installed
for f in ("IBMPlexSans-Regular.otf", "IBMPlexSans-SemiBold.otf", "IBMPlexMono-Regular.otf"):
    manimpango.register_font(os.path.join(PUB, "fonts", f))
SANS, MONO = "IBM Plex Sans", "IBM Plex Mono"

# Timing, in seconds. One set for every clip, so they move alike.
BEAT = 0.6      # a pause the eye needs between two things
MOVE = 1.2      # a transform, a fade
DRAW = 2.4      # drawing a line or a curve across the frame
HOLD = 1.5      # the last frame held before a loop restarts

# Text sizes, in manim's font_size. At 1280x720 a font_size of 28 renders
# glyphs about 20px tall in a frame that is shown at most 1140px wide.
TITLE, LABEL, SMALL = 34, 28, 24

config.background_color = BG


def label(text, size=LABEL, color=None, weight="NORMAL"):
    return Text(text, font=SANS, font_size=size, color=color or INK, weight=weight)


def number(text, size=LABEL, color=None):
    return Text(text, font=MONO, font_size=size, color=color or INK)


def house_axes(x_range, y_range, x_length=10, y_length=5, **kw):
    """Axes in the figures' style: rule-grey lines, no arrow tips, dim ticks."""
    return Axes(x_range=x_range, y_range=y_range, x_length=x_length, y_length=y_length,
                tips=False,
                axis_config={"color": RULE, "stroke_width": 2, "include_ticks": True,
                             "tick_size": 0.06},
                **kw)


class HouseScene(Scene):
    """A clip. Subclasses set:

    TITLE     what the clip shows, one line (the play button's label and the
              metadata's title)
    CAPTIONS  [(start_s, end_s, text), ...] - written to the .vtt by
              render_clip.py, which refuses cues that overlap or run past the
              clip's measured duration
    POSTER_T  the second the poster frame is taken at (default: the end)
    """
    TITLE = ""
    CAPTIONS = []
    POSTER_T = None

    def setup(self):
        self.camera.background_color = BG
