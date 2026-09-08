# Retired pages

Kept, not linked, not published. `publish.sh` mirrors `site/` only, so
nothing here ships. Each entry: what it was, when it came off, why. There
was no note here before 2026-09-05; the list lived in HANDOFF.md section 2,
which still carries the one-line version.

- **The bookshelf** - `desktop.html`, `bookshelf-app.html`,
  `assets/bookshelf-demo-*.{webp,png}`, `downloads/bookshelf-code.zip`,
  `build_bookshelf_demo.js`. A wallpaper built in the browser from a
  Goodreads export: drawn spines, or real covers fetched by ISBN from Open
  Library. Retired 2026-09-05 (PHASE5, Part 1): a desktop toy on a site
  about energy models, and the one page whose privacy claim ("nothing else
  from your export") could not be shortened for a card without becoming
  false. The sources are `bookshelf/` (README, wallpaper setter, demo
  render) and the app file here; the last download archive is in
  `downloads/`. The live URLs 404 from the publish that followed.
- **The neuron constraint app** - `neuron-app.html`, with its sources in
  `neuron/` here (`template-app.html`, `build_app.py`). Five checkboxes over
  the 32 precomputed subset counts of the NeuroMorpho census, reorderable,
  so that each constraint's cost could be read in the order ticked. Retired
  2026-09-06: it showed one of the 120 orders at a time, and a still figure
  shows all of them at once (`neuron_fig6_orders.png`, drawn by
  `neuron/fig_neuron.py` from `cascade.order_costs` in the payload), which
  is the case `prompts/NEW_PROJECTS.md` §2 says to build the still figure
  in. The card copy it carried ("costs almost nothing when applied first")
  was also wrong: the shrinkage correction is the least order-dependent of
  the five. The live URL 404s from the publish that followed.
- **dac.html**, **holdup.html**, **beans.html** - direct air capture,
  pipeline liquid holdup, the legume symbiosis. Retired before 2026-08-30;
  their figures are in `assets/` (moved out of the site on 2026-09-04).
- **running-shoes.html**, **running-shoes-app.html** - a shoe in parts, a
  three.js exploded view (opening state from
  `?shoe=1&part=2&explode=1&az=&el=`). Retired before 2026-08-30.
- **energy-web.html**, **hobbies.html**, **hobbies-app.html**,
  **navigator.html**, **navigator5.html**, **zoom_explorer.html** - earlier
  generations of the atlas and of the site (August 2026). Kept for their
  code.

## 2026-09-06, with the nonlinear hero

- **build_thumbnails.py** - the six mosaic tiles on the home page. The mosaic
  went when the home page became the hero canvas plus the index; `index.html`
  was the only page that ever referenced a `*-thumb.png`, and `library.html`
  shows those same six figures at full size, so nothing a reader could see was
  lost. The six PNGs are deleted. `sitefig.thumbnail()` stays, uncalled, for
  the crop lesson in its docstring.
- **build_model_chart.py** - `energy_model_chart.png`, the four-panel "model at
  a glance" figure. Also home-page-only, and also cut with the atlas blocks.
  Removed from `rezip_downloads.py`'s atlas-code.zip file list at the same
  time, so the archive does not ship a builder for a figure the site no longer
  has.

Both were retired rather than left building unshipped, for the reason the 714
layer render was: a generator that writes a file nothing reads goes stale
silently, and deleting the file while the generator still names it turns
`tests/test_generators.py` red instead.

---

# The home page's corner panel, retired 2026-09-07

`body.home .herofoot` — a viewport-fixed block in the left margin holding the
hero's caption and the footer. Retired because the home page is now the drawing
and then the scroll: no panel, no caption over the margin. Andrew's word was
"for now".

**Putting the caption back is one line**, and that is deliberate: add
`<p class="small herocap"></p>` as the first child of `<main>` in `index.html`.
`assets/hero.js` still picks a system and computes its caption on every load,
and its write is guarded (`if (cap)`), so it needs no edit. `body.home .herocap`
is still in `style.css` for exactly this reason.

Putting the **panel** back is more than one line — the rules below are what it
was.

## The rules, as they stood

```css
/* The caption and the footer, stacked, pinned to the bottom left - IN THE LEFT
   MARGIN, outside .paper, which is what makes the rest of this work. At 1728
   that margin is (1728-782)/2 = 473px wide and NOTHING SCROLLS THERE: the only
   thing behind this block is the canvas.
   IT IS A PANEL, NOT A HOLE, AND THAT IS THE WHOLE DESIGN. It carries an
   opaque --bg and a hairline on the two edges that face the drawing. A
   rectangle with no edge and no ground of its own, punched out of a dense
   drawing, reads as a rendering fault rather than as a deliberate label.
   WHAT THE OPAQUE GROUND REPLACED, so nobody puts it back: hero.js cleared
   this block's rectangle out of both canvases every frame, cached that rect,
   and re-measured it on document.fonts.ready - because the caption rewrapped
   when IBM Plex arrived, the block is anchored to the bottom so it grew
   UPWARD, and the stale rect left an uncleared strip along its top edge. An
   opaque rectangle hides the canvas by itself, so the clearRect pair, the
   cached rect and the font-load invalidation all went with it (2026-09-07).
   It also restores _deslop/measure.js as a real gate here. That rig resolves
   backgrounds by walking getComputedStyle up the DOM - CSS colours, not
   rendered pixels - so it reported a clean AA pass for this text whether the
   exclusion worked, was broken, or had been deleted that morning. The ground
   it reads is now the ground that paints. tests/test_panel.js is the check
   that can still see pixels, and it is what fails if this background goes.
   THE +1px ON THE WIDTH IS NOT SLOP. .paper's border-left occupies 473-474 at
   1728; a border-right on a 473px-wide block lands on 472-473, ADJACENT, and
   the two hairlines paint a 2px rule wherever .paper spans this block's rows -
   which is everywhere except the arrival screen, where the paper column starts
   below the hero band. One more pixel puts the two borders on the same column
   and they paint one hairline. box-sizing is border-box, so the text box is
   still (W-782)/2 - 68 and the 2.7px of slack at 1341 - see the breakpoint
   note below - is not spent on the border. */
body.home .herofoot {
  /* --rhythm is on :root now, shared with every page's footer. It is this
     panel's top and bottom padding AND the gap between its two lines. */
  position: fixed;
  left: 0;
  bottom: 0;
  z-index: 1;
  width: calc((100% - min(100%, 782px)) / 2 + 1px);
  padding: var(--rhythm) 34px;
  box-sizing: border-box;
  background: var(--bg);
  border-top: 1px solid var(--rule);
  border-right: 1px solid var(--rule);
}
body.home .herofoot footer {
  margin-top: 0;      /* it is a stacked block here, not the end of a document */
  padding-top: 0;
  border-top: 0;
}
/* Two lines, each a link, each a whole destination. The name goes to
   about.html, which carries the role and the email; the built-with SENTENCE is
   the link to code.html rather than a separate "All code is downloadable."
   after it, because two links in a two-line block is one more decision than
   the block is worth making the reader take.
   WHAT WAS HERE, because the breakpoint below used to be derived from it: a
   <br>-stacked identity - name, "energy systems modeling", email - three
   lines whose longest item rendered at 208.8px. That string is gone and so is
   the derivation that rested on it. Read the breakpoint note below before
   assuming any number in this block still comes from a stacked identity.
   THE line-height IS DELIBERATE and it is what makes the rhythm one number.
   footer's line boxes are 19px at line-height:normal against the caption's
   21.75 at .small's 1.5, so the SAME margin rendered 15.4px above the footer
   and 13.0px inside it - the "two different gaps" this block was reported for.
   One margin and two line-heights is two gaps.
   Two <p> rather than <br>, so the gap between the two lines comes from a
   margin and can be changed in one place. */
body.home .herofoot footer p { margin: 0; line-height: 1.5; }
body.home .herofoot footer p + p { margin-top: var(--rhythm); }
```

```css
/* Below 960 the paper is full-bleed, so there is no margin to sit in and no
   canvas to clear: the block goes back into the flow at the end of the page.
   Same breakpoint as .paper's, deliberately - one number, one behaviour
   change. The cost is that on a phone the hero's caption ends up a scroll away
   from the hero it describes; the alternative was moving the element between
   two parents on every resize, which is worse. */
/* 1340, NOT 960, AND THE DIFFERENCE IS DELIBERATE. .paper goes full-bleed at
   960 because that is where its margins stop being wide enough to read a
   trajectory in. This block goes static where its margins stop being wide
   enough to hold its own TEXT, which is a different question and a larger
   number, so the two breakpoints are not the same and must not be "tidied"
   into one.
   RE-DERIVED 2026-09-07 WHEN THE FOOTER BECAME TWO LINES. The old derivation
   is gone with the string it rested on, and the obvious way to redo it gives a
   number that would delete this feature on most screens. Read all of this
   before changing 1340.
   THE OLD RULE WAS ABOUT ATOMICITY, NOT LENGTH. It protected "energy systems
   modeling", one item of a <br>-stacked identity, where a wrap splits one
   label across two lines and reads as breakage. 208.8px + 68 gave W >= 1336,
   and 1340 shipped.
   APPLYING THAT RULE TO THE NEW FOOTER GIVES 1632, AND 1632 IS WRONG. The
   longest line is now "Built with Python, Julia and public data." at 356.7px,
   and 356.7 + 68 solves to W >= 1632 (measured: one line at 1632, two at 1600).
   But that line is a SENTENCE, and sentences wrap. A rule about atomic tokens
   applied to prose would take the fixed panel out of 1341-1631 - including
   1440, the shell width, and 1366, a very common laptop width - to prevent a
   sentence from doing the thing sentences do.
   THE BINDING CONSTRAINT NOW IS TWO LINES, NOT ONE. Measured with this media
   query overridden so the block stays fixed all the way down (Firefox,
   1728-config, dpr 2.2222, IBM Plex Mono loaded):
     the built-with sentence reaches THREE lines at W = 1300, and is still two
       at 1301 - a text box of 190.5px holds it, 190.0px does not
     the first OVERFLOW - scrollWidth > clientWidth, what test_layout.js
       actually fails on - is at W in [1070, 1075)
   The overflow figure is not a line: it is "Silvestri", 78.3px, the longest
   UNBREAKABLE run, and 78.3 + 68 predicts W >= 1075 against a measured failure
   between 1070 and 1075. Lines wrap; runs overflow; only runs fail a test.
   SO 1340 STAYS, and now it has room. The requirement is W >= 1301, so 1340
   carries 39px of slack where the old rule left 4, and the hard failure is
   another 226px below that at 1075. Nothing here is close to anything.
   BOTH DIRECTIONS WERE BROKEN BEFORE THIS WAS TRUSTED (trap 17). Moved to
   1632, the panel goes static at 1366 and at 1440 - measured, both. Moved to
   1300, the sentence takes three lines - measured with this rule overridden so
   the block stays fixed that far down, because otherwise the shipped rule wins
   and every reading below 1340 is of a static block in the 714px column, which
   is how the first attempt at that test produced nonsense.
   960 IS STILL A DIFFERENT NUMBER FOR A DIFFERENT REASON - see .paper.
   (An earlier version of this comment derived W >= 1300 from 191px and called
   the slack 40px. 191.4px is the email address, which is the widest UNBREAKABLE
   run and so the figure test_layout.js reports; the identity line is 208.8px.
   The two were swapped, and everything downstream of the 191 was wrong. See the
   longer note beside the footer rule above.)
   What it was: at 960 the block stayed fixed down to 961px, where its usable
   text width is (961-782)/2 - 68 = 21px, about two characters. At 1024 it is
   53px, and at 1280 - a common laptop width - 181px, against 191.4px for the
   email address that cannot break and 208.8px for the identity line that can.
   It shipped that way; test_layout.js ran at 1024 and had nothing asserting
   that a fixed block's text fits inside it, which it now does. */
@media (max-width: 1340px) {
  body.home .herofoot {
    position: static;
    width: auto;
    max-width: min(100%, 782px);
    margin: 0 auto;
    padding: 0 34px 40px;
    /* No panel down here. The block is back in the flow inside the 782px
       column, on the page's own ground, with nothing behind it to hide and no
       margin for an edge to divide from - so the ground and the two borders
       come off and footer's own rule below does the separating. */
    background: none;
    border: 0;
  }
  body.home .herofoot footer {
    margin-top: 40px;
    padding-top: 22px;
    border-top: 1px solid var(--rule);
  }
  body.home .herocap { max-width: none; }
}
```

## The 1340 breakpoint's derivation, in full

This is the part worth keeping. It cost two rounds and three corrections, and if
the panel ever returns the next person should inherit the reasoning rather than
re-measure it — or, if they do re-measure, be able to check themselves against
it. Every figure below is measured in Playwright Firefox at 1728x1080,
`deviceScaleFactor` 2.2222, with `document.fonts.ready` awaited.

**The rule that produced 1340 was about ATOMICITY, not line length.** It
protected `energy systems modelling`, one item of a `<br>`-stacked identity,
where a wrap splits a single label across two lines and reads as breakage.

**Correction 1 — the 191px was the wrong string.** The comment derived
`W >= 1300` from "the longest stacked line renders at 191px". It does not:

| string | width |
|---|---|
| `energy systems modelling` | **208.8px** |
| `dasilvestri@utexas.edu` | **191.4px** |

191 is the email address — the widest *unbreakable* run, which is what
`test_layout.js` reports when its `scrollWidth > clientWidth` assertion fires,
because an email has no break opportunity and `energy systems modelling` has
two. The two numbers answer different questions and had been swapped. The "209
estimate" that was thrown out as 9% high was right to within 0.2px.
Corrected: `208.8 + 68 = 276.8`, so `W >= 1335.6`, call it **1336**.

**Correction 2 — the slack was 2.7px, not 40px, and that was fine.** At 1341,
the narrowest width where the block was still fixed, the text box is 211.5px
against 208.8px. Measured as a threshold rather than a subtraction: narrowing
the block in 0.5px steps at 1341, the identity group held at three lines through
a 2.5px shrink and went to four at 3.0px, so **the wrap threshold is in
[2.5, 3.0)** and the arithmetic lands inside it. It existed in a ONE-PIXEL band —
1340 was where the block went static, so 1341 was the only width that saw the
worst case; at 1366 the slack was 15.2px. Raising the breakpoint to 1400 was
considered and **declined**: it would have taken the panel out of 1341-1399,
including 1366, to prevent a benign four-line wrap at a single width.

**Correction 3 — when the footer became two lines, the same rule gave 1632, and
1632 was wrong.** The new longest line was the sentence
`Built with Python, Julia and public data.` at **356.7px**, and `356.7 + 68`
solves to `W >= 1632` (confirmed against the page: one line at 1632, two at
1600). That would have removed the fixed panel from **1341-1631**, including
1440, the shell width, and 1366, a very common laptop width — because a rule
about atomic tokens was being applied to a sentence, and sentences wrap.

**The final derivation.** Measured with the media query overridden so the block
stayed fixed all the way down:

| threshold | measured |
|---|---|
| the built-with sentence reaches **three** lines | **W = 1300** (two at 1301; a 190.5px text box holds it, 190.0px does not) |
| **first overflow**, `scrollWidth > clientWidth` | **W in [1070, 1075)** |

The overflow figure is not a line: it is `Silvestri` at **78.3px**, the longest
unbreakable run, and `78.3 + 68` predicts `W >= 1075` against a measured failure
between 1070 and 1075. **Lines wrap; runs overflow; only runs fail a test.**

So the requirement was `W >= 1301`, and **1340 stayed with 39px of slack** where
the old rule left 4, the hard failure a further 226px below at 1075.

**Broken both ways before being trusted** (trap 17): moved to 1632, the panel
went static at 1366 and at 1440 — measured, both. Moved to 1300, the sentence
took three lines. The first attempt at that second half was worthless and is
worth knowing about: it added a media query without removing the shipped one, so
every reading below 1340 was of a static block in the 714px column, and the test
reported nonsense that looked like a pass.

## Also retired with it

- `tests/test_panel.js` — the rendered-pixel check that the panel's ground was
  opaque, and that its right border and `.paper`'s left border painted one
  hairline and not two. It went the way `tests/test_exclusion.js` went before
  it: the mechanism it guarded stopped existing. It is worth reading before
  writing another pixel check — its `--break` mode asserts on its own result,
  which is the bug trap 26 records in the file it replaced.
