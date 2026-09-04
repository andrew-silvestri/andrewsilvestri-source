# Deslop audit — andrewsilvestri.com — 2026-09-04

Phase 1 of `DESLOP_PROMPT.md`. Nothing in `site/` was changed. All tooling
lives in `_deslop/` at the repo root (gitignored): `measure.js` (Playwright
driver), `analyse.js` (digest), `static_inv.py` (static inventory),
`results.json` (raw measurements, 55 page×viewport×motion runs),
`analysis.md` (every table the findings below quote from), `shots/` (100
screenshots, named `<page>-<desk|phone>-<on|off>[-light]-<top|full>.png`).

**Disclosure.** The brief says not to open the appendix checklist until 1c is
written. I `cat`-ed `DESLOP_PROMPT.md` whole to read the brief, so the
six-item checklist was in front of me before I measured anything. I did not
open the two prior audit documents until §6. Where a finding below coincides
with the checklist I say so in §7 and say whether my method would have found
it alone; I have tried not to let the list steer severity.

**Measurement conditions.** Chromium 151 headless (Playwright 1.62) on
Windows 11, `deviceScaleFactor: 1`, served from `site/` over
`http://127.0.0.1:8765`. Every content page at 1440×900 and 390×844, with
`prefers-reduced-motion` unset (motion on) and set (motion off), dark
scheme; `index.html` additionally in the light scheme. Five apps at both
viewports, motion on. CPU figures are Chromium's `Performance.getMetrics`
`TaskDuration` over a 3 s idle window after load; headless has no GPU, so
canvas/WebGL costs are inflated relative to a real machine and should be
read as relative, not absolute. Contrast ratios are WCAG 2.x, computed from
the computed `color` against the nearest opaque ancestor background,
alpha-composited where a layer is translucent. Platform fonts are the faces
Chromium actually rasterised (`CSS.getPlatformFontsForNode`), so they are
Windows faces; Mac and Android resolve differently and I say where.

---

## 1. Criteria (written before measuring)

### 1a. What the sources say the tells are

Six-plus sources read, the strongest being a deterministic Playwright audit
of 1,590 Show HN landing pages (Developers Digest, 2026-04) which is the
only one with incidence rates and a stated false-positive rate (5–10%). The
others are practitioner write-ups (925Studios, prg.sh, Impeccable's 61-rule
detector, Shuffle, VibeZero, Jack Pearce) and two critiques of the label
(d4b.dev; Nishal/Sax/Kieslich in ACM AI Letters). Sources and evidence are
in `_deslop/research-tells.md`.

The checkable list, with the evidence grade for each:

| # | Tell | Evidence | How to check here |
|---|---|---|---|
| T1 | Indigo/violet accent or violet→blue gradient on a dark ground | Strong: 27% of 1,590 pages; mechanism traced to Tailwind's `indigo-500` default | Read `--acc`; look for gradients using it |
| T2 | Dark mode as the default state | Strong: single highest-incidence tell, 34% | `:root` palette |
| T3 | Three-up card grid, each card = kicker + title + body, identical structure | Strong: 22% | Count `.cardgrid` and card shapes per page |
| T4 | Card = hairline border + soft drop shadow + subtle gradient fill | Medium: two detectors, no rate | `.card` rule |
| T5 | Glassmorphism (blur + translucency) | Medium; contested as pre-AI trend | grep `backdrop-filter` |
| T6 | All-caps kicker/badge above a heading with wide tracking | Medium | `.tag`, `h2`, `th` rules |
| T7 | Inter/system-sans as the only face, or a generic stack with no chosen face | Medium; Anthropic's own frontend guidance names it | `--sans`, `--serif`, resolved platform font |
| T8 | Low-contrast text on dark | Medium | Computed ratios |
| T9 | Coloured glows / neon box-shadows / additive bloom on dark | Medium | grep `box-shadow`; look at the hero |
| T10 | Decorative motion: particles, ambient canvases, pulsing dots, typewriter/terminal reveals | Weak–medium (qualitative) | Motion inventory: what a reader loses if deleted |
| T11 | Em-dash overuse in copy and titles | Weak (copy-level, contested) | Count in body and `<title>` |
| T12 | Stat-banner rows and numbered step sequences | Weak (one source) | `.sys-log`, mosaic strip |
| T13 | Section order hero → cards → cards → CTA | Weak | Home page structure |
| T14 | Generic tokens (`--primary`) vs named, opinionated ones | From the "good sites" side | `:root` names |
| T15 | Decoration that is not the content | From the "good sites" side | Margin scenes, backgrounds |

Counter-arguments taken seriously: every tell above is also a real
early-2020s design fashion adopted by humans; the best detector treats any
single tell as weak and scores by count (4+ = heavy); dark mode and violet
are defensible choices when made deliberately. The question for this site
is therefore not "does it have tells" but "does it have several, and are
they defaults or decisions."

### 1b. What the good sites actually do

Twelve researcher/engineer sites inspected by reading their CSS (gwern,
Ciechanowski, Julia Evans, rsms, Nicky Case, MacWright, Andy Bell, Bret
Victor, Robin Rendle, Wattenberger, Maggie Appleton, Chris Olah); notes in
`_deslop/research-good-sites.md`. The checkable properties that recur:

- **A typeface that cost something.** Self-hosted or uncommon: Source
  Serif/Sans, Berkeley Mono, Canela, Computer Modern, self-drawn MD UI. Not
  one of the twelve relies on a bare system stack for its body text.
- **A stated measure**, usually in `ch` or a small rem count (65ch, 36rem,
  640px), and a base size that was chosen (18–23px is common).
- **One accent doing one job.** Where palettes are large they are
  structured scales with light/dark pairs, not five brand colours.
- **Named, idiosyncratic tokens** (`--GW-blood-red`, an 8px `--unit`).
- **Decoration that is the content**: interactive diagrams, the author's
  own drawings, a self-portrait. No applied ornament.
- **Dark done well** means a considered dark palette (Victor's navy
  `#10183a` with `#ace` text and one yellow) or a complete parallel token
  scale, never a partial inversion.
- **Density and idiosyncrasy are fine.** Victor at 13px/564px and Case at
  23px in a thick rounded box both read as authored. "Not slop" is
  specificity applied consistently, not minimalism.

---

## 2. What was measured (summary; full tables in `_deslop/analysis.md`)

### 2a. Weight

Desktop, dark, motion on. The brief's stated discipline is 300–600 KB per
page.

| page | total KB | html | css | js local | js CDN | images | video | motion-off total |
|---|---|---|---|---|---|---|---|---|
| index | **1,555** | 10 | 29 | 167 | 118 | 1,231 | 0 | 1,437 |
| atlas | 257 | 15 | 29 | 20 | 56 | 138 | 0 | 202 |
| model | 562 | 14 | 29 | 20 | 56 | 443 | 0 | 507 |
| library | **981** | 15 | 29 | 34 | 0 | 903 | 0 | 981 |
| code | 40 | 5 | 29 | 6 | 0 | 0 | 0 | 40 |
| heat | **736** | 11 | 29 | 35 | 0 | 476 | 185 | 552 |
| storage | **912** | 10 | 29 | 35 | 0 | 622 | 216 | 696 |
| climate-cost | 579 | 16 | 29 | 35 | 0 | 244 | 255 | 324 |
| longevity | **1,294** | 22 | 29 | 37 | 0 | 977 | 189 | 1,106 |
| skyline | 404 | 10 | 29 | 35 | 0 | 80 | 250 | 155 |
| desktop | **921** | 10 | 29 | 35 | 0 | 458 | 389 | 532 |

Six of eleven content pages exceed 600 KB; the home page is 2.6× the
ceiling. Images are 79% of the home page and 87–92% of library, longevity
and storage. The only CDN requests are three.js r128 (118 KB, index and
two apps) and force-graph 1.51 (56 KB, atlas and model); no webfont.

Apps: atlas-app 10.0 MB (9.8 MB is `atlas-data.js`, the payload);
longevity-app 974 KB single file; climate-cost-app 387 KB; skyline-app
333 KB; bookshelf-app 36 KB.

### 2b. Type

25 distinct size/weight/leading/tracking/family tuples across the content
pages; 15 distinct rendered sizes on desktop: 9, 9.17, 10.5, 11, 12, 12.08,
12.5, 13, 13.5, 14, 14.5, 15, 17.5, 19, 34 px. Under 12 px on every page:
the dropdown caret at 9 px (33 uses), `th` at 11 px (52 uses, 7 pages),
citation superscripts at 10.5 px (24 uses, 4 pages). Body prose is 17.5 px
/ 30.1 px (1.72) at a 612 px measure on desktop (≈72ch) and 350 px on the
phone; h1 34 px / 27 px. Everything between 12 and 15 px is UI sans.

Resolved faces on this Windows machine: body and headings **Palatino
Linotype**; h2/nav/tags/tables/footer/refs **Segoe UI**; code and sys-log
**Cascadia Mono**. On a Mac the same rules resolve to Iowan Old Style, SF
and SF Mono; on Android the serif stack (`Iowan Old Style, Palatino
Linotype, Palatino, Georgia, Times New Roman`) has no hit at all and falls
to the platform default serif (Noto Serif). Figures are set in Segoe UI /
DejaVu Sans by matplotlib (`build_*.py`, `heat/figstyle.py`,
`storage/figstyle.py`); the five explainer videos and their posters are set
in Computer Modern; `longevity-app.html` body is Georgia; `bookshelf-app`
is all Segoe. That is six body faces across one property, none of them
loaded by the site.

### 2c. Colour

`style.css` `:root` declares 12 colours plus a shadow and a grid line; the
light scheme redeclares 13. Names are role-based and mostly specific
(`--ink`, `--dim`, `--faint`, `--rule`, `--moss`, `--cool`), which is the
good-site pattern, not `--primary`. Additional literals: two radial washes
(`rgba(110,128,240,.075)` violet and `rgba(79,157,132,.05)` green,
repeated five times), the hero's own `#0a1024→#05070f` radial, and node
colours inside three data-URI SVG tiles. The JS scene files carry a 12-kind
palette (`#f2d98b`, `#e8c98f`, `#cfd6f0`, `#d86a86`, `#6f7fd8`, `#5c6a8c`,
`#a98fd8` and the four root accents) that the figure builders duplicate
by hand (`build_throughlines.py` `KCOL` etc.). Distinct hues across CSS +
JS + figure scripts: about 19. The apps add `#65B2CC`, `#a83a58`,
`#4a56a8`, `#7a6a92`, `#a992c9` and bookshelf's own `#0b0d12/#e8e6f0/#8b8fa3`
greys.

What `--acc` does: links (every `a`), the current-nav pill, primary
buttons, `.tag` kickers, citation numbers, the sys-log cursor, hover rules,
and the primary series in most figures. Four of those mark "actionable",
one marks "primary data", and the kickers are pure decoration.

### 2d. Contrast

Every text pair actually rendered, dark scheme, desktop (`analysis.md`
§Contrast). Passing at 4.5:1 or better: ink 15.9, cool-on-lift 7.2, dim
6.5, acc-on-bg 6.05, moss 6.1. Under the violet wash at its densest point
dim drops to 6.07 and acc to 5.65; under both washes 5.74 / 5.34. All still
pass.

**Failing:** `--acc-ink #f2f0ff` on `--acc #8b7ff2` = **2.91:1**. That is
the current-page nav pill on all 11 pages, `.btn` on 7 pages ("Open the
atlas", "Open it", "Download code and data"), and the primary buttons in
atlas-app, skyline-app, longevity-app (white on the same violet, 3.27) and
climate-cost-app. At 13–14 px semibold the AA threshold is 4.5:1. The
light scheme's `#ffffff on #4c3fb5` = 7.82 passes, so the failure is
dark-only. The brief's premise that "the current palette passes AA" is
wrong for exactly the elements that ask to be clicked. `--acc-dim
#5a4fb0` on the background is 3.0:1, but it is only used as a hover
border, which is fine.

### 2e. Images

47 `<img>` measured (`analysis.md` §Image fidelity). Desktop: the six
home-page mosaic tiles render at **0.12–0.13** of natural width (1,425 px
figures in 180 px tiles; 432 KB for six thumbnails); home-page card
thumbnails at 0.16–0.37; library figures at 0.66–0.76; article figures at
0.54–0.95; `heat_fig2_lcoh_stacked.png` (1,050 px) is upscaled to 1.09.
Phone: every figure on the site renders at **0.16–0.33** of natural width
(350 px column), which puts matplotlib's 10–11 pt tick labels at 2–4 px.
The lightbox caps at the viewport, so it cannot rescue them on a phone.
`lq_explained.png` (2,108 px) and `energy_model_throughlines.png`
(1,870×2,261) are the worst cases: 0.17 and 0.19.

### 2f. Rhythm and dead space

Fraction of document height with no text, image, table or canvas inside
`main`/`footer`, 8 px bins: index 29%, code 30%, model 21%, skyline 22%,
atlas/library/desktop 19%, heat/storage/climate-cost 16–17%, longevity
15%. The driver on index and model is the section divider: `hr` carries
52 px margins and `h2` carries 58 px top margin plus its own bottom border,
so each `hr`+`h2` boundary is 67–74 px + 110 px = ~180 px of air with two
hairlines in it (`style.css:273`, `:295`). Article pages without `hr`
run a steady 73 px `p→h2`, which is fine.

Scrolling every page at one viewport per 90 ms: **0 blank viewports** on
any page at either size, motion on or off. There are no reveal-on-scroll
animations; the only opacity-gated content is the four sys-log lines
during their 1-second typewriter (3 low-opacity hits on index, all within
the first screen). The "reveal animations leave blank viewports"
hypothesis in the brief is not true of this site.

### 2g. Motion

`data-motion="off"` (via `prefers-reduced-motion`) sets the attribute
before paint on every page, drops idle CPU to 0–1 ms per 3 s everywhere,
and stops video sources from being requested (saving 118–389 KB per page).
`document.getAnimations()` reports 0 on every page but index (the cursor
blink). The contract works.

Motion on, idle CPU per 3 s, headless software rendering: index **2,273
ms** (three hero canvases plus the margin collage), longevity 605, atlas
498, model 484, desktop 371, library 322, storage 317, skyline 318, heat
277, climate-cost 274, code 1. So every article page burns roughly a
tenth of a core continuously for its margin scene, and the home page most
of one. Real-GPU numbers will be lower, but the ratio between pages holds.

### 2h. Structure

Per page: home has 10 `.card`, 3 `.cardgrid` (2-up, 1-up, 3-up), 7
`.tag`, a mosaic strip, a sys-log, one wide figure and three `hr`+`h2`
dividers. Library has 13 cards of identical shape (kicker, h3, figure,
two-column caption). Every other project page has exactly one card (the
"Interactive" callout) and 3–9 `h2` sections; atlas and model have none.
The nav is byte-identical in structure on all 11 pages.

### 2i. Copy mechanics

`<title>`: em dash on 10 of 11, with three suffix conventions ("— Andrew
Silvestri" ×7, "— world energy model" ×2, none on model.html) and the home
page inverted ("Andrew Silvestri — energy systems"). `h1`: sentence case
on 10 pages; model.html alone is Title Case with a colon ("The World
Energy Model: Structure, Weights, and Behaviour") and its `h2`s alone are
numbered ("1. What the model does"). Body dashes: `&mdash;` on desktop
(9), climate-cost (5), longevity (3), library/storage (1); spaced hyphen
" - " on longevity (7), climate-cost (5), skyline (2), storage (1); both
conventions on the same page in three cases. Captions: 42 of 43 end in a
full stop; kickers are sentence-case in the source and uppercased by CSS;
`&middot;` separators used consistently. Straight quotes: none. This is
tidy apart from the dash split and the title suffixes.

---

## 3. Findings, ranked

Severity: **high** = a reader is misled, blocked, or the site's identity
is undermined on its most-seen surface; **medium** = it reads as
template rather than authored, or costs bandwidth/legibility broadly;
**low** = polish.

### F1 — Primary buttons and the current-nav pill fail AA (2.91:1) — HIGH

**Observed.** `style.css:181–188` (`nav.top a.on`) and `:459–470`
(`.btn`) set `color: var(--acc-ink)` `#f2f0ff` on `background: var(--acc)`
`#8b7ff2`. Measured 2.91:1 on all 11 pages and in 4 of 5 apps
(`analysis.md` §Contrast, first four rows). Verify: open any page, pick
the violet "Home" pill in DevTools, read the two colours.

**Why it hurts.** These are the elements that ask to be acted on. 2.9:1
is below the 3:1 floor for large text, never mind 4.5:1 for 13 px. It also
contradicts the brief's stated baseline, so any Phase 2 palette that
"keeps the accent" inherits the failure.

**Cost.** Trivial. Ink-on-violet (`#070a12` on `#8b7ff2`) is 6.05:1;
keeping white text and darkening the fill to `#5a4fb0` (already `--acc-dim`)
gives 5.88:1; `#4c3fb5` (the light-scheme accent) gives 6.96:1. One
token change, plus the same in the five apps' inline CSS.

### F2 — The home page has no name, no h1 and no statement — HIGH

**Observed.** `index.html` `<main>` opens with `<div id="hero"
aria-hidden="true">`, then `<ul class="sys-log" aria-hidden="true">`, then
`<div class="card"><div class="tag">Main project</div><h3>`. There is no
`h1` on the page (`analysis.md` §Column widths, "h1 none"). The name
appears only in `<title>` and the footer. First screen at 1440×900
(`shots/index-desk-on-top.png`): nav, globe, the terminal box. First
screen at 390×844 (`shots/index-phone-on-top.png`): five nav rows (230
px), then the globe; the first words a phone reader sees below the nav are
"$ 86,622 nodes / 197,068 weighted links".

**Why it hurts.** This is the T13 template exactly: hero → stat strip →
card → thumbnail strip → three card grids → footer. Every one of the
twelve reference sites states who it is in the first viewport. Here a
reader has to infer it from a globe and a fake shell prompt. It is the
single strongest "generated" signal on the site, and it is the entry
page. Accessibility: no `h1`, and the two most prominent blocks are
`aria-hidden`.

**Cost.** Small, and within the "re-order, re-weight" rule: the words
"Andrew Silvestri — energy systems" / "energy systems modelling" already
exist in the title and footer and can become an `h1` and standfirst
without new prose. Whether the hero stays above or below that line is a
Phase 2 decision.

### F3 — Six pages exceed the 600 KB ceiling; the home page is 1.55 MB — HIGH

**Observed.** §2a. Home: 1,231 KB of images, of which 432 KB is six
mosaic tiles rendered at 180 px (ratio 0.12) and 303 KB is three card
thumbnails rendered at 309–502 px (ratio 0.16–0.37); plus 118 KB of
three.js from cdnjs for the hero. Longevity 1,294 KB (977 KB images,
five figures at 95–237 KB each). Library 981 KB (13 figures). Storage
912, desktop 921, heat 736.

**Why it hurts.** The brief lists "pages in the 300–600 KB range" as the
discipline to keep; it is already broken on most of the site. On the home
page nine of thirteen images are downloaded at 3–8× the pixels they are
shown at.

**Cost.** Medium. Thumbnail renders for the mosaic and card images (a
resize step in `sync_assets.py` or the figure builders, ~40–60 KB total
instead of 735 KB) fixes the home page without touching a figure. Library
and the article pages are honest full-size figures; their weight is the
content, and the fix there is compression (the PNGs are 8-bit-able:
`lq_allometry.png` 237 KB → likely under 100 KB as palette PNG or WebP)
plus `loading="lazy"` on everything below the first figure (only the
home-page images have it now).

### F4 — Every figure is illegible at phone width — MEDIUM–HIGH

**Observed.** §2e. At 390 px all 34 article/library figures render at
0.16–0.33 of natural; tick labels 2–4 px (`shots/library-phone-on-top.png`,
the histogram's axis text). The lightbox (`lightbox.js`) shows the image
at natural size "capped by the viewport", i.e. 350 px again.

**Why it hurts.** A phone reader gets the caption and a coloured smear.
The captions are good enough that the page still reads, which is why this
is not "high", but the figures are the site's argument.

**Cost.** High if done properly (phone-sized re-renders with larger type
from every builder, or SVG output), low if done partially (lightbox that
allows pinch-zoom / horizontal scroll at natural size, which is a
10-line change to `lightbox.js` and `.lightbox-img`). Say so in Phase 2
rather than pretending CSS can fix it.

### F5 — Type: no chosen face, no scale, three sub-12 px roles on every page — MEDIUM

**Observed.** §2b. `--serif` and `--sans` are fallback stacks
(`style.css:35–39`); the body face is whatever the OS has, and on Android
it is not on the list at all. 15 rendered sizes at half-pixel steps. `th`
at 11 px uppercase tracked (`:323–330`), carets at 9 px (`:197`), cites
at 10.5 px (`:509`). Three uppercase-tracked roles (`h2` .13em, `.tag`
.16em, `th` .1em) plus the same treatment in every app panel heading.
Figures in Segoe/DejaVu, videos in Computer Modern, one app in Georgia,
one in Segoe.

**Why it hurts.** T6 and T7 together. Palatino/Iowan-and-system-sans is
a decision (it is not Inter), but it is a decision that renders three
different ways on three platforms and never matches the figures or the
videos. The good sites all pay for one face and use it everywhere,
including in their diagrams. The all-caps kicker in three sizes is the
most template-looking element in the stylesheet.

**Cost.** Medium. A self-hosted serif + sans + mono subset in
`site/assets/fonts/` (woff2, Latin subset, ~120–200 KB total, cached
across pages) with `font-display: swap`; a 6–7 step size scale; and,
separately, regenerating figures with the same face (matplotlib can load a
TTF by path). The figure regeneration is the expensive part and can be
staged.

### F6 — Decoration that restates the page at illegible size: margin scenes, sys-log, force graph — MEDIUM

**Observed.** Motion inventory in §4. `margin-scene.js` (27 KB) on seven
pages draws the page's own numbers as bars/cards/arcs in the side margins
at 10–11 px and ~40% opacity (`shots/storage-desk-on-top.png`: "2h ·
$98.1/kW-yr" top-left, restating the table 400 px to its right;
`shots/library-desk-on-top.png`: the 13 kicker strings drifting as
motes). `syslog.js` types four numbers with a blinking block cursor under
a `$` prompt (`index.html:39–44`), then the card immediately below
repeats two of them. `force-bg.js` (7 KB + 56 KB CDN) floats an
unlabelled 200-node subgraph behind atlas/model prose. Idle CPU
270–600 ms per 3 s on every article page for this; 2,273 on index. All
are `aria-hidden`; none is reachable from a phone (margin scene disables
itself under 760 px).

**Why it hurts.** T10, T12 and T15 at once. The site's own stylesheet
comment says "nothing here competes with a figure or a map"; the margin
scenes do. A fake terminal prompt is the single most-cited "AI dashboard"
motif in the sources. The stated defence, "every number is real", is true
and beside the point: a reader cannot read them, so they are texture, and
texture made from data is still texture. What a reader loses if they are
deleted: nothing they could read; some evidence that the author enjoys
canvases. `biome-scene.js` is the exception (see §5).

**Cost.** Low to delete; the pages carry their `MARGIN_SCENE` config in
an inline script that can simply go. Medium to keep one of them and make
it legible (larger, fewer items, and only where the margin is wider than
~200 px).

### F7 — Boxes in boxes, triple titles, double rules — MEDIUM

**Observed.** Home: a `.card` (border + gradient) containing an `img`
(border) whose figure carries its own boxed title panel
(`shots/index-desk-on-full.png` at y≈1,200: the tomato chain is three
nested frames). Library: 13 × (violet kicker "MATPLOTLIB HISTOGRAM,
LOGARITHMIC ON BOTH AXES" → serif h3 "Plant capacity spans five orders of
magnitude" → in-figure title "Capacity spans five orders of magnitude ·
34,936 plants, 5.71 TW"). Atlas: `h2` "THE NINE LAYERS" directly above a
figure titled "The nine layers, and what carries between them". Section
dividers on index/model: `hr` then `h2` with `border-bottom`, two
hairlines 110 px apart (`style.css:273–276`, `:295`). `.card` itself is
hairline + `linear-gradient(180deg, var(--card), var(--bg-lift))` + inset
highlight (`:417–425`), T4 minus the drop shadow.

**Why it hurts.** T3/T4/T6. The repetition is the tell: the same
kicker-title-figure-caption module tiled thirteen times reads as a
component, not a page. The double rule is the kind of thing a person
notices and a generator does not.

**Cost.** Low. CSS for the rules and card fill; for the library, the
in-figure title or the h3 can carry the title and the other can go
(punctuation/title-mechanics exception applies); the kicker can become
the figure's method note under it in the caption sans.

### F8 — The hero blooms to white — MEDIUM

**Observed.** `shots/index-desk-on-top.png` and `-phone-on-top.png`:
Europe, the US east coast and the Indian subcontinent are solid white
blobs; `shots/atlas-app-desk-on-top.png`: all of eastern North America.
`HANDOFF.md` §8 trap 10 warns that additive blending saturates to white
"exactly where trails overlap most" and says to keep per-segment
brightness low; it is still doing it in `hero-gl.js` and `atlas-app.js`.

**Why it hurts.** T9. It is the most-looked-at pixel on the site and it
reads as a glow effect rather than as data density, which is the opposite
of the "luminous data" the stylesheet header promises. The dense regions
lose all structure.

**Cost.** Low: a brightness/alpha constant in two files, or a tone-map
(clamp the summed alpha).

### F9 — Backgrounds stack three layers behind prose — LOW–MEDIUM

**Observed.** `body::before` on every page: violet radial + green radial
+ a repeating 900×900 node/edge SVG tile (`style.css:82–95`); heat and
storage swap the tile for a page-specific curve tile (`:118–135`);
atlas/model add the force graph; seven pages add a margin canvas. Up to
three decorative layers behind the text column, all at low alpha.

**Why it hurts.** T1/T2 in its mildest form. The washes are so faint
(peak composite `#0f1323`) that they cost 0.4–0.8 of a contrast point
and are barely visible on a calibrated display; the tile is visible only
in the margins. This is not the "purple gradient hero" the sources mean.
I would not call this slop on its own; it is listed because it compounds
F6 and because the light scheme keeps the dark-tuned washes at 50%
opacity, where they look like a printing fault
(`shots/index-desk-on-light-top.png`, top-right).

**Cost.** Trivial to remove; trivial to keep one wash.

### F10 — Title and heading mechanics are inconsistent — LOW

**Observed.** §2i: three `<title>` suffix conventions plus an inverted
home title; model.html alone in Title Case with a colon and numbered
`h2`s; `&mdash;` and " - " both used as the parenthetical dash, both on
the same page on longevity, climate-cost and storage.

**Why it hurts.** T11 is contested and I do not think the em dash count
here (0–9 per page, mostly 0–1) is a tell. The inconsistency is. A
person who chose spaced hyphens on longevity did not choose em dashes on
desktop.

**Cost.** Trivial; the brief already grants the exception.

### F11 — The five apps are four-fifths of one site — LOW–MEDIUM

**Observed.** atlas, skyline and climate-cost apps: serif h1, violet
accent, same tokens, same 10.5–12.5 px panel type, same failing button.
`longevity-app.html`: body in Georgia at a 1,036 px measure and 16 px,
419 elements under 12 px. `bookshelf-app.html`: all-sans including a bold
sans h1, its own greys (`#0b0d12`, `#e8e6f0`, `#8b8fa3`), radii 6–9 px
where the site uses 2 px. Radii across apps: 0, 2, 3, 7, 8, 9, 20 px.

**Why it hurts.** Phase 3 scope; noted so the option work accounts for
it.

### F12 — Phone nav takes the first 230 px as a five-row stack — LOW

**Observed.** `shots/*-phone-on-top.png`: five 44 px rows, carets
right-aligned, the current group as a full-width violet bar. Every phone
first screen is 27% navigation.

**Why it hurts.** Not a slop tell; a cost. On a project page the reader
gets h1 and one paragraph before the fold.

**Cost.** Low (a collapsed row, or a single-line nav with the current
page named). Note also: `rebuild_nav.py`'s `NAV` list has a "Climate
research" group that the shipped pages do not have (climate-cost sits
under "Energy" in all 11 files). Running the generator as-is will change
the nav; whoever does Phase 3 should decide which is intended first.

### Not findings

- **Glassmorphism (T5):** none. No `backdrop-filter` anywhere.
- **Drop shadows (T4/T9):** `--shadow` is used only on the dropdown menu
  and the lightbox, not on cards. The checklist's "hairline border plus
  soft drop shadow" description of `.card` is wrong; it is hairline +
  gradient + 3% inset highlight.
- **Reveal animations / blank viewports:** none; 0 blank viewports in 55
  sweeps.
- **Body text contrast (T8):** passes comfortably everywhere.
- **Em dashes (T11):** not overused in prose.
- **Generic tokens (T14):** the token names are good.
- **Section gaps on article pages:** a steady 73 px; fine.

---

## 4. Motion inventory

| file | KB | pages | draws | idle cost (share of page's 3 s) | lost if deleted |
|---|---|---|---|---|---|
| `hero.js` | 10 | index | 2D canvas globe: coastlines, 7,192-node sample, flow trails; two stacked canvases | part of index's 2,273 ms (the 2D pair keep drawing until GL takes over) | The site's signature image. Keep, but it is the fallback for hero-gl. |
| `hero-gl.js` | 14 (+118 CDN) | index | three.js globe with depth and additive flow | part of 2,273 ms | Depth occlusion and glow; the glow is F8. Reader loses nothing informational vs the 2D version. |
| `hero-data.js` | 106 | index | data for both | 0 | Nothing (data). |
| `margin-scene.js` | 27 | index, library, heat, storage, climate-cost, skyline, desktop | bars/cards/flow/arcs of the page's own numbers in the side margins, 10–11 px, ~40% alpha, scroll-driven presence + idle wobble | 270–370 ms per page; disabled under 760 px | Nothing a reader can read. F6. |
| `biome-scene.js` | 29 | longevity | canopy-to-ocean-floor descent tied to scroll depth; real species from the page with their real LQ labels | 605 ms | The one scene that is page-specific, legible in places, and makes an argument (depth ↔ longevity). Keep, fix the label size. |
| `force-bg.js` (+`force-graph-data.js`) | 7 + 7 (+56 CDN) | atlas, model | force-directed 200-node subgraph behind the prose, masked out of the text column, 50% alpha | ~490 ms | Nothing legible; no labels. Also the site's second CDN runtime dependency. F6. |
| `syslog.js` | 1 | index | typewriter reveal of four `<li>` numbers, blinking cursor | ~0 after 1 s (cursor is CSS) | Nothing; the numbers are repeated in the card below. The `$` prompt is the tell. F6. |
| `bgloop.js` | 1 | heat, storage, climate-cost, longevity, skyline, desktop | attaches `data-src` to `<video>` only when motion is on | 0 | Nothing; this is infrastructure and it is good. |
| `motion.js` | 1 | all | the `data-motion` contract and footer toggle | 0 | Keep. |
| `lightbox.js` | 3 | all | figure overlay | 0 | Keep; extend for F4. |
| `atlas-app.js` | 48 | atlas-app | the model | — | The product. |
| `atlas-data.js` | 9,836 | atlas-app | the payload | — | The product. |

The five `.mp4` explainers (184–389 KB each) are content, not decoration:
each animates the page's key figure and is gated by `bgloop.js`. Their
posters are the still. They are in Computer Modern (F5).

---

## 5. What is good and must survive

The premise of the brief is partly wrong, and it is wrong about the part
of the site that carries the work.

- **The article pages are a paper, not a landing page.** model.html,
  atlas.html, heat, storage, climate-cost and longevity are serif prose at
  a 72ch measure with small-caps section heads, numeric tables with
  tabular figures and right-aligned `.n` cells, numbered citations that
  jump to a references list with a source line and a "what it supplied"
  line, and captions that state the finding rather than the axis names.
  `shots/model-desk-on-full.png` and `shots/heat-desk-on-full.png` read
  like a well-set technical report. None of the 1,590-page audit's
  patterns applies to them except the dark ground. Flattening this into
  "a clean light blog" would be the failure mode the brief warns about.
- **The figures are the site.** 47 images, every one generated from the
  live payload by a builder that audits its own layout; the in-figure
  titles state a claim ("Capacity spans five orders of magnitude · 34,936
  plants, 5.71 TW"). Their palette (violet primary, green secondary, blue
  tertiary, rose for events) is consistent across 30-odd figures and the
  apps. This is the "decoration that is the content" property the good
  sites have. Whatever Phase 2 does to the page chrome must not change
  the figure vocabulary.
- **The hero is real.** A globe drawn from 7,192 recorded coordinates with
  flow along real links is exactly what a personal site for this work
  should open with. Fix the bloom, do not replace it with type.
- **The atlas app** is a serious instrument and its chrome (top strip,
  right panel, nine-tab layer bar with a sub-line each) is restrained and
  specific. It is the strongest evidence on the site that a person with
  opinions built this.
- **The motion contract** is better than most professional sites: one
  attribute, set before paint, honoured by every script, with a visible
  toggle, and video sources not even requested when off. Keep it exactly.
- **The token names** (`--ink`, `--dim`, `--faint`, `--rule`, `--moss`,
  `--cool`) and the three-track grid with `--text: min(72ch, 100%)` are
  the named-and-stated decisions the good sites have. The 72ch measure
  and the 17.5 px body are right.
- **The green.** `--moss` doing gas/wild/second-series against violet's
  electric/captive/first-series is a real two-colour semantic system, not
  a brand palette. It should be carried into any new accent.
- **biome-scene.js** is what the other scenes should have been: page-
  specific, tied to the argument, labelled with the page's own values.
- **The copy mechanics** are mostly disciplined: sentence-case headings,
  captions as full sentences, no straight quotes, `&middot;` separators,
  no development history in the prose.

Where the premise is right: the home page, the margin decorations, the
sys-log, the button contrast, the unloaded typeface, and the page weight.
Where it is wrong: the article pages and the figures are not slop, the
dark violet palette is a defensible decision that is executed
consistently, and the site does not have the glass, glow-shadow, reveal-
animation or gradient-hero tells at all. On the 1,590-page audit's own
scale (4+ patterns = heavy) the article pages score 1 (dark) and the home
page scores about 5 (dark, violet, card grids, kicker badges, stat strip
plus terminal). The problem is concentrated, which is good news for
Phase 2.

---

## 6. Cross-check against the prior audits (read after §1–5 were written)

Read in the required order: `DESIGN_AUDIT_EXTERNAL_2026-08-30.md`, then
`SITE_REVAMP_2026-08-30.md` (ten passes), then the appendix checklist.

### What they caught that I missed

- **Hero does not survive a window resize** (external §11). I measured two
  fixed viewports and never resized a live page. Method gap: add a
  resize-and-rotate step per page.
- **Tablet widths.** The external audit's note on dropdown carets sitting
  ~700 px from their label at tablet width is something my two-viewport
  sweep cannot see. Method gap: add 768 and 1024.
- **The longevity video's numbers disagree with the table** (revamp, passes
  5–6, still open). Content, not presentation, and out of my remit, but it
  sits on a page I audited and I did not notice it. The caption repeats
  the video's "45×" while the margin scene beside it says 47.48×.
- **`sync_assets.py` reports six orphaned assets (~1 MB)** shipped but
  unreferenced. They do not load on any page, so my weight numbers are
  unaffected, but a publish carries them.
- **Almost everything else in the external audit was already implemented**
  in the revamp (force-graph mask, library figure width, lightbox, margin
  clamp, storage increment chart, panels B/D/E, layer diagram, replay,
  `-999`, WebP, cache-bust glob, lazy loading on the home page). I confirm
  the outcomes I could measure: library figures render at 1,082 px, the
  force graph is masked out of the text column, the margin scenes clear
  the nav, the two card images on desktop are WebP. None of that needs
  redoing.

### What I caught that they missed

- **The AA failure on filled violet** (F1). The external audit states "No
  AA failures found in the core palette; the failures here are size, not
  contrast." It measured `--dim` and `--acc` on the background and did
  not measure text on the accent. 2.91:1 on every page's nav pill and
  every primary button.
- **No `h1` and no name on the home page** (F2). Neither document mentions
  it. The revamp records "No about page. Decided against"; F2 is not an
  about page, it is the page's first heading, and the words already exist
  in the `<title>` and footer.
- **Page weight.** The external audit lists "pages in the 300–600 KB range"
  under discipline to keep; the brief repeats it. It is not true now, and
  the revamp's own additions are why: figures on the three home cards
  (+296 KB), the home mosaic, `lq_ranked` and two more longevity figures,
  six motion videos with 80–142 KB posters each. Six of eleven pages are
  over; the home page is at 1,555 KB.
- **The typeface situation across platforms and media** (F5). The revamp's
  "Typography now matches the site" pass set matplotlib to Segoe UI so the
  figure lettering matches the page's *UI sans* — but the captions under
  every figure are `p.small`, which is the serif. And a figure rendered
  on this Windows machine in Segoe is shipped as a PNG to a Mac reader
  whose page chrome is SF, so the match holds on exactly one platform.
  The videos are in Computer Modern on every platform. Neither document
  looked at the body serif resolving to three faces.
- **Hero bloom** (F8), despite `HANDOFF.md` §8 trap 10 describing it.
- **Double rules, triple titles, in-figure title duplicating the `h2`** (F7).
- **Idle CPU of the scenes** (§2g) and **two CDN runtime dependencies for
  decoration** (three.js for the hero glow, force-graph for a background).
- **`rebuild_nav.py` is out of step with the shipped nav.** The revamp
  moved "Climate cost calculator" under Energy "across all 11 pages" by
  editing the pages; `NAV` in `rebuild_nav.py` still has a separate
  "Climate research" group. `HANDOFF.md` §3 says never hand-edit the nav
  and always run the generator. Whoever next runs it reverts the fix.
- **The light scheme keeps the dark washes at 50%** (F9).
- **419 sub-12 px elements in `longevity-app.html`**, 54 in skyline-app,
  31 in climate-cost-app (F11). The external audit noted ~10 px labels in
  bookshelf-app only.
- **Phone figure legibility** (F4). Both documents fixed the desktop
  rendering width and stopped; neither measured 390 px, where every figure
  is at 0.16–0.33 of natural and the lightbox cannot help.

### Where I think they are wrong

- **External §3 (blank viewports on scroll)** was withdrawn in the revamp
  as an automation artefact. My 55 scripted sweeps at one viewport per 90
  ms found 0 blank viewports and no reveal system, which independently
  confirms the withdrawal.
- **External §12, "no AA failures in the core palette"** — wrong, above.
- **Revamp, "section spacing … about 126 px a boundary and was left
  alone."** Measured on rendered boxes it is 177–184 px per `hr`+`h2`
  boundary on index and model (the `hr` carries 52 px on each side plus
  the `h2`'s 58 px). Not a large disagreement, but the number in the log
  is the CSS arithmetic, not the rendered gap, and it is the two-hairline
  construction rather than the height that reads as template.
- **Revamp, passes 5–10: six passes growing the margin scenes** (more
  items, bigger icons, longer fades, a home-page collage, heat 3→11 items,
  storage 3→10, skyline 15→27). Every pass verified "two to four live at
  any depth" and "zero collisions"; no pass asked whether the labels are
  readable. They are 10–11 px at ~40% alpha in a 240 px margin. The
  scenes got better as scenes and stayed illegible as information. I
  disagree with the direction, not the craft: F6 stands, with the
  explicit option of keeping `biome-scene.js` (the one that makes an
  argument) and making its labels 13 px+.
- **Revamp, "the heat.html figure suite … serif annotations inside the
  chart matching the page's body face"** (external "leave alone" list).
  The static heat figures are sans (Segoe); only the video and its poster
  are serif, and that serif is Computer Modern, not the page's Palatino /
  Iowan. The suite is good; the stated reason is not accurate.
- **The external audit's premise that the type system "was never the
  problem."** It is not *the* problem, but an unloaded stack that renders
  as three different faces is a real one on a site whose argument rests
  on figures that the page face is supposed to caption.

### What my method missed and what I would change

Resize and orientation; 768/1024 widths; a real-GPU CPU run (headless
software rendering inflates every canvas number — the *ratios* between
pages and between on/off are trustworthy, the absolute ms are not); the
light scheme on any page but the home page; keyboard focus states; and I
inferred Mac/Android face resolution from the stacks rather than
rendering there. Everything else in §2 is measured.

---

## 7. The appendix checklist, item by item

Seen before measuring (see the disclosure at the top). For each: found
independently, and would the method have found it without the prompt.

1. **`--acc #8b7ff2` on `--bg #070a12` plus two radial washes on
   `body::before`.** Found (§2c, §2d, F9) and the stylesheet read would
   have surfaced it with or without the list. My verdict differs from
   the list's implication: the accent on the background is 6.05:1 and
   does mostly semantic work; the washes are near-invisible (peak
   composite `#0f1323`, costing 0.4–0.8 of a contrast point). The violet
   problem the list does not name is the *filled* violet (F1), which
   fails AA. Fixing the checklist's item without fixing F1 would leave the
   real defect.
2. **`.cardgrid` of three cards with `.tag` kickers, three times down the
   home page.** Found (F7, §2h), by counting. Correction: the three grids
   are 2-up, 1-up and 3-up; the "three × three" shape is not what ships.
   The 1-up grid (a single full-width card containing a boxed figure) is
   the odder one.
3. **`.card` = hairline border plus soft drop shadow (`--shadow`).** Found
   the card rule (F7); the description is wrong. `.card` has no drop
   shadow — `--shadow` is used only on the dropdown menu and the lightbox.
   The card is hairline + `linear-gradient(card → bg-lift)` + a 3% inset
   highlight, which is the same family of tell (T4) with a different
   member.
4. **Em dashes throughout, including in every `<title>`.** Found in the
   titles (10 of 11, F10) — a static grep would have found it anyway. Not
   found "throughout": body prose has 0–9 per page, most pages 0–1, and the
   spaced hyphen is the more common parenthetical dash. The finding is
   inconsistency (three title conventions; both dashes on the same page),
   not overuse. I do not think the em dash count is a tell here.
5. **`margin-scene.js`, `syslog.js`, `hero-gl.js`, `bgloop.js` as motion
   that decorates rather than informs.** Found for the first three (F6,
   F8, §4) and the CPU measurement would have flagged them without the
   list. Disagree on the fourth: `bgloop.js` is 1 KB of gating that
   attaches a `src` to a content video only when motion is on; deleting
   it removes the site's best motion behaviour, not a decoration. Also a
   distinction the list does not draw: `hero-gl.js` draws the model (keep,
   fix the bloom); `margin-scene.js` restates the page (drop or make
   legible); `syslog.js` is a terminal costume (drop).
6. **`--sans` and `--serif` are generic fallback stacks rather than chosen
   faces.** Found (F5, §2b) and extended: the serif stack has no member on
   Android at all, the figures and videos are in two further faces, and
   two apps use two more. A stylesheet read would have found the stacks;
   the platform-font query is what turned it into a measurement.

Two things the checklist does not have that I would put on it: the
2.91:1 buttons, and the home page opening with a hidden globe and a `$`
prompt instead of a name.

---

## 8. Where this leaves Phase 2

Not a plan — the brief says stop here — but the audit implies which
directions would be *different* rather than three intensities of one:

- The findings cluster in three places, not one: **identity and
  structure of the home page** (F2, F7, F12), **type and its cross-media
  consistency** (F5, F10, F4), and **decoration and weight** (F6, F8, F9,
  F3). F1 is a one-token fix that every option must include.
- The article pages, the figure vocabulary, the atlas app, the motion
  contract, the token names, the 72ch measure and the moss/violet
  semantic pair are the parts to build on, not replace.
- Two of the findings (F3 thumbnails, F4 phone figures) are asset-pipeline
  work, not stylesheet work, and the options should say what they leave to
  a later figure-regeneration pass rather than pretend CSS solves them.

Stopping here, as instructed.
