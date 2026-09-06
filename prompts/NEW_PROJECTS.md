# Six new projects — the shared method, then the briefs

Point the instance at this file and a section number: *"Read
prompts/NEW_PROJECTS.md, follow the shared method, and do section 3."*

---

# Where the work lives

**Corrected 2026-09-05.** The first version of this file had Stage 1 writing
into `00 PUBLISH`. That was wrong: research is not a site artifact, five of
these six may die, and `00 PUBLISH` was just cleaned of exactly this kind of
accumulation.

**Stage 1 and 2 happen outside the site repository:**

```
50 - ENERGY MODEL/
  03 RESEARCH/
    food/            RESEARCH.md, scratch data, notebooks, downloads
    beauty/
    neuron/
    continents/
    running/
    shoe/
```

Nothing in `00 PUBLISH` is touched. A project that dies in Stage 1 leaves a
folder in `03 RESEARCH/` and no trace in the site.

**Stage 3 only** creates a project folder inside `00 PUBLISH`, following the
convention already there — `climate-cost/`, `heat/`, `storage/`,
`longevity-quotient/`, `skyline/`, each holding its model, data, tests and
template, with the page it produces in `site/`. Move the research document in
at that point as the provenance record.

If `03 RESEARCH/` does not exist, create it. Work in your project's subfolder
and nowhere else.

---

# The shared method

Every project runs in three stages with **hard stops** between them. The stops
exist because the most expensive mistake available here is building a
visualiser before knowing what it should show — or building one for a claim the
data does not support.

## Stage 1 — Research and feasibility. Auto mode.

You are not designing or building. You are answering one question: **does this
project exist?**

- Find the primary literature and the primary data. Named datasets, named
  papers, with what each actually contains and what it costs to get.
- State the project's central claim in one sentence, then say what evidence
  would support it and whether that evidence exists.
- **Say plainly if it does not.** "The data to support this claim does not
  exist, and here is the weaker claim that is supportable" is a successful
  outcome of this stage, not a failure. `HANDOFF.md` §4: if a number cannot be
  sourced, the feature is not built and the page says why it is absent. That
  rule was written for this situation.
- List what a reader would already believe, and what this project could tell
  them that they do not already know. If the honest answer is "nothing", say so.

Write `03 RESEARCH/<project>/RESEARCH.md`. Keep every download, script and
scratch file in that same folder. Nothing goes in `00 PUBLISH`. Then stop.

## Stage 2 — Design. **Plan mode.**

Switch to plan mode for this stage — `Shift+Tab`, or start with
`claude --permission-mode plan`. Plan mode is right here precisely because it
cannot write files: it forces a proposal you approve before anything is built.

Propose:

- The one question the page answers, in the reader's words.
- What is computed, what is looked up, and what is assumed — the three
  categories the site labels separately.
- The figures: what each shows, why that encoding, what it is drawn at.
- Whether it needs an interactive at all, or whether static figures and prose
  do it better. **Most of these do not need an app.** An interactive earns its
  place when moving something teaches what a picture cannot.
- What it will not do.

Then stop for approval.

## Stage 3 — Build. Auto mode.

Follow the existing system, which is not up for revision:

- Figures through `sitefig.py` — the palette, the type scale, the grid, the
  audits. Never a hand-assembled sheet; that fault produced three separate bugs
  in `energy_model_chart.png` alone.
- One page in `site/`, following the current page skeleton. An interactive, if
  Stage 2 justified one, as a separate `*-app.html` with its own inline CSS.
- A generator in the repo for every figure and payload. **An asset nobody can
  regenerate is how a fabricated number survived on this site for weeks.**
- Every number generated, never typed. Every assumption labelled *assumed*.
  Every source named in a `source=` field, not only in prose.
- The nav via `rebuild_nav.py`'s `NAV` list; the archive via
  `rezip_downloads.py`; `python bust_cache.py` before publishing.
- Tests: the page rig, the layout suite, the generator drift check, and at
  least one test specific to this project's own failure mode.

---

# Models and modes

| Stage | Mode | Model |
|---|---|---|
| 1 Research | auto | **Fable** for §1, §5; **Opus 5** for §2, §3, §4, §6 |
| 2 Design | **plan** | Opus 5 |
| 3 Build | auto | Fable |

Fable for research where the work is a long literature and data hunt with a
real chance of a negative result — §1 and §5 are both that. Opus 5 where the
data source is already known and the job is to characterise it. Fable for every
build, because these are long sessions where investigating before acting is the
whole game.

---

# 1. Beauty in research

**The claim.** Which animals get studied and funded tracks how appealing they
are to humans, not how endangered or ecologically important they are — and that
misallocation has consequences.

**This one has real literature and real data, and it is the strongest of the
six.** Taxonomic bias in conservation funding and research effort is an
established finding with named papers behind it. Start from the work on
charismatic megafauna, taxonomic bias in research output, and the mismatch
between conservation spending and extinction risk. Find the actual papers; do
not take my summary as the citation.

**The data that could carry it.** IUCN Red List status by species and taxon.
Publication counts by taxon. Conservation funding allocations where they are
public. Zoo and captive-collection composition. Some of this is free and clean;
some is not. Find out which before designing anything.

**The trap, and it is the whole project.** "Beauty determines funding" is a
causal claim, and what the data supports is a correlation between charisma
proxies and effort. Body size, range size, discovery date and human proximity
all confound it. **Do not let the visualisation assert cause where the data
shows association.** The honest version — "here is the gap between what is
endangered and what is studied, and here is how much of that gap size and
charisma account for" — is more interesting than the loud version, and it is
the one you can defend.

The second half of the brief — "how it has and will harm us" — is a forecast.
Say what is documented (species lost while unstudied, taxa with no baseline
data) and label the rest as argument, not finding.

# 2. A neuron, visualised

**The problem with this brief as stated.** "A neuron" is a subject, not a
question. Stage 1's job is to find the question. Candidates: how does a signal
actually travel; why does the morphology look like that; what is the real
scale relationship between a soma, a dendritic tree and an axon; how much of
what a textbook diagram shows is schematic rather than measured.

**The data exists and is excellent.** Reconstructed neuron morphologies are
published as digital tracings in standard formats, in large numbers, free.
The Allen Brain Atlas is already in this repository's stack — the atlas model
uses it for behaviour nodes — so there is precedent for the ingest.

**The opportunity.** Almost every neuron diagram a reader has seen is
schematic: proportions wrong, branching invented, scale absent. A visualisation
built from a real traced morphology at true proportions would show something
they have not seen, and the gap between the textbook picture and the real one
is itself the story.

**The trap.** A rotating 3D neuron is a screensaver. If the interactive does not
answer a question that a still figure cannot, build the still figure.

# 3. The science of modern food

**The claim.** Industrially formulated foods combine fat, sugar and salt in
proportions that rarely occur in whole foods, and those combinations are
engineered rather than incidental.

**This is more tractable than it sounds, because the definition has been
formalised.** There is published work defining hyperpalatable foods
*quantitatively* — thresholds on the proportion of energy from fat, sugar and
sodium — and applying those definitions to national food-composition databases.
Find that work. It turns a vague thesis into a computable one, which is what
this site does well.

**The data.** National food-composition databases are free and comprehensive.
Every product's macronutrient and sodium content is in them, which means the
whole analysis is reproducible from a public source — the strongest position
any project on this site can be in.

**The figure that probably carries it.** Whole foods and formulated foods
plotted in the same fat–sugar–salt space, showing that formulated products
occupy a region almost nothing natural does. If that separation is real, it is
the entire argument in one picture. **Check whether it is real before
committing to it.**

**The trap.** "Engineered to be addictive" is a claim about intent and about
addiction, and both are contested. Stick to composition, which is measured, and
label everything past it as interpretation.

# 4. How will the continents shift?

**The claim.** Plate motion is measured, it is extrapolable, and where the
continents end up is a question with real but bounded answers.

**The data.** Present-day plate velocities are measured to high precision and
published as standard models. Past reconstructions are open, with free software
and datasets built for exactly this. Deep-future projections exist as a small
number of named competing scenarios rather than one answer.

**The honest structure, and it is what makes this worth doing.** Three regimes
with three different epistemic statuses: the measured present, the reconstructed
past, and the projected future where the scenarios genuinely disagree. Most
popular treatments blur them. Showing the disagreement — two or three named
futures side by side, with what distinguishes them — is the version only a site
with this site's rules would build.

**The trap.** Any single future map presented as *the* answer. The uncertainty
is the finding.

# 5. The mechanics of running economy

**The claim.** Marathon performance is a small number of physiological terms
multiplied together, and improving any one of them compounds with the others —
a flywheel rather than a list.

**This is the one where you know most, which is the risk.** Everything must be
sourced anyway, and where a number is from your own training log it is labelled
as one datum, not as evidence.

**The framework.** Endurance performance decomposes into maximal oxygen uptake,
the fraction of it sustainable at race pace, and running economy — the oxygen
cost of a given speed. That decomposition is published and named; find the
paper, use its form, cite it. Economy itself decomposes further into terms that
are also measured in the literature. That nesting is the onion the brief asks
for, and it is real rather than invented.

**Copyright, and this is a hard rule.** *Advanced Marathoning* is a copyrighted
book. Its tables, its plans and its specific prescriptions cannot be reproduced,
paraphrased closely, or rebuilt as a calculator. Build from the primary
literature the book itself draws on. If a number's only source is a training
book, it does not go on the page.

**The interactive, if Stage 2 justifies one.** This is the strongest candidate
of the six for genuinely needing interactivity, because compounding is the thing
a reader will not believe from a static figure: move economy 3% and watch what
happens to a projected pace, then move two terms and see that the result is not
their sum. That is a mechanism you can only feel by moving it.

**The trap.** A pace calculator. There are hundreds and they are all the same.
The point is the compounding, not the arithmetic.

# 6. The shoe project, redone

**Prior work exists.** `unpublished/running-shoes.html` and
`unpublished/running-shoes-app.html`, plus shoe outline functions in
`build_climate_figures.py` — `HANDOFF.md` notes the flat figure and the 3D model
were meant to be the same shoe and that both must change together. Read all of
it before deciding anything.

**Stage 1 here is different: it is an autopsy first.** Before researching the
subject, work out why the first version reads as slop. Was it the 3D model, the
palette, the type, the claims, the structure — or was the project never
answering a question? Write that down. You now have a site-wide criteria list
and a set of audits that did not exist when it was built; run them against it.

Then decide whether the project is worth rebuilding at all, and say so honestly
if it is not. **Retiring it a second time is a legitimate outcome.** The
bookshelf was archived tonight and the site is better for it.

**If it is worth rebuilding**, the subject has real literature: the measured
effects of shoe mass on oxygen cost, the carbon-plate and foam studies with
their published effect sizes, and the running-economy framing from §5 — the two
projects share a spine, and doing §5 first may make this one obvious.

**The trap.** The first version's failure is a warning that a 3D model is not an
argument. If the strongest version is four static figures and 600 words, build
that.

---

# What kills a project

Any of these, found in Stage 1, and you stop and say so:

- The central claim needs data that does not exist or is not obtainable.
- The data exists but supports only a much weaker claim, and the weaker claim is
  not interesting.
- The honest version is something a reader already knows.
- The only sources are copyrighted works whose content cannot be reproduced.

Reporting one of these is worth more than building a page that hedges its way
around it. The single most valuable thing found on this site in the last week
was a number that should never have been published.
