# Fix — the longevity quotient

Acts on `AUDIT_LONGEVITY_2026-09-04.md` per `prompts/FIX_longevity.md`.
Nothing committed, nothing published, `bust_cache.py` not run, `style.css` and
`index.html` untouched. Local server: **http://localhost:8801/longevity-app.html**
(page: http://localhost:8801/longevity.html), served from `site/` on port 8801
and left running.

## 1. What changed

**Generator and source (`longevity-quotient/`)**

| file | change |
|---|---|
| `data/ingest.py` | Third lifespan column `unknown_yr` for a maximum whose source did not record origin. AnAge "origin unknown" → unrecorded (was: wild). Amniote, PanTHERIA, AmphiBIO → unrecorded (was: wild). FishBase: only a value taken from its `LongevityWild` field is wild; a per-population `tmax` is unrecorded. `origin` column added to `provenance.csv`; `origins` census added to `ingest_report.json`. Common names: `-999`, `NA`, `null` → empty; stray `<b>` tags stripped. |
| `build_lq.py` | Reads the third column into `average` and `maximum`. **Outlier rule** (`demote_outliers`, §3). `origin_census` and `outlier_rule` written to `summary.json`. `lq_table.csv` gains `unrecorded` and `note` columns. Group summary, the ranked figure, the orders figure and the console report now rank grade A and B only, which is what the visualiser shows by default. Payload gains column `u`. |
| `template.html` | Reconciled from the shipped file first (URL state, `-999` guard, `--acc-fill` tokens were only in `site/`), then: third bar state, parity-anchored bars, motion contract, phone layout, type floor, borders, keyboard access, prose. Detail in §6. |
| `update_page.py` | Arithmetic section rewritten to say what runs. `mass_str()` replaces `{lo:,.0f}` ("0 g"). Data section carries the origin counts. Sources table says which sources have no origin. New generated passages: the group-comparison paragraph, the "what comes out" paragraph, the 24 margin quotients, the bird/mammal ratio, the amphibian rejection, the order count (prose and caption), the intro mass range. Patterns match their own output, so a second run is a no-op (verified: two consecutive `--apply` runs, identical change list, exit 0). |
| `test_merge.py` | Reads the third column; new check that no Amniote/PanTHERIA/AmphiBIO row lands in the wild column. 22/22 pass. |
| `test_perf.js` | Runs now. The cause was not the script: `node_modules` was a dangling symlink to `/tmp/node_modules`. Replaced with a real install; `package.json`/`package-lock.json` added with `jsdom` as the one dev dependency. 12/12 pass. One line in the app (`syncHash`) wraps `replaceState` in try/catch because jsdom runs the page at `about:blank`. |
| `data/animals_merged.csv`, `outputs/*` | Regenerated. Figures 1, 2, 4 changed; figure 3 (wild against captive, the 309 paired rows) is byte-identical. |

**Shipped (`site/`)**

| file | change |
|---|---|
| `longevity-app.html` | The build output, copied. 1,023 KB (was 998; `+u`, `+note` columns). |
| `longevity.html` | `update_page.py --apply` plus five hand edits: the visualiser card describes three bars and parity; the explainer caption says it uses the all-animal fit; the ranked-figure and orders-figure captions say grade A–B; the orders figure's `height` attribute (1617, was 2125). `?v=` stamps not touched (the sweep's job). |
| `assets/lq_allometry.png`, `lq_ranked.png`, `lq_orders.png`, `lq_wild_captive.png` | Copied from `outputs/`. Same pixel sizes except `lq_orders` (1428×1617, was 2125 tall: fewer orders qualify under A–B). |
| `downloads/longevity-code.zip` | Rebuilt from the source tree, same 18 entries plus `package.json`. The zipped `lq_table.csv` and `animals_merged.csv` no longer carry `-999`. |

## 2. Wild against captive: recommendation and what was done

**Recommendation: split, do not grade, do not drop.** Three states — wild,
captive, origin not recorded — each drawn differently and each labelled as
what it is. Implemented.

Why not the other two:

- **Grading it** conflates two different facts. The grade says how good the
  *record* is; origin says what the record *is of*. An Amniote figure can be a
  perfectly defensible literature estimate (B) and still be of unknown origin.
  Folding origin into the grade would either demote 3,482 sound records or
  leave the label wrong.
- **Dropping the distinction** throws away the 309 paired rows and the ~4,000
  rows AnAge and the seed did label, which are the only content the
  wild-against-captive argument on the page has. It also makes "Wild only" and
  "Captive only" impossible, and those are now the one honest way to see the
  asymmetry.

The census after the change (`ingest_report.json → origins`):

| origin of the record's maximum | species |
|---|---|
| unrecorded | 3,482 |
| wild | 2,596 |
| captive | 1,486 |
| wild + captive | 309 |

So the wild column went from 6,387 rows to 2,905 (2,596 + 309): seed 412,
AnAge 1,870, FishBase 623. Of the audit's 4,015 "unlabelled" rows, those 623
FishBase rows did come from a field FishBase itself calls `LongevityWild` and
stay wild; the other 627 FishBase rows (a per-population `tmax`) are
unrecorded, as are all 2,649 Amniote, all 116 AmphiBIO and 90 AnAge rows. The
audit counted all 1,250 FishBase rows as unlabelled, which overstated it by
623.

What the reader sees: a solid bar (wild), a hollow bar (captive), a hatched
bar (origin not recorded); the legend names all three; the detail panel has a
row for each; the app's prose section is retitled "Wild, captive, and not
recorded" and gives the counts. **Lifespan used** is now *Longest* (default),
*Average*, *Wild only*, *Captive only* — the last two use nothing but a figure
a source labelled, and the count line shows the table shrinking to 2,205 and
1,749 species respectively. Nothing that was unlabelled has been relabelled in
either direction.

`provenance.csv` now carries `origin` per species. It is still not shipped
inside the app (it would add ~16 KB dictionary-encoded); the detail panel shows
grade and origin, not the source name. Left for later (§9).

## 3. The exclusion rule

**Rule:** before the final fit, a preliminary fit per pool (A and B,
non-colonial, same pooling and same rejection test as the final fit) gives a
residual for every record. A grade-B record more than **3 residual standard
deviations** from its pool's fit, in either direction, is demoted to grade C.
Grade A is exempt. Nothing is deleted; the note on the row says why
("demoted to C: 138x below its group's fit, past 3 sd").

Why this and not a lifespan floor: the bad amniote records are not a cluster at
one value, they are a tail (29 at ≤ 3 months, 23 at 3–6 months, 31 at 6–9
months, 52 at 9–12 months). A floor either stops too early or starts eating
real short-lived animals. Three sigma on the fit is the ordinary regression
outlier criterion, it is mass-aware, it is symmetric so it cannot be accused of
only removing what hurts, and it exempts exactly the records that were checked
by hand — Labord's chameleon at 0.13× and the ocean quahog at 47× are grade A
and untouched.

Result: **57 demoted** (mammals 31, birds 10, fish 8, reptiles 8). Residual SD
per pool in log10: birds 0.22, fish 0.30, reptiles 0.36, mammals 0.39, so the
threshold is roughly 4.5× for a bird and 15× for a mammal.

- 49 on the low side, from 138× below (Indian hare, 1 month at 2.2 kg) to 4×
  below (black rail). All 28 from the audit are in it. The low tail in the
  0.5–1 yr band that survives (e.g. toolache wallaby 0.07×, lesser cane rat)
  is now the bottom of the A–B ranking; those are inside 3σ and I have not
  hand-removed them, per the brief.
- **8 on the high side**, which the brief should know about: pink cockatoo
  83 yr (5× above), and seven fish at 8–11× above — splitnose rockfish, black
  oreo, Pacific ocean perch, shortspine thornyhead, a mormyrid, tiger rockfish,
  warty oreo. Several of these are probably real (Sebastes are famously
  long-lived, and the A-grade rougheye rockfish at 205 yr stays), but they are
  uncorroborated compilation figures that the rest of their group cannot
  account for, and "uncertain, shown under Include C" is the honest label. The
  page's margin still lists the pink cockatoo at 4.51×; that number is now a
  grade-C figure. Left as is and noted (§9).

Stated on the page (arithmetic section, generated) and in the app ("Data grade"
section, count generated from `FITS.outlier_rule`). The ranked figure is
regenerated over A–B; its lower half is now silkmoth, wasp, octopus, squid,
Labord's chameleon and the like, which is what the page always claimed it was.

Fit changes from removing the artefacts: mammal intercept 0.320 → 0.357, r²
0.37 → 0.40; global r² 0.30 → 0.32. Chiroptera's geometric mean fell from 2.68
to 2.53 because the mammal baseline it is measured against rose.

## 4. Prose against code, and one number per animal

**Authoritative source: `outputs/` (maximum lifespan, own-group fit, grade A
and B).** The page, the figures and the CSVs all used maximum; only the app's
default used average. The app default is therefore changed to *Longest*
(`met='mx'`), and links with `met=a` still mean average. The page's eleven
group links drop `grade=all` because the group summary is now A–B like the app
default. Every number below now comes from one place:

| item | was | now | owner |
|---|---|---|---|
| fit description | "weighted OLS … Kish n_eff … factor of two" | unweighted OLS on A–B, C held out, no weights, outlier rule stated; counts are raw | `update_page.py` |
| black garden ant queen | 28.72 (margin) / "twenty-seven" (prose) / 21.78 (app) | 28.72 everywhere | table |
| ocean quahog | "forty-five" / 47.48 | 47 / 47.48 | table |
| Chiroptera | "2.68 across 267" vs link 2.66 | 2.53 across 261, link lands on 2.53 | `group_summary.csv` |
| amphibian rejection | "r² 0.12 across twenty-four" | r² 0.04 across 83 | `summary.json` |
| birds vs mammals | "1.8 times" (page) / "twice" (app) | 2.2 (page, computed at 1 kg) / "twice" (app, unchanged wording) | fits |
| mass range | "from 0 g" / "nematode at a microgram" | "rotifer at 0.5 µg to 150 tonnes" | data |
| orders ≥ 4 species | 112 (114 in csv) | 81 (A–B) | `group_summary.csv` |
| explainer figure | global-fit LQ presented as the quotient | caption says all-animal fit; human 5.0 own-group vs 4.0 | caption |
| margin quotients | hand-typed, several stale | 24 rewritten from `lq_table.csv` on every run | `update_page.py` |
| "what comes out" | typed, stale, included data errors | generated from the A–B top 6 / bottom 5 | `update_page.py` |
| grade census | ingest counts only | ingest counts, then post-rule counts, both stated | both |

## 5. The template trap

Order followed: template first, then shipped, then proof.

1. `template.html` regenerated from `site/longevity-app.html` with the data
   literal and `FITS` replaced by the two placeholders — that alone recovered
   the URL-state block, the `-999` guard and the palette tokens that had only
   ever been hand-patched into `site/`.
2. All app changes made in the template. `build_lq.py` writes
   `longevity-quotient/longevity.html`; that is copied to `site/`.
3. **Proof:** `ingest.py --apply` → `build_lq.py` → `cmp longevity.html
   ../site/longevity-app.html` → identical; run `build_lq.py` again → identical
   again. And stripping the data and `FITS` back out of the shipped file
   reproduces `template.html` byte for byte (`template == shipped minus data:
   True`). `update_page.py --apply` twice in a row: same change list, exit 0.

One wrinkle for the record: another session's commit `c2d02aa` (17:03, a
climate-cost message) swept up an intermediate state of `template.html`,
`longevity.html` and `site/longevity-app.html` (the try/catch line only). The
working tree supersedes it; nothing to do.

## 6. The rest

- **Mobile.** Below 700 px the panel is a normal block, closed behind one
  sticky 41 px "Adjust the view" button; rows are 48 px with the name on its
  own full-width line above the bar; buttons and inputs are 44 px tall.
  Measured at 390×844: 17 rows visible per screen (was 4); 10 of 400 names
  still truncate (the Reptile-Database compound names, 60+ characters); no
  horizontal overflow; no value label off-screen.
- **Motion.** Pre-paint script sets `data-motion` from
  `prefers-reduced-motion` (the site's toggle is gone, so that is the gate);
  CSS honours both the attribute and the media query directly. Measured on a
  re-sort of 400 rows: 487 `transitionrun` events with motion on, **0** under
  `prefers-reduced-motion: reduce`, in both colour schemes.
- **Bars from parity.** In quotient mode the scale always contains 1 and every
  bar runs from the parity line (left for < 1, right for > 1). Default view
  now shows the parity line (at 9.7% of the track) and "10.0"; the group view
  no longer overprints "1.00" on "1 · as predicted". Years mode is unchanged
  (§9).
- **Hue-only encoding.** Wild solid, captive hollow, unrecorded hatched. The
  two colours still measure 1.32:1 (light) / 1.01:1 (dark) against each other
  and no longer need to.
- **Type.** Every rendered size ≥ 12 px in both schemes (was five styles at
  10.5–11.7 px). Measured: 12, 12.5, 13, 13.5, 14, 16, 20, 27.
- **Keyboard.** Rows are `role=button`, `tabindex=0`, Enter/Space open the
  detail panel (verified: focus first row, Enter → panel opens). Search and
  both selects have `aria-label`; each segment group is `role=group` named by
  its label; buttons, inputs and focused rows get a 2 px accent outline.
- **Amphibians.** The detail panel now says "no group fit — uses all animals"
  and shows the quotient it actually ranks by, instead of a dash beside a bar.
- **Dead CSS** (`canvas, #gl, #view, #stage`, `#app`) removed.

## 7. Contrast, recomputed (WCAG, against page background unless noted)

| element | light | dark |
|---|---|---|
| all text styles (24 pairs, both schemes) | ≥ 4.57 | ≥ 5.28 |
| wild bar | 5.43 | 6.11 |
| captive bar (border) | 7.18 | 6.05 |
| unrecorded bar (`--unk` #6b7186 / #7d849c) | 4.45 | 5.33 |
| group bar | 4.48 | 7.20 |
| average tick (opacity .75) | 7.27 | 9.04 |
| parity line (opacity .9) | 5.73 | 5.06 |
| range line (opacity .85) | 3.40 | 5.47 |
| gridlines (`--rule`, was 1.32 / 1.40) | 3.52 | 4.21 |
| segment / input / toggle borders (`--line`, was 1.28 / 1.12) | 3.83 on card, 3.52 on bg | 3.84 on card, 4.21 on bg |
| white on pressed button | 7.82 | 6.60 |

Everything a reader has to read or hit is ≥ 3:1 (graphics/boundaries) or
≥ 4.5:1 (text). Measured by script in the rendered page, not from the palette.

## 8. Verification

`_audit-longevity/verify.js` (Playwright 1.62, Chromium), against the shipped
file: no page errors, no console errors, load to first rows 151 ms; the
checks in §6–§7; the page's own links land on the numbers the page prints;
`#sort=bogus&fRank=or&fVal=Nope` still degrades to the first taxon
alphabetically (unchanged, §9); `test_merge.py` 22/22; `test_perf.js` 12/12.
Screenshots `fix-*.png` in `_audit-longevity/`.

## 9. What is left

- **`?v=` cache stamps** on `longevity.html` for the four figures and the
  download are stale; `bust_cache.py` is the sweep's. The app has no stamp.
- **The unknown-taxon fallback** (`fVal=Nope` → first taxon alphabetically)
  is untouched; audit F12.
- **Years mode** still draws log bars from a floating floor (0.85 × the
  smallest visible value). Only quotient mode is parity-anchored.
- **The eight high-side demotions** (§3) are probably-real long-lived fish
  now hidden by default, and the margin shows the pink cockatoo at a grade-C
  4.51×. If that is wrong, the fix is a one-sided rule or a corroboration
  exemption, not a hand edit.
- **Provenance in the app.** `origin` is drawn; `taken_from` is not shipped.
- **Payload** is 1,023 KB, up 25 KB (the `u` and `note` columns). The audit's
  derivable columns (`pg`, `pc`, `a`, `mx`, `ki`, `c`, ~265 KB) are still
  shipped.
- **Ten long names** truncate on a phone; the rest wrap onto their own line.
- **`load_anage.py` and `merge_anage.py`** are the older loaders, not in the
  pipeline; `load_anage.py` still says unknown origin is "assumed captive",
  which was never what the live pipeline did and is now wrong in the other
  direction. `README.md` describes two lifespan columns. `DATA_SOURCES.md`
  quotes pre-rule quotients (ant queen 29×, still right; rougheye 12.9×, now
  13.1×). Documentation, not code.
- **`lq_explained.png`** still uses the all-animal fit; the caption says so
  now, but the figure itself is `fig_lq_explained.py`'s to change.
- **HANDOFF.md** does not yet mention the third lifespan column or the
  outlier rule.
- `rezip_downloads.py`, `skyline/*`, `site/skyline-app.html`,
  `climate-cost/*` and `FIX_SKYLINE_2026-09-04.md` are modified in the working
  tree by other sessions, not by this one.
