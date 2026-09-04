# Phase 3b — fix the layout and type, then re-render everything

Two parts, **in this order**. The order is not negotiable: the figures must be
rendered against the final type scale and the final measure, or you will render
34 of them twice.

---

# Part 1 — four fixes, before any figure is touched

## 1. The moving backgrounds are broken

`hero.js`, `hero-gl.js` and `bgloop.js` are what still move, and they were built
to draw luminous data on a black ground. On the Yacht club paper they are
wrong. Diagnose each properly rather than tinting it until it stops looking
bad: what does it draw, what is it drawing it on now, and does it still mean
anything on a light ground?

Some of this may be better deleted than fixed. `bgloop.js` in particular should
have to justify its existence against the same question you applied to the five
scripts you already removed: **what does a reader lose if it goes?** If the
answer is nothing, remove it and say so.

The hero globe is different — it is the home page's one real object and it
should survive. Make it work on paper.

## 2. Remove the motion toggle, keep the motion contract

Delete the `Motion: on` button from the footer of every page. It is `hidden` in
the markup and unhidden by `motion.js`; take out both the markup and the
unhide.

**Do not remove reduced-motion support.** These are different things. Whatever
still animates after fix 1 must still stop for
`prefers-reduced-motion: reduce`, via the existing pre-paint `data-motion`
contract. Removing the manual switch is a UI decision; removing the
accessibility behaviour would be a regression, and someone with a vestibular
disorder does not get a switch. If the honest outcome of fix 1 is that nothing
moves any more, then say so and remove `motion.js` too — but only then.

## 3. The measure is columny, and the cause is structural

`main` reserves `minmax(0, calc((var(--wide) - var(--text)) / 2))` on each side
of the text track — about 250px a side at current values, plus 150px outer
tracks. That was correct when every page had marginalia. **3a emptied the
marginalia on library, atlas, model and code**, and on those pages the prose is
now a ~640px column floating inside 1440px of shell with 800px of reserved,
empty track around it. It reads as a phone column pasted onto a desktop.

Fix the structure, not just the number:

- Pages that still carry marginalia keep the three-track grid — the gutters are
  earning their space there.
- Pages that carry none should not reserve tracks for it. Give them a wider
  measure, or a two-track layout, or collapse the reserved gutter to the outer
  track. Your call; say what you chose and why.
- Separately, `--text: min(68ch, 100%)` at a 16–17px base is at the conservative
  end for a technical page set in a sans. Try a wider measure and a slightly
  larger base together — they compound. Judge it on `model.html`, which is the
  longest prose on the site.
- **Do not fix this by centring a narrow column in more whitespace.** The
  complaint is that the desktop layout looks built for a thumb. The test is
  whether a desktop reader feels the page was laid out for the screen they are
  on. Phone must still work: at 390px the text track goes edge to edge and
  nothing above changes that.

Show me the measure in characters, not just pixels, at 1440 and at 390.

## 4. Type scale — make it a scale

There are still three roles at 11px, which is under the 12px floor your own
audit flagged, and the sizes are a mix of hardcoded px, `clamp()` and shorthand
`font:` declarations that grep cannot even count honestly.

Define one documented scale — a base and a fixed ratio, six or seven steps —
put every step in a token, and set every role from a token. Nothing under 12px
survives. If a role genuinely needs to be smaller than the smallest step, that
is a signal the role is wrong, not that the scale is.

Write the scale into the stylesheet header as a table so the next person can
see it rather than infer it.

## Stop here and show me

Part 1 is a stopping point. I want to see the layout and type settled before
34 figures are rendered against them. Give me the URLs.

---

# Part 2 — re-render everything, after I approve Part 1

## The inventory

34 PNG/WebP, 6 MP4, 6 posters, all currently dark-ground on a paper page. The
stale list at the top of `DESLOP_3A_2026-09-04.md` is the manifest.

## Render against the final design, not the old one

Every figure gets the Yacht club palette **and** the new type. That means the
matplotlib font stack matches the site's face rather than defaulting to Segoe
or DejaVu, and axis and annotation sizes are set from the same scale as the
page. A figure whose labels are a different typeface from the caption beneath
it is the tell that started this whole pass.

The hex constants live in `build_throughlines.py` (`BG`, `INK`, `DIM`, `RULE`,
`KCOL`), `heat/figstyle.py`, `storage/figstyle.py` and the sibling builders.
**Put them in one place** rather than editing the same five constants in six
files — a shared figure-style module that reads the palette once. This is the
same class of defect as the two engines that must agree; do not create a
seventh copy.

## Fold in the findings that need this pass anyway

You are touching every figure. These are cheaper now than ever again:

- **F3, weight.** Figures are downloaded at 3–8× their rendered size and six
  pages exceed the 600 KB discipline. Render at the geometry they are actually
  displayed at, with fonts sized for that. Your `DESLOP_WEIGHT_2026-09-04.md`
  is the plan; execute it here.
- **F4, phone legibility.** Every figure is illegible at 390px. Decide per
  figure whether it needs a narrow-viewport variant, a simplified version, or
  is honestly desktop-only and should say so.
- **The heat region fill.** You removed it in the trial render and left it in
  the shipped builder, correctly deferring to this phase. Remove it in the
  builder now. Direct labels and the named crossing point carry that figure.

## The six MP4s

Decide and argue rather than assuming. They are ~1.5 MB total, they duplicate
their own poster frames, and re-rendering them is the most expensive item in
this phase for the least certain gain. Options: re-render, drop to poster
stills, or drop entirely. Tell me what you recommend and why before doing it.

## Rules

- Every builder must still report **0 layout problems** from its `audit()`.
- Recompute every contrast ratio including text over the new figures.
- `python bust_cache.py`. Remember it does not stamp assets referenced from
  CSS, so anything referenced that way needs a new filename.
- Both test suites pass.
- Do not publish. That is 3c, along with the five `*-app.html` files.

## Write-up

`DESLOP_3B_2026-09-04.md`: the type scale table, the measure before and after
in characters, what happened to each moving background and why, the figure
inventory with before/after bytes, per-page weight against the 600 KB line, and
your MP4 recommendation with its reasoning.
