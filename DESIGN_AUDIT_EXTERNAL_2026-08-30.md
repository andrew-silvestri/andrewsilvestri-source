# External design & legibility audit — andrewsilvestri.com

Audited 2026-08-30 in Chrome at 1440×900 and 390×844, live site, all pages, both
interactives, motion on and off. File weights and image dimensions verified
against the repo.

## Verdict

A stranger who models energy systems lands here and gets the right first
impression fast: a coherent dark system, a real 86,622-node artifact behind it,
prose that says what is measured and what is assumed, and source you can
actually download. That impression is then taxed three ways: the two pages that
carry the intellectual weight (`atlas.html`, `model.html`) run their body text
directly over a full-opacity background graph for thousands of pixels; the
static figures are drawn at 1425–2016px and rendered at ~554px, so their axis
text lands at ~6px effective — the charts look like exhibits you aren't meant
to read; and the scroll experience has long dead stretches and late reveals
that make the site feel emptier than it is. The system is right. The
enforcement is uneven.

## Findings

### 1. Body text over the force-graph background — `atlas.html`, `model.html` · **high**

**Observed.** Both pages place a fixed radial force-graph (60-odd nodes at
roughly half opacity, plus edge lines) behind the centre text column, and it
stays behind the text for the full scroll — 6,700px on atlas, 9,300px on
model. Every paragraph from "What a run does" downward is read over dots and
lines passing under the serif glyphs. Global contrast of body text (#e3e6f2 on
#070a12, ~16:1) is fine; local contrast where a violet node sits under a serif
hairline is not, and the speckle forces constant re-focusing. These are the
two pages where you most need the reader to sustain attention through dense
prose.

**Why it hurts.** It converts your best writing into your hardest reading. The
other pages get this right — margins carry the decoration, the column stays
clean — so the two most important pages are the two worst-treated.

**Fix.** Any of: (a) put a solid or near-solid panel under the prose column
(the library's figure cards already do this — note how much easier they read);
(b) mask the graph out of the column with a gradient; (c) move the graph to
the margins like every other page. Fifteen minutes of CSS.

### 2. Static figures rendered at 39% of drawn size — library, home, model · **high**

**Observed.** Library figures are 1425–1650px PNGs rendered at 554px
(measured). Matplotlib tick and axis labels drawn at ~15px in the bitmap land
at ~6px effective — below the ~11px comfortable-reading floor, and below
legibility outright for the log-scale exponents (10⁰…10⁵ superscripts).
Worst offenders: the home "world energy model" composite (2016px into ~900px,
with an 8-entry donut legend at ~7px), `05_link_structure`, `07_arrival_order`
(5-series line chart whose legend text and near-identical thin lines are
indistinguishable at render size), and model.html's bottom dashboard. The home
mosaic renders these same 1425px images at ~190px — pure texture, with
`alt=""`.

**Why it hurts.** The figures are the portfolio. A reader who can't read the
axes can't check the claim, and these pages are precisely a demonstration that
you make checkable figures.

**Fix.** Pick one: regenerate at the rendered geometry (content column is
~650px; draw at 1300px with fonts sized for 2× — i.e. double every font size
in the build scripts), or add a click-to-open lightbox to every `figure.card`
(one small shared JS function, no framework), or both. The heat/storage
animated figures already carry page-scale fonts — they prove you know the
target; the matplotlib scripts just weren't given it.

### 3. Scroll-reveal blanking and dead vertical space — sitewide, worst on home · **high**

**Observed.** Scrolling the home page at normal speed produced full viewports
of pure background — my capture caught an entirely black 1512×796 frame
mid-page. Reveal animations trigger late (elements enter well inside the
viewport) and transition slowly, so fast scrollers see nothing where content
is. Separately, section spacing is enormous: ~500px of empty dark between the
figure strip and "ENERGY", again before "CLIMATE RESEARCH" and "OTHER WORK".
Of the home page's 3,800px, something like a quarter is empty ground.

**Why it hurts.** A dark theme makes emptiness read as *nothing has loaded*,
not as breathing room. Combined with late reveals, the site's first minute
feels sparse and slightly broken, which is the opposite of an 86,622-node
model.

**Fix.** Expand the IntersectionObserver `rootMargin` so reveals start
~200px before entry; cap transitions at ~300ms; halve the section paddings.
Also make reveals idempotent on fast scroll (element already past the
viewport = show instantly, never blank).

### 4. Margin decorations colliding with content — `code.html`, `desktop.html` · **medium-high**

**Observed.** On `code.html` at 1440px the margin bar-chart (archive sizes:
heat, storage, atlas…) renders *underneath the table rows* — the wide green
"atlas" bar runs behind the "Climate cost calculator" link text. On
`desktop.html` the drifting book cards slide under the top nav ("Brave New
World — Huxley, 1932" behind "Home"; "1984 — Orwell, 1949" at top right). On
the home page the ghost stat cards ("1,144 negative links / relief, not
stress") sit flush against the content column edge and read as stray text
next to real copy.

**Why it hurts.** The margin scenes are one of the site's signatures, and a
signature that overlaps content looks like a bug, not a flourish.

**Fix.** In `margin-scene.js`, clamp the drawing region to
`(0 → content.left − 24px)` and `(content.right + 24px → viewport)`, and start
below the nav's bottom edge. The scenes already know the column exists on most
pages; enforce it everywhere, at every width.

### 5. `storage.html` duration chart hides its own headline · **medium**

**Observed.** "Energy-arbitrage value by duration" draws three zero-based bars:
$98, $107, $111/kW-yr. They read as equal. The page's one-line claim is "value
flattens above four hours" — the chart makes that flattening invisible;
worse, at a glance it suggests *more duration keeps paying*.

**Fix.** Chart the marginal value instead: +$9/kW-yr going 2h→4h, +$4 going
4h→8h (per the page's own table), or keep the bars and annotate the deltas on
the steps. This is the classic wrong-chart-for-the-question case; the
question is about the increment, so plot the increment.

### 6. Longevity lollipop wastes half its panel · **medium**

**Observed.** "Who beats their body mass, and who does not"
(`longevity.html`): the ×1 baseline sits mid-panel and the visible top-25 all
extend right, leaving the entire left half of a ~1,200px plot empty grid.

**Fix.** If below-1 species appear further down the same figure, fine — but
then the figure should open at a height where both directions are visible, or
be split into two half-width panels (over / under). If the left half never
fills, start the axis at ~0.8×.

### 7. Sentinel value leaking into the visualiser UI — `longevity-app.html` · **medium**

**Observed.** Row 6 of the default view: "*Terrapene mexicana* (-999)". A
missing-common-name sentinel is being displayed as the common name, inside the
default sort where everyone will see it.

**Fix.** Treat `-999` (and empty) as missing in the loader; show the
scientific name alone. Also worth a grep of the CSV for other sentinel fields.

### 8. `climate-cost.html` "one hide" figure reads as broken · **medium**

**Observed.** A ~650px-tall card containing one small bar, "7.0%", "11.65 kg
CO2e", and the phrase "same hide, same animal – nearly tripled" scattered with
large empty gaps, no axis, no second bar to compare against. It looks like an
animation captured mid-frame. The comparison it wants to make — 2.2% economic
vs 7% mass allocation, 3.66 vs 11.65 kg — is exactly two bars side by side.

**Fix.** Two labelled bars (economic vs mass allocation), values on the bars,
one sentence beneath. Half the height, all of the point. Separately: the
20-item table above it has numbers spanning 0.56→75.49 with no inline bars —
a 100px bar column would let the reader *see* that a flight and a t-shirt are
different animals.

### 9. Atlas app: the run's result is easy to miss · **medium**

**Observed.** Running "Attention is exhausted" updated the layer tabs (169
hit / 142 hit / 3 hit — nice) but the RESULT block sat below the sidebar fold
at 796px viewport height, and the on-globe response was over by the time the
eye went looking. Clicking the globe (the promised "click a point and push on
it yourself") from an ocean click produced no feedback at all — no "nothing
here" affordance. The 60-scenario `<select>` is one flat list even though the
data is "grouped by kind".

**Fix.** Scroll the RESULT block into view (or pin it) when a run completes;
flash a subtle ring where a click landed, with "no node within N km" on a
miss; use `<optgroup>` per scenario kind.

### 10. `model.html` dashboard: panel D and E undercut the set · **medium**

**Observed.** Panel D ("A large oil supply loss, step by step") draws 8 layers
as thin lines, 7 of them near-identical violet/slate, with a 6px two-column
legend; only one line is identifiable. Panel E ("Which kind of change reaches
which layer") uses a magma/inferno ramp — yellow/orange/magenta — the only
figure on the site off the palette, and its pure-black cells are ambiguous
(zero? no data?). The A/B chain diagrams above truncate node names with "…" at
~9px.

**Fix.** Panel D: direct-label the two lines that carry the story (Power
station, National grid), grey the rest to one muted tone. Panel E: rebuild the
ramp from the site's violet (or moss→violet), and give true-zero cells a
distinct "empty" hatch or dot. The chain diagrams need one more line of
vertical space per label instead of ellipsis.

### 11. Hero globe doesn't survive a resize · **low**

**Observed.** Resizing the window (1440→390) leaves the WebGL globe rendered
at the old centre — a mostly-empty dark box with the globe cropped at one
edge — until reload. Fresh mobile load is fine. Rotation/orientation changes
on tablets will hit this in the wild.

**Fix.** Handle `resize` in `hero-gl.js`: update camera aspect +
`renderer.setSize` on a debounced listener.

### 12. Small-type inventory · **low**

- Nav links: 13px with a 23px hit box — fine with a mouse, tight on touch;
  the mobile dropdown carets sit at the far right edge, ~40px from screen
  edge, ~700px from their label at tablet widths.
- "MAIN PROJECT" kicker: 10.5px. The all-caps kickers are doing hierarchy
  work; 10.5px is below the useful floor even for caps. 11.5–12px keeps the
  look.
- Margin ghost-cards ("60 prepared scenarios / grouped by kind") set ~11px in
  low-alpha slate — intentionally sub-legible, but they sit close enough to
  the column to be mistaken for real UI. If they're texture, keep them
  strictly outside the column (see finding 4); don't let texture carry words
  that near to content.
- `bookshelf-app` control panel labels ~10px.

Muted text (#8b93b0 on #070a12) measures ≈6.4:1 — passes AA including small
text; the violet (#8b7ff2) ≈6:1 — also fine. No AA failures found in the core
palette; the failures here are size, not contrast.

## What's missing

Ranked; each line is what a reader currently cannot do.

1. **A layer diagram on `atlas.html`.** The page describes nine layers, their
   node counts, and which links are one-way, in a table and four paragraphs.
   A single vertical schematic — layers as bands, arrows for direction,
   climate/events shown as one-way sources — would let a reader hold the
   architecture in their head before the prose asks them to use it. This is
   the highest-value 200 lines of SVG on the site; `model.html`'s "One node,
   one step" proves you can draw it.
2. **Propagation you can watch.** The atlas app reports runs as end-state
   numbers; the model's whole identity is *travel*. A step slider (or replay
   button) that walks the pulse outward hop by hop would teach the
   mean-not-sum rule and the inertia ordering better than either page of
   prose. The data is already there — the run computes per-step states.
3. **Figures on the home tool cards.** Heat, Storage and Climate-cost are
   text-only cards on a chart-dense site. Each has an obvious hero (break-even
   crossing, duration curve, the process tree). Without them the home page
   undersells your three most finished products.
4. **A comparison for the storage number.** The heat page's "electricity must
   fall about 4.2×" is the model of a number with a handle. Storage stops at
   "$98–111/kW-yr" and never says the one thing a reader wants: what does a
   battery *cost* per kW-yr, i.e. does it pay? One line and one dashed line on
   the duration chart.
5. **A person.** There is no about page — just an email in the footer. For a
   portfolio, one short paragraph (who you are, what you're for, one link)
   under "OTHER WORK" or in the footer would convert curiosity into contact.
6. **A figure lightbox.** Until figures are regenerated (finding 2),
   click-to-full-size is the cheap patch, and it stays useful afterwards.
7. **Deep links from claims into the visualiser.** `longevity.html` says "the
   bats of Chiroptera at 2.68 across 267 species" — that sentence should be a
   link into the app pre-filtered to Chiroptera. The app has the filter;
   it needs URL state (which also makes any view shareable — currently no
   view survives a copy of the address bar).
8. **A worked example on `climate-cost.html` before the calculator.** The page
   explains allocation abstractly, then offers a button. One pre-traced chain
   (the tomato, four levels, numbers on each edge) as a static figure would
   set up the interactive instead of asking it to carry all the teaching.

## Ten-minute wins

- Fix the `-999` common name in the longevity app's loader.
- `<optgroup>` the 60 scenarios by kind in the atlas app.
- `loading="lazy"` on the 12 library and 7 home `<img>`s (currently all eager).
- Halve the section padding on the home page; the emptiness is CSS, not content.
- Real `alt` text on the home mosaic thumbnails (they are content, currently `alt=""`).
- Annotate the storage duration bars with the +$9 / +$4 marginal steps.
- Kicker floor 10.5px → 12px (one token in `style.css`).
- Clamp `margin-scene.js` drawing to outside the content column and below the
  nav (fixes both collision pages at once).

## What to leave alone

- **The heat.html figure suite.** Animated video figures with poster frames,
  serif annotations inside the chart matching the page's body face, direct
  labels instead of legends, the break-even and parity points named on the
  plot. This is the strongest set on the site and the template the others
  should be regenerated against. The tornado chart is the best single figure
  here.
- **The atlas app.** The globe is fast, the bottom layer bar is a genuinely
  good navigation idea, the "hide small nodes" slider with its honest caveat
  ("this changes the view, not the answer") is exactly the site's voice as UI.
  Fix the feedback (finding 9); change nothing structural.
- **The prose voice.** "These are not forecasts… A model that answers the same
  number to every question is not answering." Sourced footnotes with numbered
  markers, "what is measured / assumed / invented" labelling. Do not let any
  redesign flatten this.
- **The serif body / sans UI split.** It holds up everywhere the background
  stays out of the way. The problem was never the type system.
- **Discipline you already have:** no build step, versioned asset URLs,
  `prefers-reduced-motion` respected, WebP where it matters, pages in the
  300–600KB range, source archives with READMEs. None of the fixes above
  require abandoning any of it.
