"""The favicon and the touch icon, in the site's palette.

The old ones were a near-black rounded square with gold nodes (#141310,
#d9a441): the ground and accent of a palette the site left on 2026-09-04.
This draws the same glyph - one node with five links - as paper strokes on
the accent, so it reads in a light tab bar and a dark one alike. Writes
site/favicon.svg, site/favicon.png (180) and site/apple-touch-icon.png (180)
from the one description below.

Run:  python3 build_favicon.py
"""
import os

from PIL import Image, ImageDraw

import sitefig

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
GROUND, STROKE = sitefig.ACC, sitefig.BG
# the glyph on a 64-unit square: centre, five satellites, links
CENTRE = (32, 32)
SATS = [(32, 12), (14, 44), (50, 44), (12, 26), (52, 26)]
R_C, R_S, LW = 6, 3.4, 2.6


def svg():
    links = " ".join(f"M{CENTRE[0]} {CENTRE[1]} L{x} {y}" for x, y in SATS)
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="{R_S}"/>' for x, y in SATS)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">\n'
            f'<rect width="64" height="64" rx="12" fill="{GROUND}"/>\n'
            f'<g stroke="{STROKE}" stroke-width="{LW}" fill="none" opacity=".9"><path d="{links}"/></g>\n'
            f'<g fill="{STROKE}"><circle cx="{CENTRE[0]}" cy="{CENTRE[1]}" r="{R_C}"/>{dots}</g>\n'
            f'</svg>\n')


def png(size):
    S = 8                                    # draw large, then shrink: PIL has no antialiasing
    im = Image.new("RGBA", (64 * S, 64 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 64 * S - 1, 64 * S - 1), radius=12 * S, fill=GROUND)
    for x, y in SATS:
        d.line((CENTRE[0] * S, CENTRE[1] * S, x * S, y * S), fill=STROKE, width=int(LW * S))
    for (x, y), r in [(CENTRE, R_C)] + [(p, R_S) for p in SATS]:
        d.ellipse((x * S - r * S, y * S - r * S, x * S + r * S, y * S + r * S), fill=STROKE)
    return im.resize((size, size), Image.LANCZOS)


def main():
    open(os.path.join(SITE, "favicon.svg"), "w", encoding="utf-8").write(svg())
    png(180).save(os.path.join(SITE, "favicon.png"), optimize=True)
    png(180).save(os.path.join(SITE, "apple-touch-icon.png"), optimize=True)
    print("  wrote favicon.svg, favicon.png, apple-touch-icon.png")


if __name__ == "__main__":
    main()
