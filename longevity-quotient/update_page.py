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
import collections
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
     "Entered by hand, one species at a time; 88 of its rows are graded A, "
     "and it includes projections as well as observed ages."),
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


MASS_NAME = {"avonet": "AVONET", "pantheria": "PanTHERIA",
             "amniote": "Amniote"}
WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven",
         "eight", "nine", "ten"]


def _n(k):
    return WORDS[k] if 0 <= k < len(WORDS) else fmt(k)


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
    # D-29 items 1 and 2. The mass index is AVONET (birds only), PanTHERIA
    # and Amniote together, and mass_filled also counts masses copied from
    # another lifespan record of the same species (509 of 524 in the
    # 2026-10 build). Only the index fills set mass_src, so provenance.csv
    # shows exactly those as mass_from != taken_from.
    prov = list(csv.DictReader(open(os.path.join(OUT, "provenance.csv"),
                                    encoding="utf-8")))
    idx = collections.Counter(p["mass_from"] for p in prov
                              if p["mass_from"] != p["taken_from"])
    from_index = sum(idx.values())
    idx_bits = " and ".join(f"{fmt(v)} from {MASS_NAME.get(k, k)}"
                            for k, v in sorted(idx.items())) or "none from the index"
    # D-29 item 5: the colonies leave the census here, so say so.
    col = collections.Counter(r["quality"] for r in rows
                              if r["colonial"].strip().lower() == "yes")
    col_bits = ", ".join(f"{_n(v)} grade {k}" for k, v in sorted(col.items()))

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

<p>Body-mass databases are a separate matter and they are much larger. AVONET,
which covers birds only, PanTHERIA and Amniote between them hold a mass for
{fmt(report['mass_index'])} species. None of them creates a record: a species
with a mass and no lifespan is not an observation of anything this model can
use. A record that has a lifespan and no mass takes one from elsewhere, which
happened {fmt(report['mass_filled'])} times:
{fmt(report['mass_filled'] - from_index)} from another lifespan record of the
same species, and {idx_bits}.</p>

<p>{fmt(report['species_with_a_lifespan'])} distinct species carried a lifespan
after the merge. {fmt(report['dropped_no_mass'])} of them were dropped for
having no body mass in any source &mdash; mostly reptiles and amphibians,
which are routinely measured snout to vent and never put on a scale.
{fmt(report['mass_modelled_from_length'])} fish were kept with a mass computed
from maximum length through FishBase's own length&ndash;weight relationship;
those are modeled, not measured, and are marked and graded accordingly. What
survives is <strong>{fmt(n)} species</strong>, graded {grade_bits} as they
arrive from their sources. The outlier rule described under the arithmetic
then demotes {o["demoted"]} grade-B records to C, and the
{_n(sum(col.values()))} colonies ({col_bits}) are set aside, so the model runs
on {final_bits}.</p>

<p class="small">This is the ceiling, and it is worth being clear about why.
About 2.24 million species have been described. The six databases merged here
hold fewer than nine thousand that have been both aged and weighed. Sources not
merged add some more (<code>DATA_SOURCES.md</code>, in the download, lists
Add-my-Pet, SeaLifeBase and a compilation of bivalve ages among them), but a
maximum lifespan requires somebody to have watched an animal until it died, and
for most species nobody has. The limit is less access to data than that the
observations were never made. Wikidata, which is the aggregate
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
    # D-29 item 3: 61 of the 149 grade-A records are AnAge's own "high"
    # grade, not rows of the hand-checked table.
    ga = collections.Counter(
        p["taken_from"] for p in csv.DictReader(
            open(os.path.join(OUT, "provenance.csv"), encoding="utf-8"))
        if p["grade"] == "A")
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
scored against the result. Nothing is weighted. That rests on an
assumption: that an uncertain record is biased short, not merely noisy, in
which case down-weighting still lets the bias through and dropping does not.
The simulation in <code>test_fit_strategy.py</code> shows that, but it marks
exactly the records it shortened, so it illustrates the choice rather than
proving it; in the real table grade C does not single out the briefly watched
records (see Limits). The count beside each
baseline above is the number of records in that fit. The sample spans
{span:.1f} orders of magnitude of body mass, from {mass_str(lo)} to
{mass_str(hi)}.</p>

<pre><code>{chr(10).join(lines)}

predicted lifespan  =  10 ^ (a + b * log10(mass in grams))
LQ                  =  observed maximum lifespan / predicted</code></pre>

<p>One rule runs before the final fit. A preliminary fit per group flags any
grade-B record more than {o["sigma"]:g} residual standard deviations from it,
in either direction, and demotes it to grade C: {o["demoted"]} records here
({by_pool}). The Amniote compilation grades as B by construction, and among
the records the rule demotes are twenty-seven of its mammals and reptiles
(twenty-five and two) with maximum lifespans of one to three months at body
masses up to five and a half kilograms &mdash; a 2.2&nbsp;kg hare at one
month &mdash; which are unit or field errors, not observations, and which sat
at the bottom of every ranking on this page. The rule is symmetric so that it
cannot be accused of only removing what hurts, it never touches a grade-A
record ({fmt(ga.get("seed", 0))} of those are rows of the hand-checked table,
entered and checked by hand; the other
{fmt(sum(ga.values()) - ga.get("seed", 0))} are AnAge records that AnAge itself
grades high), and it deletes
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
    # D-29 item 4, counted rather than typed (claims check, R5): the 62 / 48
    # this paragraph carried came from a heuristic that did not ship.
    tab = list(csv.DictReader(open(os.path.join(OUT, "lq_table.csv"),
                                   encoding="utf-8")))
    by_name = collections.defaultdict(list)
    for r in tab:
        if r["name"].strip():
            by_name[r["name"].strip().lower()].append(r)
    multi = [v for v in by_name.values() if len({r["sci"] for r in v}) > 1]
    in_fits = sum(1 for v in multi if sum(
        1 for r in v if r["quality"] != "C" and r["colonial"] != "True") > 1)
    return f"""<h2>Data</h2>

<p>{fmt(report['final'])} species spanning {rk['phylum']} phyla,
{rk['class']} classes, {rk['order']} orders, {rk['family']} families and
{fmt(rk['genus'])} genera. Every record carries full taxonomy, an adult body
mass, at least one maximum lifespan, a quality grade and its provenance.
Species are matched on the binomial alone, with no synonym resolution, so a
species the sources name two ways is in the table twice: matching common names
finds {fmt(len(multi))} common names carried by two or more binomials, the African
spurred tortoise as both <i>Centrochelys</i> and <i>Geochelone sulcata</i> among
them (some are distinct species that share a name), and for {fmt(in_fits)} of
those names at least two copies are grade A or B and enter the fits. The pink cockatoo and Major Mitchell&rsquo;s cockatoo,
one bird under two common names, are a further pair that check misses.
{fmt(wild)} have a maximum their source labeled wild, {fmt(cap)} one it
labeled captive, and {fmt(both)} have both &mdash; the comparison the
hand-checked table was built for, which is why no bulk source is allowed to
overwrite it. The largest set, {fmt(unrec)} species, carries a maximum whose source did
not say where the animal lived: the Amniote and AmphiBIO compilations report
one figure per species with no origin, FishBase population maxima do the same,
and {fmt(anage_unrec)} AnAge rows list the
specimen origin as unknown. A captive maximum runs longer than a wild one, so a
record whose origin is not stated is carried, drawn and counted as a maximum of
unrecorded origin rather than as a wild one.</p>

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
    "Urodela": "the salamanders and newts of", "Anura": "the frogs and toads of",
    "Salamandridae": "the true salamanders and newts of",
}


def link(rank, name):
    rk = {"order": "or", "family": "fa", "class": "cl", "phylum": "ph",
          "genus": "ge"}[rank]
    return (f'<a href="longevity-app.html#view=gr&amp;rank={rk}&amp;fRank={rk}'
            f'&amp;fVal={name}" target="_blank" rel="noopener">{name}</a>')


def _named(rank, g):
    n = g["group"]
    return f"{NICK.get(n, 'the')} {link(rank, n)}"


def groups_paragraph(groups, table=None):
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
    # D-28 item 2: amphibians have no fit of their own, so their orders are
    # scored against the all-animal line, as the page says. The ranking
    # includes them; the narrative keeps them apart, because that line is not
    # the scale the other orders are on.
    glob = lambda g: g.get("scored_against") == "global"
    n_all = len(o)
    lead = o[0]
    amph = [g for g in o if glob(g)]
    o = [g for g in o if not glob(g)]
    f_glob = [g for g in f if glob(g)]
    f = [g for g in f if not glob(g)]
    top = o[:2]
    big = [g for g in o[:12] if n(g) >= 100][:2]
    # D-29 item 11: four, so the opossums (0.49, below the ground birds)
    # are not skipped.
    bottom = o[-4:][::-1]
    by = {g["group"]: g for g in o}
    parts = [f"<p>Of the {n_all} orders holding four or more grade-A or B "
             f"species, "]
    if glob(lead):
        fits = (SUMMARY or {}).get("rejected_fits", {}).get("Amphibia", "")
        mr = re.search(r"r2=([\d.]+)", fits)
        parts.append(
            f"{_named('order', lead)} top the list at {v(lead)}, but on a "
            f"different footing: body mass explains "
            + (f"only {float(mr.group(1)):.0%} of" if mr else "almost none of")
            + " the spread in amphibian lifespans, so amphibians are scored "
            "against the line for all animals "
            "rather than a fit of their own, "
            + " and ".join(f"{_named('order', g)} coming out at {v(g)} the "
                           f"same way" for g in amph if g is not lead) +
            ". Among orders scored against their own class, ")
    small = [g for g in top if n(g) < 10]
    parts.append(f"{_named('order', top[0])} lead at {v(top[0])}" +
                 (f", but on only {_n(n(top[0]))} species" if top[0] in small
                  else "") + ". ")
    if big:
        parts.append("The large groups near the top carry more weight: "
                     + " and ".join(
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
                                 for i, g in enumerate(f[:3]))
                     + "".join(f" (on the all-animal line, {_named('family', g)} "
                               f"would reach {v(g)} over {n(g)} species)"
                               for g in f_glob if float(g["geomean_lq_class"])
                               > float(f[2]["geomean_lq_class"]))
                     + ". ")
    # D-29 item 8: Sebastes is filed under two families, and the long-lived
    # rockfishes carry the Scorpaenidae figure.
    if table is not None and "Scorpaenidae" in [g["group"] for g in f[:3]]:
        sc = [r for r in table if r["family"] == "Scorpaenidae"
              and r["quality"] != "C" and r["colonial"] != "True"
              and r["lq_class_maximum"]]
        seb = [r for r in sc if r["genus"] == "Sebastes"]
        rest = [float(r["lq_class_maximum"]) for r in sc
                if r["genus"] != "Sebastes"]
        if seb and rest:
            gm = 10 ** (sum(math.log10(x) for x in rest) / len(rest))
            parts.append(
                f"The scorpionfish figure is mostly rockfishes: {len(seb)} of "
                f"its {len(sc)} species are <i>Sebastes</i>, a genus the "
                f"sources file partly under Sebastidae and partly under "
                f"Scorpaenidae, and without them the family comes to "
                f"{gm:.2f}. ")
    parts.append("</p>")
    return "".join(parts)


def _caveat(r):
    """D-29 items 7 and 9: two of the named extremes are not what they look
    like. Said beside them for as long as they are named."""
    n = r["name"].strip().lower()
    if n == "olm":
        return ("The olm&rsquo;s 100 years is a projection, not an observed "
                "age: Voituron <i>et al.</i> (<i>Biology Letters</i> 7:105, "
                "2011) estimated a maximum of about 102 years from a "
                "laboratory population, and the 68 years the table carries as "
                "its wild maximum is that population&rsquo;s mean adult "
                "lifespan.")
    if n == "toolache wallaby":
        return (f"The toolache wallaby&rsquo;s figure is the Amniote "
                f"compilation&rsquo;s {float(r['maximum']) * 12:.0f} months "
                f"for a {float(r['mass_g']) / 1000:.0f}&nbsp;kg animal, very "
                f"likely an error of the kind the outlier rule removes, which "
                f"the rule&rsquo;s three-standard-deviation cut misses by a "
                f"hair.")
    return None


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
    inv = [r for r in top if r["phylum"] != "Chordata"]
    n_inv = sum(1 for r in table if r["phylum"] != "Chordata"
                and r["quality"] != "C" and r["colonial"] != "True")
    note = (f" {_n(len(inv)).capitalize()} of those six are invertebrates, "
            f"scored against one line pooled from {n_inv} species of every "
            f"invertebrate phylum here, a coarse yardstick." if inv else "")
    return ("<p>The highest quotients against their own group, among the grade-A "
            "and B records, belong to " + ", ".join(ts[:-1]) + " and " + ts[-1] +
            " its predicted lifespan." + note + " The lowest belong to " +
            ", ".join(bs[:-1]) + " and " + bs[-1] + "." +
            "".join(" " + c for c in (_caveat(r) for r in top + bot) if c) +
            "</p>")


WORD_N = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
ZIP = os.path.join(SITE, "downloads", "longevity-code.zip")


def _order(lst, name):
    for i, o in enumerate(lst):
        if o[0] == name:
            return i, o
    return None, None


HALVES = {1.0: "", 1.5: "one and a half", 2.0: "two", 2.5: "two and a half",
          3.0: "three"}


def _half(x):
    return round(x * 2) / 2


def headline(summary, table):
    """h1 and standfirst (_INSIGHT rule 1). Led by the group finding, which
    the study-effort checks move least (D-28); every figure in it is read
    from the pooled run and both checks in summary.json, and the wording
    stops the build if a check stops agreeing with it."""
    h = summary["headline"]
    ec = summary["effort_check"]
    c, d = ec["corrected"], ec["dropped"]
    by = {r["name"]: r for r in table}
    hu = by["Human"]
    runs = [{o[0]: o for o in x["orders"]} for x in (h, c, d)]
    oo, co, do = runs

    def every(k):
        return [r[k][1] for r in runs if k in r]
    bats, prim, gall = every("Chiroptera"), every("Primates"), every("Galliformes")
    lo = min(bats + prim)
    hi = max(bats + prim)
    # the h1 says "one and a half to two and a half"; hold it to that
    if not (_half(lo) == 1.5 and _half(hi) == 2.5 and min(bats + prim) > 1.25):
        raise SystemExit(f"h1: bats/primates span {lo:.2f}-{hi:.2f} no longer "
                         f"reads 'one and a half to two and a half'")
    if not all(.45 <= v < .55 for v in gall):
        raise SystemExit(f"h1: Galliformes {gall} is no longer 'half'")
    # tenrecs and opossums are named on the pooled and corrected runs only
    # (too few species survive the dropped run to rank them)
    for k in ("Afrosoricida", "Didelphimorphia"):
        if not all(.4 <= r[k][1] < .6 for r in (oo, co)):
            raise SystemExit(f"standfirst: {k} is no longer about half")
    hs = sorted((h["species"]["Human"], c["species"]["Human"],
                 d["species"]["Human"]))
    g = summary["global_fit"]
    qu = float(by["Ocean quahog"]["maximum"])
    return (
        f"<h1>Bats and primates live one and a half to two and a half times "
        f"as long as their size predicts; pheasants and their kin, half as "
        f"long</h1>\n"
        f'<p class="dim">Bigger animals live longer, by a predictable amount. '
        f"Draw a line through the record lifespans of the {fmt(round(g['n']))} "
        f"species whose records are sound enough to fit, against their body "
        f"weight, and each tenfold gain in weight "
        f"adds about {(10 ** g['b'] - 1):.0%} to the years; mammals, birds, "
        f"reptiles, fish and invertebrates each get a line of their own. "
        f"Against the mammal line, bats as a group live {oo['Chiroptera'][1]:.1f} "
        f"times as long as their size predicts, across "
        f"{oo['Chiroptera'][2]} species, and primates {oo['Primates'][1]:.1f} "
        f"times across {oo['Primates'][2]}, while tenrecs and golden moles, and opossums, reach "
        f"about half of what their size predicts. Against the bird line, the "
        f"{oo['Galliformes'][2]} pheasants, grouse, quail and chickens reach "
        f"about half too. Those "
        f"figures depend on a gap in the data: many mammals have been watched "
        f"only briefly, which makes their records short and pulls the mammal "
        f"line down. Corrected for that, bats come to "
        f"{co['Chiroptera'][1]:.1f} and primates to {co['Primates'][1]:.1f}; "
        f"leave the briefly watched mammals out altogether and they come to "
        f"{do['Chiroptera'][1]:.1f} and {do['Primates'][1]:.1f}, still above "
        f"their size (the Limits section at the foot of the page shows each "
        f"figure all three ways). People sit "
        f"higher still: the longest verified human life, "
        f"{float(hu['maximum']):g} years, is {hs[0]:.1f} to {hs[-1]:.1f} times "
        f"the line for a {float(hu['mass_g']) / 1000:.0f}-kilogram mammal, "
        f"depending on the same correction, though a record set among "
        f"billions of people is an upper bound "
        f"against species watched a few dozen times. The animals far above "
        f"their line, bats, the naked mole-rat and the ocean quahog, a clam "
        f"recorded at {qu:.0f} years, are where biologists look for clues to "
        f"slowing ageing, the case Steven Austad makes in "
        f"<i>Methuselah&rsquo;s Zoo</i> (2022).</p>")


def limits_section(summary, table=()):
    """D-28 item 1, disclosed (option B): the page's pooled baseline beside
    the effort-corrected one, every figure from summary.json."""
    h, e = summary["headline"], summary["effort_check"]
    c = e["corrected"]
    sh = e["amniote_share_of_fit"]
    off = e["offsets_log10"]

    def x(p):
        return f"&times;{10 ** off[p]['amniote']:.2f}"
    dr = e["dropped"]
    runs = (h, c, dr)
    gs = {(g["rank"], g["group"]): g for g in csv.DictReader(open(
        os.path.join(OUT, "group_summary.csv"), encoding="utf-8"))}
    amph = float(gs[("class", "Amphibia")]["geomean_lq_class"])
    uro = float(gs[("order", "Urodela")]["geomean_lq_class"])
    rows = [
        ("Birds against mammals of equal mass",
         *[f"{x['bird_mammal_1kg']:.1f}&times;" for x in runs]),
        ("Mammal record lifespan predicted at 1 kg",
         *[f"{x['mammal_1kg_yr']:.1f} yr" for x in runs]),
    ]
    by = {r["name"]: r for r in table}

    def label(sp):
        r = by.get(sp)
        if not r or sp == "Human":
            return sp
        return (f"{sp} ({float(r['maximum']):g} years at "
                f"{float(r['mass_g']):g} grams)")
    for sp in ("Human", "Brandt's bat", "Naked mole-rat"):
        rows.append((label(sp),
                     *[f"{x['species'][sp]:.1f}&times;" for x in runs]))

    def rk(x, k):
        i, o = _order(x["orders"], k)
        return "too few to rank" if o is None else f"{o[1]:.2f} (#{i + 1})"
    for k, nm in (("Chiroptera", "Bats"), ("Primates", "Primates"),
                  ("Monotremata", "Monotremes"), ("Galliformes", "Galliformes")):
        rows.append((f"{nm}, and rank among orders", *[rk(x, k) for x in runs]))
    tbl = ["<table>", "<tr><th>Figure</th><th>As shown on this page</th>"
           "<th>Corrected for study effort</th>"
           "<th>Briefly watched records left out</th></tr>"]
    tbl += [f"<tr><td>{a}</td><td>{b}</td><td>{d}</td><td>{f}</td></tr>"
            for a, b, d, f in rows]
    tbl.append("</table>")
    return (
        "<h2>Limits</h2>\n\n"
        "<p>The biggest one is who has been watched. A maximum lifespan is a "
        "record, and records grow with the number of animals anyone followed. "
        "The Amniote compilation supplies a lifespan only for species AnAge "
        f"lacks, which are the less-studied ones, and it is "
        f"{sh['Mammalia']:.0%} of the mammal baseline, {sh['Reptilia']:.0%} of "
        f"the reptile one and {sh['Aves']:.0%} of the bird one. Where both "
        "databases carry a species the audit found they agree (median "
        "difference zero), but at equal mass within a "
        f"family an Amniote-only record sits at {x('Mammalia')} the lifespan "
        f"of an AnAge record resting on a medium number of animals (AnAge "
        f"sorts its records from tiny to huge by how many animals stand "
        f"behind them) in mammals, "
        f"{x('Reptilia')} in reptiles and {x('Aves')} in birds. That pulls "
        "each baseline down, so every well-studied species above it reads "
        "high. The figures on this page keep the pooled baseline. The "
        "site&rsquo;s October 2026 quality audit measured the gap and ran two "
        "checks, both rebuilt in <code>build_lq.py</code> and run on every "
        "build. The first rescales every record whose source&rsquo;s offset "
        "can be measured (Amniote, and AnAge by sample size; not the "
        "hand-checked rows, FishBase or AmphiBIO) to the medium level and "
        "re-runs the same fits. The second, cruder, "
        "leaves out every record resting on few or an unknown number of "
        f"animals, which cuts the mammal line to {dr['n_mammals']} species "
        "and skews it towards the well-kept ones, so it is a bound rather "
        "than a better estimate. The fish and invertebrate lines do not move "
        "in either: they are built from hand-checked and AnAge records "
        "only.</p>\n\n" + "\n".join(tbl) + "\n\n"
        "<p>Relative to other amphibians, the salamanders&rsquo; standing "
        "is smaller than their rank suggests: amphibians as a whole sit "
        f"{amph:.1f} times above the all-animal line, so Urodela&rsquo;s "
        f"{uro:.2f} is about {uro / amph:.1f} times the amphibian "
        "average.</p>\n\n"
        "<p>Under the correction the ranking of orders barely moves: across the "
        f"{e['orders_compared']} orders the two runs share, the rank "
        f"correlation is {e['order_rank_spearman']:.3f}, and "
        + ("all ten" if e['top10_shared'] == 10 else _n(e['top10_shared']))
        + f" of the top ten are the same. The figures "
        "for single well-documented mammals, the human&rsquo;s included, are "
        "where the correction bites. The human figure has a further problem "
        "no correction here reaches: it is the best of billions of "
        "documented lives, set against species watched a few dozen times, "
        "so it is an upper bound.</p>\n\n"
        "<p>Three more. Species are treated as independent points, but "
        "related species share their lifespans by descent, and inside mammal "
        "families lifespan rises more slowly with mass than it does across "
        "them, so &ldquo;each tenfold gain in weight&rdquo; is a statement "
        "across groups. The maximum mixes record types: a zoo record for one "
        "species, a banding recapture for another, a compilation figure of "
        "unknown origin for a third, and part of any order&rsquo;s position "
        "is which kind its members have. And some species are in the table "
        "twice under two names (see Data), which counts them twice in their "
        "groups.</p>\n")


def code_section():
    kb = os.path.getsize(ZIP) / 1024 if os.path.exists(ZIP) else None
    size = ("" if kb is None else f" ({kb:,.0f} KB)" if kb < 1024
            else f" ({kb / 1024:.1f} MB)")
    return ("<h2>The code</h2>\n\n"
            "<p>The merge of the six lifespan databases, the fits, the "
            "study-effort check behind Limits, the species and group tables, "
            "and the visualiser: "
            f'<a href="downloads/longevity-code.zip">longevity-code.zip</a>'
            f"{size}.</p>\n")


def main(apply=False):
    summary, report, rows = load()
    global SUMMARY
    SUMMARY = summary
    t = open(PAGE, encoding="utf-8").read()
    table0 = list(csv.DictReader(open(os.path.join(OUT, "lq_table.csv"),
                                      encoding="utf-8")))
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

    sub(r'<h1>.*?</h1>\s*<p class="dim">.*?</p>',
        lambda m: headline(summary, table0), "headline and standfirst")

    def desc(m):
        h1 = re.search(r"<h1>(.*?)</h1>", headline(summary, table0)).group(1)
        return (f'{m.group(1)}"{h1}. Lifespan against body mass for '
                f'{fmt(n)} species, and how much the answer depends on which '
                f'animals were watched.">')
    sub(r'(<meta (?:name|property)="(?:og:)?description" content=)"[^"]*">',
        desc, "meta descriptions", count=2)

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
        ec = summary["effort_check"]["corrected"]["bird_mammal_1kg"]
        sub(r"Birds come out\s+about [\d.]+ times longer-lived than mammals"
            r" of equal mass(?: \([\d.]+ once[^)]*\))?",
            f"Birds come out\nabout {ratio:.1f} times longer-lived than "
            f"mammals of equal mass ({ec:.1f} once the mammal baseline is "
            f"corrected for study effort; see Limits)", "bird/mammal ratio")
    rej = (summary.get("rejected_fits") or {}).get("Amphibia", "")
    mr = re.search(r"r2=([\d.]+), n_eff=(\d+)", rej)
    if mr:
        sub(r"The amphibian regression returns an r\u00b2 of [\d.]+ across [\w\-]+ (?:amphibian )?species",
            f"The amphibian regression returns an r\u00b2 of {float(mr.group(1)):.2f} "
            f"across {mr.group(2)} amphibian species", "amphibian rejection")
    groups = list(csv.DictReader(open(os.path.join(OUT, "group_summary.csv"),
                                      encoding="utf-8")))
    orders = [g for g in groups if g["rank"] == "order"
              and int(g["n_species"]) >= 4 and g["geomean_lq_class"]]
    sub(r"Of the \d+ orders holding four or more (?:grade-A or B )?species",
        f"Of the {len(orders)} orders holding four or more species",
        "order count in prose")
    sub(r"All \d+ orders holding four or more (?:grade-A or B )?species",
        f"All {len(orders)} orders holding four or more grade-A or B species",
        "order count in caption")
    table = list(csv.DictReader(open(os.path.join(OUT, "lq_table.csv"),
                                     encoding="utf-8")))
    sub(r"<p>Of the \d+ orders holding four or more (?:grade-A or B )?species.*?</p>",
        lambda m: groups_paragraph(groups, table), "groups paragraph")
    sub(r"<p>The highest quotients against their own group.*?</p>",
        lambda m: outcome_paragraph(table), "what-comes-out paragraph")
    # _INSIGHT rule 4: the margin rail is gone (R5, 2026-10-24). A rail put
    # back by hand would carry typed quotients nothing rewrites.
    if "marginalia" in t:
        changes.append("MISSED: a margin rail is back on the page")
    lo = min(float(r["mass_g"]) for r in rows if r["mass_g"])
    hi = max(float(r["mass_g"]) for r in rows if r["mass_g"])
    r = float(f"{hi / lo / 1e12:.1g}")
    sub(r"run from a\s+(?:microscopic )?rotifer.+? to a blue whale (?:at|of) [\d,]+ tonnes, .+?(?:orders of\s+magnitude|to one)",
        f"run from a\nmicroscopic rotifer of {mass_str(lo)} to a blue whale of "
        f"{mass_str(hi)}, a range in body mass of about {r:g} trillion to one",
        "mass range in intro")

    # the explainer figure, once, after the quotient definition
    if 'lq_explained.png' not in t:
        anchor = ("<p>It is built by analogy with the encephalisation "
                  "quotient")
        fig = ('<img class="fig wide" src="assets/lq_explained.png" '
               'alt="Three animals of increasing mass, with the lifespan the '
               'allometry predicts beside the lifespan actually observed, and '
               'the quotient that falls out.">\n'
               '<p class="small">Mass rises left to right and so does the '
               'prediction, because the line only rises with size. The '
               'animals scatter above and below it, and the quotient '
               'measures by how much.</p>\n\n')
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
             lambda: arithmetic_section(summary, rows), "arithmetic section"),
            ("<h2>Limits</h2>", lambda: limits_section(summary, table0),
             "limits section"),
            ("<h2>The code</h2>", code_section, "code section")):
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
