# The shoe project — Stage 1

`prompts/NEW_PROJECTS.md` §6. Research and feasibility only. Nothing in
`00 PUBLISH` was touched; nothing here is designed or built.

Written 2026-09-05.

---

## Verdict, up front

**Two separate answers, because §6 turns out to contain two projects.**

1. **The materials and recycling subject — the one the retired pages are
   actually about — should be retired a second time and not rebuilt.** Its
   central number cannot be recomputed from any public source, its primary
   citation is a paywalled paper whose free version is a working paper marked
   *do not cite*, and the honest version of its argument is something the
   reader already believes. It fails three of the four kill criteria in
   "What kills a project".

2. **The performance subject — footwear and the energetic cost of running — is
   worth building, and it is stronger than the brief suggests.** Not because
   super-shoes work, which everybody knows, but because the published effect
   sizes for the same intervention disagree by a factor of nearly four between
   studies and by more than twenty percentage points between individual
   runners in a single study. The mean is the headline; the spread is the
   finding.

The autopsy §6 asks for comes first, because it is what makes the second
answer defensible rather than a new coat of paint on the same mistake.

---

# Part A — The autopsy

## A1. What was there

- `unpublished/running-shoes.html` — 13 KB, retired before 2026-08-30, per
  `unpublished/RETIRED.md`.
- `unpublished/running-shoes-app.html` — 39 KB, a three.js exploded view of
  four shoe archetypes, opening state `?shoe=1&part=2&explode=1&az=&el=`.
- `unpublished/assets/running_shoe.png` — 249 KB flat figure.
- `build_climate_figures.py` → `fig_shoe()` and `shoe()`, which generate that
  figure.

## A2. The audits, run

`HANDOFF.md` §7's suite cannot be pointed at these files unchanged: they are in
`unpublished/`, not `site/`, so the page rig and the generator drift check have
nothing to address. Everything else was run — the figure generator directly,
and the browser checks through `autopsy/audit_pages.js`, which borrows
Playwright from `00 PUBLISH/tests/node_modules` and writes nothing there.

| Check | Result |
|---|---|
| Figure generator still executes | **Passes.** Re-run with `OUT` redirected into `autopsy/`; see `autopsy/rerun_fig.py`. |
| `build_climate_figures.audit()` — overlapping and off-canvas text | **0 problems.** `running_shoe.png OK` |
| Retrospective-prose grep (`an earlier version`, `used to be`, …) | **Clean.** Neither file breaks the no-development-history rule. |
| Markdown that never became HTML | **Clean.** |
| Regenerated PNG vs shipped PNG | Differ (219,636 B vs 255,294 B). **Inconclusive**, not evidence of drift: `DESLOP_3B_2026-09-04.md` records `running_shoe.png` as re-rendered in that pass, and this machine substitutes font weight 700 for the requested 600. |
| Text contrast in the app, WCAG 2.x (deslop T8) | **Passes, every pair.** ink/bg 15.89, dim/bg 6.50, dim/panel 6.21, accent/bg 6.05, accent/panel 5.78 — all above 4.5:1. Only the hairline `--rule` on `--bg` is low at 1.40:1, and that is a border, not text. |
| Does the flat page render outside `site/`? | **No.** `style.css` fails to load, the body background resolves to `rgba(0,0,0,0)`, the `h1` falls back to Times New Roman, and the measure runs the full 1424px of the viewport. `shot-page.png`. |
| Does the 3D app boot and rotate? | **Yes**, in headless Chromium with WebGL. See A5 — this is where the interesting result is. |

Two things follow.

**The retired work passes every mechanical audit the site owns**, and it passes
the one I expected it to fail: the palette's contrast is fine. Whatever is
wrong with it, the audits do not see it. That is trap 12 in a new costume —
**the checks catch layout, staleness and contrast, and nothing in the suite
asks whether a figure contains any information.**

**The pages are not self-contained artifacts.** `RETIRED.md` says the sources
are kept, and they are, but the page cannot be opened and judged without the
stylesheet it left behind in `site/`. Its frozen nav also still advertises
"Climate research", the DAC and holdup pages and the bookshelf, all since
retired. Anything rebuilt here starts from the current skeleton, not from this
file.

## A3. Against the deslop criteria

`DESLOP_AUDIT_2026-09-04.md` §1a, T1–T15, applied to the two files:

| Tell | Present? | Evidence |
|---|---|---|
| T1 violet accent on dark | **Yes** | `--acc:#8b7ff2` in the app's `:root`; `ACC = "#8b7ff2"` in `build_climate_figures.py` |
| T2 dark as the default state | **Yes** | `--bg:#070a12`, figure `BG = "#0a0d18"` |
| T3 card grid, each card kicker + title + body | **Yes** | The figure's whole lower panel is four identical `FancyBboxPatch` cards |
| T4 hairline border + rounded fill | **Yes** | `boxstyle="round,pad=0.6,rounding_size=2", fc="#0d1322", ec=RULE` |
| T6 coloured kicker above body text | **Yes** | Card titles coloured `WARN`/`GOLD`/`GREEN` by mood, not by data |
| T7 bare system sans as the only face | **Yes** | `--sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif` |
| T9 glow | Partly | `box-shadow:0 10px 28px rgba(0,0,0,.5)` on the tooltip; a violet rim light in the 3D scene |
| T10 decorative motion | **Yes** | An auto-spin toggle on a model that gains nothing from rotating (A5) |
| T15 decoration that is not the content | **Yes** | `radial-gradient(circle at 50% 45%, #0a1024, #05070f)` behind the canvas |
| T8 low-contrast text on dark | **No — measured, not assumed** | Every text pair is above 4.5:1; see the table in A2 |

Nine of fifteen. The detector cited in that audit calls four or more "heavy".
But this is the shallow layer, and repalletting it would not fix the page —
which the T8 row makes concrete: the one tell that is a defect in its own
right, rather than a fashion, is the one this work does not have.

Also present, from `HANDOFF.md` §8: **trap 5**, `float:right` on
`header a.back` in the app — a `float` inside what the comment beside it
describes as a CSS grid.

## A4. The deeper failure — there is no quantity anywhere

This is the answer to "why does it read as slop", and it is not the palette.

**Not one number on either page or in the figure was computed.** The figure
plots nothing. It has no axis, no scale, no measurement. Its four "shoes" are
filled regions whose proportions come from eight literals in `fig_shoe()` —
`heel=0.34, fore=0.25` and so on — introduced by a docstring that says the
outline is "sampled from functions rather than placed by hand" and a comment
that says the heights "carry the real proportions". Real to what? No source is
named, in the figure, in the code, or on the page. Under §4's rule — every
number traces to a data set, a computation or a publication — those eight
literals are invented data presented as measured, on a site whose most valuable
find of the last week was exactly that.

The prose carries three numbers, all from one source, none recomputed:
13.6 kg CO₂e per pair, 65 parts, 360 processing steps.

A site whose identity is *computed models with named sources* published a page
that is an illustrated essay. Everything in A3 is downstream of that. Fix the
palette and it is a tastefully coloured illustrated essay.

## A5. The 3D model contains no third dimension

**The code says so.** `bandGeometry()` builds a `THREE.Shape` from the same
top/bottom profile the flat figure draws, extrudes it by `WID`, and then scales
each vertex's *z* by `widthAt(t)`. The width curve is another invented function.
The plan view is therefore not measured, not traced, and not independent of the
side view: it is the side view with a taper.

**And the rendering confirms it.** The app boots in headless Chromium with
WebGL; `audit_pages.js` captured the opening state and the same model dragged
about 90° (`autopsy/shot-3d-open.png`, `shot-3d-rotated.png`). Looking at the
two:

- **Rotation reveals no part that was not already visible.** Every material in
  the legend — outsole rubber, EVA foam, sockliner, engineered mesh, TPU
  overlays — is showing in the opening three-quarter view. Turning the model
  through a right angle adds no layer, no joint and no relationship. The
  interaction the page sells as "see how many pieces there are" is answered
  before you touch it.
- **Rotation makes it less legible, not more.** In the opening view the object
  at least reads as a longitudinal stack of bands. Turned toward the toe it
  collapses into a lump with a blue slab where the heel collar should be, and
  the purple heel counter and toe bumper stand proud of the mesh they are
  supposed to sit inside — a layer-ordering failure that the side view hides.
- **It does not read as a shoe from any angle.** There is no lace, no eyelet,
  no collar opening, no tread, no foot entry. The opening view reads as a
  chaise longue. The code comment beside `LEN/WID/HGT` records that an earlier
  build "read as a doorstop" and was fixed by rescaling; the fix changed which
  piece of furniture it resembles.

That is precisely the trap §2 of the brief names — "a rotating 3D neuron is a
screensaver" — and this project hit it two projects early. **The 3D model was
not the cause of the failure, but it is the clearest symptom: it is motion
substituting for information.**

To the code's credit, the dimensions that comment cites (28 cm long, 10 cm
across, 9 cm heel height) are plausible. They are also unsourced, and they are
the only three numbers in the whole model that even attempt to be real.

## A6. What the sources actually support

Checked against the primaries, not against the page.

- **Reference 2, the load-bearing one.** The page cites "MIT News, 2013". The
  study is Cheah, Duque Ciceri, Olivetti, Matsumura, Forterre, Roth & Kirchain,
  *Manufacturing-focused emissions reductions in footwear production*, Journal
  of Cleaner Production 44:18–29 (2013). **Citing the university's press
  release rather than the paper is the defect**, and it propagated an error:

  - The paper states **65 discrete parts and 360 processing steps for a single
    shoe**. The page says "the MIT life-cycle assessment of a pair of running
    shoes counted 65 discrete parts and more than 360 processing steps", and
    the figure says "65 discrete parts and 360-odd processing steps **per
    pair**." Both are wrong by a factor of two. Verified in
    `sources/cheah_2013.txt`, extracted from the MIT DSpace copy.
  - The split *is* defensible: Figure 1 gives 9.5 kg CO₂e manufacturing and
    4.0 kg materials per pair, with materials plus manufacturing at 97% of the
    total — so ≈14 kg total and manufacturing ≈68%, and "more than two thirds"
    holds. The page's 13.6 kg is close to but not the free version's number.

- **Reference 1 is not a citation.** "Manufacturer technical literature …
  cross-checked against the running-foam surveys at RunRepeat and Blister
  Review." A named source is required; two review websites and unnamed
  marketing material are not one.

- **Reference 3 is sound.** Curtis & Hansson (2019), *Case Studies in the
  Environment* 3, doi `10.1525/cse.2019.001974` — real, and it supports the
  claim made from it.

To the page's credit, its "What this page is not" section is the best writing
on it, and its refusal to attach per-part mass or carbon numbers — "a
plausible-looking figure attached to each layer would be the most quotable
thing on the page and the least defensible" — is the correct instinct, applied
one level too late. The layer numbers were refused; the layer *geometry* was
invented anyway.

## A7. So why does it read as slop — one sentence

Because it was never answering a question: it is a subject rendered
attractively, and once there is no question, the figure has nothing to plot,
the model has nothing to reveal by moving, and what is left is decoration doing
the work that evidence should.

Everything else — the violet, the dark ground, the four mood-coloured cards,
the spin toggle — is what fills that space.

---

# Part B — Should the materials subject be rebuilt?

**No.** Against "What kills a project":

**The data exists but supports only a much weaker claim, and the weaker claim
is not interesting.** The strong claim is quantitative: shoes have a large
footprint, dominated by manufacturing, and their construction forecloses
recycling. The first half rests entirely on one 2013 LCA of one shoe. Its
inventory is a bill of materials and process data "provided by the product
designers and manufacturers", aggregated through Monte Carlo over ranges those
manufacturers supplied. **It is not reproducible from any public source.** No
public database gives the mass, polymer or process energy of a shoe's parts.
Every number would be a borrowed number, which is the position §4 exists to
prevent.

**The only sources are works whose content cannot be reproduced.** The
published paper is paywalled at Elsevier. The free MIT DSpace copy is the
February 2012 working paper, stamped *"Do not cite without permission of
authors"* on every page. A site that will not publish an unsourced number
should not build a page whose one number is drawn from a document that says
that.

**The honest version is something the reader already knows.** Strip out what
cannot be sourced and what remains is: a running shoe is many bonded plastics,
so it cannot be recycled into a shoe. Anyone who has considered the question
believes this already, and the page cannot quantify the parts of it that would
be new — how much, how many, at what cost.

The subject is not worthless; there is a genuine paper here (Curtis & Hansson
on what a take-back scheme actually does). It is not a project for *this* site,
which computes things.

**Retiring it a second time is the recommendation.** `RETIRED.md` already
carries the entry; it needs no change beyond, at most, a line saying the
subject was reviewed and not rebuilt.

---

# Part C — The performance subject

## C1. The central claim, in one sentence

*The performance advantage of a modern racing shoe is real and it is measured,
but every published number for it is a different number, and the range across
studies and across individual runners is wider than the effect itself.*

The supportable second sentence, which is what makes it a page rather than a
caveat: *the effect shrinks systematically as the test conditions come to
resemble an ordinary runner in an ordinary race.*

## C2. What the reader already believes

That carbon-plated shoes make you about 4% faster. Three things are wrong with
that sentence and all three are checkable:

1. **4% was metabolic cost, not time.** On the transfer coefficient measured in
   the same laboratory, 1% of economy buys about 0.70% of race time
   (§C4). The naive translation of 4.16% economy is 2.9% time, not 4%.
2. **4% was a prototype.** The retail shoe, measured against the same control
   brand by an independent group, came out at 2.8%.
3. **4% is a mean over people for whom the answer is not the same.** In
   world-class Kenyan runners the individual responses ran from an 11.3%
   drawback to an 11.4% benefit.

## C3. The evidence, and it exists

Twenty comparisons from thirteen peer-reviewed papers are collected in
`effects.json`, every row with the sample, the speed, the setting and a DOI.
`check.py` computes over them; `check_output.txt` is its output. Findings:

**The spread between studies.** Twelve laboratory comparisons of advanced
footwear against a control shoe range from **1.10% to 4.20%**, median 2.82% —
a 3.8-fold range across peer-reviewed measurements of ostensibly the same
thing.

**The gradient.** Sorting those twelve by effect size sorts them
approximately by how artificial the test was: prototypes on treadmills at
elite pace at the top (4.20, 4.16, 4.01), the retail shoe against a stiff
control mid-table (2.80), track spikes lower (2.10), and at the bottom the
only outdoor measurement — an AFT trail shoe at 11.5 km/h on real ground —
at **1.10 ± 1.1%**, a standard deviation equal to its mean.

  *This ordering is suggestive, not demonstrated.* Speed, shoe generation,
  control shoe, terrain and laboratory all vary together across those twelve
  rows; nothing here isolates one of them. Any figure must show it as a
  pattern across studies, never as a fitted trend, and must say so.

**The individual spread.** Where studies report per-athlete results rather
than means, the ranges are: −0.50% to +5.34% and +1.72% to +7.15%
(Barnes & Kilding, n=24, both sexes); −1.1% to +9.7% in amateurs and
**−11.3% to +11.4%** in world-class runners (Knopp et al., n=7 each). Three of
the four span zero. **The widest is 22.7 percentage points, against a
literature whose every mean sits between 1% and 4%.**

**The contradiction nobody has resolved.** The foundation of the whole field is
that shoe mass costs about 1% of metabolic rate per 100 g per shoe — measured
at 1.11% (95% CI 0.88–1.35) by Hoogkamer et al. 2016, and traceable to
Frederick, Daniels & Hayes 1984. Rodrigo-Carranza et al. 2020 performed the
same manipulation and measured **7.40% at 85% of the ventilatory threshold and
10.21% at 95%** — 6.7× and 9.2× the accepted figure. Both are peer-reviewed;
neither is retracted; the second is rarely cited against the first.

**What the mechanism is not.** Stephen et al. 2025, meta-analysing 48 studies
(n=878), find that neither longitudinal bending stiffness alone nor midsole
energy return alone significantly affects oxygen consumption — only their
interaction does. Ortega et al. 2021 put the bending-stiffness literature at
"~3% deterioration to ~3% improvement". Rodrigo-Carranza et al. 2022 find that
a *curved* plate improves economy 3.45% while a *flat* plate does not.
**"The carbon plate does it" is not what the evidence says**, and that is a
correction most readers have never encountered.

**The two independent meta-analyses agree.** Xiao et al. 2025 (17 RCTs, n=281)
and Stephen et al. 2025 (48 studies, n=878) both arrive at SMD **−0.44** for
oxygen consumption, by different routes. Xiao also gives time-trial
performance at −0.23 — about half the size of the oxygen effect, which is the
same story as the transfer coefficient told a different way.

## C4. Computed, looked up, assumed

The three categories the site labels separately, decided now rather than in
Stage 2:

- **Looked up.** Every effect size, confidence interval, sample size, speed and
  setting in `effects.json`. Each carries a DOI. The World Athletics rules
  (40 mm road / 20 mm track stack, one rigid plate) come from the regulation
  PDF in `sources/`, not from press coverage.
- **Computed.** The spread statistics, the ordering, the transfer coefficient
  0.78 ÷ 1.11 = 0.70, the ratio of any two published effects, and any
  translation of an economy percentage into a race time. All arithmetic over
  the sourced table — no fitting, no smoothing, no model.
- **Assumed, and must be labelled.** That the 0.70 transfer coefficient, which
  was measured for *added mass over 3000 m in trained men*, applies to a
  different intervention over a different distance. It probably roughly does —
  it follows from the linear speed–metabolic-rate relationship — but it has not
  been measured for advanced footwear, and any figure that uses it is making an
  assumption, not reporting a finding.

## C5. The data, named, with what it costs

| Source | What it is | Cost | Usable? |
|---|---|---|---|
| The thirteen papers in `effects.json` | Effect sizes, CIs, samples, conditions | Free (abstracts carry the numbers; several are open access in PMC) | **Yes.** Already extracted. |
| Guinness et al. 2020, `github.com/joeguinness/vaporfly` | Marathon results scraped from marathonguide.com, 2015–2019, plus hand-curated shoe labels from public race photographs; men's and women's CSVs, scrape and analysis scripts | Free | **With care.** The repository carries **no licence**, so redistributing the CSVs in a `downloads/` archive is not clearly permitted. Citing the published estimates (men 1.4–2.8%, women 0.6–2.2%) is fine. |
| World Athletics Athletic Shoe Regulations, Book C – C2.1A | The rules themselves: stack heights by event, the single-rigid-plate clause, development-shoe windows | Free PDF | **Yes.** In `sources/wa_shoe_regulations_2026.pdf`. |
| World Athletics approved-shoe list | ~600 rows: brand, model, six event-eligibility flags, development-shoe dates | Free PDF; live version behind a JS app at `certcheck.worldathletics.org` | **Only for what it is.** Checked: it is an eligibility list. **No mass, no stack height, no plate geometry.** |
| Cheah et al. 2013 footwear LCA | The materials-side numbers | Paywalled; free copy is a working paper marked *do not cite* | Not needed for this project. |
| `03 RESEARCH/running/sources/` (§5's downloads) | Málaga treadmill VO₂, Lagos walk/run energetics, marathon Garmin traces, age-grade tables | Already downloaded by §5 | Possibly, for the economy spine. See C7. |

**The gap, stated plainly.** There is no free, comprehensive database of shoe
mass, stack height, foam type or plate geometry by model. RunRepeat and similar
sites hold one; it is proprietary. **So the version of this project that plots
hundreds of shoes in a specification space cannot be built.** Anything of that
shape must be dropped in Stage 2 rather than discovered in Stage 3.

## C6. What could kill it, and did not

- *Does the data exist?* Yes, and it is unusually clean: effect sizes with
  confidence intervals, in abstracts, free.
- *Does it support only a weaker claim?* The weaker claim **is** the claim. The
  project is about the spread, so the disagreement in the literature is the
  material rather than an obstacle.
- *Does the reader already know it?* No. They know "4%". They do not know it
  was a prototype, that the retail measurement was smaller, that economy is not
  time, that the plate alone does not explain it, or that some runners are
  slower in the shoe.
- *Copyrighted-only sources?* No. Everything load-bearing is a journal paper
  cited for its numbers, or a free regulation PDF. §5's *Advanced Marathoning*
  rule does not bite here.

**The one real risk is not evidential, it is editorial.** This subject has an
enormous popular literature and it is easy to write the hundredth "do super
shoes work" article. The defence is that no popular treatment puts the twenty
published effect sizes on one axis and shows how far apart they are — for the
same reason the site's other projects exist.

## C7. The dependency on §5, which is live right now

§5 (running economy) is in progress in `03 RESEARCH/running/`, with real
downloads and no `RESEARCH.md` yet. The two projects share a spine: §5
decomposes performance into V̇O₂max, fractional utilisation and economy; §6 is
about the size and uncertainty of a change to the economy term.

Two consequences for Stage 2:

- **The economy→performance transfer coefficient belongs to one of them, not
  both.** If §5 builds the decomposition, §6 should cite it rather than
  re-derive it.
- **The overlap is a real risk of two pages making the same point.** Whoever
  designs second should read the other's Stage 1 document first. On present
  evidence the clean split is: §5 owns *what determines performance*; §6 owns
  *how well any one term can be measured, and how much measurements of it
  disagree*.

## C8. What Stage 2 must decide, and what it must not assume

Not designed here. Recorded so Stage 2 starts from evidence:

- Whether an interactive is justified at all. §6's own brief warns that "a 3D
  model is not an argument" and that the strongest version may be four static
  figures and 600 words. Nothing found in Stage 1 requires interactivity: the
  spread is a static picture. **The burden is on Stage 2 to justify an app, not
  to justify its absence.**
- Whether the conditions gradient (C3) can be drawn at all without implying a
  fitted relationship it does not have.
- Whether the mass contradiction is one figure or one paragraph.
- What the page says about the shoe *this reader* should buy — the honest
  answer being that the literature cannot say, which is a finding and should be
  stated as one rather than omitted.

---

## Files in this folder

```
RESEARCH.md            this document
effects.json           20 published effect sizes + 5 meta-analyses, each with a DOI
check.py               computes the spreads, the gradient and the transfer coefficient
check_output.txt       its output, as run 2026-09-05
sources/
  cheah_2013_footwear_lca.pdf    MIT DSpace working-paper copy of the footwear LCA
  cheah_2013.txt                 extracted text, for the 65-parts check in A6
  wa_shoe_regulations_2026.pdf   World Athletics Book C - C2.1A, effective 2026-01-01
  wa_approved_shoes_2024-01-20.pdf   the approved-shoe list, checked for a spec schema
autopsy/
  rerun_fig.py             re-runs the retired figure's generator with OUT redirected here
  running_shoe.png         what it produced, 2026-09-05
  audit_pages.js           Playwright: does the page render, what are the contrast
                           ratios, does rotating the 3D model add anything
  audit_pages_output.txt   its output, as run 2026-09-05
  shot-page.png            the flat page outside site/, unstyled
  shot-3d-open.png         the 3D model, opening state
  shot-3d-rotated.png      the same model dragged ~90 degrees
```

## Sources

Bibliographic details for every paper cited above are in `effects.json`, one
per row, with DOIs. Article metadata was retrieved from **PubMed**. The papers
carrying the load in Part C:

- Hoogkamer W, Kipp S, Spiering BA, Kram R (2016). *Altered Running Economy
  Directly Translates to Altered Distance-Running Performance.* Med Sci Sports
  Exerc 48(11):2175–2180. [DOI](https://doi.org/10.1249/MSS.0000000000001012)
- Hoogkamer W, Kipp S, Frank JH, Farina EM, Luo G, Kram R (2018). *A Comparison
  of the Energetic Cost of Running in Marathon Racing Shoes.* Sports Med
  48(4):1009–1019. [DOI](https://doi.org/10.1007/s40279-017-0811-2) —
  correction, Sports Med 48(6):1521–1522,
  [DOI](https://doi.org/10.1007/s40279-017-0840-x)
- Hunter I, McLeod A, Valentine D, Low T, Ward J, Hager R (2019). *Running
  economy, mechanics, and marathon racing shoes.* J Sports Sci 37(20):2367–2373.
  [DOI](https://doi.org/10.1080/02640414.2019.1633837)
- Barnes KR, Kilding AE (2019). *A Randomized Crossover Study Investigating the
  Running Economy of Highly-Trained Male and Female Distance Runners in
  Marathon Racing Shoes versus Track Spikes.* Sports Med 49(2):331–342.
  [DOI](https://doi.org/10.1007/s40279-018-1012-3)
- Whiting CS, Hoogkamer W, Kram R (2021). *Metabolic cost of level, uphill, and
  downhill running in highly cushioned shoes with carbon-fiber plates.* J Sport
  Health Sci 11(3):303–308. [DOI](https://doi.org/10.1016/j.jshs.2021.10.004)
- Rodrigo-Carranza V, González-Mohíno F, Santos-Concejero J, González-Ravé JM
  (2020). *Influence of Shoe Mass on Performance and Running Economy in Trained
  Runners.* Front Physiol 11:573660.
  [DOI](https://doi.org/10.3389/fphys.2020.573660)
- Rodrigo-Carranza V et al. (2022). *The effects of footwear midsole
  longitudinal bending stiffness on running economy and ground contact
  biomechanics: A systematic review and meta-analysis.* Eur J Sport Sci
  22(10):1508–1521. [DOI](https://doi.org/10.1080/17461391.2021.1955014)
- Knopp M, Muñiz-Pardos B, Wackerhage H, Schönfelder M, Guppy F, Pitsiladis Y,
  Ruiz D (2023). *Variability in Running Economy of Kenyan World-Class and
  European Amateur Male Runners with Advanced Footwear Running Technology.*
  Sports Med 53(6):1255–1271.
  [DOI](https://doi.org/10.1007/s40279-023-01816-1)
- Joubert DP, Oehlert GM, Jones EJ, Burns GT (2024). *Comparative Effects of
  Advanced Footwear Technology in Track Spikes and Road-Racing Shoes on Running
  Economy.* Int J Sports Physiol Perform 19(7):705–711.
  [DOI](https://doi.org/10.1123/ijspp.2023-0372)
- Joubert DP, Sanders J (2026). *Effects of Advanced Footwear Technology in
  Trail Running Shoes on Running Economy.* J Strength Cond Res, ahead of print.
  [DOI](https://doi.org/10.1519/JSC.0000000000005553)
- Burns GT, Joubert DP (2024). *Running Shoes of the Postmodern Footwear Era: A
  Narrative Overview of Advanced Footwear Technology.* Int J Sports Physiol
  Perform 19(10):975–986. [DOI](https://doi.org/10.1123/ijspp.2023-0446)
- Ortega JA, Healey LA, Swinnen W, Hoogkamer W (2021). *Energetics and
  Biomechanics of Running Footwear with Increased Longitudinal Bending
  Stiffness: A Narrative Review.* Sports Med 51(5):873–894.
  [DOI](https://doi.org/10.1007/s40279-020-01406-5)
- Stephen CHN, Kelly LA, Schuster RW, Diamond LE (2025). *The effects of running
  shoe longitudinal bending stiffness and midsole energy return on oxygen
  consumption and ankle mechanics and energetics: A systematic review and
  meta-analysis.* J Sport Health Sci 14:101069.
  [DOI](https://doi.org/10.1016/j.jshs.2025.101069)
- Xiao Y, Hu X, Tian D, Qiu A (2025). *Effects of Advanced Footwear Technology
  on Running Economy and Endurance Performance: A Meta-Analysis.* Int J Sports
  Med 47(2):81–94. [DOI](https://doi.org/10.1055/a-2637-7283)
- Fuller JT, Bellenger CR, Thewlis D, Tsiros MD, Buckley JD (2015). *The effect
  of footwear on running performance and running economy in distance runners.*
  Sports Med 45(3):411–422. [DOI](https://doi.org/10.1007/s40279-014-0283-6)
- Guinness J, Bhattacharya D, Chen J, Chen M, Loh A (2020). *An Observational
  Study of the Effect of Nike Vaporfly Shoes on Marathon Performance.*
  arXiv:2002.06105. [DOI](https://doi.org/10.48550/arXiv.2002.06105) — code and
  data at `github.com/joeguinness/vaporfly`, no licence stated.
- Frederick EC, Daniels JT, Hayes JW (1984). *The effect of shoe weight on the
  aerobic demands of running.* In: Current Topics in Sports Medicine.
  Vienna: Urban & Schwarzenberg, 616–625. Origin of the ~1% per 100 g rule;
  not indexed in PubMed, cited here as the antecedent Hoogkamer 2016 measures.

For Part A and Part B:

- Cheah L, Duque Ciceri N, Olivetti E, Matsumura S, Forterre D, Roth R,
  Kirchain R (2013). *Manufacturing-focused emissions reductions in footwear
  production.* J Clean Prod 44:18–29.
  [DOI](https://doi.org/10.1016/j.jclepro.2012.05.037) — free copy at MIT
  DSpace is the February 2012 working paper, marked *do not cite without
  permission*.
- Curtis A, Hansson A (2019). *Examining the Viability of Corporate Recycling
  Initiatives and Their Overall Environmental Impact: The Case of Nike Grind
  and the Reuse-A-Shoe Program.* Case Studies in the Environment 3.
  [DOI](https://doi.org/10.1525/cse.2019.001974)
- World Athletics (2025). *Book C – C2.1A Athletic Shoe Regulations*, approved
  2 December 2025, effective 1 January 2026. Copy in `sources/`.

---

**Stage 1 ends here.** Nothing has been designed. Stage 2 is plan mode.

---

# What Stages 2 and 3 changed in this document's conclusions

Recorded here rather than silently corrected, because a provenance record that
describes a state the project has left is worse than none.

- **Twelve comparisons became thirteen.** Joubert et al. 2024 tested two AFT
  spikes and this memo carried only the larger. Both are in `data/studies.py`:
  dropping the smaller of a study's two arms is how a collected table starts
  flattering itself. The range is unchanged at 1.1%-4.2%.
- **"Four of twelve published dispersion" was wrong; it is six of thirteen.**
  Counted by `build_shoes.py` rather than by hand. Seven published nothing.
- **The predicted time range is 0.8%-3.0%, not 0.8%-2.9%.** The memo multiplied
  by the rounded coefficient; the build multiplies by 0.7027 and rounds once,
  at the end.
- **The transfer coefficient is no longer this project's to explain.** Between
  Stage 1 and Stage 3, §5 shipped `site/economy.html`, which derives the same
  0.7027 from the same two rows, reconciles it against the cost-of-running
  curve, and explains why the rate is not one. This page now cites that page
  and spends the number instead of re-deriving it, and `test_shoes.py` fails if
  the two ever disagree. The overlap this memo flagged in §C7 was real and
  arrived exactly where it was predicted to.
- **The autopsy's screenshots stayed in `03 RESEARCH/shoe/autopsy/`.** They are
  referenced from here and from `fig_shoes.py`, and are not shipped in the code
  archive.

Nothing in Part A, Part B or the evidence base of Part C changed.
