"""The kit's test clip (R1): eight seconds, synthetic, proves the pipeline.

A line draws across house axes, a dot and a label mark its end, and the
frame holds. It says nothing about any data and appears only on the kit's
fixture page (tests/fixtures/kit.html), never on the site.

    python clips/render_clip.py clips/scenes/kit_test.py KitTest --name kit-test --out tests/fixtures/clips
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from house import *  # noqa: E402,F401,F403
from manim import Create, FadeIn, Dot, Write  # noqa: E402


class KitTest(HouseScene):
    TITLE = "A synthetic test clip: a line drawn on axes"
    CAPTIONS = [
        (0.0, 2.0, "Synthetic test clip. Axes appear."),
        (2.0, 5.2, "A made-up line draws across them."),
        (5.2, 8.0, "Its end is marked and the frame holds."),
    ]
    POSTER_T = 7.5

    def construct(self):
        ax = house_axes([0, 10, 1], [0, 5, 1], x_length=10.5, y_length=5)
        ax.shift(DOWN * 0.4)
        head = label("Synthetic test clip", size=TITLE, weight="SEMIBOLD").to_edge(UP)
        self.play(FadeIn(head), Create(ax), run_time=MOVE)
        self.wait(2.0 - MOVE)
        curve = ax.plot(lambda x: 0.8 + 0.35 * x + 0.4 * math.sin(x * 1.3), x_range=[0, 10], color=ACC, stroke_width=5)
        self.play(Create(curve), run_time=DRAW)
        self.wait(5.2 - 2.0 - DRAW)
        end = ax.c2p(10, 0.8 + 3.5 + 0.4 * math.sin(13))
        dot = Dot(end, color=MOSS, radius=0.09)
        tag = number("end", size=SMALL, color=MOSS).next_to(dot, UP + LEFT * 0.4, buff=0.15)
        self.play(FadeIn(dot), Write(tag), run_time=MOVE)
        self.wait(8.0 - 5.2 - MOVE)
