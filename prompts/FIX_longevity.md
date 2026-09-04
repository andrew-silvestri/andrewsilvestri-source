# Fix — the longevity quotient

Acts on `AUDIT_LONGEVITY_2026-09-04.md`, which you wrote. Read
`prompts/_HOUSE_RULES.md` and the **shared rules** at the bottom.

## The blocking one: "wild maximum" is mostly not wild

4,015 of 6,387 values labelled "wild maximum" come from Amniote, FishBase and
AnAge records that carry no wild/captive field, and `ingest.py` routes AnAge
"origin unknown" into wild as well. The app then presents all of it under one
label.

This is the same defect as the climate-cost shoe in a different costume: a
label asserting a provenance the data does not have, in the direction that
makes the project look better. A captive maximum is systematically longer than
a wild one, so mislabelling inflates exactly the quotient the page is about.

Fix the label, the routing, or both — but do not fix it by quietly widening
what "wild" means. Options, and I want your recommendation rather than your
choice: split the bar into known-wild and unknown-origin; grade it; or drop the
wild/captive distinction where the data cannot support it and say so.

`outputs/provenance.csv` exists and is neither shipped nor shown. That is the
obvious raw material for whichever route you take.

## The second data problem

**28 amniotes with 1–3 month maxima at up to 5 kg** — an Indian hare at 1
month and 2.2 kg — sit at the bottom of every ranking, are graded B, and are
the default "low" end of the published `lq_ranked.png`. A 2.2 kg mammal does
not live one month. These are bad records driving a published figure.

Decide a defensible exclusion rule, state it on the page, and regenerate the
figure. Do not hand-remove species.

## The prose contradicts the code

`longevity.html` describes one fit strategy; the code runs
`FIT_STRATEGY="filter"`, unweighted, on raw counts. **The app's own text is
correct and the page's is not** — so this is a page fix, not a model fix.

While you are there, the same animal has three numbers depending on where you
look: ant queen 28.72 vs the page, quahog "forty-five" vs 47.48, the Chiroptera
link landing on 2.66 against a sentence saying 2.68, amphibian r² "0.12 over
24" against 0.043 over 8. Pick the authoritative source for each and make
everything agree with it. Say which you picked.

## The template trap, which is live here

The palette fix and the `-999` fix exist **only in
`site/longevity-app.html`, not in `template.html`.** A rebuild regresses both.
Reconcile the template first, then prove a rebuild is a no-op. `test_perf.js`
also cannot run as checked out — fix or document.

## The rest

- **Mobile is unusable.** Chrome takes most of the viewport, four rows visible,
  384 of 400 names truncated. This is the worst mobile result of the four
  audits.
- **The motion contract is ignored**: 438 transitions run on re-sort under
  `data-motion="off"` and under `prefers-reduced-motion`. The site's manual
  toggle was removed yesterday, so that preference is now the only gate.
- Log bars from a floating origin with no parity line in the default view;
  hue-only wild/captive encoding; sub-12px styles; keyboard-inaccessible rows.

## Corrections to my brief, which you already caught

URL state exists and works; `-999` no longer reaches the UI; the lollipop no
longer wastes its left half. All three of my premises were stale. Good — and
note that none of your three highest findings were on my checklist, which is
the outcome the sealed appendix was supposed to produce even though `cat`
defeated the seal.

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
- Write `FIX_LONGEVITY_2026-09-04.md` at the repo root: what changed, your
  recommendation on the wild/captive label with its reasoning, the exclusion
  rule you chose, the rebuild-is-a-no-op proof, and what is left.
- Stop when it is written. Give me the local URL.
