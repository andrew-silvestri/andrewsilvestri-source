# SITE REVAMP BRIEF — andrewsilvestri.com
Written 29 Aug 2026, in Cowork, to be picked up by a fresh Claude Code session.
Read this together with `HANDOFF.md` (which describes the site as it is).
This file describes what it should become.

---

## 0. WHAT ANDREW ASKED FOR, IN HIS WORDS

> revamp the site altogether. i like the current color scheme and projects, but i see
> tons of lightweight tools around now that could be used to make it so much cooler
> (pretext for background animations/sliding text/non-static graphics), live-moving
> centering a div, different configurations of the website depending on device its
> accessed from/dimensions, cool agentic adjacent animations/web stuff (a la kat poet
> engineer, and that whole twitter-verse type stuff), and things of that sort. we can
> maybe have a setting to toggle on the bottom footer of the site to change from
> "static to non-static".

**Keep:** the palette, the projects, the writing, the information architecture.
**Change:** the surface — motion, responsiveness, and the feeling that it is alive.

---

## 1. GROUND TRUTH — verified 29 Aug 2026, not from memory

| Thing | Reality |
|---|---|
| Source of truth | `00 PUBLISH/site/` — plain HTML, one 456-line `style.css`, five JS files. **No build step, no framework, no npm, no bundler.** |
| Deploy | `publish.ps1` clones `andrew-silvestri/andrew-silvestri.github.io`, deletes every tracked file, copies `site/` in, commits, pushes. GitHub Pages, CNAME `andrewsilvestri.com`. |
| **Is the source in git?** | **No.** Only the *output* repo is versioned. `00 PUBLISH/` itself has no `.git`. See §7 — this is step zero. |
| Palette (`style.css :root`) | `--bg #070a12` · `--ink #e3e6f2` · `--acc #8b7ff2` violet · `--moss #4f9d84` · `--cool #5aa8d8`. Dark by default, light variant under `prefers-color-scheme: light`. **This is the "current color scheme" he wants kept.** |
| Type | System stacks only. `--serif` Iowan/Palatino, `--sans` system-ui, `--mono` ui-monospace. No webfonts, no network cost. |
| Existing motion | Six occurrences of `transition|animation|transform` in the whole stylesheet. The site is effectively static. |
| Existing responsive | **Three media queries total**: `max-width: 620px` ×2, `max-width: 760px` ×1. This is the thinnest part of the site and the biggest opportunity. |
| Existing WebGL | **`assets/hero-gl.js` already exists** (13.9 KB) alongside `hero.js` and `hero-data.js` (109 KB). There is already a GL hero system. **Extend it; do not replace it before reading it.** |
| The payload constraint | `assets/atlas-data.js` is **9.7 MB**. `site/` totals 21 MB. Any motion layer competes with this for bandwidth and main thread. |
| Only external dependency | `three.js r128` from cdnjs, on one app page. r128 is ~5 years old and CDN-loaded. A liability; see §5. |
| Tests | `tests/` holds node harnesses; sub-projects have their own. A revamp must leave these green. |

---

## 2. THE ONE ARCHITECTURAL DECISION — settle this before writing any animation

The footer toggle is not a feature bolted on at the end. **It is the contract every
other item in this brief is written against.** Build it first.

```html
<!-- in <head>, BEFORE any stylesheet — blocking, ~200 bytes, no flash -->
<script>
  try {
    var m = localStorage.getItem('motion');
    if (!m) m = matchMedia('(prefers-reduced-motion: reduce)').matches ? 'off' : 'on';
    document.documentElement.dataset.motion = m;
  } catch (e) { document.documentElement.dataset.motion = 'on'; }
</script>
```

Three rules that make this hold together:

1. **`prefers-reduced-motion` is the default; the footer toggle is an override.**
   Not the other way round. This gets accessibility for free instead of bolting it on.
2. **CSS gates on the attribute, not on the media query alone.**
   ```css
   [data-motion="off"] *,
   [data-motion="off"] *::before,
   [data-motion="off"] *::after {
     animation-duration: .001ms !important;
     animation-iteration-count: 1 !important;
     transition-duration: .001ms !important;
     scroll-behavior: auto !important;
   }
   ```
3. **"Off" must mean *not downloaded*, not *downloaded and idle*.**
   Heavy modules load behind a dynamic import gated on the attribute:
   ```js
   if (document.documentElement.dataset.motion === 'on') {
     const { start } = await import('./assets/hero-gl.js');
     start();
   }
   ```
   Flipping the toggle at runtime imports on demand and tears down on disable.
   **A GL context running invisibly behind a "static" setting is the failure mode.**

Toggle lives in the footer on every page, writes `localStorage`, flips the attribute,
**no reload**. Label it plainly — "Motion: on / off" beats a clever icon.

---

## 3. WHAT TO BUILD — in dependency order

### Tier 0 — free wins, near-zero bytes, do these first

- **Cross-document view transitions.** One CSS rule turns page navigation on a static
  multi-page site into a smooth transition. Degrades to nothing where unsupported.
  ```css
  @view-transition { navigation: auto; }
  ```
  Highest perceived-quality-per-byte item on this entire list.
- **Native scroll-driven animations** — `animation-timeline: view()` and `scroll()`.
  Reveals, progress bars, parallax, sticky-section choreography with **zero JavaScript**,
  running off the compositor. Wrap in `@supports (animation-timeline: view())` so
  unsupported browsers get the static layout, not a broken one.
- **Fluid type and space with `clamp()`** — replaces the two width breakpoints with a
  continuous scale. This alone fixes most of the "looks wrong at that size" problem.
- **`text-wrap: balance`** on headings, `pretty` on prose. One line, visibly better.

### Tier 1 — responsiveness done properly (his "different configurations by device")

The current three media queries are viewport-width only. That is the wrong axis.

- **Container queries (`@container`)** are the actual answer. The `.card` / `.cardgrid`
  components reconfigure based on *their own* width, so the same card works in a sidebar,
  a three-up grid, and full-bleed without a single viewport breakpoint. This is the single
  biggest structural improvement available to the CSS.
- **`@media (pointer: coarse)` / `(hover: none)`** — the real device distinction is
  *input*, not width. Every hover-triggered effect is dead on touch and needs a
  tap-or-scroll equivalent. A 1024px-wide tablet is not a desktop.
- **`:has()`** for parent-conditional layout — e.g. a `.card` that has a figure lays out
  differently from one that doesn't, without extra classes.
- **`@media (update: slow)` and `(prefers-reduced-data)`** — cheap ways to drop the
  expensive layer on weak hardware.
- Keep `prefers-color-scheme` light/dark as-is. It already works.

### Tier 2 — the motion layer (the "agentic-adjacent" aesthetic)

What that look actually consists of, decomposed so it can be built rather than vibed:

| Element | How | Cost |
|---|---|---|
| **Text scramble / decode-in** | ~30 lines of hand-written JS over `Intl.Segmenter`. **No library needed.** This is the signature move of that whole aesthetic and it is trivial. | ~0.5 KB |
| **Per-character / per-word stagger** | `Intl.Segmenter` to split, then CSS `animation-delay: calc(var(--i) * 30ms)`. Hand-rolled beats SplitText here. | ~0.5 KB |
| **Monospace/terminal texture** | Already have `--mono`. Use it for metadata, counts, timestamps, node IDs. Free. | 0 |
| **Live counters / "thinking" indicators** | Numbers that tick toward their value on reveal; a blinking block cursor. CSS + tiny JS. | ~0.5 KB |
| **Animated shader background** | Extend the **existing `hero-gl.js`**. Read it first — it may already do most of this. | already paid |
| **Magnetic / spring-following elements** | This is the "live-moving centering div": a spring-eased `translate` driven by `pointermove`, settling back to centre. ~15 lines with a spring easing. **Gate on `(pointer: fine)`.** | ~1 KB |
| **Cursor-reactive gradient** | A CSS custom property updated on `pointermove`, read by a `radial-gradient`. Throttle to rAF. | ~0.3 KB |

**Almost none of this needs a dependency.** Resist the instinct to pull in a framework
for effects that are 20 lines of vanilla each.

### Tier 3 — only if Tiers 0–2 genuinely can't express it

Ordered by preference. **Verify current size, licence, and browser support before
adopting any of these — this brief was written 29 Aug 2026 and those change.**

- **Motion** (`motion.dev`, formerly Motion One) — ~5 KB core, built on WAAPI, so it runs
  off the main thread. The right general-purpose choice if one is needed.
- **OGL** — ~8 KB WebGL layer. **The correct replacement for the three.js r128 CDN link**
  if the shader work outgrows `hero-gl.js`.
- **Paper Shaders** (`@paper-design/shaders`) — drop-in animated mesh-gradient and noise
  backgrounds, close to the aesthetic he described. Evaluate against extending `hero-gl.js`.
- **anime.js v4** — ESM, larger than Motion, richer timeline model.
- **GSAP + ScrollTrigger** — the most capable, and reportedly now free including the
  formerly paid plugins (**verify this**). ~70 KB. Only worth it if native scroll-driven
  animation provably can't do the job. It usually can.

**Do not add:** Lenis or any smooth-scroll hijacker. It fights native scrolling, breaks
the atlas app's own input handling, and is the first thing that feels broken on a trackpad.
**Do not add:** a framework. React/Svelte/Astro would mean a build step, and the site's
zero-dependency, zero-build nature is a genuine asset, not a limitation to overcome.

---

## 4. NON-NEGOTIABLE CONSTRAINTS

1. **No front-end build step.** No bundler, no framework, no npm at runtime. `site/`
   stays plain files served verbatim. Any library gets **vendored into `assets/`**,
   pinned, and committed — never CDN-loaded. (A CDN link is a third-party runtime
   dependency and a supply-chain surface on a site that currently has neither.)
   *This is about the browser, not about deployment* — see §8, which proposes moving
   the publish step into CI. Running the existing Python scripts in GitHub Actions does
   not violate this rule; adding webpack would.
2. **Budget: ≤ 25 KB gzipped** for the entire motion layer, and it must load `async`/
   deferred. `atlas-data.js` is already 9.7 MB; the motion layer must be invisible next
   to it.
3. **Animate only `transform`, `opacity`, and `filter`.** Anything that triggers layout
   (`width`, `top`, `margin`) is a bug. `will-change` sparingly and removed after.
4. **Every GL surface pauses** on `IntersectionObserver` exit and on `document.hidden`,
   and caps `devicePixelRatio` at ~1.5. Andrew's own machine is a 28 W Radeon 780M; a
   pegged GPU is a fan-noise complaint, not a design flourish.
5. **The site must be fully usable and good-looking with `data-motion="off"` and with
   JS disabled entirely.** Motion is a layer over a working static site, never a
   prerequisite for reading it.
6. **`CNAME` and `.nojekyll` must survive.** `publish.ps1` deletes every tracked file
   before copying; losing either fails silently and takes the domain down.
7. **Leave `tests/` green**, and don't break `bust_cache.py`'s assumptions.
8. **Do not touch `19 Atlas v6/`** as part of this work — that coupling is backlog item
   D5 and is a separate job. Note it, don't fix it here.

---

## 5. THE OPEN QUESTIONS FOR ANDREW

Ask these before building, not after:

1. **Scope** — is the revamp `index.html` and the shared chrome (nav, footer, cards)
   with everything else inheriting? Or a page-by-page rework? *Recommendation: the
   former. Shared chrome + `style.css` reaches every page for a fraction of the effort.*
2. **How far does "non-static" go** — ambient (subtle background, reveals, hover) or
   editorial (scroll-driven storytelling that restructures the page as you move)? These
   are very different amounts of work.
3. **Does the toggle persist across pages and visits?** *Recommendation: yes,
   `localStorage`, and it should default to off for anyone with
   `prefers-reduced-motion: reduce`.*
4. **"kat poet engineer"** — I could not verify who this refers to. **Ask him for the
   link** rather than guessing at the reference. §3 Tier 2 decomposes what that
   aesthetic generally consists of, but a specific example beats a general description.

---

## 6. HOW TO SEQUENCE IT

One deliverable per session, per the working agreement.

1. `git init` the source (§7), then a visual audit: screenshot every page at 375 / 768 /
   1440 and write down what actually breaks.
2. Motion toggle + `data-motion` contract (§2). Nothing else. Ship it working.
3. Tier 0: view transitions, fluid type, `text-wrap`. Whole site, one pass.
4. Tier 1: container queries on `.card`/`.cardgrid`, pointer-based media queries.
5. Tier 2: text scramble + stagger on the hero. One page first, as a prototype to react to.
6. Read `hero-gl.js`; decide extend vs. replace with the evidence in hand.
7. Roll the pattern out. Re-audit against the budget in §4.

---

## 7. STEP ZERO — do this before anything else

`00 PUBLISH/` has no `.git`. Only the *deployed output* is versioned, in
`andrew-silvestri.github.io`. So every build script, every template, and every
sub-project in this folder exists in exactly one place on one laptop.

This is the same single-copy pattern that has already been found twice in this project
(the 1.8 TB lake with no backup; the taxonomy with two copies both on `C:`). It is by
far the cheapest of the three to fix, and a revamp is precisely the moment you want the
ability to revert.

```
cd "00 PUBLISH"
git init
# .gitignore: __pycache__/, backups/, site/assets/atlas-data.js, site/downloads/
git add -A && git commit -m "Site source as of pre-revamp"
```

Then push it to a **private** repo — the public one is the built output, and this folder
contains build scripts, tests, and unpublished pages that don't belong there.

---

## 8. HOSTING — stay on GitHub Pages, fix the deploy

**The host is right. The deploy method is not.** These are separate questions and only
the second one needs work.

### Why Pages is correct and migrating would be busywork

The site is 21 MB of static files with no server-side anything, serving a personal
research audience. GitHub Pages' limits are around 1 GB per repo and 100 GB of bandwidth
a month; this site is two to three orders of magnitude under both, on every axis. Custom
domain and HTTPS already work. **There is no technical problem that changing hosts solves.**
Migrating would spend a weekend to arrive at the same page loading at the same speed.

### What is actually wrong

`publish.ps1` clones a *second* repo, deletes every tracked file, copies `site/` in,
commits, and pushes. Three real costs:

1. **The deployed repo's history is worthless.** Every commit reads as "deleted 40 files,
   added 40 files." You cannot diff a release, cannot bisect a visual regression, cannot
   see what a change did. During a revamp that is exactly the capability you want.
2. **Deployment is welded to one Windows laptop.** The script's own header documents a
   Windows-1252 em-dash bug it had to be written around. That class of hazard exists only
   because publishing happens on a personal machine.
3. **Two repos, one project.** Source in an unversioned folder, output in git — the
   backwards arrangement. §7 fixes half of this; CI fixes the rest.

### The target shape — still GitHub Pages

One repo. Source at the root, `site/` as the build output, a GitHub Actions workflow that
runs the Python build scripts and the `tests/` harnesses on push and deploys via
`actions/deploy-pages`. Then:

- Real diffs and real history, because the source is what's committed
- Deploy from any machine, or from the GitHub web UI
- A broken build fails in CI instead of silently publishing
- `publish.ps1` becomes a local preview script, or is deleted
- The CNAME check the script does by hand becomes a CI assertion

### When migrating would genuinely be right

- **Preview deploys per branch.** This is the one real argument, and it is strongest
  *during a visual revamp* — a URL per branch to compare against production. Cloudflare
  Pages and Netlify both do this free; GitHub Pages does not. **If this matters, Cloudflare
  Pages is the pick** (free tier bandwidth is effectively unbounded, and it fronts a better
  CDN). Migration is genuinely about an hour: point it at the repo, set the output
  directory, move the DNS.
- **`atlas-data.js` becomes a bandwidth problem.** Note that the fix here is the *payload*,
  not the host — chunk it, or fetch on demand instead of shipping 9.7 MB up front. Solve
  it in the wrong layer and you will still be shipping 9.7 MB, just from somewhere else.
- **The atlas needs a real API.** Only then does anything server-side enter the picture,
  and that is a different project.

**Recommendation: stay on Pages, consolidate to one repo, move publish into Actions.**
Revisit Cloudflare Pages only if preview deploys turn out to be something you'd use
during the revamp — and if so, do it *before* the revamp, not after.
