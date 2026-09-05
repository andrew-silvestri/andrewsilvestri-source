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
        "_kind": kind, "_D": D,
        "bykind": dict(c),
        "ports": sum(1 for i, k in enumerate(kind) if k == "market"
                     and "Port Index" in D["srcDict"][D["src"][i]]),
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
        **run_stats(D, kind, deg),
        **provenance_stats(D, kind),
    }


def run_stats(D, kind, deg):
    """What the engine actually does, measured, for the sentences that used
    to guess it: how many rounds the sixty scenarios take to settle, how far
    they reach, and what pushing the most connected power plant moves.
    The engine is build_throughlines.engine(), the figures' copy, which
    tests/test_parity.py holds equal to the browser's."""
    import numpy as np
    from build_throughlines import engine
    run, _ = engine(D)
    ids = {k: int(v) for k, v in D["idMap"].items()}
    steps, reach = [], []
    for sc in D["scenarios"].values():
        sh = {ids[i]: a for i, a in sc["shocks"].items() if i in ids}
        if not sh:
            continue
        st, hist = run(sh)
        steps.append(len(hist) - 1)
        reach.append(int((np.abs(st) >= 0.02).sum()))
    plant = max((i for i, k in enumerate(kind) if k == "station"), key=lambda i: deg[i])
    st, hist = run({plant: 1.0})
    moved = int((np.abs(st) >= 0.02).sum()) - 1     # besides itself
    return {
        "steps_min": min(steps), "steps_max": max(steps),
        "steps_median": int(np.median(steps)), "steps_under20": sum(1 for x in steps if x < 20),
        "reach_min": min(reach), "reach_max": max(reach),
        "reach_orders": np.log10(max(reach) / min(reach)),
        "plant_name": D["name"][plant], "plant_deg": deg[plant], "plant_moved": moved,
        "plant_steps": len(hist) - 1,
    }


def provenance_stats(D, kind):
    """Which nodes carry a measured quantity and which carry an assumption,
    read from each node's own source string."""
    src = [D["srcDict"][i] for i in D["src"]]
    assumed_consumer = sum(1 for s_, k in zip(src, kind) if k == "consumer" and "literature" in s_)
    modelled_psych = sum(1 for s_, k in zip(src, kind) if k == "psych" and "model of" in s_)
    ports = sum(1 for s_, k in zip(src, kind) if k == "market" and "Port Index" in s_)
    at_origin = sum(1 for i in range(D["n"]) if D["lat"][i] == 0 and D["lon"][i] == 0)
    at_origin_kinds = sorted({kind[i] for i in range(D["n"]) if D["lat"][i] == 0 and D["lon"][i] == 0})
    return {"assumed_consumer": assumed_consumer, "modelled_psych": modelled_psych,
            "ports": ports, "at_origin": at_origin, "at_origin_kinds": at_origin_kinds,
            "assumed_total": assumed_consumer + modelled_psych + ports}


def f(n):
    return f"{n:,}"


def atlas_page(s):
    # Row order is the layer diagram's (build_layer_diagram.LAYERS): the
    # figure's band order is derived - it is the one order of the nine that
    # minimises arc crossings, checked over every order by its audit - and
    # the table's used to be arbitrary. Two orders for the same nine layers
    # on one page read as one of them being wrong, so the one with a reason
    # wins and the other follows it. The caption under the figure says so.
    from build_layer_diagram import LAYERS
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
    by_label = {r[0]: r for r in rows}
    if set(by_label) != {g for g, _ in LAYERS}:
        raise SystemExit("the table's layers and the diagram's do not match")
    rows = [by_label[g] for g, _ in LAYERS]
    tbl = ['<table><tr><th>Layer</th><th class="n">Nodes</th>'
           '<th>Contents</th></tr>']
    for a, b, cdesc in rows:
        tbl.append(f'<tr><td>{a}</td><td class="n">{f(b)}</td>'
                   f'<td>{cdesc}</td></tr>')
    tbl.append('</table>')
    return "\n".join(tbl)


# Section 5's two tables, generated from the payload the way section 2's is.
# Until 2026-09-05 they were typed: single inertia values where the payload
# holds ranges, a "grid -> district 0.60 fixed" that is 0.42-0.60, and
# "event -> grid: log10 of the real damage cost" for a layer where 8,733 of
# 9,259 events are USGS earthquakes with no cost at all. The reasons are
# still typed (a payload cannot say why); the numbers are read.
LINK_ROWS = [
    # (source kind, target kind, label, where the weight comes from)
    ("climate", "climate", "Climate system → temperature", "Fixed. The temperature follows the forcing closely."),
    ("market", "market", "Price benchmark → related benchmark", "Observed price correlation."),
    ("supply", "grid", "Fuel supply → national grid", "0.55 × <b>the real share of that fuel in that country's power</b>."),
    ("market", "supply", "Price benchmark → fuel supply", "0.35 + 0.40 × share: higher where the country depends more on that fuel."),
    ("grid", "district", "National grid → district", "0.60 for a district with a measured population, 0.42 for a synthetic filler (build_atlas_global.py)."),
    ("district", "consumer", "District → consumer group", "Fixed."),
    ("event", "grid", "Recorded event → grid", "<b>log10 of the recorded damage cost</b> for the {emdat} EM-DAT events that have one; for the {usgs} USGS earthquakes, which carry no cost, from magnitude and distance (build_atlas_global.py)."),
    ("event", "station", "Recorded event → power plant", "From magnitude and distance; a quake reaches at most twelve nodes inside its felt radius."),
    ("climate", "grid", "Temperature → national grid", "Heating and cooling demand."),
    ("climate", "market", "Temperature → gas and power price", "Heating and cooling demand."),
    ("consumer", "district", "Consumer group → district", "Negative: demand response. Consumers use less when costs rise."),
    ("station", "grid", "Power station → grid", "0.20 + 0.55 × √(capacity ÷ the largest plant); the division by plant count is the engine's fan-in, section 5.3."),
    ("district", "psych", "District → behaviour channel", "Varies by district; set in the brain build."),
    ("psych", "consumer", "Behaviour channel → consumer group", "Fixed."),
]
INERTIA_ROWS = [
    # (kinds, label, reason)
    (("event",), "Recorded event", "0.10 + 0.10 per unit of magnitude above 5: an event happens at once, a great earthquake holds longer."),
    (("market",), "Price benchmark, port", "Benchmarks: <b>set by the real volatility of that price series</b>, a more volatile price reacting faster. Ports: by harbour size class."),
    (("grid",), "National grid", "A grid must balance in seconds."),
    (("supply", "district"), "Fuel supply, district", "Supply chains take weeks."),
    (("consumer",), "Settlement, consumer group", "Settlements: 0.18 + 0.55 × ∛(population ÷ the largest); a city changes more slowly than a town."),
    (("station",), "Power station", "From capacity: a larger plant changes more slowly."),
    (("climate",), "Climate system", "The climate is a slow variable."),
    (("weather",), "Weather mode", "Set per index (build_atlas_global.py)."),
    (("psych",), "Behaviour channel", "0.30 rising by 0.02 per channel: a modelling choice, not a measurement."),
    (("sun", "insolation"), "Sun, insolation", "The sun is held; insolation follows it at once."),
]


def weight_table(D, kind):
    import collections
    rng = collections.defaultdict(list)
    for a, b, w in zip(D["es"], D["et"], D["ew"]):
        rng[(kind[a], kind[b])].append(w)
    src = [D["srcDict"][i] for i in D["src"]]
    emdat = sum(1 for s_, k in zip(src, kind) if k == "event" and "USGS" not in s_)
    usgs = sum(1 for s_, k in zip(src, kind) if k == "event" and "USGS" in s_)
    rows = ['<table><tr><th>Link</th><th class="n">Links</th><th>Weight</th>'
            '<th>Where the weight comes from</th></tr>']
    for a, b, label, why in LINK_ROWS:
        ws = rng.get((a, b))
        if not ws:
            continue
        lo, hi = min(ws), max(ws)
        val = f"{lo:+.2f}" if abs(hi - lo) < 0.005 else f"{lo:+.2f} to {hi:+.2f}"
        rows.append(f'<tr><td>{label}</td><td class="n">{f(len(ws))}</td><td>{val}</td>'
                    f'<td>{why.format(emdat=f(emdat), usgs=f(usgs))}</td></tr>')
    rows.append("</table>")
    return "\n".join(rows)


def inertia_table(D, kind):
    res = D["res"]
    rows = ['<table><tr><th>Node type</th><th>Inertia</th><th>Reason</th></tr>']
    for kinds, label, why in INERTIA_ROWS:
        vals = [r for r, k in zip(res, kind) if k in kinds]
        if not vals:
            continue
        lo, hi = min(vals), max(vals)
        val = f"{lo:.2f}" if abs(hi - lo) < 0.005 else f"{lo:.2f} to {hi:.2f}"
        rows.append(f"<tr><td>{label}</td><td>{val}</td><td>{why}</td></tr>")
    rows.append("</table>")
    return "\n".join(rows)


def model_table(s):
    """model.html section 2, one row per node kind in the payload, in the
    order the layers stack. Until 2026-09-04 this table was the July Julia
    build's README table (7,192 nodes: districts 571, price benchmarks 6,
    behaviour channels 6) with four numbers regex-patched by the rules in
    main() - and one of those rules keyed "National grid" to s["grid"],
    which is grids plus districts (the Grids tab), so the row said 3,546
    for 214. The rows summed to 84,258 under a stated 86,622. Now every row
    is counted from the payload and the total is asserted."""
    k = s["bykind"]
    ports = s["ports"]
    rows = [
        ("Sun", "sun", "The measured solar constant"),
        ("Insolation band", "insolation", "Annual mean insolation above the atmosphere at one band of latitude, computed from orbital geometry"),
        ("Weather mode", "weather", "El Ni&ntilde;o / La Ni&ntilde;a, or the North Atlantic Oscillation, from its measured index series"),
        ("Climate system", "climate", "Carbon dioxide level, or the global temperature anomaly"),
        ("Recorded event", "event", "One earthquake of magnitude 5.5 or more since 1960 that reaches infrastructure, or one earlier recorded disaster"),
        ("Market", "market", f"One traded price benchmark ({f(k['market'] - ports)}), or one port in the World Port Index ({f(ports)})"),
        ("Fuel supply", "supply", "One fuel in one country, with its share of that country's electricity"),
        ("National grid", "grid", "The power system of one country"),
        ("District", "district", "One first-level administrative division, at its settlement centroid"),
        ("Power station", "station", f"One generating unit from the world database, at its recorded coordinate; {s['countries']} countries"),
        ("Consumer group", "consumer", "The demand of one settlement above fifteen thousand people"),
        ("Behaviour channel", "psych", "One behavioural channel, placed in a drawn brain structure and wired into demand"),
    ]
    total = sum(k[kind] for _, kind, _ in rows)
    assert total == s["n"], (total, s["n"], sorted(k))
    assert set(kind for _, kind, _ in rows) == set(k), sorted(k)
    tbl = ['<table>', '<tr><th>Node type</th><th class="n">Count</th><th>What one node is</th></tr>']
    for label, kind, desc in rows:
        tbl.append(f'<tr><td>{label}</td><td class="n">{f(k[kind])}</td><td>{desc}</td></tr>')
    tbl.append(f'<tr><td><b>Total</b></td><td class="n"><b>{f(total)}</b></td><td></td></tr>')
    tbl.append('</table>')
    return "\n".join(tbl)


def scen_rows(D):
    """Per category: how many prepared changes, the widest reach among them
    and which change it was, from the payload's scenario `reach` fields
    (written by build_scenarios.py from a run of the engine). Until
    2026-09-05 both tables that show this were typed, and the numbers went
    stale the day the engine changed."""
    rows = []
    for c in D["scenarioCats"]:
        sc = [v for v in D["scenarios"].values() if v.get("cat") == c["id"]]
        if not sc:
            continue
        top = max(sc, key=lambda v: v.get("reach", 0))
        rows.append((c["label"], len(sc), top.get("reach", 0), top["label"]))
    return rows


def scen_table(D):
    """atlas.html's table, in the catalogue's own category order."""
    tbl = ['<table>', '<tr><th>Category</th><th class="n">Changes</th>'
           '<th class="n">Widest reach</th><th>Widest</th></tr>']
    for label, n, reach, top in scen_rows(D):
        tbl.append(f'<tr><td>{label}</td><td class="n">{n}</td>'
                   f'<td class="n">{f(reach)}</td><td>{top}</td></tr>')
    tbl.append('</table>')
    return "\n".join(tbl)


def behaviour_table(D):
    """model.html section 6's table, widest first."""
    tbl = ['<table>', '<tr><th>Kind of change</th><th>Widest in that kind</th>'
           '<th class="n">Nodes that changed</th></tr>']
    for label, n, reach, top in sorted(scen_rows(D), key=lambda r: -r[2]):
        tbl.append(f'<tr><td>{label}</td><td>{top}</td><td class="n">{f(reach)}</td></tr>')
    tbl.append('</table>')
    return "\n".join(tbl)


BODY = """<h1>The atlas</h1>
<p class="dim">{n} nodes and {edges} weighted links, each carrying a
parameter from a public data set.</p>

<p>The atlas is the world energy system drawn as a graph and made to move.
Most nodes hold a measured quantity, and every node names where it came
from; the {assumed_total} that hold an assumption say so in their source line:
{assumed_consumer} consumer groups carry an elasticity from the literature,
the {psych} behaviour channels are a model of where demand is decided, and
{ports} ports carry a name and a harbour size class and no number. Apply a
change anywhere
and the effect propagates along the links until it settles, which the sixty
prepared changes do in {steps_min} to {steps_max} rounds, {steps_median} in the
middle; a single node pushed on its own settles in about {plant_steps}.</p>

{globe}

{card}

<h2>The nine layers</h2>

{layerfig}

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
movement falls below a threshold, which takes {steps_min} to {steps_max} rounds
across the prepared changes and never reaches the ceiling of sixty.
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

<p>Reach spans {reach_orders} orders of magnitude, from {reach_min} nodes to
{reach_max}, and starting at the most connected power plant in the world
({plant_name}, {plant_deg} links) moves {plant_moved_text}. That spread is the
point. A model that answers the same number to every question is not
answering.</p>

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
"""

# The layer diagram and its caption. The generator takes the stamped block
# from the page it is rewriting when one is there, so bust_cache.py's stamps
# survive a regeneration; this is the fallback for a page that has lost it,
# and the source of the markup when it changes (2026-09-04: a <picture> with
# the phone render, the generator named, the band order explained).
LAYER_FIG = (
    '<picture class="wide">\n'
    '<source media="(max-width: 760px)" srcset="assets/atlas_layers-phone.png">\n'
    '<img src="assets/atlas_layers.png" class="fig" loading="lazy" '
    'width="2280" height="1400" alt="The nine layers of the atlas as bands '
    'with their live node counts. Space, weather, climate and recorded events '
    'push one way, downward; demand, power plants, markets and fuel, grids and '
    'behaviour trade back and forth.">\n'
    '</picture>\n'
    '<p class="small">Drawn by <code>build_layer_diagram.py</code> from the '
    'published payload: every count and every link is read from it, and the '
    'rank rule from the engine. A single arrowhead pushes one way; a double '
    'head trades back and forth; an arc\'s width is the number of links it '
    'stands for. The bands are in the one order that minimises arc crossings, '
    'and the table below follows the figure.</p>')


# The globe, moved here from the home page on 2026-09-04: a map belongs on
# the page about the thing it maps. Same stamp-preserving rule as the layer
# diagram; the fallback is written from the payload's own counts.
def globe_fig(s):
    return (
        '<img class="fig wide plain" src="assets/hero_globe.png" '
        'width="1440" height="1252" alt="The model\'s '
        f'{f(s["station"])} power stations and {f(s["consumer"])} settlements '
        'at their recorded coordinates, on an orthographic globe centred on '
        'the Atlantic">\n'
        '<p class="small">Every power station and every settlement in the '
        'model at its recorded coordinates, drawn on paper by '
        '<code>build_hero_figure.py</code> from the payload.</p>')

# BODY once ended with a "Limits" section (coverage follows the source
# databases; the propagation is a relaxation, not a power flow) that no
# committed atlas.html ever carried. Removed 2026-09-04 rather than kept as
# dead prose in a generator; the text is quoted in FIX_SWEEP_2026-09-04.md.


def main(apply=False):
    s = stats()
    p = os.path.join(SITE, "atlas.html")
    t = open(p, encoding="utf-8").read()

    # "<main" with whatever class it carries: the deslop pass (2026-09-04)
    # gave every page's <main> a class, and t.index("<main>") then raised on
    # every run - the generator was broken for as long as nobody ran it.
    m = re.search(r"<main[^>]*>", t)
    if not m:
        raise SystemExit("atlas.html has no <main>")
    head = t[:m.end()]
    tail = t[t.index("<footer"):]
    card = re.search(r'<div class="card">.*?</div>\s*\n', t, re.S)
    card = card.group(0) if card else ""
    fig = re.search(r'<picture class="wide">\n<source[^>]*atlas_layers-phone[^>]*>\n'
                    r'<img src="assets/atlas_layers\.png[^>]*>\n</picture>\n<p class="small">.*?</p>', t, re.S)
    layerfig = fig.group(0) if fig else LAYER_FIG
    gl = re.search(r'<img class="fig wide plain" src="assets/hero_globe\.png[^>]*>\n<p class="small">.*?</p>', t, re.S)
    globe = gl.group(0) if gl else globe_fig(s)

    body = BODY.format(
        nscen=f(s["nscen"]), scentable=scen_table(s["_D"]),
        n=f(s["n"]), edges=f(s["edges"]), card=card, table=atlas_page(s),
        layerfig=layerfig, globe=globe,
        assumed_total=f(s["assumed_total"]), assumed_consumer=f(s["assumed_consumer"]),
        ports=f(s["ports"]),
        steps_min=s["steps_min"], steps_max=s["steps_max"], steps_median=s["steps_median"],
        plant_steps=s["plant_steps"],
        reach_orders=f"{s['reach_orders']:.1f}".replace(".0", ""),
        reach_min=f(s["reach_min"]), reach_max=f(s["reach_max"]),
        plant_name=s["plant_name"], plant_deg=f(s["plant_deg"]),
        plant_moved_text=("nothing but itself" if s["plant_moved"] == 0 else
                          f"{f(s['plant_moved'])} other node" + ("" if s["plant_moved"] == 1 else "s")),
        psych=f(s["psych"]), anatomy=f(s["anatomy"]),
        isolated=f(s["isolated"]),
        isopct=f"{100 * s['isolated'] / s['n']:.2f}")
    # an empty slot (no card on the page) must not leave a run of blank lines
    new = re.sub(r"\n{3,}", "\n\n", head + "\n\n" + body + "\n" + tail)

    changes = [f"atlas.html rewritten from the model ({f(s['n'])} nodes)"]

    # how-it-works: substitute every figure that moved
    p2 = os.path.join(SITE, "model.html")
    t2 = open(p2, encoding="utf-8").read()
    subs = [
        # no rule for 7,192: that is the July build's own count, and section 7
        # names it as such. A rule here rewrote that sentence to the current
        # count the first time it existed (2026-09-04) - trap 8 again.
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
    # Section 2's table is generated whole, every row from the payload, so no
    # number in it can be left behind or mis-keyed by the rules above.
    t2, k = re.subn(r"(<h2>2\. What the model contains</h2>\s*\n\s*\n)<table>.*?</table>",
                    lambda m: m.group(1) + model_table(s), t2, count=1, flags=re.S)
    if k != 1:
        raise SystemExit("model.html: section 2 table not found")
    hits += k
    # Sections 5.1 and 5.2: the weight and inertia tables, from the payload
    # (claim 3 of ATLAS_CLAIMS_TODO_2026-09-04.md)
    t2, k = re.subn(r"(<h3>5\.1 Link weights</h3>.*?</p>\s*\n\s*\n)<table>.*?</table>",
                    lambda m: m.group(1) + weight_table(s["_D"], s["_kind"]), t2, count=1, flags=re.S)
    if k != 1:
        raise SystemExit("model.html: section 5.1 table not found")
    hits += k
    t2, k = re.subn(r"(<h3>5\.2 Node inertia</h3>.*?</p>\s*\n\s*\n)<table>.*?</table>",
                    lambda m: m.group(1) + inertia_table(s["_D"], s["_kind"]), t2, count=1, flags=re.S)
    if k != 1:
        raise SystemExit("model.html: section 5.2 table not found")
    hits += k
    # Section 4.4: the measured settle range (typed once, 2026-09-05, and
    # stale by one the same day when property 5 changed the runs)
    t2, k = re.subn(r"the prepared\s+changes settle in \d+ to \d+\.",
                    f"the prepared changes settle in {s['steps_min']} to {s['steps_max']}.", t2)
    hits += k
    # Section 6: the behaviour table, from the scenarios' measured reach
    t2, k = re.subn(r"(<h2>6\. How the model behaves</h2>\s*\n\s*\n)<table>.*?</table>",
                    lambda m: m.group(1) + behaviour_table(s["_D"]), t2, count=1, flags=re.S)
    if k != 1:
        raise SystemExit("model.html: section 6 table not found")
    hits += k
    # the sources table's brain row counts the channels
    t2, k = re.subn(r"\b\d+ channels matched\b", f"{f(s['psych'])} channels matched", t2)
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
