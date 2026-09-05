# Fix — Skylines, played

Acts on `AUDIT_SKYLINE_2026-09-04.md`; brief `prompts/FIX_skyline.md`. Not
committed, not published, `bust_cache.py` not run. Local:
**http://localhost:8802/skyline-app.html** (and `/skyline.html`), served from
`site/` on port 8802.

Evidence: `_audit-skyline/verify.js` → `verify.json`, `shots/fix-*.png`;
patch scripts that made every edit, in order, in `_audit-skyline/patches/`.

## Generator first

The zip was the only copy of the generator and was three palette lines behind
the shipped page. Before touching anything:

1. `site/downloads/skyline-code.zip` unpacked to a tracked **`skyline/`**
   folder beside `heat/` and `storage/`.
2. `skyline/template.html` reconciled with the shipped head (the `--acc-fill`
   tokens and `#spin.on`).
3. `python skyline/build_app.py` → byte-identical to `site/skyline-app.html`
   as it then stood (340,666 bytes, `cmp` clean). Baseline proven.
4. `rezip_downloads.py` given a `skyline` target and a skip list
   (`node_modules`, `__pycache__`, `package*.json`, the built page), so the
   download is rebuilt from the folder like heat's and storage's.

The raw Wikidata pull is still absent, so `build_skylines.py` still cannot
run. It was edited anyway to emit the new payload shape (below), with a
docstring saying why it cannot currently be run; the shipped
`data/skylines.json` was brought to that shape by a kept one-off,
`skyline/prune_payload.py`, which is idempotent.

## The blocking one: the label and the data

**Decision: the data and its label come out.** The app never read the
panorama (`prof`, `draw`, `view`, `dist`, and the viewpoint bearings inside
`towers` and `look`); making it read them would mean rebuilding the retired
rendering. So:

- `prof`, `draw`, `view`, `dist` removed from the payload; `towers` reduced to
  name, height, year; `look` (the starting bearing) recomputed as the wheel
  slot of the tallest tower instead of the retired viewpoint's bearing.
  Added: `ringFloor` (55) at the top level and `listFloor` on the three
  supplemented cities. Payload 281 KB → 169 KB; page 341,568 → 232,143 bytes.
- `skyline.html` "What is measured and what is invented" rewritten:
  **Measured** is now heights, coordinates, compass order and provenance per
  city; **Assumed** (the footprint width, which the wheel never used) is
  replaced by **Chosen** (standpoint, 400 m clamp, 55 m and 80 m floors, 120
  cap, the supplement override floor); **Rearranged** now says plainly that a
  wheel has no empty horizon; **Invented** unchanged. A dated note says what
  the section used to claim.
- "How the bars become sound" rewritten as a five-row table of the actual
  mapping — chord note by position, loudness as share-of-tallest^1.6
  normalised per city, seven-voice cap, spectral tilt and the triangle/sine
  timbre, the filter chain — every row headed as a choice.
- In the app, a **How it sounds** panel states the same mapping in one
  paragraph, opening "All of this is invented — chosen, not measured", and a
  **Voiced as …** line under the key names this city's voicing and ends "A
  choice, like the key."
- Sidebar rows now read "On the wheel: 27 at or above 55 m", "Standing: at
  the height-weighted centre of them", and a **Heights** row: for Fort Worth
  "27 of 27 from the city's published tallest-buildings list (Wikipedia);
  above 61 m the list overrules Wikidata"; for a Wikidata city "Wikidata,
  each tower linked below". The tooltip writes "under 0.4 km" for the 106
  clamped towers instead of a number.

`build_skyline_figure.py` reads `towers` (name and height) from the payload;
it still does, and it was re-run: `skyline_towers.png` is byte-identical
(md5 `d9212408…` before and after), 0 layout problems. No cache stamp
changes.

## The mode filter — diagnosis and decision

**Diagnosis.** `setKey()` took scale degrees 1, 3, 5, 6 of whatever the mode
was (`[0,2,4,5]` as indices into the mode's step list), then dropped any
pitch closer than 2.9 semitones to the one below it. Two things went wrong at
once. The index pick never selects a flattened second, so hijaz and insen
lost the tone that defines them before the filter ran; and the filter, being
adjacency-based across the whole ladder, took out the major sixth (7→9 is
two semitones) and hijaz's flattened sixth (7→8). Result: eight modes, five
pitch-class sets; hijaz = major triad; insen = pent minor = blues.

**Decision: fix it, in the app — it is cheap, and the keys deserve it.** A
per-mode voicing table (`VOICING` in `app.js`), in semitones from the root,
with a `ground` set for the lowest octave and an `upper` set for the two
above, chosen so the minor-third rule *never fires* — it stays in the code as
a safety net that counts what it removes, and the harness asserts zero.

| mode | lowest octave | above | what it keeps |
|---|---|---|---|
| major | 0 4 7 | 0 4 7 | the triad |
| minor | 0 3 7 | 0 3 7 | the triad |
| hijaz | 0 4 7 | 1 4 7 | the flattened second, an octave up over the major third |
| pent major | 0 4 9 | 0 4 9 | third and sixth, no fifth |
| yo | 0 5 9 | 0 5 9 | fourth and sixth, no third |
| pent minor | 0 3 7 10 | 3 7 10 | the minor seventh |
| blues | 0 3 7 10 | 3 6 10 | the blue fifth, an octave up |
| insen | 0 5 10 | 1 5 10 | the flattened second, an octave up |

The compromise, stated on the page: the semitone that defines hijaz and insen
cannot sit beside the root under a minor-third floor, so it sits an octave
up (a minor ninth against the root below it — the flamenco/Phrygian-dominant
sound, which is what people hear as "hijaz" anyway). A reader who wants the
maqam's own tetrachord is not getting it and is told so.

Measured after: 8 distinct shapes for 8 modes; 19 of 19 key labels are
acoustically distinct (verified live across all 27 cities in both schemes);
closest sounding interval 3.0 semitones; highest partial 1,397 Hz; loudest
bearing 1.0× the quietest; 7 voices max. Dubai now sounds D2 D3 Gb3 A3 **Eb4**
Gb4 A4 where Vienna sounds D2 D3 F#3 A3 D4 F#4 A4.

Where the claim could not be made true it was changed: "no bearing can
produce a dissonance" is now "no two sounding notes are closer than a minor
third", which is what the code guarantees.

## The rest

- **55 m floor** — on screen in the "On the wheel" row; the supplement
  override floor in the **Heights** row.
- **Motion contract.** The template head now carries the site's blocking
  snippet (a copy: apps load no shared scripts), sets `data-motion` before
  first paint from `prefers-reduced-motion`, and dispatches `motionchange`
  on change. The app reads it: **off** means bars snap to their value, peak
  markers sit on the bars instead of falling, Spin is hidden and Space does
  not spin. Drag, wheel and arrows still turn — that is the reader's own
  hand. **Audio is not gated by motion.** A preference for less motion is a
  preference about the screen; the audio gate is Play/Stop, and a reader who
  wants neither has both controls. Verified: with `reduce` emulated, Spin
  hidden, meter snap error 0.00000, audio still plays at the same gain;
  flipping the preference live restores Spin.
- **Type.** The app declares the site's `--fs-2 / --fs-1 / --fs1` (12 /
  14.5 / 21 px) and uses nothing else. Rendered sizes are now exactly
  {12, 14.5, 21}; **0 elements under 12 px** (was 54). Canvas text (compass,
  tower labels) is 12 px on every viewport (was 11, and 10 on a phone).
- **Buttons and boundaries**, recomputed from the rendered page:

  | element | dark | light |
  |---|---|---|
  | Play fill (`--acc-ink` on `--acc-fill`) | 5.88 | 7.82 |
  | Play / Stop / Spin outline (`--acc` on panel) | 5.78 | 6.71 |
  | Stop and Spin text (`--ink` on panel) | 15.19 | 14.89 |
  | select border (`--dim` on panel) | 6.21 | 5.02 |
  | select text | 14.51 | 17.36 |
  | every text node in the sidebar | ≥ 5.84 | ≥ 5.02 |
  | hint and bearing over the footer wash (by hand) | 6.19 | 4.83 |
  | compass points at their faintest (alpha floor 0.8, was 0.35) | 4.9 | 3.6 |

  The brief's "2:1-ish on `#spin.on`" — `#spin.on` was already 5.88 after the
  palette pass; the failing control was the Play button at 2.91, which used
  `--acc` not `--acc-fill`. Fixed at the token. The remaining sub-3:1
  hairlines are `--rule` on non-control elements (section rules), which the
  UI floor does not cover.
- **No text form of the sound.** A line under the meter, `#notes`, names the
  notes sounding now, lowest first, spelled with flats where the mode is
  flat-side: "sounding D2 D3 Gb3 A3 Eb4 Gb4 A4", or "stopped · would sound …"
  before Play. It reads the same `sounding()` set the audio does, so it is
  exactly what is sent to the output, and it updates only when the set
  changes. That is the whole proposal: not a transcript, a reading — the
  meter is the sound as bars; this is the sound as names. The canvas also
  got `role="img"` and a label pointing at the panel and the line. No live
  region: a line that changes several times a second while spinning would
  make a screen reader unusable; a screen-reader user can navigate to it.
- **Silent-but-"Stop".** 800 ms after Play, if the context is not `running`,
  `#noaudio` says so and points at the notes line. The API cannot see a
  hardware mute switch; the notes line is what covers that case.
- **Space on a focused button** no longer also spins; the phone gets a
  four-word hint ("drag the wheel to turn") where the desktop hint was simply
  hidden.

## Rebuild is a no-op — proof

```
python skyline/build_app.py          → skyline/skyline-app.html (227 kB)
cp  skyline/skyline-app.html site/skyline-app.html
cmp skyline/skyline-app.html site/skyline-app.html   → identical
```

And the download rebuilds the shipped page: `skyline-code.zip` unpacked to a
temp dir, `build_app.py` run there, `filecmp` against `site/skyline-app.html`
→ **True**. The zip (94 KB, 10 entries) is what `rezip_downloads.py` now
produces from `skyline/`.

Tests: `skyline/test_app.js` **41/41** (was 30; eleven new checks cover the
voicing, the motion contract and the provenance rows); `tests/test_layout.js`
33/33; `tests/test_markup.py` 0 hits; `verify.js` 0 console messages on
desktop dark, desktop light, reduced-motion and phone.

## Left undone, and two incidents

- `rprof` (60 KB) is derivable from `ring` in a dozen lines and is still
  shipped. Not worth the risk to the harness's "no bearing is empty" check
  today.
- The phone sidebar is still a 371 px scroll box with no affordance; the
  brief did not list it and it needs a layout decision (a collapsible panel
  or a taller cap), not a line.
- The hijaz/insen compromise above is stated, not solved; solving it means
  giving up the minor-third floor for those modes.
- `build_skylines.py` is edited but untestable until someone records a
  SPARQL query and pulls fresh data — which will be a new dataset.
- **Incident 1.** While this fix was in progress another session added a
  `bookshelf` target to `rezip_downloads.py`. My first patch failed against
  the changed file, and running `rezip_downloads.py --verify` with *their*
  version rewrote `heat-code.zip` from `heat/`, pulling in `__pycache__/` and
  `outputs/` (11 → 22 entries). **Restored** byte-for-byte from
  `backups/published-live-2026-09-04/downloads/heat-code.zip` (11 entries).
  `storage-code.zip` and `bookshelf-code.zip` were also rewritten by that
  run; their namelists were unchanged and their contents came from the
  current folders, which is what the script is for, but they are not files
  this brief covers and whoever owns them should know. `rezip_downloads.py`
  now skips `__pycache__`; it does not skip `outputs/`, which is heat's call.
- **Incident 2.** Commit `c2d02aa` (the climate-cost fix, another session)
  swept in this work mid-way: `skyline/` including the built
  `skyline/skyline-app.html` and `package*.json`, `site/skyline.html`, and
  the audit. Those three artifacts are now tracked; I have added them to
  `.gitignore`, which takes effect once the sweep does
  `git rm --cached skyline/skyline-app.html skyline/package.json
  skyline/package-lock.json`. The working tree, not that commit, is the
  finished state.
