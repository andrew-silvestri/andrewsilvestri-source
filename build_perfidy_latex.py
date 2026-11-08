"""
Draw the Perfidy page's LaTeX figure, site/assets/perfidy_latex.png and its
phone render perfidy_latex-phone.png, from the example PDF in the Perfidy
repository at the commit rezip_downloads.py pins (D-63, 2026-11-07).

Both are crops of the PDF's "Mass and energy balances" section, rendered at
one scale and tinted from black-on-white to the site's --ink on --bg. Nothing
is retypeset: the caption says the figure is from the example document, so it
is that document's pixels.

  wide   the whole section: heading, three sentences, equations (1)-(3), the
         line of inline math under them. Served at 714 CSS px.
  phone  the equations alone, stacked, without their numbers or the sentences
         between them, so the crop is about half as wide and the text about
         twice the size where the page serves it at 350 (under 760px). The
         first version cropped the full text width and set body text at about
         8px there; tests/test_fig_floor.py caught it.

The crops are found from the PDF's own text (anchor strings below), not from
pixel coordinates, so they follow the document if it moves. CROPS() returns
them in PDF points, and tests/test_fig_floor.py reads them to find which of
the PDF's text spans each PNG shows; it does not read a size from here.

    python build_perfidy_latex.py
"""
import os
import sys

import numpy as np
import pymupdf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rezip_downloads import PERFIDY_COMMIT, PERFIDY_PUBLIC, _git  # one pin for the zip and the figure

PDF_PATH = "latex/perfidy-example.pdf"
ASSETS = os.path.join(HERE, "site", "assets")
OUT = os.path.join(ASSETS, "perfidy_latex.png")
OUT_PHONE = os.path.join(ASSETS, "perfidy_latex-phone.png")

ZOOM = 3.125            # px per PDF point (225 dpi): the first version's scale, 1533 px over the text width
PAD = 6.0               # pt around a crop, for glyphs that overhang their span boxes (the integral, limits)
GAP = 2.0               # pt between the phone render's two stacked equation blocks (plus PAD on each)
BG = (0xF2, 0xF0, 0xEF)  # style.css --bg
INK = (0x24, 0x1E, 0x1A)  # style.css --ink

# Anchors: the section heading, the three sentences, and the next heading.
HEAD, S1, S2, S3, NEXT = ("Mass and energy balances", "For a steady-state reactor",
                          "The Gibbs energy of mixing", "Matrices and vectors", "Numbers")


def pdf():
    return pymupdf.open(stream=_git(PERFIDY_PUBLIC, "show", f"{PERFIDY_COMMIT}:{PDF_PATH}"),
                        filetype="pdf")


def spans(page):
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            for s in ln["spans"]:
                if s["text"].strip():
                    yield s


def _find(page, text):
    # Spaces are compared out: the bold headings' word spaces are not in the
    # PDF's text layer, so "Mass and energy balances" extracts as one word.
    key = text.replace(" ", "")
    hits = [pymupdf.Rect(s["bbox"]) for s in spans(page)
            if s["text"].replace(" ", "").startswith(key)]
    if len(hits) != 1:
        raise SystemExit(f"anchor {text!r}: {len(hits)} matches in {PDF_PATH}, want 1")
    return hits[0]


def _union(boxes):
    r = pymupdf.Rect(boxes[0])
    for b in boxes[1:]:
        r |= b
    return r


def CROPS(page):
    """{output file name: [rects in PDF points]}. A phone crop is several
    rects of one width, stacked top to bottom with GAP between them."""
    head, s1, s2, s3, nxt = (_find(page, t) for t in (HEAD, S1, S2, S3, NEXT))
    sp = [(pymupdf.Rect(s["bbox"]), s["text"].strip()) for s in spans(page)]
    section = [r for r, _ in sp if r.y0 >= head.y0 - 1 and r.y1 <= nxt.y0]
    wide = _union(section)
    wide = pymupdf.Rect(wide.x0 - PAD, wide.y0 - PAD, wide.x1 + PAD, wide.y1 + PAD)

    number = lambda t: t in ("(1)", "(2)", "(3)") or t in ("(", ")", "1", "2", "3")

    def block(top, bottom):
        rs = [r for r, t in sp if r.y0 >= top.y1 and r.y1 <= bottom.y0
              and not (number(t) and r.x0 > wide.x1 - 60)]       # the right-margin equation numbers
        if not rs:
            raise SystemExit(f"no equation between {top} and {bottom}")
        return _union(rs)

    eq1, eq23 = block(s1, s2), block(s2, s3)
    x0, x1 = min(eq1.x0, eq23.x0) - PAD, max(eq1.x1, eq23.x1) + PAD
    phone = [pymupdf.Rect(x0, b.y0 - PAD, x1, b.y1 + PAD) for b in (eq1, eq23)]
    return {os.path.basename(OUT): [wide], os.path.basename(OUT_PHONE): phone}


def render(page, rect):
    pm = page.get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM), clip=rect,
                         colorspace=pymupdf.csGRAY, alpha=False)
    g = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width).astype(np.float64)
    return g


def tint(g):
    k = 1.0 - g / 255.0                        # 0 on paper, 1 on full ink
    bg, ink = np.array(BG, float), np.array(INK, float)
    rgb = bg + (ink - bg) * k[..., None]
    return Image.fromarray(np.rint(rgb).astype(np.uint8), "RGB")


def stack(parts):
    gap = int(round(GAP * ZOOM))
    w = max(p.shape[1] for p in parts)
    h = sum(p.shape[0] for p in parts) + gap * (len(parts) - 1)
    out = np.full((h, w), 255.0)
    y = 0
    for p in parts:
        out[y:y + p.shape[0], :p.shape[1]] = p
        y += p.shape[0] + gap
    return out


def main():
    doc = pdf()
    page = doc[0]
    for name, rects in CROPS(page).items():
        img = tint(stack([render(page, r) for r in rects]))
        img.save(os.path.join(ASSETS, name), optimize=True)
        print(f"  wrote site/assets/{name}  {img.size[0]}x{img.size[1]}  ({len(rects)} crop(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
