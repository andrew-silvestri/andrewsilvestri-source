# Audit — the longevity quotient app

Read `prompts/_HOUSE_RULES.md` first. Then this.

You are auditing `site/longevity-app.html` and, where it bears on the app, the
page that introduces it, `site/longevity.html`. **This is a read-only job.**
Change nothing in `site/`. You produce one document.

## What this thing is

Body mass predicts lifespan across roughly fourteen orders of magnitude. The
longevity quotient is what is left after that relationship is divided out — how
long an animal lives against how long an animal of its size should live. The
app lets a reader explore 7,873 species.

Source lives in `longevity-quotient/`: `build_lq.py`, `update_page.py`,
`fig_lq_explained.py`, `data/` (AnAge, Amniote, PanTheria merges), `outputs/`,
`DATA_SOURCES.md`, and tests (`test_fit_strategy.py`, `test_merge.py`,
`test_perf.js`). Unlike two of the other apps, this one **has** its source.
Use it.

`longevity-app.html` is 998 KB — the largest file on the site by a wide margin.
Understanding what is in those bytes is part of the job.

## Do your own work first

Write your own findings before reading anyone else's. `DESLOP_AUDIT_2026-09-04.md`
at the repo root contains a site-wide audit that touches this app, and there is
a checklist at the bottom of this file. **Open neither until §5 below.**

## 1. Make it run and drive it

Serve locally (`python -m http.server 8801` from `site/`) — not `file://`.
Drive it with Playwright from a scratch folder outside `site/`, gitignored.
Work at 1440×900 and 390×844, motion on and off.

## 2. Does it work

Exercise it as a user would, not as a smoke test. Every control, every sort,
every filter, every combination you can reach. Record what breaks, what does
nothing, and what does something other than what its label says.

Specific things to check, none of which are the whole list:

- **Sentinel values in the interface.** A `-999` was reported reaching the UI
  as a common name (*Terrapene mexicana*, row 6 of the default view). Verify
  whether it is still there, then grep the whole payload for other sentinels —
  `-999`, `-1`, `NA`, empty strings — reaching any user-visible field.
- **The default view.** What does a first-time visitor see before touching
  anything? Is it the most interesting possible first screen, or an artifact of
  sort order?
- **URL state.** Does any view survive a copy of the address bar? If not, that
  is a finding with a large blast radius: it means no result in this app can be
  cited, linked or shared, and it means `longevity.html`'s claims (for example
  "the bats of Chiroptera at 2.68 across 267 species") cannot link into the
  evidence for them.
- **Empty and edge states.** A filter matching nothing. A species with missing
  mass or missing lifespan. The extremes of the mass range.

## 3. Is it honest

This matters more here than anywhere else on the site, because the app's whole
claim is that it divides out a fitted relationship and shows you the residual.

- Where does the fit come from, what is its form, and does the app say so
  anywhere a reader will find it?
- Wild versus captive lifespan is a known confound in this literature. Read
  `DATA_SOURCES.md` and the merge scripts, find how it is handled, and check
  whether the app tells the reader.
- Are records with weak provenance marked, dropped, or silently mixed with
  strong ones? `outputs/provenance.csv` exists — find out whether the app uses
  it.
- Do the numbers in the app agree with the numbers in `outputs/` and with the
  prose on `longevity.html`? Check specific values, not spot vibes.
- Is anything on screen a placeholder or an assumption presented as a
  measurement?

## 4. Measure it

- **Weight.** What are the 998 KB? Split the payload: embedded data, code,
  styling, anything duplicated. How much of it does the first screen need? Is
  any of it dead?
- **Time to interactive** on a cold load, at both viewports, and on a throttled
  connection.
- **Type and contrast.** Every distinct rendered size; flag under 12px. Compute
  every text/background ratio, including text over plot areas.
- **Mobile.** Is this usable at 390px, or nominally responsive and actually
  unusable? Tables and scatter plots are the usual casualties. Say plainly
  whether a phone reader can do anything real here.
- **Motion contract.** Does `data-motion="off"` stop everything that moves?

## 5. Then cross-check

Only now, and in this order: `DESLOP_AUDIT_2026-09-04.md` (its findings on this
app), then `DESIGN_AUDIT_EXTERNAL_2026-08-30.md` §7 and its "What's missing"
§7, then the checklist at the bottom of this file. Append a section saying what
they caught that you missed, what you caught that they missed, and anything in
them you think is wrong.

## 6. Write it

`AUDIT_LONGEVITY_2026-09-04.md` at the repo root. Evidence in `_audit-longevity/`,
gitignored. Each finding: what was observed with file and line and measured
value, why it hurts, severity, what fixing it costs. Ranked.

Include a section **"What is good and must survive"** — the same weight as the
findings. And a section **"What is not fixable in this app"**, separating
problems of the interface from problems of the underlying data.

Then stop. Propose nothing, fix nothing, wait.

---

## Appendix — completeness checklist

**Do not read until §6 is written.** Unverified suspicions from someone who has
not measured. Several may be wrong; the list is certainly incomplete. For each,
say whether you found it independently, and if not, whether your method should
have.

<details>
<summary>Open only after your own findings are written.</summary>

- The `-999` sentinel as a common name in the default view.
- No URL state, so no view is shareable and no claim on `longevity.html` can
  link into its evidence.
- 998 KB, most of it probably an embedded dataset shipped whole regardless of
  what the reader looks at.
- The ranked lollipop figure on `longevity.html` wastes the left half of its
  panel because the ×1 baseline sits mid-panel and the visible top-25 all
  extend right.
- Wild-versus-captive handling may be invisible to the reader.
- Control labels below 12px.

</details>
