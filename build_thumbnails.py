"""The twelve thumbnails: the home-page cards and the library mosaic.

Each is the whole figure, scaled to THUMB (542) CSS pixels wide at the
figure's own aspect - never a crop. The first thumbnails (Part 2 of the
deslop pass, 2026-09-04) were centre cover-crops to 3:2 through
sitefig.thumbnail(); the sources run from 1.6:1 to 2.1:1 and one is 0.88:1,
so the crop took up to 29 % off the sides (the skyline chart lost "played in
Bb", its last tower and its height; the tomato chain lost its gas figure and
half a box) or 41 % off the top and bottom (the ranking). Nobody could see it
in the CSS, because the crop was baked into the asset and the card's
object-fit: cover fitted a 3:2 image to a 3:2 box exactly. The rule is now
in one place, here and in sitefig.thumbnail(): a thumbnail shows the whole
figure, and the page (style.css, .cardgrid .card img and .mosaic) lets it
keep its shape.

Sources are the shipped figures in site/assets/, so the thumbnails cannot be
of a figure the site no longer shows. Run after re-rendering any of them:

    python3 build_thumbnails.py
"""
import os

import sitefig

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "site", "assets")

# shipped figure -> thumbnail, both in site/assets/
THUMBS = [
    # the library mosaic on index.html, six tiles
    "02_demand_distribution.png",
    "04_inertia_by_type.png",
    "05_link_structure.png",
    "06_scenario_reach.png",
    "07_arrival_order.png",
    "09_size_vs_lowcarbon.png",
    # the six project cards on index.html
    "heat_fig1_breakeven_price.png",
    "storage_fig3_duration_value.png",
    "climate_chain_tomato.png",
    "skyline_towers.png",
    "lq_ranked.png",
    "bookshelf-demo-shelf.webp",
]


def thumb_name(src):
    return os.path.splitext(src)[0] + "-thumb.png"


def main():
    from PIL import Image
    for src in THUMBS:
        sp = os.path.join(ASSETS, src)
        if not os.path.exists(sp):
            raise SystemExit(f"{src} is not in site/assets/; the thumbnail would be of nothing")
        dp = os.path.join(ASSETS, thumb_name(src))
        size = sitefig.thumbnail(sp, dp)
        w, h = Image.open(dp).size
        print(f"  {thumb_name(src):40s} {w}x{h}  {w / h:.2f}  {size // 1024} KB")


if __name__ == "__main__":
    main()
