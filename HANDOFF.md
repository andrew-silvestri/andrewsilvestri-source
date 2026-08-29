# Handoff: andrewsilvestri.com and the `13 - Energy Modeling` folder

Read this first if you are an AI picking up work on this site with no prior
context. It describes where everything is, how the site is built, the rules the
work follows, and the specific traps that have already caused bugs.

Written August 2026. If a number here disagrees with the payload, the payload
wins — see "Never trust a number in prose" below.

---

## 1. The one-paragraph version

`00 PUBLISH/` is the only folder that matters for the website. Inside it,
`site/` **is** the website: plain HTML, one stylesheet, three JavaScript files,
no build step, no framework, no dependencies. Everything else in `00 PUBLISH/`
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
    heat.html storage.html  project pages (Energy)
    dac.html holdup.html    project pages (Chemical)
    climate-cost.html beans.html running-shoes.html              Climate research
    longevity.html skyline.html desktop.html                      project pages (Others)
    *-app.html              full-screen interactive apps, opened in a new tab
                            (running-shoes-app.html is a three.js model whose
                             opening state can be set from the query string:
                             ?shoe=1&part=2&explode=1&az=&el=)
    style.css               the ONLY stylesheet for all non-app pages
    assets/                 figures (.png) + the three JS files + the payloads
    downloads/              per-project source .zip archives
    CNAME .nojekyll         GitHub Pages config — do not delete either
  tests/                    node test harnesses (see §7)
  climate-cost/             sub-project: LCA engine, data, tests, template
  longevity-quotient/       sub-project: model, data, tests, template
  unpublished/              retired pages kept but not linked
  *.py                      the build and verification scripts (see §5)
```

### Archives outside `00 PUBLISH`

| Folder | What it is |
|---|---|
| `19 Atlas v6/raw/` | **The raw data the atlas is built from.** WRI power plants, GeoNames cities15000 + admin1 + countryInfo, USGS quakes, World Port Index, Allen brain atlas. |
| `01`–`03`, `12` | The chemical/energy calculator projects behind heat, dac, storage, holdup pages. |
| `10`, `11`, `13`, `14` | World Energy Web v3/v4/v5 — **retired** model generations. Source of some legacy code the atlas still inherits. |
| `18 Final Deliverables/` | A snapshot of the **retired 7,192-node model**. Do not copy figures out of here; see the trap in §8. |
| `24 Skyline Sonifier/` | The skyline project. Builds `site/skyline-app.html`. Austin, Nashville and Fort Worth are carried in `supplement.py` from each city's published tallest-buildings list; above each list's stated floor the list overrules Wikidata. The instrument has one rendering, the musical one; the old realistic mode and its control are gone, so `S.mode` no longer exists. |
| `25 Desktop Gallery/` | The bookshelf app behind `site/desktop.html` (`site/bookshelf-app.html`, fully client-side; demo screenshots in `site/assets/`), plus a config-driven museum-wallpaper generator that is **deliberately unpublished** — see its `PUBLISHING-NOTE.md` for the image permissions required before any of it goes on the site. |
| `PyProjects/` | Personal desktop apps (Philbrook museum wall, Desktop Gazette), not published. Install contract: one folder, optional Startup shortcut, tray-icon quit, nothing in the registry. |
| `16 Presentation Architecture/` | 13 GB. Do not walk it casually. |

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

```python
NAV = [("Home", "index.html"),
       ("The atlas", [("Open the atlas", "atlas-app.html"), …]),
       ("Energy", […]), ("Chemical", […]), ("Others", […]),
       ("Code", "code.html")]
```

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

**Colour and layout.** Dark theme, blues/violets/dark greens. No amber. Accent
is `--acc: #8b7ff2` (violet). Sky blue `#65B2CC` is used for the hero flow
trails and the atlas impact web. All colours are CSS custom properties in
`style.css` `:root`; the figure scripts hold matching hex constants in
`build_throughlines.py` (`BG`, `INK`, `DIM`, `RULE`, `KCOL`).

**Figures.** Generated by Python, never hand-drawn, always regenerated from the
live payload. Every figure builder runs an `audit()` that reports overlapping
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
| `build_hero.py` | Rebuilds `hero-data.js` by sampling the live payload. |
| `update_atlas_pages.py` | **Regenerates `atlas.html` wholesale** and replaces stale figures in `model.html`. |

### Site-wide utilities

| Script | What it does |
|---|---|
| `rebuild_nav.py` | Rewrites the nav on every page from the `NAV` list. |
| `build_climate_figures.py` | The two climate-research diagrams (`nitrogen_fixation.png`, `running_shoe.png`). Boxes are drawn as text bboxes and arrows run underneath them, deliberately: a box sized by a guessed line height is a bug the layout audit cannot see. The shoe outline functions here are duplicated in `site/running-shoes-app.html`; if one changes, change both, because the flat figure and the 3D model are meant to be the same shoe. |
| `add_citations.py` | Attaches superscript citations anchored to phrases, not positions. |
| `sync_assets.py` | Copies figures from project folders into `site/assets/`. |
| `bust_cache.py` | **Run before every publish.** Stamps `style.css`, the JS and every image with a content hash. |
| `build_site.py` | The original generator. Mostly historical now. |
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

Four properties that took a long time to get right — **do not undo them**:

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

If you change any of this, change it in **both** engines and re-verify parity.

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
node tests/test_atlas_interaction.js   # boots the real app against a three.js stub
node tests/probe_scene.js              # prints what is actually in the scene graph
python3 build_atlas_figures.py         # must say "0 layout problem(s)"
```

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
6. Add the page to `NAV` in `rebuild_nav.py` under Energy, Chemical or Others,
   and re-run it.
7. Add a `downloads/<project>-code.zip` and a row in `code.html`.
8. Run `add_citations.py`, then `bust_cache.py`, then `publish.sh --dry-run`.

---

## 10. Publishing

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

---

## 11. Current state, August 2026

- Payload: **86,622 nodes, 197,068 weighted links**, 0.10% isolated, 12 node
  kinds, 9 tabs.
- **60 prepared scenarios** in 9 categories, each with a stated basis.
- Engine parity between the browser and the figure builder: agreement to ~1e-9.
- All figure builders report 0 layout problems; all interaction tests pass.
- No broken links; 12 download archives intact.

Known gaps, deliberately left:

- The NAO reaches only Great Britain and Ireland, because those are the only
  countries with a published, quantified NAO-to-demand relationship.
- No district-level political or values weighting. WVS/EVS is national-level
  for ~120 countries and does not exist at the resolution that would require.
  Building it would mean presenting interpolation as measurement.
- 571 of 3,332 districts are synthetic fillers with no population and no
  behaviour link, because the source data could not resolve real divisions for
  those countries.
