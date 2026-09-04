"""
Attach citations to the project pages.

Every claim on this site that came from somewhere should say where. This walks
each project page, drops a superscript marker after the specific sentence a
source supports, and appends a Sources section listing them.

The markers are anchored to phrases rather than to positions, so re-running
after an edit does not scatter them: if the phrase moved, the marker moves with
it; if the phrase is gone, the script says so instead of silently dropping the
reference. That last part matters - a citation list that quietly loses entries
is worse than none, because it still looks complete.

Run:
    python3 add_citations.py            # report what it would do
    python3 add_citations.py --apply
"""

import argparse
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")

# For each page: the reference list, and for each reference the phrase in the
# prose it supports. The phrase must be unique on the page.
PAGES = {
    "heat.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("resistive electric boiler",
         'Zuberi, Hasanbeigi &amp; Morrow, <i>Electrification of industrial '
         'process heat</i>, Lawrence Berkeley National Laboratory, 2021.',
         "Electric boiler efficiency and capital cost ranges."),
        ("At a gas price of $3.50",
         'U.S. Energy Information Administration, <i>Electric Power Monthly</i> '
         'Table 5.6.A and the Natural Gas Industrial Price series.',
         "Texas industrial electricity and gas prices."),
        ("grid carbon intensity",
         'U.S. EPA, <i>eGRID</i> 2022, ERCOT subregion output emission rates; '
         'and EPA, <i>Emission Factors for Greenhouse Gas Inventories</i>, '
         'stationary combustion.',
         "Grid carbon intensity and the natural gas emission factor."),
        ("levelised cost",
         'NREL, <i>Annual Technology Baseline</i> 2024, financial assumptions.',
         "Discount rate, economic life and the levelisation method."),
    ],
    "storage.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("hourly prices",
         'ERCOT, <i>Day-Ahead Market Settlement Point Prices</i>, historical '
         'archive.',
         "The price shape the synthetic year is calibrated to reproduce."),
        ("cycling cost",
         'Mongird <i>et al.</i>, <i>Grid Energy Storage Technology Cost and '
         'Performance Assessment</i>, Pacific Northwest National Laboratory, '
         '2020.',
         "Degradation cost per megawatt hour of throughput, and round-trip "
         "efficiency."),
        ("linear programming",
         'Sioshansi, Denholm, Jenkin &amp; Weiss, <i>Energy Economics</i>, '
         '2009 - estimating the value of electricity storage under '
         'perfect foresight.',
         "The perfect-foresight dispatch formulation and its upper-bound "
         "character."),
        ("four hours",
         'Denholm <i>et al.</i>, <i>The Four-Hour Challenge</i>, National '
         'Renewable Energy Laboratory, 2019.',
         "Why duration value flattens past four hours."),
    ],
    "longevity.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("encephalisation quotient",
         'Jerison, <i>Evolution of the Brain and Intelligence</i>, Academic '
         'Press, 1973.',
         "The quotient construction this model borrows."),
        ("AnAge build 15",
         'Tacutu <i>et al.</i>, <i>Nucleic Acids Research</i> 46:D1083, '
         '2018 - the AnAge database of animal ageing and longevity.',
         "Maximum lifespan and adult body mass for most species in the table."),
        ("ocean quahog",
         'Butler <i>et al.</i>, <i>Palaeogeography, Palaeoclimatology, '
         'Palaeoecology</i>, 2013 - the 507-year <i>Arctica islandica</i>.',
         "The longest-lived non-colonial animal recorded."),
        ("rockfishes of Sebastidae",
         'Nielsen <i>et al.</i>, <i>Science</i> 353:702, 2016 (Greenland '
         'shark, eye-lens radiocarbon); Cailliet <i>et al.</i>, '
         '<i>Experimental Gerontology</i> 36:739, 2001 (rockfish otolith '
         'ageing).',
         "The extreme fish lifespans, and the dating methods behind them."),
        ("bats of Chiroptera",
         'Wilkinson &amp; Adams, <i>Biology Letters</i>, 2019 - recent '
         'advances in the biology of bat ageing.',
         "Why flight and longevity travel together."),
        ("Amniote life-history database",
         'Myhrvold <i>et al.</i>, <i>Ecology</i> 96:3109, 2015 - an amniote '
         'life-history database for comparative analyses with birds, mammals '
         'and reptiles.',
         "Lifespan and body mass for most birds, mammals and reptiles here."),
        ("PanTHERIA",
         'Jones <i>et al.</i>, <i>Ecology</i> 90:2648, 2009 - PanTHERIA, a '
         'species-level database of life history, ecology and geography of '
         'extant and recently extinct mammals.',
         "Mammalian maximum longevity and adult body mass."),
        ("AmphiBIO",
         'Oliveira <i>et al.</i>, <i>Scientific Data</i> 4:170123, 2017 - '
         'AmphiBIO, a global database for amphibian ecological traits.',
         "Amphibian longevity and body mass."),
        ("FishBase v25.04",
         'Froese &amp; Pauly (eds.), <i>FishBase</i>, v25.04 snapshot, '
         'distributed as parquet by rOpenSci. CC BY-NC.',
         "Maximum age and weight for fish, graded C throughout."),
        ("AVONET",
         'Tobias <i>et al.</i>, <i>Ecology Letters</i> 25:581, 2022 - AVONET, '
         'morphological, ecological and geographical data for all birds.',
         "Body mass used only to fill gaps for birds already aged."),
    ],
    "climate-cost.html": [
        ("Anchor phrase", "Source", "What it supports"),
        ("published literature",
         'Poore &amp; Nemecek, <i>Science</i> 360:987, 2018 - reducing food’s '
         'environmental impacts through producers and consumers.',
         "Per-kilogram footprints and the spread within each food."),
        ("fertiliser",
         'IPCC, <i>2019 Refinement to the 2006 Guidelines for National '
         'Greenhouse Gas Inventories</i>, Volume 4 Chapter 11 - direct and '
         'indirect nitrous oxide from managed soils.',
         "The emission factor for nitrogen applied to soils."),
        ("methane",
         'IPCC, <i>Sixth Assessment Report</i>, Working Group I Chapter 7, '
         'Table 7.15 - global warming potentials.',
         "Methane at 27 and nitrous oxide at 273 over a century."),
        ("tonne-kilometre",
         'UK Department for Energy Security and Net Zero, <i>Greenhouse gas '
         'reporting: conversion factors</i>, 2023.',
         "Freight emission factors by mode."),
        ("allocation",
         'ISO 14044:2006, <i>Environmental management - Life cycle assessment '
         '- Requirements and guidelines</i>, clause 4.3.4.',
         "The allocation hierarchy: avoid, then physical, then economic."),
        ("Flysjö",
         'Flysjö, Cederberg, Henriksson &amp; Ledgard, <i>International '
         'Journal of Life Cycle Assessment</i> 16:420, 2011 - how does '
         'co-product handling affect the carbon footprint of milk? Table 1.',
         "Milk-to-meat allocation by physical (85-86%), economic (88-92%), "
         "protein (93-94%) and mass (98%) bases, and 63-76% by system "
         "expansion."),
        ("International Dairy Federation",
         'International Dairy Federation, <i>A common carbon footprint '
         'approach for the dairy sector</i>, Bulletin 479, 2015, pp. 34-36.',
         "The physical allocation formula AF = 1 - 6.04 x BMR and the 88% "
         "milk share at a typical beef-to-milk ratio of 0.02."),
        ("Lunesu",
         'Lunesu, Correddu, Carta, Sechi, Farina &amp; Pulina, <i>Animals</i> '
         '15:3546, 2025 - attributing farm-to-slaughter emissions to hides.',
         "Hide share of the animal: 2.7% by economic allocation (2023 mean), "
         "5.9% by live weight (range 4.2-6.9%)."),
    ],
}


def strip(t):
    """Remove any citations already present, so the script is re-runnable."""
    t = re.sub(r'<sup class="cite".*?</sup>', "", t, flags=re.S)
    t = re.sub(r'\n<h2>Sources</h2>.*?</ol>\n\n', "\n", t, flags=re.S)
    return t


def build(page, refs):
    path = os.path.join(SITE, page)
    if not os.path.exists(path):
        return None, [f"{page} does not exist"]
    t = strip(open(path, encoding="utf-8").read())

    problems = []
    body_end = t.find("<footer")
    if body_end < 0:
        return None, [f"{page} has no footer to insert before"]

    # Only the text between tags is eligible. Matching anywhere would let a
    # phrase inside an attribute collect a marker, which silently corrupts the
    # tag: the first version of this put a superscript inside a <meta
    # description> and the reference simply never appeared on the page.
    body = t[:body_end]
    spans = []
    depth_pos = 0
    for m in re.finditer(r"<[^>]*>", body):
        if m.start() > depth_pos:
            spans.append((depth_pos, m.start()))
        depth_pos = m.end()
    if depth_pos < len(body):
        spans.append((depth_pos, len(body)))

    # ...and only inside <main>, so nothing in the nav or head is annotated.
    # "<main", not "<main>": the deslop pass gave <main> a class, and an exact
    # match then failed silently, which let the nav become eligible for markers.
    main_at = t.find("<main")
    spans = [(a, b) for a, b in spans if main_at < 0 or a >= main_at]

    def find_in_text(phrase):
        pat = re.compile(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)")
        for a, b in spans:
            m = pat.search(body, a, b)
            if m:
                return m.end()
        return None

    # Number by where they appear, not by the order they sit in this file. A
    # reader meeting marker 5 before marker 2 assumes something is broken, and
    # they are right to: numbered references run in order of first appearance.
    found = []
    for phrase, src, what in refs[1:]:
        pos = find_in_text(phrase)
        if pos is None:
            problems.append(f"{page}: phrase not found in prose - {phrase!r}")
            continue
        found.append({"pos": pos, "src": src, "what": what,
                      "phrase": phrase})
    found.sort(key=lambda f: f["pos"])
    for i, f in enumerate(found, 1):
        f["n"] = i

    # Insert from the back so earlier offsets stay valid.
    for f in sorted(found, key=lambda f: -f["pos"]):
        marker = (f'<sup class="cite" id="cr{f["n"]}">'
                  f'<a href="#ref{f["n"]}">{f["n"]}</a></sup>')
        t = t[:f["pos"]] + marker + t[f["pos"]:]

    body_end = t.find("<footer")
    items = "".join(
        f'<li id="ref{f["n"]}"><span class="src">{f["src"]}</span>'
        f'<span class="what">{html.escape(f["what"])}</span></li>'
        for f in found)
    block = (f'\n<h2>Sources</h2>\n'
             f'<p class="small">Numbered markers in the text above point here. '
             f'Emission factors, cost ranges and lifespan figures are '
             f'representative values from these sources, not measurements '
             f'made for this project.</p>\n'
             f'<ol class="refs">{items}</ol>\n\n')
    t = t[:body_end] + block + t[body_end:]
    return t, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    allprob, done = [], 0
    for page, refs in PAGES.items():
        out, probs = build(page, refs)
        allprob += probs
        if out is None:
            continue
        placed = out.count('class="cite"')
        print(f"  {page:22s} {placed} of {len(refs)-1} markers placed")
        if a.apply:
            open(os.path.join(SITE, page), "w", encoding="utf-8").write(out)
            done += 1

    if allprob:
        print("\n  problems:")
        for p in allprob:
            print(f"    {p}")
    if a.apply:
        print(f"\n  wrote {done} page(s)")
    else:
        print("\n  report only. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
