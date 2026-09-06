"""Reading SWC reconstructions, and the one rule this project cannot break.

A reconstruction is a measurement with known systematic errors, and two of
them decide what may be drawn:

  z.  A slice reconstruction is shipped with an uncorrected z axis.  Fixed,
      sectioned, mounted tissue loses roughly half its thickness (Gardella
      et al., J Neurosci Methods 124(1):45-59, 2003, measured vibratome
      sections at 39.7% of nominal; Mohan et al., Cereb Cortex
      25(12):4839-4853, 2015, measured 63 +/- 10% z shrinkage in the 350 um
      slices this project's Allen files come from).  The Allen Cell Types
      technical white paper documents no correction, and Gouwens et al.,
      Nat Neurosci 22(7):1182-1195, 2019, handled the compression by
      *excluding* z-derived features from their classification rather than
      by fixing coordinates; the correction exists only downstream, per cell,
      in Lee et al., eLife 10:e65482, 2021.  So a slice file has a z column
      and no z this site may draw.

      load_xy() is therefore the only loader the figures use, and it returns
      two columns.  Reaching for z is a TypeError rather than a plausible
      wrong picture.  load_xyz() exists for the whole-brain, in vivo
      reconstructions that never went through a microtome, and refuses
      everything else by name.

  diameter.  70.1% of the archive records no varying radius at all, and the
      whole-brain files that do carry one carry a placeholder: every
      MouseLight source file sampled holds a single radius, 1.0, on every
      point.  measured_diameter() is the test a cell must pass before a
      figure is allowed to vary its line width.

Segment geometry, stated once because every number on the page rests on it:
a segment runs from a point to its parent; its length is the Euclidean
distance between them in 3D (z is untrustworthy for *drawing* but is the
depositor's own measure of path length, and dropping it would understate
every length); its diameter is twice the child point's radius, not the mean
of the two, so that a segment hanging off the soma is not credited with the
soma's radius.

Run:  python3 swclib.py    # self-check against tests/fixture.swc
"""
import os
import numpy as np

# Whole-brain, in vivo reconstructions: no slice, no microtome, no shrinkage
# correction to be missing.  Everything absent from this set is assumed to be
# slice-derived and has no drawable z.  Adding a name here is a claim about
# how the tissue was prepared; make it with a citation.
Z_TRUSTWORTHY = {"mouselight", "peng"}

# ~lateral resolution of visible light through a high-NA objective.  Huang,
# Bates & Zhuang, Annu Rev Biochem 78:993-1016, 2009: 200-300 nm laterally,
# 500-700 nm axially.  Used only to report how much of a drawn arbor is
# thinner than the microscope that measured it could resolve.
DIFFRACTION_UM = 0.25

# A radius column is a measurement only if it varies.  NeuroMorpho's own flag
# uses "not constant"; that passes a file with three values, so this project
# uses both a count and a length-weighted share (see measured_diameter).
MIN_DISTINCT_DIAM = 4
MAX_MODAL_SHARE = 0.90

SOMA, AXON, BASAL, APICAL = 1, 2, 3, 4
TYPE_NAME = {AXON: "axon", BASAL: "basal", APICAL: "apical"}


class ZProvenanceError(RuntimeError):
    """Raised when z is asked for from a reconstruction that has no usable z."""


def read_swc(path):
    """Parse an SWC file into (idx, typ, xyz, rad, par).

    Tolerant in the ways deposited files actually vary: comments, blank
    lines, short rows, float-formatted integer ids, ids that are neither
    contiguous nor sorted, and more than one root.  Not tolerant of a file
    with no parseable rows.
    """
    idx, typ, xyz, rad, par = [], [], [], [], []
    with open(path, "r", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line or line[0] == "#":
                continue
            f = line.split()
            if len(f) < 7:
                continue
            try:
                i = int(float(f[0]))
                t = int(float(f[1]))
                x, y, z = float(f[2]), float(f[3]), float(f[4])
                r = float(f[5])
                p = int(float(f[6]))
            except ValueError:
                continue
            idx.append(i); typ.append(t); xyz.append((x, y, z)); rad.append(r); par.append(p)
    if not idx:
        raise ValueError("no parseable SWC rows in %s" % path)
    return (np.asarray(idx), np.asarray(typ), np.asarray(xyz, dtype=float),
            np.asarray(rad, dtype=float), np.asarray(par))


def load_xy(path):
    """The (N, 2) point array the figures draw from.

    Two columns, deliberately.  Every figure on this page is a projection or
    a chart; none may imply a depth this data does not support.
    """
    _, _, xyz, _, _ = read_swc(path)
    return xyz[:, :2].copy()


def source_of(path):
    """The archive a file came from, taken from the directory that holds it.

    Files live at data/swc/<source>/<name>.swc.  The provenance is the
    location, never an argument: an earlier version of load_xyz() took the
    source as a string and would happily have drawn an Allen file's z if the
    caller typed "mouselight".  A label a caller supplies is a claim; a
    directory is a fact about where the bytes came from.
    """
    return os.path.basename(os.path.dirname(os.path.abspath(path))).strip().lower()


def load_xyz(path):
    """The (N, 3) array, for whole-brain reconstructions only.

    The source is read from the path (see source_of).  Anything outside
    Z_TRUSTWORTHY raises rather than returning a z that is compressed by
    roughly a factor of two.
    """
    src = source_of(path)
    if src not in Z_TRUSTWORTHY:
        raise ZProvenanceError(
            "%r is not a whole-brain source, so its z axis is uncorrected slice "
            "geometry (~2x compressed) and must not be drawn; use load_xy(). "
            "Trustworthy sources: %s" % (src, ", ".join(sorted(Z_TRUSTWORTHY))))
    _, _, xyz, _, _ = read_swc(path)
    return xyz.copy()


def segments(idx, typ, xyz, rad, par):
    """(length, type, diameter) per segment, plus the child count per point.

    A segment is a point joined to its parent.  Orphans - a parent id absent
    from the file, or a root - contribute no segment.  Diameter is twice the
    child's radius (see the module docstring).
    """
    pos = {int(i): k for k, i in enumerate(idx)}
    n = len(idx)
    nchild = np.zeros(n, dtype=int)
    lens, types, diams = [], [], []
    for k in range(n):
        p = int(par[k])
        if p == -1 or p not in pos:
            continue
        j = pos[p]
        nchild[j] += 1
        lens.append(float(np.linalg.norm(xyz[k] - xyz[j])))
        types.append(int(typ[k]))
        diams.append(2.0 * float(rad[k]))
    return (np.asarray(lens, dtype=float), np.asarray(types, dtype=int),
            np.asarray(diams, dtype=float), nchild)


def measured_diameter(n_distinct, modal_share):
    """Is this file's radius column a measurement or a placeholder?

    Both tests must pass.  The count alone passes a MouseLight CNG file,
    which holds exactly two values; the share alone passes a file with many
    values clustered on one.
    """
    return bool(n_distinct >= MIN_DISTINCT_DIAM and modal_share <= MAX_MODAL_SHARE)


def metrics(path, source=None):
    """Everything this project measures from one reconstruction.

    Lengths in um.  `source` is recorded, not used: nothing here needs z
    provenance because nothing here is drawn.
    """
    idx, typ, xyz, rad, par = read_swc(path)
    seg_len, seg_typ, seg_diam, nchild = segments(idx, typ, xyz, rad, par)
    m = {"file": os.path.basename(path), "source": source, "points": int(len(idx))}

    som = rad[typ == SOMA]
    m["soma_diam_um"] = round(2.0 * float(som.mean()), 4) if len(som) else None
    m["soma_points"] = int((typ == SOMA).sum())

    for t, name in TYPE_NAME.items():
        sel = seg_typ == t
        m["len_%s_um" % name] = round(float(seg_len[sel].sum()), 4)
        pts = np.where(typ == t)[0]
        m["bp_%s" % name] = int(sum(1 for k in pts if nchild[k] > 1))
        m["tip_%s" % name] = int(sum(1 for k in pts if nchild[k] == 0))
    m["len_dend_um"] = round(m["len_basal_um"] + m["len_apical_um"], 4)
    # Neurite length only.  A CNG file writes the soma as three points, which
    # contribute two short segments; L-Measure's `length` excludes them, and
    # including them put this 2 um above the archive's own figure for every
    # cell checked.  Matching the convention is what makes the two numbers
    # comparable at all - see check 7 in test_neuron.py.
    m["len_total_um"] = round(float(seg_len[seg_typ != SOMA].sum()), 4)
    m["axon_dend_ratio"] = (round(m["len_axon_um"] / m["len_dend_um"], 6)
                            if m["len_dend_um"] > 0 else None)

    neurite = typ != SOMA
    if neurite.any():
        span = xyz[neurite].max(axis=0) - xyz[neurite].min(axis=0)
        m["extent_x_um"], m["extent_y_um"], m["extent_z_um"] = [round(float(v), 4) for v in span]
        m["max_extent_um"] = round(float(span.max()), 4)
        centre = xyz[typ == SOMA].mean(axis=0) if (typ == SOMA).any() else xyz[0]
        m["max_radial_um"] = round(float(np.linalg.norm(xyz[neurite] - centre, axis=1).max()), 4)
    else:
        for k in ("extent_x_um", "extent_y_um", "extent_z_um", "max_extent_um", "max_radial_um"):
            m[k] = None

    nd, nl = seg_diam[seg_typ != SOMA], seg_len[seg_typ != SOMA]
    if len(nd) and nl.sum() > 0:
        pos_d = nd[nd > 0]
        m["diam_min_um"] = round(float(pos_d.min()), 6) if len(pos_d) else 0.0
        m["diam_med_um"] = round(float(np.median(nd)), 6)
        m["diam_max_um"] = round(float(nd.max()), 6)
        vals, inv = np.unique(np.round(nd, 6), return_inverse=True)
        wl = np.bincount(inv, weights=nl)
        m["n_distinct_diam"] = int(len(vals))
        m["modal_diam_um"] = round(float(vals[int(wl.argmax())]), 6)
        m["frac_len_modal_diam"] = round(float(wl.max() / nl.sum()), 6)
        m["frac_len_subres"] = round(float(nl[nd < DIFFRACTION_UM].sum() / nl.sum()), 6)
        m["diam_measured"] = measured_diameter(m["n_distinct_diam"], m["frac_len_modal_diam"])
        m["dynamic_range"] = (int(round(m["max_extent_um"] / m["diam_min_um"]))
                              if m.get("max_extent_um") and m["diam_min_um"] > 0 else None)
    else:
        for k in ("diam_min_um", "diam_med_um", "diam_max_um", "n_distinct_diam",
                  "modal_diam_um", "frac_len_modal_diam", "frac_len_subres", "dynamic_range"):
            m[k] = None
        m["diam_measured"] = False
    return m


FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "fixture.swc")


def _self_check():
    """The parser against hand-computed geometry, not against a published mean.

    A summary statistic is a loose target: a parser that mis-sums segments,
    double-counts the soma or drops a root can still land near a published
    average and look confirmed.  tests/fixture.swc is small enough that every
    quantity below was worked out by hand, so this pins the arithmetic
    itself.  test_neuron.py runs the same assertions.
    """
    m = metrics(FIXTURE, source="fixture")
    want = {
        "points": 7, "soma_points": 1, "soma_diam_um": 10.0,
        "len_basal_um": 23.0, "len_axon_um": 20.0, "len_apical_um": 0.0,
        "len_dend_um": 23.0, "len_total_um": 43.0,
        "bp_basal": 1, "tip_basal": 2, "bp_axon": 0, "tip_axon": 1,
        "max_radial_um": 20.0, "max_extent_um": 32.0,
        "extent_x_um": 6.0, "extent_y_um": 4.0, "extent_z_um": 32.0,
        "n_distinct_diam": 3, "diam_min_um": 0.5, "diam_max_um": 2.0,
        "diam_med_um": 1.0, "modal_diam_um": 0.5,
        "frac_len_subres": 0.0, "dynamic_range": 64, "diam_measured": False,
    }
    bad = []
    for k, v in sorted(want.items()):
        got = m.get(k)
        if isinstance(v, float):
            ok = got is not None and abs(got - v) < 1e-9
        else:
            ok = got == v
        if not ok:
            bad.append("  %-22s want %-8s got %s" % (k, v, got))
    for k, v in (("axon_dend_ratio", 20.0 / 23.0), ("frac_len_modal_diam", 20.0 / 43.0)):
        if m.get(k) is None or abs(m[k] - v) > 1e-5:
            bad.append("  %-22s want %-8.6f got %s" % (k, v, m.get(k)))
    if bad:
        print("swclib self-check FAILED:")
        print("\n".join(bad))
        return 1
    print("swclib self-check: %d hand-computed quantities agree" % (len(want) + 2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_self_check())
