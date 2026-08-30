# Site audit findings — unresolved items

A record of things found during the site work sessions that were **not**
fixed and are not reflected on the live site. Each entry: what was found,
when, why it wasn't fixed, and what it implies if left alone. Items that
were found and fixed are not repeated here — see the git log for those
(commits `769d2b3`, `613e944`, `ed5e28e`, `167a7d7` and earlier on
2026-08-29 cover the fixed items).

---

## 2026-08-29 — Content/data mismatches

### `site/assets/01_world_fuel_mix.png` and `03_price_histories.png` render on a light background
- **What**: Both images use a plain white/light matplotlib default theme
  (black title text, white canvas), inconsistent with every other chart on
  the site, which is dark-themed to match `site/style.css`'s palette.
- **Why not fixed**: No live, editable source script could be found for
  either figure. Searched: every top-level `build_*.py` in `00 PUBLISH/`,
  and the contents of `atlas-code.zip`, `model-code.zip`, and
  `deliverables-code.zip` (the three most plausible downloadable archives).
  None contain a script that plots "Electricity fuel mix" or "price
  histories" content. Regenerating a chart of this complexity from scratch
  without the real source (which fonts, which exact seaborn/matplotlib
  calls, which data file) risked introducing a *content* error to fix a
  *style* inconsistency — judged worse than leaving it.
- **Implication**: These two images will keep looking visually out of place
  against the rest of the site until someone locates or rewrites their
  source. Low severity (readable, just a jarring white rectangle on a dark
  page) but a real, visible bug.

### `site/assets/09_size_vs_lowcarbon.png` content does not match its filename or caption
- **What**: `library.html`'s own copy describes this figure as "System size
  against low carbon share... Each point is one country" — a scatter plot.
  The actual image is a horizontal bar chart titled "Where the world's
  generating capacity sits, by fuel" (installed GW by fuel type). It is
  generated correctly (no layout bugs, 0 audit problems) — it's simply the
  wrong chart for its filename and surrounding prose.
- **Why not fixed**: This is a content-correctness question, not a
  rendering bug. I don't know whether the filename/caption is stale (the
  chart was intentionally swapped at some point and the copy never updated)
  or the wrong output got saved under this filename by mistake. Guessing
  either way risks removing correct content or fabricating a scatter plot
  that doesn't exist in the source.
- **Implication**: A reader who reads the library.html caption and then
  looks at the image will find they don't match. Someone with context on
  which chart was *supposed* to ship here needs to resolve this — it is a
  one-line fix once the intent is known (either fix the copy, or find/
  regenerate the real scatter plot).

---

## 2026-08-29 — Minor palette inconsistencies (not fixed, judged low priority)

### `heat_fig4_tornado.png` bar colors
- Uses matplotlib's default tab10 blue/orange rather than the site's
  ACC/COOL/WARM constants from `figstyle.py`. Legible and not clashing
  badly with the dark background, just not using the house palette. Did
  not fix because the sensitivity-tornado bars' color already encodes
  direction (increase/decrease) consistently within the figure, and
  reassigning colors risked breaking that internal logic without a matching
  source-code review pass I didn't have budget for in that session.

### `storage_fig2_dispatch_week.png` charge/discharge colors
- Uses `"tab:red"` / `"tab:blue"` / `figstyle.GREEN` rather than the exact
  site hex values throughout. Red-for-charge/green-for-discharge is a
  standard, intuitive convention on its own; left as-is rather than forcing
  an exact-hex match for a convention that already reads correctly.

**Implication of both**: Cosmetic only. Neither affects legibility or
correctness. Worth a follow-up palette pass if a fully uniform look across
every chart matters more than the current state.

---

## 2026-08-29 — Efficiency / build-hygiene observations

### Unused generated figures
- `heat`'s `model.py` generates `fig2_lcoh_stacked.png` — never referenced
  by any HTML page.
- `storage`'s `model.py` generates `fig5_monthly.png` — never referenced by
  any HTML page.
- `longevity-quotient`'s `build_lq.py` generates `fig2_lq_ranked.png`
  ("Who beats their body mass, and who does not") — never referenced by
  `longevity.html`.
- **Why not fixed**: Removing generation code for figures nobody asked me
  to touch felt like unrequested scope during a bug-fixing pass, and there
  was no way to confirm from the code alone whether these are dead weight
  or reserved for a future page section.
- **Implication**: Each `python model.py` / `build_lq.py` run does a small
  amount of unnecessary work (one extra `plt.subplots`/`savefig` cycle
  apiece — on the order of tens of milliseconds, not a real performance
  problem). The more relevant cost is maintenance confusion: a future
  editor may reasonably assume every generated PNG is used somewhere and
  waste time looking for its `<img>` tag. Worth either wiring these three
  into their pages or deleting the generation code, once someone confirms
  which.

### `assets/margin-scene.js` and `assets/biome-scene.js` are not cache-busted
- **What**: Every other site script is loaded with a content-hash query
  string (e.g. `motion.js?v=4cbbdec3`) that `bust_cache.py` rewrites when
  the file's content changes, forcing browsers to fetch the new version.
  `margin-scene.js` and `biome-scene.js` (added 2026-08-29) are linked with
  no `?v=` at all, matching the pre-existing pattern already used for
  `bgloop.js`.
- **Why not fixed**: `bust_cache.py`'s existing logic only *updates* an
  existing `?v=` parameter on a script tag; it does not *add* one to a tag
  that has none, and extending that tool was out of scope for a pass
  focused on visual/data bugs. I matched the file to the site's own
  existing convention (`bgloop.js` already ships without one) rather than
  inventing a new one unilaterally.
- **Implication**: If either file is edited again in the future, a
  browser that already cached the old copy will not automatically pick up
  the change — a returning visitor could keep running stale JS
  indefinitely (no forced-refresh mechanism). This already carries the same
  risk for `bgloop.js`. Low real-world impact (these files change rarely),
  but it's a real gap in the cache-busting coverage worth closing if
  `bust_cache.py` is ever revisited.

### General JS efficiency review — margin-scene.js / biome-scene.js
- Reviewed both for the "make the code more efficient" ask: per-frame
  allocations, redundant `getComputedStyle` calls, wasted trig/string work.
- **Finding**: nothing worth changing. Both draw a small, fixed number of
  canvas elements (a handful of bands/bars/creatures) at a capped
  device-pixel-ratio, gated so the animation loop never runs when
  `data-motion` is off, the tab is hidden, or the viewport is too narrow to
  show anything. There is no meaningful CPU/GPU cost to optimize at this
  scale. Recorded here because the user asked for an efficiency pass and a
  clean bill of health is itself a finding, not a non-answer.

---

## 2026-08-29 — Design intent not fully realized

### `climate-cost.html`'s arc-route margin animation doesn't reveal progressively down the whole page
- **What**: The plan called for each of the page's 20 real shipping-route
  arcs to reveal "as its row scrolls into view," implying a reveal spread
  across the full length of the (long) article. The shipped `arcroute`
  primitive instead anchors all 20 rows near a fixed document position
  (close to where the real data table sits) and they scroll out of view
  together after roughly the first 600px of scrolling — so for most of the
  page's remaining length, that margin animation shows nothing.
- **Why not "fixed"**: This was a deliberate simplification made while
  building the primitive, not a bug — the anchored version still ties the
  visualization to the real table's position and looks correct where it
  appears. It just doesn't fill the whole scroll length the original plan
  implied.
- **Implication**: No correctness issue, just an unrealized ambition. A
  future pass could stretch the arc reveal across the full document height
  (similar to how `atlas.html`'s `strata` primitive spans the whole page)
  if a more continuous margin presence on this page is wanted.

---

*This file is intentionally kept outside `site/` so it is not published to
the live domain. It is tracked in git for the project's own record.*
