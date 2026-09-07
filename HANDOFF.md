# Handoff: andrewsilvestri.com and the `13 - Energy Modeling` folder

Read this first if you are an AI picking up work on this site with no prior
context. It describes where everything is, how the site is built, the rules the
work follows, and the specific traps that have already caused bugs.

Written August 2026. If a number here disagrees with the payload, the payload
wins — see "Never trust a number in prose" below.

---

## 1. The one-paragraph version

`00 PUBLISH/` is the only folder that matters for the website. Inside it,
`site/` **is** the website: plain HTML, one stylesheet, four JavaScript files
(the atlas app and its payload, the lightbox, the motion contract), no build
step, no framework, no dependencies beyond three.js from a CDN for the two
WebGL apps. Everything else in `00 PUBLISH/`
is a Python script that generates or verifies part of `site/`. The numbered
folders `01`–`24` outside it are working archives; treat them as read-only
source material unless told otherwise.

---

## 2. Folder map

### The folder you work in

```
00 PUBLISH/
  site/                     THE WEBSITE. Upload the contents of this to the repo root.
    index.html              home
    atlas.html              about the energy model
    model.html              how the model works (the long method page)
    library.html            figure library
    code.html               downloads index
    heat.html storage.html                      project pages (Energy)
    shoes.html economy.html                     project pages (Running)
    climate-cost.html food.html continents.html
    longevity.html skyline.html neuron.html     project pages (Misc)
    atlas-app.html longevity-app.html skyline-app.html
    climate-cost-app.html continents-app.html   full-screen interactive apps,
                                                opened in a new tab
    style.css               the ONLY stylesheet for all non-app pages
    assets/                 figures (.png/.webp) and their -thumb.png, 4 JS files
                            (atlas-app, atlas-data, lightbox, motion), fonts/
                            (IBM Plex, OFL). No video and no WebGL hero since
                            2026-09-04. The home-page hero is the layer diagram
                            (atlas_layers-notes.png, -phone.png for a phone);
                            the globe, hero_globe.png, is on atlas.html.
    downloads/              per-project source .zip archives (gitignored; four
                            of the twelve are rebuilt by rezip_downloads.py)
    CNAME .nojekyll         GitHub Pages config — do not delete either
  tests/                    the test suites (see §7) and their Playwright
  climate-cost/             sub-project: LCA engine, data, tests, template
  longevity-quotient/       sub-project: model, data, tests, template
  food/                     sub-project: USDA fetch, the hyper-palatable rule and its nulls, figures, template, tests
  heat/ storage/            the two calculator models (see the table below)
  skyline/ bookshelf/       the skyline generator; the retired bookshelf app's README,
                            wallpaper setter and demo render (see unpublished/)
  fonts/                    Plex OTFs for the figure builders (sitefig.py)
  unpublished/              retired pages kept but not linked (RETIRED.md there says
                            what each was and why): the bookshelf (desktop.html,
                            bookshelf-app.html, 2026-09-05), dac, holdup, beans,
                            running-shoes and its three.js app (opening state from
                            ?shoe=1&part=2&explode=1&az=&el=), energy-web, hobbies,
                            navigator. Corrected 2026-09-04: this file used to list
                            four of them as live pages.
  *.py                      the build and verification scripts (see §5)
```

### Project sources and archives

Corrected 2026-09-04. Every row of this table used to name a folder at the
workspace root; the numbered ones moved into `01 ARCHIVE/` in July or are no
longer in the workspace at all, and three projects now live inside
`00 PUBLISH/`. Paths are relative to the workspace root, `50 - ENERGY MODEL/`.
`01 ARCHIVE/INDEX.md` still lists folders `00`–`15` as present; only `10`,
`11`, `13`–`18`, `20`, `21` are.

| Folder | What it is |
|---|---|
| `19 Atlas v6/raw/` | **The raw data the atlas is built from.** WRI power plants, GeoNames cities15000 + admin1 + countryInfo, USGS quakes, World Port Index, Allen brain atlas. |
| `00 PUBLISH/heat/`, `00 PUBLISH/storage/` | The heat and storage calculator models: `model.py`, `figstyle.py`, Julia and Octave ports, the formula workbook, README. Unpacked from their own download zips on 2026-08-30; the zips are rebuilt from them by `rezip_downloads.py`. The `01`–`03` model folders this table used to point at are not in the workspace. The DAC and holdup models (`02`, `12`) have no folder here; their pages sit in `unpublished/`. |
| `01 ARCHIVE/10 World Energy Web/`, `11 …`, `13 World Energy Web v4/`, `14 World Energy Web v5/` | World Energy Web v3/v4/v5 — **retired** model generations. Source of some legacy code the atlas still inherits. |
| `01 ARCHIVE/18 Final Deliverables/` | A snapshot of the **retired 7,192-node model**. Do not copy figures out of here; see the trap in §8. |
| `00 PUBLISH/skyline/` | The skyline project, unpacked from `skyline-code.zip` on 2026-09-04 (the zip had been the only copy). `build_app.py` builds `skyline/skyline-app.html`; the shipped copy is `site/skyline-app.html` and the two must be identical (`tests/test_generators.py` checks). Austin, Nashville and Fort Worth are carried in `supplement.py` from each city's published tallest-buildings list; above each list's stated floor the list overrules Wikidata. The instrument has one rendering, the musical one; the old realistic mode and its control are gone, so `S.mode` no longer exists. `24 Skyline Sonifier/` is not in the workspace. |
| `00 PUBLISH/bookshelf/` | The README and the wallpaper setter of the bookshelf download, retired 2026-09-05; the app itself is `unpublished/bookshelf-app.html` (fully client-side; demo screenshots in `site/assets/`). `25 Desktop Gallery/`, which also held a config-driven museum-wallpaper generator and its `PUBLISHING-NOTE.md` on image permissions, is not in the workspace; nothing from that generator is on the site. |
| `dumpNew/PyProjects/` | Personal desktop apps (Philbrook museum wall, Desktop Gazette), not published. Install contract: one folder, optional Startup shortcut, tray-icon quit, nothing in the registry. **Do not publish the museum wall.** Its `PUBLISHING-NOTE.md`, which held the reason, is gone (noticed 2026-09-05); the reason was image rights: `philbrook_museum/images_full/` is the museum's collection photography, pulled for a private wall and not licensed for a public site. A working generator with no visible reason not to ship it is how that warning would otherwise be lost. |
| `01 ARCHIVE/16 Presentation Architecture/` | 13 GB. Do not walk it casually. |

---

## 3. How a page is put together

Every non-app page is a complete standalone HTML file with this skeleton:

```html
<!DOCTYPE html>
<html lang="en"><head>
  <title>Page name — Andrew Silvestri</title>
  <meta name="description" content="one sentence">
  favicon links, theme-color
  <link rel="stylesheet" href="style.css?v=HASH">
</head><body>
<nav class="top">…generated, do not hand-edit…</nav>
<main>
  <h1>…</h1>
  <p class="dim">…standfirst…</p>
  …prose, <h2> sections, tables, <img class="fig wide">…
</main>
<footer>Andrew Silvestri · energy systems modelling · <a href="mailto:…">…</a></footer>
</body></html>
```

Conventions that matter:

- `main` is a CSS grid with three tracks. A child defaults to the **text**
  column; add `class="wide"` to break out sideways, `class="full"` for the full
  width. Figures use `<img class="fig wide">`.
- `class="dim"` is the muted standfirst under an `h1`.
- `class="card"` + `<div class="tag">` is the boxed callout used on project and
  library pages.
- `<table>` needs `class="n"` on numeric cells for tabular alignment.
- Interactive apps are separate `*-app.html` files with their own inline CSS,
  **no shared nav**, and are linked with `target="_blank"`.

### The nav is generated

Do not hand-edit `<nav class="top">`. Edit the `NAV` list at the top of
`rebuild_nav.py` and re-run it. It rewrites the nav on every page and marks the
current page with `class="on"`.

**This rule was broken once and the trap it left is worth knowing.** The
2026-08-30 revamp moved "Climate cost calculator" under "Energy" by editing all
eleven pages and left `NAV` with the old one-item "Climate research" group, so
for five weeks running the generator would have silently reverted a deliberate
change. `NAV` was brought back into line on 2026-09-04 (0 pages rewritten when
re-run). Before you trust it: run it, and if it reports anything but
"unchanged" for every page, stop and find out which side is right.

```python
NAV = [("Home", "index.html"),
       ("Energy", [("Open the atlas", "atlas-app.html"), …]),
       ("Running", […]), ("Misc", […]),
       ("Code", "code.html")]
```

Regrouped on 2026-09-05: "The atlas" lost its own group and folds into Energy
as its first four entries, "Others" became "Misc", and Running was split out.
Two rules came out of that pass and both are in `rebuild_nav.py`'s comments.
**Every label in `NAV` is the page's own title** - a nav that renames a page
gives the site two names for one thing. And **`index.html`'s section headings
are this same taxonomy in a second place**, so they must match `NAV` exactly or
the site describes itself two ways; they had already drifted, index still
carrying a "Climate research" heading that `NAV` dropped five weeks earlier.
Note that `nav_for()` renders a group holding one page as a bare link to that
page and drops the category name, so a one-page group cannot appear in the bar
at all - which is why the neuron page sits in Misc rather than in a "Mind"
group of its own until the beauty project joins it.

`python3 rebuild_nav.py --dry-run` reports what would change and writes
nothing. Use it before the real run.

---

## 4. The house style

These are settled decisions, arrived at over many rounds. Follow them.

**Prose.** Standard technical English, "half Stephen Austad, half the
standard". Plain declaratives. No marketing voice.

**No development history on published pages.** Never write "an earlier version
of this did X", "this used to be Y", "what this replaced". The page states what
the thing *is*. Development history belongs in code comments, where it is
useful to a maintainer and invisible to a reader. This rule has been broken
before and had to be swept out; there is an audit for it in §7.

**Never invent data.** Every number on the site traces to a public data set, an
exact computation, or a named publication. If a number cannot be sourced, the
feature is not built, and the page says why it is absent. Anything assumed is
explicitly labelled *assumed* rather than presented as measured. This is the
single most important rule in the project.

**Colour and layout.** Light ground, one accent: the "Yacht club" palette
since 2026-09-04 (paper `--bg #F2F0EF`, ink `#241E1A`, deep blue `--acc
#245F73` for anything actionable, brown `--moss #733E24` as the second data
colour; `PALETTE_TRIAL_2026-09-04.md`). Single theme, no gradients, no
washes. All colours are custom properties in `style.css` `:root`, and the
figure builders take theirs from `sitefig.py`, which is the same set by
name and value; the five apps copy the set into their own `:root` because
each must work alone from a folder. The one dark scene left is the atlas
app's globe (and the same globe in the climate-cost app), drawn for the sea
it sits on; the atlas page's globe is a figure on paper (it was the home
page's until Phase 4, 2026-09-04, when the layer diagram became the hero:
a globe is a map, and the first picture should say "this is a model", not
"this is a map"). Until 2026-09-04
this paragraph described the previous palette (violet accent, dark ground,
WebGL hero trails); that stylesheet is in git before that date.

**The home page's hero is a live canvas, and that trade was made
deliberately on 2026-09-06.** `site/assets/hero.js` draws one of three named
nonlinear systems - double pendulum, Lorenz attractor, Burrau's three-body
problem - integrated in the browser from published equations. Phase 4's
argument above, that the first picture should say *this is a model*, was
traded for *this is a nonlinear system*. **That is a weaker claim and it is
written down here so the next audit finds an argument rather than
re-deriving it.**

`DESLOP_AUDIT_2026-09-04.md` F6 cut `force-bg.js` - a real, physically
simulated subgraph of the published atlas behind the prose - for being
"decoration that restates the page at illegible size", on the grounds that
"a reader cannot read them, so they are texture, and texture made from data
is still texture". A fixed full-viewport canvas behind the prose is
structurally the same thing returning. What differs: the hero does not
restate the page and does not claim to be the energy model; it is drawn at
full size, where a trajectory that never repeats is the whole of what it
has to say, which is the exact legibility test F6 applied; and every
caption names the system, its parameters and its integrator and says in as
many words that it is not the energy model.

What still lands is T15, decoration that is not the content: this is a
picture of a nonlinear system on a page about energy modelling, and its
defence is metaphorical. That was the trade Andrew asked for, and the
captions are what keep it honest. The design and every measurement behind
it are in `03 RESEARCH/rename-hero/STAGE2_PLAN.md`.

**The captions no longer say "not the energy model", and that was deliberate
on 2026-09-06.** They were cut to about a dozen words each - the long versions
were the longest text on the first screen and read as an apology - and the
explicit denial went with the length. What the three still carry is the name of
the system, its date and its published parameters:

> Three double pendulums, released 0.001 rad apart.
> Lorenz attractor, 1963. σ = 10, ρ = 28, β = 8/3.
> Burrau's three-body problem, 1913. Masses 3, 4 and 5.

So the F6 answer above now rests on the weaker of its two legs. The strong one
is unchanged: each caption names a published system, so the figure cannot be
mistaken for a drawing of the atlas the way an unlabelled 200-node subgraph
could. The one that went is the sentence that said so outright. **If a future
audit reaches for F6 again, this paragraph and `hero.js`'s header are where the
argument lives - it is no longer on the page**, and anyone restoring it should
know it was removed on purpose rather than lost.

The home page also stopped carrying the atlas card, the figure mosaic and the
model chart the same day: it is the hero and the index now, and the Energy nav
group is the only route to atlas-app, atlas, model and library. That orphaned
seven generated PNGs, and both builders were retired rather than left writing
files nothing reads (`unpublished/RETIRED.md`).

**The index.** The home page's projects are an index, not cards: "THE INDEX
SPEC" in `style.css` beside `.index .entry`, changed before the code. An entry
is a kicker, a linked title and one sentence, a hook, not a summary; no
figure; a rule above, 16px above and 18px below, every entry the same shape.
There is no copy budget because one sentence always fits, and
`tests/test_layout.js` counts the sentences, fails an entry with more than
one or with a figure, and fails a sentence that opens by repeating its title.
This replaced THE CARD SPEC on 2026-09-05 after four passes of card fixes
(the crop, the 3:2 aspect, the dead space, the alignment, then a copy
budget): a 271px thumbnail cannot hold its own beside a paragraph, and a
full-width figure lets the tallest figure set the page's rhythm. The figures
live on the pages that explain them; `build_thumbnails.py` now makes only the
mosaic's six.

**Figures.** Generated by Python, never hand-drawn, always regenerated from the
live payload. A panel is labelled only through `sitefig.panel()`, and
`sitefig.save()` refuses a figure with any other axes title. An audit reads
titles through `sitefig.titles()`, never `ax.title` (see the trap in section 8).
Every figure builder runs an `audit()` that reports overlapping
or off-canvas text and must report **0 layout problems**.

---

## 5. The build scripts

Run everything from inside `00 PUBLISH/`. Scripts that mutate the payload take
`--apply`; without it they print a report and change nothing. **Always run the
report first.**

### The atlas pipeline, in order

| Script | What it does |
|---|---|
| `build_atlas_global.py` | Builds the base payload from `19 Atlas v6/raw/`. The expensive one. |
| `prune_atlas_edges.py` | Removes links the model should not have drawn (climate→earthquake). |
| `build_atlas_space.py` | Adds the sun, insolation bands, ENSO and NAO. |
| `build_atlas_brain.py` | Joins districts to GeoNames population, wires them into behaviour. |
| `build_scenarios.py` | Rebuilds the 60-scenario catalogue in 9 categories. |
| `build_atlas_figures.py` | Regenerates the 11 library figures. |
| `build_throughlines.py` | Regenerates the big throughlines sheet. |
| `build_model_chart.py` | Regenerates the home-page overview chart. |
| `build_layer_diagram.py` | The nine layers as bands with their counts, and every layer-to-layer link as an arc, one-way on the right and two-way on the left, stroke by edge count. Counts, links and the rank rule are read from the payload and `atlas-app.js`; nothing is typed in. Three renders: 1140 (above the atlas table), 714 (the home-page hero) and 350 (a phone). The band order is the one that minimises arc crossings, checked over all 120, and `update_atlas_pages.py` orders the layer table to match. In `tests/test_generators.py`. |
| `build_hero_figure.py` | Draws the globe (`hero_globe.png`) from the atlas payload: stations, settlements, coastlines, on paper. The home-page hero from 2026-09-04 22:32 until Phase 4 the same night; now under the intro on `atlas.html`. |
| `unpublished/build_bookshelf_demo.js` | Retired with the bookshelf (2026-09-05): renders the app's demo shelf to `bookshelf/demo-wallpaper.png`. Kept runnable from `unpublished/`. |
| `build_favicon.py` | The favicon and touch icon from one description, in the palette. |
| `update_atlas_pages.py` | **Regenerates `atlas.html` wholesale** and replaces stale figures in `model.html`. |

### Site-wide utilities

| Script | What it does |
|---|---|
| `rebuild_nav.py` | Rewrites the nav on every page from the `NAV` list. |
| `build_climate_figures.py` | The two climate-research diagrams (`nitrogen_fixation.png`, `running_shoe.png`). Boxes are drawn as text bboxes and arrows run underneath them, deliberately: a box sized by a guessed line height is a bug the layout audit cannot see. The shoe outline functions here are duplicated in `site/running-shoes-app.html`; if one changes, change both, because the flat figure and the 3D model are meant to be the same shoe. |
| `add_citations.py` | Attaches superscript citations anchored to phrases, not positions. Armed and round-tripping all seven pages it owns since 2026-09-05; it was disarmed for a day while three defects it could not reproduce were fixed, and its docstring records them. |
| `build_sitemap.py` | Writes `site/sitemap.xml` from the pages that exist, apps excluded. `--apply` to write; without it, reports and lists the urls that would be added or dropped. Carries each page's existing `lastmod` over so a run does not churn every date, which is also what makes it idempotent enough for the drift check. It was a hand-kept list and was four pages behind on 2026-09-05. |
| `sync_assets.py` | Copies figures from project folders into `site/assets/`. |
| `bust_cache.py` | **Run before every publish.** Stamps `style.css`, the JS and every image with a content hash. Does not stamp what CSS `url()` references (the fonts). |
| `sync_img_dims.py` | Keeps every `<img width height>` equal to the file's pixels. |
| `build_thumbnails.py` | The six mosaic thumbnails on the home page from the library figures, whole at their own aspect (`sitefig.thumbnail()`). The five card thumbnails went with the cards on 2026-09-05. |
| `rezip_downloads.py` | Rebuilds the atlas, heat, storage and skyline `-code.zip` (the bookshelf's last build is in `unpublished/downloads/`; `atlas-code.zip` is a named-files archive, `ATLAS_FILES`, carrying the builders, the app, the fonts and the tests, with `atlas-code-README.md` as its README, since 2026-09-05) from their source folders. One run at a time (lock file in `site/downloads/`); each archive is written beside itself and moved into place; `--verify` compares a fresh build against what is shipped without writing. Never ships `__pycache__/`, `outputs/`, node state or a built page — storage-code.zip did, on 2026-09-04. |
| `tests/test_generators.py` | Runs every text generator into a copy of the tree and diffs the result against `site/`. **Run it before trusting any generator**, and run a generator for real only after the check says it agrees. |
| `build_site.py` | **Retired. Never run it.** The original generator, last valid 2026-08-01: it writes pages that are no longer on the site (dac, holdup, energy-web), a nav from before the regrouping, and its own icons. `tests/test_generators.py --retired` shows what it would do to the tree. |
| `publish.sh` | Mirrors `site/` into the Pages repo and commits. `--dry-run` first. |

### Typical loop after changing the model

```bash
python3 build_scenarios.py            # report
python3 build_scenarios.py --apply
python3 build_atlas_figures.py
python3 build_throughlines.py
python3 build_model_chart.py
python3 update_atlas_pages.py --apply
node tests/test_atlas_interaction.js
python3 bust_cache.py
./publish.sh --dry-run
```

---

## 6. The atlas data model

`site/assets/atlas-data.js` is one line: `window.ATLAS={…};`. Parse it as
`raw[raw.index("=")+1 : raw.rindex(";")]`.

Columnar, dictionary-encoded. Arrays are parallel and all length `n`:

| Key | Meaning |
|---|---|
| `n` | node count |
| `lat` `lon` | coordinates |
| `kind` | index into `kinds` |
| `tab` | index into `tabs` |
| `res` | resilience / inertia, 0–1 |
| `name` | display name — **carries data**, e.g. `"CHN coal supply (54.4% of power)"` |
| `src` | index into `srcDict` (provenance string) |
| `es` `et` `ew` | edge source, target, weight (parallel, length = link count) |
| `idMap` | `{"GRID_USA": 1234}` — stable ids for ~3,231 addressable nodes |
| `mwMap` `popMap` | sparse `{nodeIndex: value}` |
| `scenarios` `scenarioCats` | the prepared-change catalogue |
| `anatomy` `brain` | brain scenery and channel positions |
| `co2` `temp` `coast` | measured series and coastline rings |

**Node kinds** (12): `sun`, `insolation`, `weather`, `climate`, `event`,
`market`, `supply`, `grid`, `station`, `district`, `consumer`, `psych`.

**Id prefixes:** `SUN_TSI`, `INSOL_15N`, `WX_ENSO`/`WX_NAO`, `CLIMATE_SYS`/
`GLOBAL_TEMP`, `MKT_*`, `SUP_{ISO3}_{fuel}`, `GRID_{ISO3}`, `DIS_*`, `CON_*`,
`PSYCH_*`, `EVENT_*`.

### The propagation engine

The engine exists **twice** and the two must agree:

- `site/assets/atlas-app.js` — the browser copy, the model of record.
- `build_throughlines.py` `engine()` — sparse linear algebra, used by every
  figure script.

The iteration is
`s ← (1−λ)·s + λ·tanh(b + damp·(A·s))`, λ = 0.95, damp = 1 − 0.6·res, stopping
when the largest move is under 1e-5 or at 60 rounds.

Five properties that took a long time to get right — **do not undo them**:

1. **A node takes the weighted mean of its drivers, not their sum.** Summing
   gave the operator a spectral radius of 26; it could not converge and every
   scenario saturated everything.
2. **Layers carry an exogeneity rank** — sun 0, insolation 1, weather 2,
   climate 3, event 4, everything else 5. An edge is two-way only *within* a
   rank. Anything crossing a rank drives and is not driven, because an
   earthquake acts on a grid and no grid causes an earthquake.
3. **Fan-in normalisation**: each edge is divided by the number of edges
   arriving at the same node from the same layer, so a layer speaks once
   however many members it has.
4. **Row normalisation** by the node's total in-weight, which makes the
   spectral radius exactly 1 and the iteration a contraction.
5. **A response is not promoted, and neither is the coupling it answers.**
   Added 2026-09-05, because property 2 had a casualty: making every
   same-rank edge two-way gave the district→consumer demand edge (+0.50) a
   back-channel, consumer→district, which property 3 filed in the same
   fan-in bucket as the consumer's −0.01 response edge, and the bucket
   summed to +0.49. Demand response was in the payload and never in a run:
   pushing a consumer moved its district up. The rule states the reason
   rather than the instance: a negative edge within a rank is a response
   (the site's definition of a negative link, relief rather than stress),
   the reverse edge is the coupling it answers, and the response is that
   coupling's back-channel, so the engine does not invent another. Any
   future response edge inherits this. Not a kind-pair rule and not a
   payload flag: the payload already says which edges are responses, by
   sign. Today it selects exactly the 1,142 consumer↔district pairs;
   `tests/test_demand_response.py` pushes consumers and asserts their
   districts fall. Rejected on the way: a per-edge type flag (a payload
   change, so a rebuild or a second hand-patch), and "an explicit reverse
   edge overrides the implied back-channel" (principled, but it also sweeps
   in the 571 filler-district↔grid pairs and moves 41 of the 60 scenario
   reaches, for pairs whose intent nobody can verify).

If you change any of this, change it in **both** engines and re-run
`python tests/test_parity.py`, which runs all sixty prepared changes through
both and holds every node's settled effect to 1e-12 (measured 1.1e-15 on
2026-09-05, step counts equal). Until that day no such test existed and the
claim below it was unverified.

### Scenario magnitudes

One rule: **a shock of 1.0 is the largest change of that kind in the modern
record.** Every scenario stores `label`, `cat`, `shocks`, `desc`, `basis` and
`reach`. `basis` states the number the magnitude rests on and whether it is
derived, cited, or assumed. Fuel scenarios shock **both** the supply node and
its grid, because a fuel providing X% of a country's power *is* X% of that
grid's generation — the share is read from the node name.

---

## 7. Tests and audits

```bash
python3 tests/test_markup.py           # markdown that never became HTML
python3 tests/test_units.py            # every climate-cost input against its declared unit
python3 tests/test_generators.py       # every text generator run into a copy and diffed against site/
node tests/test_atlas_interaction.js   # boots the real app against a three.js stub
python3 tests/test_parity.py           # the browser engine against the figures' engine, all 60 scenarios, to 1e-12
python3 tests/test_payload.py          # the payload's SHA-1 against atlas_payload.json (trap 23)
node tests/verify_hero_systems.js      # what the home page hero's captions claim, recomputed; --break for the mutations
python3 tests/test_demand_response.py  # push consumer groups, districts must fall (engine property 5)
node climate-cost/test_scene.js        # the climate-cost visualiser: JS engine against lca.py, layout, overlap; jsdom and three r128 from tests/node_modules
node tests/test_layout.js              # Playwright: marginalia, measure, hierarchy at 1440/1024/390
node tests/probe_scene.js              # prints what is actually in the scene graph
python3 build_atlas_figures.py         # must say "0 layout problem(s)"
python3 neuron/test_neuron.py          # the measured neuron: z provenance, placeholder widths, the cascade, the parser
python3 neuron/fig_neuron.py           # must say "0 layout problem(s) in total"
```

Project suites this block has not always listed, and which the tree has:
`food/test_food.py`, `beauty/test_beauty.py`, `economy/test_economy.py`,
`shoes/test_shoes.py`, `neuron/test_neuron.py`. Section 11 is the current
inventory; this block is a claim about it (trap 11).

All of them must pass before a publish; section 11 says what each one
catches. The Python checks need numpy, scipy, matplotlib and Pillow; the
node suites use the playwright, jsdom and three in `tests/package.json`
(`npm install` in `tests/`).

**`_deslop/` is gitignored, so one edit the rig needs cannot be committed.**
`_deslop/measure.js` opens every page with no query string. The home page
picks one of three systems at random per load (`site/assets/hero.js`), so an
unpinned run measures a different system each time and its CPU and weight
columns are not comparable between passes - and nothing says so in the
output. The edit is two lines, near the top and at the `page.goto`:

```js
const HERO = process.env.HERO ? '?hero=' + process.env.HERO : '';
...
await page.goto(BASE+p+'.html'+((p==='index'&&!app)?HERO:''), {...});
```

then `HERO=pendulum node measure.js index`, and again for `lorenz` and
`threebody`. **Anyone measuring `index.html` must re-apply this first, or they
are measuring a random system without knowing it.** It cannot live in the repo
because `.gitignore` line 6 excludes the whole directory; that exclusion is
deliberate (the rig carries hundreds of megabytes of screenshots and results)
and is not worth changing for two lines, so the two lines live here instead.

`tests/three-stub.js` is a hand-written partial three.js so the app can be
booted headlessly. `window.__atlasUI` and `window.__atlasScene` are test hooks
deliberately exposed by `atlas-app.js`.

The interaction test currently asserts: every node kind is clickable, the
brain/map switcher works, the opening tab is the plant layer, the impact web is
cleared with the selection, and every scenario is filed, targets real nodes,
moves something, and states a basis.

Useful ad-hoc audit — stale text and retrospective prose across the site:

```python
STALE = ["7,192", "13,826", "86,601", "1,906", "15,247", "seven layers"]
RETRO = r"(an earlier version|used to be|this used to|had been|what this replaced)"
# strip <script> blocks first: the app pages inline megabytes of JSON
```

---

## 8. Traps that have already caused bugs

Read this section. Every item is a real bug that shipped.

1. **Magic indices.** `tab = 4`, `setTab(4)`, `ti === 6` were hard-coded tab
   indices. Inserting two tabs silently turned the plant layer into the markets
   layer and the brain into the demand tab. **Resolve tabs by id or from the
   data, never by number.**
2. **`sync_assets.py` used to copy the two model figures out of
   `18 Final Deliverables`**, which is a retired 7,192-node snapshot. That
   overwrote the regenerated figures with figures of a model that no longer
   exists. Those entries are now removed with a comment; do not re-add them.
3. **Browser caching looks exactly like a change that did not take.** Figures
   and CSS keep their filenames. Run `bust_cache.py` before publishing.
4. **Layout audits must measure what is drawn.** Titles and tick labels are not
   in `ax.texts`. Hidden axes keep their label objects. Legend text is a
   separate artist. Log axes keep tick objects outside the visible range. All
   four have caused a "0 problems" report on a broken figure.
5. **`float: right` does nothing in a flex row**, and `margin-left` on a
   centred element kills `margin: 0 auto` and drags the whole page left.
6. **Country code mismatches.** GeoNames uses ISO2, grids use ISO3, the WRI
   plant file uses full country names. Two separate bugs came from matching the
   wrong pair. Join on the file that carries both columns and assert the match
   rate.
7. **Never trust a number in prose.** Node and link counts appear in many
   pages. They are regenerated by `update_atlas_pages.py`. When you change the
   payload, re-run it and then grep for the old numbers.
8. **Generic numeric substitution collides with itself.** A regex replacing a
   bare number rewrote a value another rule had just generated correctly.
   Generate text *after* patching, never before.
9. **WebGL ignores `linewidth`** on effectively every platform. Line weight has
   to come from geometry, density or brightness.
10. **Additive blending saturates to white.** A bright sky blue stacks into
    white exactly where trails overlap most. Keep per-segment brightness low.
    (It happened anyway, for a month, to the plant layer: 34,936 sprites over
    Europe and the US east coast summed to solid white in both `hero-gl.js`
    and `atlas-app.js`. Fixed 2026-09-04 by scaling the sprite output.)
11. **Anything that describes the site can describe a state the site has left.**
    Four instances in one session, 2026-09-04: `rebuild_nav.py`'s `NAV` list
    still had a "Climate research" group five weeks after the pages dropped
    it, so running the generator would have silently reverted a deliberate
    change; this file listed four `unpublished/` pages as live and counted
    "three" JS files when there were thirteen; and the deslop brief carried
    "the palette passes AA" from an audit that never measured text on the
    accent (it was 2.91:1 on every button). The check is cheap every time:
    run the generator and diff, list the directory, compute the ratio.
    Nobody ran it for a month. When a doc, a script and the tree disagree,
    the tree is the fact and the other two are claims.
12. **A claim that flatters the page's own argument is the one nobody
    audits.** `climate-cost.html` argued for a month that allocation decides
    the answer, and illustrated it with a leather shoe going from 3.66 to
    11.65 kg CO2e under mass allocation, "nearly tripled". The model gives
    4.40. The 11.65 was the whole shoe scaled by the ratio of two allocation
    factors, as if every gram of it were hide, when the hide is 9% of it;
    the video carrying the number had no generator in the repo, so nobody
    could re-run it, and two audits looked straight at it and discussed
    its layout. Three things let it survive: the number agreed with the
    thesis, it lived in an asset no script produced, and the field it
    scaled meant three different things (share, amortisation, shipment
    mass) so "scale the allocation" was not a defined operation. Fixed
    2026-09-04 (`CLIMATE_COST_FIX_2026-09-04.md`): every figure on a page is
    built by a script in the repo from the model, every allocation share
    carries its `basis`, and the showcase moved to the product where the
    claim is true (cheese). The check: when a number makes the page's
    point unusually well, recompute it before admiring it.
    The same sweep found the opposite case, and it sharpens the lesson.
    The train's track was charged through the road process at a scaled
    amount, 2.1 g CO2e per passenger-km; UIC's 2016 review of rail
    infrastructure puts it at 6-7 g. A proxy nobody sourced, in the one
    entry whose whole point is to look absurdly good, and it survived for
    the same reason the shoe did: nobody had a motive to check it. (It
    was expected to run against the page - rail priced as road ought to
    overstate rail - and it turned out to flatter it after all; the
    direction is not knowable without the source.) So the trap is wider
    than flattering claims: **claims nobody has a motive to check go
    unaudited.** `tests/test_units.py` now checks every input against its
    declared unit whether or not anyone is curious about it.
13. **A generator is a claim about a shipped file, and it goes stale
    silently.** Nothing fails when the tree moves on without the script; the
    failure comes later, when someone trusts the script and it reverts the
    change. Found on 2026-09-04 by running every generator into a copy of
    the tree and diffing (`tests/test_generators.py`): `update_atlas_pages.py`
    raised on its first line of work, because the deslop pass had given
    `<main>` a class and it searched for the bare tag; its body also carried
    a "Limits" section that has never been on the shipped page and lacked the
    layer figure that has; `heat-code.zip` had been restored from a copy two
    edits behind `heat/`; `storage-code.zip` shipped `__pycache__/` and
    `outputs/` because the rezip walked a folder a builder had just run in;
    the stamps on `longevity.html` were behind three figures. Earlier the
    same day, `longevity-app.html` and `climate-cost-app.html` had been
    edited in place while their `template.html` stood still, and
    `skyline-code.zip` carried a template three lines behind `site/`; the
    sessions that owned them caught the templates up, and the check now
    confirms all three agree. The rule: run the check before the generator,
    and run the generator for real only when the check says it agrees.
14. **A brief's factual premises are leads, not facts.** A brief is written
    from memory of the tree, and the tree moves. Corrections made on
    2026-09-04 alone: "the palette passes AA" (2.91:1 on every button); "the
    1,144 negative links line is on atlas.html" (it is on model.html); "Option
    B has no gradients" (fourteen remained); "commit `c2d02aa` swept up
    `skyline/skyline-app.html` and `package*.json`" (they were tracked by
    `34cfe58` and `577d582`; what `c2d02aa` actually contains, under a
    climate-cost message, is the bookshelf write-up and four longevity
    lines); "add the flattering-claim trap" (item 12 was already here); and
    this file's own §2, which pointed at folders that are not merely moved
    but absent from the workspace. Each check cost seconds: a directory
    listing, `git show --stat`, a grep. Check the premise before acting on
    it, and when it is wrong, say so and quote it rather than quietly
    building on the corrected version.
15. **A fix that deletes the comment explaining an earlier fix will be
    undone by the next person, including when the next person is you.**
    Three times on 2026-09-04: the margin-scene clamp that kept marginalia
    off the figures lived in a script the deslop pass deleted, and the
    collision came back; `rebuild_nav.py`'s NAV list was corrected without a
    note and would have been trusted again; and the mosaic's `object-fit:
    contain` carried a comment saying exactly why not `cover` ("a centred
    cover-crop was cutting whole panels and axis labels off"), the dead-space
    fix replaced it with `cover` and deleted the comment, and the crop came
    back - this time baked into the thumbnails themselves by
    `sitefig.thumbnail()`, where no CSS could show it. The rule: a rule that
    exists because of a bug carries the bug in a comment beside it; when you
    replace the rule, the comment moves to whatever replaces it; when you
    delete a file, its warnings go into the thing that took over its job
    (the grid comment in `style.css` is the margin-scene clamp's).
16. **A test that reproduces published summary statistics does not pin the
    parameters behind them.** `economy/` computes everything it says from five
    transcribed cost-of-running polynomials, and the obvious guard is that the
    source paper states three results of its own: a 1% metabolic saving is
    worth 1.17% of speed at 2.60 m/s and 0.65% at 5.72 m/s, and a 4% saving is
    worth 2.64% at 5.72. Reproducing all three to 0.008 of a percentage point
    looked like proof the transcription was right. It is not. Perturbing any
    single coefficient by 1% still passes, and a 5% error in the linear term
    *lowers* the residual below what the correct coefficients give. Four
    parameters, three published numbers, and all three are ratios evaluated at
    two speeds, so errors in different terms cancel inside them. The check
    constrains the shape of the curve and says almost nothing about the
    coefficients.
    The fix is to check the parameters as parameters: `economy/test_economy.py`
    holds the coefficients a second time, apart from `model.py`, and compares
    them digit for digit, so an edit fails whether or not it moves a published
    number and a curve refitted to other data cannot be substituted quietly.
    The published-results check is kept, because it does catch gross errors -
    a sign flip on the linear term lands 0.25 pp out.
    **The general form: reproducing a source's summary statistics is evidence
    about behaviour, not about parameters. The test is only as strong as the
    number of independent published quantities it checks against, and it is
    worthless where those quantities are degenerate combinations of the
    parameters** - three ratios at two speeds cannot separate four
    coefficients however precisely they are reproduced.
    Two sibling projects were checked against this on the night it was found,
    and both are in better shape, which is what the rule looks like when it is
    satisfied. `beauty/` reached the sharper version independently the same
    night and is the pattern to copy: `model_maths()` in
    `beauty/test_beauty.py` fits synthetic data built from known coefficients
    and asserts the estimator recovers them, which is a direct test of the
    parameters rather than of an aggregate, and it adds two invariants that
    hold whatever the numbers are - that a category-only model's g-computed
    means equal the raw group means, and that no dropped term can raise
    R-squared. Its docstring also records what it does *not* reach: the
    synthetic frame arrives already transformed, so nothing `join()` does to
    build one is covered.
    **That test was written after this trap, not before it, and the sentence
    above was wrong when it was first written.** `beauty/` had only the drift
    check then - it recomputed the coefficients through the same `fit_all()`
    that produced them and compared - which is the weak shape this trap is
    about. Its approved plan says so in as many words and says nothing about
    synthetic recovery. The session that wrote this trap set out to verify
    that claim and reported the opposite; the operator's original suspicion,
    that `beauty/` was of the weak shape, was correct and was talked out of.
    A verification that returns a confident answer without pinning the thing
    it claims to have checked is this trap happening to the trap. Two lessons
    stand: check the file, not the plan; and a sibling project's clean bill of
    health is a claim like any other. The continents work
    (`03 RESEARCH/continents/`) fits three Euler-pole parameters per plate and
    `crosscheck.py` compares them against NGL's published model station by
    station, in mm/yr - hundreds of independent comparisons over a velocity
    field that varies across them, not a handful of summary figures. The count
    is what saves it.
17. **Break every new test before trusting it.** A test nobody has seen fail
    is a claim, not a check. Three defects in the `economy/` build on
    2026-09-05, and each was found by a different active method, none by
    reading:
    - trap 16 above, by deliberately corrupting a coefficient and watching the
      test pass;
    - a margin note reading "2:56 pace" beside prose that generated 2:55, by
      opening the rendered page and comparing it against itself. The drift
      check could not have caught it: it compares the page to what the
      template renders, and the wrong number was in the template;
    - a stated 2.9% that the model contradicts with 3.3%, by building the
      thing. It came from applying a transfer coefficient of 0.70 at a pace
      where the elasticity is 0.81, it was written into the approved design,
      and it survived the plan being read by two people.
    So: after writing a test, introduce the defect it exists to catch and
    confirm it fails; then fix the defect and confirm it passes. Both
    directions, every time. `economy/test_economy.py`'s docstring records what
    each of its checks was proven to catch and, for the weak one, what it was
    proven not to.
    `beauty/break_model.py` is the mechanised form: it mutates
    `build_beauty.py` in memory, one realistic fault at a time - a misaligned
    design matrix, a dropped reference category, an adjusted mean that forgets
    to clear a species' own category, a drop-one R-squared reported with its
    sign flipped - and reports whether the test noticed each. All four are
    caught, one of them by raising. The first attempt at it is worth knowing
    about: the intended "swapped columns" mutation swapped the lookup that
    `design()` reads *both* a column and its name from, so it swapped them
    together and changed nothing. A mutation that does not mutate reads
    exactly like a test that works. Check that the clean run and the mutated
    run actually differ.
18. **Placeholder data left in a project folder is one `rezip` away from being
    published.** On 2026-09-05 `beauty/` held `data/openalex_counts.csv` whose
    rows had been generated to exercise the build while the real fetch waited
    on an API key. Another session ran `rezip_downloads.py` across every
    target that evening and walked `beauty/` as it stood. The archive it wrote
    does not contain that file, and the only reason is timing: the placeholder
    was written after that run and deleted before the next. Nothing in the
    repository would have stopped it. A fabricated table inside the download
    archive of the page about research that does not trace to its sources is
    the version of this failure that would have been hardest to live down.
    The fix is a stamp. Every `beauty/fetch_*.py` writes the date it ran into
    each row it appends, and `check_settled()` in `build_beauty.py` refuses to
    build when any value in that column is not a date, naming the file and the
    script that should have produced it. Placeholder data can no longer reach
    a payload, so it cannot reach a figure, a page or an archive.
    **The general form: a project folder is shared surface, and tooling you do
    not control runs across it on a schedule you do not set. Make the
    difference between real and provisional data machine-readable rather than
    something you intend to remember.**
19. **A rule about what must not ship belongs with the code that ships, not
    with the project it constrains.** `beauty/` may not redistribute IUCN Red
    List categories; the Red List's terms forbid it. That rule lives as a
    `skip=` tuple on the project's target in `rezip_downloads.py`, with its
    reason in the comment beside it, and *not* inside `beauty/`. The placement
    was tested by accident on 2026-09-05, in the best way available: another
    session, which knew nothing about the Red List or the carve-out, rebuilt
    every archive, and the one it produced for `beauty/` contained no category
    column, no `data/raw/` and no joined species table. The rule held because
    it sat in the path the archive is actually built by.
    Had it lived in `beauty/` instead - a check in `test_beauty.py`, an ignore
    file, a line in its README - it would have held only for someone who ran
    that project's own tooling first, which is exactly what the session that
    rebuilt the archives did not do.
    **The general form: put a constraint on the last piece of code that can
    violate it.** Someone will want to move this next to the project it
    describes, where it reads better. It reads better there and protects less.

20. **A gate that reads a recorded result rather than recomputing it is not
    a gate.** Trap 16 says a test reproducing a published summary statistic
    does not pin the parameters behind it. Trap 17 says break every new test
    before trusting it. Apply 17 to the gates themselves and 16 turns up one
    level higher, where it is harder to see.

    `continents/` gates its reconstruction data on an identity: at age 0 every
    plate model must hand back the point it was given. That is the only known
    answer that regime has and the whole defence against the service swapping
    its coordinate order, which would leave every distance plausible and every
    position wrong. The gate passed. `break_gates.py` then swapped lon and lat
    throughout the cached responses on purpose, and **the gate still passed**:
    it was reading `identity_worst_km` as computed and recorded by the fetcher
    at download time, not recomputing it from the cache the build actually
    reads. Damaging the data left the recorded number innocent. Five other
    gates in the same project refused the same class of damage; this one did
    not, and nothing but deliberately breaking it would have shown that.

    `neuron/` hit the same shape independently within the hour. Two projects
    finding it separately in one evening is why it is here rather than in a
    project README.

    **The rule: a gate must be computed from the artefact it is guarding, in
    the process that consumes that artefact.** A value another script wrote
    earlier is provenance, not verification - it describes the data as it was
    at some past moment, and the whole point of a gate is to catch the case
    where that is no longer true. Recording the number as well is fine and
    useful; reading it instead of recomputing is the bug.

    Two smaller instances of the same family, both from the same build:
    a probe test that passed trivially because the sampling helper read each
    file's declared header, so the control could never present the wrong
    convention it was meant to catch - the control has to force the mistake,
    not ask the code to make it; and a weighting bug that reported land as
    41,882 per cent of the Earth's surface on the gate's first run, which is
    the useful kind of wrong, because a number that far out announces itself
    where a plausible one would not.


21. **`ax.title` is only the centre title.** `sitefig.panel()` sets a
    left-aligned title, which matplotlib keeps in `ax._left_title`, so every
    audit that read `ax.title` saw no panel label at all and passed a sheet
    whose label sat on a legend (`energy_model_chart.png`, Phase 4,
    2026-09-04). Read `sitefig.titles(ax)`. A legend is also a box, not just
    its words: `build_throughlines.audit()` checks the legend's whole extent
    against every other text.

22. **A figure is drawn at the width it is shown, and the page decides the
    width.** `index.html` spent one day as `main.prose` (two tracks) and every
    714px figure and 271px thumbnail on it was scaled up 1.6x and went soft.
    It is `main.notes` again, one 714px measure, no marginalia; the CSS beside
    `main.notes` says why. `tests/test_layout.js` fails a page whose text
    blocks have more than one left edge, and a picture that breaks out
    off-centre.

23. **The payload carries two hand-patched strings, and its builder now
    produces the corrected versions.** On 2026-09-05 (PHASE5 Part 3) the
    tab subtitles "2,896 ports and benchmarks" and "34,065 settlements" in
    `site/assets/atlas-data.js` were replaced in place with "ports, price
    benchmarks and fuel supplies" and "settlements and consumer groups", and
    `build_atlas_global.py` was changed to write those. The payload was not
    rebuilt: the pipeline needs the raw data under `19 Atlas v6/raw` and a
    day. So builder and payload agree on the words and disagree on how they
    got there, and the next full rebuild resolves it. The payload is
    gitignored and too large for the generator check, so
    `tests/test_payload.py` holds its SHA-1 against `atlas_payload.json`
    (this state, recorded 2026-09-05) and fails on any change until someone
    re-records it with a note. Anyone who diffs a fresh build against the
    shipped file and finds exactly those two strings has found this note.

24. **A harness measures the machine you configured, not the machine a reader
    has, and its defaults are a configuration you did not make.** Every canvas
    measurement in this project - the 2,273 ms/3s baseline, every idle-CPU
    figure in the deslop rig, the whole `TRAIL_DPR` sweep - was taken at
    **deviceScaleFactor 1**, because that is Playwright's default and nobody
    passed anything else. The panel these were run against is 3840x2400. So
    the back canvas measured **1.3 megapixels** in the harness and is **9.22**
    on the machine, and `hero.js`'s `TRAIL_DPR = Math.min(devicePixelRatio, 2)`
    was clamped to 1 in every run that was supposed to be testing it.

    **What survives and what does not.** The comparisons hold: the 2,273
    baseline and everything measured since came off the same rig at the same
    ratio, so "this is cheaper than that" is still true. The absolute numbers
    do not - they understate the real canvas cost by up to 4x. And one
    conclusion is simply wrong: "raising the trail resolution costs nothing
    measurable", recorded on 2026-09-06 and used to ship `TRAIL_DPR = 2`, was
    drawn from a harness in which dpr 2 could not take effect. It may still be
    the right setting; it was not measured.

    The same run added `1920x1200` to the scroll harness for the same reason.
    `1440x900` was the only desktop size ever used, and it understates this
    display maximised by 78%.

    **This is trap 20 for the third time** - a gate reading something other
    than the artefact it guards. Trap 20 was about reading a recorded value
    instead of recomputing it; this is about recomputing it faithfully in a
    world you configured wrong. The general form is wider than either: **a
    measurement inherits every default you did not set, and a default is a
    decision somebody else made about a machine that is not yours.** Before
    trusting a performance number, print the configuration it was taken under -
    device ratio, viewport, renderer, whether the GPU is in play - beside the
    number. `tests/test_scroll_jank.js` prints its ratio and renderer in its
    header line for exactly this reason, and takes `--real` because headless
    Chromium composites in software and a fixed canvas under a scrolling layer
    is a compositing question.

---

## 9. Adding a new project

The pattern every existing project follows:

1. Build the project in its own folder (either a new numbered folder, or a
   sub-folder of `00 PUBLISH/` like `climate-cost/`).
2. Generate figures into that folder's `outputs/`.
3. Add a prefix mapping in `sync_assets.py` if figures need copying, or write
   them straight into `site/assets/` (preferred for anything generated from a
   live payload).
4. Write `site/<project>.html` following the skeleton in §3: `h1`, `dim`
   standfirst, a card with the try-it link **directly under the intro
   paragraph**, then `What it finds` / `Method` / `Limits` / `The code` /
   `Sources`.
5. If it is interactive, build `site/<project>-app.html` as a standalone
   full-screen page with inline CSS, and link it with `target="_blank"`.
6. Add the page to `NAV` in `rebuild_nav.py` under Energy or Others,
   and re-run it.
7. Add a `downloads/<project>-code.zip` and a row in `code.html`.
8. Run `add_citations.py`, then `bust_cache.py`, then `publish.sh --dry-run`.

---

## 10. Publishing

### The mirror

`site/` is mirrored into `~/andrew-silvestri.github.io` and committed.
`index.html` must be at the repo root and `CNAME` must say
`andrewsilvestri.com` — Pages fails silently without either.

```bash
python3 bust_cache.py
./publish.sh --dry-run
./publish.sh
```

Use `publish.sh` (Git Bash) rather than `publish.ps1`; the bash version is the
one that gets tested on this machine.

The mirror's remote is `andrew-silvestri/andrew-silvestri.github.io`, branch
`main`. `publish.sh` clones it if it is missing and hard-resets it to
`origin/<branch>` before copying, so the mirror is disposable: it holds no
state that is not either in `site/` or in its own history. Its history is the
rollback: the commit before the current head is the version to reset to.

### This repository, and where the only copy is

`00 PUBLISH` **does** have a remote, added 2026-09-06:
`andrew-silvestri/andrewsilvestri-source.git`, branch `master`, and
`git ls-remote --heads origin` should answer with the local head. Earlier
briefs said it had none; that was true when they were written and is not now.
Push after any session that changes the tree — the remote is the off-machine
copy of the source, which the mirror is not, because the mirror holds only
`site/`.

The `git bundle` habit predates the remote and is still worth keeping before
anything destructive, but a bundle on `~/Desktop` is on the same disk as the
repository and is not a backup:

```bash
git bundle create ~/Desktop/00-PUBLISH-$(date +%F).bundle --all
```

The bundles on disk are dated 2026-09-04 and 2026-09-05. The remote is newer
than all of them.

### What a fresh clone cannot serve

`site/downloads/` is gitignored in full, so **none** of the source archives are
in this repository. `site/code.html` links sixteen of them:

- Ten are rebuilt by `python3 rezip_downloads.py` — atlas, continents, economy,
  food, heat, longevity, neuron, shoes, skyline, storage. (It builds an
  eleventh, `beauty-code.zip`, which `code.html` does not link yet.)
- **Six have no generator at all**: `climate-cost-code.zip`,
  `deliverables-code.zip`, `model-code.zip`, `web-v3-code.zip`,
  `web-v4-code.zip` and `web-v5-code.zip`. They exist only in the working
  copy's `site/downloads/` and in the published mirror. Nothing in the tree can
  reproduce them. If they are lost, they come back from
  `~/andrew-silvestri.github.io` or from the live site, and from nowhere else.

So a clone of this repository serves `code.html` with sixteen dead links until
`rezip_downloads.py` runs, and with six dead links for good afterwards.

---

## 11. Current state, 6 September 2026

**Live: the mirror's `5f91a1b`**, 2026-09-07 — the caption and footer as one
viewport-fixed block at the bottom left, and an `<h1>Projects</h1>` on a page
that had carried no top-level heading since the masthead was deleted. Merged to
master here as `ad11c75`, which also brought in the root `.gitattributes` and
two new checks: `tests/test_scroll_jank.js` (scroll cadence across elapsed time,
which no gate measured) and `tests/test_exclusion.js` (rendered pixels, which
`_deslop/measure.js` cannot see).
**Rollback is `66ca9eb`**, 2026-09-07 01:51 — three pendulums and an
emptier home page. The hero draws three double pendulums released 0.001 rad
apart; the band is the whole viewport less the nav; and the atlas card, the
figure mosaic and the model chart are gone, so the home page is the hero and
the index and the Energy nav group is the only route to atlas-app, atlas,
model and library. Seven PNGs were deleted with them (six `*-thumb.png` and
`energy_model_chart.png`) and their builders retired to `unpublished/`. Merged
to master here as `93bd8dc`.
Before those, `7ff2323` (2026-09-06 18:43, the hero as first published, with
the atlas blocks still on the page) and `b5b38af` (15:42). Before those: `fee3e64` (15:22),
then `72d928e` (09-05 16:52, "Continents move in the reconstruction viewer"),
`a55c566` (15:34, "Publish: where the ground goes, and the measured neuron"),
`791dfe3` (13:51, shoes), `6d0316e` (03:01), the grid at `b768538`, Phase 5
Parts 1/2b/3/4+5, and Phase 4 Part A `a934a13` on 4 September.

Four mirror commits are dated 6–7 September and all four carry publish.sh's
canned subject line, "Rebuild site: globe atlas, 3D brain, wider layout,
corrected models" — a message that has described no publish accurately for
some time. It is the script's constant, not a claim about what changed; read
the diff, not the subject. An earlier version of this section said there was
no 6 September mirror commit at all, which was true when it was written.

`site/` here is identical to the mirror's head — checked file by file on
2026-09-06, the only differences being the mirror's `LICENSE` and the
gitignored `site/_preview/`. **Nothing in the tree is waiting to be
published.** Two earlier notes said otherwise and were behind the pages they
described: `site/neuron.html`, `neuron-app.html`, `continents.html` and
`continents-app.html` were written at 16:48 on 5 September, twenty-seven
minutes after the previous version of this section, and published four minutes
later. All four answer 200 on `andrewsilvestri.com`.

The write-ups are `PHASE4_2026-09-04.md` and `PHASE5_2026-09-04.md`; every
earlier one is listed in section 2. This section is the state, not the
history, so that nobody has to read eleven write-ups to know it.

### The nav, as shipped

Five top-level items: **Home / Energy / Running / Misc / Code.** The
retaxonomy landed and is live; the atlas did fold into Energy rather than keep
a group of its own. There is **no Mind group** — a brief that describes one
(Energy / Mind / Running / Misc) is describing a plan, not the site. `neuron`
sits under Misc, which now carries six items (climate-cost, food, continents,
longevity, skyline, neuron) against Energy's six and Running's two. Misc is
the group that will need splitting when beauty lands; that is the decision
someone will have to make, and it was not made by shipping this.
`rebuild_nav.py` writes the nav on every page — see section 8, trap 11 before
hand-editing it.

### The model

- Payload `site/assets/atlas-data.js`: **86,622 nodes, 197,068 weighted
  links**, 12 kinds, 9 tabs, 60 prepared scenarios in 9 categories. Its
  SHA-1 is recorded in `atlas_payload.json` and `tests/test_payload.py`
  holds it there; the record's note says what state the file is in (last
  full build 2026-09-04, two hand-patched tab subtitles, scenario reach
  fields rewritten under property 5). See section 8, trap 23.
- The propagation engine exists **twice** and nowhere else: `atlas-app.js`
  (the model of record) and `build_throughlines.engine()` (every figure,
  the scenario builder, the page generator). A third copy lived in
  `build_scenarios.py` until 2026-09-05; it imports the second now.
- **Five properties**, all in section 6 with their reasons: (1) a node takes
  the weighted mean of its drivers, not the sum; (2) layers carry an
  exogeneity rank and an edge is two-way only within a rank; (3) fan-in
  normalisation, a layer speaks once however many members it has; (4) row
  normalisation by total in-weight, spectral radius 1; (5) a negative
  same-rank edge is a response, and neither it nor the coupling it answers
  is promoted to two-way. Change any of them in both engines and run the
  parity test.
- What the engine measures, as of this payload: the sixty prepared changes
  settle in 5 to 43 rounds (never the ceiling of sixty), reach 2 to 77,684
  nodes, and pushing the most connected power plant moves nothing but
  itself. These are computed by `update_atlas_pages.py` and written into
  the pages; do not type them.

### The tests, and what each one catches

All of these must pass before a publish; `./publish.sh --dry-run` after.

| Test | Catches |
|---|---|
| `tests/test_generators.py` | Any of the text generators drifting from what is shipped: nav, atlas and model pages, longevity page and app, food page, neuron page and app, shoes page, economy page, citations, climate-cost app, skyline app, the download archives, thumbnails, the layer diagram, image dimensions, cache stamps. Run before trusting any generator. The `add_citations.py` entry is **armed**: the guard and the flag that bypassed it are both gone, and the comment above the entry says why. |
| `tests/test_parity.py` | The two engines disagreeing: all 60 scenarios, every node, to 1e-12 (measured 2.2e-15), and the round counts. |
| `tests/test_demand_response.py` | Property 5 regressing: push a consumer group, its district must fall. 40 sampled, `--all` for 1,142. |
| `tests/test_payload.py` | The payload changing without anyone re-recording it. |
| `tests/verify_hero_systems.js` | The hero's captions claiming something its integrator does not do. The three-body caption names an outcome and the pendulum asserts an energy bound; neither is true by construction. It found that a fixed step cannot do Burrau (energy drift 1.8e+1, encounters unresolved) and that RK4's secular drift would have breached a guessed 1e-4 bound at six hours. `--break` carries three mutations, all caught. |
| `tests/test_atlas_interaction.js` | The app failing to boot or a node kind that cannot be clicked, against a three.js stub. 19 checks. |
| `tests/test_layout.js` | Marginalia painting over content; a page with more than one left edge for its text blocks, or a breakout picture off the measure; the home page's index entries off spec (one sentence, no figure, same shape). 40 page-viewport combinations at 1920, 1440, 1024, 390. |
| `tests/test_markup.py` | Markdown that never became HTML. |
| `tests/test_units.py` | A climate-cost input against its declared unit (211). |
| `climate-cost/test_lca.py` | The life-cycle model against its published ranges. |
| `climate-cost/test_scene.js` | The page's JavaScript engine drifting from `lca.py`; a branch placed off-frustum; balls overlapping; idle cost. 25 checks; needs jsdom and three r128 from `tests/node_modules`, and fails loudly without them. First ran 2026-09-05. |
| `skyline/test_app.js` | An empty bearing; tower names colliding with each other or the compass; bars reaching into the foot. 43 checks. |
| `longevity-quotient/test_perf.js`, `test_fit_strategy.py`, `test_merge.py` | The app's render cost; the fit strategy; the merge of the three lifespan sources. 12, ok, 22. |
| `neuron/test_neuron.py` | The measured neuron, seven modes: a slice reconstruction's z reaching a figure (the characteristic failure here - Allen files ship uncorrected, so a 3D drawing from them is wrong by about 2x in one axis and looks entirely plausible); a placeholder width drawn as if it varied; the cascade and the app's 32 subset counts; what the fully-qualified set is; the gradient verdict against a rule fixed before the answer was known; page against payload; and the SWC parser against a hand-computed fixture and, with `--network`, against L-Measure's independent computation. The parser check exists because reproducing a published summary statistic does not pin a parser. |
| Every figure builder's `audit()` | Text overlapping text, text off the canvas, anything under the 12px floor, text spilling its box, a legend's box over text, a panel label not set through `sitefig.panel()` (`save()` refuses), and on a multi-panel sheet: stacked panels not sharing a column, content off-centre, a legend under a panel off its centre (`sitefig.grid_problems()`). Every builder must print 0 problems. |
| `_deslop/measure.js` then `analyse.js` | The page rig: every page and app at 1440 and 390, console errors, failed requests, text under 12px, every contrast pair against AA, weight. Serve `site/` on 8765 first. |

### Generated against typed

Generated, and regenerated by `python update_atlas_pages.py --apply` from
the payload and a run: all of `atlas.html` (the layer table in the
diagram's order, the assumed-node counts, the settle range, the reach span,
the plant push, the category table); on `model.html` the §2 node table,
the §4.4 settle range, the §5.1 weight and §5.2 inertia tables' numbers,
the §6 behaviour table, and every bare count. `rebuild_nav.py` writes the
nav on every page; `bust_cache.py` the stamps; `sync_img_dims.py` the
image sizes; `build_thumbnails.py` the mosaic's six; `build_layer_diagram.py`
the hero and the atlas figure; `rezip_downloads.py` eleven archives (§10);
`longevity-quotient/update_page.py` the longevity page's numbers.

Typed, and therefore able to go stale: the prose on every page; the
"reason" columns of the §5 tables (each checked against
`build_atlas_global.py` on 2026-09-05, but typed); `model.html` §7;
`code.html`'s rows, including each archive's file count and size; the five
sentences on the home page; the specs in `style.css`; and the two tab
subtitles inside the payload (trap 23). If a number on a page is not in the
generated list above, it was typed.

### Settled on 6 September, so that nobody re-litigates it

- **`add_citations.py` is armed, not disarmed.** The guard is gone from
  `tests/test_generators.py` and the script's own banner marks all four
  defects resolved. Verified on 2026-09-06 by copying `site/` to a scratch
  directory and running `python add_citations.py --apply` against the copy: a
  no-op on all seven pages it owns — heat (4 markers), economy (10), neuron
  (17), continents (13), food (10), storage (5), climate-cost (8) — byte-identical
  output, its only report `beauty.html does not exist`, exit 0. Any brief
  saying it drifts on `heat.html`, `longevity.html` and `storage.html`, or that
  the test is "correctly red" on it, is describing 5 September.
  `longevity.html` is a separate matter and is below.

- **`beauty/data/iucn_table1a.csv` is kept deliberately.** It is a cited
  aggregate, published as a summary table, and `beauty/DATA_SOURCES.md` is its
  authority. That is distinct from the per-species Red List categories, which
  the Red List terms do not permit redistributing and which are gitignored
  (`beauty/data/iucn_aves.csv`, `beauty/data/birds_joined.csv`,
  `beauty/data/raw/`). Checked and kept, not overlooked — do not remove it as
  a licence problem without reading that file first.

- **`neuron/data/_work/` is gitignored** (6 September): empty in a clean
  tree, it fills with about 1,500 sampled SWC files the moment the fetch runs,
  one `git add -A` away from trap 18, which is the whole reason it is listed.
  (`neuron/neuron-app.html` was the other ignored path until the app was
  retired the same day.)

- **`.claude/settings.local.json`** is ignored, and now ignored *by this
  repository* rather than only by the machine's global git ignore, so a clone
  on another machine behaves the same way. It is local tool configuration and
  is not part of the site.

### Open, by name

- **longevity.html lists ten references and carries one marker.** The other
  nine point at nothing. The page is written in place by
  `longevity-quotient/update_page.py`, which keeps whatever Sources block it
  finds, so the list is maintained by hand and the markers were never placed.
  It was removed from `add_citations.PAGES` on 2026-09-05 because a second
  owner made the citation sweep un-runnable site-wide; the entry there was
  also stale, two of its anchors having left the prose. Either the page's own
  generator should build the list from its data, as `shoes/update_page.py`
  does, or it should return to `PAGES` with anchors that match the prose.
  Whichever, it is the longevity project's call.

- **Payload rebuild.** The pipeline (`build_atlas_global.py` onward) has not
  been run since 2026-09-04; the shipped payload carries two hand-patched
  subtitles the builder now writes itself, and the scenario reach fields
  from `build_scenarios.py --apply` under property 5. Needs the raw data in
  `19 Atlas v6/raw` and a day; re-record `atlas_payload.json` after.
- **Skyline's Wikidata pull.** `build_skylines.py` cannot run because the
  raw pull was never archived; its docstring says what a fresh pull takes
  and that it is a new dataset. `rprof` (60 KB) is derivable and still
  shipped; the hijaz/insen compromise is stated, not solved.
- **Longevity's remaining leftovers** (`FIX_LONGEVITY_2026-09-04.md` §9):
  `taken_from` not shipped; six derivable payload columns (~265 KB) still
  shipped; ten long names truncate on a phone; `load_anage.py`,
  `README.md` and `DATA_SOURCES.md` describe the older pipeline;
  `lq_explained.png` uses the all-animal fit. The eight high-side
  demotions stay grade C by decision (PHASE5 Part 5).
- **The heat and storage builders** live in their download zips with their
  own `figstyle.py`, off `sitefig.py`; their audits read `ax.title` and
  have no panel labels or grids to miss. Bringing them onto sitefig is a
  rezip.
- **`code.html`'s archive rows** are typed (file counts, sizes) and drift
  whenever an archive is rebuilt; a generator would read the zips.
- **`.notes`** is on **eleven** pages - climate-cost, continents, economy,
  food, heat, index, longevity, neuron, shoes, skyline, storage - and
  `main.prose` on four (atlas, code, library, model). It is not the home
  page's class and never was a home-only hook; the home page's own hook is
  `body.home`, added 2026-09-06 because `.notes` could not gate anything.
  The CSS comment beside the rule says why the class exists. A rename
  touches eleven pages, not eight: this entry said eight until 2026-09-06,
  written before the food, economy and shoes projects landed.
- **`library.html`'s four text blocks** are `.flush`: one left edge with the
  cards, held to the measure, two widths on one page.
- **The mosaic** shows 271px renders at 232px; fine, but the only figures
  on the site not shown at their render width.
- **The museum generator** under `dumpNew/PyProjects/` must not be
  published (image rights; section 2). The warning is the only thing
  keeping it that way.

### The measured neuron (2026-09-05)

`neuron/`, `site/neuron.html` and `site/neuron-app.html`, section 2 of
`prompts/NEW_PROJECTS.md`; the research memo is `neuron/RESEARCH.md`, moved in
from `03 RESEARCH/neuron/`, which keeps the Stage 1 scratch scripts. The brief
asked for "a neuron, visualised", which is a subject and not a question; the
question the data answers is how much of the picture was measured. Two public
APIs, no key: a complete census of all 298,339 NeuroMorpho.Org reconstructions
and 1,501 files sampled across 22 archives. Of the census, 104 carry all five
things a drawing at true proportions needs, and 48 of those 104 carry one DOI,
the paper stating the shrinkage correction they were corrected with.

**Depth is the failure mode, and it is closed structurally.** Slice
reconstructions are distributed with an uncorrected z axis, compressed by
roughly a factor of two; the Allen white paper documents no correction, and
Gouwens et al. 2019 excluded z-derived features rather than fixing
coordinates. A 3D drawing from those files would be wrong in one axis and look
entirely plausible. So `swclib.load_xy()` returns two columns and is what the
figures use, `load_xyz()` takes its provenance from the file's directory
rather than from an argument, and `test_neuron.py` asserts that
`fig_neuron.py` contains no call to it by any route.

**The gradient was tested and not found.** Stage 1 measured a rank correlation
of 0.88 between how far an arbor reaches and how coarse its recorded thickness
is - across two datasets whose reach ranges barely overlap, so the correlation
was the boundary between two methods. Across 22 archives the median
within-archive correlation is -0.0026 and the pooled figure falls to 0.28. The
verdict rule was fixed before the answer was known and the page states the
negative result; `test_neuron.py` check 5 fails if the page's sentence stops
following from the rule.

**Two things worth stealing.** The parser is pinned to `tests/fixture.swc`,
whose every quantity was worked out by hand, and cross-checked against
L-Measure on the same bytes - because reproducing a published summary
statistic does not pin a parser, and the earlier "it matches Winnubst's
85 metres" check was exactly that mistake. And the sample contains archives
whose files are not in micrometres: SWC has seven columns and none is a unit,
so an archive is trusted only if the median soma of its measured-diameter
cells is a plausible soma, or, where its radii are placeholders, if no arbor
reaches further than a brain. Two of 22 archives fail, and the page says which
and why.

**The interactive was retired on 2026-09-06** (`unpublished/neuron-app.html`,
sources in `unpublished/neuron/`, entry in `unpublished/RETIRED.md`).

**Where that retirement was actually completed, because the obvious commit is
not it.** `bd9b117` on master, "neuron: retire the constraint app; figure 6
holds every order at once", writes the figure and the prose but **never moves
the files**: on master `site/neuron-app.html` still exists and
`unpublished/neuron-app.html` does not. The three renames that finish the job -
`site/neuron-app.html`, `neuron/build_app.py` and `neuron/template-app.html`
into `unpublished/` - are in `6b29932` on the `hero-nonlinear-system` branch,
under the message "Tests: recompute what the hero's captions will claim". They
landed there because a session stashed one branch's work to publish another's
and the two got bundled on the way back; the content is right and complete, the
message describes only half of it. `git log --follow -- unpublished/neuron-app.html`
finds it. This note exists so nobody has to know to run that. It was
the cascade made reorderable, five toggles over the 32 subset counts, and it
showed one of the 120 orders at a time. `build_neuron.order_costs()` now
computes every constraint's cost at every position over all 120 orders from
the same subsets, and figure 6 draws the table: a range per constraint with
its first-position and last-position costs marked. That is the case
`NEW_PROJECTS` §2 names for building the still figure. Computing it also
corrected the sentence this paragraph used to carry: the shrinkage correction
does not cost "almost nothing when applied first"; it removes 90-99% wherever
it sits and is the *least* order-dependent constraint. The order-dependence
is in the three-parts requirement (92.5% first, 14% last) and in three
dimensions (22% first, 0% last). `test_neuron.RETIRED` carries the old
sentence so it cannot come back. `neuron/` had a `--build` flag and a
`build_app.py`; both are gone, and `tests/test_generators.py` no longer
lists a neuron app.

**The 104, opened (2026-09-06).** As first shipped the page never opened one
of the 104: none of their six archives was in `fetch_data.py`'s sample, so
the punchline rested on the archive's flags, which is what the page's own
Limits section warns against. `fetch_data.py --complete-only` now opens all
of them into `data/complete_metrics.csv`: 82 pass the page's width rule, 22
fail (Conte 20, Feldmeyer 1, Turner 1), 2 hold a single width and carry the
"Diameter" flag anyway. Fifteen are in vivo mouse L2 barrel-cortex projection
cells (Petersen archive, Yamashita et al. 2018) with 2-6 mm reach and 20-71
widths, flagged *Corrected* and *Axon Complete*; their paper contains no
statement about shrinkage and calls its tracing possibly incomplete. The page
says so, and cites it. Figure 5 draws one of the 104 at three nested scales,
at the file's own widths as polygons in data units over a hairline: cell
BC150319A_28 (Feldmeyer), chosen by rule in `fetch_data.pick_drawn()` - the
largest single-paper group, less the one file failing the width rule, then
the cell nearest the group's median reach and axon. Figure 2 now puts its
two cells in one frame at one scale, the slice cell 28 px wide in a box that
the right-hand panel opens. The panel boxes and "under one pixel" shares
live in `build_neuron.py` (`LADDER_CSS`, `PAIR_CSS`, `ladder_windows()`) and
`fig_neuron.py` places its axes from the same boxes; check 8 in
`test_neuron.py` asserts the file's hash, the re-pick, the windows and the
shares. The Feldmeyer CNG file is 3.7 MB (90,781 points); the depositor's
Source-Version is not distributed for that archive, so the drawing is in the
archive's PCA orientation and the caption says so.

Published 2026-09-06: source commit `6bff69b` on `master`, mirror head `fee3e64` on `main`; the alt-text correction `0445bcc` followed as mirror `b5b38af` (the commit before it is the rollback).

### Fat, sugar, salt (2026-09-05)

`food/` and `site/food.html`, the first of the six projects in
`prompts/NEW_PROJECTS.md` (its section 3) to be built; the research memo is
`food/RESEARCH.md`, the only copy (`03 RESEARCH/food/` is a pointer plus the
Stage 1 scratch scripts the project's generators superseded). One public-domain
download (USDA SR Legacy, pinned by hash in `fetch_data.py`), the published
hyper-palatable-food thresholds applied to every solid food, a raw / prepared
split that is the page's own rule and is labelled assumed, and three nulls
that separate the fat-sugar exclusion from the share-of-energy arithmetic.
Static figures only; the page says the rule was drawn by eye from 75 foods
and that two rating studies find it does not predict liking. `test_food.py`
guards the raw group against USDA's "raw" sausage, brine-injected pork and
salted egg, the human-milk exception, the null's seed, the pairs' salt
exclusion and page-payload agreement. Everything on the page is written by
`update_page.py` from `outputs/food_payload.json`, and the drift check runs it.

Known gaps in the model, deliberately left and unchanged since August: the
NAO reaches only Great Britain and Ireland (the only quantified NAO-to-demand
relationship published); no district-level political or values weighting
(WVS/EVS is national and interpolating it would be presented as
measurement); 571 of 3,332 districts are synthetic fillers with no
population and no behaviour link.
