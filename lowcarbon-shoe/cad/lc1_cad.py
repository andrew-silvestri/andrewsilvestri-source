"""LC-1 parametric sole unit (CadQuery).

Builds, for a men's US size (default 9), the parts of the LC-1 sole unit:
  outsole skin   solid TPU, with transverse flex grooves
  midsole        expanded-TPU (eTPU) bead foam, heel-to-toe drop, toe spring
  rim            solid TPU band on the midsole's top edge; the upper is stitched
                 through it (stitchdown) - no adhesive anywhere
  sockliner      removable eTPU sheet
and exports STEP and STL for each, a combined STEP, and volumes.json, which the
mass test and the LCA read. The same envelope is the home-print midsole: the
slicer fills it with gyroid infill (BUILD.md).

Geometry is a starting design, not a last-fitted pattern. Sizing: Brannock-type
rule, foot length (in) = (US men's size + 22) / 3; sole length = foot + 20 mm.

Run:  python lc1_cad.py [--size 9] [--out out]
"""
import argparse
import json
import math
import os

import cadquery as cq

# Half-widths (mm) of the sole outline for a 285 mm sole, right foot.
# (x from heel, medial half-width, lateral half-width). Scaled to size.
STATIONS = [
    (0, 0, 0), (6, 26, 26), (20, 37, 36), (45, 40, 38), (75, 37, 38),
    (110, 31, 38), (145, 42, 42), (180, 54, 46), (205, 56, 45),
    (232, 52, 41), (255, 43, 33), (272, 30, 20), (282, 14, 6), (285, 0, 0),
]
REF_LEN = 285.0


def sole_length_mm(size):
    foot_in = (size + 22.0) / 3.0
    return foot_in * 25.4 + 20.0


def outline_pts(L, W_scale=1.0):
    s = L / REF_LEN
    med = [(x * s, m * s * W_scale) for x, m, _ in STATIONS[1:-1]]
    lat = [(x * s, -l * s * W_scale) for x, _, l in reversed(STATIONS[1:-1])]
    return [(STATIONS[0][0], 0.0)] + med + [(STATIONS[-1][0] * s, 0.0)] + lat


def outline_wp(L, z=0.0, W_scale=1.0, inset=0.0):
    pts = outline_pts(L, W_scale)
    w = cq.Workplane("XY", origin=(0, 0, z)).spline(pts, periodic=True, includeCurrent=False).close()
    if inset:
        w = w.offset2D(-inset)
    return w


def profile_solid(L, z0, heel_t, fore_t, toe_t, spring, width=200.0):
    """Side profile (XZ) extruded across Y: bottom with toe spring, top sloping."""
    s = L / REF_LEN
    xh, xf, xt = 70 * s, 190 * s, L
    bot = [(0, z0), (xf, z0), (xt + 2, z0 + spring)]
    top = [(xt + 2, z0 + spring + toe_t), (xf, z0 + fore_t), (xh, z0 + heel_t), (-2, z0 + heel_t)]
    pts = [(-2, z0)] + bot + top
    return (cq.Workplane("XZ", origin=(0, width / 2, 0)).polyline(pts).close().extrude(width))


def build(size=9.0, heel_mid=26.0, fore_mid=17.0, outsole_t=1.5, sock_t=4.0,
          rim_w=3.0, rim_h=8.0, groove_d=1.0):
    L = sole_length_mm(size)
    s = L / REF_LEN
    parts = {}
    # outsole skin, z 0..outsole_t, with toe spring applied by intersecting the profile
    out = outline_wp(L).extrude(outsole_t + 12)
    out = out.intersect(profile_solid(L, 0.0, outsole_t, outsole_t, outsole_t, 8.0))
    for gx in (150, 170, 190, 210, 230):  # transverse flex grooves in the forefoot
        g = (cq.Workplane("XY").box(3.0, 200, groove_d * 2).translate((gx * s, 0, 0)))
        out = out.cut(g)
    # arch window: no outsole under the midfoot (saves mass; the midfoot carries little load)
    win = cq.Workplane("XY").ellipse(32 * s, 20 * s).extrude(outsole_t + 14).translate((118 * s, 6 * s, -1))
    out = out.cut(win)
    parts["outsole"] = out
    # midsole envelope, z outsole_t .. outsole_t + thickness
    z0 = outsole_t
    mid_env = outline_wp(L, z=z0).extrude(heel_mid + 12)
    mid_env = mid_env.intersect(profile_solid(L, z0, heel_mid, fore_mid, 10.0, 8.0))
    # rim: perimeter band on the top rim_h of the sidewall (solid TPU)
    band = outline_wp(L, z=z0).extrude(heel_mid + 12).cut(outline_wp(L, z=z0, inset=rim_w).extrude(heel_mid + 12))
    top_strip = (profile_solid(L, z0, heel_mid, fore_mid, 10.0, 8.0)
                 .cut(profile_solid(L, z0 - rim_h, heel_mid, fore_mid, 10.0, 8.0)))
    rim = band.intersect(top_strip)
    parts["rim"] = rim
    parts["midsole"] = mid_env.cut(rim)
    # sockliner: inset outline, on top of the midsole at the heel; follows the slope
    sock = outline_wp(L, z=z0, inset=rim_w + 1.0).extrude(heel_mid + sock_t + 12)
    sock = sock.intersect(profile_solid(L, z0, heel_mid + sock_t, fore_mid + sock_t, 10.0 + sock_t, 8.0)
                          .cut(profile_solid(L, z0, heel_mid, fore_mid, 10.0, 8.0)))
    parts["sockliner"] = sock
    dims = dict(size_us_men=size, sole_length_mm=round(L, 1), heel_midsole_mm=heel_mid,
                forefoot_midsole_mm=fore_mid, outsole_mm=outsole_t, sockliner_mm=sock_t,
                rim_width_mm=rim_w, rim_height_mm=rim_h,
                heel_stack_mm=outsole_t + heel_mid + sock_t,
                forefoot_stack_mm=outsole_t + fore_mid + sock_t,
                ball_width_mm=round((56 + 45) * s, 1), heel_width_mm=round((40 + 38) * s, 1))
    return parts, dims


def volume_cm3(wp):
    return wp.val().Volume() / 1000.0 if hasattr(wp, "val") else wp.Volume() / 1000.0


def plantar_area_cm2(L):
    return outline_wp(L).extrude(1.0).val().Volume() / 100.0  # 1 mm thick -> mm3/100 = cm2... (mm2/100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=float, default=9.0)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    parts, dims = build(a.size)
    vols = {}
    asm = cq.Assembly()
    for name, wp in parts.items():
        vols[name] = round(volume_cm3(wp), 2)
        cq.exporters.export(wp, os.path.join(a.out, f"lc1_{name}.step"))
        cq.exporters.export(wp, os.path.join(a.out, f"lc1_{name}.stl"), tolerance=0.2, angularTolerance=0.2)
        asm.add(wp, name=name)
    asm.save(os.path.join(a.out, "lc1_sole_unit.step"))
    L = dims["sole_length_mm"]
    dims["plantar_area_cm2"] = round(outline_wp(L).extrude(1.0).val().Volume() / 100.0, 1)
    res = dict(dims=dims, volumes_cm3=vols,
               note="Volumes are of the CAD solids; masses = volume x density in tests/mass.py")
    with open(os.path.join(a.out, "volumes.json"), "w", newline="\n") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
