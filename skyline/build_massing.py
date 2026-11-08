"""
The shape of every tower on every wheel, as seen from the centre of its city.

Reads data/raw/massing_<date>.json.gz (fetch_massing.py), the towers on the
wheels (data/skylines.json, and build_skylines for each tower's coordinate
and confirming OSM object), data/raw/wdextra_<date>.json
(fetch_wikidata_extra.py) and data/authored.json (silhouettes written by
hand, each with its sources). Writes data/massing.json, which build_app.py
folds into the app.

WHAT IS MEASURED. Where OpenStreetMap models a tower in 3D (Simple 3D
Buildings: building:part ways and relations with height, min_height and
roof:*), every part is kept: its outline, bottom, top and roof. Where it maps
only the outline, the outline is extruded to the tower's height. Either way
the outline is real, so the width the tower presents to the centre of the
city, and how that width breaks into faces, is real.

WHAT IS FITTED. The height is Wikidata's, as everywhere on the wheel: the
massing is rescaled so its top meets it. Where OSM's massing stops more than
15% short of Wikidata's height, the gap is drawn as a needle (a spire or mast,
which is what such gaps almost always are) instead of stretching the whole
building, and the tower says so (needle: true).

WHAT IS INVENTED. Colour, windows, haze: the surface. The light is not
invented: each face carries the compass bearing its outward normal points
to, and the app lights it from the real sun (or moon) for the city's local
time, so the shading is the sundial it would be. Window rhythm comes
from the floor count (OSM building:levels, else Wikidata P1101, else height
over 3.6 m) and the facade type from the recorded style (Wikidata P149), else
the year built.

THE VIEW. Each tower is seen orthographically along the line from the city's
height-weighted centre to the tower: every edge of every part facing the
centre becomes a vertical face, at its projected position across the line of
sight (u, metres, + to the viewer's right), with the compass bearing of its
outward normal and its true length. Parts are listed far to near so drawing
them in order occludes correctly.

Run:  python build_massing.py
"""
import glob, gzip, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

M_LAT = 110540.0
M_LON = 111320.0
NEEDLE_GAP = 0.15     # OSM top more than this share short of Wikidata: needle;
                      # less than that, the massing is stretched to fit
FIT_BAD = 0.55        # OSM top below this share of Wikidata: parts are not it
STOREY = 3.6          # metres per floor where only a floor count is known
SIMPLIFY_M = 0.8      # Douglas-Peucker tolerance on outlines


def latest(pat):
    xs = sorted(glob.glob(os.path.join(HERE, "data", "raw", pat)))
    if not xs:
        raise SystemExit("missing " + pat)
    return xs[-1]


def num(s):
    if s is None:
        return None
    m = re.match(r"\s*(-?\d+(?:[.,]\d+)?)\s*(m|ft|')?", str(s))
    if not m:
        return None
    v = float(m.group(1).replace(",", "."))
    if m.group(2) in ("ft", "'"):
        v *= 0.3048
    return v


# ------------------------------------------------------------- geometry --
def ring_area(r):
    a = 0.0
    for i in range(len(r) - 1):
        a += r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1]
    return a / 2.0


def centroid(r):
    a = ring_area(r)
    if abs(a) < 1e-9:
        xs = [p[0] for p in r]; ys = [p[1] for p in r]
        return (sum(xs) / len(xs), sum(ys) / len(ys))
    cx = cy = 0.0
    for i in range(len(r) - 1):
        f = r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1]
        cx += (r[i][0] + r[i + 1][0]) * f
        cy += (r[i][1] + r[i + 1][1]) * f
    return (cx / (6 * a), cy / (6 * a))


def inside(p, r):
    x, y = p
    c = False
    for i in range(len(r) - 1):
        x1, y1 = r[i]; x2, y2 = r[i + 1]
        if (y1 > y) != (y2 > y):
            if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
    return c


def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def near_ring(p, r, tol):
    return inside(p, r) or any(seg_dist(p, r[i], r[i + 1]) <= tol
                               for i in range(len(r) - 1))


def simplify(pts, tol):
    if len(pts) < 4:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        best, k = 0, None
        for m in range(i + 1, j):
            d = seg_dist(pts[m], pts[i], pts[j])
            if d > best:
                best, k = d, m
        if k is not None and best > tol:
            keep[k] = True
            stack += [(i, k), (k, j)]
    return [p for p, f in zip(pts, keep) if f]


def assemble(segs):
    """Closed rings from multipolygon member ways that may be split."""
    segs = [list(s) for s in segs if len(s) >= 2]
    rings = []
    while segs:
        cur = segs.pop(0)
        changed = True
        while cur[0] != cur[-1] and changed:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == cur[-1]:
                    cur += s[1:]
                elif s[-1] == cur[-1]:
                    cur += s[::-1][1:]
                elif s[-1] == cur[0]:
                    cur = s[:-1] + cur
                elif s[0] == cur[0]:
                    cur = s[::-1][:-1] + cur
                else:
                    continue
                segs.pop(i)
                changed = True
                break
        if cur[0] != cur[-1]:
            cur.append(cur[0])
        if len(cur) >= 4:
            rings.append(cur)
    return rings


def outer_rings(el):
    """Lat/lon outer rings of a way or a multipolygon relation."""
    if el["type"] == "way":
        g = el.get("geometry") or []
        r = [(p["lat"], p["lon"]) for p in g if p]
        if len(r) >= 3 and r[0] != r[-1]:
            r.append(r[0])
        return [r] if len(r) >= 4 else []
    segs = []
    for m in el.get("members", []):
        if m.get("type") == "way" and m.get("role", "outer") in ("outer", ""):
            g = m.get("geometry") or []
            segs.append([(p["lat"], p["lon"]) for p in g if p])
    return assemble(segs)


def to_local(r, lat0, lon0):
    k = math.cos(math.radians(lat0))
    return [((lon - lon0) * M_LON * k, (lat - lat0) * M_LAT) for lat, lon in r]


# ------------------------------------------------------------- the parts --
ROOFS = {"flat": 0, "pyramidal": 1, "dome": 2, "gabled": 3, "hipped": 3,
         "skillion": 4, "onion": 5, "round": 2, "half-hipped": 3,
         "gambrel": 3, "mansard": 6, "cone": 1, "spire": 1}


CARD = {"N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5, "E": 90, "ESE": 112.5,
        "SE": 135, "SSE": 157.5, "S": 180, "SSW": 202.5, "SW": 225,
        "WSW": 247.5, "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5}


def roof_dir(t):
    """roof:direction (the way a sloped roof faces, downhill) in degrees."""
    d = (t.get("roof:direction") or "").strip().upper()
    if d in CARD:
        return CARD[d]
    return num(d)


def part_heights(t):
    """(bottom, top of walls, roof height, roof code) for one OSM element."""
    h = num(t.get("height"))
    lv = num(t.get("building:levels"))
    mh = num(t.get("min_height"))
    ml = num(t.get("building:min_level"))
    rh = num(t.get("roof:height"))
    rl = num(t.get("roof:levels"))
    shape = ROOFS.get((t.get("roof:shape") or "flat").lower(), 0)
    if h is None and lv is not None:
        h = lv * STOREY + (rh or (rl or 0) * STOREY if shape else 0)
    if h is None:
        return None
    bot = mh if mh is not None else (ml * STOREY if ml is not None else 0.0)
    if shape == 0:
        rh = 0.0
    elif rh is None:
        rh = (rl * STOREY) if rl else None
    if rh is None:            # a shaped roof with no height: a modest one
        rh = min(0.25 * (h - bot), 12.0) if shape != 1 else 0.3 * (h - bot)
    rh = max(0.0, min(rh, h - bot))
    return bot, h - rh, rh, shape


def faces_of(ring, uvec, vvec):
    """Visible faces of a prism with this footprint, seen along vvec.
    ring is local metres (x east, y north), closed. Returns
    [[u0, u1, normal bearing in degrees, true length]] and the footprint's
    (umin, umax) and the depth of its centroid."""
    r = ring[:]
    if ring_area(r) < 0:          # counter-clockwise, so normals point out
        r = r[::-1]
    out = []
    to_view = (-vvec[0], -vvec[1])
    for i in range(len(r) - 1):
        (x1, y1), (x2, y2) = r[i], r[i + 1]
        ex, ey = x2 - x1, y2 - y1
        L = math.hypot(ex, ey)
        if L < 0.05:
            continue
        nx, ny = ey / L, -ex / L          # outward for a CCW ring
        if nx * to_view[0] + ny * to_view[1] <= 1e-6:
            continue
        u1 = x1 * uvec[0] + y1 * uvec[1]
        u2 = x2 * uvec[0] + y2 * uvec[1]
        if abs(u2 - u1) < 0.05:
            continue
        nb = math.degrees(math.atan2(nx, ny)) % 360.0
        out.append([min(u1, u2), max(u1, u2), nb, L])
    us = [p[0] * uvec[0] + p[1] * uvec[1] for p in r]
    c = centroid(r)
    depth = c[0] * vvec[0] + c[1] * vvec[1]
    out.sort(key=lambda f: f[0])
    # merge neighbours facing almost the same way: a round tower stays round,
    # a rectangle stays two faces, and a mapped wall in ten pieces is one
    merged = []
    for f in out:
        if merged and abs(merged[-1][1] - f[0]) < 0.3 and \
                abs((merged[-1][2] - f[2] + 180) % 360 - 180) < 3.0:
            merged[-1][1] = f[1]
            merged[-1][3] += f[3]
        else:
            merged.append(f)
    return merged, (min(us), max(us)), depth


def roof_profile(ring, uvec, rdir, rh, shape):
    """The top edge of a sloped roof as seen along the line of sight:
    [[u, height above the walls], ...] left to right, and the roof plane's
    normal (bearing, tilt in degrees). A skillion rises linearly from its
    low edge (the side roof:direction points to) to its high edge, so over
    any vertical line of sight its highest point is where that line leaves
    the footprint; sampling the footprint's cross-sections gives the outline
    The Shard and One World Trade Center are mapped with. Pyramids peak over
    the footprint's centroid."""
    us = [p[0] * uvec[0] + p[1] * uvec[1] for p in ring]
    u0, u1 = min(us), max(us)
    if u1 - u0 < 0.5 or rh <= 0:
        return None, None
    if shape == 1:
        c = centroid(ring)
        uc = c[0] * uvec[0] + c[1] * uvec[1]
        return [[round(u0, 1), 0.0], [round(uc, 1), round(rh, 1)],
                [round(u1, 1), 0.0]], None
    if shape != 4 or rdir is None:
        return None, None
    a = math.radians(rdir)
    D = (math.sin(a), math.cos(a))            # downhill
    ss = [p[0] * D[0] + p[1] * D[1] for p in ring]
    smin, smax = min(ss), max(ss)
    if smax - smin < 0.5:
        return None, None

    def hgt(p):
        return rh * (smax - (p[0] * D[0] + p[1] * D[1])) / (smax - smin)
    samples = sorted(set([u0, u1] + us +
                         [u0 + (u1 - u0) * k / 24.0 for k in range(1, 24)]))
    prof = []
    for u in samples:
        best = None
        for i in range(len(ring) - 1):
            pa, pb = ring[i], ring[i + 1]
            ua = pa[0] * uvec[0] + pa[1] * uvec[1]
            ub = pb[0] * uvec[0] + pb[1] * uvec[1]
            if (ua - u) * (ub - u) > 0:
                continue
            t = 0.0 if abs(ub - ua) < 1e-9 else (u - ua) / (ub - ua)
            t = max(0.0, min(1.0, t))
            pt = (pa[0] + t * (pb[0] - pa[0]), pa[1] + t * (pb[1] - pa[1]))
            v = hgt(pt)
            best = v if best is None else max(best, v)
        if best is not None:
            prof.append([round(u, 1), round(best, 1)])
    # drop points a straight line through their neighbours already gives
    out = [prof[0]] if prof else []
    for k in range(1, len(prof) - 1):
        a_, b_, c_ = out[-1], prof[k], prof[k + 1]
        if c_[0] - a_[0] > 1e-6:
            lin = a_[1] + (c_[1] - a_[1]) * (b_[0] - a_[0]) / (c_[0] - a_[0])
            if abs(lin - b_[1]) < 0.6:
                continue
        out.append(b_)
    if len(prof) > 1:
        out.append(prof[-1])
    prof = out
    run = smax - smin
    tilt = math.degrees(math.atan2(run, rh))      # 0 vertical, 90 flat
    return prof, [round(rdir % 360), round(tilt)]


# ------------------------------------------------------------- the build --
def facade(style_labels, year):
    """masonry | ribbon | grid, from the recorded style, else the year."""
    s = " ".join(style_labels).lower()
    if re.search(r"gothic|deco|beaux|renaissance|romanesque|neoclassic|"
                 r"stalinist|byzantine|baroque|nouveau|eclectic|revival|"
                 r"historicism|chicago school", s):
        return "masonry"
    if re.search(r"international|brutalis|neues bauen|functionalis|"
                 r"socialist", s):
        return "ribbon"
    if re.search(r"high-tech|neo-futur|deconstruct|contemporary|neomodern|"
                 r"parametric|postmodern|modern", s):
        return "grid"
    if year and year < 1946:
        return "masonry"
    if year and year < 1976:
        return "ribbon"
    return "grid"


def project(mine, h, uvec, vvec, top, needle_at=None, free_top=False,
            gap=None):
    """Every part's visible faces, roof outline and normals across the line
    of sight. Heights are rescaled so the top meets Wikidata's h, except
    that an OSM top more than NEEDLE_GAP short leaves the gap to a needle.
    needle_at: an authored needle [z0, z1, u] in the drawing's own heights.
    Returns (parts, umin, umax, needle or None)."""
    scale, needle = 1.0, None
    if needle_at is not None:
        scale = h / max(top, 1e-6)
    elif top < (1 - (NEEDLE_GAP if gap is None else gap)) * h and not free_top:
        needle = top            # draw the gap as a needle
    elif top > 0:
        scale = h / top
    plist = []
    umin, umax = 1e9, -1e9
    for lr, (b0, wt, rh, shp, rdir) in mine:
        lr = simplify(lr, SIMPLIFY_M)
        if len(lr) < 4:
            continue
        faces, (u0, u1), depth = faces_of(lr, uvec, vvec)
        if not faces:
            continue
        umin, umax = min(umin, u0), max(umax, u1)
        # a sloped roof's fall across the line of sight: + falls to the
        # viewer's right, so its high edge is on the left
        rd = 0.0
        if rdir is not None:
            a = math.radians(rdir)
            rd = math.sin(a) * uvec[0] + math.cos(a) * uvec[1]
        prof, rn = roof_profile(lr, uvec, rdir, rh * scale, shp)
        plist.append({"z0": round(b0 * scale, 1),
                      "prof": prof, "rn": rn,
                      "z1": round(wt * scale, 1),
                      "rh": round(rh * scale, 1), "roof": shp,
                      "rd": round(rd, 2),
                      "u": [round(u0, 1), round(u1, 1)],
                      "d": round(depth, 1),
                      "f": [[round(f[0], 1), round(f[1], 1),
                             round(f[2]), round(f[3], 1)]
                            for f in faces]})
    # far parts first, so near ones cover them
    plist.sort(key=lambda p: -p["d"])
    nd = None
    if plist and needle:
        topp = max(plist, key=lambda p: p["z1"] + p["rh"])
        cu = (topp["u"][0] + topp["u"][1]) / 2
        nd = [round(cu, 1), round(needle, 1), round(h, 1)]
    if plist and needle_at is not None:
        nd = [round(needle_at[2], 1), round(needle_at[0] * scale, 1),
              round(needle_at[1] * scale, 1)]
    return plist, umin, umax, nd


# ---------------------------------------------------- authored drawings --
ROOF_OF = {"flat": 0, "pyramid": 1, "spire": 1, "dome": 2, "gable": 3,
           "hip": 3, "skillion": 4, "onion": 5, "mansard": 6}


def _bearing_axes(rot):
    r = math.radians(rot or 0.0)
    return (math.sin(r), math.cos(r)), (math.cos(r), -math.sin(r))


def _shape(t, outline):
    """A tier's plan as a closed ring in local metres (x east, y north),
    before its scale, twist and offset. None if it cannot be made."""
    p = (t.get("plan") or "outline").lower()
    w = float(t.get("w") or 0)
    d = float(t.get("d") or w or 0)
    a, b = _bearing_axes(t.get("rot"))

    def pt(s_, q_):          # s_ along the w side, q_ across it
        return (s_ * a[0] + q_ * b[0], s_ * a[1] + q_ * b[1])

    def ngon(n, rx, ry, phase=0.0):
        return [pt(rx * math.cos(phase + 2 * math.pi * k / n),
                   ry * math.sin(phase + 2 * math.pi * k / n))
                for k in range(n)]
    if p == "outline":
        if not outline:
            return None
        ring = max(outline, key=lambda r_: abs(ring_area(r_)))
        return [tuple(q) for q in ring[:-1]]
    if p in ("rect", "square"):
        if w <= 0:
            return None
        if p == "square":
            d = w
        return [pt(-w / 2, -d / 2), pt(w / 2, -d / 2), pt(w / 2, d / 2),
                pt(-w / 2, d / 2)]
    if p in ("circle", "ellipse"):
        return ngon(36, w / 2, (w if p == "circle" else d) / 2) if w > 0 else None
    if p == "octagon":
        R = (w / 2) / math.cos(math.pi / 8)
        return ngon(8, R, R, math.pi / 8) if w > 0 else None
    if p == "triangle":
        R = w / math.sqrt(3)
        # the first vertex points along rot
        return [pt(R * math.cos(2 * math.pi * k / 3), R * math.sin(2 * math.pi * k / 3))
                for k in range(3)] if w > 0 else None
    if p == "chamfered":
        c = min(float(t.get("c") or 0.15 * min(w, d)), 0.49 * min(w, d))
        return [pt(-w / 2 + c, -d / 2), pt(w / 2 - c, -d / 2), pt(w / 2, -d / 2 + c),
                pt(w / 2, d / 2 - c), pt(w / 2 - c, d / 2), pt(-w / 2 + c, d / 2),
                pt(-w / 2, d / 2 - c), pt(-w / 2, -d / 2 + c)] if w > 0 else None
    if p == "polygon":
        pts = [(float(x), float(y)) for x, y in (t.get("points") or [])]
        return pts if len(pts) >= 3 else None
    return None


def _place(shape, scale, twist_deg, offset):
    if not shape:
        return None
    ring = shape + [shape[0]]
    c = centroid(ring)
    th = math.radians(twist_deg or 0.0)
    ct, st = math.cos(th), math.sin(th)
    out = []
    for x, y in shape:
        dx, dy = (x - c[0]) * scale, (y - c[1]) * scale
        # twist is clockwise seen from above, like a compass bearing
        rx, ry = dx * ct + dy * st, -dx * st + dy * ct
        out.append((c[0] + rx + offset[0], c[1] + ry + offset[1]))
    out.append(out[0])
    return out


def authored_mine(spec, outline):
    """An agent's drawing (authoring/SPEC.md) as the same part list the OSM
    path makes: [(ring, (z0, wall top, roof height, roof code, roof dir))].
    Returns (parts, top, needle [z0, z1, u-less centre ring] or None)."""
    mine = []
    top_ring = None
    top_z = -1
    for t in spec.get("tiers") or []:
        try:
            z0, z1 = float(t["z0"]), float(t["z1"])
        except (KeyError, TypeError, ValueError):
            continue
        if z1 <= z0:
            continue
        shape = _shape(t, outline)
        if not shape:
            continue
        sc = t.get("scale", 1.0)
        tp = t.get("taper")
        if isinstance(sc, list) and len(sc) == 2:
            s0, s1 = float(sc[0]), float(sc[1])
        elif isinstance(tp, list) and len(tp) == 2:
            s0, s1 = float(tp[0]) * float(sc or 1), float(tp[1]) * float(sc or 1)
        else:
            s0 = s1 = float(sc or 1.0)
        tw = float(t.get("twist") or 0.0)
        off = t.get("offset") or [0, 0]
        off = (float(off[0]), float(off[1]))
        n = 1
        if abs(s1 - s0) > 0.02:
            n = 8
        if abs(tw) > 1:
            n = max(n, min(24, int(abs(tw) / 5) + 2))
        roof = t.get("roof") or {}
        rtype = (roof.get("type") or "flat").lower()
        rh = float(roof.get("h") or 0.0)
        last = None
        for i in range(n):
            a0 = z0 + (z1 - z0) * i / n
            a1 = z0 + (z1 - z0) * (i + 1) / n
            f = (i + 0.5) / n
            ring = _place(shape, s0 + (s1 - s0) * f, tw * f, off)
            if not ring or len(ring) < 4:
                continue
            last = (ring, a1, s1, tw)
            mine.append((ring, (a0, a1, 0.0, 0, None)))
        if not last:
            continue
        ring_top = _place(shape, s1, tw, off)
        if rh > 0 and rtype in ("stepped", "crown"):
            k = max(1, min(8, int(roof.get("steps") or 3)))
            for j in range(k):
                fr = 1.0 - 0.7 * (j + 1) / (k + 1)
                rg = _place(shape, s1 * fr, tw, off)
                b0 = z1 + rh * j / k
                b1 = z1 + rh * (j + 1) / k
                if rtype == "crown" and j == k - 1:
                    mine.append((rg, (b0, b0, b1 - b0, 1, None)))
                else:
                    mine.append((rg, (b0, b1, 0.0, 0, None)))
        elif rh > 0 and rtype in ROOF_OF and ROOF_OF[rtype]:
            code = ROOF_OF[rtype]
            rdir = roof.get("dir")
            rdir = float(rdir) if rdir is not None and code == 4 else None
            ring_roof = ring_top
            if rtype == "spire":   # a slender pyramid on part of the top
                ring_roof = _place(shape, s1 * 0.35, tw, off)
            # the last slice carries the roof
            rg, (a0, a1, _, _, _) = mine[-1]
            if rtype == "spire":
                mine.append((ring_roof, (z1, z1, rh, code, None)))
            else:
                mine[-1] = (rg, (a0, a1, rh, code, rdir))
        tz = z1 + (rh if rtype != "flat" else 0)
        if tz >= top_z:
            top_z, top_ring = tz, ring_top
    if not mine:
        return None, 0, None
    top = max(b[1] + b[2] for _, b in mine)
    nd = None
    ns = spec.get("needle")
    if isinstance(ns, dict):
        try:
            nz0, nz1 = float(ns["z0"]), float(ns["z1"])
            if nz1 > nz0:
                ring_n = top_ring
                if ns.get("offset"):
                    ox, oy = float(ns["offset"][0]), float(ns["offset"][1])
                    ring_n = [(ox - 1, oy - 1), (ox + 1, oy - 1), (ox + 1, oy + 1),
                              (ox - 1, oy + 1), (ox - 1, oy - 1)]
                nd = (nz0, nz1, ring_n)
                top = max(top, nz1)
        except (KeyError, TypeError, ValueError):
            pass
    return mine, top, nd


COLLECT = None     # make_packets.py sets this to see each tower's inputs


def main():
    import build_skylines as B
    pay = json.load(open(os.path.join(HERE, "data", "skylines.json"),
                         encoding="utf-8"))
    mpath = latest("massing_*.json.gz")
    with gzip.open(mpath, "rt", encoding="utf-8") as f:
        mass = json.load(f)
    xpath = latest("wdextra_*.json")
    extra = json.load(open(xpath, encoding="utf-8"))["answers"]
    apath = os.path.join(HERE, "data", "authored.json")
    authored = json.load(open(apath, encoding="utf-8")) if \
        os.path.exists(apath) else {}

    def q(b):
        return b["b"]["value"].rsplit("/", 1)[1]
    styles, floors = {}, {}
    for b in extra["style"]:
        styles.setdefault(q(b), set()).add(b["sLabel"]["value"])
    for b in extra["floors"]:
        v = num(b["f"]["value"])
        if v:
            floors[q(b)] = max(floors.get(q(b), 0), v)

    # each ring tower's coordinate and confirming OSM object, as the wheel
    # build decided them
    wd, osm, _, _ = B.load_raw()
    B.set_classes(wd)
    out = {"sources": {"massing": os.path.basename(mpath),
                       "wikidata_extra": os.path.basename(xpath),
                       "fetched": mass["fetched"]},
           "cities": {}}
    tally = {"parts": 0, "outline": 0, "podium": 0, "authored": 0,
             "generated": 0, "needle": 0}
    for c in pay["cities"]:
        name = c["city"]
        towers, _, _ = B.filter_city(name, wd["cities"][name],
                                     osm["cities"][name], wd["fetched"], wd)
        byq = {t["qid"]: t for t in towers}
        els = mass["cities"].get(name, {}).get("elements", [])
        byid = {}
        parts = []
        for e in els:
            k = e["type"] + "/" + str(e["id"])
            if k in byid:          # the same part answers for two towers
                continue
            byid[k] = e
            # building:part=no is a mapper saying "not a part" (The Shard's
            # outline carries it); it is not one
            if e.get("tags", {}).get("building:part", "no") != "no":
                parts.append(e)
        clat, clon = c["centre"]
        # every ring tower's outline, for deciding which tower a part is in
        outlines = {}
        for r in c["ring"]:
            t = byq[r[7]]
            el = byid.get(t["osm"])
            if el:
                outlines[r[7]] = outer_rings(el)
        city = []
        for r in c["ring"]:
            qid, h = r[7], r[3]
            t = byq[qid]
            lat0, lon0 = t["lat"], t["lon"]
            el = byid.get(t["osm"])
            rings = outlines.get(qid) or []
            # the line of sight, centre to tower
            az = math.radians(B.bearing(clat, clon, lat0, lon0))
            vvec = (math.sin(az), math.cos(az))
            uvec = (math.cos(az), -math.sin(az))
            rec = {"q": qid, "fac": facade(styles.get(qid, ()), r[5]),
                   "style": sorted(styles.get(qid, ())),
                   "lv": None, "src": None, "parts": []}
            tags = (el or {}).get("tags", {})
            lv = num(tags.get("building:levels")) or floors.get(qid)
            rec["lv"] = int(round(lv)) if lv else int(round(h / STOREY))

            spec = authored.get(qid)
            if spec and spec.get("keep_osm"):
                rec["checked"] = True        # an agent compared it to photos
            if spec and not spec.get("keep_osm") and spec.get("tiers"):
                lrs = [to_local(rg, lat0, lon0) for rg in rings]
                am, atop, anl = authored_mine(spec, lrs)
                if am:
                    nat = None
                    if anl:
                        cu = 0.0
                        if anl[2]:
                            cc = centroid(anl[2])
                            cu = cc[0] * uvec[0] + cc[1] * uvec[1]
                        nat = [anl[0], anl[1], cu]
                    # A drawing that stops more than 8% under Wikidata's
                    # height without a needle was drawn to its roof where
                    # Wikidata counts a mast (Main Tower: 200 m roof, 240 m
                    # antenna): the gap is drawn as a needle rather than the
                    # building being stretched. Above it, or within 8%, the
                    # drawing is scaled to the height.
                    plist, umin, umax, nd = project(am, h, uvec, vvec, atop,
                                                    needle_at=nat,
                                                    free_top=atop >= 0.92 * h,
                                                    gap=0.08)
                    if plist:
                        rec["src"] = "authored"
                        rec["conf"] = spec.get("confidence", "medium")
                        rec["why"] = spec.get("sources", [])[:4]
                        rec["parts"] = plist
                        rec["w"] = [round(umin, 1), round(umax, 1)]
                        rec["fit"] = round(atop / h, 3)
                        if nd:
                            rec["needle"] = nd
                            tally["needle"] += 1
                        tally["authored"] += 1
                        city.append(rec)
                        continue
                tally.setdefault("authored_failed", 0)
                tally["authored_failed"] += 1

            if rings:
                # the tower's footprint in local metres around its own
                # coordinate, and the parts whose centre lies inside it
                loc_rings = [to_local(rg, lat0, lon0) for rg in rings]
                mine = []
                # the middle of the confirming outline: a part whose own
                # outline holds it is a tier of this tower even when the
                # confirming object is itself a small part (Lotte World
                # Tower is confirmed by its 13 m crown; its tiers enclose it)
                core = centroid(max(loc_rings, key=lambda r_: abs(ring_area(r_))))
                for p in parts:
                    prs = outer_rings(p)
                    if not prs:
                        continue
                    lp = to_local(prs[0], lat0, lon0)
                    ctr = centroid(lp)
                    if not any(near_ring(ctr, lr, 2.0) for lr in loc_rings) \
                            and not inside(core, lp):
                        continue
                    # a part inside a shared podium belongs to the nearest
                    # ring tower whose outline holds it
                    own = qid
                    best = math.hypot(*ctr)
                    for oq, ors in outlines.items():
                        if oq == qid or not ors:
                            continue
                        ot = byq[oq]
                        o_l = to_local([(ot["lat"], ot["lon"])], lat0, lon0)[0]
                        if any(near_ring(ctr, to_local(rr, lat0, lon0), 2.0)
                               for rr in ors):
                            d = math.hypot(ctr[0] - o_l[0], ctr[1] - o_l[1])
                            if d < best:
                                own, best = oq, d
                    if own != qid:
                        continue
                    hh = part_heights(p.get("tags", {}))
                    if hh:
                        mine.append((lp, hh + (roof_dir(p.get("tags", {})),)))
                src = "parts" if mine else "outline"
                if not mine:
                    hh = part_heights(tags) or (0.0, h, 0.0, 0)
                    for lr in loc_rings:
                        mine.append((lr, hh + (roof_dir(tags),)))
                top = max(b[1] + b[2] for _, b in mine)

                def span(rs):
                    us = [p[0] * uvec[0] + p[1] * uvec[1] for r_ in rs for p in r_]
                    return (max(us) - min(us)) if us else 0.0
                w_out = max(span(loc_rings), span([lp for lp, _ in mine]))
                w_parts = span([lp for lp, _ in mine]) if src == "parts" else w_out
                if src == "parts" and w_parts < 0.3 * w_out and h >= 100:
                    # only the crown or the spire is modelled: the outline
                    # is the tower
                    top = 0.0
                if src == "parts" and \
                        min(b[0] for _, b in mine) > 0.25 * max(top, 1):
                    # every part floats: a roof or a crown with nothing
                    # mapped under it (Harbour Plaza: one strip at 132 m)
                    top = 0.0
                if src == "parts" and top < FIT_BAD * h:
                    # the parts found are a podium or a neighbour, not the
                    # tower: fall back to its outline
                    src = "outline"
                    hh = part_heights(tags) or (0.0, h, 0.0, 0)
                    mine = [(lr, hh + (roof_dir(tags),)) for lr in loc_rings]
                    top = max(b[1] + b[2] for _, b in mine)
                if src == "outline" and h >= 100 and w_out > 1.0 * h:
                    # An outline wider than the tower is tall is a complex,
                    # not a shaft: Dubai World Trade Centre's is 500 m
                    # across. Raising all of it to the tower's height draws
                    # a wall that is not there. So the outline stands as a
                    # podium and the tower above it is a plain slab at the
                    # tower's own coordinate, and says so (src "podium").
                    src = "podium"
                    pod = min(30.0, 0.2 * h)
                    mine = [(lr, (0.0, pod, 0.0, 0, None)) for lr in loc_rings]
                    side = max(18.0, min(60.0, h / 6.5))
                    sq = [(-side / 2, -side / 2), (side / 2, -side / 2),
                          (side / 2, side / 2), (-side / 2, side / 2),
                          (-side / 2, -side / 2)]
                    mine.append((sq, (0.0, h, 0.0, 0, None)))
                    top = h
                elif src == "outline":
                    # an extruded outline stands at the tower's height; its
                    # own roof, if mapped, is kept
                    mine = [(lr, (0.0, h - b[2], b[2], b[3], b[4]))
                            for lr, b in mine]
                    top = h
                if COLLECT is not None:
                    COLLECT[qid] = {"src": src, "outline": loc_rings,
                                    "mine": mine, "h": h}
                plist, umin, umax, nd = project(mine, h, uvec, vvec, top)
                if nd:
                    rec["needle"] = nd
                    tally["needle"] += 1
                if plist and (umax - umin) < max(10.0, 0.04 * h) and h >= 80:
                    # too thin to be the tower (JW Marriott Marquis came out
                    # 4 m wide: the match is a sliver of it); a slab says so
                    plist = []
                if plist:
                    rec["src"] = src
                    rec["parts"] = plist
                    rec["w"] = [round(umin, 1), round(umax, 1)]
                    rec["fit"] = round(top / h, 3)
                    tally[src] += 1
                    city.append(rec)
                    continue
            # nothing to draw from: a plain slab, said to be generated
            side = max(18.0, min(60.0, h / 6.5))
            back = math.degrees(az) + 180.0
            rec["src"] = "generated"
            rec["parts"] = [{"z0": 0.0, "z1": h, "rh": 0.0, "roof": 0,
                             "u": [-side / 2, side / 2], "d": 0.0,
                             "f": [[-side / 2, -side * 0.1,
                                    round((back + 45) % 360), side],
                                   [-side * 0.1, side / 2,
                                    round((back - 45) % 360), side]]}]
            rec["w"] = [-side / 2, side / 2]
            tally["generated"] += 1
            city.append(rec)
        out["cities"][name] = city
    p = os.path.join(HERE, "data", "massing.json")
    json.dump(out, open(p, "w", encoding="utf-8"), separators=(",", ":"))
    print("  wrote", p, "%.0f kB" % (os.path.getsize(p) / 1024))
    print("  ", tally)
    return out


if __name__ == "__main__":
    main()
