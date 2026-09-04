# Audit — the longevity quotient app

Date 2026-09-04. Brief: `prompts/AUDIT_longevity.md`. Read-only; nothing in
`site/` was changed. Evidence in `_audit-longevity/` (gitignored, added to
`.gitignore` this session): `drive.js` and `err.js` (Playwright drivers),
`results.json`, `segs.json`, `rows.json` (the rehydrated payload), and
`shot-*.png`.

**Disclosure on the seal.** The brief's appendix checklist is at the bottom of
the same file, inside a `<details>` block. My first `cat` of the brief printed
it, so I had seen the six bullets before doing any work. I did not open
`DESLOP_AUDIT_2026-09-04.md` or `DESIGN_AUDIT_EXTERNAL_2026-08-30.md` until
§5. Where a finding below coincides with a checklist bullet I say so in §5 and
say whether the method would have found it unprompted.

**Concurrent edits.** While this audit ran, another session modified `site/longevity.html` (motion bootstrap, `main.notes`, marginalia `grid-row`, footer) and 13 other files under `site/`, none of them `longevity-app.html`. Every observation here is against the committed tree at `37401cc`; the prose quoted from `longevity.html` is unchanged by that edit.

**One premise in the brief is stale.** §2 asks whether any view survives a copy
of the address bar and says a "no" would have a large blast radius. The shipped
app has full hash state (`site/longevity-app.html:341-395`), `longevity.html`
already links into it, and the round trip works (§2.4 below). The `-999` common
name is also already normalised at the app boundary (`:327-331`). Both fixes
live only in the shipped file, not in the source that generates it — that is
finding F5.

---

## 0. Summary

The app works. Every control does what its label says, nothing throws on load,
first render is 0.25 s on a normal connection, and the code is unusually well
reasoned. The problems are not bugs in the interface; they are that the
interface is more confident than its data.

The three findings that matter most:

1. **The green "wild" bar is mostly not wild.** 4,015 of the 6,387 wild maxima
   come from sources that carry no wild/captive field at all, and the AnAge
   loader routes "origin unknown" to wild too. The app draws them as measured
   wild maxima and tells the reader a missing bar means "no dependable figure
   exists". `outputs/provenance.csv` would let it say otherwise; the app does
   not ship or use it.
2. **The bottom of every ranking is data-entry artefact graded B.** Twenty-eight
   amniotes carry maximum lifespans of one to three months at body masses up to
   5 kg (Indian hare: 1 month, 2.2 kg). They are grade B by construction, so
   the grade-C filter the page is proud of does not touch them, and they are
   the whole lower half of the published `lq_ranked.png`.
3. **`longevity.html` describes a regression the code does not run.** The page
   says weighted OLS with grade weights and Kish effective n. `build_lq.py`
   runs `FIT_STRATEGY = "filter"`: every weight is 1.0 and n is a raw count.
   The app's own text is right; the page's is wrong.

After those: numbers disagree between page, margin, video caption, explainer
figure and app for the same animals (F4); the shipped app has drifted from its
build source (F5); bars are drawn on a log scale from a floating origin with
no parity line in the default view (F6); the motion contract is not honoured
at all (F7); and on a phone the sticky control panel occupies 83% of the
viewport, leaving four rows visible (F8).

---

## 1. Method

- Served `site/` with `python -m http.server 8801`. Drove with Playwright
  1.62.1 / Chromium from `_audit-longevity/`, at 1440×900 and 390×844, light
  and dark colour schemes, with `prefers-reduced-motion` both ways and with
  `data-motion="off"` injected before first paint.
- Rehydrated the embedded payload in Python and censused every column;
  cross-checked against `outputs/lq_table.csv`, `outputs/group_summary.csv`,
  `outputs/summary.json`, `outputs/provenance.csv`, and the prose on
  `longevity.html`.
- Read `build_lq.py`, `update_page.py`, `data/ingest.py`, `data/load_anage.py`,
  `data/merge_anage.py`, `DATA_SOURCES.md`, `README.md`, and diffed the shipped
  app against `longevity-quotient/longevity.html` and `template.html`.
- Ran the three shipped tests. `test_merge.py` 21/21 pass. `test_fit_strategy.py`
  runs and prints its simulation table but asserts nothing. `test_perf.js`
  cannot run: `jsdom` is not installed in `longevity-quotient/node_modules`
  (MODULE_NOT_FOUND), and it targets the build output rather than the shipped
  file.

---

## 2. Does it work

### 2.1 Controls

Every segment button in both views was clicked in turn and the rendered state
recorded (`segs.json`, `results.json → groups`). All 13 segment groups, both
selects, the search box, the clear-filter button, the detail panel and its
close button do what their labels say. No control is dead. Per-click render
times at 400 rows, desktop: quotient 108 ms, lifespan 185 ms, body mass 498 ms,
name 421 ms; a second pass gave 242–682 ms for the same four. "All" rows
(6,398 DOM rows, chart 191,950 px tall) took 2.3 s to render and 4.7 s to
re-sort by name.

Observed behaviours that are not what the label says or are worth knowing:

- **Filter to → a taxon that does not exist** (via hash `fVal=Nope`, or a
  renamed taxon in a stale link): `fillVals()` silently selects the first
  option alphabetically. `#fRank=or&fVal=Nope` lands on "showing
  **Acanthuriformes** (order) · 0 species", a crumb naming a taxon the reader
  never asked for. (`:757-760`)
- **Sort by Name** sorts on the lowercased *common* name (`:509`), and rows
  with no common name sort by their binomial. The first five under "Name" are
  therefore `Ammodramus sandwichensis, Anthochaera rufogularis, Cacatua
  roseicapilla, Diomedea albatrus, Meliphaga penicillata` — all nameless
  binomials sorted as empty strings, before "Aardvark". Screen: `segs.json`.
- **Rows shown = 400** truncates at the end of the sort and the count line says
  so. But the *scale* is built from the visible 400 only (`:529-532`), so the
  axis changes as the cap changes and the parity line disappears whenever the
  visible subset is all above 1 (see F6).
- **Search** is substring on lowercased common and scientific name, so `b`
  matches 2,788 species and `bat` matches "Sabatia" fish as well as bats. It
  does not fold diacritics ("Ereğli minnow" is unreachable by "eregli"). Minor.
- **Include colonies** puts the four colonies at the top; correct and labelled.
- **Group → click** drops into the species view filtered to that group,
  presses the View button, fills the select and preserves the wanted value.
  Correct.
- One uncaught `TypeError: Cannot read properties of null (reading
  'dataset')` was captured by `pageerror` once during the scripted run. A
  second pass replaying every navigation and hash in that run (`err.js`)
  reproduced nothing. I could not attribute it to a line in the app; reported,
  not counted.

### 2.2 Sentinels

- **`-999` in the interface: no longer.** Default view, row 6 is now
  *Proteus anguinus* (Olm); *Terrapene mexicana* renders as a bare binomial.
  The 127 `-999` common names are normalised to `""` at rehydration
  (`:327-331`) and the search index never sees them; searching `-999` returns
  0 species. Verified at both viewports.
- **`-999` in the data: still there.** 127 rows carry it in the embedded
  payload (`cols.n`), in `outputs/lq_table.csv` (127 lines), in
  `data/animals_merged.csv` (127), and in the "Download code and data" zip
  (`site/downloads/longevity-code.zip` → `outputs/lq_table.csv`,
  `data/animals_merged.csv`). `ingest.py:87-101` (`num()`) strips `-999` for
  numbers only; `ingest.py:516` passes `common_name or scientific_name`, and
  the string `"-999"` is truthy. The fix was applied at the last possible
  moment instead of the first.
- **Other sentinels reaching the UI.** No `NA`, `null`, empty or negative
  numeric values reach any rendered field (all 19 columns censused). Two
  common names contain literal HTML from AnAge — `Franquet's Epauletted
  Fruit<b> </b>Bat`, `Sundaic Arboreal<b> </b>Niviventer` — which `putHTML`
  renders as markup (the tag is invisible; the `<b>` is real). Twelve common
  names carry Reptile-Database subspecies junk: `abyssus: Grand Canyon
  Rattlesnake`, `Sertao Lancehead [iglesiasi]`, `Beauty Snake (friesei: Taiwan
  Beauty Snake; schmackeri: …)`. 261 rows have common name == scientific name
  (the loader's placeholder), handled by `label2()`.
- **Hash injection.** `#q=<img src=x onerror=…>` is set into the search
  input's `value` and never into markup. Not exploitable. `fVal` is only ever
  compared, never rendered raw. Crumb renders `S.fVal` via `innerHTML`
  (`:597`) but only after `fillVals()` has replaced it with a real option
  value, so it is safe by accident of ordering.

### 2.3 The default view

First-time visitor at 1440×900 (`shot-default-desktop.png`): title, a
four-line paragraph, a 228 px control panel with 13 groups and 40 buttons,
a count line, a legend, and then ~11 rows of the 400 before the fold. The
first row is 556 px down the page.

The default sort (quotient, own group, average lifespan, A–B, colonies out) is
the right one, and its top is genuinely the most interesting screen the data
has: ocean quahog 47.48×, cold-seep tubeworm 23.41×, black garden ant queen
21.78×, freshwater pearl mussel 15.78×, rougheye rockfish 12.90×, olm 12.90×,
Brandt's bat 12.75×. But:

- The axis shows a single tick, **"10.0"**, and no "1 · as predicted" line —
  because every value in the top 400 is above 1 and the scale is fit to the
  visible subset (`makeScale`, `:529-546`). The legend text says "1 = as
  predicted" beside a chart on which 1 does not appear.
- Bars are log-scaled from a floor of 0.85 × the smallest visible value
  (`:534`), so *Myotis occultus* at 10.32× draws at ~60% of the quahog's
  length while their ratio is 4.6, and a species at the floor would draw at
  zero length. Bar length is not a quantity on this chart; only the numeric
  label is. (F6.)
- Rows 8, 12 and 13 of the default top (Cinnamon myotis 10.75×, Arizona
  myotis 10.32×, *Terrapene mexicana* 8.45× at 138 yr) are Amniote grade-B
  records with no corroborating source (`provenance.csv`). The reader cannot
  tell them from the A-grade radiocarbon-dated animals beside them.
- Flip **Order** to Low first and the screen is the artefact list of F2:
  Indian hare 0.01×, Hose's palm civet 0.01×, pocket gopher 0.01×, marsupial
  mole 0.02×, then six shrews and mice all at 0.02×.

### 2.4 URL state

Present and correct in the shipped file. Every state key that differs from
its default is written to `location.hash` with `replaceState` on each render
(`:361-364`); `decodeHash()` validates enums and numbers and degrades
malformed input to defaults (`:369-383`); `hashchange` re-restores (`:836`).
Verified round trips:

| Hash | Result |
|---|---|
| `#view=gr&rank=or&fRank=or&fVal=Chiroptera&grade=all` (the page's link) | 1 group row, "Chiroptera 267 **2.66×**" — page says 2.68 (F4) |
| `…&met=mx` | "Chiroptera 267 2.68×" — matches the page |
| `#fRank=or&fVal=Chiroptera&sort=life` | 261 species, Brandt's bat 41.0 yr first |
| `#q=quahog` | 1 species, search box filled |
| `#sort=bogus&cap=7&fRank=or&fVal=Nope` | sort/cap ignored; fVal falls to Acanthuriformes, 0 species (§2.1) |
| `#view=gr&rank=fa&fRank=fa&fVal=Sebastidae` (no `grade=all`) | "Sebastidae **3** 6.51×" vs the page's 2.76 over 16 |
| Back button after three control changes | stays on the page, state kept (`replaceState`) |

The landing for the page's group links is one bar with no neighbours
(`shot-link-chiroptera.png`): the reader arrives at "Chiroptera 2.66×" and
has nothing to compare it against until they clear the filter.

### 2.5 Empty and edge states

- **Search matching nothing**: "0 species of 7873", chart collapses to 10 px,
  the axis still draws "1.00" and "1 · as predicted" (the scale falls back to
  `[1]`). No message beyond the count line. Acceptable.
- **Filter matching nothing under A–B**: Carangiformes (30 species, all
  FishBase C), Porifera, Hexactinellida → "0 species of 7873" with no hint
  that switching grade or colonies would populate it. The crumb still names
  the taxon. The page's own prose cites Carangiformes ("the jacks at 0.43"),
  and following that thought into the app at default settings yields nothing.
- **Missing mass or lifespan**: none reach the app; `ingest.py` drops rows
  without both (710 dropped for no mass, per the page). Every row has `m`,
  `a`, `mx`, `pg`. 207 amphibians have `pc = null`; the ranking silently uses
  `pg` (`:401`) while the detail panel prints "predicted, own group —" and
  "quotient, own group —" for the same animal whose bar reads 12.90×
  (`results.json → detail_olm`). Two numbers for the same thing on the same
  screen, one of them a dash.
- **Extremes of the mass range**: bdelloid rotifer at 0.5 µg → "0.5 µg"; blue
  whale 150 t → "150 t". `fmtMass` handles both. `longevity.html` prints the
  same range as "from 0 g to 150,000,000 g" (`update_page.py:225`, `{lo:,.0f}`).
- **Group view, genus, min 1**: 2,346 rows, 70,390 px tall, renders in ~0.6 s.
  Fine.

---

## 3. Is it honest

### F1. The wild bar — HIGH

**Observed.** `ingest.py` builds one record per species with `wild_yr` and
`captive_yr`. AnAge routes by its "Specimen origin" field, and when that is
unknown, *to wild*: `ingest.py:169-172`, `if wild is None and cap is None:
wild = life`. Every other bulk source has a single "maximum longevity" with no
origin at all, and all of them are written into the wild column: Amniote
(`:204-206`, `mass, life, None`), PanTHERIA (`:224`), AmphiBIO (`:246`),
FishBase (`:345-346`). The census of the shipped payload by
`provenance.csv → taken_from`:

| source of the row | rows with a "wild" figure | rows with a "captive" figure |
|---|---|---|
| seed (hand-checked) | 412 | 314 |
| AnAge | 1,960 | 1,481 |
| Amniote | 2,649 | 0 |
| FishBase | 1,250 | 0 |
| AmphiBIO | 116 | 0 |

4,015 of 6,387 "wild maxima" — 63% — come from sources that never said the
animal was wild. An unknown share of the 1,960 AnAge ones are "origin
unknown" relabelled wild. `load_anage.py:153-155` (the older loader, not the
one in use) makes the opposite call — "specimen origin not stated, assumed
captive" — and writes a note saying so. `ingest.py` writes no note.

**What the app tells the reader.** The detail panel labels the figure "wild
maximum" (`:686`); the legend says "wild"; the prose under the chart says "A
missing wild or captive bar means no dependable figure exists, usually because
the species has never been held, or never been followed" (`:280-283`). For an
Amniote bird with one bar, that sentence is false: the source simply did not
say. The page's "6,387 have a wild maximum, 1,795 a captive maximum, and 309
have both" is a count of column labels, not of observations.

**Why it hurts.** The app's own §"What the wild and captive numbers mean"
argues carefully about the wild/captive asymmetry. That argument is only about
the 309 paired rows plus whatever AnAge actually labelled; the reader is
invited to read it into every green bar. Switching **Lifespan used** to "Wild"
does not select wild records; it selects the column most bulk sources were
dumped into.

**Provenance is available and unused.** `outputs/provenance.csv` has
`taken_from`, `grade`, `corroborating_sources`, `mass_from` for every row. None
of it is in the payload; the detail panel shows grade only. The one field that
would let a reader weigh a bar is the one left out.

**Cost to fix.** Data side: one column in `ingest.py` recording origin
(`wild | captive | unstated`) per row, ~20 lines. App side: a third bar state
or label, ~30 lines, plus ~16 KB of payload for `taken_from` if shipped
dictionary-encoded.

### F2. The bottom of the ranking is Amniote data-entry artefact graded B — HIGH

**Observed.** 28 A/B-grade mammals, birds and reptiles heavier than 5 g carry a
maximum lifespan of ≤ 3 months (`rows.json` census; 13 at 0.25 yr, 11 at
0.083 yr, 3 at 0.167 yr, 1 at 0.2 yr). All 28 come from Amniote. Examples:

| species | max lifespan | mass | grade | LQ (own group) |
|---|---|---|---|---|
| *Lepus nigricollis* (Indian hare) | 0.083 yr | 2,197 g | B | 0.007 |
| *Diplogale hosei* (Hose's palm civet) | 0.167 yr | 5,452 g | B | 0.012 |
| *Geomys pinetis* (pocket gopher) | 0.083 yr | 196 g | B | 0.012 |
| *Notoryctes caurinus* (marsupial mole) | 0.083 yr | 34 g | B | 0.018 |

A one-month maximum for a 2 kg hare is not a sampling artefact of the kind the
page describes; it is a unit or field error in the source (Amniote reports
some longevity in months elsewhere). `ingest.py:206` grades every Amniote row
`"B"` unconditionally, so the C-filter never sees them, and they enter the
regressions at full weight (F3 makes that literal).

**Where they show.** The default view under Low first (§2.3); every "Low
first" in every taxon filter they belong to; and `site/assets/lq_ranked.png`,
where the twelve "who does not" species are exactly these twelve. The page
prose under that figure calls them "the twelve species furthest below their
predicted lifespan". The page also says the lowest quotients "belong to the
silkmoth, a wasp worker, Labord's chameleon, and the squid and octopus at
around one-twentieth" — which is true of the seed table and false of the
shipped model, whose bottom is 0.007.

**Why it hurts.** The page's whole case for hiding grade C is that thin
records "pile up at the bottom of the ranking looking like a discovery". The
shipped ranking does exactly that with grade-B records, under the reader's
default settings, and publishes it as a figure.

**Cost to fix.** A plausibility gate in `ingest.py` (e.g. flag amniotes with
max lifespan < 0.5 yr for review or demote to C), ~10 lines, plus a rebuild
of the figures. Deciding what the right values are is data work, not app work
(§8).

### F3. `longevity.html` describes a weighted regression; the code runs an unweighted one — HIGH

**Observed.** `build_lq.py:96-99`: `FIT_STRATEGY = "filter"`, and
`weight_of()` (`:236-239`) returns `1.0` unless the strategy is `"weighted"`.
`ols_loglog` then computes Kish n_eff on all-ones weights, which is the raw
count: global n = 6,398 = 149 A + 6,249 B non-colonial, exactly. The page's
"The arithmetic, written out" section (`longevity.html:337-347`,
`update_page.py:214-238`) says:

> One **weighted** ordinary least squares regression per baseline … Weights
> come from the data grade, so a record verified against a named individual
> counts for five times what a compilation estimate counts for. … The sample
> size quoted for each fit is Kish's effective sample size … quoting the raw
> number would overstate the fit's authority by about a factor of two.

None of that is what ran. `summary.json` ships `quality_weights` and the app
embeds them in `FITS` (`:336`) but nothing reads them. The app's own fit
section (`:213-232`) says "An ordinary least squares regression" and describes
the C exclusion — correct. The build's own comment block (`build_lq.py:66-95`)
explains, with a simulation table, why filtering beat weighting; the page was
never updated to match the decision.

**Why it hurts.** It is the one paragraph on the page that claims to tell the
reader exactly what was computed, and it is wrong in both its specifics.

**Cost.** Prose only: rewrite one paragraph in `update_page.py` and re-apply.
Trivial. Deciding whether to also drop `quality_weights` from the shipped
`FITS` is a one-line choice.

### F4. The same animal has three numbers — MEDIUM-HIGH

The app defaults to **average** of wild and captive; `lq_table.csv`,
`group_summary.csv`, the figures and the page prose use **maximum**; and
some prose was written against an older table. Specific disagreements,
all verified against `rows.json` and the outputs:

| claim | where | value there | app at default | app with `met=mx` | note |
|---|---|---|---|---|---|
| black garden ant queen | margin | 28.72× | 21.78× | 28.72× | prose two paragraphs later: "twenty-seven" |
| ocean quahog | prose "forty-five times", video caption "45×" | — | 47.48× | 47.48× | margin says 47.48×; 45 is stale |
| leafcutter ant queen | prose "ten" | — | 9.61× | 10.98× | |
| Chiroptera | prose "2.68 across 267" + link | 2.6768 | link shows **2.66×** | 2.68× | link omits `met=mx` |
| Monotremata | prose 2.73 | 2.7342 | 2.67× | 2.73× | |
| Primates | prose 2.12 | 2.1198 | 2.10× | 2.12× | |
| Vespertilionidae | prose 3.43 | 3.4269 | 3.42× | 3.43× | |
| Sebastidae | prose "2.76" over 16 | 2.7617 | without `grade=all`: **6.51×** over 3 | | 13 of 16 are FishBase C |
| Carangiformes, Beloniformes | prose 0.43, 0.39 | | at default grade: **0 species** / 2 species | | wholly or mostly C |
| amphibian rejection | prose "r² of 0.12 across twenty-four species" | `summary.json`: r2 = 0.043, n_eff = 83 | app fit table: "r2=0.043, n_eff=83" | | prose is from an earlier run |
| birds vs mammals | page "about 1.8 times"; app "about twice" | 22.3 / 9.7 yr at 1 kg = **2.3×** | | | neither number matches the shipped fits |
| mass range | page "from 0 g to 150,000,000 g" | 5e-7 g | app "a microgram" (rotifer is half that) | | formatting bug in `update_page.py:225` |
| explainer figure (`lq_explained.png`) | Human LQ 4.03, shark 8.12, elephant 1.19 | these are **global-fit** maximum LQs | own-group: human 5.07 (max) / 3.98 (avg), shark 6.34, elephant 1.31/1.19 | | figure uses the baseline the page calls unfair |
| "Of the 112 orders holding four or more species" | prose + figure caption "All 112 orders" | `group_summary.csv`: 114; 2 are Anura/Urodela with no class LQ | app shows Anura and Urodela **with** a quotient (global fallback), Urodela ranked 2nd at 2.94× | | |
| fit table column "Species in fit" | page and app | 6,398 etc. | | | is a raw count; the page says it is Kish n_eff (F3) |
| grade census | app `FITS.grade_census` C 1,471 B 6,249 A 149 | payload: C 1,474 B 6,250 A 149 | | | difference is the 4 colonies; explained nowhere on screen |

**Why it hurts.** A reader who follows the page's Chiroptera link to check
"2.68" sees 2.66, and has no way to know that the page counted maxima and the
app is averaging. The margin scene says every figure "is that species' own
figure from the table above" — it is the maximum figure, which the app does
not show by default.

**Cost.** Either add `met=mx` to the eleven links and the margin note, or
change the app default. Then re-run `update_page.py` for the mechanical
numbers, and hand-fix the five prose numbers it does not own (45, 27, 1.8,
0.12/twenty-four, 112). An hour.

### F5. The shipped app has drifted from its source — MEDIUM

`site/longevity-app.html` differs from `longevity-quotient/longevity.html`
(the file `build_lq.py` writes) by 127 lines of JS and 10 of CSS: the `-999`
normalisation, the whole URL-state block, the `--acc-fill` tokens and the
2 px radii. `template.html` (dated 2 Aug) has none of them: `grep -c
"location.hash" template.html` → 0, `grep -c -- "-999"` → 0. Re-running
`build_lq.py` produces an app without shareable links and with `-999` on
screen; `test_perf.js` tests that older file. The brief's "this one has its
source" is true of the data and the fits, and false of the interface.

**Cost.** Port the two patches into `template.html` (copy-paste, 15 minutes)
and install `jsdom` so the perf test runs. Until then, every future rebuild
is a regression.

### F6. Bars on a log scale from a floating origin — MEDIUM

`makeScale` (`:529-546`) sets the log floor at 0.85 × the smallest visible
value and the ceiling at 1.12 × the largest, per render. Consequences,
measured:

- Default view: axis ticks = `["10.0"]`; no parity line (`results.json →
  default_state.axis`). The parity line only appears when the visible range
  straddles 1.
- Quahog bar 97.0% of track; cold-seep tubeworm 78.6%; ant queen 66.8%
  (`default_state.first`). The ratios are 47.5 : 23.4 : 21.8. A bar from a
  non-zero, non-parity origin on a log axis has no length semantics.
- Group view: the "1.00" tick label and the "1 · as predicted" label are
  drawn at the same x and overprint each other ("1.00s predicted",
  `shot-groups-desktop.png`, `drawAxis` `:657-671`).
- Linear scale has an honest zero but then the quahog compresses everything
  else into the left tenth; the page's own figure (`lq_ranked.png`) solved
  this by anchoring bars at 1 on a log axis, which the app does not do.

**Why it hurts.** The app's promise is that bar length shows the quotient
("bar length: quotient" in the legend). It shows `log(v) − log(0.85·min)`.

**Cost.** Anchor at 1 in quotient mode (bars extend left or right of parity,
as the figure does) and keep the current scale for years. ~40 lines in
`renderSpecies`/`renderGroups`/`drawAxis`.

### F7. Placeholders and assumptions presented as measurement — LOW-MEDIUM

- 77 genus clusters of four or more species share identical lifespan *and*
  mass (`rows.json`): *Chelonoidis* ×7 at 177 yr / 175,000 g, *Otomys* ×10,
  *Proechimys* ×10, *Chalcides* ×10, *Myotis* ×8 at 24 yr / 5.3 g. These are
  genus-level values copied per species by the Amniote compilation. Each
  renders as its own measured row, and in the group view inflates n.
- Human "wild maximum" = 70 yr is, per its own note, "pre-industrial adult
  expectancy at age 15" — a life expectancy, not a maximum. The note is
  visible only in the detail panel; the bar and the average (96.25) are not.
- FishBase masses "estimated from maximum length by FishBase's length-weight
  relationship, not weighed" (641 rows, the most common note) are drawn with
  no mark on the row.
- The count line "6398 species of 7873" under A–B hides that A–B excludes
  every FishBase and AmphiBIO record; the page says fish are "graded C
  throughout", the app does not.

---

## 4. Measure it

### 4.1 Weight

`site/longevity-app.html` 998,362 bytes. gzip −6: 266,816 bytes (GitHub Pages
compresses; the local server does not, so my throttled timings are worst case).

| part | bytes | share |
|---|---|---|
| data literal (`const P = JSON.parse("…")`) | 955,427 | 95.7% |
| JS code excluding data and FITS | 25,949 | 2.6% (7,179 of it comments) |
| markup + prose | 10,025 | 1.0% |
| CSS | 6,077 | 0.6% |
| FITS | 884 | 0.1% |

Inside the data literal:

| column(s) | bytes | note |
|---|---|---|
| `n` + `s` (names) | 331,557 | irreducible short of a second file |
| `pg` + `pc` (predictions) | 116,714 | derivable from `m` and `FITS` at load; 3 lines of JS |
| `a` + `mx` | 76,986 | derivable from `w` and `p` |
| `ki` (kingdom, one value) + `c` (pool, a function of `cl`) | 31,494 | constant / derivable |
| JSON-inside-a-string escaping | 39,566 | overhead of `JSON.parse("…")` over an inline literal |
| `note` dictionary | 2,509 | 60 distinct notes, fine |

~265 KB (28%) of the payload is derivable or constant. The first screen
needs 400 rows of 7,873 (5%); nothing is lazy. Dead code: none in JS; in CSS,
the `canvas, #gl, #view, #stage { touch-action:none }` and `#app { height:
100dvh }` rules (`:129-131`) address elements that do not exist in this page
and were pasted from another app's stylesheet.

### 4.2 Time to interactive (rows on screen, cold load, Chromium)

| condition | rows visible after | DOMContentLoaded | responseEnd |
|---|---|---|---|
| 1440×900, unthrottled | 245 ms | 83 ms | 10 ms |
| 390×844, unthrottled | 205 ms | 186 ms | 22 ms |
| 1440×900, Fast 3G (1.6 Mb/s, 150 ms RTT) | 5,469 ms | 5,413 ms | 5,194 ms |
| 390×844, Fast 3G | 5,431 ms | 5,382 ms | 5,224 ms |

Parse + rehydrate + first render is ~200 ms; everything else is transfer. On a
gzipping host the 3G figure would be roughly 1.6 s. No console messages of any
kind on load, in any condition.

### 4.3 Type

Distinct rendered sizes: 10.5, 11, 11.5, 11.67, 12.5, 13, 13.5, 14, 16, 20,
27 px. Under 12 px:

| element | size | what |
|---|---|---|
| `.lab` | 10.5 px | every control-group label ("VIEW", "SORT BY", …) |
| `.gl span` | 10.5 px | axis tick labels, including "1 · as predicted" |
| `.val` | 11.5 px | the quotient / years label on every row |
| `table.fits th` | 11 px | fit table headers |
| `sup` | 11.67 px | the exponent *b* in the fit note |

Also 10 px: `.colb` (the "colonial" badge), not on the default screen.

### 4.4 Contrast

Text, computed from rendered colours (`results.json → type_light/type_dark`):
every text/background pair passes AA in both schemes; lowest are `code` 4.57:1
(light) and `.dim`-class text 5.37:1 (light) / 6.5:1 (dark). One "fail" my
script reported (axis tick 4.07:1) is an artefact of measuring the span
against its 1 px gridline parent; against the page it is 5.37:1.

Non-text, against the page background (3:1 is the AA floor for UI boundaries
and graphical objects):

| element | light | dark |
|---|---|---|
| wild bar | 5.43 | 6.11 |
| captive bar | 7.18 | 6.05 |
| group bar | 4.48 | 7.20 |
| average tick (`.avg`, opacity .55) | 3.78 | 5.23 |
| **gridlines** (`--rule`) | **1.32** | **1.40** |
| **range line** (`.rng`, opacity .32) | **1.49** | **1.72** |
| **parity line** (`.gl.one`, opacity .55) | **2.63** | **2.55** |
| **segment / input borders** (`--faint` on card) | **1.28** | **1.12** |
| **wild bar vs captive bar** | **1.32** | **1.01** |

The last row is the one that matters: wild and captive are distinguished by
hue alone, and in dark mode their luminance is identical. The average tick is
the only cue that both are present, and it is hidden when only one exists.

### 4.5 Mobile (390×844, `shot-mobile-*.png`)

Plainly: a phone reader can read the introduction and can, with effort, see
the top few rows. They cannot browse a ranking.

- The control panel is **724 px tall — 83% of the viewport — and
  `position: sticky; top: 0`**. Once the reader scrolls to the chart, the
  panel pins and **four rows** are visible below it (`mobile_scrolled`:
  panelBottom 724, visibleRows 4, viewportH 877). Without the panel the
  viewport holds 29 rows. Group view: panel 682 px, first row at 754 px.
- Name column is 150 px; **384 of 400** default rows are truncated with an
  ellipsis (`mobile.truncatedNames`); 78 of 400 still truncate under Names →
  Common. The track is 196 px wide, so the whole quotient range sits in 196
  px.
- All 27 visible buttons are 29 px tall (`err.js → btn.minH`), under the
  44 px touch-target guideline.
- The detail panel covers 54% of the viewport, is `position: fixed`, and does
  not trap focus.
- No horizontal overflow (scrollWidth == innerWidth). Body text 16 px. One
  `.val` label sits off the right edge.
- `@media (max-width:700px)` (`:125-126`) is the only breakpoint and only
  narrows the name column.

### 4.6 Motion contract

Not honoured. The source contains neither `data-motion` nor
`prefers-reduced-motion` (`results.json → grep_motion_in_source`). Measured
on a re-sort of 400 rows: **438 `transitionrun` events** with motion default,
with `prefers-reduced-motion: reduce`, and with `data-motion="off"` set on
`<html>` before first paint — identical in all three. Transitions in play:
`.row` transform 0.58 s and opacity 0.3 s, `.bar` width 0.58 s, `.avg` /
`.rng` / `.val` / `.gl` left 0.5–0.58 s, `#chart` height 0.45 s
(`:52-81`). The content page `longevity.html` sets the contract on its own
`<html>`; the app opens in a new tab and never reads it.

### 4.7 Accessibility, briefly

Rows are `div`s with `onclick`, `tabIndex -1`, no role — the detail panel is
unreachable by keyboard. Search and both selects have no label or
`aria-label`; the `.lab` spans are not `<label>`s. Segment groups have no
`role`. Buttons have `outline: none`-equivalent focus (computed
`outlineStyle: none`). `aria-pressed` on the segment buttons is correct and
kept in sync.

---

## 5. Cross-check

*(appended after §6 was written — see the end of this document)*

---

## 6. Findings, ranked

| # | finding | severity | where | cost to fix |
|---|---|---|---|---|
| F1 | 63% of "wild" maxima come from sources with no origin field; AnAge unknowns routed to wild; provenance not shipped or shown | **HIGH** (honesty) | `ingest.py:169-172, 204-206, 224, 246, 345`; app `:280-283, :686` | data: ~20 lines; app: ~30 lines + 16 KB |
| F2 | 28 Amniote records with 1–3 month maxima at up to 5 kg, graded B, are the bottom of every ranking and half of `lq_ranked.png` | **HIGH** (data honesty, published figure) | `ingest.py:206`; `build_lq.py:565-567` | gate ~10 lines; figure rebuild; data review is real work |
| F3 | Page says weighted OLS + Kish n_eff; code runs unweighted filter, n is raw | **HIGH** (honesty, prose) | `longevity.html:337-352`; `update_page.py:214-238`; `build_lq.py:96-99, 236-239` | one paragraph |
| F4 | Page/margin/video/figure/app disagree: ant queen 28.72/27/21.78; quahog 45/47.48; Chiroptera 2.68 vs linked 2.66; amphibian r² 0.12 vs 0.043; 1.8× vs 2×; "0 g"; explainer uses global fit; 112 vs 114 orders | **MED-HIGH** | see table in §3 | ~1 hour |
| F8 | Mobile: sticky panel 83% of viewport, 4 rows visible; 96% of names truncated; 29 px buttons | **HIGH** (mobile unusable) | `:26-29, :125-126` | collapse the panel below 700 px: ~40 lines CSS/JS |
| F5 | Shipped app hand-patched; `template.html` lacks URL state and `-999` fix; rebuild regresses; `test_perf.js` can't run | **MED** | `template.html`; `longevity-quotient/longevity.html` | 15 min port + `npm i jsdom` |
| F6 | Log bars from a floating origin; default view has no parity line; "1.00"/"1 · as predicted" overprint | **MED** (chart honesty) | `:529-546, :657-671` | ~40 lines |
| F7 | Motion contract ignored: 438 transitions run under `data-motion=off` and `prefers-reduced-motion` | **MED** (site contract) | `:52-81`, no reader of `data-motion` | 1 media query + 1 attribute selector, ~8 lines, plus the pre-paint script |
| F9 | Amphibians: bar uses global fallback, detail panel shows "—" for the same quantity; Urodela ranked 2nd of all orders on a baseline the page calls unfair | MED | `:401, :688-690, :156-160` | label the fallback in detail + group rows: ~10 lines |
| F10 | `-999` still in payload (127), `lq_table.csv`, and the public download zip; `<b> </b>` in two names; subspecies junk in 12 | MED (data hygiene) | `ingest.py:87-101, 516` | 3 lines in `num()`/name cleaning + rebuild |
| F11 | Wild/captive distinguished by hue only; 1.01:1 luminance in dark; gridlines/borders/range/parity lines all < 3:1 | MED (a11y) | `:6-13, :63-81` | palette + a pattern or marker |
| F12 | Filter/hash value not found → silently lands on first taxon alphabetically with a wrong crumb | LOW-MED | `:757-760` | 5 lines |
| F13 | Keyboard: rows unfocusable, detail unreachable; unlabelled inputs; no focus ring | MED (a11y) | `:601-616, :185-190` | ~20 lines |
| F14 | Five text styles under 12 px, incl. every control label and every row value | LOW-MED | `:30, :77, :74, :102, :112` | CSS |
| F15 | 28% of payload derivable (`pg`,`pc`,`a`,`mx`,`ki`,`c`) + 40 KB string escaping; nothing lazy; 5.4 s on 3G uncompressed | LOW-MED | `build_lq.py:709-740` | ~30 lines either side; or split data to a second file |
| F16 | Genus-copied values (77 clusters ≥4 identical rows); human "wild" is a life expectancy; modelled fish masses unmarked on the row | LOW-MED (honesty) | data + `:686` | mark on row: ~10 lines; data review: real work |
| F17 | Group-link landing shows a single bar with nothing to compare; filtered-to-nothing under A–B gives no hint | LOW | `:594-600, :548-556` | copy |
| F18 | "Name" sort puts 127 nameless species first as empty strings | LOW | `:509` | 1 line |
| F19 | Dead CSS for `canvas/#gl/#view/#stage/#app` | LOW | `:129-131` | delete |
| F20 | Default first screen at 1440×900: first row 556 px down; ~11 rows visible | LOW | `:26-29` | layout |

---

## 7. What is good and must survive

- **The payload design.** Column-oriented, dictionary-encoded, handed to
  `JSON.parse` as a string, rehydrated once (`:312-334`; `build_lq.py:686-740`).
  The reasoning in the docstring is correct and the result is a 200 ms parse
  for eight thousand rows.
- **The render architecture.** Persistent row nodes keyed by species, moved
  by `transform`, with child references cached on the node and every style
  write guarded against its last value (`:576-620`, `put`/`putText`/`putHTML`).
  The comments explain what was slow and why, and the measurements here
  confirm it: 100–500 ms per re-sort at 400 rows including animation.
- **Cached pools and groups** keyed on exactly the state that changes them
  (`:415-426`, `:466-500`), with a comment documenting the cache-key ordering
  bug that was fixed. This is the difference between typing in the search box
  feeling instant and not.
- **The URL-state contract** (`:341-395`): every key validated against an
  enum, malformed input degrades to defaults, `replaceState` keeps history
  clean, `hashchange` re-restores, and the format is documented as a contract
  for other pages. It works in every case I threw at it, including injection.
- **The prose inside the app.** The sections on grade C ("read the bottom of
  that ranking as a map of what is understudied"), on colonies, on what a
  maximum is and is not, and on the wild/captive asymmetry (`:213-283`) are
  honest and clear. They are better than the page's. The fit table with the
  rejection reason printed in the row is exactly right.
- **Both baselines in the detail panel**, with the own-group one bolded and
  the global one beside it, so the reader can see what the baseline choice
  does to one animal.
- **Geometric mean for the group view**, with the range line and the
  minimum-species control, and the explanation of why the arithmetic mean is
  wrong for ratios.
- **Honey bee queen and worker kept as two rows** under one binomial, and the
  merge code that goes out of its way to preserve that (`ingest.py:405-427`).
- **The default sort and default filters.** Quotient, own group, A–B, colonies
  out is the right first screen. The top of it is the real result.
- **Text contrast** passes AA everywhere in both schemes; the `--acc-fill`
  correction is present here.
- **No console noise, no errors on load**, at any viewport or throttle.
- **`window.__lq`** as a test handle, and `test_merge.py` passing 21/21.
- **The explainer figure** (`lq_explained.png`) as a teaching device — the
  form is right even though its numbers are on the wrong baseline (F4).

---

## 8. What is not fixable in this app

**Problems of the interface** (fixable here, listed above): F5, F6, F7, F8,
F9, F11, F12, F13, F14, F15, F17, F18, F19, F20, and the labelling half of
F1 and F16.

**Problems of the underlying data**, which the app can label but not cure:

- **No wild/captive distinction exists for 4,015 records** (F1). Amniote,
  FishBase, AmphiBIO and PanTHERIA report one number. The app can say
  "maximum, origin not recorded"; it cannot recover the origin.
- **The 28 one-to-three-month amniote maxima** (F2) are source errors. The
  app can exclude or flag them; the correct values need a person and the
  primary literature.
- **Genus-level values copied per species** (F16, 77 clusters). Amniote fills
  species from genus means; only a source with species-level provenance
  fixes that, and `DATA_SOURCES.md` already lists the candidates.
- **127 missing common names** and the AnAge HTML/subspecies junk (F10) —
  cleanable at ingest, but the names themselves have to come from somewhere.
- **The amphibian baseline** (F9). r² = 0.043 over 83 effective species is
  not a relationship; the app's choice to fall back to the global fit is
  defensible, but the result — Urodela second of all orders — is a statement
  about the baseline, not about salamanders. Only more amphibian data changes
  that, and `DATA_SOURCES.md` says so.
- **The invertebrate baseline rests on 57 species** across 24 classes. Every
  headline result at the top of the ranking is scored against it.
- **Maximum lifespan is a record, not a rate.** The app says this well. It
  remains true of every bar on screen and no interface change alters it.
- **The human row** mixes a life expectancy with a verified maximum; that is a
  seed-table decision, recorded in its note.

---

## 5. Cross-check (written after §6–§8)

Read in the order the brief set: `DESLOP_AUDIT_2026-09-04.md`, then
`DESIGN_AUDIT_EXTERNAL_2026-08-30.md` §6, §7, §12 and "What's missing" §7,
then the appendix checklist.

### 5.1 `DESLOP_AUDIT_2026-09-04.md` on this app

What it has on `longevity-app.html`: 974 KB single file (§2a); body in Georgia
at a 1,036 px measure, 419 elements under 12 px (F11 there); primary buttons
white on violet at 3.27:1 in dark (§2c); and, on the page, the video caption's
45× against the margin's 47.48× ("Content, not presentation, and out of my
remit"), 977 KB of figures, and 605 ms idle CPU per 3 s for the margin scene.

- **Caught that I missed:** nothing on the app itself. The 1,036 px measure
  (my `.wrap` note, not a finding), and the page-level items (figure weight,
  idle CPU of `biome-scene.js`, phone-width figures), which are outside this
  brief.
- **Now resolved since it was written:** the button contrast. The shipped app
  carries `--acc-fill` and measures 6.6:1 dark / 7.82:1 light (§4.4).
- **Caught here that it missed:** everything in §3 (F1–F4, F7, F9, F16), the
  source drift (F5), the floating log origin (F6), the motion contract on the
  app (F7 — that audit tested the contract on content pages only), the mobile
  panel (F8), hue-only bar encoding (F11), keyboard access (F13). Its remit
  was presentation across the site, so most of this is scope rather than
  oversight; F7 and F8 are the two it would reasonably have been expected to
  find.
- **Wrong in it:** nothing I can show. Its "419 sub-12 px elements" is an
  element count where mine is a style count (five styles; 400 of the 419 are
  the `.val` labels); both are right.

### 5.2 `DESIGN_AUDIT_EXTERNAL_2026-08-30.md`

**§6 "Longevity lollipop wastes half its panel."** Not true of the shipped
figure. `lq_ranked.png` as it stands is log-scaled and anchored at 1
(`build_lq.py:571-577`, and the comment above it describes exactly the
linear-from-zero problem the external audit saw); the twelve below-parity
species extend left and the eighteen above extend right. The layout was fixed
in `a402b9f` (4 Sep). What is wrong with that figure now is its content: the
twelve on the left are the Amniote artefacts of F2, not "who does not".

**§7 "Sentinel value leaking into the visualiser UI."** Fixed at the app
boundary in the same commit; still in the payload, `lq_table.csv` and the
public zip (F10). Its "also worth a grep of the CSV for other sentinel fields"
was the right instinct: the grep turns up the `<b> </b>` names and the
subspecies junk.

**"What's missing" §7 "Deep links from claims into the visualiser … currently
no view survives a copy of the address bar."** Also fixed in `a402b9f`: the
app has URL state and the page has eleven links into it. The brief
(`prompts/AUDIT_longevity.md` §2, written 4 Sep) repeats the 30 Aug claim as
an open question. Per the house rules' request to report stale premises: this
is one, and the interesting residue is not that the links are missing but that
they land on a different number from the sentence that carries them (F4,
Chiroptera 2.68 → 2.66).

**§12 small-type inventory** did not look at this app. **Its contrast note**
("No AA failures found in the core palette") was already corrected by the
deslop audit; for this app the correction has been applied.

- **Caught that I missed:** nothing on the app.
- **Caught here that it missed:** as for §5.1, plus the figure's content
  problem it read as a layout problem.
- **Wrong in it, as of today:** §6 and "What's missing" §7 describe a state
  that no longer exists; §7 (sentinel) is half-resolved.

### 5.3 The appendix checklist

Disclosed at the top: I saw these six bullets on my first read of the brief.
For each, whether I found it, and whether the method would have without the
prompt.

| bullet | found? | what I actually found | would the method have found it unprompted? |
|---|---|---|---|
| `-999` as a common name in the default view | yes — verified gone from the UI, present in the data (F10) | 127 rows in payload/CSV/zip; fix is in the app, not the pipeline | yes; brief §2 names it too, and the payload census was the first thing done |
| No URL state | premise is stale — state exists and works (§2.4) | the links resolve to different numbers than the prose (F4); unknown `fVal` lands on the wrong taxon (F12); the linked landing is one bar (F17) | yes; brief §2 asks for the round-trip test |
| 998 KB mostly an embedded dataset | yes (§4.1) | 95.7% data; 28% of it derivable; 40 KB escaping overhead; gzip 267 KB | yes |
| Lollipop wastes the left half | checked; **no longer true** (§5.2) | the figure's left half is the F2 artefact list | yes — §3 of the brief asks whether the figures agree with the outputs, which means opening them |
| Wild-vs-captive handling invisible to the reader | yes, and worse (F1) | 63% of "wild" is unlabelled-origin data; AnAge unknowns → wild; provenance not shipped | yes; brief §3 points at `DATA_SOURCES.md` and the merge scripts, and the answer is in `ingest.py` |
| Control labels below 12 px | yes (§4.3, F14) | 10.5 px labels and ticks, 11.5 px row values, 11 px table headers | yes; §4 asks for every rendered size |

Two of the six describe conditions that were fixed on the same day the brief
was written. The list did not contain the three findings I rank highest
(F1 in its full form, F2, F3), and the brief's §3 questions are what led to
them.
