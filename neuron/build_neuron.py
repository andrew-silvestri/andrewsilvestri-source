"""How much of a drawn neuron was measured.

Reads  data/neurons.csv.gz    the census of NeuroMorpho.Org (fetch_data.py)
       data/swc_metrics.csv   morphometrics from files, computed by swclib
       data/manifest.json     what was fetched, when, and its hashes
Writes outputs/neuron_payload.json
       neuron-app.html        with --build

Everything the page states is computed here.  Nothing is typed into the
template except prose; every number arrives through a placeholder.

Run:  python3 build_neuron.py
      python3 build_neuron.py --build
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


def read_census():
    with gzip.open(os.path.join(DATA, "neurons.csv.gz"), "rt", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_metrics():
    with open(os.path.join(DATA, "swc_metrics.csv"), encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for k, v in list(r.items()):
            if v in ("", "None"):
                r[k] = None
            elif k in ("whole_brain", "diam_measured"):
                r[k] = v in ("True", "true", "1")
            elif k not in ("archive", "neuron_name", "species", "source", "file",
                           "nmo_attributes", "nmo_domain", "dendrite_type", "structure"):
                try:
                    r[k] = float(v)
                except (TypeError, ValueError):
                    pass
    return rows


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
            "n_complete": full}, keep


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
    payload = {
        "generated_from": "NeuroMorpho.Org v8.x (CC BY 4.0) and the Allen Cell Types Database",
        "retrieved": man["retrieved"],
        "manifest_sha256": man["sha256"],
        "seed": man["seed"],
        "cascade": casc,
        "the_complete": describe_104(keep),
        "tradeoff_metadata": tradeoff(rows),
        "tradeoff_files": method_split(um),
        "gradient": gradient_test(um),
        "scatter": scatter(um),
        "pair": pair_block(man, mets),
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="also write neuron-app.html")
    a = ap.parse_args()
    p = build()
    report(p)
    if a.build:
        import build_app
        build_app.write(p, HERE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
