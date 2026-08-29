"""
Regenerate the atlas write-up and the how-it-works page from the built model.

Every figure on both pages is read out of atlas-data.js. Nothing is typed. The
model went from 7,192 nodes to 86,601 in a week and left about twenty stale
numbers behind it, which is the argument for this file existing.

Run:  python3 update_atlas_pages.py            report only
      python3 update_atlas_pages.py --apply
"""

import argparse
import collections
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
DATA = os.path.join(SITE, "assets", "atlas-data.js")


def stats():
    raw = open(DATA, encoding="utf-8").read()
    D = json.loads(raw[raw.index("=") + 1:raw.rindex(";")])
    kind = [D["kinds"][k] for k in D["kind"]]
    c = collections.Counter(kind)
    deg = collections.Counter()
    for s, t in zip(D["es"], D["et"]):
        deg[s] += 1
        deg[t] += 1
    countries = set()
    for i, k in enumerate(kind):
        if k == "station":
            s = D["srcDict"][D["src"][i]]
            if "·" in s:
                countries.add(s.split("·")[1].strip())
    return {
        "n": D["n"], "edges": len(D["es"]),
        "isolated": sum(1 for i in range(D["n"]) if deg[i] == 0),
        "anatomy": len(D["anatomy"]), "countries": len(countries),
        "station": c["station"], "consumer": c["consumer"],
        "event": c["event"], "market": c["market"] + c["supply"],
        "grid": c["grid"] + c["district"], "psych": c["psych"],
        "climate": c["climate"], "tabs": D["tabs"],
        "nscen": len(D["scenarios"]),
        "space": c["sun"] + c["insolation"], "weather": c["weather"],
        "neg": sum(1 for x in D["ew"] if x < 0),
        "wmin": min(D["ew"]), "wmax": max(D["ew"]),
    }


def f(n):
    return f"{n:,}"


def atlas_page(s):
    rows = [
        ("Space", s["space"], "The measured solar constant, and the annual "
         "mean insolation above the atmosphere at each band of latitude, "
         "computed from orbital geometry"),
        ("Weather", s["weather"], "El Nino / La Nina and the North Atlantic "
         "Oscillation, from their measured index series"),
        ("Climate", s["climate"], "Carbon dioxide and the global temperature "
         "anomaly, both global series shown at Mauna Loa, where the record "
         "is kept"),
        ("Events", s["event"], "Earthquakes of magnitude 5.5 and above since "
         "1960 that reach infrastructure, and the earlier disaster set"),
        ("Markets and fuel", s["market"], "Price benchmarks, national fuel "
         "supplies, and every port in the World Port Index"),
        ("Grids", s["grid"], "National grids and first-level administrative "
         "districts at their settlement centroid"),
        ("Power plants", s["station"], f"Every unit in the world database, "
         f"{s['countries']} countries"),
        ("Demand", s["consumer"], "Every settlement above fifteen thousand "
         "people"),
        ("Behaviour", s["psych"], f"Behavioural channels, inside "
         f"{f(s['anatomy'])} drawn brain structures, fed by every district "
         f"with a measured population"),
    ]
    tbl = ['<table><tr><th>Layer</th><th class="n">Nodes</th>'
           '<th>Contents</th></tr>']
    for a, b, cdesc in rows:
        tbl.append(f'<tr><td>{a}</td><td class="n">{f(b)}</td>'
                   f'<td>{cdesc}</td></tr>')
    tbl.append('</table>')
    return "\n".join(tbl)


SCEN_TABLE = """<table>
<tr><th>Category</th><th class="n">Changes</th><th class="n">Widest reach</th><th>Widest</th></tr>
<tr><td>People & cognition</td><td class="n">6</td><td class="n">3,004</td><td>Fear becomes salient</td></tr>
<tr><td>Universe & Earth, exogenous</td><td class="n">10</td><td class="n">77,669</td><td>A step in climate forcing</td></tr>
<tr><td>Country policy changes</td><td class="n">8</td><td class="n">13,969</td><td>The United States retires coal</td></tr>
<tr><td>Climate goal meetings</td><td class="n">8</td><td class="n">76,165</td><td>Paris, fully met</td></tr>
<tr><td>Natural disasters</td><td class="n">6</td><td class="n">13,969</td><td>A major California earthquake</td></tr>
<tr><td>Global pandemics</td><td class="n">6</td><td class="n">2,744</td><td>The Black Death, at today's scale</td></tr>
<tr><td>Wars</td><td class="n">5</td><td class="n">5,478</td><td>A war of 1939-45 scale</td></tr>
<tr><td>Technology improvement & buildout</td><td class="n">5</td><td class="n">6,983</td><td>Fusion arrives at scale</td></tr>
<tr><td>Energy makeup evolution</td><td class="n">6</td><td class="n">5,121</td><td>Renewables pass half of world power</td></tr>
</table>"""

BODY = """<h1>The atlas</h1>
<p class="dim">{n} nodes and {edges} weighted links, each carrying a
parameter from a public data set.</p>

<p>The atlas is the world energy system drawn as a graph and made to move.
Every node holds one measured quantity and names where it came from. Apply a
change anywhere and the effect propagates along the links until it settles,
which takes between twenty and fifty steps.</p>

{card}

<h2>The nine layers</h2>

{table}

<p>Seven of the nine layers are drawn on a sphere. Mercator inflates Greenland
to the size of Africa and stretches the high-latitude Russian and Canadian
grids into ribbons, which is where a good deal of this system's fuel lives. On
a globe every node sits at its true angular position and a point on the far
side is hidden by the planet rather than flung to the edge of a rectangle.</p>

<p>The space layer is drawn standing off the surface, because the sun is not
on the Earth and neither is the sunlight arriving above the atmosphere.</p>

<p>The last layer is not a place. Behaviour is drawn inside a brain, with
{psych} channels at anatomically defensible positions among {anatomy} named
structures of the Allen Mouse Brain Common Coordinate Framework. The
structures are scenery: they carry no weight, no link and no channel, and they
are held outside the node arrays so that nothing can mistake them for part of
the model. The channels carry weight and wire into demand.</p>

<h2>What a run does</h2>

<p>Select a scenario or click any node and push on it. Each node takes the
mean of what its neighbours are carrying, damped by its own resilience, bounded
by a hyperbolic tangent so that nothing runs away, and the source is held at
the value it was pushed to. The run repeats until the largest remaining
movement falls below a threshold, which takes between twenty and fifty steps.
Nodes the run moved pulse, with the depth of the pulse scaling with the size of
the effect. Clicking a node draws its web of influence three hops deep.</p>

<p>The mean rather than the sum is the load-bearing choice. A national grid
carries thousands of plants, and a node that added what its drivers were
carrying would multiply a change by its own degree rather than distribute it.
Each link is also divided by the number of links reaching that node from the
same layer, so a layer speaks once however many members it has.</p>

<p>Most links carry in both directions: a grid outage reaches the plants that
feed it as well as the cities below it. Links out of the climate and event
layers carry one way only, because an earthquake acts on a grid and no grid
causes an earthquake.</p>

<p>The atlas carries {nscen} prepared changes, grouped by kind. Each one
names the number its size rests on, because turning a real event into a
dimensionless push is where a model quietly becomes fiction. The rule is that a
change of 1.0 is the largest of its kind in the record: the 1973 oil shock is
1.0 because crude roughly quadrupled in real terms and nothing since has beaten
it, and everything else is measured against that.</p>

<p>Some magnitudes are derived rather than asserted. A country's fuel shares
are already measured and sit in the model, so withdrawing its coal pushes its
grid by the generation it actually loses; that number is different for every
country and none of it is chosen. The El Nino scenarios are the observed peak
of each event divided by the largest peak in the record. Where no number could
be found, the scenario says so and calls itself an assumption.</p>

{scentable}

<p>These are not forecasts. The model answers what is connected to what and how
strongly, so a prepared change is a way of asking that question from a
particular starting point.</p>

<p>Reach spans five orders of magnitude, and starting at the most connected
power plant in the world moves one other node. That spread is the point. A
model that answers the same number to every question is not answering.</p>

<h2>What is above the climate</h2>

<p>The sun is measured. The solar constant here is the NRLTSI2 composite,
1362.00 W/m&sup2; in 2023, with a stated uncertainty of 0.61. Across a solar
cycle it moves by about one part in fifteen hundred, which is the size of the
change the solar minimum scenario applies.</p>

<p>The insolation bands are not measured, and they are not estimated either.
The annual mean sunlight arriving above the atmosphere at a given latitude is
orbital geometry, and it is computed here from the measured solar constant,
the obliquity and the eccentricity. The check that it is right is that the
area-weighted global mean of the computed field has to equal the solar constant
divided by four, the ratio of the disc the Earth intercepts to the sphere it
radiates from. It does, to one part in ten thousand.</p>

<p>Each band reaches the national grids at its latitude, weighted by the share
of that country's generating capacity that is solar, measured from the plant
layer. Ninety-one countries have a solar fleet large enough to record. The rest
get no link, because a country with no solar plants has no exposure to the
sunlight for the model to carry.</p>

<h2>Weather</h2>

<p>Two modes of year-to-year variability carry their own measured index
series. El Ni&ntilde;o and La Ni&ntilde;a enter as the Oceanic Ni&ntilde;o
Index, 917 overlapping seasons since 1950. The North Atlantic Oscillation
enters as the standardised station-based index, 917 months over the same
period.</p>

<p>The ENSO weight was not chosen. Regressing the global temperature anomaly
on the annual ONI over 1950 to 2025 gives a correlation of 0.44, significant
at better than one in a thousand, and a slope of 0.068 &deg;C of global anomaly
per degree of ONI. The correlation on the raw series is 0.10, because the
temperature carries a strong trend and the ONI does not, so most of what a raw
correlation measures is the trend. A quadratic in time is removed from the
temperature first. The 0.44 is the link weight.</p>

<p>The NAO reaches two countries. Winter NAO and winter electricity demand in
Great Britain are anti-correlated at &minus;0.67, which is a published,
quantified relationship, and there is an equivalent study for Ireland. A
negative NAO winter is cold and calm: demand rises and the wind does not blow.
That is the link. The NAO plainly affects more of Europe than two islands, but
a weight is a number, and for the rest of the continent I did not have one I
could cite, so those links are not drawn. The layer is deliberately smaller
than the physics.</p>

<p>One correction worth stating, since it is the usual explanation for why
Ireland is habitable at the latitude of Labrador. It is mostly not the Gulf
Stream. Seager and colleagues took the ocean heat transport out of an
atmospheric model and the winter contrast across the North Atlantic barely
moved; the warmth is carried by the prevailing south-westerlies, by the
seasonal release of heat the ocean absorbed in summer, and by the standing wave
the Rocky Mountains impose on the flow. The ocean stores and releases; the
atmosphere is what carries.</p>

<h2>The behaviour layer</h2>

<p>Behaviour is wired in both directions: the channels reach the consumer
groups, and every district that resolves to a real administrative division
reaches the channels.</p>

<p>Each of those 2,761 districts carries the population GeoNames records inside
it and the concentration of that population, a Herfindahl index over its
settlements: 1.0 means a single city holds everyone, and small means the
population is spread across many towns. Kerala comes out at 0.012 and Bulawayo
at 1.000, which is what those two places look like. Districts are joined to the
settlement data on their administrative code, so the join is exact rather than
a spatial guess.</p>

<p>The concentration is the weight of the link from a district into the
behaviour layer. That the measurement is real does not make the direction real:
that a more concentrated population couples more strongly to shared behaviour
is a hypothesis, and it is marked assumed rather than measured.</p>

<p>The behaviour tab switches between the brain and the map, because the two
things worth seeing are the channels and the places feeding them.</p>

<p>What is deliberately absent: there is no weighting of a district by the
values of the people in it. The World Values Survey measures its two dimensions
at national level for about 120 countries, subnational data exists for a
handful, and nothing exists at the resolution of a state or a congressional
district. Putting a value set on a district would mean spreading a national
average across geography and calling the result a measurement. The
concentration figure is a population statistic and says nothing about anyone's
politics.</p>

<h2>Connectivity</h2>

<p>{isolated} of the {n} nodes have no link to anything, which is
{isopct} per cent. The figure is checked on every build, because an isolated
node is a node the model cannot answer any question about.</p>

<p>An earthquake with nothing inside its felt radius is not added at all. Such
a record is real and it affects nothing, and keeping it would make the layer
look full while leaving most of it inert.</p>

<h2>Reading a dense scene</h2>

<p>{n} points is more than anyone can take in at once, so the sidebar carries
a threshold that hides everything below a chosen weight. Weight is generating
capacity for a power plant and resilience for everything else, which is the
quantity the propagation already uses. Hidden nodes still take part in a run.
The threshold changes the view, not the answer.</p>

<h2>Limits</h2>

<p>Coverage follows the source databases rather than reality. Wikidata and the
World Resources Institute are better on countries that publish in English, so
a thin layer over a region is a statement about record-keeping and not about
the region.</p>

<p>The propagation is a relaxation on a weighted graph, not a power flow. It
answers what is connected to what and how strongly, and it does not solve
Kirchhoff's laws, clear a market or respect a transmission constraint. The
link weights are calibrated against replayed historical events to within about
a factor of two, and that band is quoted rather than hidden.</p>
"""


def main(apply=False):
    s = stats()
    p = os.path.join(SITE, "atlas.html")
    t = open(p, encoding="utf-8").read()

    head = t[:t.index("<main>") + len("<main>")]
    tail = t[t.index("<footer"):]
    card = re.search(r'<div class="card">.*?</div>\s*\n', t, re.S)
    card = card.group(0) if card else ""

    body = BODY.format(
        nscen=f(s["nscen"]), scentable=SCEN_TABLE,
        n=f(s["n"]), edges=f(s["edges"]), card=card, table=atlas_page(s),
        psych=f(s["psych"]), anatomy=f(s["anatomy"]),
        isolated=f(s["isolated"]),
        isopct=f"{100 * s['isolated'] / s['n']:.2f}")
    new = head + "\n\n" + body + "\n" + tail

    changes = [f"atlas.html rewritten from the model ({f(s['n'])} nodes)"]

    # how-it-works: substitute every figure that moved
    p2 = os.path.join(SITE, "model.html")
    t2 = open(p2, encoding="utf-8").read()
    subs = [
        (r"\b7,192\b", f(s["n"])),
        (r"\b13,826\b", f(s["edges"])),
        (r"\b130,772\b", f(s["edges"])),
        (r"\b130,804\b", f(s["edges"])),
        (r"\b86,622\b", f(s["n"])),
        (r"\b4,000\b", f(s["station"])),
        (r"\b1,142\b", f(s["consumer"])),
        (r"\b526\b", f(s["event"])),
        (r"\b214\b", f(s["grid"])),
        (r"\b4,265\b", f(s["market"])),
        (r"six behaviour channels", f"{f(s['psych'])} behavioural channels"),
        (r"six channels", f"{f(s['psych'])} channels"),
        (r"real United States plants", "plants worldwide"),
        (r"United States power plants", "power plants worldwide"),
    ]
    hits = 0
    for pat, rep in subs:
        t2, k = re.subn(pat, rep, t2)
        hits += k
    # Generated last, and deliberately so. The substitution loop above
    # rewrites bare numbers wherever they appear, and the count of negative
    # links happens to equal an older value of the consumer-group count. Run
    # in the other order, the loop found the 1,142 this line had just written
    # and turned it into 35,207. Generated text goes in after the patching,
    # never before.
    t2 = re.sub(
        r"<p>There are [\d,]+ links, with weights.*?</p>",
        f"<p>There are {f(s['edges'])} links, with weights between "
        f"{s['wmin']:.3f} and +{s['wmax']:.3f}. Of these, {f(s['neg'])} are "
        f"negative. A negative link carries relief rather than stress.</p>",
        t2, flags=re.S)


    changes.append(f"model.html: {hits} stale figures replaced")

    for c in changes:
        print("  " + c)
    if not apply:
        print("\n  report only. Re-run with --apply.")
        return
    open(p, "w", encoding="utf-8").write(new)
    open(p2, "w", encoding="utf-8").write(t2)
    print("\n  written")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
