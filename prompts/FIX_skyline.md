# Fix — skylines, played

Acts on `AUDIT_SKYLINE_2026-09-04.md`, which you wrote. Read
`prompts/_HOUSE_RULES.md` and the **shared rules** at the bottom.

## The blocking one: the page's distinguishing claim is the thing that is false

`skyline.html` says what is measured, what is assumed and what is invented are
each labelled. Your audit found the opposite in two places:

1. **Panorama data labelled "Measured" that the app never reads.** Occlusion
   and off-axis silence are described as properties of the instrument. The app
   is tested to never be silent at any bearing. A label asserting provenance
   for behaviour that does not exist is worse than no label.
2. **The mapping is never stated.** Per-city normalisation, timbre, drone and
   the filter chain are all inventions — choices, not measurements — and none
   of them appears in the sidebar or on the page.

Fix the claim and the data together: either the app reads the panorama data and
behaves as described, or the data and its label come out. Do not leave a
"Measured" tag on something inert. Then state the mapping where a reader will
find it, and mark every part of it invented.

## The one that will annoy you most

**The chord filter collapses 8 modes into 5 sounds.** Hijaz plays as something
else; Tel Aviv is acoustically identical to Vienna, Chicago and Austin to Hong
Kong, Madrid to Auckland. The keys are sourced and tiered — that work is real —
and then the filter throws the distinction away at the last step.

This is a substantive bug, not a labelling one: the project's premise is that
each city sounds like itself. Either the filter preserves the modes or the page
stops claiming 27 distinct instruments. Diagnose before deciding; if the fix is
cheap, fix it.

## The rest

- **The 55 m floor on the ring is never shown.** Supplemented cities say
  "Wikipedia, Wikidata overridden above a floor" — show the floor.
- **The motion contract is absent from the app entirely.** This matters more
  than it did yesterday: the site's manual motion toggle was removed and
  `prefers-reduced-motion` is now the only gate. An app that ignores it has no
  gate at all. Wire it up. Note that reduced motion and reduced *audio* are
  different preferences — say what you decided.
- **54 sub-12px elements.** The site now has a seven-step type scale with a
  12px floor. Bring the app's chrome onto it.
- **Play button still 2:1-ish on `#spin.on`** — below the 3:1 UI floor.
- **No text form of what is sounding**, so there is no path through this app
  for a reader who cannot hear. Your report called this out; propose something
  proportionate rather than a full transcript.

## Two corrections to my brief

I told you the generator was missing entirely. **It is in
`site/downloads/skyline-code.zip`** — you found it, and you were right to check
there. I searched for a folder name and never looked in the directory the
site's own Code page exists to publish. Only the raw Wikidata pull is genuinely
absent, so the 24 Wikidata cities cannot be rebuilt from scratch; everything
else can.

That has a consequence for this job: **the zip's `template.html` is three
palette lines behind `site/`.** Reconcile it before you change anything, or
your fix ships and the next rebuild reverts it. This is the same trap that has
now appeared in longevity, climate-cost and the nav.

---

## Shared rules — every fix brief in this set

- **Fix the template or generator first**, then the shipped file, then prove a
  rebuild is a no-op. Shipped-vs-template drift is the most common defect class
  in this repository; do not add an instance while fixing one.
- **Do not touch** `site/index.html`, `site/style.css`, `bust_cache.py`, or
  anything outside your own app and its page. A separate sweep collects the
  home-page copy, the cache stamp and the commit.
- **Do not run `bust_cache.py`. Do not commit. Do not publish.**
- Where a claim cannot be made true, **change the claim, not the data**.
- Recompute every contrast ratio you touch. AA or better.
- Write `FIX_SKYLINE_2026-09-04.md` at the repo root: what changed, what you
  decided about the mode filter and why, the rebuild-is-a-no-op proof, and
  anything left undone.
- Stop when it is written. Give me the local URL.
