# Phase 4 — the hero, three broken images, and everything still open

The site is live. Mirror commit `085d3d2`, published 22:32 on 2026-09-04. Every
change here republishes, so the archive-and-dry-run discipline still applies and
the rollback hash for the current live state is in `DESLOP_3D_2026-09-04.md`.

Four parts, **A through D, with a hard stop after A**. A is what a reader can
see; B and C are what a reader could catch you on.

---

# Part A — the three things that are visibly wrong right now

## A1. The home-page hero is the wrong kind of picture

Option (b) shipped and it is not right. Two problems, one of them structural.

**The surface problem:** on paper, dark dots on a white ground read as speckle.
The dark version at least had a metaphor — bright points on black are obviously
"where the energy is". Inverted, that is gone, and because land and sea are both
paper the sphere does not resolve as Earth until you find the coastlines.

**The real problem:** a globe of dots is a **map**, not a picture of a system.
It shows where about 70,000 things sit. It shows nothing about layers, weights,
direction, ranks or propagation — which is the entire claim of the project. The
home page's first object should say *this is a model*, not *this is a map*.

The answer is already written down and was never built.
`DESIGN_AUDIT_EXTERNAL_2026-08-30.md`, "What's missing" item 1:

> A layer diagram on `atlas.html`. The page describes nine layers, their node
> counts, and which links are one-way, in a table and four paragraphs. A single
> vertical schematic — layers as bands, arrows for direction, climate/events
> shown as one-way sources — would let a reader hold the architecture in their
> head before the prose asks them to use it. This is the highest-value 200 lines
> of SVG on the site; `model.html`'s "One node, one step" proves you can draw it.

Build that, from the live payload, through `sitefig.py`, and make it the home
page's hero. It states the architecture, it is drawn for paper, it carries no
three.js, and it is the one picture that answers "what is this."

Requirements:

- Every number on it comes from the payload, not from prose. Node counts per
  layer, and the exogeneity rank that decides which links are one-way.
- The one-way relationships must be visible as one-way. `HANDOFF.md` §6 has the
  rule: sun 0, insolation 1, weather 2, climate 3, event 4, everything else 5;
  two-way only within a rank.
- It must survive at 390px or carry a stated narrow variant.
- Generator in the repo, named in the page's provenance, in the generator check.

**Keep the globe.** Move `hero_globe.png` to `atlas.html`, where a map is the
right object and the page is about the thing it maps. Do not delete it.

**Stop after this and show me before wiring it in.** This is a new figure and a
new first screen; I want to see it as an image before it becomes the page.

## A2. The bookshelf card is a screenshot of the tool

`index.html`'s bookshelf thumbnail shows the app's control panel — "THE SCREEN",
"THE SHELF", "Walnut" are legible down the left edge. The card should show the
wallpaper the tool produces, not the tool that produces it.

Check every app card for the same mistake while you are there.

## A3. The model chart has three faults, one introduced today

`energy_model_chart.png` on the home page:

1. **It is soft.** Text is blurry at display size, worst on the mono panel.
   Every other figure got one point per CSS pixel and two bitmap pixels per
   point. Find out why this one did not — it may be the last figure on the old
   geometry, in which case check whether anything else shares its path.
2. **The donut legend collides with the panel title beneath it.** "everything
   else — 1,518" is struck through by "How far the 60 prepared changes travel".
   Your layout audit reports 0 problems on this figure, so **the audit does not
   see cross-panel overlap.** Fix the figure and the check; the check is the
   more valuable half.
3. **Panel titles disagree inside one figure.** "Link weights" is sans, "How far
   the 60 prepared changes travel" is mono. `sitefig.panel()` was supposed to
   make every panel label mono furniture. One panel did not go through it —
   drift introduced this afternoon, inside the pass that introduced the rule.
   Fix it, then make `panel()` the only way a panel can be labelled so it cannot
   recur.

Also reconsider the eleven-category colour assignment on the node bars. Climate
at near-black among the tints reads as a different kind of thing rather than one
more category. Eleven categories is more than this palette can separate — say so
and find another encoding rather than stretching it further.

## A4. The page has two left edges

On `index.html` the section headings, the horizontal rules and the figure
captions all align to the text track. The cards and the wide figures break out
past it, to the wide track. So "Energy", the rule above it, and "The model at a
glance…" start at one x, and every card starts at a noticeably smaller one, and
nothing lines up down the left of the page.

That breakout made sense when the gutters held marginalia. **The home page's
marginalia is now blank** — Part 6 of the last pass — so the cards are breaking
out into empty space for no reason a reader can see, and paying for it with a
broken left edge.

Fix the alignment, and decide it rather than nudging it:

- Either the cards come back to the text track on pages with no marginalia, so
  the page has one left edge, or the headings, rules and captions break out with
  them so the whole page shares the wider one. Pick one and say why.
- Whatever you choose, **the left edge of every block on a page must be the
  same** unless something is deliberately in a gutter. Add that to
  `test_layout.js`: collect the left edge of every direct child of `main`,
  excluding asides, and fail on more than one distinct value per page.
- Check the same thing on the pages that *do* have marginalia. Three tracks is
  fine; three left edges is not.

Second, smaller: inside the cards, the figure occupies about a third of the
card's width and the text the rest, and neither fills its own column's height,
so the space inside a card reads as leftover rather than as rhythm. Measure the
image column against the text column at 1440 and decide a ratio deliberately
rather than letting the image's natural size choose it.

---

# Part B — the atlas claims

`ATLAS_CLAIMS_TODO_2026-09-04.md`, all six, plus the two structural ones. Same
rule as every claim fixed today: **where a claim cannot be made true, change the
claim, not the data.**

1. "Settles in between twenty and fifty steps" (`atlas.html`, twice). Actual
   range across the 60 scenarios is 5 to 42, and 14 settle under 20.
2. "Every node holds one measured quantity." 1,142 consumer nodes, all 24
   behaviour nodes and 2,896 ports do not.
3. `model.html` §4 says "(1 − inertia)"; the code is (1 − 0.6·RES). The inertia
   and weight tables give single values where the code uses ranges. 8,733 of
   9,259 events carry no damage cost.
4. "Moves one other node" moves none. "Five orders" is 4.6. 25 nodes sit at 0,0.
5. §7's instructions run the retired July build. Say so plainly or remove them.
6. The engine-parity test named in `HANDOFF.md` §6 does not exist. Either write
   it — `atlas-app.js` against `build_throughlines.py`, agreement to a stated
   tolerance — or strike the claim that parity is verified. I would rather have
   the test.

Every one of these is generated text where possible, not hand-corrected, so the
next payload change carries them. `update_page.py` on longevity is the pattern.

---

# Part C — the demand-response bug

`ATLAS_DEMAND_RESPONSE_2026-09-04.md`. The 1,144 negative consumer→district
links are swamped by their paired +0.50 edge, so pushing a consumer up pushes
its district up. A documented behaviour of the model does not happen.

This is a model bug, not a copy bug, and it is the one item in this brief that
might change a published number. Investigate before proposing: is the pairing
intentional and the sign convention wrong, or is the negative edge simply too
small to matter? Do not change the engine until you have told me which, because
`HANDOFF.md` §6 lists four properties of that engine that took a long time to
get right and warns against undoing them.

If it is fixed, both engines change together and parity is re-verified.

---

# Part D — housekeeping

- `climate-cost/test_scene.js` cannot run: it needs jsdom, which is not
  installed beside it. An unrunnable test is indistinguishable from a passing
  one. Install it or vendor it, and make the suite fail loudly rather than skip
  when a dependency is missing.
- Longevity's §9 leftovers: stale `?v=` stamps, the unknown-taxon fallback, the
  years-mode log floor, the eight high-side demotions flagged as probably real.
- Skyline's leftovers: the scroll affordance, and `build_skylines.py` remaining
  untestable without a fresh Wikidata pull. Say what a fresh pull would take.
- `HANDOFF.md`: record that the museum generator survives under
  `dumpNew/PyProjects/` but its `PUBLISHING-NOTE.md` does not, so the image
  rights reasoning that kept it unpublished is gone. A missing warning is more
  dangerous than a missing feature.

---

## Rules, unchanged

- Fix the generator or template first, prove a rebuild is a no-op, then ship.
- Compute every contrast ratio. AA or better. 12px floor.
- `python bust_cache.py` before any publish.
- All suites plus the generator check, at 1440 and 390.
- `./publish.sh --dry-run` from Git Bash, show me, then push on my word.
- Where you think this brief is wrong, argue it. Eight of its predecessors'
  premises did not survive contact today, and saying so each time is why the
  work held up.

## Write-up

`PHASE4_2026-09-04.md`. Per part: what changed, what you found that this brief
did not anticipate, and what you decided not to do and why.
