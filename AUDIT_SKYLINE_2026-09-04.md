# Audit — Skylines, played (`site/skyline-app.html`)

Date 2026-09-04. Read-only; nothing under `site/` was changed. Brief:
`prompts/AUDIT_skyline.md`. Evidence in `_audit-skyline/` (gitignored; added to
`.gitignore` by this audit): `drive.js` (Playwright driver), `results.json`
(every number below), `shots/` (14 screenshots), `src/` (the unpacked download
zip), `embedded_skylines.json` (the data pulled back out of the shipped page).

Served with `python -m http.server 8802` from `site/`, Playwright 1.62.1,
Chromium 151 headless, 1440×900 and 390×844 (touch, DPR 3), dark and light,
reduced-motion on and off, throttled at 1.6 Mbps / 150 ms / 4× CPU.

**Disclosure the house rules ask for.** I read the brief with `cat`, which
printed the sealed appendix in the first tool call. I did not re-open it, but
its six items were in my context before I started. Where a finding below
matches one of them I have said so in §7 rather than pretend independence.
`DESLOP_AUDIT_2026-09-04.md` and `DESIGN_AUDIT_EXTERNAL_2026-08-30.md` were
not opened until §7.

---

## 0. Finding zero, corrected: the generator is not missing. Its input is.

The brief's premise was that `24 Skyline Sonifier/` is gone and the two HTML
files are the only artifacts. The folder is gone — searched the whole
`50 - ENERGY MODEL` workspace to depth 9, `01 ARCHIVE/` included; the only
hits are `HANDOFF.md`, its backup, and the prompts. But the brief also said to
look in `site/downloads/`, and that is where the generator is:

`site/downloads/skyline-code.zip` (394 KB, gitignored like every download)
holds `build_skylines.py`, `supplement.py`, `keys.py`, `build_app.py`,
`template.html`, `app.js`, `test_app.js` and `data/skylines.json`. It is not
a snapshot from some earlier version:

| in the zip | vs the shipped page |
|---|---|
| `data/skylines.json` | byte-identical to the JSON embedded in line 163 of the page |
| `app.js` | identical to the page's `<script>` (only the closing tag differs) |
| `template.html` | **3 lines behind**: the 2026-09-04 palette edit (`--acc-fill` tokens, `#spin.on`) was made in `site/` and never in the template |

So the page can be regenerated, verified and corrected from the zip — with
one exception that decides everything downstream:

**`data/raw/wikidata_buildings.json` is not in the zip and not anywhere in
the workspace.** `build_skylines.py` line 58 reads it; it is the raw Wikidata
pull that every one of the 24 non-supplemented cities is built from. The
SPARQL query that produced it is not recorded either — not in the zip, not in
`HANDOFF.md`, not in any `.py` or `.md` in the workspace. The docstring
describes the query's *filters* (class checks, unit normalisation, 55 m
floor, 830 m ceiling, 35 km radius) but not the query.

What this costs, concretely:

- **Cannot regenerate.** `python build_skylines.py --apply` fails on line 58.
  Any correction to a building height, a viewpoint, a city's inclusion, the
  ring cap, or a key that needs the data rebuilt is impossible without a
  fresh Wikidata pull, and a fresh pull will not reproduce the shipped
  numbers (Wikidata has moved on since 2 August; the docstring itself
  records that the *first* pull included a suspension bridge and a nuclear
  test).
- **Cannot verify the 24 Wikidata cities.** The page links each tower to its
  Wikidata entity, so a reader can check any one building. Nobody can check
  the *set* — that the 205 New York towers at or above 80 m are what the
  query returned, that nothing was dropped or duplicated.
- **Can verify and regenerate the three supplemented cities**, because
  `supplement.py` carries their rows inline. Austin, Nashville and Fort
  Worth are the only cities with a complete provenance chain on disk.
- **Can change the app and the palette** freely: `template.html` + `app.js`
  + the existing `skylines.json` rebuild the page via `build_app.py` with no
  raw data needed. Every fix in this report except the data-level ones is
  reachable.

Two smaller drift facts. The zip is behind the page (the palette lines), so
"Download code and data" currently hands out code that does not reproduce
what the reader is looking at; `rezip_downloads.py` only knows about `heat/`
and `storage/`. And `HANDOFF.md` §2 still names the folder — the house rules'
"seventh instance" of a stale premise, except the rules already list it.

**Recommendation** (not done, per the brief): unpack the zip to a tracked
`skyline/` folder beside `heat/` and `storage/`, add it to
`rezip_downloads.py`, port the three palette lines into `template.html`, and
write the SPARQL query into `build_skylines.py`'s docstring from memory or
by reconstruction — labelled as reconstructed. The raw JSON itself is gone.

---

## 1. Does it work

**Yes, cleanly.** All 27 cities load, key, draw and sound; zero console
messages across the whole run on both viewports; one network request (the
page itself); every control does what its label says.

| control | verified by | result |
|---|---|---|
| City select ×27 | instrumentation | pitches rebuilt, panel rebuilt, oscillator count stays 28 |
| Field of view 40–160 | instrumentation | `S.fov` follows, bearing readout updates |
| Volume 0–100 | instrumentation | master gain eases to 0.003 at 0, 0.44 at 55 |
| Play / Stop | instrumentation | gain to target in ~130 ms; Stop suspends the context |
| Spin | instrumentation | 22.4°/s; Space toggles it; drag cancels it |
| Drag (mouse) | instrumentation | 30% of canvas width = 12° at 40° FOV (correct: it scales with FOV) |
| Drag (touch, 390 px) | CDP touch events | 40° turn; page did not scroll (`touch-action:none` works) |
| Arrow / Shift+Arrow | instrumentation | 3° / 15° |
| Scroll wheel | code | 4° per notch, `preventDefault` |
| Hover tooltip | instrumentation | name, height, distance, year |
| Tab order | instrumentation | city → fov → vol → Play → Spin → tower links |

**The "turn on the spot" interaction, measured.** With `setTargetAtTime`
instrumented across four bearings (0/90/180/270°), every call in a 900 ms
window was on a *gain* param: 1,566–1,595 calls, zero on any oscillator
frequency, zero panner or stereo-panner nodes ever created (the graph is 28
oscillators → 28 gains → master → highshelf → lowpass → compressor → ceiling
gain → destination; nothing else). Rotation changes **which of the city's
7–10 fixed pitches are loud and by how much**; it changes nothing spatial.
The output is mono. The page never claims stereo, but "the sound turns with
you" (`prompts/AUDIT_skyline.md`'s gloss, and the site's framing) would be
read by most people as something spatial. It is a mixer, not a head.

Per bearing the sounding set is 7 voices plus the drone (8 active gains,
matching the on-screen "seven voices at a time"). Frequency automation
happens only on city change.

**Autoplay-blocked first load.** I could not reproduce a blocked context by
instrumentation: headless Chromium reports `running` before any gesture even
with Playwright's default `--autoplay-policy=no-user-gesture-required`
removed and the strict policy passed. So this is by code reading. The
context is *created inside the click handler* (`buildAudio()` is only called
from Play), so on every desktop browser the gesture that makes it also
unblocks it. The handler then calls `resume()` if suspended but does not
await it, sets `S.playing = true`, and writes "Stop" on the button
regardless. The two real-world cases where that produces a silent page
saying "Stop" with a moving meter and no message: iOS with the hardware
mute switch on (Web Audio is silenced; the API reports `running`), and a
context whose `resume()` never resolves (Linux with no sink, some kiosk
policies). `#noaudio` only appears when the `AudioContext` *constructor* is
missing, which no shipping browser lacks. There is no "not hearing
anything?" affordance. **Cost:** on a muted iPhone — the single most common
way this page will be opened from a link — it looks broken and says
nothing.

**No output device.** Unverifiable here (headless has a fake sink). By code:
no handling; same silent-"Stop" outcome as above.

**Leaks.** None. The graph is built once (28 oscillators, 30 gains, 2
biquads, 1 compressor, counted from boot through 27 city changes and a
hide/show cycle — the count never moved). Hiding the tab suspends the
context and flips the button to Play. `pagehide` closes the context when
the page is really leaving; navigating away logged `closes: 1` and the
context state `suspended` at close. Idle cost with the page open and not
playing: 46 ms of task time per 3 s (about 1.5% of a core). The rAF loop
is scheduled every frame (181 per 3 s) but skips draw and audio when
nothing moved.

**Stopping the sound.** The Play button becomes Stop, in the same place; it
is the fourth Tab stop; Space does *not* stop it (Space is Spin). Hiding the
tab stops it. That is findable. The volume slider is a second route.

---

## 2. Is it honest — the main event

The page's claim is that measured, assumed and invented are each labelled.
Tested as a claim, against the app and against `site/skyline.html` which
carries the labels. Ranked by how much it matters.

### 2.1 `skyline.html` labels a rendering that no longer exists — HIGH

The "What is measured and what is invented" section is the labelling. Its
**Measured** paragraph says: "The listener stands at a stated point, and
each tower's bearing and apparent height follow from those two numbers by
trigonometry. Where a tower stands behind a taller one it contributes
nothing, which is what an eye does." Its table says "Empty horizon →
Silence — which is why turning away from the towers quiets the instrument."

That is the *panorama* rendering, retired before this page shipped
(`HANDOFF.md` §2: "the old realistic mode and its control are gone"). The
app reads none of the panorama data: `prof`, `draw`, `towers`, `view`,
`dist`, `centre`, `mass` are referenced **zero** times in `app.js`. What
plays is `rprof`, built from the *equalised ring*: buildings at invented
evenly-spaced slots, distance from a height-weighted centroid clamped to a
400 m minimum, no occlusion (every ring entry writes its own slot). The
generator's own test asserts the opposite of the page: "no bearing in any
city is empty" (`test_app.js`, and `min(rprof)` over all 27 cities is
0.116°, never zero). Turning away from the towers **cannot** quiet this
instrument; the wheel was built so it never does.

The page does say, under **Rearranged**, that spacing is equalised. It then
contradicts that two paragraphs earlier and one table later. A reader who
takes the Measured paragraph at its word believes the meter is a true
horizon. It is a carousel.

**Fix cost:** low — rewrite three paragraphs and one table row on
`skyline.html`; the app's own sidebar ("On the wheel", "Standing: in the
middle of it") is already truthful about the ring. Does not need the source.

### 2.2 The key is labelled, sourced, tiered — and mostly inaudible — HIGH

The key is the app's headline editorial content: 27 cities, 19 distinct
keys, 8 modes, each with a "from" sentence and a PIECE/ANTHEM/MODE tier. It
is the best-documented choice in the app. Then `setKey()` keeps only scale
degrees 1, 3, 5 and 6 of the mode and drops anything closer than a minor
third to its lower neighbour. Recomputed exactly (`_audit-skyline/`, and
confirmed against the live `pitches()` per city):

| mode | steps | what actually sounds (semitones from root) |
|---|---|---|
| major | 0 2 4 5 7 9 11 | 0 4 7 — a major triad; the sixth is filtered out |
| hijaz | 0 1 4 5 7 8 10 | 0 4 7 — **a major triad**; the b2 is never selected, the b6 is filtered |
| minor | 0 2 3 5 7 8 10 | 0 3 7 — a minor triad |
| pent major | 0 2 4 7 9 | 0 4 9 |
| yo | 0 2 5 7 9 | 0 5 9 |
| blues | 0 3 5 6 7 10 | 0 5 10 |
| pent minor | 0 3 5 7 10 | 0 5 10 |
| insen | 0 1 5 7 10 | 0 5 10 |

Eight modes become five sounds. Hijaz — "the mode most characteristic of
Gulf music", "the Jewish liturgical mode", "the Phrygian dominant of
flamenco" — is a plain major triad in every one of its four cities. Insen,
"the darker of the two Japanese pentatonics", is identical to pent minor and
to blues. The cities that are acoustically indistinguishable from each
other while labelled differently:

- Dubai (D hijaz), Tel Aviv (D hijaz), Vienna (D major): same ten pitches.
- Chicago (E blues), Austin (E blues), Hong Kong (E pent minor): same eight.
- Madrid (E hijaz), Auckland (E major): same ten.

This is not a bug in the code; it is the deliberate consequence of the
consonance rule, which the app explains well. But the labelling now
overstates what was chosen: the page tells the reader Dubai is in Hijaz for
a documented reason, and the instrument plays D major. The "from" sentences
are true of the key *name* and false of the sound. Under the site's own
rule — the interface has to say what the output was computed from, where
the person is looking — the sidebar needs one sentence: which degrees of
the mode survive, and that the mode's colour tones do not.

Also: the in-app note says "first, third, fifth and sixth of the mode". For
the three pentatonic modes there is no sixth degree, so three notes sound;
for hijaz the "third" is the major third and the "sixth" is filtered; for
blues the "third" is the fourth. The sentence is correct as an index into
an array and misleading as music.

And: "no bearing in any city can produce a dissonance". What the filter
guarantees is no interval under a minor third *between adjacent sounding
pitches*. Blues/pent-minor/insen cities sound root, fourth and minor
seventh together; a minor seventh is a dissonance in any textbook. "Nothing
closer than a minor third" is the true claim and would be a fine one.

**Fix cost:** low for the wording; medium if the author wants the modes to
be audible (change the degree selection per mode), which does not need the
source data either — it is all in `app.js`.

### 2.3 The height → frequency mapping is stated in two places, and they disagree — MEDIUM

`skyline.html` "How the bars become sound": "Position across the view →
Pitch, four octaves of the city's scale" and "Four octaves of a five-note
scale is twenty pitches". The app: chord tones over three octaves, capped
at 1,500 Hz, 7–10 pitches per city (7 for New York, 10 for most). The app's
sidebar says "over two and a half octaves, seven voices". So the content
page describes an earlier mapping and the app describes the current one;
neither is where the *full* mapping lives. What a reader cannot find
anywhere on either page:

- loudness is `(bar / city peak)^1.6` — **normalised per city**, so the
  tallest tower in Fort Worth (173 m) is exactly as loud as One WTC;
- then a 1/√(0.5·j+1) spectral tilt by pitch index, then a 7-voice cap,
  then constant-power normalisation to 0.46, then master = 0.8 × volume;
- timbre: every fourth oscillator is a triangle wave, the rest sine
  (`k % 4 === 0`), unstated anywhere;
- the drone: the root an octave below, always on;
- the filter chain (−9 dB shelf above 1.8 kHz, lowpass at 3.2 kHz, 20:1
  limiter, 0.62 ceiling).

Each is a choice, and each is documented — in comments in `app.js`, which
is in the download. The page's promise is "it is written out in full
below". It is not; it is written out in full in the source. **Fix cost:**
low — one table on `skyline.html`, or a "how it sounds" paragraph in the
sidebar. No source needed.

### 2.4 The supplemented cities: labelled, but the label does not say what was done — MEDIUM

What the app tells the reader for Austin / Nashville / Fort Worth: "On the
wheel — 66 of them, 65 hand-entered" (Austin), "27 of them, 27
hand-entered" (Fort Worth). The tower list has no links for those rows
(Wikidata rows link; hand rows are plain text, by design). That is the
whole disclosure.

What was actually done (`supplement.py`, `build_skylines.assign()`):

1. Rows transcribed from each city's Wikipedia "List of tallest buildings"
   article, retrieved 2026; heights are the article's metres column;
   coordinates are the article's, block-level.
2. Above a per-city floor (91.4 m Austin and Nashville, 61 m Fort Worth)
   the list *overrules* Wikidata: any Wikidata building at that height not
   on the list is dropped as presumed unbuilt/demolished/misrecorded (the
   docstring names the 228.6 m never-built Paramount Tower).
3. Below the floor, Wikidata rows within 150 m and 15 m of a list row are
   dropped as duplicates; others are kept.
4. Landmarks below the 80 m headline floor were added because they clear
   the 55 m ring floor (Tennessee State Capitol, 63 m; Tarrant County
   Courthouse, 59 m).

The reader is told "hand-entered". They are not told the source is
Wikipedia, that it *overrode* the database above a stated height, or that
for Fort Worth zero Wikidata rows survive (27 of 27 hand). `supplement.py`'s
own docstring says `Any city listed here is marked "supplemented" in the
app` — the word does not appear in the app — and refers to "the 55 m floor
the wheel states on screen" — the app never states 55 m; it says "at or
above 80 m" for the count and nothing for the ring. Two on-screen
statements the generator believes it makes and does not.

Honest as far as it goes; incomplete where it matters. **Fix cost:** low
— a sentence in the sidebar for `c.hand > 0` and the ring floor in the
"On the wheel" row. The supplement rows themselves are fully recoverable.

### 2.5 Where heights come from: general, not per city — LOW–MEDIUM

`skyline.html`: "Each building carries a published structural height and a
published coordinate." In the app: nothing about source at all except the
per-tower Wikidata link. So provenance is per-*building* (good) for 24
cities and per-*nothing* for 3. No city says "Wikidata, retrieved 2 August
2026". No ring entry says "Wikipedia list, retrieved 2026". The tooltip's
"2.2 km from the centre" is haversine from the height-weighted centroid,
clamped to 0.4 km — 106 ring entries across 16 cities sit at exactly the
clamp (18 of Austin's 66, 14 of Calgary's 18, 18 of Fort Worth's 27), and
the tooltip presents 0.4 km as a measurement. Small, but it is exactly
"chosen presented as measured".

### 2.6 What is presented as measured that is chosen — summary

| presented as | actually | where |
|---|---|---|
| "apparent height … by trigonometry", occlusion, silence off-axis | equalised slots, 400 m clamp, no occlusion, never silent | `skyline.html` Measured |
| "x km from the centre" | clamped at 0.4 km for 106 towers | tooltip |
| "D hijaz, from maqam Hijaz…" | D major triad | sidebar, all four hijaz cities |
| "four octaves of the city's scale" | 2.5 octaves of a triad-plus-one | `skyline.html` table |
| "hand-entered" | Wikipedia list overriding Wikidata above a floor | sidebar |
| "Towers: 14 at or above 80 m / On the wheel: 27" | second number uses an unstated 55 m floor | sidebar |

What is **correctly** labelled: the ring's equalised spacing (Rearranged
paragraph and generator comments agree); the footprint-width assumption
(0.18 h, 25–70 m — though the app no longer uses it, since the ring does
not draw widths from it); the key as an editorial choice with tier and
source; the per-city 80 m count; the hand-entered count. The app's sidebar
is more truthful than the content page that introduces it.

---

## 3. Measure it

### 3.1 Weight

341,568 bytes, one request, no CDN, no fonts. Composition:

| part | bytes | share |
|---|---|---|
| data line (`const D = JSON.parse(...)`) | 302,725 | 88.6% |
| app JS | ~31,000 | 9.1% |
| CSS + markup | ~7,700 | 2.3% |

Inside the data, by field across 27 cities: `ring` 81 KB, `draw` 63 KB,
`rprof` 60 KB, `prof` 40 KB, `towers` 32 KB, `key` 4.5 KB, the rest under
1 KB each. **`draw`, `prof`, `towers`, `view`, `centre`, `dist`, `mass`,
`country` are never read by the app** — 136 KB, 45% of the data, 40% of
the page, is the retired panorama's payload still shipped. `rprof` (60 KB)
is derivable from `ring` in a dozen lines and is the same 360 floats per
city. A page that shipped only what it draws would be ~145 KB. Fixable
from the zip: `build_skylines.py` writes those fields; deleting them from
the output dict and re-running `build_app.py` on the *existing*
`skylines.json` (filtered in `build_app.py`) needs no raw data.

### 3.2 Cold load and first sound

Throttled (1.6 Mbps down, 150 ms RTT, 4× CPU, cache off):

| | desktop | phone |
|---|---|---|
| first contentful paint | 396 ms | 372 ms |
| response end (last byte) | 1,889 ms | 1,895 ms |
| load | 2,225 ms | 2,248 ms |
| panel populated after load | 0 ms | 1 ms |
| Play click → context running | < 1 ms | < 1 ms |
| Play click → master gain > 0.30 (of 0.44) | ~130 ms | ~130 ms |

The sidebar and an empty stage paint at 0.4 s because the CSS and markup
precede the 300 KB data line; the wheel appears at ~1.9 s when the data
arrives. Nothing to fix here beyond §3.1. Unthrottled: DCL 66 ms, load 104 ms.

### 3.3 Type and contrast

Rendered sizes in the sidebar and stage chrome: 10.5, 11, 11.5, 12, 12.5,
13, 13.5, 14, 20 px. **54 text elements under 12 px** on desktop (same
count as the deslop audit found), in six selectors:

| selector | px | what | dark ratio | light ratio |
|---|---|---|---|---|
| `h2` | 10.5 | section headings "THE KEY", "THIS SKYLINE", "ON THE WHEEL" | 6.21 | 5.02 |
| `.tier` | 10.5 | PIECE / ANTHEM / MODE pill | 5.84 | 5.07 |
| `label.f` | 11 | CITY, FIELD OF VIEW, VOLUME | 6.21 | 5.02 |
| `dt` | 11.5 | stat labels | 6.21 | 5.02 |
| `ol.tow span` | 11.5 | "541 m · 2014 · SW of centre" ×40 | 6.21 | 5.02 |
| `#hint` | 11.5 | the only instructions | 6.19* | 4.83* |
| `#az` | 12 | bearing readout | 6.19* | 4.83* |

\* over the footer wash on the stage gradient's bottom stop, computed by
hand; the meter's bars can rise behind this text, where the ratio is not
predictable.

Canvas text: compass points at 11 px, tower names at 11 px (10 px under
560 px canvas width, i.e. every phone). Tower names in `--dim` on the
gradient at ~58% height: 6.2 dark, 4.74 light — passes, small. Compass
points fade to alpha 0.35 at the sides: **1.78:1** at the fade. They are
decorative at that point, but "NW" at 1.78 is not readable.

Contrast failures:

- **Play button, dark scheme: `#f2f0ff` on `#8b7ff2` = 2.91:1** at 14 px
  600 (not "large" under WCAG, which needs 18.7 px bold). This is the exact
  failure the 2026-09-04 palette correction fixed site-wide. The correction
  reached this file — `--acc-fill` tokens were added and `#spin.on` was
  switched to them — but `.btns button` (the Play button, the one that
  matters) still uses `--acc`. Light scheme passes at 7.82. Once playing,
  the button goes transparent-with-ink and passes; so the failing state is
  precisely the one a new reader sees.
- Spin button off-state border `--rule` on `--panel`: 1.34:1 (needs 3:1
  for a UI boundary). Select border on card: 1.28 dark, 1.44 light. Both
  are the site's hairline convention; flagged, not pressed.
- Meter bars and near-face towers pass (5.4–6.8 dark, 4.4–5.9 light).
  Back-half towers at alpha 0.22: 1.42 — intentionally "behind you", fine.

### 3.4 Mobile, 390×844 with touch

Works: tap Play → running in one gesture; touch-drag turns 40° without
scrolling the page; tap Spin spins; layout does not overflow horizontally.

Costs:

- The sidebar is capped at 44 vh = **371 px, with 2,461 px of content in
  it.** Play and Spin are visible without scrolling (bottom edge at 322 px)
  — good — but "The key", the consonance note, every stat, and the tower
  list live inside a 371 px scroll box with no visible affordance that it
  scrolls. In the phone screenshot the panel ends at the heading "THE KEY"
  with nothing under it.
- `#hint` is `display:none` under 760 px, by an explicit and reasonable
  comment (it mentions arrow keys and Space). Nothing replaces it. A phone
  reader is never told to drag. The wheel does not look draggable; the
  canvas cursor hint is mouse-only.
- Tower labels drop to 10 px and three at most; the compass ring at 11 px.
- 390 px wide, 473 px of stage: the wheel is drawn at Rx ≈ 135 px; the
  drum reads. The meter is 96 bars at 3.5 px each; it reads as texture.

Can a phone reader do what the page promises? Play, yes. Turn, only if
they guess. Read which tower is which, no — 3 labels and a scroll box.

### 3.5 Motion contract

**`data-motion` does not reach this app at all.** The attribute is never
set (`dataset.motion` is `null`); there is no motion script in the head
(`motion.js` is not loaded — apps carry no shared scripts); the CSS never
references it. Under `prefers-reduced-motion: reduce`, Spin still turns at
22.4°/s, the meter still animates, the peak markers still fall. I also set
`data-motion="off"` on `<html>` by hand mid-session: no effect. The
content page `skyline.html` honours the contract (its video is gated by
`bgloop.js`) and then opens this app in a new tab where the contract does
not exist.

What the app currently assumes: that a reader who asked for reduced motion
still wants a spinning drum and a dancing meter, and — the brief's point —
that motion and audio are one preference. They are not. The meter *is* the
audio, drawn; someone who wants no motion may want the sound, and someone
who wants no sound (a vestibular reader is not usually a sound-averse one)
can already use Stop. A reasonable contract here: reduced motion → no idle
peak-fall animation, no Spin auto-rotation (drag and arrows still work),
bars snap rather than ease; audio untouched. **Fix cost:** low, in
`template.html` and `app.js`; no source needed.

### 3.6 Accessibility beyond contrast

This is the one app whose primary output is not visual, and it has **no
path for a reader who cannot hear.** What such a reader gets: the meter,
which is the sound drawn — genuinely the same information, bar for bar —
and the sidebar's text about the key. What they do not get: any statement
of *which pitches are sounding now*. The app knows (`pitches()`, the 7 kept
voices per frame); it draws bars by bearing, not by pitch, and never
writes a note name anywhere. One line under the meter — "sounding: D2 A2
D3 F#3 A3 D4 F#4" updating with the bearing — would make the instrument
legible to a deaf reader and, incidentally, make §2.2 visible to everyone.

For a reader who cannot see: zero ARIA attributes on the page; the canvas
has no role, no label, no fallback text; the sidebar is real text with
real headings (h1, three h2s) and a real `<ol>` of towers with links, so a
screen reader gets the city, the key and its reason, the stats, and the
tower list with "behind you" markers — that is a decent textual model of
the wheel. The bearing readout (`#az`) is not a live region, so turning
with the arrow keys (which works from anywhere but a form field) announces
nothing. A `role="img"` with a label on the canvas, `aria-live="polite"`
on `#az`, and the sounding-pitch line above would give a blind reader the
same instrument a sighted one has — and the sound itself is fully
available to them already. That is unusual and worth saying: for the blind
reader this is the *most* accessible page on the site.

No keyboard trap; Tab order is sane; Space is captured for Spin outside
form fields, which means Space on a focused Play button *both* clicks Play
(native) and toggles Spin (the window listener runs too, since the button
is neither SELECT nor INPUT). Verified by reading the handler; a keyboard
user pressing Space on Play starts the sound and the spin together.

---

## 4. What is good and must survive

- **The graph is built once and left running.** 28 oscillators, gains
  moved, nothing rebuilt on city change, context suspended on hide and
  closed on leave, a dead context detected and rebuilt. This is the correct
  Web Audio architecture and it is rare to see it done right.
- **The harshness engineering.** Voice cap, spectral tilt before
  normalisation, constant power, minor-third floor, shelf + lowpass +
  limiter + ceiling — and a test file that measures each of those claims
  rather than asserting them. `test_app.js` also catches the "drew 432
  invisible rectangles" class of bug. Keep every line.
- **The sidebar's honesty about the ring.** "On the wheel: 120 of them",
  "Standing: in the middle of it", the "behind you" markers, the per-tower
  Wikidata links, the count of hand-entered rows. This is the labelling the
  page promises, and it is in the app, not just the prose.
- **The keys as sourced editorial choices with tiers.** The idea is right
  and the sourcing is real. Only the audibility (§2.2) is wrong.
- **The prose in the code.** Every design reversal is recorded in place
  with its reason — the pitch-from-median-height mistake, the Paramount
  Tower, the 120 m floor, the swapped sin/cos rim. The download is worth
  reading on its own.
- **`touch-action: none` and pointer capture.** Phone dragging works first
  time.
- **Single request, no dependencies, 2.2 s on a throttled phone.**

---

## 5. What cannot be fixed without the missing source

The zip recovers the generator; what is gone is `data/raw/
wikidata_buildings.json` and the query behind it. So the line falls here:

**Cannot be done at all** (needs the raw pull that no longer exists):

- Reproduce the shipped 24 Wikidata cities from a stated query. Any
  regeneration is a *new* dataset, and the page would have to say so.
- Verify that the per-city building sets are what the query returned
  (nothing dropped by the class filter that should not have been, nothing
  kept that a human would reject beyond what the docstring records).
- Correct a single Wikidata-sourced height or coordinate by re-running
  the pipeline. (It *can* be patched in `skylines.json` by hand, which is
  then a second undocumented supplement.)
- Add a city, or restore one that fell under the 7-tower / 16-building
  floor.

**Can be done from the zip alone** (everything in §§1–3 except the above):

- Every wording fix on `skyline.html` and in the sidebar (§2.1–2.5).
- Making the modes audible, or stating which degrees sound (§2.2).
- Dropping the 136 KB of unread panorama fields (§3.1) — filter in
  `build_app.py`, no regeneration.
- The Play button's `--acc-fill` (§3.3), the sub-12 px sizes, the motion
  contract (§3.5), ARIA and a sounding-pitch readout (§3.6), a phone hint
  and a scroll affordance (§3.4), a "not hearing anything?" line (§1).
- The three supplemented cities in full: their rows are in `supplement.py`.

**Should be done first, because it decides the rest:** move the zip's
contents into a tracked folder and wire `rezip_downloads.py` to it, so the
next edit does not happen inside an archive; and write the SPARQL query
down, labelled as reconstructed from the docstring, so the *next* pull is
at least a stated one.

---

## 6. Findings, ranked

| # | finding | observation | cost to the reader | severity | fix cost |
|---|---|---|---|---|---|
| 0 | Raw Wikidata input and its query are not in the workspace or the zip | §0 | 24 of 27 cities cannot be regenerated or set-verified | **HIGH** | cannot — recoverable only as a new, labelled dataset |
| 1 | `skyline.html` "Measured" section describes the retired panorama; "empty horizon → silence" is built to be impossible | §2.1 | reader believes the meter is a true, occluded horizon | **HIGH** | low, prose |
| 2 | Keys are sourced and tiered but the instrument reduces 8 modes to 5 sounds; hijaz = major triad; Dubai ≡ Vienna, Chicago ≡ Hong Kong, Madrid ≡ Auckland | §2.2 | the page's central editorial claim is inaudible | **HIGH** | low (say so) / medium (make modes audible) |
| 3 | Play button 2.91:1 in dark scheme; the 2026-09-04 fix reached `#spin.on` but not `.btns button` | §3.3 | the first thing to click fails AA in the default scheme | HIGH | trivial, one CSS line (also in `template.html`) |
| 4 | Motion contract absent from the app; reduced-motion ignored; motion and audio conflated | §3.5 | vestibular readers get a spinning drum | MEDIUM–HIGH | low |
| 5 | No path for a reader who cannot hear; no note names anywhere; canvas has no role or label; `#az` not live | §3.6 | the non-visual output has no text form | MEDIUM–HIGH | low |
| 6 | 40% of the page (136 KB) is panorama data the app never reads | §3.1 | 2× the bytes on every load | MEDIUM | low, in `build_app.py` |
| 7 | Mapping stated in two places that disagree; per-city normalisation, tilt, timbre, drone, filter chain unstated on either page | §2.3 | "written out in full below" is not | MEDIUM | low |
| 8 | Supplement disclosure is "hand-entered" only; source, override-above-floor, and the 55 m ring floor are unstated; generator docstring believes two on-screen statements exist that do not | §2.4 | reader cannot tell Fort Worth is 100% Wikipedia | MEDIUM | low |
| 9 | Silent-but-"Stop" on muted iOS / no sink; `#noaudio` only fires on a missing constructor | §1 | looks broken with no message on the commonest phone path | MEDIUM | low |
| 10 | Phone: sidebar is a 371 px box holding 2,461 px, no scroll affordance; no instruction to drag; 3 labels at 10 px | §3.4 | phone reader can Play but not learn to turn or read the towers | MEDIUM | low–medium |
| 11 | 54 elements under 12 px in six selectors; compass points at 1.78:1 in the fade | §3.3 | strain; the instructions are 11.5 px | LOW–MEDIUM | low |
| 12 | Download zip's `template.html` is three lines behind the shipped page; `rezip_downloads.py` does not know this project | §0 | the code a reader downloads does not build the page they see | LOW–MEDIUM | low |
| 13 | Tooltip presents the 0.4 km clamp as a measured distance (106 towers, 16 cities) | §2.5 | chosen presented as measured, small | LOW | trivial |
| 14 | "No dissonance" claim; a minor seventh sounds in three modes; the true guarantee is "nothing under a minor third" | §2.2 | overclaim | LOW | trivial |
| 15 | Space on a focused Play button both plays and spins | §3.6 | surprise | LOW | trivial |
| 16 | Hairline borders at 1.3–1.4:1 on Spin and the select | §3.3 | site convention; UI boundary AA is 3:1 | LOW | site-level decision |

---

## 7. Cross-check

Read after §§1–6 were drafted, in the order the brief gives.

**`DESLOP_AUDIT_2026-09-04.md`.** Caught that I also caught: the app
button failure (it reports 3.27:1 "white on the same violet"; my computed
value for the actual pair `#f2f0ff` on `#8b7ff2` is 2.91 — its number may
be for `#fff`; either fails), 54 sub-12 px elements (exact match), the
shared tokens across atlas/skyline/climate-cost apps (its F11). It measured
the *content page* (weight 404 KB, idle CPU 318 ms per 3 s, the poster PNG)
which this audit did not cover and which is real. It did not open the app
beyond type and contrast — nothing on audio, honesty, motion, data weight,
mobile or provenance, which is fair: it was a site pass.

**`DESIGN_AUDIT_EXTERNAL_2026-08-30.md`.** Zero mentions of skyline in
either form. Its one transferable observation — "set up the interactive
instead of asking it to carry all the teaching" (line 250) — is the
inverse of §2.1 here: `skyline.html` does the teaching, and teaches the
wrong instrument.

**`DESLOP_3A` / `DESLOP_WEIGHT`.** The 27-city key list in the margin of
`skyline.html` is verified here against the data: all 27 match (the
abbreviations "pent maj." / "pent min." expand correctly). Weight doc's
poster/video notes stand and are outside this audit's file.

**The appendix checklist** (seen at the start, see the disclosure at the
top). Six items; all six are in the findings above (#0 as corrected, #2,
#9, #3, #5, #11). Two things it does not have that this audit found and
weighs higher than most of its list: the Measured paragraph describing a
retired rendering (#1) and the modes collapsing to five sounds (#2). One
thing it states more strongly than the evidence supports: "the generator
folder is missing from the workspace entirely" is true of the folder and
false of the generator — the download zip is a complete, current,
buildable copy minus its raw input, and the brief's own instruction to
search `site/downloads/` is what found it.

---

*Stopped here, as instructed. Nothing under `site/` was modified; the only
writes outside `_audit-skyline/` are this file and one line in `.gitignore`.*
