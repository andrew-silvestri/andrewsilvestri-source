## Goal

The published site (andrewsilvestri.com, source in `00 PUBLISH/`, served content in
`00 PUBLISH/site/`, zero build step / no bundler) got a full diagnostic pass after the
user said "site needs to be reworked still. figure out what is wrong with it, then get
back to me." A written report was delivered (not yet implemented). The user then asked
to implement every item in one pass, log all changes in a non-published markdown file,
and to plan the work in plan mode before executing. Plan mode was entered, two research
agents finished, but plan mode was interrupted before a final plan was written — the
actual implementation plan for this revamp still does not exist. Currently gathering
user decisions on the handful of "needs a judgment call" items before that plan gets
written.

## State

- Working tree is clean, on branch `master` (main branch for PRs is `main`). Tip commit
  `161207a`.
- Diagnostic report already delivered to the user in-chat (not saved anywhere else). It
  found: (1) a real content bug in `longevity.html` — intro says "twenty orders of
  magnitude" of body-mass range, page's own later section correctly says "14.5 orders
  of magnitude"; (2) inconsistent nav grouping — "Climate cost calculator" sits at
  top level while Heat/Storage (also energy tools) are nested under "Energy ▾"; (3)
  `desktop.html` ships two oversized PNGs (`bookshelf-demo-covers.png` 2.15MB,
  `bookshelf-demo-shelf.png` 840KB); (4) site-wide Cloudflare Turnstile console noise,
  judged edge-injected/not a site bug, informational only.
- `SITE_AUDIT_FINDINGS.md` (repo root, intentionally outside `site/` so never published)
  holds an older, still-unresolved list from a prior pass — user asked for "everything"
  to be tackled, which is read as including this file's items.
- Plan-mode research is done (do not re-run these two investigations):
  - Nav bar `<nav class="top">` markup is byte-identical in structure across 11 pages
    (`index, atlas, model, library, heat, storage, climate-cost, longevity, skyline,
    desktop, code`.html); only the `class="on"` marker placement differs per page. The
    5 `*-app.html` tool pages have no nav at all (out of scope for the nav fix).
  - `bust_cache.py`'s `SCRIPTS` tuple (lines 22-24) is a hardcoded whitelist of `.js`
    files eligible for `?v=` stamping; `bgloop.js`, `margin-scene.js`, `biome-scene.js`,
    `force-graph-data.js`, `force-bg.js` are real, in-use files simply missing from that
    tuple — the regex itself already handles bare (no `?v=`) src attributes fine.
  - `climate-cost.html`'s arc-route reveal bug (arcs all finish revealing within the
    first ~660px of scroll) is caused by `drawArcs()`/`layoutArcs()` in
    `site/assets/margin-scene.js` hardcoding `top = -scrollY + 60` and `rowH = 30`
    instead of spreading rows across `docH` (the file already computes `docH` and uses
    it correctly for `cardItems`/`strataBands` — this is the pattern to copy).
  - Palette drift confirmed in two figures generated from zipped source (no local copy
    outside `site/downloads/*.zip`): `heat-code.zip:model.py` `fig_tornado()` (line 231)
    hardcodes seaborn-default hex `#4C72B0`/`#DD8452` instead of house palette;
    `storage-code.zip:model.py` `fig_dispatch_week()` (lines 168-169) uses matplotlib
    named colors `tab:red`/`tab:blue` instead of `figstyle.WARM`/`figstyle.COOL`.
    `figstyle.py` itself (already fixed earlier this session) is correct in both zips.
  - `bookshelf-demo-covers.png`/`bookshelf-demo-shelf.png` have no build script; they
    were manually exported once via `bookshelf-app.html`'s canvas `toBlob` "Download
    wallpaper" button and hand-copied into `site/assets`. No Python pipeline exists for
    this pair — recompression is a manual/one-off job either way.
- Decision items resolved this session:
  - **`01_world_fuel_mix.png` / `03_price_histories.png`** (light-themed, no generating
    script anywhere in the repo — checked every `build_*.py` and all three code zips):
    user chose **drop the `library.html` cards** for both rather than write new
    generators or leave them.
- Decision items still open (asked, not yet answered):
  - **`09_size_vs_lowcarbon.png`**: `library.html` caption/tag says "grammar of graphics
    / scatter of size vs. low-carbon share per country"; the actual generator
    (`build_atlas_figures.py` lines 247-273) produces a bar chart of installed capacity
    by fuel type, titled "Where the world's generating capacity sits, by fuel," and
    uses plain matplotlib (no plotnine import, contradicting the card's own tag). Asked
    the user whether to rewrite the caption, write a genuine scatter, or defer — user
    asked to clarify the question itself before answering; clarification not yet given.
  - **Three generated-but-unused figures**: `fig2_lcoh_stacked.png` (heat, source folder
    no longer exists on disk), `fig5_monthly.png` (storage, source folder no longer
    exists on disk), `fig2_lq_ranked.png` (longevity-quotient, exists at
    `longevity-quotient/outputs/fig2_lq_ranked.png`). No page references any of the
    three. Asked the user whether to wire in, delete the generation code, or defer —
    same clarification-requested state as above, not yet answered.

## Tried and rejected

- A prior audit fork claimed the homepage hero (globe/graph) renders as a blank box at
  desktop width and a clipped sliver at mobile width. Directly re-verified on the live
  production site at both 1600px and 390px — the globe renders fully and correctly at
  both sizes. Treated as a false positive from the fork (likely screenshotted before
  three.js finished loading); not a real bug, do not re-investigate.
- The same fork claimed `desktop.html`'s margin cards sit inconsistently close to the
  nav compared to other pages. Directly compared live screenshots of `desktop.html` and
  `skyline.html` (both use the same margin-scene `cards`/`bars` engine) — offsets are
  identical. Not a real bug, do not re-investigate.
- Asked both remaining decision questions (scatter/bar mismatch, three unused figures)
  as a single batched `AskUserQuestion` call — user rejected the tool call and asked to
  clarify the questions first, rather than answering. Whatever they raise needs to be
  folded into how those two questions get re-asked next session.

## Next

1. Ask the user what they want clarified about the two still-open questions (scatter-
   vs-bar mismatch on `09_size_vs_lowcarbon.png`; what to do with the three unused
   figures), then get real answers before planning around them.
2. Write the actual implementation plan (plan mode was interrupted before this step),
   now folding in the resolved decision (drop the two orphaned image cards) and
   whatever the remaining two resolve to.
3. Fix `longevity.html` line 22: "twenty orders of magnitude" → wording consistent with
   the correct "14.5 orders of magnitude" already stated at line 215.
4. Restructure nav on all 11 pages: move "Climate cost calculator" from a top-level
   link into the "Energy ▾" dropdown alongside Heat/Storage. Per-file edits differ
   slightly because the `class="on"` marker sits on a different segment per page (see
   State above) — not a single blind global find/replace.
5. Add `assets/bgloop.js`, `assets/margin-scene.js`, `assets/biome-scene.js`,
   `assets/force-graph-data.js`, `assets/force-bg.js` to `bust_cache.py`'s `SCRIPTS`
   tuple (lines 22-24), then re-run `bust_cache.py`.
6. Fix `climate-cost.html`'s arc reveal in `site/assets/margin-scene.js`
   (`layoutArcs()`/`drawArcs()`, ~lines 187-193 and 311-337): derive each row's
   document-space `y` from a fraction of `docH` instead of the hardcoded
   `top = -scrollY + 60` / `rowH = 30`.
7. Drop the `01_world_fuel_mix.png` / `03_price_histories.png` cards from
   `library.html` (lines 20-37) per the resolved decision above.
8. Recompress `bookshelf-demo-covers.png` and `bookshelf-demo-shelf.png` (open
   `bookshelf-app.html`, or write a one-off PIL resize/optimize pass on the existing
   PNGs directly — no source pipeline exists either way).
9. Fix the two off-palette figure functions in the extracted zip sources
   (`heat-code.zip:model.py fig_tornado()`, `storage-code.zip:model.py
   fig_dispatch_week()`), regenerate, re-copy into `site/assets`, re-zip the download.
10. Resolve the two still-open flagged items per user decision from step 1.
11. Create a new, dated, non-published markdown log (do not silently reuse/overwrite
    `SITE_AUDIT_FINDINGS.md`'s older unresolved items without folding them in) recording
    every change made this pass, matching the "what/why/implication" structure of the
    existing findings doc.
12. Re-run `tests/test_markup.py` and the `node tests/*.js` harnesses; verify every new
    or touched script tag resolves (200) on every page it's on.
13. Visually verify nav on all 11 pages and the longevity.html text fix in-browser
    before considering the pass done.
14. Do **not** publish until the user explicitly says the word "publish" (standing rule
    for this project, reconfirmed multiple times this session).

## Files

- `site/longevity.html` — line 22 has the wrong "twenty orders of magnitude" claim;
  line 215 has the correct "14.5 orders of magnitude" to match.
- `site/{index,atlas,model,library,heat,storage,climate-cost,longevity,skyline,desktop,
  code}.html` — the 11 pages carrying the `<nav class="top">` bar that needs the
  Climate-cost-calculator move into "Energy ▾".
- `bust_cache.py` — `SCRIPTS` tuple at lines 22-24 needs the 5 missing filenames added.
- `site/assets/margin-scene.js` — `layoutArcs()`/`drawArcs()` (~lines 187-193, 311-337)
  need the `docH`-relative fix for climate-cost.html's arc reveal.
- `site/assets/bookshelf-demo-covers.png`, `site/assets/bookshelf-demo-shelf.png` —
  oversized, need recompression; source is `site/bookshelf-app.html`'s manual export.
- `site/downloads/heat-code.zip`, `site/downloads/storage-code.zip` — contain the
  `model.py`/`figstyle.py` sources for the two off-palette figures; must be extracted,
  fixed, regenerated, and re-zipped (no unzipped working copies exist elsewhere).
- `site/library.html` — lines 20-37 (01/03 image cards, to be deleted per resolved
  decision), lines 69-73 (`09_size_vs_lowcarbon.png` card — caption/tag to reconcile,
  still pending clarification).
- `SITE_AUDIT_FINDINGS.md` (repo root, not published) — older unresolved-findings log;
  this pass's new changes should be logged in a markdown file following the same
  pattern (new file or a clearly dated new section — additive to, not necessarily
  merged into, this existing file).
- `sync_assets.py` — governs which generated figures get copied into `site/assets`
  (only if referenced by an `<img>` tag); relevant if the three unused figures get
  wired into a page.
- `C:\Users\dasil\.claude\plans\read-revamp-brief-md-then-handoff-md-streamed-parasol.md`
  — stale (describes an already-completed, unrelated prior pass); needs to be
  overwritten with the real plan for this revamp before implementation resumes.
