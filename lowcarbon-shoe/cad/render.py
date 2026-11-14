"""Render the LC-1 shoe, assembled and exploded (PNG), from the CAD parts.

The upper is a SCHEMATIC volume (a loft from the sole outline to a smaller
collar outline, with the collar and throat cut away) for the picture only; the
real upper is the flat pattern in out/lc1_upper_pattern.*.

python render.py  -> out/lc1_assembled.png, out/lc1_exploded.png
"""
import os

import cadquery as cq
import matplotlib
import numpy as np
import trimesh

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

import lc1_cad as C  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
COL = {"outsole": "#241E1A", "midsole": "#C9C2B8", "rim": "#733E24", "sockliner": "#9DB4BC", "upper": "#245F73"}


def upper_solid(L, z0):
    s = L / C.REF_LEN
    base = C.outline_wp(L, z=z0, inset=3.0)
    w1 = base.val()
    pts = C.outline_pts(L, 0.78)
    top = cq.Workplane("XY", origin=(14 * s, 0, z0 + 58 * s)).spline(pts, periodic=True, includeCurrent=False).close().val()
    shell = cq.Solid.makeLoft([w1, top], True)
    up = cq.Workplane("XY").add(shell)
    inner = cq.Workplane("XY").add(shell).translate((0, 0, 0)).val().scale(1.0)
    collar = (cq.Workplane("XZ", origin=(0, 100, 0))
              .polyline([(30 * s, z0 + 48 * s), (130 * s, z0 + 30 * s), (190 * s, z0 + 34 * s), (190 * s, z0 + 200), (30 * s, z0 + 200)])
              .close().extrude(200))
    up = up.cut(collar)
    return up


def mesh_of(wp):
    path = os.path.join(OUT, "_tmp.stl")
    cq.exporters.export(wp, path, tolerance=0.3, angularTolerance=0.3)
    m = trimesh.load(path)
    os.remove(path)
    return m


def draw(meshes, offsets, fname, elev=18, azim=-62):
    fig = plt.figure(figsize=(9, 6), dpi=130)
    ax = fig.add_subplot(111, projection="3d")
    light = np.array([0.3, -0.5, 0.8]) / np.linalg.norm([0.3, -0.5, 0.8])
    allv = []
    for name, m in meshes.items():
        v = m.vertices + [0, 0, offsets.get(name, 0)]
        tri = v[m.faces]
        n = m.face_normals
        shade = 0.55 + 0.45 * np.clip(n @ light, 0, 1)
        base = np.array(matplotlib.colors.to_rgb(COL[name]))
        fc = np.clip(base[None, :] * shade[:, None], 0, 1)
        pc = Poly3DCollection(tri, facecolors=fc, edgecolors="none", alpha=1.0 if name != "upper" else 0.85)
        ax.add_collection3d(pc)
        allv.append(v)
    allv = np.vstack(allv)
    mn, mx = allv.min(0), allv.max(0)
    c = (mn + mx) / 2
    r = (mx - mn).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r * 0.6, c[2] + r * 0.6)
    ax.set_box_aspect((1, 1, 0.6))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.patch.set_facecolor("#F2F0EF")
    fig.savefig(os.path.join(OUT, fname), bbox_inches="tight", facecolor="#F2F0EF")
    plt.close(fig)


def main():
    parts, dims = C.build(9.0)
    L = dims["sole_length_mm"]
    meshes = {k: mesh_of(v) for k, v in parts.items()}
    z_top = dims["outsole_mm"] + dims["heel_midsole_mm"] - 8
    try:
        meshes["upper"] = mesh_of(upper_solid(L, z_top))
    except Exception as e:  # the picture still works without the schematic upper
        print("upper loft failed:", e)
    draw(meshes, {}, "lc1_assembled.png")
    draw(meshes, {"outsole": -30, "midsole": 0, "rim": 25, "sockliner": 55, "upper": 95}, "lc1_exploded.png", elev=14)
    print("rendered", list(meshes))


if __name__ == "__main__":
    main()
