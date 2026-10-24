"""The lost-gas page's clip (R3): how a meter infers flow, why an error every
meter shares does not average away, and where it lands in a utility's books.

Three parts, about thirty seconds:
  1. an orifice plate: gas squeezes through the hole, the pressure falls, and
     the flow is inferred from that fall through a coefficient that comes from
     an equation, not from a measurement of this meter;
  2. many meters: each meter's own error shrinks as one over the square root
     of their number; an error they all share stays the same size;
  3. in minus out: a shared error on the customer meters (cold gas read as if
     it were at 60 F) is gas delivered and never billed, and it is reported as
     unaccounted for.

The one number it shows, the shared temperature error, is read from the
lost-gas payload (lostgas/outputs/payload.json, model.temp_bias at the page's
defaults), so the clip cannot disagree with the page.

    python clips/render_clip.py clips/scenes/lost_gas.py LostGas --name lostgas-meter --out site/assets/clips
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from house import *  # noqa: E402,F401,F403
from house import PUB  # noqa: E402
from manim import (VMobject, Create, FadeIn, FadeOut, Dot, Line, Rectangle, ValueTracker, always_redraw,  # noqa: E402
                   Transform, linear, smooth, MoveAlongPath, Succession, AnimationGroup)

PAYLOAD = json.load(open(os.path.join(PUB, "lostgas", "outputs", "payload.json"), encoding="utf-8"))
SHARED = PAYLOAD["clip"]["shared_temp_pct"]          # e.g. 0.68: % of deliveries read low
T_GAS = PAYLOAD["clip"]["gas_temp_f"]


class LostGas(HouseScene):
    TITLE = "How a gas meter can report gas as lost that was delivered"
    CAPTIONS = [
        (0.0, 4.0, "An orifice meter: gas squeezes through a hole in a plate."),
        (4.0, 8.5, "The pressure falls across the plate, and the fall says how fast the gas is moving."),
        (8.5, 12.0, "The coefficient that turns that fall into a flow comes from an equation, not from this meter."),
        (12.0, 16.5, "A utility has thousands of customer meters. Each meter's own error averages away."),
        (16.5, 21.0, "An error they all share does not: it stays the same size however many meters there are."),
        (21.0, 26.0, "One such error: a meter that does not correct for temperature reads cold gas as less gas."),
        (26.0, 31.5, "Gas in minus gas billed is reported as unaccounted for, though customers got it; its cost returns through the gas charge."),
    ]
    POSTER_T = 30.5

    def construct(self):
        self.part_meter()
        self.part_average()
        self.part_books()

    # ------------------------------------------------------------ part 1 ---
    def part_meter(self):
        head = label("How an orifice meter measures gas", size=TITLE, weight="SEMIBOLD").to_edge(UP)
        y0, r, hole = -0.2, 1.1, 0.42
        top = Line([-6, y0 + r, 0], [6, y0 + r, 0], color=RULE, stroke_width=4)
        bot = Line([-6, y0 - r, 0], [6, y0 - r, 0], color=RULE, stroke_width=4)
        plate_u = Line([0, y0 + r, 0], [0, y0 + hole, 0], color=INK, stroke_width=8)
        plate_d = Line([0, y0 - hole, 0], [0, y0 - r, 0], color=INK, stroke_width=8)
        self.play(FadeIn(head), Create(top), Create(bot), Create(plate_u), Create(plate_d), run_time=MOVE)

        # gas: dots that speed up and pinch through the hole
        def path_y(x, y):
            squeeze = math.exp(-(x / 1.2) ** 2)
            return y * (1 - squeeze * (1 - hole / r))
        dots = VGroup()
        anims = []
        for i, yy in enumerate((-0.75, -0.25, 0.25, 0.75)):
            for k in range(4):
                d = Dot(radius=0.06, color=ACC)
                x_start = -6 + k * 1.4
                pts = [[x, y0 + path_y(x, yy), 0] for x in [x_start + j * 0.1 for j in range(int((6 - x_start) / 0.1))]]
                d.move_to(pts[0])
                dots.add(d)
                path = VMobject().set_points_as_corners(pts)
                anims.append(MoveAlongPath(d, path, rate_func=linear))
        self.add(dots)
        self.play(*anims, run_time=3.0)
        self.remove(dots)

        # pressure, upstream and downstream
        g1 = Rectangle(width=0.35, height=1.6, color=MOSS, fill_color=MOSS, fill_opacity=0.8).move_to([-2.5, y0 + r + 0.9, 0])
        g2 = Rectangle(width=0.35, height=0.9, color=MOSS, fill_color=MOSS, fill_opacity=0.8)
        g2.move_to([2.5, y0 + r + 0.1, 0]).align_to(g1, DOWN)
        p1 = number("pressure before", size=SMALL, color=DIM).next_to(g1, LEFT, buff=0.2)
        p2 = number("after", size=SMALL, color=DIM).next_to(g2, RIGHT, buff=0.2)
        self.play(FadeIn(g1), FadeIn(g2), FadeIn(p1), FadeIn(p2), run_time=MOVE)
        self.wait(8.5 - (2 * MOVE + 3.0))
        eq = equation(r"\text{flow} = C \times \sqrt{\text{pressure drop}} \times \cdots", size=LABEL).move_to([0, y0 - r - 0.75, 0])
        note = label("C comes from an equation fitted to laboratory data", size=SMALL, color=DIM).next_to(eq, DOWN, buff=0.2)
        self.play(FadeIn(eq), run_time=MOVE)
        self.play(FadeIn(note), run_time=MOVE)
        self.wait(12.0 - 8.5 - 2 * MOVE - 0.4)
        self.play(*[FadeOut(m) for m in (head, top, bot, plate_u, plate_d, g1, g2, p1, p2, eq, note)], run_time=0.4)

    # ------------------------------------------------------------ part 2 ---
    def part_average(self):
        head = label("Many meters, two kinds of error", size=TITLE, weight="SEMIBOLD").to_edge(UP)
        n = ValueTracker(1)
        W0 = 6.0                         # bar length for a 1% error
        own_lab = label("each meter's own error", size=SMALL, color=DIM).move_to([-1.2, 1.3, 0]).align_to([-5.5, 0, 0], LEFT)
        sh_lab = label("an error every meter shares", size=SMALL, color=DIM).move_to([-1.2, -0.5, 0]).align_to([-5.5, 0, 0], LEFT)
        own = always_redraw(lambda: Rectangle(width=max(W0 / math.sqrt(n.get_value()), 0.02), height=0.5,
                                              color=ACC, fill_color=ACC, fill_opacity=0.85, stroke_width=0)
                            .move_to([-5.5, 0.7, 0], aligned_edge=LEFT))
        sh = always_redraw(lambda: Rectangle(width=W0 * 0.5, height=0.5, color=MOSS, fill_color=MOSS,
                                             fill_opacity=0.85, stroke_width=0).move_to([-5.5, -1.1, 0], aligned_edge=LEFT))
        cnt = always_redraw(lambda: number("%s meters" % format(int(round(n.get_value())), ","), size=LABEL)
                            .move_to([3.6, 2.2, 0]))
        self.play(FadeIn(head), FadeIn(own_lab), FadeIn(sh_lab), FadeIn(own), FadeIn(sh), FadeIn(cnt), run_time=MOVE)
        self.wait(16.5 - 12.0 - MOVE - 3.0)
        self.play(n.animate.set_value(10000), run_time=3.0, rate_func=lambda t: smooth(t) ** 3)
        self.wait(21.0 - 16.5 - 0.4)
        self.play(*[FadeOut(m) for m in (head, own_lab, sh_lab, own, sh, cnt)], run_time=0.4)

    # ------------------------------------------------------------ part 3 ---
    def part_books(self):
        head = label("Where a shared error lands", size=TITLE, weight="SEMIBOLD").to_edge(UP)
        cold = label("gas at %d °F, billed as if at 60 °F" % round(T_GAS), size=SMALL, color=DIM).next_to(head, DOWN, buff=0.3)
        W = 9.0
        x0 = -4.5
        inb = Rectangle(width=W, height=0.6, color=INK, fill_color=INK, fill_opacity=0.25, stroke_width=0).move_to([x0, 0.6, 0], aligned_edge=LEFT)
        inl = label("gas in, city gate", size=SMALL).next_to(inb, UP, buff=0.12).align_to(inb, LEFT)
        frac = 1 - SHARED / 100 * 12        # the gap is drawn 12x so it can be seen; the label says the true size
        outb = Rectangle(width=W * frac, height=0.6, color=MOSS, fill_color=MOSS, fill_opacity=0.85, stroke_width=0).move_to([x0, -0.6, 0], aligned_edge=LEFT)
        outl = label("gas billed, customer meters", size=SMALL).next_to(outb, DOWN, buff=0.12).align_to(outb, LEFT)
        self.play(FadeIn(head), FadeIn(cold), FadeIn(inb), FadeIn(inl), run_time=MOVE)
        self.play(FadeIn(outb), FadeIn(outl), run_time=MOVE)
        self.wait(26.0 - 21.0 - 2 * MOVE)
        gap = Rectangle(width=W * (1 - frac), height=0.6, color=ACC, fill_color=ACC, fill_opacity=0.9, stroke_width=0)
        gap.move_to([x0 + W * frac, -0.6, 0], aligned_edge=LEFT)
        gl = number("%.1f%% reported as unaccounted for" % SHARED, size=LABEL, color=ACC).next_to(gap, DOWN, buff=0.55).align_to(gap, RIGHT)
        sc = label("gap drawn 12 times its size", size=SMALL, color=DIM).next_to(gl, DOWN, buff=0.12).align_to(gl, RIGHT)
        why = label("delivered, not billed by a meter: recovered through the gas charge", size=SMALL, color=INK)
        why.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(gap), FadeIn(gl), FadeIn(sc), FadeIn(why), run_time=MOVE)
        self.wait(31.5 - 26.0 - MOVE + 0.3)
