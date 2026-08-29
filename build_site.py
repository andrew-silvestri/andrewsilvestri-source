#!/usr/bin/env python3
"""Build the andrewsilvestri.com static site.

Assembles: favicon, shared navigation with a Projects dropdown, one page per
completed project, a code page, and a zipped source bundle per project.

Run from this folder:  python3 build_site.py
Everything is written into ./site, which is what gets pushed to the repo.
"""

import os
import re
import shutil
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # "13 - Energy Modeling (sans linux)"
SITE = HERE / "site"
ASSETS = SITE / "assets"
DL = SITE / "downloads"

ASSETS.mkdir(parents=True, exist_ok=True)
DL.mkdir(parents=True, exist_ok=True)

FOOTER = ('<footer>Andrew Silvestri · energy systems modelling ·\n'
          '<a href="mailto:dasilvestri@utexas.edu">dasilvestri@utexas.edu</a></footer>')

# --------------------------------------------------------------------------
# 1. Navigation
# --------------------------------------------------------------------------

PROJECTS = [
    ("heat.html",       "Industrial heat break-even"),
    ("dac.html",        "Direct air capture TEA"),
    ("storage.html",    "Battery revenue simulator"),
    ("holdup.html",     "Pipeline liquid holdup"),
    ("energy-web.html", "World energy web, v1–v5"),
    ("atlas.html",      "The atlas"),
]


def nav(active=""):
    def on(h):
        return ' class="on"' if h == active else ''
    items = "".join(f'<a href="{h}"{on(h)}>{t}</a>' for h, t in PROJECTS)
    return (
        '<nav class="top">'
        f'<a href="index.html"{on("index.html")}>Home</a>'
        '<span class="dd"><a href="#" class="ddbtn" aria-haspopup="true">'
        'Projects <span class="caret">▾</span></a>'
        f'<span class="ddmenu">{items}</span></span>'
        f'<a href="library.html"{on("library.html")}>Figures</a>'
        f'<a href="model.html"{on("model.html")}>How it works</a>'
        f'<a href="code.html"{on("code.html")}>Code</a>'
        '</nav>')


HEAD_ICONS = (
    '<link rel="icon" href="favicon.svg" type="image/svg+xml">\n'
    '<link rel="alternate icon" href="favicon.png">\n'
    '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
    '<meta name="theme-color" content="#141310">\n')


def page(title, body, active="", desc=""):
    meta = f'<meta name="description" content="{desc}">\n' if desc else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
{meta}{HEAD_ICONS}<link rel="stylesheet" href="style.css">
</head><body>
{nav(active)}
<main>

{body}

{FOOTER}
</main></body></html>
"""


# --------------------------------------------------------------------------
# 2. Favicon
# --------------------------------------------------------------------------

FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="12" fill="#141310"/>
<g stroke="#d9a441" stroke-width="2.6" fill="none" opacity=".85">
<path d="M32 12 L32 32 M32 32 L14 44 M32 32 L50 44 M32 32 L12 26 M32 32 L52 26"/>
</g>
<g fill="#d9a441">
<circle cx="32" cy="32" r="6"/>
<circle cx="32" cy="12" r="3.4"/><circle cx="14" cy="44" r="3.4"/>
<circle cx="50" cy="44" r="3.4"/><circle cx="12" cy="26" r="3"/>
<circle cx="52" cy="26" r="3"/>
</g>
</svg>
"""


def build_favicon():
    (SITE / "favicon.svg").write_text(FAVICON_SVG, encoding="utf-8")
    try:
        import cairosvg  # noqa
        cairosvg.svg2png(bytestring=FAVICON_SVG.encode(),
                         write_to=str(SITE / "favicon.png"),
                         output_width=180, output_height=180)
        shutil.copy(SITE / "favicon.png", SITE / "apple-touch-icon.png")
        return "svg+png(cairosvg)"
    except Exception:
        pass
    try:
        from PIL import Image, ImageDraw
        import math
        for size, name in ((180, "apple-touch-icon.png"), (180, "favicon.png")):
            im = Image.new("RGBA", (size, size), (20, 19, 16, 255))
            d = ImageDraw.Draw(im)
            s = size / 64.0
            gold = (217, 164, 65, 255)
            c = (32 * s, 32 * s)
            pts = [(32, 12), (14, 44), (50, 44), (12, 26), (52, 26)]
            for x, y in pts:
                d.line([c, (x * s, y * s)], fill=(217, 164, 65, 210),
                       width=max(2, int(2.6 * s)))
            for x, y in pts:
                r = 3.2 * s
                d.ellipse([x * s - r, y * s - r, x * s + r, y * s + r], fill=gold)
            r = 6 * s
            d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=gold)
            im.save(SITE / name)
        im = Image.open(SITE / "favicon.png")
        im.save(SITE / "favicon.ico",
                sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        return "svg+png+ico(PIL)"
    except Exception as e:
        return f"svg only ({e})"


# --------------------------------------------------------------------------
# 3. Figures
# --------------------------------------------------------------------------

FIGCOPY = [
    ("01 Industrial Heat Breakeven/outputs", "heat_"),
    ("02 DAC Adsorption TEA/outputs",        "dac_"),
    ("03 Storage Revenue Stack/outputs",     "storage_"),
    ("14 World Energy Web v5/outputs",       "web5_"),
]


def copy_figures():
    n = 0
    for rel, prefix in FIGCOPY:
        src = ROOT / rel
        if not src.is_dir():
            continue
        for f in sorted(src.glob("fig*.png")):
            shutil.copy(f, ASSETS / (prefix + f.name))
            n += 1
    extra = ROOT / "15 Website" / "assets"
    if extra.is_dir():
        for name in ("fig0_web_overview.png", "fig2_validation.png",
                     "ripple_hormuz_closure.png", "fig2_taxonomy_heatmap.png"):
            f = extra / name
            if f.exists():
                shutil.copy(f, ASSETS / ("web_" + name))
                n += 1
    return n


def fig(name, caption):
    """Figure block, but only if the file actually landed in assets."""
    if not (ASSETS / name).exists():
        return ""
    return (f'<img class="fig" src="assets/{name}" alt="{caption}">\n'
            f'<p class="small">{caption}</p>\n')


# --------------------------------------------------------------------------
# 4. Code bundles
# --------------------------------------------------------------------------

CODE_EXT = {".py", ".jl", ".m", ".toml", ".sh", ".md", ".txt", ".json"}
MAX_MEMBER = 4 * 1024 * 1024          # skip anything fat; this is source, not data

BUNDLES = [
    ("heat",     "01 Industrial Heat Breakeven", True),
    ("dac",      "02 DAC Adsorption TEA",        True),
    ("storage",  "03 Storage Revenue Stack",     True),
    ("web-v3",   "10 World Energy Web",          False),
    ("web-v4",   "13 World Energy Web v4",       False),
    ("web-v5",   "14 World Energy Web v5",       False),
    ("model",    "17 Julia Model",               False),
    ("atlas",    "19 Atlas v6",                  False),
    ("deliverables", "18 Final Deliverables",    False),
]

SKIP_DIRS = {"outputs", "out", "data", "library", "feedstocks", ".vscode",
             "__pycache__", ".git", "enrichment"}


def build_bundles():
    made = {}
    for slug, rel, with_xlsx in BUNDLES:
        src = ROOT / rel
        if not src.is_dir():
            continue
        out = DL / f"{slug}-code.zip"
        count = 0
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for dirpath, dirnames, filenames in os.walk(src):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fn in filenames:
                    p = Path(dirpath) / fn
                    ext = p.suffix.lower()
                    ok = ext in CODE_EXT or (with_xlsx and ext == ".xlsx")
                    if not ok:
                        continue
                    try:
                        if p.stat().st_size > MAX_MEMBER:
                            continue
                        z.write(p, Path(slug) / p.relative_to(src))
                        count += 1
                    except OSError:
                        continue
        if count == 0:
            out.unlink(missing_ok=True)
        else:
            made[slug] = (count, out.stat().st_size)
    return made


def dlbox(slug, label, note=""):
    """Download card for the bottom of a project page."""
    z = DL / f"{slug}-code.zip"
    if not z.exists():
        return ""
    kb = z.stat().st_size / 1024
    size = f"{kb/1024:.1f} MB" if kb > 1024 else f"{kb:.0f} KB"
    extra = f'<p class="small">{note}</p>' if note else ""
    return f"""<hr>
<h2>The code</h2>
<p>{label} The archive holds the source only: no generated figures, no bulk
data. Each model runs from its own <code>README.md</code>.</p>
{extra}
<p><a class="btn" href="downloads/{slug}-code.zip">Download source · {size}</a>
<a class="btn ghost" href="code.html">All code</a></p>
"""


# --------------------------------------------------------------------------
# 5. Project pages
# --------------------------------------------------------------------------

def build_heat():
    b = f"""<h1>Industrial heat electrification break-even</h1>
<p class="dim">Levelised cost of heat from a resistive electric boiler against a
natural-gas boiler, for process steam in Texas.</p>

<p>An industrial site that wants to stop burning gas for process steam has one
obvious substitute: a resistive electric boiler. The question is what the
electricity has to cost before that substitution stops losing money. This model
answers it in dollars per million British thermal units of heat actually
delivered, so the two routes are compared on the same basis.</p>

<h2>What the model finds</h2>
<p>At a gas price of $3.50 per million British thermal units and electricity at
6.5 cents per kilowatt hour, gas heat costs about <strong>$5.13</strong> per
million British thermal units and electric heat about <strong>$20.00</strong>.
The break-even electricity price is about <strong>1.53 cents per kilowatt
hour</strong>, or 1.38 cents if only fuel is counted.</p>

<p>The result that matters is not the number itself but its insensitivity.
Moving capital cost and fixed operations across a range of plus or minus fifty
per cent shifts the break-even by roughly 0.15 cents per kilowatt hour. The
spark gap, meaning the ratio between the electricity price and the gas price,
decides the outcome almost by itself. Arguments about equipment cost are
therefore arguments about the wrong variable.</p>

<p>Emissions follow the same logic and give a second threshold. The electric
boiler only emits less than the gas boiler when the grid carbon intensity is at
or below <strong>0.209 tonnes of carbon dioxide per megawatt hour</strong>. The
eGRID average for the Texas grid is about 0.365. On average grid power, in other
words, electrifying this heat increases emissions.</p>

{fig('heat_fig1_breakeven_price.png', 'Break-even electricity price as a function of the gas price. The line is the locus where the two routes cost the same; below it the electric boiler wins.')}
{fig('heat_fig3_costgap_contour.png', 'Cost gap across the electricity price and gas price plane. The diagonal structure is the spark gap dominating both axes.')}
{fig('heat_fig4_tornado.png', 'Sensitivity of the break-even to every input. Fuel prices dominate; capital and operations barely move it.')}
{fig('heat_fig5_emissions_parity.png', 'Emissions of both routes against grid carbon intensity. The crossing point is the parity threshold.')}

<h2>Method</h2>
<p>The levelised cost is built from an annualised capital charge, fixed and
variable operations, and fuel, divided by annual delivered heat. Boiler
efficiency is applied on the gas side and conversion and distribution losses on
the electric side. The workbook carries the same arithmetic in live formulas so
that the assumptions can be edited without touching code, and the Python
implementation is the reference the other ports were checked against.</p>

<h2>Limits</h2>
<p>The prices in the shipped run are placeholders, and the model reads a real
series from a template file the moment one is supplied. The boundary between
retail all-in electricity and wholesale energy-only pricing has to be stated
before any number is quoted, because it moves the answer by more than the
capital cost does. Capital figures are scaling placeholders with a stated
uncertainty band rather than vendor quotes. The emissions comparison uses
average grid intensity; a marginal-emissions treatment is the more defensible
framing and is the next revision.</p>

{dlbox('heat', 'Python reference implementation, Julia and Octave ports, and the formula-driven workbook.')}
"""
    return page("Industrial heat break-even — Andrew Silvestri", b,
                "heat.html",
                "Levelised cost of heat for electric versus gas boilers in Texas.")


def build_dac():
    b = f"""<h1>Direct air capture: a fixed-bed cycle and its cost</h1>
<p class="dim">A temperature-swing adsorption model and capture-cost analysis,
and the negative result that redirected a laboratory project.</p>

<p>This model started as a check on a sorbent the laboratory already had. The
check failed, and the failure was the useful part.</p>

<h2>The negative result</h2>
<p>Running the laboratory's own dual-site Langmuir parameters for CALF-20 at
direct air capture conditions gives an adsorbed quantity of about
<strong>0.031 millimoles per gram</strong> at 420 parts per million. That is
effectively zero working capacity: the desorption backpressure defeats any
temperature swing that could be run in practice. CALF-20 is a flue-gas
physisorbent, and the arithmetic says so plainly. The implementation was
validated against the laboratory's own spreadsheet first, reproducing its
affinity constant at 303 kelvin to three figures, so the disagreement is with
the material rather than with the code.</p>

<p>That is the quantitative justification for moving to an amine chemisorbent,
which the cost model then runs on.</p>

<h2>The amine case</h2>
<table><tr><th>Quantity</th><th>Value</th></tr>
<tr><td>Working capacity per cycle</td><td>1.06 moles per kilogram</td></tr>
<tr><td>Regeneration energy, thermal</td><td>1,113 kilowatt hours per tonne</td></tr>
<tr><td>Regeneration energy, electrical</td><td>150 kilowatt hours per tonne</td></tr>
<tr><td>Capture cost, baseline</td><td>about $591 per tonne</td></tr>
</table>
<p class="small">Adsorption at 25 degrees Celsius and 420 parts per million,
desorption at 100 degrees Celsius and 2 kilopascals of carbon dioxide, without
heat recovery.</p>

<p>The cost sits inside the published range for small direct air capture. The
sensitivity analysis puts cycles per day, sorbent cost, and sorbent lifetime at
the top, which means the economics are governed by how hard the bed is worked
and how long it survives, not by the thermodynamics of the swing.</p>

{fig('dac_fig1_isotherms.png', 'Isotherms for the amine sorbent and CALF-20. At the concentration of air, the two materials are not in the same regime.')}
{fig('dac_fig2_working_capacity.png', 'Working capacity against desorption temperature. The curve shows how much swing is bought by each additional degree.')}
{fig('dac_fig3_energy_per_tonne.png', 'Regeneration energy per tonne against heat recovery fraction.')}
{fig('dac_fig5_cost_tornado.png', 'Cost sensitivity. Cycles per day, sorbent cost and sorbent life dominate.')}

<h2>Limits</h2>
<p>The amine isotherm is a single-site Langmuir calibrated to literature anchor
points rather than a full Toth fit, which is what publication-grade work would
use. Humidity is ignored, and this is the largest single omission: water
co-adsorption on an amine roughly doubles the real thermal duty, so the energy
figures above should be read as a floor. The breakthrough calculation uses a
linear driving force in a single well-mixed stage, which gives timing but not
spatial profiles.</p>

{dlbox('dac', 'Python reference implementation, Julia and Octave ports, and the formula-driven workbook.')}
"""
    return page("Direct air capture TEA — Andrew Silvestri", b, "dac.html",
                "Temperature-swing adsorption cycle model and capture cost for direct air capture.")


def build_storage():
    b = f"""<h1>Battery revenue simulator</h1>
<p class="dim">A linear program over a year of hourly prices, and what it says
about how long a battery should be.</p>

<p>A grid battery earns by buying cheap and selling dear. How much it can earn
depends on the shape of the price series and on how many hours of energy it can
hold. This model dispatches a one-megawatt battery against 8,760 hourly prices
by linear programming, in monthly blocks with the state of charge carried
across the joins, and charges a cycling cost against every megawatt hour of
throughput so that the optimiser cannot trade for free.</p>

<h2>Duration value flattens</h2>
<table><tr><th>Duration</th><th>Revenue, $/kW-year</th><th>Equivalent cycles</th></tr>
<tr><td>2 hours</td><td>100.1</td><td>1,254</td></tr>
<tr><td>4 hours</td><td>110.2 (104.4 net of degradation)</td><td>725</td></tr>
<tr><td>8 hours</td><td>114.6</td><td>392</td></tr>
</table>

<p>Doubling from two hours to four buys about ten per cent more revenue.
Doubling again from four to eight buys about four per cent. On energy arbitrage
alone, value flattens hard past four hours. This is the expected result and the
reason four-hour systems are the market default; the point of the model is that
the flattening is now measured on a stated price series rather than asserted.</p>

<p>The longer battery also cycles far less, which matters for a warranty
argument even where it does not matter for revenue. The eight-hour case turns
over about a third as many equivalent cycles as the two-hour case.</p>

{fig('storage_fig3_duration_value.png', 'Revenue against storage duration. The curve bends at about four hours.')}
{fig('storage_fig2_dispatch_week.png', 'A summer week of dispatch. Charging fills the solar belly of the day; discharge meets the evening peak.')}
{fig('storage_fig4_sensitivity.png', 'Sensitivity to round-trip efficiency and degradation cost.')}
{fig('storage_fig1_prices.png', 'The price series: duration curve and average daily shape.')}

<h2>Two honest caveats</h2>
<p>The shipped run uses a documented synthetic price year built to resemble the
Texas market, with a solar belly, an evening peak, summer scarcity spikes and a
small fraction of negative hours. It is not real data. The model reads a real
day-ahead price file automatically as soon as one is placed in its data folder,
and replacing the series is the first thing to do before quoting any figure.</p>

<p>The dispatch assumes perfect foresight, which is an upper bound rather than
an estimate. Real bidding into a day-ahead market captures roughly seventy to
ninety per cent of the perfect-foresight value, so the revenue column above
should be discounted accordingly.</p>

<p>The Julia port is written with JuMP and HiGHS, which is the stack this class
of model is actually built on in industry.</p>

{dlbox('storage', 'Python reference implementation using an open solver, a JuMP and HiGHS port, an Octave port, and the dispatch workbook.')}
"""
    return page("Battery revenue simulator — Andrew Silvestri", b,
                "storage.html",
                "Linear-program dispatch of a grid battery and the value of storage duration.")


def build_holdup():
    b = """<h1>Pipeline liquid holdup calculator</h1>
<p class="dim">A spreadsheet with 19,653 simulation runs behind it, ported to an
interactive tool, which then found a bug in the spreadsheet.</p>

<p>Gathering pipelines accumulate liquid. How much sits in a line, how it
responds to flow rate, and how often the line has to be pigged are planning
questions with money attached: slug catcher sizing, tank capacity, truck
schedules. The source workbook answered them by interpolating across a library
of 19,653 process simulation runs laid out on a Latin hypercube.</p>

<p>The port reproduces that engine exactly. It rebuilds the nine-dimensional
normalised query space, the inverse-quartic distance kernels with their separate
feature weightings for holdup, pressure drop and yields, the seasonal ground
temperature model with damping by burial depth, the frozen-soil rule, and the
downstream planning arithmetic, formula for formula.</p>

<h2>What the port found</h2>
<p>The port's kernel weights match the workbook's own cached weight columns cell
for cell, and the query normalisation matches to machine precision. The
workbook's <em>displayed</em> results, however, disagree with what its own
cached kernels imply, by between two and twelve per cent. In the simple profile
case the sheet displays 8.554 barrels per mile; recomputing from the weights
the sheet itself has stored gives 8.359, and the port gives 8.361.</p>

<p>The workbook is carrying stale values from a partial recalculation. Forcing a
full recalculation brings it back into agreement. This is worth knowing before
anyone quotes a number off that sheet, and it is the kind of error that only
shows up when an independent implementation is checked against the original
rather than against its own output.</p>

<hr>
<h2>Code</h2>
<p>This work was done during an industrial internship. The engine, the
simulation library and the source workbook are the company's, so they are not
published here. The description above covers the method and the finding; the
implementation stays private.</p>
"""
    return page("Pipeline liquid holdup — Andrew Silvestri", b, "holdup.html",
                "Interactive port of a pipeline liquid holdup calculator, and the stale-cache bug it found.")


def build_web():
    b = f"""<h1>The world energy web, five generations</h1>
<p class="dim">How far shock propagation through the global energy system can be
pushed, and where pushing it stops helping.</p>

<p>This project ran for five generations. Each one asked the same question: if
something changes somewhere in the world energy system, what else moves, in what
order, and by how much? The generations differ in how much of the world they
tried to hold at once, and the honest summary is that the largest version was
not the best one.</p>

<h2>The generations</h2>
<table><tr><th>Generation</th><th>Size</th><th>What it added</th></tr>
<tr><td>v3</td><td>52,804 nodes, 222,240 links</td><td>31,416 real named power
plants with coordinates, districts under every grid, consumer groups, weather
cells, and a dispatch core clearing each grid by merit order</td></tr>
<tr><td>v4</td><td>957,000 nodes</td><td>Household, vehicle, diet, transit and
data-centre cohorts; a behavioural layer; historical replays from 1973 to
2024</td></tr>
<tr><td>v5</td><td>959,229 nodes, 2.64 million links</td><td>A driver taxonomy
of 1,842 rows across 31 sheets used as the model's semantic spine, so that
editing the spreadsheet regrows the graph</td></tr>
</table>

<p>The calibration work in v3 is the part that survives scrutiny. Stress values
were mapped to real prices and checked by replaying known events through the
graph: the February 2021 Texas freeze, the 2021 to 2022 European gas crisis, and
the 2022 oil shock. The model reproduces the observed peaks within a stated
error band of roughly a factor of two. That band is wide, and it is quoted
rather than hidden.</p>

{fig('web_fig0_web_overview.png', 'The web at full extent. Structure, not decoration: the layout is produced from the link structure itself.')}
{fig('web_fig2_validation.png', 'Replaying historical events through the graph and comparing the modelled price response against what was actually observed.')}

<h2>Where it went next</h2>
<p>A million nodes is impressive and hard to defend. Most of that count was
procedural: cohorts and districts generated from plausible rules rather than
measured from data. So the project was deliberately cut down. The current model
holds <strong>7,192 nodes</strong>, and every one of them carries a parameter
taken from a public data set, with the source named on the node. National
demand comes from published statistics, fuel shares from the same, disasters
from the international disaster database, prices from public financial series,
the climate record from direct measurement, and plant locations from the public
energy archive.</p>

<p>Fewer nodes, every one defensible. That is the version the
<a href="atlas.html">atlas</a> and the <a href="model.html">how it works</a>
page describe, and it is the one worth trusting.</p>

<h2>Explore the earlier versions</h2>
<p>These explorers are self-contained: they carry their data inside and run
entirely in the browser.</p>
<p><a class="btn ghost" href="navigator.html">v4 navigator</a>
<a class="btn ghost" href="navigator5.html">v5 taxonomy navigator</a>
<a class="btn ghost" href="zoom_explorer.html">Three-dimensional dive</a></p>

<hr>
<h2>The code</h2>
<p>Three separate archives, one per generation. Source only; the graph data and
generated outputs are rebuilt by the scripts.</p>
<p><a class="btn" href="downloads/web-v3-code.zip">v3 source</a>
<a class="btn" href="downloads/web-v4-code.zip">v4 source</a>
<a class="btn" href="downloads/web-v5-code.zip">v5 source</a>
<a class="btn ghost" href="code.html">All code</a></p>
"""
    return page("The world energy web — Andrew Silvestri", b,
                "energy-web.html",
                "Five generations of a shock-propagation model of the global energy system.")


def build_code_page(made):
    labels = {
        "heat": ("Industrial heat break-even", "heat.html",
                 "Python reference, Julia and Octave ports, formula workbook."),
        "dac": ("Direct air capture TEA", "dac.html",
                "Adsorption cycle and cost model in three languages, plus the workbook."),
        "storage": ("Battery revenue simulator", "storage.html",
                    "Linear-program dispatch; JuMP and HiGHS port included."),
        "web-v3": ("World energy web, v3", "energy-web.html",
                   "Units calibration, real plant loader, merit-order dispatch core."),
        "web-v4": ("World energy web, v4", "energy-web.html",
                   "Cohort builders, behavioural layer, historical replays."),
        "web-v5": ("World energy web, v5", "energy-web.html",
                   "Taxonomy loader that turns the driver spreadsheet into the graph."),
        "model": ("The calibrated model", "model.html",
                  "The current 7,192-node model in Julia, with the Python parity check."),
        "atlas": ("The atlas", "atlas.html",
                  "Scene exporter and the builder that produces the single-file atlas."),
        "deliverables": ("Charts and terminal application", "model.html",
                         "Figure generators and the interactive terminal client."),
    }
    rows = []
    for slug, (name, href, desc) in labels.items():
        if slug not in made:
            continue
        count, size = made[slug]
        s = f"{size/1048576:.1f} MB" if size > 1048576 else f"{size/1024:.0f} KB"
        rows.append(
            f'<tr><td><a href="{href}">{name}</a></td><td>{desc}</td>'
            f'<td>{count} files</td>'
            f'<td><a href="downloads/{slug}-code.zip">{s}</a></td></tr>')

    b = f"""<h1>Code</h1>
<p class="dim">Every model on this site, as source you can run.</p>

<p>Each archive contains source only: the programs, their ports to other
languages, and the notes needed to run them. Generated figures and bulk data
are left out, because every model rebuilds them. Each archive has a
<code>README.md</code> at its root giving the command to run, the results to
expect, and the assumptions that produced them.</p>

<table>
<tr><th>Model</th><th>Contents</th><th>Size</th><th>Download</th></tr>
{chr(10).join(rows)}
</table>

<h2>Running them</h2>
<p>The Python implementations are the verified references; where a Julia or
Octave port exists it was written line for line from the Python and is marked in
the archive as untested in the environment that produced it. The three
techno-economic models also ship a formula-driven workbook carrying the same
arithmetic, so the assumptions can be edited without running any code.</p>

<h2>Not published</h2>
<p>The <a href="holdup.html">pipeline liquid holdup</a> work was done during an
industrial internship. Its engine, simulation library and source workbook belong
to the company, so only the method and the result appear on this site.</p>
"""
    return page("Code — Andrew Silvestri", b, "code.html",
                "Downloadable source for every model on the site.")


# --------------------------------------------------------------------------
# 6. Home page
# --------------------------------------------------------------------------

def build_index():
    b = """<h1>Andrew Silvestri</h1>
<p class="dim">Chemical engineering at UT Austin. Energy systems modelling.
Currently a general engineering intern at Targa Resources.</p>

<p>I build models of energy systems, from the thermodynamics of a single vessel
up to a model of the world energy system with 7,192 nodes. Everything here ships
with its code, its data sources, and its limits written down.</p>

<div class="card">
<div class="tag">Main project</div>
<h3 style="margin-top:4px">A model of the world energy system</h3>
<p>7,192 nodes and 13,826 weighted links. Real power plants, real national fuel
mixes, real recorded disasters, real price histories, and the measured climate
record. Apply a change anywhere and watch it move through the system.</p>
<p class="small">Every parameter comes from a public data set. Every node names
its source.</p>
<a class="btn" href="atlas.html">Open the atlas</a>
<a class="btn ghost" href="model.html">How it works</a>
<a class="btn ghost" href="energy-web.html">How it got there</a>
</div>

<img class="fig" src="assets/energy_model_chart.png"
 alt="Overview chart of the world energy model">
<p class="small">The model at a glance: what it contains, how it is weighted,
and how it behaves. <a href="library.html">All figures</a>.</p>

<hr>
<h2>Focused models</h2>

<div class="card">
<div class="tag">Techno-economics</div>
<h3 style="margin-top:4px"><a href="heat.html">Industrial heat electrification
break-even</a></h3>
<p>Cost of heat from an electric boiler against a gas boiler in Texas. The gap
between the fuel prices decides the outcome. Break-even electricity is about
1.5 cents per kilowatt hour at $3.50 gas, and capital cost moves it very
little.</p>
</div>

<div class="card">
<div class="tag">Optimisation</div>
<h3 style="margin-top:4px"><a href="storage.html">Battery revenue
simulator</a></h3>
<p>Linear program over 8,760 hours. Value flattens above four hours of storage
duration, which is the expected result, now measured.</p>
</div>

<div class="card">
<div class="tag">Chemical engineering</div>
<h3 style="margin-top:4px"><a href="dac.html">Why our sorbent could not do
direct air capture</a></h3>
<p>Using the laboratory's own isotherm parameters, the material holds almost
nothing at 420 parts per million. A negative result, and the reason the project
changed material.</p>
</div>

<div class="card">
<div class="tag">Industry tooling</div>
<h3 style="margin-top:4px"><a href="holdup.html">Pipeline liquid holdup
calculator</a></h3>
<p>A spreadsheet with 19,653 simulation runs, ported to an interactive tool.
The port matched the workbook formulas exactly, and showed that the workbook's
displayed values carried a stale calculation.</p>
</div>

<div class="card">
<div class="tag">Method</div>
<h3 style="margin-top:4px"><a href="energy-web.html">The world energy web,
v1 to v5</a></h3>
<p>Five generations of shock propagation through the global energy system, from
52,000 nodes to 959,000 and back down to 7,192. The smallest version is the one
worth trusting, and the page explains why.</p>
</div>

<hr>
<p class="small">Built with Python, Julia and public data.
<a href="code.html">All source is downloadable.</a></p>
"""
    return page("Andrew Silvestri — energy systems", b, "index.html",
                "Energy systems modelling: techno-economics, optimisation, and a "
                "calibrated model of the world energy system.")


# --------------------------------------------------------------------------
# 7. Patch existing pages (nav + favicon)
# --------------------------------------------------------------------------

def patch_existing():
    for name, active in (("atlas.html", "atlas.html"),
                         ("library.html", "library.html"),
                         ("model.html", "model.html")):
        p = SITE / name
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        t = re.sub(r'<nav class="top">.*?</nav>', nav(active), t, flags=re.S)
        if 'rel="icon"' not in t:
            t = t.replace('<link rel="stylesheet"', HEAD_ICONS + '<link rel="stylesheet"', 1)
        p.write_text(t, encoding="utf-8")


CSS_ADD = """
/* dropdown navigation */
nav.top{position:relative;z-index:50}
.dd{position:relative;display:inline-block;margin-right:18px}
.dd>.ddbtn{margin-right:0;cursor:pointer}
.caret{font-size:10px;opacity:.7}
.ddmenu{display:none;position:absolute;left:-14px;top:100%;padding:8px 0;
 min-width:250px;background:var(--card);border:1px solid var(--faint);
 border-radius:8px;box-shadow:0 10px 30px rgba(0,0,0,.16)}
.dd:hover>.ddmenu,.dd:focus-within>.ddmenu{display:block}
.ddmenu a{display:block;margin:0;padding:8px 16px;color:var(--ink);
 font-size:14px;white-space:nowrap}
.ddmenu a:hover{color:var(--acc);background:var(--faint);text-decoration:none}
@media (max-width:620px){
 .ddmenu{position:static;display:block;border:0;box-shadow:none;padding:4px 0 8px;
  min-width:0;background:transparent}
 .ddmenu a{padding:5px 0 5px 14px}
 .dd{display:block;margin:6px 0}}
"""


def patch_css():
    p = SITE / "style.css"
    t = p.read_text(encoding="utf-8")
    if "ddmenu" not in t:
        p.write_text(t + CSS_ADD, encoding="utf-8")


# --------------------------------------------------------------------------

def main():
    icon = build_favicon()
    nfig = copy_figures()
    made = build_bundles()
    patch_css()

    (SITE / "index.html").write_text(build_index(), encoding="utf-8")
    (SITE / "heat.html").write_text(build_heat(), encoding="utf-8")
    (SITE / "dac.html").write_text(build_dac(), encoding="utf-8")
    (SITE / "storage.html").write_text(build_storage(), encoding="utf-8")
    (SITE / "holdup.html").write_text(build_holdup(), encoding="utf-8")
    (SITE / "energy-web.html").write_text(build_web(), encoding="utf-8")
    (SITE / "code.html").write_text(build_code_page(made), encoding="utf-8")
    patch_existing()

    print(f"favicon : {icon}")
    print(f"figures : {nfig} copied")
    print("bundles :")
    for slug, (n, size) in sorted(made.items()):
        print(f"  {slug:<14} {n:>3} files  {size/1024:>8.0f} KB")
    print(f"total   : {sum(s for _, s in made.values())/1048576:.2f} MB of zips")


if __name__ == "__main__":
    main()
