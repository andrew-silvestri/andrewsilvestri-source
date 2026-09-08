"""The favicon and the touch icon: an African penguin, in the site's palette.

WHY A PENGUIN, because without the reason this is decoration. Spheniscus
demersus is a row in this site's own data. `longevity-quotient/data/animals.csv`
records it at 3,100 g, 27 years in the wild and 40 in captivity, and the model's
own output in `longevity-quotient/outputs/lq_table.csv` gives it
`lq_class_maximum` 1.3896 - it lives about 1.39x as long as a 3.1 kg bird is
predicted to, and 2.30x as long as a 3.1 kg animal of any class. It is a
measured outlier from a page on this site, not a mascot.

WHAT IT DRAWS, and the geometry is a DESCRIPTION rather than three drawings:
the constants below are read by both renderers, so the SVG and the two PNGs
cannot drift. That is the whole reason this file exists rather than three
committed assets. Change a number here and all three follow.

The bird is drawn in NEGATIVE SPACE. The accent ground is the dark plumage; the
paper marks are the facial horseshoe and the front, which is how an African
penguin is actually marked. Nothing is outlined, because an outline at 16px is
a smudge.

PALETTE ONLY, section 4: deep blue ground (--acc #245F73), paper front and face
(--bg #F2F0EF), moss bill (--moss #733E24). No orange exists in this palette and
none is invented; no gradients.

THE TEST IS 16px IN A TAB, NOT 180px IN A PREVIEW. A silhouette with one large
mass survives that; the five thin links this replaced did not - at 16px they
were under a pixel each and the icon read as a dot. Render and look at 16
first: `python3 build_favicon.py --preview` writes the three sizes side by side.

Writes site/favicon.svg, site/favicon.png (180) and site/apple-touch-icon.png
(180) from the one description below.

Run:  python3 build_favicon.py
"""
import os
import sys

from PIL import Image, ImageDraw

import sitefig

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")

GROUND, PAPER, BILL = sitefig.ACC, sitefig.BG, sitefig.MOSS

# ---- the description, on a 64-unit square -------------------------------
# Everything is an ellipse or a triangle so both renderers can draw it exactly.
# Order matters: each shape is painted over the last.
RADIUS = 12                      # the rounded square, as before

FACE_OUT = (32, 20, 11.5, 10.5)  # cx, cy, rx, ry - paper, the facial horseshoe
FACE_IN = (32, 18.5, 7.5, 8.5)   # ground again, carving the face back out
FRONT = (32, 42, 13.5, 17)       # paper, the front; drawn last so it joins the
#                                  horseshoe at the throat the way the bird does
BILL_TRI = [(28.4, 23.6), (35.6, 23.6), (32, 30.4)]   # moss


def _ell(c):
    """(cx, cy, rx, ry) -> the bounding box both renderers want."""
    cx, cy, rx, ry = c
    return cx - rx, cy - ry, cx + rx, cy + ry


def svg():
    def e(c, fill):
        cx, cy, rx, ry = c
        return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}"/>'
    tri = " ".join(f"{x},{y}" for x, y in BILL_TRI)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">\n'
            f'<rect width="64" height="64" rx="{RADIUS}" fill="{GROUND}"/>\n'
            f'{e(FACE_OUT, PAPER)}\n'
            f'{e(FACE_IN, GROUND)}\n'
            f'{e(FRONT, PAPER)}\n'
            f'<polygon points="{tri}" fill="{BILL}"/>\n'
            f'</svg>\n')


def png(size):
    S = 8                     # draw large, then shrink: PIL has no antialiasing
    im = Image.new("RGBA", (64 * S, 64 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 64 * S - 1, 64 * S - 1), radius=RADIUS * S, fill=GROUND)
    for shape, fill in ((FACE_OUT, PAPER), (FACE_IN, GROUND), (FRONT, PAPER)):
        x0, y0, x1, y1 = _ell(shape)
        d.ellipse((x0 * S, y0 * S, x1 * S, y1 * S), fill=fill)
    d.polygon([(x * S, y * S) for x, y in BILL_TRI], fill=BILL)
    return im.resize((size, size), Image.LANCZOS)


def preview(path):
    """The three sizes side by side on paper, 16 first, because 16 is the one
    that decides whether this works."""
    sizes = [16, 32, 180]
    pad = 16
    w = sum(sizes) + pad * (len(sizes) + 1)
    h = max(sizes) + pad * 2
    sheet = Image.new("RGB", (w, h), sitefig.BG)
    x = pad
    for s in sizes:
        sheet.paste(png(s), (x, pad + (max(sizes) - s) // 2), png(s))
        x += s + pad
    sheet.save(path)
    print(f"  wrote {path}  ({', '.join(str(s) for s in sizes)} px)")


def main():
    open(os.path.join(SITE, "favicon.svg"), "w", encoding="utf-8").write(svg())
    png(180).save(os.path.join(SITE, "favicon.png"), optimize=True)
    png(180).save(os.path.join(SITE, "apple-touch-icon.png"), optimize=True)
    print("  wrote favicon.svg, favicon.png, apple-touch-icon.png")
    if "--preview" in sys.argv:
        preview(os.path.join(HERE, "favicon_preview.png"))


if __name__ == "__main__":
    main()
