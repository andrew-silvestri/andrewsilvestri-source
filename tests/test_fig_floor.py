"""THE FLOOR, AT THE WIDTH THE PAGE SERVES THE FIGURE AT.

    No text in a figure renders below 12px at any width the page serves it at.

12px is --fs-2, the smallest step of the site's own type scale, and it is the
promise the site already keeps at 1440 on all 28 figures. A floor that holds at
one width and not another is not a floor.

WHY THIS FILE EXISTS AND fig_floor.py IS NOT ENOUGH. fig_floor.py computes
`pt * display / (72 * width_in)` where `display` is the figure's OWN authored
width, so it asks whether a figure would be legible if it were shown at the
size it was drawn for. Every one of the 28 figures passes that. At 390 the
page serves a 714px figure into a 350px column, and twenty of them render
their smallest text at 5.9px and seven at 7.1px. The gate was green because it
asked about the wrong width - HANDOFF section 8, trap 31, authored by nobody
on purpose - and the repair is to ask at the served width, not to lower the
number. Nothing here replaces fig_floor.py; that check still runs inside every
builder's audit() and still catches a label too small for its own figure.

HOW THE TWO HALVES ARE OBTAINED, AND WHY NEITHER IS READ FROM A FILE.

  served width  - measured in a real browser by tests/fig_served_widths.js, at
                  1440 and 390, in Chromium and Firefox, because nothing in a
                  figure's source says what width a page gives it (trap 22).
                  Where the engines disagree the SMALLEST width wins, so a
                  disagreement makes this stricter rather than picking a winner.
  smallest text - recomputed by running every builder into a throw-away copy of
                  the tree and reading the point size off the text artists
                  matplotlib actually drew. It is not read from a manifest: a
                  gate that reads a recorded result rather than recomputing it
                  is not a gate (trap 20).

The text enumeration is the continents/beauty shape - fig.texts, titles through
sitefig.titles (never ax.title, trap 21), axis labels, ax.texts, tick labels
inside the view limits, legend texts - and never findobj, which returns ticks
that were never drawn (trap 4).

THE EXEMPTION LIST, AND THE TWO PROPERTIES ANY SUCH GATE NEEDS. Both, not
either: they are a pair, and the second is the one that was missing here and
cost three figures.

Twenty-seven figures failed this when it was written. They are named in
ORIGINAL, one line each, spelled out - never a pattern, because a pattern
silently covers the next figure somebody adds. CONVERTED is what has since been
fixed, and EXEMPT is the remainder: the work queue.

  PROPERTY 1 - THE NUMERATOR ONLY SHRINKS. The exempt set can lose names and
  cannot gain them. ORIGINAL is frozen and EXEMPT must be a subset of it, so a
  conversion takes a name out and nothing puts one in without editing a
  constant somebody has to justify. A listed figure that now PASSES also fails
  the run, because the list is then stale and the count is a lie in the
  flattering direction. An unlisted figure that FAILS fails the run; that is
  the gate itself.

  PROPERTY 2 - THE DENOMINATOR CANNOT SILENTLY CONTRACT. Every figure the pages
  actually serve must be measured, or a shrinking numerator means nothing. This
  is the half that failed. min_points() keys a builder's output name through
  ASSET_OF; a name with no entry made `asset not in served` true and the row
  was dropped with NO MESSAGE. A2.1 added three narrow renders to the site and
  this gate reported the same 29 figures measured as before they existed -
  correct arithmetic over a set three smaller than the one it claimed. So any
  PNG the pages serve that no builder row accounts for is now a problem.

WHY THE PAIR IS WRITTEN OUT RATHER THAN JUST FIXED. This is the third gate in
this project to be wrong about its denominator rather than its verdict, and all
three were arithmetically correct on whatever they did examine:

  - tests/test_contrast.js's predecessor resolved backgrounds through CSS and
    so never looked at text over a fill (trap 31);
  - heat/figstyle.py's audit() returned before it ran and so never looked at
    five figures, while every "0 layout problems" ever recorded for them came
    from a check that never executed;
  - this file skipped any name without an ASSET_OF entry.

THE FAMILY, AND IT IS THE SAME FAILURE AT THREE LAYERS. Three instruments
in this project have been green over a red tree, each wrong somewhere else,
and none of the three visible from inside itself:

  wrong about the SET it examines    the denominator pattern, five instances,
                                     written out in tests/test_fig_floor.py
  wrong about the RULE it enforces   trap 37, the paraphrase
  wrong about the STATE it examines  trap 38, the wrong frame

AN INSTRUMENT IS ONLY AS GOOD AS ITS AGREEMENT WITH WHAT SHIPS. Evaluate the
artefact in the state it will be saved in - same set, same rule, same
transformations applied. A check that runs on a precursor is checking
something the reader will never see.

The verdict is the easy half to get right. The next exemption-list gate built
here should be built from both properties at once, and a gate that has only
Property 1 should be read as unfinished rather than as strict.

WHAT THIS DOES NOT ASSERT. It measures the point size matplotlib gave a text
artist, scaled by served-over-authored width; it does not rasterise the PNG and
does not know what a reader can actually resolve, so a 12px label in a pale
grey on a busy ground passes here and tests/test_contrast.js is what looks at
that. It sees only text drawn by a builder through matplotlib: text baked into
a raster the builder composites, and any text an app draws into a canvas, are
invisible to it. It covers the ten document pages and not the four viewers. It
says nothing about overlap, off-canvas text or layout at any width - each
builder's own audit() owns that, and at 350 those counts are the Stage A2
workload rather than this gate's business. And it measures at 1440 and 390
only: a width between them that served some third size would not be seen.

    python tests/test_fig_floor.py
    python tests/test_fig_floor.py --break stale    # 0 caught, non-zero blind
    python tests/test_fig_floor.py --break added    # 0 caught, non-zero blind
    python tests/test_fig_floor.py --keep           # leave the work copy
    python tests/test_fig_floor.py --enforce        # D-01 matrix rows gate too
    python tests/test_fig_floor.py --break matrix   # non-zero caught, 0 blind

D-01 RULE 3, AT EVERY CONFIGURATION, REPORTED (Q1, 2026-10-20). D-01 adopted
12px "at every config" (answer 3A) and found this file green on four pages
that are under 12px at 360 and 768-1024, because it measures 1440 and 390
only - the last sentence of the paragraph above, now with numbers. So after
the gate above, the same text sizes are scaled by the widths
tests/fig_served_widths.js --matrix measures at D-01's nine configurations, in
Chromium and WebKit, and every figure-configuration pair under the floor is
printed with its configuration. Exempt figures are counted and marked, not
excused. It REPORTS: it does not change the exit status unless --enforce is
given (Q5 turns that on).

  Fixture first: two synthetic rows (9pt on a 714 figure served at 350 must
  read 4.4px and fail; 12pt on a 350 figure served at 350 must read 12.0 and
  pass), and the matrix must MOVE - some figure must be served at different
  widths in different configurations, or the instrument is pinned (trap 28).
  A fixture failure exits 1 in every mode.

  --break matrix measures the matrix at 1440x900 and 390x844 only, the set
  this file had, and the coverage assertion - all nine configurations, both
  engines - refuses it. It EXITS NON-ZERO WHEN CAUGHT, 0 when blind: the Q1
  convention for a new check, and the opposite of --break stale|added above.

Both --break modes report 0 when the fault they inject is caught and non-zero
when it is not, the way beauty/break_model.py points it. The third break - a
converted figure losing its conversion - is not a flag, because it is an edit
to the tree rather than to this file: remove the <source> from
continents/template.html, rebuild, and continents_fig1_futures.png must fail
here. That has been run; see the commit.
"""
import argparse
import json
import os
import runpy
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FLOOR_PX = 12.0

# Frozen. The twenty-seven figures that rendered below the floor at 390 on
# 2026-09-11, when this check was written. NEVER EDITED - see property 3.
ORIGINAL = (
    "beauty_fig1_gap.png",
    "beauty_fig2_category.png",
    "beauty_fig3_terms.png",
    "beauty_fig4_strata.png",
    "climate_allocation_bases.png",
    "climate_chain_tomato.png",
    "continents_fig2_belts.png",
    "continents_fig3_rigidity.png",
    "continents_fig4_slowdown.png",
    "continents_fig5_past.png",
    "continents_fig6_regimes.png",
    "heat_fig1_breakeven_price.png",
    "heat_fig2_lcoh_stacked.png",
    "heat_fig3_costgap_contour.png",
    "heat_fig4_tornado.png",
    "heat_fig5_emissions_parity.png",
    "lq_allometry.png",
    "lq_explained.png",
    "lq_orders.png",
    "lq_ranked.png",
    "lq_wild_captive.png",
    "skyline_towers.png",
    "storage_fig1_prices.png",
    "storage_fig2_dispatch_week.png",
    "storage_fig3_duration_value.png",
    "storage_fig4_sensitivity.png",
    "storage_fig5_monthly.png",
)

# The work queue. Take a name out when its figure is converted; the run fails
# if you forget, and fails if you put one back.
# Converted and taken off the list. ORIGINAL is frozen; this is the queue.
#   A2.1, 2026-09-12: storage's three, the first conversions. Two were clean at
#   350 with no edit beyond the second render; fig2_dispatch_week needed 5% of
#   margin, which is in storage/model.py beside the call with its numbers.
CONVERTED = {
    "storage_fig2_dispatch_week.png",
    "storage_fig4_sensitivity.png",
    "storage_fig5_monthly.png",
    #   A2.2, 2026-09-12: heat's two. fig2_lcoh_stacked needed only the second
    #   render; fig3_costgap_contour needed its three labels wrapped at 26
    #   characters - two axis labels and the colourbar's, which is an axis label
    #   of its own axes and the easiest of the three to forget.
    "heat_fig2_lcoh_stacked.png",
    "heat_fig3_costgap_contour.png",
    #   A2.3, 2026-09-13: longevity's allometry scatter. Plumbing only - it
    #   comes back at 0 layout problems at 350 with nothing but the second
    #   render. build_lq.py gained an `only` parameter so that render costs
    #   one figure rather than a second pass over eight thousand species.
    "lq_allometry.png",
    #   A2.4, 2026-09-13, grouped by builder. storage: fig1_prices needed the
    #   second render plus its rotated Y label wrapped at 11 columns. The
    #   measured 26 is for HORIZONTAL labels and never breaks an
    #   18-character string, so it changed nothing here; a rotated label
    #   overflows along the figure's short axis and wants its own count.
    "storage_fig1_prices.png",
    #   longevity: lq_ranked, the second render plus its x label wrapped at
    #   the measured 26. lq_orders was SPLIT OUT of the same group - wrapped
    #   at 26 its label is still off canvas on a two-panel 350px figure,
    #   which makes it the third figure wanting a count that is neither 26
    #   nor 11 and fires the trigger recorded beside sitefig.wrap_label.
    "lq_ranked.png",
    #   Stage A resumed, 2026-10-17 (October P1). storage: fig3_duration_value,
    #   the last storage figure. The panels STACK at 350 (side by side they
    #   had ~150px each and 16 audit problems); the in-panel value labels drop
    #   to FS_2, which is the floor, because at FS_1 two of them touched with
    #   the audit clean. And the render found a bug: storage/figstyle.finish
    #   hands the layout engine (l, b, r, t) where it takes (l, b, w, h), so a
    #   footnoted figure runs off the top; the phone render opted into the
    #   correct rect. D-12 (2026-10-20) made it the only rect: the 714 was
    #   re-rendered and model.py's tick-dropping workaround deleted.
    "storage_fig3_duration_value.png",
    #   heat's last three, 2026-10-17 (October P1, one builder per branch).
    #   fig1, fig4 and fig5 are SQUARE at 350 rather than 16:9: at 16:9 their
    #   y labels ran off and fig4's and fig5's legends landed on row labels and
    #   ticks (7 audit problems on the plain render). Legends move below the
    #   axes; axis labels go through sitefig.fit_label; fig1's answer note and
    #   its "fuel only" label sit higher and lower so the curves and the note
    #   do not meet. Same words, same numbers, 714 renders byte-identical.
    "heat_fig1_breakeven_price.png",
    "heat_fig4_tornado.png",
    "heat_fig5_emissions_parity.png",
    #   skyline_towers, 2026-10-18 (October P1). At 350 the bars lie down:
    #   eight upright bars leave ~38px per tower name, and the wrapped names
    #   collided row on row (7 audit problems at 13 columns). One-line names on
    #   the left, the caption on two lines; same towers, heights and words.
    #   The 714 render is byte-identical. build_skyline_figure.py now exits
    #   non-zero on its own audit.
    "skyline_towers.png",
    #   lq_explained, 2026-10-18 (October P1). The three columns stay, because
    #   the page's caption says mass rises left to right. The per-bar labels
    #   become one legend, names and verdicts wrap, the formula breaks after
    #   its "=". audit() now reads legend text (trap 4) and text on a sphere:
    #   the first phone render set "4,000 kg" on the elephant and the audit,
    #   which never looked at patches, said 0. Same numbers and words; the 714
    #   is byte-identical.
    "lq_explained.png",
    #   build_lq.py's last two, 2026-10-18 (October P1, one builder per branch).
    #   lq_wild_captive sizes by rows at 350, as lq_ranked does: at the 714's
    #   PLOT aspect 26 rows got ~7px each and every name sat on the next (26
    #   audit problems). lq_orders keeps its two columns (the caption reads
    #   them left then right) and says its shared x label once, under both:
    #   each ~160px panel's own copy ran off and the two overlapped, which is
    #   what fired the wrap trigger in 1c0ec82. One label fits unwrapped, so
    #   no third wrap count. Same rows and words; both 714s byte-identical.
    "lq_wild_captive.png",
    "lq_orders.png",
    #   climate_allocation_bases, 2026-10-18 (October P1). The 714 layout at
    #   350 gives 53 audit problems: its label column leaves the bars no room
    #   at any aspect tried. At 350 each row's label sits above its bar; the
    #   panel labels and source note break by MEASURED width
    #   (build_allocation_figure._fill), not by a third character count. Same
    #   rows, numbers and words; the 714 is byte-identical.
    "climate_allocation_bases.png",
}
EXEMPT = set(ORIGINAL) - CONVERTED

# Which builder draws which shipped asset. The builders write their own names
# into their own outputs/; this maps those to the names site/assets/ uses,
# because sync_assets.py renames on the way in for three projects.
BUILDERS = [
    ("beauty/fig_beauty.py", "beauty"),
    ("build_allocation_chain.py", "."),
    ("climate-cost/build_allocation_figure.py", "climate-cost"),
    ("continents/fig_continents.py", "continents"),
    ("heat/model.py", "heat"),
    ("storage/model.py", "storage"),
    ("longevity-quotient/build_lq.py", "longevity-quotient"),
    ("longevity-quotient/fig_lq_explained.py", "longevity-quotient"),
    ("build_skyline_figure.py", "."),
    ("meter/fig_meter.py", "meter"),
]

# outputs/ name -> site/assets/ name, where they differ. sync_assets.py's
# PREFIX_SOURCE does the same mapping for the copy; this is the same fact and
# the two must not be allowed to disagree silently, so ASSET_OF is asserted
# against site/assets/ at the end of the run.
ASSET_OF = {
    "fig1_breakeven_price.png": "heat_fig1_breakeven_price.png",
    "fig2_lcoh_stacked.png": "heat_fig2_lcoh_stacked.png",
    "fig3_costgap_contour.png": "heat_fig3_costgap_contour.png",
    "fig4_tornado.png": "heat_fig4_tornado.png",
    "fig5_emissions_parity.png": "heat_fig5_emissions_parity.png",
    "fig1_prices.png": "storage_fig1_prices.png",
    "fig2_dispatch_week.png": "storage_fig2_dispatch_week.png",
    "fig3_duration_value.png": "storage_fig3_duration_value.png",
    "fig4_sensitivity.png": "storage_fig4_sensitivity.png",
    "fig5_monthly.png": "storage_fig5_monthly.png",
    # A2.1's narrow renders. The builders name these without the site's prefix,
    # the same as their wide counterparts.
    "fig2_dispatch_week-phone.png": "storage_fig2_dispatch_week-phone.png",
    "fig4_sensitivity-phone.png": "storage_fig4_sensitivity-phone.png",
    "fig5_monthly-phone.png": "storage_fig5_monthly-phone.png",
    "fig2_lcoh_stacked-phone.png": "heat_fig2_lcoh_stacked-phone.png",
    "fig3_costgap_contour-phone.png": "heat_fig3_costgap_contour-phone.png",
    "fig1_allometry-phone.png": "lq_allometry-phone.png",
    "fig1_prices-phone.png": "storage_fig1_prices-phone.png",
    "fig2_lq_ranked-phone.png": "lq_ranked-phone.png",
    "fig3_duration_value-phone.png": "storage_fig3_duration_value-phone.png",
    "fig1_breakeven_price-phone.png": "heat_fig1_breakeven_price-phone.png",
    "fig4_tornado-phone.png": "heat_fig4_tornado-phone.png",
    "fig5_emissions_parity-phone.png": "heat_fig5_emissions_parity-phone.png",
    "fig0_lq_explained-phone.png": "lq_explained-phone.png",
    "fig0_lq_explained.png": "lq_explained.png",
    "fig1_allometry.png": "lq_allometry.png",
    "fig2_lq_ranked.png": "lq_ranked.png",
    "fig3_wild_vs_captive-phone.png": "lq_wild_captive-phone.png",
    "fig4_orders-phone.png": "lq_orders-phone.png",
    "fig3_wild_vs_captive.png": "lq_wild_captive.png",
    "fig4_orders.png": "lq_orders.png",
}


def served_widths():
    """Run the browser measurement and fold it to file -> smallest CSS width."""
    out = subprocess.run(["node", os.path.join(HERE, "fig_served_widths.js")],
                         cwd=HERE, capture_output=True, text=True,
                         env={**os.environ,
                              "NODE_PATH": os.path.join(HERE, "node_modules")})
    if out.returncode != 0:
        sys.exit("fig_served_widths.js failed:\n" + (out.stderr or "")[-2000:])
    data = json.loads(out.stdout)
    served = {}
    for r in data["rows"]:
        if not r["file"].lower().endswith(".png"):
            continue                      # the OpenMoji SVGs carry no figure text
        prev = served.get(r["file"])
        if prev is None or r["cssWidth"] < prev[0]:
            served[r["file"]] = (r["cssWidth"], r["page"], r["viewport"], r["engine"])
    return data["config"], served


def min_points(work):
    """Run every builder into `work` and record each figure's authored width
    and smallest text, in points. Recomputed, never read from a file."""
    code = r'''
import json, os, runpy, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT); sys.path.insert(0, ROOT)
import matplotlib; matplotlib.use("Agg")
import matplotlib.figure
import sitefig
REC = {}
def items(fig):
    out = [t for t in fig.texts if t.get_text().strip()]
    titles = {id(t) for ax in fig.axes for t in sitefig.titles(ax)}
    for ax in fig.axes:
        for t in (sitefig.titles(ax) + [ax.xaxis.label, ax.yaxis.label] + list(ax.texts)):
            if t.get_text().strip():
                out.append(t)
        if ax.axison:
            x0, x1 = sorted(ax.get_xlim()); y0, y1 = sorted(ax.get_ylim())
            for tk, lo, hi in ((ax.xaxis, x0, x1), (ax.yaxis, y0, y1)):
                if not tk.get_visible():
                    continue
                for loc, lab in zip(tk.get_ticklocs(), tk.get_ticklabels()):
                    if lo - 1e-9 <= loc <= hi + 1e-9 and lab.get_text().strip() and lab.get_visible():
                        out.append(lab)
        lg = ax.get_legend()
        if lg:
            out += [x for x in lg.get_texts() if x.get_text().strip()]
    seen, uniq = set(), []
    for t in out:
        if id(t) not in seen:
            seen.add(id(t)); uniq.append(t)
    return uniq, titles
_sf = matplotlib.figure.Figure.savefig
def savefig(self, fname, *a, **kw):
    name = os.path.basename(str(fname))
    try:
        got, _titles = items(self)
        pts = [(float(t.get_fontsize()), t.get_text().strip()[:40]) for t in got]
        lo = min(pts) if pts else (None, None)
        REC[name] = {"authored": round(float(self.get_size_inches()[0]) * 72, 1),
                     "min_pt": lo[0], "text": lo[1]}
    except Exception as e:
        REC[name] = {"error": repr(e)[:140]}
    return _sf(self, fname, *a, **kw)
matplotlib.figure.Figure.savefig = savefig
rel, cwd, out = sys.argv[1], sys.argv[2], sys.argv[3]
script = os.path.join(ROOT, rel); here = os.path.join(ROOT, cwd)
os.chdir(here); sys.path.insert(0, here)
sys.argv = [script]
try:
    runpy.run_path(script, run_name="__main__"); st = "ok"
except SystemExit as e:
    st = "SystemExit %s" % e.code
except Exception as e:
    st = "%s: %s" % (type(e).__name__, e)
json.dump({"status": st, "figures": REC}, open(out, "w"))
'''
    runner = os.path.join(work, "_figpt_runner.py")
    open(runner, "w", encoding="utf-8").write(code)
    # one builder per subprocess. Nine in one interpreter made
    # fig_lq_explained.py exit 1 where it exits 0 alone - build_lq.py runs
    # before it and leaves state behind - so the gate was reporting a builder
    # as broken because of how the gate ran it.
    status, figures = {}, {}
    for i, (rel, cwd) in enumerate(BUILDERS):
        res = os.path.join(work, f"_figpt_{i}.json")
        out = subprocess.run([PY, runner, rel, cwd, res], cwd=work,
                             capture_output=True, text=True, encoding="utf-8",
                             errors="replace")
        if not os.path.exists(res):
            status[rel] = ("produced nothing: "
                           + ((out.stderr or out.stdout or "")[-300:]).replace("\n", " "))
            continue
        got = json.load(open(res, encoding="utf-8"))
        status[rel] = got["status"]
        figures.update(got["figures"])
    return {"status": status, "figures": figures}


def copy_tree():
    sys.path.insert(0, HERE)
    import test_generators as TG
    work = tempfile.mkdtemp(prefix="figfloor-")
    dst = os.path.join(work, "tree")
    shutil.copytree(ROOT, dst, ignore=TG._ignore(ROOT), symlinks=True)
    return work, dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--break", dest="brk", choices=["stale", "added", "matrix"])
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--enforce", action="store_true")
    args = ap.parse_args()

    fx = matrix_fixture()                                     # fixture first
    if fx:
        print("  D-01 matrix FIXTURE FAILED - the arithmetic is wrong, no verdict:")
        for f in fx:
            print("    - " + f)
        return 1

    exempt = set(EXEMPT)
    if args.brk == "added":
        # A name that was never in ORIGINAL. Property 3 must refuse it.
        exempt.add("a_figure_that_was_never_here.png")
    cfg, served = served_widths()
    mcfg, mrows = matrix_widths(args.brk == "matrix")
    work, tree = copy_tree()
    try:
        run = min_points(tree)
    finally:
        if not args.keep:
            shutil.rmtree(work, ignore_errors=True)
        else:
            print(f"  work copy kept at {work}")

    failed_builders = [f"{k}: {v}" for k, v in run["status"].items()
                       if v not in ("ok", "SystemExit 0", "SystemExit None")]

    print("  config: playwright %s, %s, deviceScaleFactor %s, viewports %s"
          % (cfg["playwright"], ", ".join(cfg["engines"]),
             cfg["deviceScaleFactor"], ", ".join(cfg["viewports"])))
    print(f"  floor {FLOOR_PX:g}px at the served width; "
          f"{len(exempt)} of {len(ORIGINAL)} figures still on the list")

    rows, problems = [], []
    accounted = set()
    for out_name, rec in sorted(run["figures"].items()):
        asset = ASSET_OF.get(out_name, out_name)
        if asset not in served:
            continue                      # drawn but not shown on a page
        accounted.add(asset)
        if "error" in rec or not rec.get("min_pt"):
            problems.append(f"{asset}: the builder gave no text to measure "
                            f"({rec.get('error', 'no text')})")
            continue
        css, page, vp, eng = served[asset]
        px = rec["min_pt"] * css / rec["authored"]
        ok = px >= FLOOR_PX - 1e-6
        if args.brk == "stale" and asset in exempt and not ok:
            # Pretend this one was converted. Property 1 must notice that a
            # listed figure now passes and call the list stale.
            ok, px = True, FLOOR_PX
        rows.append((asset, page, rec["authored"], css, rec["min_pt"], px, ok))

    listed_passing = [r[0] for r in rows if r[6] and r[0] in exempt]
    unlisted_failing = [r for r in rows if not r[6] and r[0] not in exempt]
    not_original = sorted(exempt - set(ORIGINAL))
    listed_missing = sorted(exempt - {r[0] for r in rows})

    for a, page, aw, css, pt, px, ok in rows:
        mark = "ok  " if ok else ("EXEMPT" if a in exempt else "FAIL")
        print(f"  {mark:6s} {a:34s} {page:12s} authored {aw:6.0f} "
              f"served {css:6.1f}  {pt:4.1f}pt -> {px:5.1f}px")

    if not_original:                                        # Property 1
        problems.append("EXEMPT holds %d name(s) not in ORIGINAL - the list may "
                        "only shrink: %s" % (len(not_original), ", ".join(not_original)))
    if listed_passing:
        problems.append("%d listed figure(s) now meet the floor; take them out "
                        "of EXEMPT: %s" % (len(listed_passing), ", ".join(sorted(listed_passing))))
    for a, page, aw, css, pt, px, _ in unlisted_failing:
        problems.append(f"{a} on {page}: {pt:g}pt at {css:g}/{aw:g} renders "
                        f"{px:.1f}px, under the {FLOOR_PX:g}px floor")
    if listed_missing:
        problems.append("EXEMPT names %d figure(s) this run never measured: %s"
                        % (len(listed_missing), ", ".join(listed_missing)))
    # A FIGURE THE PAGES SERVE THAT NO BUILDER ROW EXPLAINS. This closes the
    # only way this gate can be green for a figure it never measured: a name
    # missing from ASSET_OF made `asset not in served` true and the row was
    # dropped in silence. A2.1's three narrow renders hit it first - the gate
    # reported the same 29 figures measured after three new ones reached the
    # site - and the count was the only tell, in a line nobody reads as an
    # assertion. It is one now.
    unexplained = sorted(set(served) - accounted)            # Property 2
    if unexplained:
        problems.append("%d figure(s) the pages serve that no builder row "
                        "accounted for - add them to ASSET_OF or find out who "
                        "draws them: %s" % (len(unexplained), ", ".join(unexplained)))

    # The docstring says ASSET_OF is asserted against site/assets/, so assert
    # it. sync_assets.py's PREFIX_SOURCE holds the same mapping; a rename on
    # either side that is not made on both would otherwise show up here as a
    # figure quietly dropping out of the run rather than as an error.
    assets = os.path.join(ROOT, "site", "assets")
    ghosts = sorted(v for v in ASSET_OF.values()
                    if not os.path.exists(os.path.join(assets, v)))
    if ghosts:
        problems.append("ASSET_OF names %d file(s) that are not in "
                        "site/assets/: %s" % (len(ghosts), ", ".join(ghosts)))
    problems += failed_builders

    print()
    if problems:
        print(f"  {len(problems)} problem(s):")
        for p in problems:
            print("    - " + p)
    else:
        print(f"  {len(rows)} figures measured at the served width, "
              f"{len(rows) - len(exempt)} at or above {FLOOR_PX:g}px, "
              f"{len(exempt)} on the list")

    mfails, mproblems = matrix_report(run, mcfg, mrows, exempt, args.enforce)
    if args.brk == "matrix":
        caught = bool(mproblems)
        print(f"  --break matrix: {'caught' if caught else 'BLIND'}")
        return 1 if caught else 0
    if mproblems:
        return 1
    if args.brk:
        caught = bool(problems)
        print(f"  --break {args.brk}: {'caught' if caught else 'BLIND'}")
        return 0 if caught else 1
    return 1 if problems or (args.enforce and mfails) else 0


# D-01 RULE 3 -------------------------------------------------------------------
D01_VIEWPORTS = ("360x780", "390x844", "768x1024", "1024x768", "1440x900",
                 "960x600", "720x450", "576x360", "360x225")
D01_ZOOM = {"960x600": 150, "720x450": 200, "576x360": 250, "360x225": 400}
D01_ENGINES = ("chromium", "webkit")


def matrix_px(min_pt, css, authored):
    return min_pt * css / authored


def matrix_fixture():
    bad = []
    for pt, auth, css, want_px, want_ok in ((9.0, 714.0, 350.0, 4.41, False),
                                           (12.0, 350.0, 350.0, 12.0, True)):
        px = matrix_px(pt, css, auth)
        if abs(px - want_px) > 0.01 or (px >= FLOOR_PX - 1e-6) != want_ok:
            bad.append(f"{pt}pt on a {auth:g} figure served at {css:g} read {px:.2f}px, "
                       f"want {want_px}px and {'pass' if want_ok else 'fail'}")
    return bad


def matrix_widths(narrow):
    """(config, {(file, viewport): (css, page, engine)}), smallest css across engines."""
    out = subprocess.run(["node", os.path.join(HERE, "fig_served_widths.js"), "--matrix"],
                         cwd=HERE, capture_output=True, text=True,
                         env={**os.environ,
                              "NODE_PATH": os.path.join(HERE, "node_modules")})
    if out.returncode != 0:
        sys.exit("fig_served_widths.js --matrix failed:\n" + (out.stderr or "")[-2000:])
    data = json.loads(out.stdout)
    rows = {}
    for r in data["rows"]:
        if not r["file"].lower().endswith(".png"):
            continue
        if narrow and r["viewport"] not in ("1440x900", "390x844"):
            continue                       # --break matrix: the set this file had
        k = (r["file"], r["viewport"])
        if k not in rows or r["cssWidth"] < rows[k][0]:
            rows[k] = (r["cssWidth"], r["page"], r["engine"])
    cfg = data["config"]
    cfg["measured"] = sorted({v for _, v in rows})
    cfg["engines_measured"] = sorted({e.split()[0] for e in cfg["engines"]})
    return cfg, rows


def matrix_report(run, cfg, rows, exempt, enforce):
    problems = []
    missing_v = [v for v in D01_VIEWPORTS if v not in cfg["measured"]]
    missing_e = [e for e in D01_ENGINES if e not in cfg["engines_measured"]]
    if missing_v or missing_e:                       # coverage: the whole matrix
        problems.append("the D-01 matrix was not measured whole: missing "
                        + ", ".join(missing_v + missing_e))
    # The instrument must move: some figure served at two different widths.
    by_file = {}
    for (f, v), (css, _p, _e) in rows.items():
        by_file.setdefault(f, set()).add(round(css, 1))
    if not any(len(w) > 1 for w in by_file.values()):
        problems.append("no figure is served at more than one width across the "
                        "matrix - the measurement is pinned (trap 28)")
    rec_of = {ASSET_OF.get(k, k): v for k, v in run["figures"].items()}
    fails, pairs = [], 0
    for (f, v), (css, page, eng) in sorted(rows.items(), key=lambda x: (x[0][1], x[0][0])):
        rec = rec_of.get(f)
        if not rec or not rec.get("min_pt"):
            continue            # the 1440/390 gate above already names these
        pairs += 1
        px = matrix_px(rec["min_pt"], css, rec["authored"])
        if px < FLOOR_PX - 1e-6:
            fails.append((v, f, page, rec["authored"], css, rec["min_pt"], px, f in exempt, eng))
    print()
    print("  D-01 RULE 3 (12px at every configuration), %s: config playwright %s, %s, "
          "deviceScaleFactor %s" % ("enforced" if enforce else "reported, not enforced",
                                    cfg["playwright"], ", ".join(cfg["engines"]),
                                    cfg["deviceScaleFactor"]))
    for v, f, page, aw, css, pt, px, ex, eng in fails:
        z = f" = {D01_ZOOM[v]}% of 1440x900" if v in D01_ZOOM else ""
        print(f"    [{eng} | {v}{z} | dpr 1] {'EXEMPT ' if ex else ''}{f} on {page}: "
              f"{pt:g}pt at {css:g}/{aw:g} -> {px:.1f}px")
    pages = sorted({x[2] for x in fails})
    print(f"  D-01 rule 3: {len(fails)} of {pairs} figure-configuration pairs under "
          f"{FLOOR_PX:g}px ({sum(1 for x in fails if x[7])} on exempt figures), on "
          f"{len(pages)} page(s){': ' + ', '.join(pages) if pages else ''}")
    for p in problems:
        print("    - MATRIX: " + p)
    return fails, problems


if __name__ == "__main__":
    sys.exit(main())
