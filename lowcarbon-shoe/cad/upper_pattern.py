"""LC-1 flat upper pattern (DXF + SVG), men's US size parameter.

Pieces, all in mm, one shoe (mirror for the left):
  1 strobel sock    the sole outline inset by the rim width, plus 5 mm seam allowance
  2 wrap upper      the side wall unrolled around the sole perimeter (a moccasin-wrap
                    approximation): bottom edge = perimeter length + 10 mm stitchdown
                    flange; height profile heel 62 mm, ankle dip 48 mm, throat; the
                    two ends meet at a centre-back heel seam
  3 tongue
  4 heel counter    recycled TPU sheet 1.0-1.5 mm, inside the heel
This is a STARTING pattern: an unrolled wall cannot follow the toe's double
curvature, so the toe needs darts or a stretch knit. Fit it on a last before
cutting good material (BUILD.md step 4).

python upper_pattern.py [--size 9]
"""
import argparse
import math
import os

import ezdxf
import numpy as np

import lc1_cad as C

HERE = os.path.dirname(os.path.abspath(__file__))


def perimeter_pts(L, n=400):
    import cadquery as cq
    w = C.outline_wp(L, inset=3.0).val()
    pts = [w.positionAt(t) for t in np.linspace(0, 1, n)]
    return np.array([[p.x, p.y] for p in pts])


def wrap_piece(L, flange=10.0):
    pts = perimeter_pts(L)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    P = s[-1]
    # start the unroll at the heel centre (min x)
    i0 = int(np.argmin(pts[:, 0]))
    s = (s - s[i0]) % P
    order = np.argsort(s)
    s, xs = s[order], pts[order, 0]
    # height as a function of position along the foot (x / L), heel -> toe
    def h(xn):
        return np.interp(xn, [0.0, 0.12, 0.30, 0.45, 0.60, 0.72, 0.85, 1.0],
                         [62, 58, 48, 50, 62, 70, 45, 30])
    top = np.column_stack([s, flange + h(xs / L)])
    bottom = [(P, 0.0), (0.0, 0.0)]
    return np.vstack([top, bottom]), P


def tongue(L):
    s = L / C.REF_LEN
    w, ln = 60 * s, 150 * s
    return [(0, 0), (w, 0), (w * 0.92, ln * 0.85), (w * 0.5, ln), (w * 0.08, ln * 0.85), (0, 0)]


def heel_counter(L):
    s = L / C.REF_LEN
    t = np.linspace(-1, 1, 41)
    span = 170 * s
    top = [(span / 2 * u + span / 2, 10 + 45 * s * math.cos(u * math.pi / 2) ** 0.5) for u in t]
    return [(0, 10)] + top + [(span, 10), (span, 0), (0, 0)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=float, default=9.0)
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    L = C.sole_length_mm(a.size)
    strobel = perimeter_pts(L)
    import cadquery as cq
    sw = C.outline_wp(L, inset=3.0 - 5.0).val()  # inset 3 (rim) less 5 mm seam allowance
    strobel_sa = np.array([[p.x, p.y] for p in (sw.positionAt(t) for t in np.linspace(0, 1, 300))])
    wrap, P = wrap_piece(L)
    pieces = {
        "1 strobel sock (seam line)": strobel,
        "1 strobel sock (cut line)": strobel_sa,
        "2 wrap upper (cut 1)": wrap + [0, 160],
        "3 tongue (cut 1)": np.array(tongue(L)) + [0, 260],
        "4 heel counter, rTPU sheet (cut 1)": np.array(heel_counter(L)) + [P + 30, 160],
    }
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    for name, pts in pieces.items():
        doc.layers.add(name.replace(",", ""))
        msp.add_lwpolyline([tuple(p) for p in pts], close=True, dxfattribs={"layer": name.replace(",", "")})
        c = pts.mean(axis=0)
        msp.add_text(name, dxfattribs={"height": 5, "layer": name.replace(",", "")}).set_placement(tuple(c))
    msp.add_text(f"LC-1 upper pattern, US men's {a.size:g}, mm. Starting pattern: fit on a last.",
                 dxfattribs={"height": 6}).set_placement((0, -60))
    dxf = os.path.join(a.out, "lc1_upper_pattern.dxf")
    doc.saveas(dxf)
    allp = np.vstack(list(pieces.values()))
    x0, y0 = allp.min(axis=0) - 20
    x1, y1 = allp.max(axis=0) + 20
    W, H = x1 - x0, y1 - y0 + 40
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}mm" height="{H:.0f}mm" viewBox="0 0 {W:.1f} {H:.1f}">',
           '<rect width="100%" height="100%" fill="#F2F0EF"/>']
    for name, pts in pieces.items():
        d = " ".join(f"{p[0]-x0:.1f},{y1-p[1]:.1f}" for p in pts)
        dash = ' stroke-dasharray="4 3"' if "seam line" in name else ""
        svg.append(f'<polygon points="{d}" fill="none" stroke="#241E1A" stroke-width="0.6"{dash}/>')
        c = pts.mean(axis=0)
        svg.append(f'<text x="{c[0]-x0:.1f}" y="{y1-c[1]:.1f}" font-size="6" font-family="sans-serif" fill="#245F73">{name}</text>')
    svg.append(f'<text x="5" y="{H-8:.1f}" font-size="7" font-family="sans-serif">LC-1 upper pattern, US men\'s {a.size:g}, 1:1 in mm. Starting pattern: fit on a last before cutting.</text>')
    svg.append("</svg>")
    with open(os.path.join(a.out, "lc1_upper_pattern.svg"), "w", newline="\n") as f:
        f.write("\n".join(svg))
    print(f"perimeter {P:.0f} mm; wrote {dxf} and .svg")


if __name__ == "__main__":
    main()
