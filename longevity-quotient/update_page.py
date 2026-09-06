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
     "median where its own sources disagreed. One maximum per species, with "
     "no record of whether the animal was wild or captive; carried here as "
     "origin not recorded."),
    ("pantheria", "PanTHERIA",
     "Mammals. Maximum longevity in months, converted."),
    ("amphibio", "AmphiBIO",
     "Amphibians, which are otherwise almost absent. No origin field; carried "
     "as origin not recorded."),
    ("fishbase", "FishBase v25.04",
     "Fish. Maximum age taken as the largest of three fields that disagree: "
     "the curated wild longevity, the per-population maximum, and the tmax "
     "used to fit growth curves. Only the first is kept as a wild maximum; "
     "the others are carried as origin not recorded. Graded C throughout."),
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


SUMMARY = None


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
    gc = SUMMARY["grade_census"]
    final_bits = " &middot; ".join(
        f"{k} {fmt(v)}" for k, v in sorted(gc.items()))
    o = SUMMARY["outlier_rule"]

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
survives is <strong>{fmt(n)} species</strong>, graded {grade_bits} as they
arrive from their sources. The outlier rule described under the arithmetic
then demotes {o["demoted"]} grade-B records to C, so the model runs on
{final_bits} (the four colonies are counted separately).</p>

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


def mass_str(g):
    """A body mass a reader can picture: the smallest animal here is half a
    microgram, and formatting that as 0 g (which this page did) is wrong."""
    if g >= 1e6:
        return f"{g / 1e6:,.0f} tonnes"
    if g >= 1e3:
        return f"{g / 1e3:,.0f} kg"
    if g >= 1:
        return f"{g:,.0f} g"
    if g >= 1e-3:
        return f"{g * 1e3:g} mg"
    return f"{g * 1e6:g} &micro;g"


def arithmetic_section(summary, rows):
    g = summary["global_fit"]
    fits = summary["class_fits"]
    masses = [float(r["mass_g"]) for r in rows if r["mass_g"]]
    lo, hi = min(masses), max(masses)
    span = math.log10(hi / lo)
    o = summary["outlier_rule"]
    pools = {"Pisces": "fish", "Aves": "birds", "Mammalia": "mammals",
             "Reptilia": "reptiles", "Amphibia": "amphibians",
             "Invertebrata": "invertebrates"}
    by_pool = ", ".join(f"{v} {pools.get(k, k)}" for k, v in
                        sorted(o["by_pool"].items(), key=lambda kv: -kv[1]))

    lines = []
    for label, key in POOLS:
        f = g if key is None else fits.get(key)
        if f is None:
            continue
        lines.append(f"{label + ':':16s}log10 L = {f['a']:+.3f} "
                     f"{f['b']:+.3f} log10 M")

    return f"""<h2>The arithmetic, written out</h2>

<p>One ordinary least squares regression per baseline, unweighted, of
log&#8321;&#8320; maximum lifespan in years on log&#8321;&#8320; adult body mass in grams,
over the grade-A and grade-B records. Grade C is held out of every fit and
scored against the result. Nothing is weighted: an earlier version of this
page described a grade-weighted fit with an effective sample size, which the
model does not run. The simulation in <code>test_fit_strategy.py</code> is why
&mdash; a thin record is biased short, not merely noisy, and down-weighting a
bias still lets it through where dropping it does not. The count beside each
baseline above is the number of records in that fit. The sample spans
{span:.1f} orders of magnitude of body mass, from {mass_str(lo)} to
{mass_str(hi)}.</p>

<pre><code>{chr(10).join(lines)}

predicted lifespan  =  10 ^ (a + b * log10(mass in grams))
LQ                  =  observed maximum lifespan / predicted</code></pre>

<p>One rule runs before the final fit. A preliminary fit per group flags any
grade-B record more than {o["sigma"]:g} residual standard deviations from it,
in either direction, and demotes it to grade C: {o["demoted"]} records here
({by_pool}). The Amniote compilation grades as B by construction and carried
twenty-eight mammals, birds and reptiles with maximum lifespans of one to three
months at body masses up to five kilograms &mdash; a 2.2&nbsp;kg hare at one
month &mdash; which are unit or field errors, not observations, and which sat
at the bottom of every ranking on this page. The rule is symmetric so that it
cannot be accused of only removing what hurts, it never touches a grade-A
record (each of those was checked by hand against a citation), and it deletes
nothing: a demoted record keeps its row, its note says why, and the visualiser
shows it under <b>Include C</b>.</p>

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
    unrec = sum(1 for r in rows if r.get("unknown_yr", "").strip())
    prov = {p["scientific_name"]: p["taken_from"] for p in csv.DictReader(
        open(os.path.join(OUT, "provenance.csv"), encoding="utf-8"))}
    anage_unrec = sum(1 for r in rows if r.get("unknown_yr", "").strip()
                      and prov.get(r["scientific_name"]) == "anage")
    return f"""<h2>Data</h2>

<p>{fmt(report['final'])} species spanning {rk['phylum']} phyla,
{rk['class']} classes, {rk['order']} orders, {rk['family']} families and
{fmt(rk['genus'])} genera. Every record carries full taxonomy, an adult body
mass, at least one maximum lifespan, a quality grade and its provenance.
{fmt(wild)} have a maximum their source labelled wild, {fmt(cap)} one it
labelled captive, and {fmt(both)} have both &mdash; the comparison this
project was built around, and the reason the merge keeps the hand-checked table
at the top of the precedence order rather than letting a bulk source overwrite
it. The largest set, {fmt(unrec)} species, carries a maximum whose source did
not say where the animal lived: the Amniote and AmphiBIO compilations report
one figure per species with no origin, FishBase population maxima do the same,
and {fmt(anage_unrec)} AnAge rows list the
specimen origin as unknown. Until 4 September 2026 every one of those was
labelled wild, here and in the visualiser. A captive maximum runs longer than a
wild one, so the mislabelling flattered exactly the quotient this page is
about. They are now carried, drawn and counted as what they are: a maximum of
unrecorded origin.</p>

<p>Disputed records lose to verified ones: the 226-year koi and the 120-year
cockatoo are both out. Grade C records appear in the table and in the
visualiser, with their grade shown, but are held out of every regression, so a
weak record can be looked at without being allowed to move the baseline that
judges it.</p>
"""


NICK = {
    "Zeiformes": "the dories of", "Monotremata": "the egg-laying",
    "Chiroptera": "the bats of", "Primates": "the", "Tinamiformes": "the tinamous of",
    "Beloniformes": "the needlefishes of", "Carangiformes": "the jacks of",
    "Galliformes": "the ground birds of",
    "Eulipotyphla": "the shrews, moles and hedgehogs of",
    "Afrosoricida": "the tenrecs and golden moles of",
    "Pholidota": "the pangolins of", "Didelphimorphia": "the opossums of",
    "Cuculiformes": "the cuckoos of", "Anguilliformes": "the eels of",
    "Phoenicopteriformes": "the flamingos of",
    "Squaliformes": "the dogfish sharks of", "Beryciformes": "the alfonsinos of",
    "Testudines": "the turtles of", "Vespertilionidae": "the evening bats of",
    "Rhinolophidae": "the horseshoe bats of", "Sebastidae": "the rockfishes of",
    "Scorpaenidae": "the scorpionfishes of", "Hylobatidae": "the gibbons of",
    "Phyllostomidae": "the leaf-nosed bats of",
    "Natalidae": "the funnel-eared bats of",
}


def link(rank, name):
    rk = {"order": "or", "family": "fa", "class": "cl", "phylum": "ph",
          "genus": "ge"}[rank]
    return (f'<a href="longevity-app.html#view=gr&amp;rank={rk}&amp;fRank={rk}'
            f'&amp;fVal={name}" target="_blank" rel="noopener">{name}</a>')


def _named(rank, g):
    n = g["group"]
    return f"{NICK.get(n, 'the')} {link(rank, n)}"


def groups_paragraph(groups):
    """The group-comparison paragraph, written from group_summary.csv. Every
    value in it used to be typed, and after the outlier rule moved the bat
    fit none of them were right."""
    o = [g for g in groups if g["rank"] == "order"
         and int(g["n_species"]) >= 4 and g["geomean_lq_class"]]
    o.sort(key=lambda g: -float(g["geomean_lq_class"]))
    f = [g for g in groups if g["rank"] == "family"
         and int(g["n_species"]) >= 10 and g["geomean_lq_class"]]
    f.sort(key=lambda g: -float(g["geomean_lq_class"]))
    v = lambda g: f"{float(g['geomean_lq_class']):.2f}"
    n = lambda g: int(g["n_species"])
    top = o[:2]
    big = [g for g in o[:12] if n(g) >= 100][:2]
    bottom = o[-3:][::-1]
    by = {g["group"]: g for g in o}
    parts = [f"<p>Of the {len(o)} orders holding four or more grade-A or B "
             f"species, {_named('order', top[0])} top the list at {v(top[0])} "
             f"and {_named('order', top[1])} follow at {v(top[1])}"]
    small = [g for g in top if n(g) < 10]
    if small:
        parts.append(" &mdash; but " + ("both rest" if len(small) == 2 else
                     "one rests") + " on a handful of species, " +
                     " and ".join(str(n(g)) for g in small) +
                     (" respectively" if len(small) == 2 else "") +
                     ", and a geometric mean over four animals is a claim "
                     "about four animals")
    parts.append(". ")
    if big:
        parts.append("The large groups near the top are the ones worth the "
                     "weight: " + " and ".join(
                         f"{_named('order', g)} at {v(g)} across {n(g):,} "
                         f"species" for g in big) + ". ")
    parts.append("At the bottom sit " + ", ".join(
        f"{_named('order', g)} at {v(g)}" for g in bottom))
    extra = [by[k] for k in ("Galliformes", "Eulipotyphla") if k in by
             and by[k] not in bottom]
    if extra:
        parts.append("; " + " and ".join(
            f"{_named('order', g)} come in at {v(g)}" if g["group"] == "Galliformes"
            else f"{_named('order', g)} at {v(g)}" for g in extra))
    parts.append(". ")
    if f:
        parts.append("At family rank, among families with ten or more species, "
                     + ", ".join(f"{_named('family', g)} reach {v(g)} over "
                                 f"{n(g)} species" if i == 0 else
                                 f"{_named('family', g)} {v(g)}"
                                 for i, g in enumerate(f[:3])) + ". ")
    parts.append("Flight, burrowing, venom, armour and simply being difficult "
                 "to swallow all register as raised quotients. Being a ground "
                 "bird or a small terrestrial insectivore registers as the "
                 "reverse.</p>")
    return "".join(parts)


def outcome_paragraph(table):
    """Top and bottom of the species ranking, grade A and B, no colonies."""
    rows = [r for r in table if r["quality"] != "C" and r["colonial"] != "True"
            and (r["lq_class_maximum"] or r["lq_global_maximum"])]
    lq = lambda r: float(r["lq_class_maximum"] or r["lq_global_maximum"])
    rows.sort(key=lambda r: -lq(r))
    top, bot = rows[:6], rows[-5:][::-1]
    art = lambda s: ("an " if s[0].lower() in "aeiou" else "a ") + s
    ts = [f"{art(r['name'].lower())} at {lq(r):.0f}&times;" for r in top]
    bs = [f"{art(r['name'].lower())} at {lq(r):.2f}&times;" for r in bot]
    return ("<p>The highest quotients against their own group, among the grade-A "
            "and B records, belong to " + ", ".join(ts[:-1]) + " and " + ts[-1] +
            " its predicted lifespan. The lowest belong to " +
            ", ".join(bs[:-1]) + " and " + bs[-1] + ".</p>")


def margin_values(t, table):
    """The quotient beside each creature in the margin is that species' own
    lq_class_maximum from the table; rewrite each one from the table."""
    by = {}
    for r in table:
        by.setdefault(r["name"].strip().lower(), r)
    k = 0

    def repl(m):
        nonlocal k
        r = by.get(m.group(1).strip().lower())
        if not r:
            return m.group(0)
        v = float(r["lq_class_maximum"] or r["lq_global_maximum"])
        k += 1
        return f"<b>{m.group(1)}</b>{v:.2f}&times; prediction"
    t = re.sub(r"<b>([^<]+)</b>([\d.]+)(?:&times;|\u00d7) prediction", repl, t)
    return t, k


def main(apply=False):
    summary, report, rows = load()
    global SUMMARY
    SUMMARY = summary
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
    sub(r"(?i)the [\d,]+ species in this model",
        f"The {fmt(n)} species in this model", "headline species count")

    # the baseline table
    sub(r"<table>\s*<tr><th>Baseline</th>.*?</table>",
        lambda m: baseline_table(summary), "baseline table")

    # numbers inside hand-written prose that the model owns
    fits = summary["class_fits"]
    if "Aves" in fits and "Mammalia" in fits:
        b, mm = fits["Aves"], fits["Mammalia"]
        ratio = 10 ** (b["a"] + 3 * b["b"]) / 10 ** (mm["a"] + 3 * mm["b"])
        sub(r"Birds come out\s+about [\d.]+ times longer-lived than mammals of equal mass",
            f"Birds come out\nabout {ratio:.1f} times longer-lived than mammals of equal mass",
            "bird/mammal ratio")
    rej = (summary.get("rejected_fits") or {}).get("Amphibia", "")
    mr = re.search(r"r2=([\d.]+), n_eff=(\d+)", rej)
    if mr:
        sub(r"The amphibian regression returns an r\u00b2 of [\d.]+ across [\w\-]+ species",
            f"The amphibian regression returns an r\u00b2 of {float(mr.group(1)):.2f} "
            f"across {mr.group(2)} species", "amphibian rejection")
    groups = list(csv.DictReader(open(os.path.join(OUT, "group_summary.csv"),
                                      encoding="utf-8")))
    orders = [g for g in groups if g["rank"] == "order"
              and int(g["n_species"]) >= 4 and g["geomean_lq_class"]]
    sub(r"Of the \d+ orders holding four or more (?:grade-A or B )?species",
        f"Of the {len(orders)} orders holding four or more species",
        "order count in prose")
    sub(r"All \d+ orders holding four or more species",
        f"All {len(orders)} orders holding four or more species",
        "order count in caption")
    sub(r"<p>Of the \d+ orders holding four or more (?:grade-A or B )?species.*?</p>",
        lambda m: groups_paragraph(groups), "groups paragraph")
    table = list(csv.DictReader(open(os.path.join(OUT, "lq_table.csv"),
                                     encoding="utf-8")))
    sub(r"<p>The highest quotients against their own group.*?</p>",
        lambda m: outcome_paragraph(table), "what-comes-out paragraph")
    t, k = margin_values(t, table)
    changes.append(f"margin quotients ({k})")
    lo = min(float(r["mass_g"]) for r in rows if r["mass_g"])
    hi = max(float(r["mass_g"]) for r in rows if r["mass_g"])
    sub(r"run from a\s+\w+ at .+? to a blue whale at [\d,]+ tonnes, [\d.]+ orders of\s+magnitude",
        f"run from a\nrotifer at {mass_str(lo).replace('&micro;', '&micro;')} to a blue whale at "
        f"{mass_str(hi)}, {math.log10(hi / lo):.1f} orders of\nmagnitude", "mass range in intro")

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
    open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    print(f"\n  wrote {PAGE}")
    return 1 if any(c.startswith("MISSED") for c in changes) else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    raise SystemExit(main(ap.parse_args().apply))
