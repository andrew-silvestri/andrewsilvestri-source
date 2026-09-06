"""
The failure modes this project is exposed to.

The signature one is first, and it is specific to what this page argues. The
page's whole claim is about dispersion - how far apart the published numbers
are, and how much wider the individual ranges are than the means. So the
characteristic way for this project to lie is to draw an interval nobody
published. Two thirds of these papers report a mean and nothing else; a figure
that quietly gave those rows a whisker would look better, read as more
rigorous, and be false.

1. An interval is drawn where none was published. Checked against the
   LineCollections actually on the axes, not against the intention: a row whose
   paper published no dispersion must have no horizontal extent drawn at its y.
   Testing the pixel rather than the plan is the only version of this check
   that catches the bug it exists for.
2. A standard deviation is presented as a confidence interval. They are
   different quantities. No row may carry both, neither may be derived from the
   other, and only Hoogkamer 2016 published a real CI.
3. A sign flips. An advanced-footwear row is a shoe helping and must be
   positive; an added-mass row is mass added and must be negative. HANDOFF §8
   item 12 - the 11.65 kg shoe - was an operation on a signed field whose
   meaning nobody had pinned down.
4. A row loses its provenance. Every row names a study that exists, and every
   study carries a source and a DOI.
5. The transfer coefficient is applied without its label. Every number derived
   through it must be marked assumed in the payload and on the page.
6. The two registers of figure 2 disagree about a study's colour. Both read one
   map in data/studies.py; if a figure ever grows its own, the colours drift
   apart and the reader is told two studies are one.
7. This page and site/economy.html disagree about the transfer
   coefficient. Both derive it from the same two published rows; economy.html
   owns the explanation and this page spends the number. If either revises it,
   this fails loudly instead of the two pages quietly stating different
   exchange rates.
8. The page and the payload disagree. Rendering the template from the payload
   must reproduce the shipped page byte for byte.

Run:  python3 test_shoes.py
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
from matplotlib.collections import LineCollection            # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import sitefig                                               # noqa: E402
import fig_shoes                                             # noqa: E402
import update_page                                           # noqa: E402
from data.studies import ROWS, STUDIES                       # noqa: E402

PAYLOAD = os.path.join(HERE, "outputs", "shoes_payload.json")
PAGE = os.path.join(ROOT, "site", "shoes.html")
DOI = ("10.", "https://doi.org/10.")


def captured(builder, P):
    """Run a figure builder and hand back the Figure instead of a file."""
    held = {}

    def spy(fig, name):
        held["fig"] = fig
        held["name"] = name
        return 0

    real, fig_shoes.emit = fig_shoes.emit, spy
    try:
        builder(P)
    finally:
        fig_shoes.emit = real
    return held["fig"]


def drawn_extents(ax):
    """Every horizontal line segment actually on the axes, as y -> width.

    hlines() makes a LineCollection; scatter() makes a PathCollection; the
    gridlines and the zero rule are Line2D on ax.lines and are not collections
    at all. So the LineCollections are exactly the intervals this figure drew.
    """
    out = {}
    for c in ax.collections:
        if not isinstance(c, LineCollection):
            continue
        for seg in c.get_segments():
            (x0, y0), (x1, y1) = seg[0], seg[-1]
            if abs(y1 - y0) > 1e-6:          # a vertical cap, not an interval
                continue
            y = round(float(y0), 3)
            out[y] = max(out.get(y, 0.0), abs(float(x1) - float(x0)))
    return out


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    fails = []
    sitefig.style()

    # 1. no interval is drawn that no paper published -----------------------
    fig = captured(fig_shoes.fig_measurements, P)
    ax = fig.axes[0]
    extents = drawn_extents(ax)
    for i, r in enumerate(P["aft"]):
        w = extents.get(float(i), 0.0)
        if r["dispersion"] == "none" and w > 1e-6:
            fails.append(f"1. {r['key']}: published no dispersion but a "
                         f"{w:.3f}-wide interval is drawn at row {i}")
        if r["dispersion"] == "sd":
            want = 2 * r["sd_pct"]
            if abs(w - want) > 1e-6:
                fails.append(f"1. {r['key']}: SD is {r['sd_pct']}, so the bar "
                             f"should be {want:.3f} wide; {w:.3f} is drawn")
    n_drawn = sum(1 for v in extents.values() if v > 1e-6)
    if n_drawn != P["spread"]["n_with_sd"]:
        fails.append(f"1. {n_drawn} intervals drawn in figure 1, but "
                     f"{P['spread']['n_with_sd']} comparisons published one")
    plt.close(fig)

    # 2. an SD is never a CI -------------------------------------------------
    for k, r in ROWS.items():
        if r.get("sd_pct") is not None and r.get("ci_pct") is not None:
            fails.append(f"2. {k}: carries both an SD and a CI")
    real_ci = {k for k, r in ROWS.items() if r.get("ci_pct") is not None}
    expect_ci = {"hoogkamer2016_mass_metabolic", "hoogkamer2016_mass_time",
                 "guinness2020_men", "guinness2020_women"}
    if real_ci != expect_ci:
        fails.append(f"2. rows carrying a CI changed: {sorted(real_ci)}")

    # 3. the sign convention -------------------------------------------------
    for k, r in ROWS.items():
        e = r.get("effect_pct")
        if e is None:
            continue
        if r["family"] == "aft" and e <= 0:
            fails.append(f"3. {k}: an aft row must be positive, is {e}")
        if r["family"] == "mass" and e >= 0:
            fails.append(f"3. {k}: a mass row must be negative, is {e}")

    # 4. provenance ----------------------------------------------------------
    for k, r in ROWS.items():
        st = STUDIES.get(r["study"])
        if st is None:
            fails.append(f"4. {k}: names study {r['study']!r}, which does not exist")
            continue
        if not st.get("source", "").strip():
            fails.append(f"4. {r['study']}: no source")
        if not str(st.get("doi", "")).startswith(DOI):
            fails.append(f"4. {r['study']}: doi {st.get('doi')!r} is not a DOI")

    # 5. the one assumption is labelled --------------------------------------
    if not P["predicted"].get("assumed"):
        fails.append("5. the predicted time range is not marked assumed")
    page = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else ""
    lo = f"{P['predicted']['lo']:.1f}%"
    hi = f"{P['predicted']['hi']:.1f}%"
    if lo not in page or hi not in page:
        fails.append(f"5. the page does not carry the predicted range {lo}-{hi}")
    if "<em>assumed</em>" not in page:
        fails.append("5. the page never marks anything assumed")

    # 6. one colour map, read by both registers ------------------------------
    for a in P["aft"]:
        if a["colour"] != STUDIES[a["study"]]["colour"]:
            fails.append(f"6. {a['key']}: figure-1 colour disagrees with STUDIES")
    for r in P["individual"]["rows"]:
        if r["colour"] != STUDIES[r["study"]]["colour"]:
            fails.append(f"6. {r['key']}: figure-2 colour disagrees with STUDIES")
    unknown = ({a["colour"] for a in P["aft"]}
               | {r["colour"] for r in P["individual"]["rows"]}) - set(fig_shoes.COLOURS)
    if unknown:
        fails.append(f"6. colours with no entry in fig_shoes.COLOURS: {unknown}")

    # 7. the sibling page agrees about the transfer coefficient ---------------
    sib = os.path.join(ROOT, "economy", "outputs", "economy_payload.json")
    if os.path.exists(sib):
        theirs = json.load(open(sib, encoding="utf-8"))["transfer"]["measured"]
        if abs(theirs["value"] - P["transfer"]["value"]) > 1e-9:
            fails.append(f"7. economy.html has transfer {theirs['value']!r}, "
                         f"this project has {P['transfer']['value']!r}")
        for end in ("lo", "hi"):
            if abs(theirs[end] - P["transfer"][end]) > 1e-9:
                fails.append(f"7. economy.html has transfer {end} "
                             f"{theirs[end]!r}, this project has "
                             f"{P['transfer'][end]!r}")
    else:
        print("  7. economy/outputs/economy_payload.json absent; "
              "cross-project check skipped")

    # 8. the page is the payload ---------------------------------------------
    if not page:
        fails.append("8. site/shoes.html does not exist")
    else:
        rendered, probs = update_page.cite(update_page.render(P), P)
        for p in probs:
            fails.append(f"8. citations: {p}")
        if rendered != page:
            fails.append("8. re-rendering the template from the payload does "
                         "not reproduce site/shoes.html")

    for f in fails:
        print("  " + f)
    print(f"  {len(fails)} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
