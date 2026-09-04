# Site revamp — 2026-08-30

Not published. Lives at the repo root, outside `site/`, like
`SITE_AUDIT_FINDINGS.md`.

This pass implements every item in `SITE_AUDIT_FINDINGS.md` plus the four
findings from the diagnostic report that preceded it. Each entry below records
**what** changed, **why**, and the **implication** — the same structure the
findings doc uses. Items marked **NEW** were not on either list; they surfaced
while doing the work.

Nothing here has been published. The site has not been deployed.

---

## Content correctness

### `longevity.html` claimed twenty orders of magnitude of body mass

- **What**: Line 22 said the 7,873 species span "twenty orders of magnitude of
  body size". The page's own methods section says **14.5 orders of magnitude,
  from 0 g to 150,000,000 g**. Changed line 22 to agree.
- **Why**: The page contradicted itself, and the intro's number was the wrong
  one. 150 tonnes over a microgram is about 14.2 orders; twenty was not a
  rounding of anything.
- **Implication**: A reader who checked the two numbers against each other no
  longer finds the page arguing with itself.

### **NEW** — three `library.html` cards described figures that do not exist

- **What**: Cards 02, 05 and 12 each described a **two-panel** figure ("The
  left panel… The right panel…"). All three figures are single-panel and about
  different subjects entirely:
  - `02_demand_distribution.png` — card said country demand distribution plus a
    cumulative concentration curve. The figure is a histogram of **generating
    unit capacity** on log-log axes, titled "Capacity spans five orders of
    magnitude · 34,936 plants, 5.71 TW".
  - `05_link_structure.png` — card said a link-weight histogram plus a bar of
    node-type pairs. The figure is a **log-log scatter of node degree**.
  - `12_recorded_events.png` — card said decadal disaster damage by type plus
    the twelve costliest events. The figure is a **histogram of earthquake
    moment magnitude** on a log count axis.
  Titles, alt text and captions were rewritten against what each generator
  actually draws.
- **Why**: `build_atlas_figures.py` was rewritten at some point to draw from the
  live payload — its docstring says as much, and describes the numbers-drifting
  failure it was designed to prevent. The figures were replaced; the prose
  around them was not.
- **Implication**: This was the largest correctness problem found on the site.
  Three of the fourteen cards told the reader to look for things that were not
  in the picture. The builder protects its numbers from drift but nothing
  protected the surrounding prose, and nothing does now either — see the note
  under "What is still open".

### **NEW** — `library.html` named a toolkit the project never used

- **What**: Seven of fourteen method tags, and the closing Method paragraph,
  credited seaborn (4 cards), plotnine (1), pandas (1) and plotly. Every figure
  on the page comes from `build_atlas_figures.py`, which imports only
  matplotlib, numpy and scipy; none of those four libraries were imported
  anywhere in the repo or installed in the environment. Tags now name what each
  figure actually does, and the Method paragraph says matplotlib throughout,
  plotnine for the one grammar-of-graphics panel, and that the atlas is drawn
  live in WebGL rather than plotted.
- **Why**: The page's whole framing is a tour of methods, and each card ends
  with "Each figure names its method above the title." The tags were the one
  thing on the page a reader could not check, and they were wrong.
- **Implication**: The tags are now verifiable against the generator. The tag
  text is duplicated in the page's own `MARGIN_SCENE.items` list, so a comment
  was added there saying both copies have to move together.

### `09_size_vs_lowcarbon.png` was a bar chart under a scatter-plot caption

- **What**: The card described a scatter of country system size against
  low-carbon share with a smoothed trend, tagged "plotnine, grammar of
  graphics". The generator produced a horizontal bar chart of installed capacity
  by fuel, in plain matplotlib. **The scatter the card describes has now been
  written**, replacing the bar chart at `build_atlas_figures.py:249`.
- **Why**: Chosen over rewriting the caption, so the library keeps a genuine
  grammar-of-graphics example and the filename stops lying.
- **How**: Both axes come out of `atlas-data.js`, the same payload every other
  figure reads — no new data source. The 214 `grid` nodes carry each country's
  average load in their names (`"AFG grid (0.8 GW avg)"`), and the 725 `supply`
  nodes carry its fuel split (`"ABW renew supply (17.0% of power)"`), of which
  `nuclear`, `hydro` and `renew` are summed for the low-carbon share. `WLD` is
  dropped, being a world aggregate rather than a country, and so are the
  countries whose average load rounds to 0.0 GW, which a log axis cannot place.
  **184 countries** remain, and the caption now says so.
- **Implication**: New dependencies — `plotnine`, `statsmodels` and
  `scikit-misc` (plotnine's loess needs the last one, not statsmodels as first
  assumed). The repo previously needed only matplotlib/numpy/scipy. plotnine
  does not inherit `plt.rcParams`, so the house palette is applied through an
  explicit `theme()`; and `plot.draw()` returns a figure on the base canvas, so
  an Agg canvas is bound to it before `save()` runs, letting the new figure go
  through the same `audit()` overlap check as every other one. It passes.

---

## Layout and markup

### **NEW** — the provenance card had no `<div class="card">` opener

- **What**: `13_provenance`'s card on `library.html` was missing its opening
  `<div class="card">`, so its tag, heading, figure and caption rendered
  *inside* the space-layer card. The file had 13 card openers for 14 cards.
  Pre-existing, confirmed against `git show HEAD`.
- **Why not caught before**: The page still looked plausible — one card was
  simply twice as tall, and `test_markup.py` checks for unrendered markdown, not
  for balanced containers.
- **Implication**: The page now renders 13 discrete cards for 13 tags.

### `climate-cost.html`'s arc animation finished inside the first screen

- **What**: All 20 shipping-route arcs revealed within roughly the first 660px
  of a 6,806px page. `drawArcs()` stacked rows from `-scrollY + 60` at a fixed
  30px pitch — viewport space — instead of spreading them through the document.
  `layoutArcs()` now assigns each row a document-space `y0` across `docH`, and
  `drawArcs()` derives its viewport position from that.
- **Why**: `margin-scene.js` already had the right pattern in two places —
  `strataBands` (`heights[i] / total * docH`) and `cardItems` (`rnd() * docH`).
  The arcs were the one scene kind that had not been converted.
- **Implication**: Verified in-browser: three different sets of route labels at
  0%, 50% and 85% scroll, where before the whole set appeared at once and the
  remaining 90% of the page scrolled past nothing.

### **NEW** — every document-space scene was laid out against a stale `docH`

- **What**: Found while verifying the arc fix. `docH` is read in `resize()`,
  which only fires on **window** resize. `climate-cost.html`'s own height
  settles after load, so the arcs were spread over a document taller than the
  one that ended up existing and **the last two never came into view at all** —
  a forced `resize` event made them appear. Added a `ResizeObserver` on
  `document.body` that re-runs the layout when the document height changes.
- **Why**: `strataBands`, `cardItems` and `arcRows` all divide `docH`. Any page
  whose height settles after load had a layout computed against a number that
  was already wrong.
- **Implication**: Fixes the arcs at the foot of `climate-cost.html`, and the
  same latent error on every page using the strata and card scenes. Re-verified
  in-browser: the last two arcs now appear at maximum scroll without
  intervention.

### Navigation grouping

- **What**: "Climate cost calculator" sat at the top level while Heat and
  Storage — also energy tools — were nested under `Energy ▾`. Moved into that
  dropdown after Storage, across all 11 pages carrying the nav.
- **Why**: Nothing distinguished it from the two tools it sat beside.
- **Implication**: `climate-cost.html` also needed the nested-active pattern
  the other nested pages use (`class="ddbtn on"` on the Energy button as well as
  `class="on"` on its own link). Verified: all 11 pages show the link inside the
  Energy menu, with correct highlighting, and no page keeps a top-level copy.
  The 5 `*-app.html` tool pages carry no nav and were not touched.

---

## Assets and weight

### Two 2,200px PNGs were the heaviest things on the site

- **What**: `bookshelf-demo-covers.png` (2.15 MB) and `bookshelf-demo-shelf.png`
  (840 KB), both loading on `desktop.html`. Converted to WebP at quality 88,
  same 2200×1280 dimensions: **2,967 KB → 368 KB, an 87% saving**. The PNGs were
  deleted and `desktop.html` updated.
- **Why WebP over PNG quantization**: 256-colour PNG landed at a similar size
  (490 KB) but these are photographic book covers, where quantization bands.
  WebP q88 is both smaller and higher fidelity; sidebar text and cover titles
  were checked at full size and stay crisp.
- **Implication**: `bust_cache.py` only stamped `.png`, `.svg` and `.mp4`, so
  the new files would have shipped unversioned — `*.webp` was added to that
  list. No PNG fallback was written: WebP is supported by every browser that can
  run this site's WebGL atlas.

### Five scripts were never cache-busted

- **What**: `bust_cache.py`'s `SCRIPTS` tuple was a hand-kept whitelist.
  `margin-scene.js` (8 pages), `bgloop.js` (6), `force-graph-data.js` (2),
  `force-bg.js` (2) and `biome-scene.js` (1) were missing from it — 19 unstamped
  `<script src>` tags. Replaced the tuple with a glob over `site/assets/*.js`.
- **Why the glob rather than five more entries**: forgetting to add a new file
  to the list fails silently, which is how these five shipped unstamped for as
  long as they existed. Images were already handled by walking a directory; the
  scripts now match.
- **Implication**: A returning visitor holding a cached copy of any of these
  five was being served stale JavaScript after a deploy — which looks exactly
  like a change that did not take. Verified: **0 unstamped assets** remain
  across the site.

### **NEW** — `sync_assets.py --apply` deleted 16 live files

- **What**: Running it during this pass pruned 16 assets it judged orphaned,
  including six `poster=` frames referenced by the motion-gated `<video>` tags
  on `climate-cost`, `desktop`, `heat`, `longevity`, `skyline` and `storage`,
  and the four OpenMoji SVGs added in the previous commit. All were restored
  from `git HEAD`, and `referenced()` was fixed.
- **Why it happened**: `referenced()` scanned only `href` and `src` on the HTML
  pages. It never saw `poster=`, never saw `data-src=` (the motion-gated video
  pattern that `bust_cache.py` already knew about), and never read the scripts —
  the OpenMoji paths are string literals in `assets/biome-scene.js`. It now
  scans all four attributes and the scripts as well.
- **Implication**: This was a live footgun in a script whose whole job is to
  decide what may be deleted; anyone running `--apply` would have hit it.
  Reference count went from 49 to 57, and the orphan list from 16 to 6. The
  remaining 6 (`dac_fig1`–`dac_fig5`, `nitrogen_fixation.png`,
  `running_shoe.png`, 1.0 MB) are genuinely unreferenced and were **left in
  place** — see "What is still open".

### The two light-themed figures were dropped

- **What**: `01_world_fuel_mix.png` and `03_price_histories.png` rendered on a
  white background against the site's dark theme, and no generating script for
  either exists anywhere in the repo. Both cards were removed from
  `library.html` (and their `MARGIN_SCENE` entries), and the files deleted.
- **NEW**: both were *also* thumbnails in the `index.html` mosaic, which the
  first deletion attempt broke. They were replaced there with
  `07_arrival_order.png` and the new `09_size_vs_lowcarbon.png`, both on-theme.
- **Implication**: `library.html` now carries 13 cards. The homepage mosaic is
  uniformly dark for the first time.

### `fig2_lq_ranked.png` was generated but never displayed

- **What**: `build_lq.py` produced it, `sync_assets.py:44` mapped it to
  `lq_ranked.png`, but sync only copies figures an `<img>` asks for and no page
  asked. Added to `longevity.html` after the allometry figure, ahead of the
  order-level `lq_orders` — it is species-level, so it belongs on that side of
  the "Comparing whole groups" heading.
- **Implication**: The sync map is now true rather than aspirational. The figure
  ("Who beats their body mass, and who does not") is a good one and was being
  built into a directory nothing read.

---

## Palette

### Both code downloads abandoned their own palette module

- **What**: `heat-code.zip` and `storage-code.zip` each ship a correct
  `figstyle.py`, which each `model.py` uses for its first figure and then stops
  using. Ten colour sites were routed back through it — wider than the two
  originally recorded:

  | zip | line | figure | was | now |
  |---|---|---|---|---|
  | heat | 170–172 | `fig_lcoh_stacked` | `#4C72B0` `#DD8452` `#55A868` | `COOL` `WARM` `GREEN` |
  | heat | 198 | `fig3_costgap_contour` | `colors="k"` | `figstyle.INK` |
  | heat | 200 | `fig3_costgap_contour` | `"k*"` marker | `"*"`, `figstyle.INK` |
  | heat | 231 | `fig4_tornado` | `#4C72B0` / `#DD8452` | `COOL` / `ACC` |
  | heat | 233 | `fig4_tornado` | `color="k"` | `figstyle.INK` |
  | heat | 249–253 | `fig5_emissions_parity` | `#DD8452`, `"k"`, `"k*"` | `WARM`, `DIM`, `INK` |
  | storage | 168–169 | `fig2_dispatch_week` | `tab:red` / `tab:blue` | `WARM` / `COOL` |
  | storage | 181 | `fig3_duration_value` | `#4C72B0` | `COOL` |
  | storage | 217 | `fig_monthly` | `#DD8452` | `WARM` |

  `fig4_tornado`'s bars take `COOL`/`ACC` rather than the obvious `COOL`/`WARM`
  because the same figure's parity rule already uses `WARM`.
- **NEW — the black-on-black problem**: three of these were not seaborn colours
  but plain black (`"k"`) on a near-black ground: the zero contour on
  `fig3_costgap_contour`, the baseline rule on `fig4_tornado`, and the ERCOT
  marker star on `fig5_emissions_parity`. They were, in practice, invisible.
  That is a legibility defect rather than a palette one and is the more
  significant half of this entry.
- **Both pipelines are byte-deterministic**: every figure not touched by the
  patch (`heat fig1`, `storage fig1`, `storage fig4`) regenerated **identical to
  the published copy**, which is the check that only colour changed.
- **Implication**: The four affected published figures were replaced, and both
  zips rebuilt with their original archive layout preserved. The Octave ports
  also use `"k"` but plot on Octave's white default, where black is correct;
  they were left alone.

### **NEW** — the heat download was stale, and both labels were wrong

- **What**: The published `heat_fig5_emissions_parity.png` differed from what
  the zip's code produces — the site read "ERCOT avg (eGRID, update)", the code
  said "ERCOT avg (eGRID 2022)". Same number, same geometry. **Neither label was
  right.**
- **What the number actually is**: `model.py`'s own source comment reads
  `grid_ci: float = 0.365  # tCO2/MWh average grid intensity, eGRID ERCOT-ish;
  scenario variable`. It is a round assumption, not a figure any eGRID release
  publishes — eGRID2023 puts the ERCOT subregion at 733.862 lb/MWh, which is
  **0.333**, not 0.365. "eGRID 2022" claimed a citation the number does not
  have; "eGRID, update" was a placeholder.
- **Resolution**: **the model now tracks the published figure.** `grid_ci` was
  changed from the 0.365 assumption to **0.333**, the ERCOT average from
  eGRID2023 (revised 12 June 2025), which reports **733.862 lb CO₂/MWh** for the
  ERCT subregion. The CO₂ rate is used rather than the 736.629 CO₂e rate,
  because `ef_gas` is a carbon-dioxide-only factor and the two have to be the
  same gas. The figure's label now reads "ERCOT average, eGRID2023 (0.333)".
- **Changed in all four implementations**, which are meant to agree and did not
  after the first pass: `model.py`, `julia/model.jl`, `octave/model.m` and
  `lcoh_model.xlsx` (`Inputs!B16`). The README's conclusions line was updated
  too.
- **What moved**: electric-boiler emissions fall from 109.15 to **99.58
  kg/MMBtu**. The gas boiler is unchanged at 62.42, and the parity threshold is
  unchanged at **0.209** — it derives from the two efficiencies and the gas
  factor, not from grid intensity. **The conclusion is unchanged**: 0.333 is
  still well above 0.209, so on average grid power the e-boiler still emits
  more than gas.
- **`heat.html` carried the same false claim** and was corrected: the page had
  said "The eGRID average for the Texas grid is about 0.365", and reference 3
  cited "eGRID 2022". Both now give the real release, the real number and the
  CO₂-not-CO₂e reasoning.
- **Note on the source**: an initial web search returned 738.038 lb/MWh for
  ERCOT. EPA's own summary-data page gives **733.862**. The EPA figure was used.

---

## What is still open

- **The 6 remaining orphaned assets** (`dac_fig1_isotherms`,
  `dac_fig2_working_capacity`, `dac_fig3_energy_per_tonne`,
  `dac_fig5_cost_tornado`, `nitrogen_fixation.png`, `running_shoe.png`, 1.0 MB
  total) are genuinely unreferenced. Left in place — the DAC set looks like it
  is waiting for a page that has not been written, and deleting it was not
  asked for.
- ~~`fig2_lcoh_stacked.png` and `fig5_monthly.png`~~ — **resolved: both are now
  on the site.** Wiring them in exposed two defects that had gone unseen
  precisely because nothing displayed them, both fixed before publishing:
  - **`fig5_monthly` was drawing eight bars for twelve months.** The month
    letters `J F M A M J J A S O N D` were passed to `bar()` as categories, and
    because J, M and A repeat, matplotlib collapsed them — silently dropping
    May, June, July and August, *the ERCOT scarcity months the figure exists to
    show*. The old chart put the annual peak in January. Corrected to numeric
    positions with explicit tick labels; the peak is July, as it should be.
  - **`fig2_lcoh_stacked`'s title was broken and clipped.** It read
    `Baseline LCOH @ $P_e$=6.5¢/kWh, $P_g$=$3.5/MMBtu` — an odd number of
    dollar signs, so matplotlib abandoned the mathtext and drew the `$P_e$`
    markup raw, and the line ran off a 7in canvas. Now uses
    `figstyle.finish(title=…, subtitle=…)`, the header mechanism every other
    figure in the file already used, which reserves its own strip.

  `heat_fig2_lcoh_stacked.png` sits first on `heat.html`, ahead of the
  break-even locus it explains; `storage_fig5_monthly.png` follows the dispatch
  week on `storage.html`. Both captions were checked against the model's own
  numbers rather than written from the picture — a first draft claiming capital
  and O&M were "under a dollar per MMBtu for either boiler" was wrong for gas
  ($1.02), and one claiming June–September carry "the bulk" of revenue was
  corrected to the true 43 per cent.
- ~~The bar chart replaced at `09`~~ — **resolved: given its own card.** It is
  now generated as `10_capacity_by_fuel.png` and carries card 8 on
  `library.html`, sitting directly after the scatter that displaced it. It
  answers a different question about the same station layer — capacity by fuel
  rather than by country — and the caption draws out the contrast the figure
  makes plain: nuclear holds 408 GW across 195 units, solar 188 GW across
  10,665.
- **`02_demand_distribution.png` is a misnomer** — the figure is about plant
  capacity, not demand. The filename was left alone because renaming it touches
  the sync map, the cache stamps and the homepage mosaic for no reader-visible
  gain.
- **Nothing protects `library.html`'s prose from drifting again.** The builder
  guarantees its own numbers and titles against the live payload; the card text
  beside each figure is hand-written and was, before this pass, describing a
  figure set that had been replaced. A test that compares each card's `<h3>`
  against its figure's rendered title would have caught all three cases.

---

## Verification run

| check | result |
|---|---|
| `python tests/test_markup.py` | pass — 0 unrendered-markdown hits across 16 pages |
| `node tests/test_atlas_interaction.js` | pass — 19/19 |
| `node tests/probe_scene.js` | pass |
| `python build_atlas_figures.py` | **0 layout problems** across the set, including the new plotnine scatter |
| `python sync_assets.py` | 57 referenced, 0 stale, 6 genuine orphans |
| `python bust_cache.py` | 0 unstamped assets remain |
| local reference check | **324 local references, 0 missing** |
| browser — nav | all 11 pages correct, verified statically and in-browser |
| browser — `climate-cost.html` | arcs reveal across the full scroll, including at maximum scroll |
| browser — `library.html` | 13 cards, 13 tags, 0 broken images |
| browser — `longevity.html` | corrected magnitude text, `lq_ranked` renders |
| browser — `desktop.html` | both WebP wallpapers load at 2200×1280 |
| browser — console | no errors on `index.html` |

**Not published.**

---

## Second pass — longevity figures and typography

### **NEW** — `lq_ranked` hid the entire "who does not" half of its own title

- **What**: Bars ran from zero on a linear axis with the ocean quahog out at
  47.5, so the twelve species *below* parity — quotients of 0.007 to 0.02 —
  drew as **twelve blank rows with labels and nothing beside them**. Redrawn as
  a lollipop from parity on a logarithmic axis: a ratio belongs on a log scale,
  and now short-to-the-left reads as plainly as long-to-the-right.
- **Why it survived**: the figure was generated but never displayed until this
  session wired it in. Nothing had ever looked at it on a page.
- **Implication**: this shipped in the previous publish. It is the clearest
  argument in this whole log for not carrying figures that no page renders.

### **NEW** — `lq_orders` was a 1350×5265 sliver

- **What**: 112 orders in one column at 0.3in a row made a figure four times
  taller than it was wide. The page scaled it to 953px across, at which point
  every label was around 2px tall. Split into two columns sorted best-first,
  row pitch 0.17in: **1950×1638**, and legible at the width the page actually
  gives it.

### **NEW** — three of six classes in the allometry legend were the same violet

- **What**: Mammalia `#8b7ff2`, Amphibia `#a98fd8` and Pisces `#6f7fd8` are
  distinguishable as swatches and identical as 20px scatter dots. Amphibia
  moved to gold `#c9a227` and Pisces to slate `#6e8096`, both already in the
  site's cycle. The visualiser doesn't use this map, so nothing else moved.
- **Also**: the labelled outliers were written straight into the densest part
  of an 7,873-point cloud. Each now sits on an opaque plate in the panel
  colour, so it reads as a gap rather than as text over noise.

### Typography now matches the site

- **What**: every generator was on matplotlib's DejaVu Sans while the site sets
  its UI text in the system sans stack, so each chart was lettered differently
  from the caption beneath it. `build_atlas_figures.py`,
  `longevity-quotient/build_lq.py` and both zips' `figstyle.py` now set
  `font.sans-serif` to `["Segoe UI", "Selawik", "DejaVu Sans", "Arial"]` —
  a list, so a reader running the downloads on a machine without Segoe UI gets
  a graceful fallback rather than tofu.
- **Checked**: all figures regenerated, **0 layout problems** — the new metrics
  did not push any label off-canvas or into another.

### **NEW** — longevity.html's order rankings were wrong throughout

- **What**: the page said Chiroptera led at "two and a half times prediction",
  Primates sat at 1.8, Eulipotyphla at 0.37, Galliformes at 0.43, and
  Vespertilionidae reached 3.1 against Sebastidae's 3.5. Against
  `group_summary.csv`: **Zeiformes** leads at 3.95, Chiroptera is third at
  2.68, Primates 2.12, Eulipotyphla 0.58, Galliformes 0.51, Vespertilionidae
  3.43, Sebastidae 2.76 — every figure in the paragraph was off, most of the
  orderings with them.
- **Rewritten**, and the rewrite adds a caveat the original lacked: the two
  orders at the very top rest on seven and four species respectively, so the
  substantial claims are Chiroptera (267 species) and Primates (350), not the
  leaders.
- **Implication**: the third instance this session of prose describing a
  figure set that had since been regenerated. Same root cause as the
  `library.html` cards.

---

# Third pass — the external design audit

`DESIGN_AUDIT_EXTERNAL_2026-08-30.md` (repo root, unpublished) is an
outside-critic pass over the live site: legibility, the figure set judged as a
set, what a reader would want that isn't there, interaction, and responsive and
accessible behaviour. This section records implementing it.

Three of its findings were **checked against the source and withdrawn** before
any work started. They are recorded here so nobody re-finds them.

## Withdrawn before implementation

### There is no scroll-reveal system to fix

- **What the audit said**: content blanks out on fast scroll, and reveals fire
  too late.
- **What is true**: `IntersectionObserver` appears exactly three times on this
  site — `hero-gl.js`, `hero.js`, `bgloop.js` — and all three are play/pause
  gates for a canvas or a video. Nothing reveals content on scroll. The blank
  viewports in the audit were artifacts of the automation scrolling faster than
  Chrome painted; scripted scrolls to fixed offsets never reproduced them.
- **Implication**: the section spacing the audit wanted halved is ordinary
  (`hr` 52px plus `h2` 58px, about 126px a boundary) and was left alone.

### The longevity lollipop does use both halves of its panel

- **What the audit said**: `lq_ranked` leaves its whole left half empty.
- **What is true**: the full 1350x1320 figure runs twelve below-parity species
  leftward from the dashed parity line, down to the Indian hare at about 0.007.
  The audit saw the top of a tall figure inside one viewport and generalised
  from it. Unchanged.

### The atlas scenario list is already grouped

- **What the audit said**: sixty scenarios in one flat `select`.
- **What is true**: `buildScenarioList()` in `atlas-app.js` already emits an
  `optgroup` per category with an "Other" sweep, and
  `tests/test_atlas_interaction.js` asserts all sixty are filed under nine
  categories. Unchanged.

## The rule that governed the figure work

For a figure rendered in the site's 1140px `wide` track,

    on_screen_px = pt * 1140 / (72 * figsize_width_inches)

`dpi` cancels: it changes the bitmap's pixel count and nothing a reader sees.
Every previous attempt to make these figures more legible reached for dpi. The
floor adopted here is **11px for anything a reader must read, 13px for a panel
title**, and it is now enforced in code (`fig_floor.py`) inside each
generator's existing `audit()`, so a regeneration that undercuts it fails the
same way a text collision does.

## Legibility

### Library figures were rendering at 554px, and it was a CSS bug

- **What**: twelve figures drawn 1425-1650px wide were rendering at 554px, so
  matplotlib tick labels landed near 6px. The cause was not the generators:
  `style.css` promotes `main > img.fig` to the `wide` track, but
  `library.html` nests its images inside `.card` inside `div.grid`, so the
  selector never matched and they inherited the 72ch prose column. Every other
  page puts figures as direct children of `main`, which is why heat and storage
  always read well.
- **Fixed** by promoting the grid itself (`div class="grid wide"`) and capping
  only the card's prose at 72ch. The figures now render **1082px**, with no
  regeneration at all.
- **Implication**: the audit read this as a figure-generation problem across
  the whole set. It was one selector. Worth remembering before regenerating
  anything on legibility grounds — measure the rendered width first.

### The two composite sheets really were too small

- `energy_model_throughlines.png` was 15.5in wide with no `rcParams` block and
  about 25 literal `fontsize=` values from 7.2 to 21 — a factor of 1.02, so a
  7.2pt heatmap tick landed at **7.35px**. Canvas cut to 11in and put on the
  house scale: smallest label now **11.23px**.
- `energy_model_chart.png`, the home overview, was 14.4in, factor 1.10, its
  eight-entry donut legend landing at 8.79px. Canvas cut to 10.2in: **12.42px**.
- In both, `dpi` was raised only to hold the bitmap's pixel count, which by the
  rule above changes nothing a reader sees.

### Prose no longer reads through the force graph

- **What**: `force-bg.js` appends a fixed full-viewport canvas at `z-index:0`
  painting at `globalAlpha` 0.5. `main` sits above it, but nothing in the text
  column is opaque, so on `atlas.html` and `model.html` the graph passed under
  every serif glyph for 6,700 and 9,300px of scroll — the two pages carrying
  the most demanding prose on the site.
- **Fixed** with a feathered `mask-image` on the graph host that cuts the text
  column out, reusing the grid-track parser `margin-scene.js` already has, and
  re-applied inside the existing resize debounce.
- **Needed a second change to be worth anything**: the graph's physics were
  scaled off `min(innerWidth, innerHeight)`, which on a wide desktop window
  clustered every node *inside* the column the mask now removes — so masking
  alone deleted the graph rather than moving it to the margins. Rescaled off
  `innerWidth`, with the charge and link constants raised to match.

## Margin scenes no longer collide with content

- **What**: `margin-scene.js` anchored its drawing bands to `text-start` and
  `text-end`, but tables, figures and card grids sit in the wider `wide` track
  — so `code.html` drew its archive-size bars underneath the file table. And
  there was no vertical clamp at all, so `desktop.html`'s drifting book cards
  passed straight through `nav.top`, which has no background.
- **Fixed**: bands re-anchored to `wide-start`/`wide-end` plus a 24px gutter,
  and a live clip at the nav's bottom edge.

## Figures that were doing their job badly

- **Panel D of the throughlines** drew eight near-identical lines behind a
  two-column 8.4pt legend. It now direct-labels by magnitude, computed from the
  data rather than named in advance: always the top two by final value, a third
  only if it clears both a floor and a gap test. For the oil-supply scenario
  that is Fuel supply at 0.186 and National grid at 0.026, with the remaining
  five — all inside 0.004 to 0.009 — muted into one bundle. **The first attempt
  hardcoded "Power station and National grid" from the plan, which left the
  dominant trace grey and unlabelled**: a worse failure than the legend it
  replaced.
- **Panel E** used a magma ramp, the only off-palette figure on the site, with
  pure-black cells ambiguous between zero and no-data. Rebuilt on the site's
  violet, with exact zeros marked and captioned "x = exact zero, not missing
  data".
- **Panel B** truncated node names with an ellipsis at 8.2pt; it now wraps.
- **The storage duration chart** drew three zero-based bars — 98.1, 107.1 and
  111.0 per kW-yr — that read as equal, while the page's claim is that value
  *flattens*. It now leads with the increment, computed at render time, so the
  flattening is the visible fact.

### `climate_allocation` showed only half its own argument

- **What**: the Manim scene animates a leather shoe's share of a beef animal
  from economic allocation (2.2 per cent, 3.66 kg) to mass allocation (7.0 per
  cent, 11.65 kg), but the final transform *replaced* the economic values. So
  the resting frame, and therefore the poster, showed one state. Anyone with
  motion off, or scrolling past, saw half the comparison; on a dark page it
  read as a broken figure.
- **Fixed** in the scene: both states survive at rest, and colour now carries
  one consistent rule — violet is economic, blue is mass. A first fix left the
  7.0 per cent in violet after violet had become the *economic* colour, so the
  two halves of the same fact were painted as opposites.
- `heat_breakeven` had tick marks with no values on either axis; it now labels
  both. Both scenes re-rendered, both posters re-extracted.

## What a reader wanted that was not there

- **`atlas.html` now opens with a diagram of its own architecture**
  (`build_layer_diagram.py`, `atlas_layers.png`), above the nine-layer table it
  has always had. One-way and two-way links are drawn, not just argued —
  derived from the propagation's own rank table rather than a hand-written
  list, and folded from twelve node kinds to the table's nine layers with every
  count summed live from the payload. **A first version titled itself "The nine
  layers" over twelve boxes**, which would have disagreed with the table
  directly beneath it.
- **The atlas app can replay a run.** `propagate()` already computed `fh`, the
  step at which each node first moved, and stored it for a single tooltip line.
  A slider and a play button now walk `replayStep` through it, gating node
  intensity in `paint()`, so the spread the page spends two paragraphs
  describing can be watched hop by hop. No new data: storing sixty full state
  arrays would have cost about 41MB.
- **A missed click on the globe now says so**, instead of being
  indistinguishable from a dead app, and the result block scrolls into view
  when a run finishes rather than sitting below the sidebar fold.
- **`climate-cost.html` has a worked example before its calculator** — the
  tomato's fertiliser chain, four levels deep, traced by `lca.py` itself.
  **Its first draft carried "alloc x1.00" on three of four edges and a
  three-line caption explaining why it did not demonstrate allocation.** Every
  process in that chain is single-output, so no allocation happens anywhere in
  it. Reframed around what it does show: real depth, tapering 59.8g to 5.27g to
  3.20g to 0.386g.
- **The home tool cards carry a figure each**, and **every `img.fig` opens at
  natural size** in a keyboard-reachable lightbox (`assets/lightbox.js`).
- **The longevity visualiser has URL state**, and `longevity.html`'s claims
  about named taxa link into it pre-filtered.

## Bugs found while doing the above

### The group view served stale aggregates — shipping, and silent

- **What**: `groups()` in `longevity-app.html` built its cache key from
  `_poolKey` *before* calling `speciesPool()`, which is the only thing that
  refreshes `_poolKey`. So changing data grade, taxon filter or search while in
  the group view produced a key identical to the previous one, hit the cache,
  and returned the previous groups.
- **Confirmed against the shipped file before fixing**: switching grade from
  A-B to include-C returned "89 order groups, 6,314 species" both times. After
  the fix, that becomes 119 groups and 7,771 species, and is reversible.
- **Why it stayed hidden**: it needs two renders in one session. A fresh load
  always misses the cache and is always right, so every deep link and every
  first impression of the page was correct.

### `-999` was rendering as a common name

- AnAge's missing-value sentinel appears as the literal string `-999` 127 times
  in the packed payload and was never mapped to empty, so rows read
  `Terrapene mexicana (-999)` in the default sort, and `-999` alone in the
  Common name mode. Normalised at decode time, before the label, the search
  index and the detail panel.

### Every sized image was being squashed

- **What**: adding `width`/`height` to 44 images to stop layout shift
  introduced a worse bug than it fixed. Those attributes are a presentational
  hint as well as an aspect ratio, and neither `img.fig` nor the new card-image
  rule set `height: auto` — so each image rendered at its *full pixel height*
  inside a column a third as wide. `heat_fig1` drew 502x810 against a natural
  aspect of 1.67.
- **Fixed** with `height: auto` on both rules, and `sync_img_dims.py` added,
  because four pages had already drifted out of step with their own figures
  inside this one session: a regenerated figure changes size, the markup keeps
  the old number, and the reserved box is now the wrong shape. `bust_cache.py`
  rewrites the `?v=` stamp on the same tags and never looks at the dimensions.

### A layout audit that could not see its own boxes

- `build_layer_diagram.py`'s `audit()` checks `Text` objects, so two node
  *patches* drawn on top of each other passed every check — which is how the
  Space and Markets boxes came out 0.5 units apart, reading as one merged box
  and hiding the edge that ran underneath. It now checks box separation and
  canvas bounds too.

### `audit()` was measuring tick labels that were not there

- `ax.axis("off")` does not clear `xaxis.get_visible()`, so
  `build_throughlines.py`'s audit measured phantom default tick labels on every
  diagram panel and reported false collisions once real content came near them.

## The generators are no longer only inside a zip

`figstyle.py` and the heat and storage `model.py` existed **only** inside
`site/downloads/heat-code.zip` and `storage-code.zip` — the sibling folders
`sync_assets.py` expected were never created, so the source of two of the
site's three tools was recoverable only by unzipping a download. Both are now
tracked folders, `heat/` and `storage/`; `sync_assets.py` points at them; and
`rezip_downloads.py` rebuilds the archives from the folders, verified to
produce a byte-identical zip.

## Deliberately not done

- **No about page.** Decided against; the footer address stays the only contact
  route.
- **The ATB capital cost needs a human check.** The 334 dollars per kWh behind
  the 189 per kW-yr reference could not be fetched from `atb.nrel.gov` or
  `docs.nrel.gov` from this environment, and rests on search-engine summaries
  of NREL ATB 2024. It is named in the figure, cited as ref5 on the page, and
  flagged here. Worth checking against the real workbook.
- **The synthetic price series was left as the page already describes it.**
  `storage/model.py` falls back to `synthetic_ercot_prices(8760)` because no
  `data/prices.csv` ships. The page's own ref1 already says ERCOT's archive is
  "the price shape the synthetic year is calibrated to reproduce", so the fact
  is disclosed; no stronger wording was added. It is the reason the capital
  cost sits in its own panel, worded strictly as a scale reference and never as
  a payback verdict.

---

# Fourth pass — owner review after the first publish

Everything below was reported by the site's owner reading the published site,
plus one correction that came out of finally reaching a source that had been
unreachable.

## The ATB number was wrong, and now comes from the dataset itself

- **What**: the capital-cost reference on `storage.html`'s duration figure was
  drawn at **$189/kW-yr**, derived from an assumed $334/kWh. That assumption
  came from search-engine summaries, because `atb.nrel.gov` would not resolve
  and the previous pass shipped it flagged rather than verified.
- **Why it would not resolve**: NREL now brands itself NLR, and the Annual
  Technology Baseline moved to **`atb.nlr.gov`**. The old host is dead, not
  blocked. The site is unmistakably the same one - its stylesheets are still
  served as `nrel.complete.min.css`, its social links still point at NREL
  accounts, and it is still DOE-funded on a .gov.
- **The real figures**, pulled from the published dataset
  (`oedi-data-lake.s3.amazonaws.com/ATB/electricity/csv/2024/v3.0.0/ATBe.csv`),
  for Utility-Scale Battery Storage, 4-hour, Moderate scenario, Market case,
  2024: **CAPEX 1,938.204 $/kW** and **fixed O&M 44.247 $/kW-yr**. CAPEX is
  confirmed to be per kW rather than per kWh because its own components sum to
  it exactly: OCC 1,769.877 + GCC 100.000 + CFC 68.327.
- Annualised over the dataset's own 20-year capital recovery period at the 8
  per cent real rate the heat model already uses, that is **$242/kW-yr**, not
  $189. The old assumption implied $334/kWh; the real 4-hour system works out
  at $484.55/kWh. Reference 5 on the page now states all of it.
- **Implication**: the one number this project shipped without a fetched
  source was wrong by about a quarter, which is the argument for the house
  rule rather than against it. It is now computed in code from named
  constants, so it cannot drift from what the citation says.

## The longevity margin scene ran on a timer and started a quarter of the way down

- **What**: two complaints, one cause each. The scene was invisible until
  roughly a quarter down the page; and creatures vanished instantly on a fast
  scroll instead of fading.
- **Why**: depth was keyed to the position of three of the page's own `h2`
  headings and stepped between them as integers. The first tracked heading
  sits about a quarter down, and before it the scene rendered biome 0 - whose
  colours were the page background, so there was nothing to see. Because the
  step was discrete, the only thing making it gradual was
  `biomeShown += (target - biomeShown) * 0.04`, run once per frame. That is a
  timer: at reading pace it eased, and on a fast scroll it was outrun, so a
  creature's opacity collapsed before its fade could play.
- **Fixed**: depth is now a continuous function of scroll position across the
  whole document, and every opacity - the gradient's and each creature's - is
  read from that position with no state carried between frames. Each creature
  has its own home position on the page and fades over 26 per cent of the
  document either side of it, about 3,700px on this page, with the ranges
  deliberately overlapping so the margins are never empty. Verified by driving
  the real `draw()`, `progress()` and `presence()` directly: at the very top
  the first creature is at 0.82 and at the very bottom the last is at 0.82,
  the backdrop moves open water to canopy to abyssal to reef across the full
  scroll, and a 2 per cent scroll step produces a correspondingly small colour
  step rather than a jump.
- **Implication**: scrolling back up now retraces exactly what scrolling down
  drew, which a frame-rate lerp could never do.

## The motion toggle did nothing on two pages if you arrived with motion off

- **What**: both `biome-scene.js` and `margin-scene.js` ended with
  `if (still) return;` before registering their `motionchange` listener. A
  reader who arrived with motion off - which includes anyone whose system asks
  for reduced motion, since that supplies the default - never got the
  listener, so the footer control did nothing on those pages until a reload.
- This contradicts the contract `motion.js` states in its own header: the
  footer control overrides the default *without* one.
- **Fixed** in both: the listeners register unconditionally and only the call
  to `start()` is conditional, which `start()` already guarded anyway.
  Verified by loading with motion off and clicking the control.
- **Implication**: found while checking something else. Nothing tested the
  toggle from an off start, which is the state a reduced-motion reader always
  begins in.

## Figures the owner flagged

- **The home overview's header collided with its own panels.** The subtitle
  ran horizontally into "Where the numbers come from" and sat flush against
  "What the model contains". A consequence of narrowing that canvas from
  14.4in to 10.2in in the previous pass to lift its type off the floor,
  without enlarging the header strip to match.
- **"One node, one step" needed a rework.** Its title was clipped at the left
  canvas edge and the `model.html §4.4` stamp at the right; the numbered step
  captions sat under the wrong elements, with 2 and 3 crowded together; and a
  dead vertical band separated the boxes from the captions. Re-laid out so
  nothing is clipped and every caption sits under what it describes.
- **Throughlines panel B crowded C and D.** The bottom row's wrapped labels
  reached the "C." and "D." titles, and within B a two-line label reached the
  value belonging to the row beneath. Row pitch and inter-panel spacing both
  opened up.
- **The dispatch week's legend sat on the data.** It was placed at a corner
  inside the axes, and a 4-hour battery in a summer week fills every corner.
  Moved outside the axes entirely, below the x-axis label, where it cannot
  collide however the price series moves.
  - **And the reason no audit caught it**: `storage/figstyle.py`'s `finish()`
    only ran `audit()` when a title or footnote was passed. Four of the five
    storage figures pass neither, so they had never been checked at all. The
    audit now runs on every save; confirmed to leave rendered pixels
    unchanged.

## Library captions were reading as a layout fault

- **What**: capping a caption at 72ch inside a 1082px-wide card left every one
  of them in the left half with the right half empty.
- **Fixed** by setting them in two columns, which uses the width the figure
  already claims and gives a roughly 55-character measure - better than the 72
  it had. The captions run 186 to 636 characters, so each has the body to fill
  two columns; below the 760px breakpoint, where the card is back to prose
  width, they collapse to one.

## Still open

- `longevity-quotient/test_perf.js` cannot run here: it requires `jsdom`,
  which is not installed. Pre-existing, and it exercises that sub-project's
  own copy of the page rather than the site's.
- `sync_assets.py` still reports six orphaned assets - `dac_fig1/2/3/5.png`,
  `nitrogen_fixation.png`, `running_shoe.png`, about 1MB. No generator exists
  for the DAC set anywhere in the repo and no page references any of them.
  They are shipped but unreachable. `--apply` would prune them; that is a
  deletion, so it waits for a decision.

---

# Fifth pass — the longevity margin scene

## The sitewide node graph is off that page

- **What**: `longevity.html` draws its own scene - a vertical biome gradient
  and real animals in the margins - and the sitewide `body::before` node/edge
  tile sat behind it as a second, unrelated background competing with it.
- **Fixed** with a `body.bg-biome` class, the same override convention
  `bg-curve-heat`, `bg-curve-storage` and `bg-force-graph` already use. It
  keeps the two soft radial washes, which are what stop the black reading as
  a void, and drops only the graph tile. Every other page is untouched.

## Fourteen animals instead of six, and the numbers now match the table

- **What**: the scene carried six creatures, four of them OpenMoji icons.
  There are now **fourteen**, twelve of them icons, extracted from the
  OpenMoji 17.0.0 release archive's `black/svg` set (the outline-only
  variant; the colour set would fight the palette).
- **Ordered as a descent**: bat, ant, chameleon, elephant across the canopy
  and ground; mole-rat, tortoise, whale through open water; shark, rockfish,
  tubeworm in the deep; mussel, quahog, octopus, nautilus on the floor. Two
  to four are visible at any depth, verified across the whole scroll.
- **`BIOME` was reordered** so canopy is 0 and the floor is 3. Before, the
  page opened over land animals while the tint said open water.

### Three labels had drifted from the table

Corrected against `longevity-quotient/outputs/lq_table.csv`, the same table
the page's figures are drawn from:

| creature | said | is |
|---|---|---|
| bat | Chiroptera 2.5x | Brandt's bat 12.75x (the order itself is 2.68) |
| tubeworm | 22x | 23.41x |
| quahog | 45x | 47.48x |

Every one of the fourteen now carries its own species' `lq_class_maximum` and
its own `maximum` lifespan - the same baseline the visualiser opens on.

### Three bugs found while doing it

- **A creature with no way to draw it killed the whole scene.** `DRAW` was a
  hand-written table, so a kind added to `ICON_SRC` and `CREATURES` without a
  matching entry threw `DRAW[c.kind] is not a function` on the first frame -
  which stops the animation loop for every creature, not just that one. `DRAW`
  is now built from `ICON_SRC`, and a creature naming an undrawable kind
  throws at load with a message that says so.
- **Half the icons would have been invisible.** OpenMoji writes its single
  stroke colour as `#000000` on some icons and `#000` on others; the recolour
  matched only the long form, so the short-form ones would have drawn black on
  a near-black page. Icons are normalised to the long form on extraction, and
  the recolour now matches both.
- **Labels were drawn through their own creature.** The placement reserved a
  flat 140px for every label, which was fine while they read "octopus" plus a
  quotient. Carrying a species name, a quotient and a lifespan they run past
  200px, so the flip-to-the-left test fired too late. The width is measured
  now.

## Still open

- **The longevity Manim video disagrees with the table.**
  `longevity_quotient.mp4` and its poster are annotated "ocean quahog 45x" and
  "giant Pacific octopus about a twentieth", and `longevity.html`'s caption
  repeats them. Against the published table the quahog is **65.32x** on the
  global fit and **47.48x** on its class fit; the octopus is **0.22x** global
  and **0.11x** class. The caption says "distance from the global fit", so
  neither number matches on either baseline. Left alone rather than guessed
  at: the numbers are baked into a Manim scene and which baseline was intended
  is a question for whoever wrote it. The margin scene beside it now states
  the table's own figures, so the two are visibly inconsistent until this is
  settled.
- The six orphaned assets stay, by decision.

---

# Sixth pass — the scene grows up

## Longevity: twenty-four animals, bigger, and no longer mirrored

- **Bigger.** Icons were sized `max(7, min(16, bandWidth * 0.09))`, tuned when
  there were six of them; they read as specks. Now
  `max(11, min(24, bandWidth * 0.13))`.
- **Twenty-four species, up from fourteen**, twenty-two of them real OpenMoji
  icons. Added: honey bee queen 1.98x, pink cockatoo 4.55x, Laysan albatross
  2.60x, Mexican redknee tarantula 3.55x, giraffe 0.84x, African penguin
  1.41x, Baikal seal 2.13x, moon jellyfish 0.07x, American lobster 3.04x,
  Roman snail 3.91x, and black coral at **122.84x on a 4,265-year lifespan**,
  which is the most extreme thing in the whole table that has an icon.
  Every quotient is that species' own `lq_class_maximum` and every lifespan
  its own `maximum`, from `longevity-quotient/outputs/lq_table.csv`.
- **The nautilus was dropped** and its snail icon reassigned to the Roman
  snail, which is a real species in the table. The nautilus had been drawn
  with a snail because no nautilus icon exists - an inaccurate pairing kept
  only because it was already there.
- **A caution on picking species by icon.** Searching the table for names
  matching an available emoji returns confident nonsense: "bear" matches
  *Black-bearded Tomb Bat*, "horse" matches *Lesser horseshoe bat*, "crab"
  matches *Crab-eating raccoon*, "swan" matches *Swan Island Hutia*. Every
  pairing above was checked by hand; none of those four shipped.
- **No longer mirrored.** Both margins drew the same creature at the same
  moment, so the page read as a mirror rather than as a place. Each creature
  now takes one side, strictly alternating down the page, so consecutive
  creatures land opposite each other. Verified across the scroll: two to four
  visible at every depth, both margins always populated, never with the same
  animal. When the window is too narrow for two bands, the single surviving
  band takes every creature rather than half of them silently vanishing.
- **Colour is resolved from `ICON_SRC`** rather than duplicated on each
  creature, so the icon and the label can no longer disagree about which
  palette entry a species uses.

## Still open

- The longevity Manim video's "45x" and "a twentieth" still disagree with the
  table on either baseline - see the previous pass. The margin scene beside it
  now names twenty-four species with the table's own figures, which makes the
  disagreement more visible, not less.

## Other pages are scroll-driven too

`margin-scene.js` - the shared scene on index, library, code, heat, storage,
skyline, desktop and climate-cost - now uses the same contract
`biome-scene.js` does. Which item is visible, and how strongly, is a pure
function of scroll position; only each kind's small idle motion (a dot's
shimmer, a bar's breathing, a pulse travelling its path, an arc's wobble)
stays time-driven.

- Every item gets `at = (i + 0.5) / n` and `span = 2 / n` from its own index
  and the item count, so a three-item scene (heat) and a forty-four-item scene
  (desktop) both settle to two to four live at once. No page's
  `window.MARGIN_SCENE` config needed editing - the real labels and numbers
  each page publishes are untouched.
- **Sides alternate** there too, so those pages stopped mirroring as well.
  `bandForSide()` falls back to whichever band exists when the window is too
  narrow for two.
- **A missing repaint was fixed on the way**: with motion off, this file only
  redrew on resize, so a reader scrolling with motion off kept a frame
  belonging to a scroll position they had left. It now repaints on scroll the
  way `biome-scene.js` does.
- Verified per page by driving the real `draw()`/`presence()` at p=0, 0.5 and
  1: two to four live at each, alternating sides, both margins populated.

---

# Seventh pass — the scenes fill the page

## Everything was glued to the top quarter of the window

- **What**: every scene on the site drew its items inside the top ~200-370px
  of the viewport, with the rest of the margin empty.
- **Why**: each kind computed its row height as
  `Math.min(CAP, (H - 40) / ROWS)` with CAP between 34 and 70. On an 876px
  window `(H - 40) / 5` is 167, so the cap always won, five rows spanned
  20..190 or 20..370, and the rest of the column was never used. The cap was
  presumably meant as a maximum item height; it silently became the layout.
- **Fixed**: `slotY(i, frac)` derives the slot from the real column - from
  below `nav.top` to the bottom of the viewport - and each kind asks for a
  fraction of its slot for its own drawing box. On the same window the rows
  now run 117..796.
- An item's row is stamped on the item by `assignAtSpan()` rather than read
  from its index in whichever list is being drawn, which is what makes the
  collage below possible without two kinds both starting at row 0.

## The bookshelf and the skyline lost the node tile too

`body.bg-biome` became `body.bg-own-scene` and now covers longevity, desktop
and skyline: three pages that draw a scene of their own and had the sitewide
node/edge tile sitting behind it as a second, unrelated background. Every
other page keeps the tile.

## The home page is a collage of the others

A new `collage` scene kind takes a list of parts, each with its own kind and
its own items. Each part is laid out by its existing layout function, then the
union is re-assigned across the document in interleaved order, so a reader
going down the home page meets a card from the atlas, then a bar from the code
index, then a pulse from the heat model, then an arc from the climate
calculator - rather than one of every kind at every scroll position.
`drawCollage()` is five lines: every draw function already skips items that
are not live.

Every number in it is already published on the page it comes from.

## More content in the thin scenes

- **heat**: 3 to 11. Added the fuel-only break-even (1.38 c/kWh), the
  capital/fixed-ops sensitivity (+/-0.15 c), the emissions parity threshold
  (0.209 tCO2/MWh) against the ERCOT average (0.333), both boilers' emissions
  (99.6 and 62.4 kg/MMBtu) and the fuel share of each boiler's cost ($4.12 of
  $5.13, $19.44 of $20.00) - all sentences already on the page.
- **storage**: 3 to 10. Added the duration table's own equivalent-cycles and
  hours-at-rated-output columns, and the $242/kW-yr capital reference from
  ref5.
- **skyline**: 15 to 27, the full city roster. The twelve added cities carry
  the musical key the app itself assigns them - each key in that payload also
  carries a `why` explaining the choice - checked one by one against
  `skyline-app.html`'s own data, not inferred.
- code (12), climate-cost (20), library (13) and desktop (44) were already at
  full coverage of their pages' real content and were left alone.

**A verification note worth keeping**: two of the added numbers looked
unsourced on a first grep - heat's "0.15 cents" and the twelve skyline keys -
and both turned out to be real. The first was split by markup so a plain text
search missed it; the second sits after a several-hundred-number `prof` array,
outside the window the first check looked in. Neither was invented; but the
check that finds that out has to parse, not grep.

---

# Eighth pass — slower fades, and a bare code page

## Items now hold at full opacity instead of peaking at a point

- **What**: presence was `ease(1 - |p - at| / span)` - a single peak. An item
  was fully opaque at exactly one scroll position and visibly on its way in or
  out everywhere else, which is why the scenes still read as flicking past
  however slowly you scrolled.
- **Fixed**: the profile is a trapezoid. Full opacity anywhere within `hold`
  of the item's own slot, then a fade to nothing at `span`. Both are expressed
  in item-spacings so the feel is identical whether a page hands over ten
  items or forty-four: an item is fully opaque across two spacings and fades
  over another two, so it is on screen for six in all, against four before
  with no plateau at all.
- On heat.html an item now holds full opacity across about a fifth of the
  document - roughly 1,500px of scrolling - with fade tails of about the same
  length either side. On the home page, every one of forty-one sampled scroll
  positions has at least one item at full opacity; before, that was true only
  at isolated points.
- **ROWS 5 to 7.** Six items can now be live at once, and two items sharing a
  row are seven spacings apart, wider than the six-spacing window, so a row is
  never asked to hold two visible items. Checked across forty-one positions on
  two pages: max six simultaneous, zero row-and-side collisions.
- Both caps (`hold` at 0.16, `span` at 0.42 of the document) exist so a scene
  with very few items does not end up with all of them permanently on screen.

`biome-scene.js`, which drives longevity.html, was deliberately left alone.

## code.html has nothing behind it

It is a plain index of downloads and now carries no scene and no background
layer at all: the `MARGIN_SCENE` config and the `margin-scene.js` tag are gone
from the page, and `body.bg-bare::before { content: none; }` removes the
sitewide background pseudo-element outright rather than blanking its paint, so
nothing is composited over the page. Verified in the browser: zero canvases,
`window.MARGIN_SCENE` undefined, and the only scripts left are `motion.js` and
`lightbox.js`.

The twelve real archive sizes that scene carried are still on the page, in the
downloads table they were read from in the first place.

---

# Ninth pass — longer tails still

Fade length raised again, everywhere except longevity.html.

- `span` 3/n to 4.5/n (cap 0.42 to 0.55). `hold` is unchanged, so the plateau
  is the same width and only the approach and departure grew: the fade on each
  side went from two item-spacings to three and a half.
- On heat.html that is **2,690px of scrolling per fade**, up from about 1,540,
  against an unchanged 1,535px of full opacity in the middle.
- **ROWS 7 to 10.** An item is now live across nine item-spacings, so up to
  nine can be on screen at once - most of them faint, out in a tail. Two items
  sharing a row are ten spacings apart, wider than that window. Verified on
  four pages across sixty-one scroll positions each: max nine live, **zero
  row-and-side collisions**, and something at full opacity at every single
  position.
- Ten rows in a 787px column give each item a 49px box, which cards still
  render title and author into without clipping - checked on desktop.html,
  the densest scene at forty-four items.

`biome-scene.js` was not touched: longevity.html keeps its own profile.

---

# Tenth pass — longevity joins the rest

The longevity scene now uses the same fade shape as every other page, and
three things had to follow from that.

- **Trapezoid presence**, `hold` and `span` computed from the creature count
  in one place rather than written on each of the twenty-four: about 1,200px
  of full opacity and 2,100px of fade on each side of it. Something is at
  full opacity at every one of forty-nine sampled scroll positions; before,
  a creature was fully drawn at one exact position and nowhere else.
- **Lanes.** With two or three creatures on screen their hand-authored paths
  kept them apart by luck. At nine, luck ran out: the Baikal seal and the
  naked mole-rat drew their labels on the same line, one over the other and
  neither readable. Each creature now has one of ten lanes and plays its
  waypoint path out inside it - the drift survives, the collisions do not.
  Creatures sharing a lane are ten slots apart, wider than the nine-slot
  window, so a lane never holds two visible creatures. Zero lane-and-side
  collisions across sixty-one positions.
- **Bands re-anchored** to wide-start/wide-end plus a gutter, matching
  margin-scene.js. Anchored to the text column, a label ran underneath this
  page's own full-width figures and read as truncated - the text was there
  with an opaque figure card painted over its first two thirds.
- **Labels fall below the icon when they cannot fit beside it.** A margin is
  about 240px wide and these labels run to 200, so once the icon has its 48px
  there is often no room alongside. Two placements are tried and each is
  rejected if it intersects the icon; failing both, the label drops under the
  creature and uses the band's full width. The overlap check on its own made
  every label disappear - the fallback is what brought them back.
