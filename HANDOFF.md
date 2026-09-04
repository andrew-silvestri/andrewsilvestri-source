# Handoff: andrewsilvestri.com and the `13 - Energy Modeling` folder

Read this first if you are an AI picking up work on this site with no prior
context. It describes where everything is, how the site is built, the rules the
work follows, and the specific traps that have already caused bugs.

Written August 2026. If a number here disagrees with the payload, the payload
wins — see "Never trust a number in prose" below.

---

## 1. The one-paragraph version

`00 PUBLISH/` is the only folder that matters for the website. Inside it,
`site/` **is** the website: plain HTML, one stylesheet, thirteen JavaScript files,
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
    heat.html storage.html climate-cost.html    project pages (Energy)
    longevity.html skyline.html desktop.html    project pages (Others)
    atlas-app.html longevity-app.html skyline-app.html
    bookshelf-app.html climate-cost-app.html    full-screen interactive apps,
                                                opened in a new tab
    style.css               the ONLY stylesheet for all non-app pages
    assets/                 figures (.png/.webp) and their -thumb.png, 7 JS files
                            (atlas-app, atlas-data, hero, hero-data, hero-gl,
                            lightbox, motion), fonts/ (IBM Plex, OFL). No video
                            since 2026-09-04.
    downloads/              per-project source .zip archives (gitignored; four
                            of the twelve are rebuilt by rezip_downloads.py)
    CNAME .nojekyll         GitHub Pages config — do not delete either
  tests/                    the test suites (see §7) and their Playwright
  climate-cost/             sub-project: LCA engine, data, tests, template
  longevity-quotient/       sub-project: model, data, tests, template
  heat/ storage/            the two calculator models (see the table below)
  skyline/ bookshelf/       the skyline generator; the bookshelf download's README
  fonts/                    Plex OTFs for the figure builders (sitefig.py)
  unpublished/              retired pages kept but not linked: dac, holdup, beans,
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
| `00 PUBLISH/bookshelf/` | The README and the wallpaper setter for the bookshelf download; the app itself is `site/bookshelf-app.html` (fully client-side; demo screenshots in `site/assets/`). `25 Desktop Gallery/`, which also held a config-driven museum-wallpaper generator and its `PUBLISHING-NOTE.md` on image permissions, is not in the workspace; nothing from that generator is on the site. |
| `dumpNew/PyProjects/` | Personal desktop apps (Philbrook museum wall, Desktop Gazette), not published. Install contract: one folder, optional Startup shortcut, tray-icon quit, nothing in the registry. |
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
       ("The atlas", [("Open the atlas", "atlas-app.html"), …]),
       ("Energy", […]), ("Others", […]),
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
is `--acc: #8b7ff2` (violet). The hero flow trails gradient from `--acc` at
the head to `--cool: #5aa8d8` at the tail (changed from a flat sky blue
`#65B2CC` in the design-revamp pass, August 2026 - see `hero.js`/`hero-gl.js`).
The atlas impact web is still sky blue `#65B2CC`, untouched. All colours are
CSS custom properties in
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
| `bust_cache.py` | **Run before every publish.** Stamps `style.css`, the JS and every image with a content hash. Does not stamp what CSS `url()` references (the fonts). |
| `sync_img_dims.py` | Keeps every `<img width height>` equal to the file's pixels. |
| `rezip_downloads.py` | Rebuilds the heat, storage, bookshelf and skyline `-code.zip` from their source folders. One run at a time (lock file in `site/downloads/`); each archive is written beside itself and moved into place; `--verify` compares a fresh build against what is shipped without writing. Never ships `__pycache__/`, `outputs/`, node state or a built page — storage-code.zip did, on 2026-09-04. |
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
python3 tests/test_units.py            # every climate-cost input against its declared unit
python3 tests/test_generators.py       # every text generator run into a copy and diffed against site/
node tests/test_atlas_interaction.js   # boots the real app against a three.js stub
node tests/test_layout.js              # Playwright: marginalia, measure, hierarchy at 1440/1024/390
node tests/probe_scene.js              # prints what is actually in the scene graph
python3 build_atlas_figures.py         # must say "0 layout problem(s)"
```

The first five are the suites; all of them must pass before a commit. The
generator check needs nothing installed; the two node suites use the
Playwright in `tests/package.json`.

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
