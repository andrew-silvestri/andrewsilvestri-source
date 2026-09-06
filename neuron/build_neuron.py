"""How much of a drawn neuron was measured.

Reads  data/neurons.csv.gz    the census of NeuroMorpho.Org (fetch_data.py)
       data/swc_metrics.csv   morphometrics from files, computed by swclib
       data/complete_metrics.csv
                              the complete set, opened and measured
       data/swc/<source>/     the three reconstructions the figures draw
       data/manifest.json     what was fetched, when, and its hashes
Writes outputs/neuron_payload.json

Everything the page states is computed here.  Nothing is typed into the
template except prose; every number arrives through a placeholder.

Run:  python3 build_neuron.py
"""
import argparse
import csv
import gzip
import itertools
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swclib                                                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "outputs")

# --- the five properties a drawing at true proportions needs ----------------
# Each is read from the archive's own metadata, and each is the archive's own
# claim rather than a measurement of the file; check 7 in test_neuron.py is
# the reason that distinction is kept in view.
CONSTRAINTS = [
    ("parts", "a soma, a dendrite and an axon",
     lambda r: r["domain"] == "Dendrites, Soma, Axon"),
    ("diameter", "a measured diameter",
     lambda r: not (r["attributes"] or "").startswith("No Diameter")),
    ("three_d", "three dimensions",
     lambda r: ", 3D," in (r["attributes"] or "")),
    ("axon_complete", "an axon its depositor marked complete",
     lambda r: "Axon Complete" in (r["physical_integrity"] or "")),
    ("shrinkage", "a correction for tissue shrinkage",
     lambda r: (r["shrinkage_corrected"] or "").strip().lower().startswith("correc")
     and "not" not in (r["shrinkage_corrected"] or "").lower()),
]

# The gradient verdict, fixed before the answer is known so that it cannot be
# tuned to it.  An archive qualifies for the within-archive test only if it
# has enough cells and enough spread in reach for a gradient to be visible at
# all; a set of cells that all reach the same distance cannot show one.
GRADIENT_MIN_CELLS = 20
GRADIENT_MIN_SPREAD = 3.0        # max reach / min reach, within the archive
GRADIENT_RHO = 0.20              # what counts as a relationship
GRADIENT_SHARE = 0.60            # of qualifying archives that must show it

# SWC has seven columns and none of them is a unit.  The convention is
# micrometres and there is no way for a file to say otherwise, so a laboratory
# writing nanometres or voxels produces a file that is silently, undetectably
# wrong - the pitfall named in the format's own documentation, and one this
# sample contains.  The soma is the only yardstick inside the file: it is the
# one structure whose true size is known independently and varies little,
# 5-50 um across essentially every neuron.  Where the radius column is a
# placeholder the soma says nothing about units, so a reach bound stands in:
# no neuron reaches further than any dimension of the brain it sits in.
UNIT_SOMA_MIN, UNIT_SOMA_MAX = 3.0, 60.0
UNIT_REACH_MAX = 20000.0

# Published electron-microscopy calibres.  Light microscopy cannot resolve
# these, which is why they are the right yardstick for what a true-proportion
# drawing would have to render.
THINNEST = {
    "value_um": 0.17,
    "structure": "CA3-to-CA1 axon shaft, measured by electron microscopy",
    "source": "Shepherd & Harris, J Neurosci 18(20):8300-8310, 1998 "
              "(0.17 +/- 0.04 um)",
}


# --- what the two drawing figures are laid out on, in CSS pixels ------------
# The figures are displayed DISPLAY_PX wide (sitefig.NOTES), one point per
# pixel, and every "under one pixel" statement on the page is made at that
# size.  Both figure builders place their axes from these boxes, and the
# shares below are computed from the same boxes, so the number in the caption
# and the drawing above it cannot disagree about what a pixel is.
DISPLAY_PX = 714
STRIP_PX = 28            # a strip inside each panel, below the drawing, for the scale bar
HAIRLINE_PT = 0.5        # the shape's hairline, drawn under the true widths
WINDOW_PAD = 0.05        # panel A: the cell's bounding box, padded this much per side
WINDOW_B = 0.10          # panel B: this fraction of panel A's window, centred on the soma
WINDOW_C_SOMA = 1.5      # panel C: this many soma diameters, centred on the soma
LADDER_CSS = {           # (x, y, w, h) from the top-left, in CSS px
    "fig": (714, 560),
    "A": (8, 30, 316, 522),
    "B": (354, 30, 352, 250),
    "C": (354, 310, 352, 250),
}
PAIR_CSS = {
    "fig": (714, 458),
    "shared": (8, 30, 470, 420),     # both cells at one scale
    "own": (508, 30, 198, 226),      # the slice cell at its own scale
    "gap_um_frac": 0.06,             # the gap between the two cells, as a share of the wide one
}


def read_census():
    with gzip.open(os.path.join(DATA, "neurons.csv.gz"), "rt", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


_TEXT_COLS = ("archive", "neuron_name", "species", "source", "file", "nmo_attributes",
              "nmo_domain", "dendrite_type", "structure", "cell_type", "brain_region",
              "doi", "protocol")


def _typed(rows):
    for r in rows:
        for k, v in list(r.items()):
            if v in ("", "None"):
                r[k] = None
            elif k in ("whole_brain", "diam_measured"):
                r[k] = v in ("True", "true", "1")
            elif k not in _TEXT_COLS:
                try:
                    r[k] = float(v)
                except (TypeError, ValueError):
                    pass
    return rows


def read_metrics():
    with open(os.path.join(DATA, "swc_metrics.csv"), encoding="utf-8") as fh:
        return _typed(list(csv.DictReader(fh)))


def read_complete():
    with open(os.path.join(DATA, "complete_metrics.csv"), encoding="utf-8") as fh:
        return _typed(list(csv.DictReader(fh)))


def unit_check(mets):
    """Which sampled archives are in micrometres, and which cannot be told.

    Returns (per-archive verdicts, the set of archive names to trust).  An
    archive fails if the median soma of its measured-diameter cells is not a
    plausible soma, or if any of its cells reaches further than a brain.
    """
    by = {}
    for m in mets:
        by.setdefault(m["archive"], []).append(m)
    out, ok = [], set()
    for arch, g in sorted(by.items()):
        som = [m["soma_diam_um"] for m in g
               if m.get("diam_measured") and m.get("soma_diam_um")]
        reach = [m["max_radial_um"] for m in g if m.get("max_radial_um")]
        med = float(np.median(som)) if som else None
        far = max(reach) if reach else 0.0
        why = None
        if med is not None and not (UNIT_SOMA_MIN <= med <= UNIT_SOMA_MAX):
            why = "median soma of %.1f um is not a soma" % med
        elif far > UNIT_REACH_MAX:
            why = "an arbor reaching %.0f um is longer than a brain" % far
        out.append({"archive": arch, "n": len(g),
                    "median_soma_um": round(med, 2) if med is not None else None,
                    "max_reach_um": round(far, 1),
                    "yardstick": "soma" if med is not None else "reach",
                    "micrometres": why is None, "why": why})
        if why is None:
            ok.add(arch)
    return out, ok


def spearman(x, y):
    """Rank correlation, numpy only."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if len(x) < 4:
        return None
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    if rx.std() == 0 or ry.std() == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


# ---------------------------------------------------------------- cascade ---

def cascade(rows):
    n = len(rows)
    flags = [[f(r) for _, _, f in CONSTRAINTS] for r in rows]
    alone = []
    for i, (key, label, _) in enumerate(CONSTRAINTS):
        c = sum(1 for fl in flags if fl[i])
        alone.append({"key": key, "label": label, "n": c, "share": round(c / n, 6)})

    steps, run = [], list(range(0))
    for k in range(1, len(CONSTRAINTS) + 1):
        combo = tuple(range(k))
        c = sum(1 for fl in flags if all(fl[i] for i in combo))
        steps.append({"key": CONSTRAINTS[k - 1][0], "label": CONSTRAINTS[k - 1][1],
                      "n": c, "share": round(c / n, 8)})

    # every subset, so the app can apply the constraints in any order
    subsets = {}
    for k in range(len(CONSTRAINTS) + 1):
        for combo in itertools.combinations(range(len(CONSTRAINTS)), k):
            key = "".join(str(i) for i in combo) or "-"
            subsets[key] = sum(1 for fl in flags if all(fl[i] for i in combo))

    full = subsets["01234"]
    keep = [r for r, fl in zip(rows, flags) if all(fl)]
    return {"n_total": n, "alone": alone, "steps": steps, "subsets": subsets,
            "n_complete": full, "order_costs": order_costs(subsets)}, keep


def order_costs(subsets):
    """What each constraint costs at each position, over all 120 orders.

    The five constraints are not independent, so what one removes depends
    on what has already been removed.  A cost is 1 - (count after) /
    (count before), and every count is one of the 32 subsets, so nothing
    here is estimated: each cell of the five-by-five table is the exact
    cost over the 24 orders that put that constraint at that position.
    This is the whole of the order-dependence finding, in one table; the
    figure draws it, and it replaced the reorderable cascade app on
    2026-09-06 because a still figure holds all 120 orders at once and the
    app held one.
    """
    k = len(CONSTRAINTS)

    def key(done):
        return "".join(str(i) for i in sorted(done)) or "-"
    cost = [[[] for _ in range(k)] for _ in range(k)]
    cheapest, dearest = [None] * k, [None] * k
    for perm in itertools.permutations(range(k)):
        done = []
        for pos, i in enumerate(perm):
            before = subsets[key(done)]
            done.append(i)
            after = subsets[key(done)]
            c = 1.0 - after / before if before else 0.0
            cost[i][pos].append(c)
            if cheapest[i] is None or c < cheapest[i][0]:
                cheapest[i] = (c, list(perm[:pos]))
            if dearest[i] is None or c > dearest[i][0]:
                dearest[i] = (c, list(perm[:pos]))
    out = []
    for i, (ck, label, _) in enumerate(CONSTRAINTS):
        allv = [v for pos in range(k) for v in cost[i][pos]]
        out.append({
            "key": ck, "label": label,
            "first": round(cost[i][0][0], 6), "last": round(cost[i][k - 1][0], 6),
            "min": round(min(allv), 6), "max": round(max(allv), 6),
            "by_position": [{"mean": round(sum(v) / len(v), 6), "min": round(min(v), 6),
                             "max": round(max(v), 6)} for v in cost[i]],
            "cheapest_after": [CONSTRAINTS[j][0] for j in cheapest[i][1]],
            "dearest_after": [CONSTRAINTS[j][0] for j in dearest[i][1]],
            "swing": round(max(allv) - min(allv), 6),
        })
    return {"n_orders": len(list(itertools.permutations(range(k)))), "constraints": out,
            "most_order_dependent": max(out, key=lambda o: o["swing"])["key"],
            "least_order_dependent": min(out, key=lambda o: o["swing"])["key"]}


def describe_104(keep):
    """Who the fully-qualified reconstructions belong to."""
    from collections import Counter
    labs = Counter(r["archive"] for r in keep)
    sp = Counter(r["species"] for r in keep)
    reg = Counter((r["brain_region"] or "").split("|")[0] for r in keep)
    doi = Counter(r["doi"] for r in keep if r["doi"])
    top_doi, top_n = (doi.most_common(1)[0] if doi else ("", 0))
    return {
        "n": len(keep),
        "n_labs": len(labs),
        "labs": [{"archive": a, "n": c} for a, c in labs.most_common()],
        "species": [{"species": s, "n": c} for s, c in sp.most_common()],
        "regions": [{"region": s, "n": c} for s, c in reg.most_common(5)],
        "has_human": any((s or "").lower() == "human" for s in sp),
        "top_doi": top_doi, "top_doi_n": top_n,
        "top_doi_share": round(top_n / len(keep), 4) if keep else 0,
    }


def opened(comp):
    """The complete set, measured from its files rather than counted from
    its flags.  Every file in data/complete_metrics.csv passed all five
    constraints in the archive's metadata; this is what they hold."""
    from collections import Counter
    n = len(comp)
    fail = [m for m in comp if not m["diam_measured"]]
    single = [m for m in comp if (m.get("n_distinct_diam") or 0) == 1]
    fails_by = Counter(m["archive"] for m in fail)
    # the projection cells: the part of the set that looks like the thing the
    # page says no file contains, so the page has to say what they are
    proj_all = [m for m in comp if "projection" in (m["cell_type"] or "").lower()
                and "principal" in (m["cell_type"] or "").lower()]
    pdoi = Counter(m["doi"] for m in proj_all if m["doi"])
    top = pdoi.most_common(1)[0][0] if pdoi else None
    # the largest single-paper group among them is what the page describes,
    # because what has to be said about them is said by their paper
    proj = [m for m in proj_all if m["doi"] == top]
    return {
        "n": n,
        "n_pass_width": n - len(fail),
        "n_fail_width": len(fail),
        "fails_by_archive": [{"archive": a, "n": c} for a, c in fails_by.most_common()],
        "n_single_width": len(single),
        "single_width_archives": sorted({m["archive"] for m in single}),
        "projection": {
            "n_all": len(proj_all),
            "n": len(proj),
            "archives": sorted({m["archive"] for m in proj}),
            "species": sorted({m["species"] for m in proj}),
            "regions": sorted({m["brain_region"] for m in proj}),
            "protocols": sorted({m["protocol"] for m in proj}),
            "doi": top,
            "reach_min_um": round(min(m["max_radial_um"] for m in proj), 1) if proj else None,
            "reach_max_um": round(max(m["max_radial_um"] for m in proj), 1) if proj else None,
            "axon_min_um": round(min(m["len_axon_um"] for m in proj), 1) if proj else None,
            "axon_max_um": round(max(m["len_axon_um"] for m in proj), 1) if proj else None,
            "distinct_min": int(min(m["n_distinct_diam"] for m in proj)) if proj else None,
            "distinct_max": int(max(m["n_distinct_diam"] for m in proj)) if proj else None,
            "n_pass_width": sum(1 for m in proj if m["diam_measured"]),
        },
    }


# ------------------------------------------------------------ the drawing ---

def _cell_xy(path):
    """Points, segments and widths of one file, in the two drawable columns.

    Lengths come from swclib.segments (3D, the depositor's own path length);
    positions and windows come from load_xy, which has no z.  Nothing here
    is a figure, but the windows it computes are the figures' windows, so
    it draws from the same two columns they do.
    """
    idx, typ, xyz, rad, par = swclib.read_swc(path)
    xy = swclib.load_xy(path)
    seg_len, seg_typ, seg_diam, _ = swclib.segments(idx, typ, xyz, rad, par)
    neurite = typ != swclib.SOMA
    som = xy[typ == swclib.SOMA]
    soma_c = som.mean(axis=0) if len(som) else xy[0]
    soma_d = 2.0 * float(rad[typ == swclib.SOMA].mean()) if len(som) else 0.0
    return {"xy": xy, "neurite": neurite, "soma_c": soma_c, "soma_d": soma_d,
            "seg_len": seg_len[seg_typ != swclib.SOMA], "seg_typ": seg_typ[seg_typ != swclib.SOMA],
            "seg_diam": seg_diam[seg_typ != swclib.SOMA]}


def ladder_windows(path):
    """The three windows figure 5 draws, from the file and LADDER_CSS.

    A: the whole cell, its bounding box padded WINDOW_PAD per side.
    B: WINDOW_B of A's longer side, square, centred on the soma.
    C: WINDOW_C_SOMA soma diameters, square, centred on the soma.
    Each panel's micrometres per CSS pixel follow from its window and its
    box, with STRIP_PX of the box kept under the drawing for the scale bar.
    """
    c = _cell_xy(path)
    pts = c["xy"][c["neurite"]]
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    span = hi - lo
    a_win = span * (1 + 2 * WINDOW_PAD)
    a_centre = (lo + hi) / 2
    b_win = float(a_win.max() * WINDOW_B)
    c_win = float(c["soma_d"] * WINDOW_C_SOMA)
    out = {}
    for key, win, centre in (("A", a_win, a_centre),
                             ("B", np.array([b_win, b_win]), c["soma_c"]),
                             ("C", np.array([c_win, c_win]), c["soma_c"])):
        x, y, w, h = LADDER_CSS[key]
        draw_h = h - STRIP_PX
        upp = float(max(win[0] / w, win[1] / draw_h))
        ax_sel = c["seg_typ"] == swclib.AXON

        def under(sel):
            ll = c["seg_len"][sel]
            return round(float(ll[c["seg_diam"][sel] < upp].sum() / ll.sum()), 4) if ll.sum() else None
        out[key] = {
            "box_css": [x, y, w, h],
            "window_um": [round(float(win[0]), 2), round(float(win[1]), 2)],
            "centre_um": [round(float(centre[0]), 3), round(float(centre[1]), 3)],
            "um_per_px": round(upp, 5),
            "share_under_one_px": under(np.ones(len(ax_sel), dtype=bool)),
            "axon_under_one_px": under(ax_sel),
            "dendrite_under_one_px": under(~ax_sel),
            "soma_px": round(c["soma_d"] / upp, 2),
            "thinnest_em_px": round(THINNEST["value_um"] / upp, 3),
        }
    return out


def drawn_block(man):
    """The cell from the complete set that figure 5 draws, measured from its
    file, with the windows it is drawn in."""
    d = man.get("drawn")
    if not d:
        return None
    path = os.path.join(HERE, d["file"])
    m = swclib.metrics(path, source=swclib.source_of(path))
    c = _cell_xy(path)
    by_part = {}
    for t, name in swclib.TYPE_NAME.items():
        sel = c["seg_typ"] == t
        if not sel.any():
            continue
        dd, ll = c["seg_diam"][sel], c["seg_len"][sel]
        vals, inv = np.unique(np.round(dd, 6), return_inverse=True)
        wl = np.bincount(inv, weights=ll)
        by_part[name] = {
            "len_um": round(float(ll.sum()), 1),
            "n_distinct_diam": int(len(vals)),
            "diam_min_um": round(float(dd.min()), 3),
            "diam_max_um": round(float(dd.max()), 3),
            "modal_diam_um": round(float(vals[int(wl.argmax())]), 3),
            "frac_len_modal": round(float(wl.max() / ll.sum()), 4),
        }
    dend = {"len_um": round(by_part.get("basal", {}).get("len_um", 0)
                             + by_part.get("apical", {}).get("len_um", 0), 1)}
    dsel = c["seg_typ"] != swclib.AXON
    if dsel.any():
        dd, ll = c["seg_diam"][dsel], c["seg_len"][dsel]
        vals, inv = np.unique(np.round(dd, 6), return_inverse=True)
        wl = np.bincount(inv, weights=ll)
        dend.update({"n_distinct_diam": int(len(vals)),
                     "diam_min_um": round(float(dd.min()), 3),
                     "diam_max_um": round(float(dd.max()), 3),
                     "modal_diam_um": round(float(vals[int(wl.argmax())]), 3),
                     "frac_len_modal": round(float(wl.max() / ll.sum()), 4)})
    pts = c["xy"][c["neurite"]]
    extent = float((pts.max(axis=0) - pts.min(axis=0)).max())
    # The width count, stated four ways so the page cannot contradict itself:
    # the axon's values, the dendrites' values, the values both share, and
    # their union - which is what n_distinct_diam and the width rule count,
    # because swclib.metrics() measures neurites only.  The soma is a
    # decision: it is drawn (the disc in every panel, at its radius) and it
    # is counted in n_distinct_file, but it belongs to neither compartment
    # and is not part of the width rule, which asks whether the *neurite*
    # radii vary.
    ax_vals = set(np.round(c["seg_diam"][c["seg_typ"] == swclib.AXON], 6).tolist())
    dn_vals = set(np.round(c["seg_diam"][c["seg_typ"] != swclib.AXON], 6).tolist())
    soma_vals = {round(c["soma_d"], 6)} if c["soma_d"] else set()
    widths = {
        "axon": len(ax_vals), "dendrite": len(dn_vals),
        "shared": len(ax_vals & dn_vals), "neurite_union": len(ax_vals | dn_vals),
        "soma": len(soma_vals - ax_vals - dn_vals),
        "file": len(ax_vals | dn_vals | soma_vals),
        "soma_drawn": True, "soma_in_width_rule": False,
    }
    return {
        "widths": widths,
        "file": d["file"], "neuron": d["neuron"], "neuron_id": d["neuron_id"],
        "archive": d["archive"], "species": d["species"],
        "cell_type": [s for s in (d["cell_type"] or "").split("|") if s],
        "brain_region": [s for s in (d["brain_region"] or "").split("|") if s],
        "doi": d["doi"], "protocol": d["protocol"],
        "rule": d["rule"],
        "source": swclib.source_of(path),
        "z_drawable": swclib.source_of(path) in swclib.Z_TRUSTWORTHY,
        "reach_um": m["max_radial_um"], "axon_um": m["len_axon_um"],
        "dend_um": m["len_dend_um"], "soma_diam_um": m["soma_diam_um"],
        "extent_xy_um": round(extent, 1),
        "n_distinct_diam": m["n_distinct_diam"],
        "frac_len_modal_diam": m["frac_len_modal_diam"],
        "diam_measured": m["diam_measured"],
        "axon": by_part.get("axon"), "dendrite": dend,
        "orders_to_em": round(float(np.log10(extent / THINNEST["value_um"])), 2),
        "windows": ladder_windows(path),
    }


def pair_geometry(pair):
    """Figure 2's shared frame: both cells at one scale, and what the slice
    cell measures in it."""
    al, ml = pair.get("allen"), pair.get("mouselight")
    if not (al and ml):
        return None
    spans = {}
    for src, d in (("allen", al), ("mouselight", ml)):
        c = _cell_xy(os.path.join(HERE, d["file"]))
        pts = c["xy"][c["neurite"]]
        spans[src] = pts.max(axis=0) - pts.min(axis=0)
    wide, small = spans["mouselight"], spans["allen"]
    gap = float(wide.max() * PAIR_CSS["gap_um_frac"])
    win_x = float(wide[0] + gap + small[0])
    win_y = float(max(wide[1], small[1]))
    x, y, w, h = PAIR_CSS["shared"]
    upp = max(win_x * (1 + 2 * WINDOW_PAD) / w, win_y * (1 + 2 * WINDOW_PAD) / (h - STRIP_PX))
    ox, oy, ow, oh = PAIR_CSS["own"]
    upp_own = max(small[0] * (1 + 2 * WINDOW_PAD) / ow, small[1] * (1 + 2 * WINDOW_PAD) / (oh - STRIP_PX))
    return {
        "extent_ratio": round(float(wide.max() / small.max()), 2),
        "shared_um_per_px": round(float(upp), 4),
        "own_um_per_px": round(float(upp_own), 4),
        "allen_px_in_shared": round(float(small.max() / upp), 1),
        "allen_soma_px_in_shared": round(float((al.get("soma_diam_um") or 0) / upp), 2),
        "gap_um": round(gap, 1),
        "allen_span_um": [round(float(v), 1) for v in small],
        "mouselight_span_um": [round(float(v), 1) for v in wide],
    }


def tradeoff(rows):
    """Of the reconstructions whose axon is complete, how many measure width."""
    ac = [r for r in rows if "Axon Complete" in (r["physical_integrity"] or "")]
    md = [r for r in ac if not (r["attributes"] or "").startswith("No Diameter")]
    return {"axon_complete": len(ac), "and_measured_diameter": len(md),
            "share": round(len(md) / len(ac), 6) if ac else None}


# --------------------------------------------------------------- gradient ---

def gradient_test(mets):
    """Does thickness coarsen with reach *within* an archive, or only between
    reconstruction methods?

    Stage 1 measured the relationship across two datasets and found a rank
    correlation of 0.88 - but Allen's arbors reach at most 1,781 um and
    MouseLight's at least 865 um, so the two barely overlap and the gradient
    was indistinguishable from the boundary between them.  Within Allen alone
    it was 0.078.  This runs the same test inside each archive, where method
    is held constant, and the verdict rule above was fixed before the answer
    was known.
    """
    usable = [m for m in mets
              if m.get("max_radial_um") and m.get("frac_len_modal_diam") is not None]
    by = {}
    for m in usable:
        by.setdefault(m["archive"], []).append(m)

    per = []
    for arch, g in sorted(by.items()):
        reach = [m["max_radial_um"] for m in g]
        spread = max(reach) / min(reach) if min(reach) > 0 else 0
        entry = {"archive": arch, "n": len(g), "reach_spread": round(spread, 2),
                 "reach_min": round(min(reach), 1), "reach_max": round(max(reach), 1)}
        entry["qualifies"] = bool(len(g) >= GRADIENT_MIN_CELLS and spread >= GRADIENT_MIN_SPREAD)
        if entry["qualifies"]:
            rho = spearman(np.log10(reach), [m["frac_len_modal_diam"] for m in g])
            entry["rho"] = round(rho, 4) if rho is not None else None
        else:
            entry["rho"] = None
        per.append(entry)

    q = [p for p in per if p["qualifies"] and p["rho"] is not None]
    rhos = [p["rho"] for p in q]
    n_pos = sum(1 for r in rhos if r > GRADIENT_RHO)
    share = (n_pos / len(q)) if q else 0.0
    median_rho = round(float(np.median(rhos)), 4) if rhos else None
    held = bool(q and median_rho is not None
                and median_rho > GRADIENT_RHO and share >= GRADIENT_SHARE)

    # the pooled figure, for contrast: this is the number that looks strong
    # and means little, because archive and method are confounded with reach
    pooled = spearman(np.log10([m["max_radial_um"] for m in usable]),
                      [m["frac_len_modal_diam"] for m in usable])

    return {
        "n_cells": len(usable), "n_archives": len(by),
        "n_qualifying_archives": len(q),
        "rule": {"min_cells": GRADIENT_MIN_CELLS, "min_reach_spread": GRADIENT_MIN_SPREAD,
                 "rho_threshold": GRADIENT_RHO, "share_threshold": GRADIENT_SHARE},
        "per_archive": per,
        "median_within_rho": median_rho,
        "share_above_threshold": round(share, 4),
        "pooled_rho": round(pooled, 4) if pooled is not None else None,
        "held": held,
        "verdict": ("a gradient survives inside archives" if held
                    else "no gradient survives inside archives"),
    }


def method_split(mets):
    """The trade-off, measured on files rather than counted from flags."""
    wb = [m for m in mets if m.get("whole_brain")]
    sl = [m for m in mets if not m.get("whole_brain")]

    def summarise(g, label):
        reach = [m["max_radial_um"] for m in g if m.get("max_radial_um")]
        nd = [m["n_distinct_diam"] for m in g if m.get("n_distinct_diam")]
        ms = [m["frac_len_modal_diam"] for m in g if m.get("frac_len_modal_diam") is not None]
        meas = [m for m in g if m.get("diam_measured")]
        return {"label": label, "n": len(g),
                "reach_median_um": round(float(np.median(reach)), 1) if reach else None,
                "distinct_diam_median": int(np.median(nd)) if nd else None,
                "modal_share_median": round(float(np.median(ms)), 4) if ms else None,
                "n_diam_measured": len(meas),
                "share_diam_measured": round(len(meas) / len(g), 4) if g else None}
    return {"whole_brain": summarise(wb, "whole-brain, in vivo"),
            "slice": summarise(sl, "slice and culture")}


def ladder(mets, pair):
    """What a drawing at true proportions would have to span."""
    wb = [m["max_extent_um"] for m in mets
          if m.get("whole_brain") and m.get("max_extent_um")]
    extent = float(np.median(wb)) if wb else None
    thin = THINNEST["value_um"]
    rng = extent / thin if extent else None
    return {"extent_um": round(extent, 1) if extent else None,
            "thinnest_um": thin,
            "dynamic_range": int(round(rng)) if rng else None,
            "orders": round(float(np.log10(rng)), 2) if rng else None,
            "px_at_1000": round(1000.0 / rng, 4) if rng else None,
            "px_for_one_px_neurite": int(round(rng)) if rng else None}


def scatter(mets):
    """One row per sampled cell, for the trade-off figure."""
    out = []
    for m in mets:
        if not m.get("max_radial_um") or m.get("frac_len_modal_diam") is None:
            continue
        out.append({"archive": m["archive"], "whole_brain": bool(m.get("whole_brain")),
                    "reach_um": round(m["max_radial_um"], 1),
                    "modal_share": round(m["frac_len_modal_diam"], 4),
                    "n_distinct_diam": int(m["n_distinct_diam"] or 0),
                    "axon_um": round(m["len_axon_um"], 1) if m.get("len_axon_um") else 0.0,
                    "diam_measured": bool(m.get("diam_measured"))})
    return out


def pair_block(man, mets):
    """The two reconstructions figure 2 draws, with what each lacks."""
    ex = man.get("exemplars", {})
    by = {(m["archive"], str(m["neuron_name"])): m for m in mets}
    out = {}
    for src, e in ex.items():
        m = by.get((e["archive"], str(e["neuron"])))
        out[src] = {
            "file": e["file"], "neuron": e["neuron"], "archive": e["archive"],
            "source": src,
            "reach_um": round(e["reach_um"], 1),
            "axon_um": round(e["axon_um"], 1),
            "dend_um": round(e["dend_um"], 1),
            "diam_measured": bool(e["diam_measured"]),
            "n_distinct_diam": int(e["n_distinct_diam"]),
            "frac_len_modal_diam": round(e["frac_len_modal_diam"], 4),
            "soma_diam_um": round(m["soma_diam_um"], 2) if m and m.get("soma_diam_um") else None,
            # z is recorded so the figure builder and the test agree on it
            "z_drawable": src in swclib.Z_TRUSTWORTHY,
        }
    return out


def looked_up():
    return {
        "diffraction_limit": {
            "value_um": "0.20-0.30 lateral, 0.50-0.70 axial",
            "source": "Huang, Bates & Zhuang, Annu Rev Biochem 78:993-1016, 2009, "
                      "doi:10.1146/annurev.biochem.77.061906.092014"},
        "thinnest_axon": {"value_um": THINNEST["value_um"], "source": THINNEST["source"]},
        "spine_neck": {"value_um": 0.15,
                       "source": "Harris & Stevens, J Neurosci 9(8):2982-2997, 1989 "
                                 "(0.15 +/- 0.06 um)"},
        "axon_truncation": {
            "value": "48–49% of intracortical axon lost in a 300 µm slice; 15–17% of dendrite",
            "source": "van Pelt, van Ooyen & Uylings, Front Neuroanat 8:54, 2014, "
                      "doi:10.3389/fnana.2014.00054"},
        "z_shrinkage": {
            "value": "63 +/- 10% in 350 um slices; total dendritic length rises only 11 +/- 2% "
                     "when corrected",
            "source": "Mohan et al., Cereb Cortex 25(12):4839-4853, 2015, "
                      "doi:10.1093/cercor/bhv188"},
        "vibratome_shrinkage": {
            "value": "80 um vibratome sections measured at 31.78 um after processing",
            "source": "Gardella et al., J Neurosci Methods 124(1):45-59, 2003, "
                      "doi:10.1016/S0165-0270(02)00363-1"},
        "shrinkage_factors": {
            "value": "x1.1 in x-y, x2.1 in z",
            "source": "Marx & Feldmeyer, Cereb Cortex 23(12):2803-2817, 2013, "
                      "doi:10.1093/cercor/bhs254, attributing Marx et al., Nat Protoc "
                      "7(2):394-407, 2012, doi:10.1038/nprot.2011.449"},
        "allen_uncorrected": {
            "value": "z-derived features excluded rather than corrected; the correction is "
                     "applied per cell downstream",
            "source": "Gouwens et al., Nat Neurosci 22(7):1182-1195, 2019, "
                      "doi:10.1038/s41593-019-0417-0; Lee et al., eLife 10:e65482, 2021, "
                      "doi:10.7554/eLife.65482"},
        "diameter_subjective": {
            "value": "diameter was excluded from the DIADEM competition as too subjective at "
                     "the resolutions used for whole-arbor reconstruction",
            "source": "Gillette, Brown & Ascoli, Neuroinformatics 9(2-3):233-245, 2011, "
                      "doi:10.1007/s12021-011-9117-y"},
        "diameter_between_pipelines": {
            "value": "1.80 +/- 0.15 um vs 0.91 +/- 0.09 um on visually matched segments of the "
                     "same eight cells",
            "source": "Blackman, Grabuschnig, Legenstein & Sjostrom, Front Neuroanat 8:65, "
                      "2014, doi:10.3389/fnana.2014.00065"},
        "tracer_agreement": {
            "value": "three experts tracing one dendrite agreed to an intersection-over-union "
                     "of 0.470 +/- 0.071; one person re-tracing agreed with themselves 87.5%",
            "source": "Fernholz, Guggiana Nilo, Bonhoeffer & Kist, PLoS Comput Biol "
                      "20(2):e1011774, 2024, doi:10.1371/journal.pcbi.1011774"},
        "whole_brain_axon": {
            "value": "more than 85 m of axon across more than 1,000 projection neurons",
            "source": "Winnubst et al., Cell 179(1):268-281.e13, 2019, "
                      "doi:10.1016/j.cell.2019.07.042"},
        "spine_factor": {
            "value": "F = 1.78-2.39, mean 1.946, applied only beyond 60 um from the soma",
            "source": "Eyal et al., eLife 5:e16553, 2016, doi:10.7554/eLife.16553"},
        "spine_factor_miscited": {
            "value": "contains no membrane-area factor; it is the source for where spines are, "
                     "not for how much membrane they carry",
            "source": "Megias, Emri, Freund & Gulyas, Neuroscience 102(3):527-540, 2001, "
                      "doi:10.1016/S0306-4522(00)00496-6"},
        "synaptic_delay": {
            "value": "minimum 0.4-0.5 ms, modal about 0.75 ms, frog neuromuscular junction at "
                     "20 C in low-calcium Ringer",
            "source": "Katz & Miledi, Proc R Soc Lond B 161(985):483-495, 1965, "
                      "doi:10.1098/rspb.1965.0016"},
        "central_synapse_delay": {
            "value": "150 us at physiological temperature",
            "source": "Sabatini & Regehr, Nature 384(6605):170-172, 1996, "
                      "doi:10.1038/384170a0"},
        "swc_format": {
            "value": "seven columns; type 1 soma, 2 axon, 3 basal dendrite, 4 apical dendrite",
            "source": "Cannon, Turner, Pyapali & Wheal, J Neurosci Methods 84(1-2):49-54, 1998, "
                      "doi:10.1016/S0165-0270(98)00091-0"},
        "projection_cells_paper": {
            "value": "the paper behind the projection cells in the complete set contains no "
                     "occurrence of 'shrink', 'shrinkage', 'correction' or 'corrected'; it "
                     "states 'we cannot exclude that some axons might have been incompletely "
                     "traced, and it is likely that some axons were incompletely labeled' and "
                     "'in most cases we lost the axon within the callosal fiber tract'",
            "source": "Yamashita et al., Front Neuroanat 12:33, 2018, "
                      "doi:10.3389/fnana.2018.00033 (full text searched 2026-09-06)"},
        "drawn_cell_paper": {
            "value": "x1.1 in x-y, x2.1 in z, stated in the paper the drawn cell was "
                     "published with",
            "source": "Emmenegger, Qi, Wang & Feldmeyer, Cereb Cortex 28(4):1439-1457, 2018, "
                      "doi:10.1093/cercor/bhx352"},
        "cng_standardisation": {
            "value": "the CNG version of a file has its soma moved to the origin and its axes "
                     "rotated onto the principal components of the coordinates, so its "
                     "orientation is the archive's, not the tissue's",
            "source": "NeuroMorpho.Org, 'CNG version' file documentation; checked on the "
                      "Ascoli archive, whose depositor's file and CNG file agree on every "
                      "metric swclib computes"},
    }


def assumed():
    return [
        {"key": "segment_diameter",
         "text": "a segment's diameter is taken as twice the radius recorded at its far end, "
                 "not the mean of its two ends, so that a segment hanging off the soma is not "
                 "credited with the soma's radius"},
        {"key": "measured_diameter",
         "text": "a reconstruction's radius column counts as measured only if it holds at "
                 "least %d distinct values and no single value covers more than %d%% of the "
                 "drawn length" % (swclib.MIN_DISTINCT_DIAM, int(100 * swclib.MAX_MODAL_SHARE))},
        {"key": "z_trustworthy",
         "text": "only whole-brain, in vivo reconstructions are treated as having a drawable "
                 "z axis; every slice preparation is assumed uncorrected"},
        {"key": "gradient_rule",
         "text": "a gradient counts as surviving only if the median within-archive rank "
                 "correlation exceeds %.2f and at least %d%% of qualifying archives exceed it; "
                 "an archive qualifies with at least %d cells and a %.0f-fold spread in reach"
                 % (GRADIENT_RHO, int(100 * GRADIENT_SHARE), GRADIENT_MIN_CELLS,
                    GRADIENT_MIN_SPREAD)},
        {"key": "thinnest",
         "text": "the thinnest structure a true-proportion drawing must render is taken as a "
                 "%.2f um axon shaft, an electron-microscopy value, because light microscopy "
                 "cannot resolve it" % THINNEST["value_um"]},
        {"key": "exemplars",
         "text": "the two reconstructions drawn side by side are each the cell closest to its "
                 "group's median reach and axon length, chosen by rule rather than by eye"},
        {"key": "units",
         "text": "SWC has no unit field, so an archive is taken as micrometres only if the "
                 "median soma of its measured-diameter cells falls between %.0f and %.0f um, "
                 "or, where its radii are placeholders, if no arbor reaches beyond %.0f um; "
                 "archives failing that are counted and named but not measured from"
                 % (UNIT_SOMA_MIN, UNIT_SOMA_MAX, UNIT_REACH_MAX)},
        {"key": "sample",
         "text": "the cross-archive sample is drawn from the first page of each archive's "
                 "records with a fixed seed, not uniformly at random across the whole archive"},
        {"key": "drawn_cell",
         "text": "the cell drawn from the complete set is chosen by rule: the largest "
                 "single-paper group in the set, less any file failing the width rule when "
                 "opened, and then the cell closest to that group's median reach and axon "
                 "length"},
        {"key": "windows",
         "text": "the three windows it is drawn in are the whole cell padded %d%% per side, "
                 "%d%% of that window centred on the soma, and %.1f soma diameters centred on "
                 "the soma; 'under one pixel' means at the %d CSS pixels the page displays "
                 "the figure at" % (int(100 * WINDOW_PAD), int(100 * WINDOW_B),
                                    WINDOW_C_SOMA, DISPLAY_PX)},
        {"key": "hairline",
         "text": "where a recorded width is thinner than a pixel the shape is carried by a "
                 "%.1f-point hairline in a fainter tint; the width itself is still drawn at "
                 "its true size on top, and vanishes" % HAIRLINE_PT},
    ]


def build():
    rows = read_census()
    mets = read_metrics()
    with open(os.path.join(DATA, "manifest.json"), encoding="utf-8") as fh:
        man = json.load(fh)

    casc, keep = cascade(rows)
    units, trusted = unit_check(mets)
    # Everything measured from files is measured on the archives whose units
    # can be confirmed. The rest are counted and named, not silently dropped.
    um = [m for m in mets if m["archive"] in trusted]
    comp = read_complete()
    if len(comp) != casc["n_complete"]:
        raise SystemExit("complete_metrics.csv holds %d files but the cascade leaves %d; "
                         "run fetch_data.py --complete-only" % (len(comp), casc["n_complete"]))
    the_complete = describe_104(keep)
    the_complete["opened"] = opened(comp)
    pair = pair_block(man, mets)
    payload = {
        "generated_from": "NeuroMorpho.Org v8.x (CC BY 4.0) and the Allen Cell Types Database",
        "retrieved": man["retrieved"],
        "manifest_sha256": man["sha256"],
        "seed": man["seed"],
        "cascade": casc,
        "the_complete": the_complete,
        "tradeoff_metadata": tradeoff(rows),
        "tradeoff_files": method_split(um),
        "gradient": gradient_test(um),
        "scatter": scatter(um),
        "pair": pair,
        "pair_geometry": pair_geometry(pair),
        "drawn": drawn_block(man),
        "layout": {"display_px": DISPLAY_PX, "strip_px": STRIP_PX, "hairline_pt": HAIRLINE_PT,
                   "ladder_css": LADDER_CSS, "pair_css": PAIR_CSS},
        "ladder": None,
        "units": {"per_archive": units,
                  "n_archives": len(units),
                  "n_micrometres": len(trusted),
                  "n_rejected": len(units) - len(trusted),
                  "rejected": [u["archive"] for u in units if not u["micrometres"]],
                  "n_cells_kept": len(um), "n_cells_dropped": len(mets) - len(um),
                  "rule": {"soma_min_um": UNIT_SOMA_MIN, "soma_max_um": UNIT_SOMA_MAX,
                           "reach_max_um": UNIT_REACH_MAX}},
        "sample": {"n": len(mets), "archives": sorted({m["archive"] for m in mets}),
                   "per_archive": man["per_archive"]},
        "looked_up": looked_up(),
        "assumed": assumed(),
    }
    payload["ladder"] = ladder(um, payload["pair"])
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "neuron_payload.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
    return payload


def report(p):
    c = p["cascade"]
    print("  census                     %s reconstructions" % f'{c["n_total"]:,}')
    for s in c["steps"]:
        print("    + %-38s %8s" % (s["label"], f'{s["n"]:,}'))
    t = p["tradeoff_metadata"]
    print("  axon complete              %s, of which %s measure diameter (%.1f%%)"
          % (f'{t["axon_complete"]:,}', f'{t["and_measured_diameter"]:,}', 100 * t["share"]))
    k = p["the_complete"]
    print("  the complete set           %d cells, %d labs, human present: %s"
          % (k["n"], k["n_labs"], k["has_human"]))
    print("                             %d of them carry %s" % (k["top_doi_n"], k["top_doi"]))
    o = k["opened"]
    print("  ... opened                 %d pass the width rule, %d fail (%s); %d hold one width"
          % (o["n_pass_width"], o["n_fail_width"],
             ", ".join("%s %d" % (f["archive"], f["n"]) for f in o["fails_by_archive"]),
             o["n_single_width"]))
    pj = o["projection"]
    print("                             %d projection cells (%s), reach %s-%s um, axon %s-%s um, %s-%s widths"
          % (pj["n"], ", ".join(pj["archives"]), f'{pj["reach_min_um"]:,.0f}',
             f'{pj["reach_max_um"]:,.0f}', f'{pj["axon_min_um"]:,.0f}', f'{pj["axon_max_um"]:,.0f}',
             pj["distinct_min"], pj["distinct_max"]))
    d = p["drawn"]
    if d:
        print("  drawn                      %s (%s), reach %s um, axon %s um, %d widths; "
              "axon %d widths at %.0f%% one value"
              % (d["neuron"], d["archive"], f'{d["reach_um"]:,.0f}', f'{d["axon_um"]:,.0f}',
                 d["n_distinct_diam"], d["axon"]["n_distinct_diam"], 100 * d["axon"]["frac_len_modal"]))
        for key in ("A", "B", "C"):
            w = d["windows"][key]
            print("    %s  window %8.1f um  %.3f um/px  under a pixel: %3.0f%% of length, axon %3.0f%%, "
                  "dendrite %3.0f%%  soma %6.1f px  EM %.2f px"
                  % (key, w["window_um"][0], w["um_per_px"], 100 * w["share_under_one_px"],
                     100 * w["axon_under_one_px"], 100 * w["dendrite_under_one_px"],
                     w["soma_px"], w["thinnest_em_px"]))
    g2 = p["pair_geometry"]
    if g2:
        print("  pair at one scale          %.1fx in extent; the slice cell is %.0f px wide, soma %.1f px"
              % (g2["extent_ratio"], g2["allen_px_in_shared"], g2["allen_soma_px_in_shared"]))
    oc = c["order_costs"]
    print("  order dependence           over %d orders: most %s, least %s"
          % (oc["n_orders"], oc["most_order_dependent"], oc["least_order_dependent"]))
    for o in oc["constraints"]:
        print("    %-38s first %5.1f%%  last %5.1f%%  min %5.1f%%  max %5.1f%%"
              % (o["label"], 100 * o["first"], 100 * o["last"], 100 * o["min"], 100 * o["max"]))
    u = p["units"]
    print("  units                      %d of %d archives confirmed micrometres; %d rejected%s"
          % (u["n_micrometres"], u["n_archives"], u["n_rejected"],
             (" (" + ", ".join(u["rejected"]) + ")") if u["rejected"] else ""))
    for r in u["per_archive"]:
        if not r["micrometres"]:
            print("      %-16s %s" % (r["archive"], r["why"]))
    print("  cells used                 %s of %s" % (f'{u["n_cells_kept"]:,}',
                                                     f'{u["n_cells_kept"] + u["n_cells_dropped"]:,}'))
    g = p["gradient"]
    print("  gradient                   %s" % g["verdict"])
    print("                             pooled rho %s; median within-archive rho %s over %d "
          "qualifying archives" % (g["pooled_rho"], g["median_within_rho"],
                                   g["n_qualifying_archives"]))
    l = p["ladder"]
    print("  true proportions           %s um across, thinnest %.2f um -> 1:%s, %.2f orders"
          % (f'{l["extent_um"]:,.0f}', l["thinnest_um"], f'{l["dynamic_range"]:,}', l["orders"]))
    for src, d in p["pair"].items():
        print("  exemplar %-11s       %-20s axon %9s um, diameter %s"
              % (src, d["neuron"][:20], f'{d["axon_um"]:,.0f}',
                 "measured" if d["diam_measured"] else "one placeholder value"))


def main():
    argparse.ArgumentParser().parse_args()
    p = build()
    report(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
