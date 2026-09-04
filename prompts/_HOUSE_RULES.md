# House rules — read this with whichever brief sent you here

These apply to every audit and build brief in `prompts/`. Your brief adds to
them; where it conflicts, your brief wins and you should say so.

## The site

`site/` **is** the website. Plain HTML, one stylesheet (`site/style.css`),
13 JS files in `site/assets/`. No build step, no framework, no npm dependency
shipped in `site/`. `publish.sh` (Git Bash) mirrors `site/` to GitHub Pages —
`publish.ps1` is retired and untested; do not use it.

Content pages: `index.html`, `atlas.html`, `model.html`, `library.html`,
`code.html`, `heat.html`, `storage.html`, `climate-cost.html`, `longevity.html`,
`skyline.html`, `desktop.html`.

Interactives, each with its own inline CSS and no shared nav, linked with
`target="_blank"`: `atlas-app.html`, `longevity-app.html`, `skyline-app.html`,
`bookshelf-app.html`, `climate-cost-app.html`.

## The rule that outranks everything

From `HANDOFF.md` §4: **never invent data.** Every number traces to a public
data set, an exact computation, or a named publication. Anything assumed is
labelled *assumed*, not presented as measured. If a number cannot be sourced,
the feature is not built and the page says why it is absent.

For an interactive this has a sharper edge than for prose: a control that lets
someone change an input implies the output was computed from it. If the output
is interpolated, approximated, or precomputed from a synthetic input, the
interface has to say so where the person is looking — not in a footnote.

## Documents here describe a repository that has partly moved on

`HANDOFF.md` is the system's map and is worth reading, but four separate stale
claims in it were found and corrected on 2026-09-04, and it now carries trap 11
warning about exactly this. Two more remain as of this writing: its §2 archive
table points at workspace-root folders (`24 Skyline Sonifier/`,
`25 Desktop Gallery/`, `18 Final Deliverables/`, `16 Presentation
Architecture/`, `PyProjects/`) that do not exist — the numbered archives are
under `01 ARCHIVE/`, and 24 and 25 are gone entirely.

**Verify any factual premise before you build on it, including premises in your
own brief.** The deslop brief asserted "the current palette passes AA"; it was
2.91:1 and failed on every button on every page. Treat a stated fact as a lead.

If you find a seventh instance, report it rather than working around it
silently.

## Accessibility

Compute contrast ratios, do not eyeball them. AA is 4.5:1 for normal text,
3:1 for large text and UI boundaries. The main site's palette was corrected on
2026-09-04 (`--acc-fill` tokens, 5.88:1 dark / 7.82:1 light); the apps carry
their own inline CSS and were only partly swept.

## Motion

The site has a motion contract: `data-motion="on"|"off"` on `<html>`, set
before first paint from `localStorage` or `prefers-reduced-motion`. Anything
that moves must stop when it is `off`. Check whether the app you are working on
honours it — the apps are the most likely place it was skipped.

## Do not

- Run `build_site.py`. It is stale (1 Aug) and reverts the HTML by a month.
- Hand-edit `<nav class="top">`, or run `rebuild_nav.py` without diffing its
  output first.
- Touch `site/style.css` or any content page unless your brief says to.
- Publish. No brief in this folder ends in a publish.
- Skip `bust_cache.py` if you did change a shipped asset — and note it does
  **not** stamp files referenced from CSS, so a changed font needs a new
  filename.

## How to work

Show your reasoning rather than only your conclusions. Where you think your
brief is wrong, argue it rather than routing around it. Do not soften a finding
to be agreeable and do not manufacture one to look thorough. If a brief asks
you not to read something until a given point, say plainly whether you managed
that — a previous instance disclosed that `cat` had shown it a sealed appendix
early, and that disclosure was worth more than the seal.
