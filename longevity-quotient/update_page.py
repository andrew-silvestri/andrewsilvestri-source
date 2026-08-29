"""
Regenerate the data-dependent parts of the write-up page from the model.

Every number on that page used to be typed. That is fine exactly once: the
first time the data changes, some of them are updated and some are not, and a
page that is right in eight places and wrong in two is worse than one that is
wrong everywhere, because nothing tells the reader which is which. This widened
the table from 417 species to nearly eight thousand and moved the fitted
intercept by a quarter, which would have left about a dozen stale figures
scattered through the prose.

So the numbers are written from outputs/summary.json and
outputs/ingest_report.json, both produced by the build. Prose stays hand
written; arithmetic does not.

Run:  python3 update_page.py            report only
      python3 update_page.py --apply
"""

import argparse
import csv
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
SITE = os.path.abspath(os.path.join(HERE, "..", "site"))
PAGE = os.path.join(SITE, "longevity.html")

# What each baseline is called on the page, and what the model calls it.
POOLS = [("All animals", None), ("Mammals", "Mammalia"), ("Birds", "Aves"),
         ("Reptiles", "Reptilia"), ("Fish", "Pisces"),
         ("Amphibians", "Amphibia"), ("Invertebrates", "Invertebrata")]

SOURCE_ROWS = [
    ("seed", "Hand-checked seed table",
     "Records verified one at a time, each with its own citation."),
    ("anage", "AnAge build 15",
     "The curated standard. Carries its own quality grade and a wild versus "
     "captive distinction, both of which are honoured rather than "
     "overwritten."),
    ("amniote", "Amniote life-history database",
     "Birds, mammals and reptiles. A peer-reviewed compilation reporting the "
     "median where its own sources disagreed."),
    ("pantheria", "PanTHERIA",
     "Mammals. Maximum longevity in months, converted."),
    ("amphibio", "AmphiBIO",
     "Amphibians, which are otherwise almost absent."),
    ("fishbase", "FishBase v25.04",
     "Fish. Maximum age taken as the largest of three fields that disagree: "
     "the curated longevity, the per-population maximum, and the tmax used "
     "to fit growth curves. Graded C throughout."),
]


def fmt(n):
    return f"{n:,}"


def sig(x, n=3):
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "n/a"
    return f"{x:.{n}f}"


def load():
    summary = json.load(open(os.path.join(OUT, "summary.json"),
                             encoding="utf-8"))
    report = json.load(open(os.path.join(OUT, "ingest_report.json"),
                            encoding="utf-8"))
    rows = list(csv.DictReader(
        open(os.path.join(HERE, "data", "animals_merged.csv"),
             encoding="utf-8")))
    return summary, report, rows


def baseline_table(summary):
    """Slope, fit quality and what each baseline predicts for a kilogram —
    which is the only way to read an intercept without doing arithmetic in
    your head."""
    g = summary["global_fit"]
    fits = summary["class_fits"]
    rej = summary.get("rejected_fits", {}) or {}

    out = ['<table>',
           '<tr><th>Baseline</th><th>Species in fit</th><th>Slope b</th>'
           '<th>r&sup2;</th><th>Predicted at 1 kg</th></tr>']
    for label, key in POOLS:
        f = g if key is None else fits.get(key)
        if f is None:
            why = rej.get(key)
            note = ("rejected, falls back to the global baseline"
                    if why else "not fitted")
            out.append(f'<tr><td>{label}</td><td colspan="4" '
                       f'class="dim">{note}</td></tr>')
            continue
        pred = 10 ** (f["a"] + f["b"] * 3.0)          # 1 kg = 1000 g
        out.append(
            f'<tr><td>{label}</td><td>{fmt(round(f["n"]))}</td>'
            f'<td>{sig(f["b"])}</td><td>{sig(f["r2"], 2)}</td>'
            f'<td>{pred:.1f} yr</td></tr>')
    out.append('</table>')
    return "\n".join(out)


def sources_section(report, rows):
    pulled, kept = report["pulled"], report["kept_by_source"]
    grades = report["grades"]
    n = report["final"]

    tr = []
    for key, name, what in SOURCE_ROWS:
        tr.append(
            f'<tr><td>{name}</td><td>{fmt(pulled.get(key, 0))}</td>'
            f'<td>{fmt(kept.get(key, 0))}</td><td>{what}</td></tr>')

    grade_bits = " &middot; ".join(
        f"{k} {fmt(v)}" for k, v in sorted(grades.items()))

    return f"""<h2>Where the data comes from</h2>

<p>Six databases carry a maximum lifespan. They overlap heavily and they
disagree, so a species found in more than one takes its numbers from the best
source available and records the others as corroboration. Averaging a careful
record against a careless one produces a number that belongs to neither.</p>

<table>
<tr><th>Source</th><th>Records with a lifespan</th><th>Used as the record</th>
 <th>What it is</th></tr>
{chr(10).join(tr)}
</table>

<p>Body-mass databases are a separate matter and they are much larger. AVONET
alone has measured masses for {fmt(report['mass_index'])} species, mostly
birds. None of them create a record: a species with a mass and no lifespan is
not an observation of anything this model can use. They only rescue a species
that has been aged and never weighed, which they did
{fmt(report['mass_filled'])} times.</p>

<p>{fmt(report['species_with_a_lifespan'])} distinct species carried a lifespan
after the merge. {fmt(report['dropped_no_mass'])} of them were dropped for
having no body mass in any source &mdash; mostly reptiles and amphibians,
which are routinely measured snout to vent and never put on a scale.
{fmt(report['mass_modelled_from_length'])} fish were kept with a mass computed
from maximum length through FishBase's own length&ndash;weight relationship;
those are modelled, not measured, and are marked and graded accordingly. What
survives is <strong>{fmt(n)} species</strong>, graded {grade_bits}.</p>

<p class="small">This is the ceiling, and it is worth being clear about why.
About 2.24 million species have been described. Fewer than nine thousand have
ever been both aged and weighed, because a maximum lifespan requires somebody
to have watched an animal until it died. The limit here is not access to data.
It is that the observations were never made. Wikidata, which is the aggregate
of individual species pages rather than a compiled table, holds 1,147 taxa with
a recorded maximum lifespan and 259 with a lifespan and a mass together
&mdash; less than a twentieth of what the compiled databases give, which is the
answer to whether scraping species pages one at a time would do better.</p>
"""


def arithmetic_section(summary, rows):
    g = summary["global_fit"]
    fits = summary["class_fits"]
    masses = [float(r["mass_g"]) for r in rows if r["mass_g"]]
    lo, hi = min(masses), max(masses)
    span = math.log10(hi / lo)

    lines = []
    for label, key in POOLS:
        f = g if key is None else fits.get(key)
        if f is None:
            continue
        lines.append(f"{label + ':':16s}log10 L = {f['a']:+.3f} "
                     f"{f['b']:+.3f} log10 M")

    return f"""<h2>The arithmetic, written out</h2>

<p>One weighted ordinary least squares regression per baseline, of log&#8321;&#8320;
maximum lifespan in years on log&#8321;&#8320; adult body mass in grams. Weights come
from the data grade, so a record verified against a named individual counts for
five times what a compilation estimate counts for. The sample spans
{span:.1f} orders of magnitude of body mass, from {lo:,.0f} g to
{hi:,.0f} g.</p>

<pre><code>{chr(10).join(lines)}

predicted lifespan  =  10 ^ (a + b * log10(mass in grams))
LQ                  =  observed maximum lifespan / predicted</code></pre>

<p>The sample size quoted for each fit is Kish's effective sample size,
(&Sigma;w)&sup2; / &Sigma;w&sup2;, not the raw count. A thousand records at a fifth
weight do not carry the information of a thousand records at full weight, and
quoting the raw number would overstate the fit's authority by about a
factor of two.</p>

<p>The slope is the interesting parameter. At {sig(g['b'])} it says a tenfold
increase in mass buys a {10 ** g['b']:.2f}-fold increase in maximum lifespan
&mdash; lifespan goes roughly as the {1 / g['b']:.0f}th root of mass. This is
why the prediction is so hard to escape by growing: an animal a thousand times
heavier than another is predicted to live only about
{10 ** (3 * g['b']):.1f} times longer.</p>
"""


def data_section(summary, report, rows):
    rk = summary["ranks"]
    wild = sum(1 for r in rows if r["wild_yr"].strip())
    cap = sum(1 for r in rows if r["captive_yr"].strip())
    both = sum(1 for r in rows
               if r["wild_yr"].strip() and r["captive_yr"].strip())
    return f"""<h2>Data</h2>

<p>{fmt(report['final'])} species spanning {rk['phylum']} phyla,
{rk['class']} classes, {rk['order']} orders, {rk['family']} families and
{rk['genus']} genera. Every record carries full taxonomy, an adult body mass, at
least one maximum lifespan, a quality grade and its provenance.
{fmt(wild)} have a wild maximum, {fmt(cap)} a captive maximum, and
{fmt(both)} have both &mdash; which is the comparison this project was built
around, and the reason the merge keeps the hand-checked table at the top of the
precedence order rather than letting a bulk source overwrite it. Most bulk
sources report a single figure per species without saying which kind it is.</p>

<p>Disputed records lose to verified ones: the 226-year koi and the 120-year
cockatoo are both out. Grade C records appear in the table and in the
visualiser, with their grade shown, but are held out of every regression, so a
weak record can be looked at without being allowed to move the baseline that
judges it.</p>
"""


def main(apply=False):
    summary, report, rows = load()
    t = open(PAGE, encoding="utf-8").read()
    n = report["final"]
    changes = []

    def sub(pattern, repl, label, count=1):
        nonlocal t
        new, k = re.subn(pattern, repl, t, count=count, flags=re.S)
        if k:
            changes.append(f"{label} ({k})")
            t = new
        else:
            changes.append(f"MISSED {label}")

    # the headline count, wherever it appears as "N species in this model"
    sub(r"the [\d,]+ species in this model",
        f"the {fmt(n)} species in this model", "headline species count")

    # the baseline table
    sub(r"<table>\s*<tr><th>Baseline</th>.*?</table>",
        lambda m: baseline_table(summary), "baseline table")

    # the explainer figure, once, after the quotient definition
    if 'lq_explained.png' not in t:
        anchor = ("<p>It is built by analogy with the encephalisation "
                  "quotient")
        fig = ('<img class="fig wide" src="assets/lq_explained.png" '
               'alt="Three animals of increasing mass, with the lifespan the '
               'allometry predicts beside the lifespan actually observed, and '
               'the quotient that falls out.">\n'
               '<p class="small">Mass rises left to right and so does the '
               'prediction, because the fit can only go up. What the animals '
               'do is not monotonic, and the quotient is what is left once '
               'size has been divided out.</p>\n\n')
        if anchor in t:
            t = t.replace(anchor, fig + anchor, 1)
            changes.append("explainer figure inserted")
        else:
            changes.append("MISSED explainer figure anchor")
    else:
        # and if an earlier run left duplicates, drop them
        blocks = re.findall(
            r'<img class="fig wide" src="assets/lq_explained\.png".*?</p>\n\n',
            t, flags=re.S)
        if len(blocks) > 1:
            for b in blocks[1:]:
                t = t.replace(b, "", 1)
            changes.append(f"removed {len(blocks) - 1} duplicate figure(s)")
        else:
            changes.append("explainer figure already present")

    # the two generated sections, before Sources
    for marker, builder, label in (
            ("<h2>Data</h2>",
             lambda: data_section(summary, report, rows), "data section"),
            ("<h2>Where the data comes from</h2>",
             lambda: sources_section(report, rows), "sources section"),
            ("<h2>The arithmetic, written out</h2>",
             lambda: arithmetic_section(summary, rows), "arithmetic section")):
        block = builder()
        if marker in t:
            t = re.sub(re.escape(marker) + r".*?(?=<h2>)", block + "\n", t,
                       count=1, flags=re.S)
            changes.append(f"{label} refreshed")
        else:
            t = t.replace("<h2>Sources</h2>", block + "\n<h2>Sources</h2>", 1)
            changes.append(f"{label} inserted")

    for c in changes:
        print(f"  {c}")
    if not apply:
        print("\n  report only. Re-run with --apply.")
        return 1 if any(c.startswith("MISSED") for c in changes) else 0
    open(PAGE, "w", encoding="utf-8").write(t)
    print(f"\n  wrote {PAGE}")
    return 1 if any(c.startswith("MISSED") for c in changes) else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    raise SystemExit(main(ap.parse_args().apply))
