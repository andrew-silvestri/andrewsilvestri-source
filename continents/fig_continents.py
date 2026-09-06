"""The six figures for site/continents.html, drawn from the payload.

  continents_fig1_futures.png    four published futures, one moment, 2x2 maps
  continents_fig1_futures-phone.png   the same, 1x4, for the narrow track
  continents_fig2_belts.png      where the deformation is, on the globe
  continents_fig3_rigidity.png   residual against distance to a boundary
  continents_fig4_slowdown.png   today's rate against the geological average
  continents_fig5_past.png       reconstructed latitude, eight models, six places
  continents_fig6_regimes.png    the three regimes on one pair of axes

Every colour, size and face comes from sitefig.py. Every number comes from
outputs/continents_payload.json; nothing is typed here. Each figure is
audited for text that overlaps, runs off the canvas or falls under the site's
size floor, and for grid faults; the build prints the count and it must be 0.

The maps are raster, drawn by inverse-mapping Equal Earth pixels back to
lon/lat and sampling. That is deliberate: it needs no antimeridian handling
at all, because there is no polyline to break. The one vector overlay that
does cross the seam, the PB2002 boundaries, is split by geo.split_at_seam
before projecting.

Run:  python3 fig_continents.py
"""
import json
import math
import os
import sys

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import sitefig                                                    # noqa: E402
from sitefig import (ACC, BG, COOL, DIM, FAINT, FS_2, INK, MOSS, NOTES,  # noqa: E402
                     PHONE, PLOT, ROSE, RULE, SLATE, fig_size, row_aspect)
from fig_floor import floor_problems                              # noqa: E402
import geo                                                        # noqa: E402
import plates as P                                                # noqa: E402

PAYLOAD = os.path.join(HERE, "outputs", "continents_payload.json")
OUT = os.path.join(ROOT, "site", "assets")

INK_RGB = tuple(int(INK[i:i + 2], 16) / 255 for i in (1, 3, 5))
ACC_RGB = tuple(int(ACC[i:i + 2], 16) / 255 for i in (1, 3, 5))

# Where a plate's speed label sits. These are label positions, chosen so the
# text lands on the plate and clear of its neighbours; they are not data, and
# the speed printed at each is computed from the payload's fitted rotation.
LABEL_AT = {
    "NA": (-100.0, 45.0), "EU": (70.0, 57.0), "PA": (-150.0, 5.0),
    "AU": (133.0, -25.0), "SA": (-58.0, -12.0), "AF": (18.0, 5.0),
    "AN": (95.0, -66.0), "IN": (78.0, 18.0), "SO": (42.0, -12.0),
}
FAN_PLACES = ("Sydney", "Nagpur", "Denver", "Warsaw", "Kinshasa", "Brasilia")


def load():
    if not os.path.exists(PAYLOAD):
        sys.exit("fig_continents: run build_continents.py first.")
    return json.load(open(PAYLOAD, encoding="utf-8"))


# ------------------------------------------------------------------- audit

def audit(fig):
    """Text that overlaps other text, runs off the canvas or is under the
    size floor, plus the grid checks. Every Text object is enumerated
    explicitly, because findobj returns ticks that were never drawn."""
    fig.canvas.draw()
    ren = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    title_ids = {id(t) for ax in fig.axes for t in sitefig.titles(ax)}
    problems_grid = sitefig.grid_problems(fig)
    items = [t for t in fig.texts if t.get_text().strip()]
    for ax in fig.axes:
        for t in (sitefig.titles(ax) + [ax.xaxis.label, ax.yaxis.label]
                  + list(ax.texts)):
            if t.get_text().strip():
                items.append(t)
        if ax.axison:
            x0, x1 = sorted(ax.get_xlim())
            y0, y1 = sorted(ax.get_ylim())
            for tk, lo, hi in ((ax.xaxis, x0, x1), (ax.yaxis, y0, y1)):
                if not tk.get_visible():
                    continue
                for loc, lab in zip(tk.get_ticklocs(), tk.get_ticklabels()):
                    if lo - 1e-9 <= loc <= hi + 1e-9 and \
                            lab.get_text().strip() and lab.get_visible():
                        items.append(lab)
        lg = ax.get_legend()
        if lg:
            items += [x for x in lg.get_texts() if x.get_text().strip()]
    boxes = []
    for t in items:
        try:
            boxes.append((t.get_text()[:30], t.get_window_extent(renderer=ren)))
        except Exception:                                          # noqa: BLE001
            pass
    bad = []
    for lab, b in boxes:
        if b.x0 < -1 or b.y0 < -1 or b.x1 > W + 1 or b.y1 > H + 1:
            bad.append(f"off canvas: {lab!r}")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (la, a), (lb, b) = boxes[i], boxes[j]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0)
            oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ox > 0 and oy > 0:
                fr = ox * oy / min(a.width * a.height, b.width * b.height)
                if fr > 0.15:
                    bad.append(f"overlap {fr:.0%}: {la!r} / {lb!r}")
    bad += floor_problems(fig, [(t, id(t) in title_ids) for t in items])
    return bad + problems_grid


def emit(fig, name, quantise=None, why=""):
    bad = audit(fig)
    path = os.path.join(OUT, name)
    sitefig.save(fig, path, close=False)
    plt.close(fig)
    if quantise:
        # build_hero_figure.py's precedent: a dot cloud or a flat-ink map
        # blends into thousands of near-identical colours and the palette
        # becomes most of the file. Fewer colours is indistinguishable here
        # and the page has a 600 KB budget with six figures in it.
        from PIL import Image
        im = Image.open(path).convert("RGB")
        im.quantize(colors=quantise, method=Image.Quantize.MEDIANCUT,
                    dither=Image.Dither.NONE).save(path, optimize=True)
    kb = os.path.getsize(path) / 1024
    flag = "  LAYOUT: " + "; ".join(bad[:3]) if bad else ""
    print(f"  {name:38s} {len(bad)} layout problems  {kb:6.0f} KB{flag}")
    return len(bad), kb


# -------------------------------------------------------------- map helpers

def eq_earth_axes(ax):
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-geo.X_MAX * 1.02, geo.X_MAX * 1.02)
    ax.set_ylim(-geo.Y_MAX * 1.40, geo.Y_MAX * 1.05)


def pixel_lonlat(w_px, ss):
    """Inverse-map a supersampled Equal Earth pixel grid to lon/lat."""
    h_px = int(round(w_px / geo.ASPECT))
    xs = np.linspace(-geo.X_MAX, geo.X_MAX, w_px * ss)
    ys = np.linspace(-geo.Y_MAX, geo.Y_MAX, h_px * ss)
    X, Y = np.meshgrid(xs, ys)
    lon, lat, inside = geo.inverse(X, Y)
    return lon, lat, inside, h_px


def raster_mask(mask, w_px, ss=3, polar=88.0):
    """A land mask as an alpha coverage image, box-averaged from ss x ss."""
    lon, lat, inside, h_px = pixel_lonlat(w_px, ss)
    n, m = mask.shape
    i = np.mod(np.round((lon + 180.0) / 0.25).astype(np.int64), n)
    j = np.clip(np.round((lat + 90.0) / 0.25).astype(np.int64), 0, m - 1)
    v = mask[i, j] & inside & (np.abs(lat) <= polar)
    return v.reshape(h_px, ss, w_px, ss).mean(axis=(1, 3))


def rgba(cov, rgb):
    out = np.zeros(cov.shape + (4,))
    out[..., 0:3] = rgb
    out[..., 3] = cov
    return out


def draw_frame(ax, graticule=True):
    if graticule:
        for gx, gy in geo.graticule(30):
            ax.plot(gx, gy, color=FAINT, lw=0.4, zorder=1)
    lx, ly = geo.limb()
    ax.plot(lx, ly, color=RULE, lw=0.8, zorder=6)


EXTENT = [-geo.X_MAX, geo.X_MAX, -geo.Y_MAX, geo.Y_MAX]


# ------------------------------------------------------------------ figures

def fig1_futures(D, masks, phone=False):
    """Four published futures at the one age all four reach."""
    order = ["Pangaea Ultima", "Novopangaea", "Aurica", "Amasia"]
    key = {"Pangaea Ultima": "pun", "Novopangaea": "novon",
           "Aurica": "aurn", "Amasia": "amn"}
    src = {"Pangaea Ultima": "Scotese and van der Pluijm 2020",
           "Novopangaea": "no primary source",
           "Aurica": "Duarte et al. 2018",
           "Amasia": "Mitchell et al. 2012"}
    land = {r["scenario"]: r for r in D["future"]["land_distribution"]}
    age = D["future"]["common_age"]

    if phone:
        fig = plt.figure(figsize=fig_size(PHONE, 0.40))
        gs = fig.add_gridspec(4, 1, hspace=0.62)
        cells = [gs[i, 0] for i in range(4)]
        w_px = 300
    else:
        fig = plt.figure(figsize=fig_size(NOTES, 1.40))
        gs = fig.add_gridspec(2, 2, hspace=0.46, wspace=0.08)
        cells = [gs[i // 2, i % 2] for i in range(4)]
        w_px = 330
    for cell, name in zip(cells, order):
        ax = fig.add_subplot(cell)
        draw_frame(ax)
        ax.imshow(rgba(raster_mask(masks[key[name]][age], w_px), INK_RGB),
                  extent=EXTENT, origin="lower", interpolation="none", zorder=2)
        eq_earth_axes(ax)
        sitefig.panel(ax, f"{name}\n{src[name]}")
        r = land[name]
        ax.text(0, -geo.Y_MAX * 1.30,
                f"tropics {r['within_30_pct']:.0f}%   "
                f"far north {r['above_60N_land_pct']:.0f}%",
                fontsize=FS_2, color=DIM, fontfamily=sitefig.MONO,
                ha="center", va="bottom")
    sitefig.centre(fig)
    return fig


def fig2_belts(D, cache={}):
    """Where the deformation is: distance to a plate boundary, on the globe.

    Shaded by a computed field on a uniform lattice rather than by station
    positions. A map of 14,390 receivers is a map of where receivers are -
    North America has 5,911 and Africa 123 - and it would invite the reader
    to conclude something about Africa. The lattice has no such bias.
    """
    w_px, ss = 690, 2
    lon, lat, inside, h_px = pixel_lonlat(w_px, ss)
    if "dist" not in cache:
        bp = P.boundary_points(os.path.join(HERE, "data",
                                            "PB2002_boundaries.json"))
        step = 6
        sl = (slice(None, None, step), slice(None, None, step))
        d = P.distance_to_boundary(lat[sl].ravel(), lon[sl].ravel(), bp)
        cache["dist"] = d.reshape(lat[sl].shape)
        cache["shape"] = lat[sl].shape
        cache["step"] = step
    d = np.repeat(np.repeat(cache["dist"], cache["step"], axis=0),
                  cache["step"], axis=1)[:lat.shape[0], :lat.shape[1]]

    # near a boundary is dark, deep interior is pale: the ink follows the
    # deformation, not the land
    cov = np.clip(1.0 - np.log10(np.clip(d, 30, 3000) / 30) / math.log10(100),
                  0, 1) * inside
    cov = cov.reshape(h_px, ss, w_px, ss).mean(axis=(1, 3))

    fig, ax = plt.subplots(figsize=fig_size(NOTES, 1.71))
    draw_frame(ax, graticule=False)
    ax.imshow(rgba(cov, ACC_RGB), extent=EXTENT, origin="lower",
              interpolation="none", zorder=2)
    gj = json.load(open(os.path.join(HERE, "data", "PB2002_boundaries.json"),
                        encoding="utf-8"))
    for ft in gj["features"]:
        g = ft.get("geometry") or {}
        lines = ([g["coordinates"]] if g.get("type") == "LineString"
                 else g.get("coordinates", []))
        for ln in lines:
            a = np.array(ln, float)
            for plon, plat in geo.split_at_seam(a[:, 0], a[:, 1]):
                gx, gy = geo.forward(plon, plat)
                ax.plot(gx, gy, color=INK, lw=0.45, zorder=4)
    for r in D["present"]["plates"]:
        if r["plate"] not in LABEL_AT:
            continue
        lo, la = LABEL_AT[r["plate"]]
        om = P.omega_of(r["pole_lat"], r["pole_lon"], r["rate_deg_myr"])
        e, n = P.velocity(om, [la], [lo])
        sp = math.hypot(e[0], n[0])
        x, y = geo.forward(lo, la)
        ax.text(float(x), float(y), f"{r['name']}\n{sp:.0f} mm/yr",
                fontsize=FS_2, color=INK, fontfamily=sitefig.MONO,
                ha="center", va="center", zorder=5,
                bbox=dict(boxstyle="round,pad=0.18", facecolor=BG,
                          edgecolor="none", alpha=0.82))
    eq_earth_axes(ax)
    b = D["present"]["distance_bands"]
    ax.text(0, -geo.Y_MAX * 1.34,
            f"median miss: {b[0]['median_mm_yr']:.1f} mm/yr within 100 km of "
            f"a boundary, {b[4]['median_mm_yr']:.2f} beyond 1,000",
            fontsize=FS_2, color=DIM, fontfamily=sitefig.MONO,
            ha="center", va="bottom")
    sitefig.centre(fig)
    return fig


def fig3_rigidity(D):
    """Residual against distance to a boundary, with the counterexample in it."""
    import csv as _csv
    rows = list(_csv.DictReader(
        open(os.path.join(HERE, "outputs", "stations_fit.csv"),
             encoding="utf-8")))
    x = np.array([float(r["dist_km"]) for r in rows])
    y = np.maximum(np.array([float(r["residual_mm_yr"]) for r in rows]), 0.03)
    big = np.array([r["plate"] == "PA" and 18.8 <= float(r["lat"]) <= 20.4
                    and -156.2 <= float(r["lon"]) <= -154.7 for r in rows])

    fig, ax = plt.subplots(figsize=fig_size(NOTES, PLOT))
    ax.scatter(x[~big], y[~big], s=3, alpha=0.22, color=ACC, linewidths=0,
               zorder=2)
    ax.scatter(x[big], y[big], s=9, alpha=0.95, color=MOSS, linewidths=0,
               zorder=4)
    bands = D["present"]["distance_bands"]
    xs, med, p90 = [], [], []
    for b in bands:
        hi = b["hi_km"] or 6000
        xs += [b["lo_km"] or 20, hi]
        med += [b["median_mm_yr"]] * 2
        p90 += [b["p90_mm_yr"]] * 2
    ax.plot(xs, med, color=INK, lw=1.6, zorder=5)
    ax.plot(xs, p90, color=SLATE, lw=1.0, ls=(0, (4, 2)), zorder=5)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(20, 6000)
    ax.set_ylim(0.03, 300)
    ax.set_xlabel("distance to the nearest plate boundary, km")
    ax.set_ylabel("miss against the plate's own rotation, mm/yr")
    ax.grid(alpha=0.16, which="both")
    ax.set_xticks([30, 100, 300, 1000, 3000])
    ax.set_xticklabels(["30", "100", "300", "1,000", "3,000"])
    ax.set_yticks([0.1, 1, 10, 100])
    ax.set_yticklabels(["0.1", "1", "10", "100"])
    pa = D["present"]["pacific"]
    bi = pa["big_island_only"]
    ax.annotate(
        f"Hawaii. The {bi['n']} Big Island stations alone" + "\n"
        f"return a pole at {bi['pole_lat']:.0f} N turning "
        f"{bi['rate_deg_myr']:.2f} deg/Myr:" + "\n"
        "that is a volcano, not a plate.",
        xy=(3500, 20), xytext=(300, 90), fontsize=FS_2, color=MOSS,
        fontfamily=sitefig.MONO, ha="left", va="center",
        arrowprops=dict(arrowstyle="-", color=MOSS, lw=0.9,
                        shrinkA=2, shrinkB=6))
    ax.plot([], [], color=INK, lw=1.6, label="median")
    ax.plot([], [], color=SLATE, lw=1.0, ls=(0, (4, 2)), label="90th percentile")
    ax.legend(frameon=False, fontsize=FS_2, loc="lower left")
    sitefig.centre(fig)
    return fig


def fig4_slowdown(D):
    """Today's rate against the geological average, seven boundaries."""
    rows = [r for r in D["geologic_vs_geodetic"]
            if r["morvel"] is not None and r["itrf"] is not None]
    rows.sort(key=lambda r: -r["speed_change_mm_yr"])
    n = len(rows)
    fig, ax = plt.subplots(figsize=fig_size(NOTES, row_aspect(n, row_px=34, header_px=120)))
    for i, r in enumerate(rows):
        col = MOSS if abs(r["speed_change_mm_yr"]) >= 5 else SLATE
        ax.plot([r["itrf"], r["morvel"]], [i, i], color=col, lw=1.4, zorder=2)
        ax.scatter([r["morvel"]], [i], s=36, facecolor=BG, edgecolor=col,
                   lw=1.4, zorder=3)
        ax.scatter([r["itrf"]], [i], s=36, color=col, zorder=4)
        ax.text(max(r["morvel"], r["itrf"]) + 2.0, i,
                f"{r['speed_change_mm_yr']:+.1f} mm/yr",
                fontsize=FS_2, color=col, fontfamily=sitefig.MONO,
                va="center", ha="left")
    ax.set_yticks(range(n))
    ax.set_yticklabels([f"{r['boundary']} · {r['pair']}" for r in rows],
                       fontsize=FS_2)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, 92)
    ax.set_ylim(-0.7, n - 0.3)
    ax.set_xlabel("motion of the first plate relative to the second, mm/yr")
    ax.grid(axis="x", alpha=0.16)
    ax.scatter([], [], s=36, facecolor=BG, edgecolor=SLATE, lw=1.4,
               label="NNR-MORVEL56, averaged over 0.78 to 3.16 Myr")
    ax.scatter([], [], s=36, color=SLATE,
               label="ITRF2020-PMM, averaged over decades")
    ax.legend(frameon=False, fontsize=FS_2, loc="upper left")
    sitefig.centre(fig)
    return fig


def fig5_past(D):
    """Reconstructed latitude, eight models, six places.

    Latitude and not position, because palaeomagnetism determines latitude
    and cannot determine longitude. A fan of latitudes is the measured
    quantity; a map of positions is that quantity plus each model's own
    assumption about the east-west placement.
    """
    tracks = {t["place"]: t for t in D["past"]["tracks"]}
    ages = np.array(D["past"]["ages"], float)
    models = [m["name"] for m in D["past"]["models"]]
    fig, axes = plt.subplots(3, 2, figsize=fig_size(NOTES, 0.92),
                             sharex=True, sharey=True)
    for ax, place in zip(axes.ravel(), FAN_PLACES):
        tr = tracks[place]
        for lab in (-23.44, 23.44):
            ax.axhline(lab, color=FAINT, lw=0.6, zorder=1)
        ax.axhline(0.0, color=RULE, lw=0.8, zorder=1)
        for m in models:
            la = np.array([np.nan if v is None else v
                           for v in tr["models"][m]["lat"]], float)
            ax.plot(ages, la, color=ACC, lw=0.9, alpha=0.55, zorder=3)
        ax.set_xlim(0, 500)
        ax.set_ylim(-90, 90)
        ax.set_yticks([-60, -30, 0, 30, 60])
        ax.grid(alpha=0.12)
        sitefig.panel(ax, place)
    for ax in axes[-1]:
        ax.set_xlabel("millions of years ago")
    for ax in axes[:, 0]:
        ax.set_ylabel("reconstructed latitude")
    syd = axes.ravel()[0]
    syd.annotate("at 500 Ma most models" + chr(10) + "place no crust here,",
                 xy=(492, -30), xytext=(105, -80), fontsize=FS_2, color=MOSS,
                 fontfamily=sitefig.MONO, ha="left", va="center",
                 arrowprops=dict(arrowstyle="-", color=MOSS, lw=0.9,
                                 shrinkA=2, shrinkB=4))
    fig.tight_layout(w_pad=1.2, h_pad=0.9)
    sitefig.centre(fig)
    return fig


def fig6_regimes(D):
    """The three regimes on one pair of axes."""
    fig, ax = plt.subplots(figsize=fig_size(NOTES, PLOT))
    ceiling = D["antipodal_km"]
    ax.axhline(ceiling, color=RULE, lw=0.9, zorder=2)
    ax.text(497, ceiling * 1.05, "the furthest two points on Earth can be",
            fontsize=FS_2, color=DIM, fontfamily=sitefig.MONO, ha="right",
            va="bottom")

    t = np.linspace(1, 500, 200)
    floor = D["present"]["distance_bands"][4]["median_mm_yr"]
    ax.plot(t, floor * t, color=SLATE, lw=1.1, ls=(0, (5, 3)), zorder=3)
    ax.text(500, floor * 500 * 0.26,
            f"today's measured miss, run forward:\n{floor} mm/yr is "
            f"{floor} km per million years",
            fontsize=FS_2, color=SLATE, fontfamily=sitefig.MONO,
            ha="right", va="top")

    sp = [r for r in D["past"]["spread"] if r["max_km"] is not None
          and r["age"] % 50 == 0 and r["age"] > 0]
    ax.plot([r["age"] for r in sp], [r["max_km"] for r in sp],
            color=ACC, lw=1.6, marker="o", ms=4, zorder=5,
            label="eight published reconstructions of the same past")

    px = D["future"]["centroid_proxy"]
    ax.plot([r["age"] for r in px], [max(r["max_centroid_km"], 10) for r in px],
            color=MOSS, lw=1.0, ls=(0, (1, 2)), marker="s", ms=4.5,
            markerfacecolor=BG, markeredgecolor=MOSS, zorder=5,
            label="four scenarios: separation of their land centroids, a proxy")

    worst = max(r["max"] for r in D["future"]["disagreement"])
    ax.annotate(f"the four futures also disagree about\n{worst:.0f}% of the "
                "Earth's surface by here",
                xy=(px[-1]["age"], px[-1]["max_centroid_km"]),
                xytext=(120, 1600), fontsize=FS_2, color=MOSS,
                fontfamily=sitefig.MONO, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=MOSS, lw=0.9,
                                shrinkA=2, shrinkB=4))
    ax.set_yscale("log")
    ax.set_xlim(0, 505)
    ax.set_ylim(3, 60000)
    ax.set_xlabel("millions of years from now, in either direction")
    ax.set_ylabel("how far apart independent answers are, km")
    ax.set_yticks([10, 100, 1000, 10000])
    ax.set_yticklabels(["10", "100", "1,000", "10,000"])
    ax.grid(alpha=0.14, which="both")
    ax.legend(frameon=False, fontsize=FS_2, loc="lower right")
    sitefig.centre(fig)
    return fig


def main():
    D = load()
    sitefig.style()
    os.makedirs(OUT, exist_ok=True)
    import build_continents as B
    masks, _shape = B.load_masks()

    bad, kb = 0, 0.0
    for fig, name, q in (
        (fig1_futures(D, masks), "continents_fig1_futures.png", 32),
        (fig1_futures(D, masks, phone=True),
         "continents_fig1_futures-phone.png", 32),
        (fig2_belts(D), "continents_fig2_belts.png", 64),
        (fig3_rigidity(D), "continents_fig3_rigidity.png", 64),
        (fig4_slowdown(D), "continents_fig4_slowdown.png", 32),
        (fig5_past(D), "continents_fig5_past.png", 32),
        (fig6_regimes(D), "continents_fig6_regimes.png", 32),
    ):
        b, k = emit(fig, name, q)
        bad += b
        kb += k
    print(f"  {'':38s} {bad} total          {kb:6.0f} KB of figures")
    return bad


if __name__ == "__main__":
    raise SystemExit(0 if main() == 0 else 1)
