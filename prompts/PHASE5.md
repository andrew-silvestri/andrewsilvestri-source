# Phase 5 — the bookshelf app, the card format, and everything still open

Five parts. **Hard stops after Part 1 and after Part 2a.** Parts 3 to 5 are the
outstanding work from Phase 4's brief, unchanged and still owed.

The site is live. Archive and dry-run before anything goes up; the rollback
hash for the current live state is in the most recent write-up.

---

# Part 1 — archive the bookshelf

The Goodreads wallpaper app comes off the site. Not deleted — retired, the way
`unpublished/` already holds `dac.html`, `holdup.html`, `beans.html` and the
running-shoes pages.

What that means, and check for more:

- `desktop.html` and `bookshelf-app.html` move to `unpublished/`, with their
  assets (`bookshelf-demo-covers.webp`, `bookshelf-demo-shelf.webp`, the new
  wallpaper thumbnail).
- The card comes off `index.html`. **The home page is now five projects, not
  six** — that changes Part 2's mock-ups, so do this first.
- The nav: "The bookshelf" comes out of the `Others` dropdown. That is a change
  to `rebuild_nav.py`'s `NAV` list, not to the pages — and then run the
  generator and diff, per constraint 3.
- `bookshelf-code.zip` off `code.html` and out of `site/downloads/`. Keep the
  zip in `unpublished/` so the source survives.
- `sitemap.xml`.
- `test_layout.js`'s card assertions now run over five cards.

**It is live right now**, so `desktop.html` and `bookshelf-app.html` will start
404ing. For a personal site that is usually fine, but say so explicitly in the
write-up rather than discovering it later — and check nothing else on the site
links to either page before you pull them.

Two things to record while you are in there:

- In `unpublished/`, a short note saying what this was and why it was retired,
  next to whatever convention the existing retired pages already use. Match
  their convention rather than inventing one.
- In `HANDOFF.md`: the museum sibling survives under `dumpNew/PyProjects/` but
  its `PUBLISHING-NOTE.md` does not, so the image-rights reasoning that kept it
  unpublished is gone. Someone will otherwise find a working generator with no
  visible reason not to ship it. A missing warning is more dangerous than a
  missing feature.

One consequence worth noticing rather than mourning: the privacy sentence we
spent three rounds on — "nothing else from your export", the scope that kept
going missing — is now moot. The claim that was hardest to state truly is gone
because the thing it described is gone. That is a legitimate way to resolve a
claim, and it is worth a line in the write-up alongside the others.

---

# Part 2 — the card format

## The problem, stated properly

Four passes have now adjusted the card — the crop, the aspect ratio, the dead
space, the alignment — plus a copy trim to fit a text budget. Each fixed what it
was pointed at. The format is still wrong, and the reason is structural:

**A 271px image cannot hold its own against a five-line paragraph.** The image
reads as a stamp beside the text rather than as the thing being shown, the
paragraph does work that belongs on the project page, and six of these stacked
vertically is one module tiled — which is a finding from the very first audit
that was never actually addressed, only restyled.

The copy budget is the tell. When a layout can only work if the prose is cut to
215 characters, the layout is choosing the writing. That is backwards for a site
whose prose is its best asset.

## 2a. Mock two directions, then stop

Do not implement. Render both, at 1440 and 390, and show me.

**(a) Figure-led.** One figure per project at the full text-column width — the
same 714 the hero uses — with the kicker and title above it and **one sentence**
beneath. The figure is big enough to actually read. The sentence is a hook, not
a summary; the project page carries the explanation. No copy budget, because one
sentence always fits.

**(b) Index.** No figures on the home page at all. Kicker, title, one sentence,
rule. The home page becomes an index and the figures live where they are
explained. This is the strongest subtraction available and the most consistent
with everything else this pass has done; it is also the one that risks making a
chart-dense site look plain on its first screen.

For each, show me what happens to the six existing paragraphs. Both directions
mean writing one sentence per project where there are now three or four, so
draft them — that is real work and I want to see it before choosing, not after.

Where you think a third direction beats both, mock that too and argue for it.

## 2b. After I choose

Implement to the card spec's successor. Rewrite `THE CARD SPEC` in `style.css`
and `HANDOFF.md` §4 to describe whatever wins, and delete what it replaces
rather than leaving both. Update `test_layout.js` to assert the new shape.

**The allometry sentence is the test case.** "How long an animal lives, against
how long an animal of its size should live. Body mass predicts lifespan across
fourteen orders of magnitude; the quotient is what is left once that
relationship is divided out." Two sentences doing two jobs — the first says what
the quotient is, the second says how it is derived. On the home page it needs to
be one sentence that makes someone click. Draft it; the derivation belongs on
`longevity.html`, which already says it.

---

# Part 3 — the atlas claims

`ATLAS_CLAIMS_TODO_2026-09-04.md`, all six. Same rule as every claim fixed in
this project: **where a claim cannot be made true, change the claim, not the
data.** Generate the text where possible rather than hand-correcting it, so the
next payload change carries it — `update_page.py` on longevity is the pattern.

1. "Settles in between twenty and fifty steps" (`atlas.html`, twice). The actual
   range across the 60 scenarios is 5 to 42, and 14 settle under 20.
2. "Every node holds one measured quantity." 1,142 consumer nodes, all 24
   behaviour nodes and 2,896 ports do not.
3. `model.html` §4 says "(1 − inertia)"; the code is (1 − 0.6·RES). The inertia
   and weight tables give single values where the code uses ranges. 8,733 of
   9,259 events carry no damage cost.
4. "Moves one other node" moves none. "Five orders" is 4.6. 25 nodes sit at 0,0.
5. §7's instructions run the retired July build. Say so plainly or remove them.
6. The engine-parity test named in `HANDOFF.md` §6 does not exist. Write it —
   `atlas-app.js` against `build_throughlines.py`, agreement to a stated
   tolerance — or strike the claim that parity is verified. I would rather have
   the test; the two engines existing and having to agree is the single most
   load-bearing fact about this model.

---

# Part 4 — the demand-response bug

`ATLAS_DEMAND_RESPONSE_2026-09-04.md`. The 1,144 negative consumer→district
links are swamped by their paired +0.50 edge, so pushing a consumer up pushes
its district up. A documented behaviour of the model does not happen.

This is a model bug, not a copy bug, and the only item in this brief that can
change a published number. **Investigate and report before changing anything.**
Is the pairing intentional with the sign convention wrong, or is the negative
edge simply too small to matter? `HANDOFF.md` §6 lists four properties of that
engine that took a long time to get right and warns against undoing them, so
this is exactly the place not to guess.

If it is fixed, both engines change together and parity is re-verified — which
is another reason Part 3 item 6 comes first.

---

# Part 5 — housekeeping

- `climate_allocation_bases.png` is a 1140 render shown at 714 — the opposite of
  the softness fixed in Part A. Redraw at its display width.
- `climate-cost/test_scene.js` cannot run: it needs jsdom, which is not
  installed beside it. An unrunnable test is indistinguishable from a passing
  one. Install or vendor it, and make the suite fail loudly rather than skip
  when a dependency is missing.
- Longevity's §9 leftovers: stale `?v=` stamps, the unknown-taxon fallback, the
  years-mode log floor, the eight high-side demotions flagged as probably real.
- Skyline's leftovers: the scroll affordance, and `build_skylines.py` remaining
  untestable without a fresh Wikidata pull — say what a fresh pull would take.

---

## Rules, unchanged

- Fix the generator or template first, prove a rebuild is a no-op, then ship.
- Compute every contrast ratio. AA or better. 12px floor.
- `python bust_cache.py` before any publish.
- All suites plus the generator check, at 1440 and 390.
- `./publish.sh --dry-run` from Git Bash, show me, then push on my word.
- Where you think this brief is wrong, argue it. Nine of its predecessors'
  premises did not survive contact, and saying so each time is the reason the
  work held.

## Write-up

`PHASE5_2026-09-04.md`. Per part: what changed, what you found that this brief
did not anticipate, and what you decided not to do and why.
