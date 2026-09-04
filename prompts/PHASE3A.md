# Phase 3a — Option B, Yacht club, and killing the sys-log

Decisions made. This brief is the first of three parts; **3a is CSS and markup
only.** Figures come in 3b and the apps in 3c. Do not run ahead.

## What was decided

1. **Option B, "the instrument."** Self-hosted IBM Plex Sans + Plex Mono, margin
   scenes converted to readable sticky marginalia, sys-log becomes a readout
   strip, cards become rows. Fold it into `site/style.css` itself.
2. **Yacht club, single theme.** `#F2F0EF` off-white ground, `#BBBDBC` grey
   surfaces, `#245F73` deep blue and `#733E24` brown as accent and data.
3. **The sys-log block comes off the home page** entirely.

Light/dark is deferred, not cancelled — see "leave the door open" below.

## Two things about this palette you need to handle

**It has no ink.** Four swatches and none of them is a body-text dark. The blue
reaches 6.25:1 on the ground and the brown 7.57:1, both technically passing, but
setting long-form prose in a saturated hue is tiring. Import one near-black
neutral. `#241E1A` gives 14.49:1 and keeps the palette warm; `#1C2226` gives
14.15:1 and runs cool. Pick one, say why. Muted text needs the same treatment —
`#6B6560` measures 5.06:1, `#7A7570` only 4.01:1 and fails.

Verify all of this yourself. Compute, do not trust the numbers above.

**The site becomes light-ground.** The current stylesheet's own header says
"dark ground, luminous data" and calls light mode "a deliberate second-class
citizen." That inverts now. Every assumption built on a dark ground — the
radial washes on `body::before`, the node/edge SVG tile, the scene tinting —
has to be rethought rather than recoloured. A wash designed to stop black being
a void does nothing on paper.

## The figures will look wrong, and that is expected in 3a

Roughly thirty PNGs and six MP4s carry dark backgrounds baked in by the Python
builders. In 3a they will sit on the new light pages as black rectangles. **Do
not regenerate them in this phase** and do not try to patch around them with
CSS filters. Instead:

- Leave them in place.
- Add a short note at the top of your write-up listing exactly which assets are
  stale, so I do not mistake the breakage for the design when I look.

Regeneration is 3b, where it gets bundled with the weight and legibility
findings, because those need the same pass.

## Leave the door open for a second theme

I may add a dark mode later using the Gothic noir neutrals with these two hues
lifted for a black ground (`#4E9EBC` reaches 6.94:1, `#B87A50` 5.94:1). Nothing
in 3a should make that expensive:

- Keep every colour in custom properties on `:root`. No hardcoded hex anywhere
  in rules, in the JS scenes, or in inline styles.
- Structure the tokens so a second theme is a block of overrides, not a rewrite.
- Where a figure filename is referenced, use a convention that can take a
  `-dark` sibling later without touching markup.

Do not build the toggle. Just do not foreclose it.

## Removing the sys-log — both halves

The `<ul class="sys-log">` in `index.html`, `site/assets/syslog.js`, and its CSS
all go. So does its cache-busting entry.

**The same four numbers also appear as ghost cards in `window.MARGIN_SCENE` at
the bottom of `index.html`** — 86,622 nodes, 1,144 negative links, 34,936 plant
units, 60 prepared scenarios. Removing one and not the other leaves the job
half done. Take the numbers out of the collage too. Option B is converting the
margin scenes anyway, so decide what the home page's marginalia becomes now
that it is not restating counts, and tell me what you chose.

None of this loses anything factual — all four numbers remain on `atlas.html`.

## While you are in the home page

Your own F2 said `index.html` is the only page of eleven with no `<h1>` and
never shows my name above the fold. Removing the sys-log makes the first screen
emptier, not fuller, so fix that here. Use the wordings you proposed in
`DESLOP_OPTIONS_2026-09-04.md` §4 — give me the shortlist again with your
recommendation, apply your recommendation as a placeholder, and I will confirm
or swap it.

## Merge from the right source — this is the easy way to lose work

`style-option-b.css` still carries all **14 gradients**: the card fill at
~line 430, the hardcoded violet/green `body::before` washes, and the
`#0a1024` hero disc at ~line 500. `style-palette-2.css` is the sheet where
those were audited and deleted, down to 1 gradient and no chromatic literal
outside `:root`, plus the new `--hero-ground` and lightbox-overlay tokens.

**Merge Option B's structure onto palette 2's cleaned colour layer, not the
other way round.** Then grep the result and confirm the gradient count and the
literal count match palette 2, not option B. If a gradient reappears in the
merged sheet, it is a regression, not a feature.

## What I have and have not seen

I approved Yacht club on the **baseline** structure. Option B plus Yacht club is
a combination nobody has looked at yet. It should be better — B removes the
`hr` plus `h2` double rule you flagged, and turns the cards into rows — but do
not assume the approval transfers. That is why 3a ends with me looking.

## Rules

- `site/style.css` is the target. Delete `style-option-a/b/c.css` and any
  `style-palette-*.css` once B is folded in. Delete `site/_preview/`.
- Every content page gets the row/marginalia treatment, not just the home page.
- Compute every text/background ratio. AA or better, no exceptions.
- Honour the motion contract; `data-motion="off"` still stops everything.
- Do not touch the five `*-app.html` files — that is 3c.
- Do not run `build_site.py`. Do not regenerate figures. Do not publish.
- `python bust_cache.py` when done.
- Test both suites.

## Write-up and stop

`DESLOP_3A_2026-09-04.md` at the repo root: what changed, the token table with
computed ratios, the stale-asset list, what the margin scenes became, the h1
shortlist, and anything you hit that this brief got wrong.

Then stop. Give me the local URL. I will look before 3b.
