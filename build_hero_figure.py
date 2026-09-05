"""A light-ground object for the home page: the model's power stations and
settlements on an orthographic globe, drawn on paper from the atlas payload.

Option (b) of the 2026-09-04 hero decision (DESLOP_3D): the WebGL globe is
a dark object drawn for a dark ground and stays in the atlas app, where it
has one; the home page gets a figure that belongs on the page - the same
34,936 stations at their recorded coordinates, the same coastlines, in the
palette, no lighting, no halo, no script. If (a) is chosen instead this
file is still the figure the mosaic and the atlas card can use.

Run:  python3 build_hero_figure.py
"""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import numpy as np                # noqa: E402

import sitefig                    # noqa: E402
from sitefig import ACC, COOL, DIM, FAINT, MOSS, RULE, BG, PROSE, SQUARE, fig_size  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "assets", "atlas-data.js")
OUT = os.path.join(HERE, "site", "assets", "hero_globe.png")
LON0, LAT0 = -20.0, 22.0      # the Atlantic view: Europe, Africa, the Americas
HERO_PX = 720                 # the CSS width the figure is displayed at


def load():
    raw = open(DATA, encoding="utf-8").read()
    return json.loads(raw[raw.index("=") + 1:raw.rindex(";")])


def ortho(lon, lat):
    """Orthographic projection about (LON0, LAT0); returns x, y, visible."""
    lo = np.radians(np.asarray(lon, float) - LON0)
    la = np.radians(np.asarray(lat, float))
    la0 = math.radians(LAT0)
    cosc = math.sin(la0) * np.sin(la) + math.cos(la0) * np.cos(la) * np.cos(lo)
    x = np.cos(la) * np.sin(lo)
    y = math.cos(la0) * np.sin(la) - math.sin(la0) * np.cos(la) * np.cos(lo)
    return x, y, cosc > 0


def main():
    sitefig.style()
    D = load()
    kind = [D["kinds"][k] for k in D["kind"]]
    lon, lat = np.array(D["lon"], float), np.array(D["lat"], float)
    # Drawn at the width it is shown at, 720 CSS px (style.css caps
    # img.fig.plain there), not the wide track: at PROSE the file was 338 KB
    # and the home page 751 KB; at 720 it is a third of that and the page
    # is under the 600 KB line. sitefig saves at two pixels per CSS pixel.
    fig, ax = plt.subplots(figsize=fig_size(HERO_PX, SQUARE * 1.15))
    ax.set_aspect("equal"); ax.axis("off")
    # the caption sits under the limb, so the frame is a little taller than
    # the sphere and the extra is at the bottom
    ax.set_xlim(-1.06, 1.06); ax.set_ylim(-1.06 - 0.18, 1.06)

    # the limb: one hairline, the only line that says "sphere"
    ax.add_patch(plt.Circle((0, 0), 1.0, facecolor="none", edgecolor=RULE, lw=0.9, zorder=1))
    # graticule, faint
    for lat_ in range(-60, 61, 30):
        ln = np.linspace(-180, 180, 361); x, y, v = ortho(ln, np.full(361, lat_))
        x, y = np.where(v, x, np.nan), np.where(v, y, np.nan)
        ax.plot(x, y, color=FAINT, lw=0.5, zorder=1)
    for lon_ in range(-180, 180, 30):
        lt = np.linspace(-90, 90, 181); x, y, v = ortho(np.full(181, lon_), lt)
        x, y = np.where(v, x, np.nan), np.where(v, y, np.nan)
        ax.plot(x, y, color=FAINT, lw=0.5, zorder=1)
    # coastlines
    for ring in D["coast"]:
        r = np.array(ring, float)
        x, y, v = ortho(r[:, 0], r[:, 1])
        x, y = np.where(v, x, np.nan), np.where(v, y, np.nan)
        ax.plot(x, y, color=DIM, lw=0.55, alpha=0.8, zorder=2)
    # settlements, then stations on top
    for want, col, size, alpha, z in (("consumer", MOSS, 1.2, 0.35, 3), ("station", ACC, 2.0, 0.55, 4)):
        idx = [i for i, k in enumerate(kind) if k == want]
        x, y, v = ortho(lon[idx], lat[idx])
        ax.scatter(x[v], y[v], s=size, c=col, alpha=alpha, linewidths=0, zorder=z)
    n_st = sum(1 for k in kind if k == "station"); n_co = sum(1 for k in kind if k == "consumer")
    ax.text(-1.04, -1.10, f"{n_st:,} power stations · {n_co:,} settlements · at their recorded coordinates",
            fontsize=sitefig.FS_2, color=DIM, fontfamily=sitefig.MONO, ha="left", va="top")
    fig.subplots_adjust(0, 0, 1, 1)
    size = sitefig.save(fig, OUT)
    # Seventy thousand translucent dots blend into thousands of near-
    # identical colours, and at 256 the palette is most of the file. Sixty-
    # four is indistinguishable on this figure (a scan by eye at 2x) and
    # keeps the home page under the 600 KB line; the general save() stays
    # at 256 because a chart's legend colours must not merge.
    from PIL import Image
    im = Image.open(OUT).convert("RGB")
    im.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(OUT, optimize=True)
    size = os.path.getsize(OUT)
    print(f"  wrote {os.path.basename(OUT)}  {size // 1024} KB")


if __name__ == "__main__":
    main()
