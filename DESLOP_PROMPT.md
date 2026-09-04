# Deslop pass — andrewsilvestri.com

You are working on `andrewsilvestri.com`, a hand-built static site. This file
is your brief. Read `HANDOFF.md` in this folder before touching anything — it
describes the whole system and lists traps that have already caused shipped
bugs.

## The job

The site's **presentation** may read as generic AI-generated work. Your first
task is to find out whether it does, where, and how badly — by measuring, not
by assuming. Then fix it.

**Do not change the content.** No rewriting of prose claims, no changed
numbers, no removed or added sections. Words may be re-typeset, re-weighted,
re-spaced and re-ordered on the page; they may not be rewritten. The one
exception is punctuation and title mechanics, and only if your own audit
concludes it matters.

This runs in **three phases with hard stops**. Do not cross a stop without my
explicit go-ahead.

---

## What you are working with

- `site/` **is** the website. Plain HTML, one stylesheet (`site/style.css`,
  ~734 lines), 13 JS files in `site/assets/`. No build step, no framework.
- Content pages, hand-maintained: `index.html`, `atlas.html`, `model.html`,
  `library.html`, `code.html`, `heat.html`, `storage.html`, `climate-cost.html`,
  `longevity.html`, `skyline.html`, `desktop.html`.
- Full-screen interactives, each with its own inline CSS: `atlas-app.html`,
  `longevity-app.html`, `skyline-app.html`, `bookshelf-app.html`,
  `climate-cost-app.html`.
- `publish.ps1` mirrors `site/` into `~/andrew-silvestri.github.io` and pushes
  to GitHub Pages.

## Hard constraints

1. **Do not run `build_site.py`.** It is stale (1 Aug) and does not know about
   the mosaic, sys-log, margin scenes or motion toggle. Running it regenerates
   the HTML back to an August state and destroys a month of work.
2. **`atlas.html` is generated** by `update_atlas_pages.py`. Any change to it
   goes in the generator, not the file.
3. **The nav is generated** by `rebuild_nav.py` from its `NAV` list. Never
   hand-edit `<nav class="top">`. (Corrected 2026-09-04: the shipped nav had
   been hand-edited in the 2026-08-30 revamp and the `NAV` list had not
   followed; the list now matches what shipped, verified by running the
   generator and seeing 0 pages rewritten. Before running it, diff its
   output against the pages — if any page changes, someone hand-edited
   again.)
4. **Run `python bust_cache.py`** after any edit to `style.css`, any JS, or any
   image, and always before a publish. Filenames never change; the `?v=` hash
   is the only thing that busts a browser cache. Skipping it looks exactly like
   a change that did not take.
5. **Keep the discipline that already exists**: no build step for the site, no
   framework, no npm dependency shipped in `site/`, no render-blocking CDN
   webfont, versioned `?v=` asset URLs, `prefers-reduced-motion` respected via
   the existing `data-motion` contract, pages in the 300–600 KB range.
   Dev tooling for the audit is fine — put it outside `site/` and gitignore it.
6. **Preserve accessibility.** Every text/background pair must pass AA, and
   you must compute the ratios rather than eyeball them. (Corrected
   2026-09-04: this line used to say "the current palette passes AA". It did
   not — `--acc-ink` on `--acc` is 2.91:1 in the dark scheme, on every nav
   pill and primary button. The claim came from the 2026-08-30 external audit,
   which never measured text on the accent. Treat the brief's factual
   premises as checkable.)
7. **`HANDOFF.md` §4 is the settled house style.** The prose voice, the
   never-invent-data rule and the figure discipline are not up for revision.

---

# Phase 1 — Audit

You are not implementing anything in this phase. You are producing a document.

**Do your own work before reading anyone else's.** There are two prior audits in
this folder (`DESIGN_AUDIT_EXTERNAL_2026-08-30.md`,
`SITE_REVAMP_2026-08-30.md`) and a completeness checklist at the bottom of this
file. **Do not open any of them until you have written your own findings.**
They exist to catch what you missed, and they cannot do that if they seed you.

## 1a. Establish the criteria from sources

Search the web for current writing on AI-generated and vibe-coded website
design: the visual tells, the CSS fingerprints, the typography failures, the
specific fixes practitioners recommend, and the critiques of those critiques.
Read at least six substantive sources and prefer ones that show evidence over
ones that assert.

Then look at the other side of the question: what do well-regarded personal
sites by researchers, scientists and engineers actually look like right now?
Find real examples that read as *designed by a person with opinions*, and
articulate specifically what makes them read that way. Note that "not slop" is
not a synonym for "minimal" — a distinctive maximalist site is also not slop,
and sanding a site into a quieter kind of generic is a failure mode, not a fix.

Write the criteria down before you apply them. You should end this step with an
explicit, checkable list of tells, each with the evidence that it is a tell.

## 1b. Measure the site

Set up a real browser you can drive and instrument. Node is available (there
are node test harnesses in `tests/`). Playwright via `npx` in a scratch folder
outside `site/` is the obvious route; use whatever you have. Serve the site
locally (`python -m http.server` from `site/`) rather than opening `file://`
URLs, so relative paths and scripts behave.

For **every content page**, at 1440×900 and 390×844, motion on and motion off,
collect actual measurements. At minimum:

- **Type inventory.** Every distinct computed `font-size` / `weight` /
  `line-height` / `letter-spacing` / family actually rendered. Flag everything
  under 12px. Is there a coherent scale, or a pile of one-off values?
- **Colour inventory.** Every colour literal in `style.css`, in the JS scene
  files, and in the generated figures. How many distinct hues? What is the
  actual accent doing — does it mark meaning, or decorate?
- **Contrast.** Computed ratios for every foreground/background pair actually
  used, including text over the background washes and over figures.
- **Image fidelity.** Natural vs rendered dimensions for every `<img>`. Anything
  rendered well below its natural size is either wasted bytes or unreadable
  detail; anything above is soft.
- **Vertical rhythm and dead space.** Measure section gaps. What fraction of
  each page's scroll height contains no content? Scroll each page at speed and
  record whether reveal animations leave blank viewports.
- **Weight.** Bytes per page, split HTML / CSS / JS / images / video.
- **Motion inventory.** For each of the 13 JS files: what it draws, what it
  costs in bytes and frame time, and — the real question — **what a reader
  loses if it is deleted.** Name anything that decorates without informing.
- **Structural repetition.** Count the repeated layout patterns. How many times
  does the same card-grid shape appear? Does the page have a rhythm, or one
  module tiled?
- **Punctuation and copy mechanics.** Not the prose itself — the mechanics.
  Title construction, dash usage, kicker capitalisation, caption patterns.
- **Interactives.** Same pass, lighter, on the five `*-app.html` files: type
  sizes, panel surfaces, accent use, whether they read as the same site.

Take screenshots and keep them. Your findings need to be checkable.

## 1c. Write the audit

Write `DESLOP_AUDIT_2026-09-04.md` at the repo root — **not** in `site/`.

Structure each finding as: **what was observed** (with file, line numbers and
measured values), **why it hurts**, **severity**, **what fixing it costs**.
Rank by severity. Be specific enough that I could verify any finding myself in
under a minute.

Include a section titled **"What is good and must survive."** This matters as
much as the findings. Name what is distinctive, opinionated or hard-won, and
say what would be lost by flattening it. If you conclude some part of the site
is not slop at all and my premise is wrong there, say so plainly.

## 1d. Only now, cross-check

Having written your own findings, read — in this order:

1. `DESIGN_AUDIT_EXTERNAL_2026-08-30.md` — a prior external critique.
2. `SITE_REVAMP_2026-08-30.md` — what was fixed against it, and what was
   deliberately left open. **Do not redo work already done.**
3. The completeness checklist at the bottom of this file.

Append a short section to your audit: what those three caught that you missed,
what you caught that they missed, and anything in them you think is wrong.

**Then stop.** Report the audit and wait.

---

# Phase 2 — Three options

Only after I have read the audit and told you to proceed.

Produce **three** complete, working alternative treatments, driven by your
audit's findings rather than by generic taste. Each option is:

- A full alternative stylesheet at `site/style-option-a.css` (and `-b`, `-c`).
- A rendered proof: copies of `index.html`, `model.html` and `heat.html` under
  `site/_preview/option-a/` etc., pointed at that option's stylesheet, so I can
  open each in a browser and compare against the current site. Add
  `site/_preview/` to `.gitignore`; it is scratch and gets deleted before any
  publish.
- Any markup changes the option needs, made **in the preview copies only**, and
  described in writing.
- A rationale: what it is, which audit findings it resolves, which it does not,
  and what it costs.

The three must be **genuinely different directions**, not one idea at three
intensities. Beyond that, the directions are your call — they should follow
from what the audit actually found. If your audit says the problem is
typography, three palette variations are the wrong three options.

On typefaces: prefer self-hosted, subset files in `site/assets/fonts/` over a
CDN — no external dependency, no blocking request, consistent with the existing
no-dependency discipline. Check the licence permits web use and record it.

**Then stop.** Tell me exactly which URLs to open to compare. Ask me to choose.
Do not publish. Do not delete the unchosen options until I say so.

---

# Phase 3 — Apply and publish

Only after I have named an option.

1. Fold the chosen treatment into `site/style.css` itself — do not ship three
   stylesheets. Apply its markup changes across **all** content pages. Delete
   the option files and `site/_preview/`.
2. Apply the same treatment as **light chrome only** to the five `*-app.html`
   interactives: control-panel type sizes, panel surfaces, accent colour, so
   they do not read as a different site. Do not touch their behaviour or their
   layout logic.
3. Verify, and show me the evidence:
   - Every content page and every app renders correctly at 1440×900 and
     390×844. Actually look at them; screenshots in the write-up.
   - Contrast ratios computed for the new palette. AA or better throughout.
   - `data-motion="off"` still stops everything that moves.
   - No page grew past ~600 KB.
   - `python tests/test_markup.py` passes.
   - `node tests/test_atlas_interaction.js` passes.
   - Nothing in `site/` references a stylesheet, script, font or image that no
     longer exists. Grep for it.
4. `python bust_cache.py`
5. Write `DESLOP_2026-09-04.md` at the repo root, in the what / why /
   implication structure `SITE_REVAMP_2026-08-30.md` uses. Include what you
   chose **not** to do and why.
6. Commit in `00 PUBLISH` with a message describing the change.
7. `.\publish.ps1 -DryRun` and show me the output.
8. If the dry run is clean, `.\publish.ps1` to publish.

---

# How to work

Show your reasoning on design decisions rather than just making them. Where you
disagree with this brief — including the framing that the site has a problem at
all — say so directly and argue it. I would rather be corrected than agreed
with. Do not soften a finding to be agreeable, and do not manufacture one to
seem thorough.

---
---

# Appendix — completeness checklist

**Do not read this until Phase 1c is written.** These are one reader's
unverified suspicions, recorded before any measurement. They are here to test
whether your audit was thorough, not to tell you what to find. Several may be
wrong, and the list is certainly incomplete.

<details>
<summary>Open only after your own findings are written.</summary>

- `--acc: #8b7ff2` violet on `--bg: #070a12`, plus two `radial-gradient`
  washes on `body::before` sitewide.
- `.cardgrid` of three cards with `.tag` all-caps kickers, repeated three times
  down the home page.
- `.card` = hairline border plus soft drop shadow (`--shadow`).
- Em dashes throughout, including in the `<title>` of every page.
- `margin-scene.js` (28 KB), `syslog.js`, `hero-gl.js`, `bgloop.js` — motion
  that may decorate rather than inform.
- `--sans` and `--serif` are both generic fallback stacks rather than chosen
  faces.

For each: did you find it independently? If not, why not — is it not actually a
problem, or did your method miss it? If your method missed it, say what you
would change about the method.

</details>
