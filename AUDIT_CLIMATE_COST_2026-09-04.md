# Audit — the true climate cost calculator — 2026-09-04

Scope: `site/climate-cost-app.html` (277 KB) and, where it bears on the app,
`site/climate-cost.html`. Read-only; nothing in `site/` was changed. Source in
`climate-cost/`. Evidence in `_audit-climate-cost/` (gitignored; one line was
added to `.gitignore` for it).

**Disclosure on the seal.** The brief's appendix is sealed until §6. I did not
manage that: `cat prompts/AUDIT_climate-cost.md` printed the whole file,
appendix included, before I had read a line of source. I read it once at that
moment and did not return to it until §5. Every finding below was established
by running code, not by working back from the list, and the numbers speak for
themselves; but the reader should know the seal was broken by the first
command, not the last.

Working-tree note: the tree was clean when this audit started and was not
clean when it finished — another session (Phase 3b deslop, by its file) edited
`site/style.css`, `site/assets/motion.js` and the chrome of every content page,
including `site/climate-cost.html`, while this ran. Those edits touch the
motion snippet, the marginalia and the footer, not the prose, table, figure or
video this audit reports on; `site/climate-cost-app.html` was not touched.
This audit's only writes are this file, `_audit-climate-cost/`, and one
`.gitignore` line.

Environment note: the Claude-in-Chrome extension was not connected, so the
browser work was done with headless Chrome (installed build, SwiftShader WebGL)
driven over the DevTools protocol by `_audit-climate-cost/browser.js` and
`timing.js`. Screenshots are real renders of the shipped file.

---

## The two claims

### Claim 1 — "Change the route and it recomputes" — **TRUE, and proven**

The app computes. There is no lookup path.

- `scene.js` calls `model(item, origin, dest, mode, life)` on every control
  change (`render()`, line 930). Nothing reads a stored answer.
- **Sweep:** 356 combinations in the shipped page — every one of the 20 items ×
  4 freight modes × 4 routes (first/last region alphabetically, France→France,
  Norway→New Zealand, South Africa→Canada) plus lifetime extremes (0, −1, 1e-9,
  1e15, NaN, Infinity) — returned finite, positive totals with no console
  errors (`browser.txt`).
- **Independent computation:** `_audit-climate-cost/independent.py` is a
  fresh recursive evaluator written from `processes.py` alone, with no cutoff
  and no depth limit. On 12 routes, none of them defaults (tomato Morocco→France
  by road; tomato Ethiopia→New Zealand by air; beef Norway→South Africa by air;
  electric car Poland→Norway by rail at a 480,000 km life; cotton t-shirt
  India→Norway by air; long-haul flight at a 3×10⁸ pkm airframe life; …), the
  engine's `total + cut` matches mine to 2×10⁻¹⁶ on 11 routes and 1.9×10⁻⁵ on
  one (see finding 9 for why that one is not zero).
- Deep nesting was covered: the data's deepest chain is three processes
  (nitrate → ammonia → gas; glider → film → gas), and those routes exercise it.

**But a precomputed answer set is shipped anyway, and it is dead.** `lca.py
build_site()` embeds `data["runs"]` — all 20 items at their default route,
full trees — in the page. `D.runs` is never referenced by `engine.js` or
`scene.js`. It is 123.6 KB raw (17.5 KB gzipped), **44.9 % of the file**, and
it is the first thing anyone who views source will find, directly under a
comment saying the page does not precompute. The central sentence is right;
the payload contradicts it for no benefit. Finding 3.

### Claim 2 — "Allocation is exposed, not hidden" — **HALF TRUE, and the showcase is wrong**

The number is on every edge. The *method* is not, the reader cannot change it,
and the page's own worked demonstration of the allocation argument is a figure
the model does not produce.

**The 11.65 kg shoe does not exist in this model.** `climate-cost.html` says
the leather shoe is 3.66 kg at 2.2 % economic allocation and "would triple" at
7 % mass allocation; the video caption says "nearly tripled"; the poster frame
prints **11.65 kg CO2e**. Running the model with the hide edge at 0.07 instead
of 0.022 gives **4.40 kg, ×1.20** (`independent.txt`). 11.65 is exactly
3.66 × (7 ÷ 2.2): the whole shoe was scaled by the allocation ratio, as though
every gram of it were hide. In fact the hide stage is 0.34 kg of the 3.66; the
tannery, sole, freight, retail and landfill do not move with the cow. To reach
11.65 the hide allocation would have to be **53.8 %**. No script in the
repository generates `climate_allocation.mp4` or its poster, so the number
cannot be traced to a computation. Under HANDOFF §4 this is an invented
figure on a page whose thesis is that footprints hide their arithmetic. The
same wrong claim is baked into `processes.py` (leather note: "the shoe would
triple"). Finding 1.

The rest of the allocation picture, honestly:

- **Method stated per edge?** No. There is no method field. Of the eight
  co-product edges, four say the method in a free-text note (beef slaughter
  0.72 "economic split; mass would give 0.55"; cheese herd 0.85 "IDF standard
  economic split"; leather 0.022 "economic … by mass about 7 %"; cheesemaking
  0.90 "a tenth goes with the whey", method unstated). Chicken slaughter 0.78,
  coffee wet-mill 0.55, almond hulling 0.62 and rice milling 0.80 state no
  method at all. The app shows "Allocation 72.0 %" and the note; it never says
  *economic* or *mass* as a label.
- **Can the reader change it?** No. The only allocation-like control is the
  vehicle-lifetime slider. The 2.2 %/7 % choice the page builds its argument
  on is a constant in the data.
- **"Allocation" is three different things wearing one label.** The stage
  `allocation` field is (a) a co-product share (beef 0.72), (b) a lifetime
  amortisation (car manufacture 0.0005 = 100 km ÷ 200,000 km), and (c) for
  every clothing freight stage, **the shipment mass in kilograms** (t-shirt
  0.22, jeans 0.85, trainers **1.6**, leather shoes **1.2**). The app
  presents (c) as "ALLOCATION 160.0 %" in the selection panel and draws the
  allocation ring 1.6 turns around the ball (`desktop-dark-sneakers-freight.png`
  shows the seam where it overlaps itself). The legend says "a full ring means
  the whole process is charged to this product." Finding 2.
- **Every food freight node shows more than 100 % too.** Both engines fold the
  over-production factor into the freight node's `alloc` (`transport_node(alloc
  * scale)`); a tomato's container-ship ball reads **123.5 %** with a ring
  drawn 123 % of a circle, on the default view. Children of the same stage get
  the scale on `amount` instead, so only freight is mislabelled. Finding 2.
- **Emission-factor provenance is thinner than the page implies.** The
  module docstring names Poore & Nemecek 2018, IPCC AR6 ch. 7, the 2019
  Refinement, "ecoinvent process descriptions" and DEFRA/BEIS. Per process,
  only the four transport modes (DEFRA 2023), soil N₂O (IPCC 2019), aviation
  non-CO₂ (Lee et al. 2021) and the GWP values name a source. The other 38
  processes and every stage-level `direct` number carry a quality letter and a
  candid note but no citation. Grid intensities for 28 regions: "operating
  margin, roughly 2023-2024", no source. The content page's Sources list has
  five entries for a 62 KB database. Finding 5.
- **The biggest numbers carry no quality grade.** A/B/C grades exist on
  process nodes only. Stage-level directs — beef enteric 38.0, land use 16.0,
  manure 6.2, cheese enteric 8.4, the leather hide 8.4, rice paddy 1.85,
  chicken feed 2.1 — are the largest single terms in the model and show no
  pill. Finding 5.
- **Vehicle lifetimes: exposed, yes; consistent, not quite.** The slider is
  real, log-scaled between stated bounds, labelled "as published" at the
  default, and the URL carries it. But the defaults were back-derived from the
  allocation constants (default = 100/alloc for every vehicle), and for the bus
  the constant contradicts its own note: "800,000 km and twelve seats filled"
  is 9.6 M passenger-km; the shipped allocation 6.3×10⁻⁶ implies 15.87 M, a
  factor of 1.65. Finding 6.
- **Cut-off: the numerical one is stated, the boundary is not.** The 0.15 %
  proportional cutoff is reported ("0.044 kg dropped below the 0.15 % cutoff")
  — but only when it is non-zero, and it under-counts (finding 9). What the
  model never includes — farm and factory capital goods, water, refrigerant
  beyond an "allowance", particulates, vehicle end-of-life, the roasting
  yield, business-class seats — is scattered across notes and never stated as
  a system boundary anywhere the total is shown. Finding 7.
- **Assumed-and-not-labelled.** The natural-gas note says "1.5 % fugitive
  methane at 82× GWP20"; the number shipped (0.42 kg/kg) is 1.5 % × 28, the AR5
  100-year value, not 82 and not the AR6 27/29.8 the page cites. The
  `processes.py` PRODUCTS comment says "amounts are per kilogram as eaten, so
  losses are already folded into the amounts"; `lca.py` then scales every
  pre-bin stage by 1/(1−waste) and says leaving that out "understates the whole
  chain". Both cannot be true; one of them double-counts or the comment is
  stale. The "about the same as driving N km" yardstick is a hard-coded
  0.171 kg/km in `scene.js`, unsourced, and disagrees with the model's own
  petrol car (0.235 kg/km), so the page compares its answer to a car it did not
  compute. Finding 8.

---

## Engine parity

**`engine.js` and `lca.py` agree.** Established four ways:

1. **Read side by side.** Same two-pass structure (first pass with no hint to
   learn the total, second with the proportional cutoff), same recursion, same
   grid rule, same lifetime scaling, same over-production and landfill terms,
   same freight node. The only behavioural difference: Python
   `life_scale = default/life` raises `ZeroDivisionError` at `life=0`; JS
   guards `life > 0`. Unreachable from the UI (slider minimum is the product's
   `lt.min`; `?life=0` is rejected by `parseFloat(q) > 0`). Note text differs
   only in number formatting.
2. **The repo's own test.** `test_scene.js` runs 22 routes (14 food, 8
   vehicle with lifetimes) through both engines stage by stage. **25/25 pass,
   worst relative difference 2.17×10⁻¹⁶** (`test_scene_built.txt`). The
   discipline the brief asks about *was* applied here — better than the atlas,
   which has no automated parity test.
3. **My broader run on the shipped file.** `parity_shipped.js` loads
   `site/climate-cost-app.html` (not the build output) and compares 92 routes —
   every item at its default, a pseudo-random route, two antipodal routes, and
   for vehicles the lifetime minimum and maximum — 846 numbers (totals, cuts,
   kilometres, every stage). **Worst 3.55×10⁻¹⁶.**
4. **Against an independent evaluator** (Claim 1 above).

Two caveats that are findings in their own right:

- **The parity test could not run as checked out.** `climate-cost/node_modules`
  is a symlink to `/tmp/node_modules`, which does not exist; there is no
  `package.json`; `tests/` has no harness that includes `test_scene.js`. It
  passed only after I installed `jsdom` and `three` in a scratch directory and
  pointed `NODE_PATH` at them. So the parity check exists but has not been
  runnable on this machine since at least the 2 August build.
- **It tests the wrong file.** `PAGE` is `climate-cost/climate-cost.html`, the
  build output. The shipped `site/climate-cost-app.html` differs from it in 45
  diff lines (`built-vs-shipped.diff`): the `--acc-fill` tokens and the tab
  button fix from the 4 September palette correction, and a touch-action /
  `100dvh` block. Those edits were made to the shipped file by hand and **not
  to `template.html`**, so `python lca.py --build` followed by a copy reverts
  both. Engines agree; the build pipeline does not.

**What the tests cover / do not.** `test_lca.py` (20 items in literature
bands; tree sums; allocation compounds; levers move the right way; the
producing-grid bug; cutoff share) — 0 failures. It never exercises lifetimes,
same-region routes, allocation > 1, or the `cut` figure's accuracy.
`test_scene.js` adds parity, layout completeness, overlap, label seating,
idle cost. Neither tests the shipped file, the URL parameters, the list view's
numbers against the scene's, the content page's table (which does match: all
20 numbers reproduce), or the content page's figures — which is how 11.65 kg
went out.

---

## Findings, ranked

### 1. The "one hide" figure states a number the model does not produce — HIGH
See Claim 2. 4.40 kg at 7 %, not 11.65; ×1.20, not ×3. Appears in
`climate-cost.html` prose, the video caption, the poster frame, the mp4, and
the leather note in `processes.py`. No generator script in the repo. Fix: the
figure should be traced from `lca.py` the way `climate_chain_tomato.png` is
(`build_allocation_chain.py` is the model to follow); the prose becomes "a
fifth more", which is a smaller and truer point about where a shoe's carbon
actually is.

### 2. "Allocation" over 100 % on screen — HIGH (for a page about allocation)
Trainers freight 160 %, leather freight 120 %, every food freight node
100/(1−waste) % (tomato 123.5 %, banana 125 %). Ring geometry wraps past a full
circle. Root causes: the clothing freight stages store shipment mass in the
`allocation` field; both engines fold the over-production scale into the
freight node's `alloc`. Fix: a separate `mass_kg` on freight stages; freight
node reports `alloc` and puts scale on `amount` like its siblings; clamp the
ring at 1 and label anything else "×1.60 mass", not "allocation".

### 3. 45 % of the page is a precomputed answer set nobody reads — HIGH (weight)
`D.runs`, 123.6 KB raw / 17.5 KB gzip, unreferenced. Removing it takes the file
from 277 KB to 153 KB raw, 62 KB to 47 KB gzip (`browser.txt`, gzip test in
the session). Coastlines are a further 38.6 KB raw / 12.5 KB gzip for a globe
drawn at ~200 px. The actual model — processes + products + regions +
transport — is **44.5 KB raw**. Weight table, shipped file:

| block | raw KB | share |
|---|---|---|
| `runs` (dead) | 123.6 | 44.9 % |
| `coast` | 38.6 | 14.0 % |
| `products` | 32.8 | 11.9 % |
| `processes` | 9.6 | 3.5 % |
| `items` + `regions` + `transport` | 8.8 | 3.2 % |
| scene.js | 44.8 | 16.2 % |
| engine.js | 5.2 | 1.9 % |
| CSS | 9.0 | 3.3 % |

Plus three.js r128 from cdnjs: 603 KB raw, 121 KB on the wire. The
DESLOP audit's 387 KB total for this app is the page + three.js uncompressed.

### 4. At 390 px the chain diagram does not work; the list does — HIGH (mobile)
Measured on the shipped file, beef (25 nodes), home view, 390×844
(`mobile-dark-beef.png`, `browser.txt`):
- stage is 390×456 px under a 388 px panel;
- 3 of 25 nodes are outside the frame at the home view, the globe is
  half-cut at the left edge and "End of life" runs off the right;
- 4 of 9 stage labels are dropped, **including "Enteric fermentation"**, the
  largest single term in the whole model (43 kg of 75);
- median ball radius **2.5 px**, smallest **1.2 px** — not a touch target;
- there is no pinch or two-finger zoom: zoom is `wheel` only, so a phone
  reader can orbit but never magnify;
- the hint reads "drag to orbit · scroll to zoom · click a node · arrow keys
  walk the chain" and wraps under the Reset button.
The list view at 390 px is fine: no horizontal overflow, deepest indent 64 px,
every number and note readable (`mobile-dark-beef-list.png`). The honest fix
is to open in the list below ~600 px and offer the scene as the secondary
view, which is the reverse of today.

### 5. Provenance and grading are thinner than the pitch — MEDIUM–HIGH
Detailed under Claim 2. Four process citations plus GWPs for 42 processes;
no grades on stage-level directs; grids unsourced. The house rule is that an
unsourced number is labelled assumed; here it is labelled "B · literature
estimate" without saying which literature.

### 6. The build pipeline reverts the shipped fixes — MEDIUM–HIGH
`template.html` still has `.tabs button.on{background:var(--acc)}` (2.91:1 in
dark) and no touch-action / dvh block. The corrected file exists only in
`site/`. A rebuild silently reintroduces the AA failure and breaks touch
orbit. Fix: port the 45-line diff into `template.html` and make `--build`
write straight to `site/climate-cost-app.html` (or have the test read the
shipped path).

### 7. The system boundary is never stated where the total is — MEDIUM
The cutoff line only appears when `cut > 0`; for the four vehicle items it is
zero, so nothing about exclusion is shown at all. What is not modelled is
only discoverable by reading every note. One sentence under the total —
"excludes capital goods on farms and factories, water, particulates, vehicle
end-of-life; contributions under 0.15 % of the total are pruned and summed
here" — would satisfy the house rule.

### 8. Assumed numbers not labelled assumed — MEDIUM
- `scene.js` yardsticks 0.171 kg/km (car) and 0.214 kg/km (flight),
  unsourced; the model's own car is 0.235 kg/km, so "About the same as driving
  441 km" for beef would be 322 km by the model's own car.
- The compare line says "where it is eaten" for cars, flights and jeans (the
  globe pin was fixed for this in scene.js; the sentence was not).
- natgas note (82× GWP20) vs shipped factor (28× GWP100).
- PRODUCTS comment ("losses already folded in") vs engine (scales by
  1/(1−waste)).
- Bus lifetime note vs constant (1.65×).
- `scale = 60` "widest published food footprint" for the total bar — beef is
  75.49, so the bar saturates.
- Content page: "All nine items land inside their bands" (there are 20);
  "about what thirty-three kilometres of driving costs" reproduces from
  neither yardstick (41 km at 0.171, 30 km by the model's car).

### 9. The reported cut under-counts what was cut — LOW
`expand()` prunes on the pruned node's *direct* term and adds only that to
`cut`; the node's own upstream is dropped silently. On tomato Ethiopia→New
Zealand by air, `total + cut` is 1.9×10⁻⁵ below the true full-depth figure
(`independent.txt`). Negligible, but the sentence "X kg dropped below the
cutoff" is presented as the whole of what is missing and it is not.

### 10. Motion contract not honoured — LOW
No `data-motion`, no `prefers-reduced-motion` check anywhere in the app. The
only motion is the eased camera (k = 0.14 lerp on every select, reset and item
change) — user-triggered, no autoplay, and the idle loop provably sleeps
(test: 300 idle frames in 2 ms). A reduced-motion user still gets camera
flights on every click. Small, but the house rule is "anything that moves
must stop."

### 11. Contrast — LOW (text) / MEDIUM (labels on balls)
Every text pair against its designed background passes AA in both themes
(`contrast.txt`; worst 4.82:1, light geo pin over the stage edge; the 2.91:1
button is fixed in the shipped file, see finding 6). Failing at 3:1 for UI
boundaries: `--rule` on card/panel 1.28–1.44:1 both themes, `select:focus`
border 2.73:1 dark. **Labels that land on balls** — and they do, see
"Corrugated board", "Cold storage", "Ammonia synthesis" in
`desktop-dark-tomato.png` and the light render — are 1.0–1.3:1 (dim) and
2.1–3.0:1 (ink) against the ball colours, with a 4 px text-shadow as the only
help. The label placer avoids other *labels*, not balls. Light mode keeps the
globe hard-coded at `0x0b1226`, a dark disc on a white stage.

### 12. Type — LOW
Visible text nodes in the list view + panel, shipped file: 10 px ×17 (quality
badges), 10.5 px ×2 (section kickers), 11 px ×4, 11.5 px ×19, 12 px ×33,
12.5 px ×33, 13 px ×16, 17/20 px serif ×10, 27 px ×1. **42 text nodes under
12 px**; scene labels are 11.5 px and geo pins 11 px caps. Three faces
(system sans, Iowan/Palatino serif, mono for the slider value).

### 13. No way to share what you are looking at — LOW
The URL is read on load (`?item&from&to&mode&life`, all validated; nonsense
falls back cleanly to the tomato) but **never written**. After changing item
and destination, `location.search` is still empty. Tab and selection are not
in the URL at all. A reader who finds the electric-car-in-Poland result cannot
hand it to anyone without composing the query string by hand.

### 14. Load — informational
Cold, cache off, median of 3, local server (no gzip, so pessimistic on the
document):

| viewport | network | doc received | three.js received | total shown | scene settled |
|---|---|---|---|---|---|
| 1440×900 | unthrottled | 15 ms | 95 ms | 742 ms | 754 ms |
| 1440×900 | Slow 4G + 4× CPU | 2.16 s | 3.56 s | 4.69 s | 4.70 s |
| 390×844 | unthrottled | 30 ms | 144 ms | 1.11 s | 1.15 s |
| 390×844 | Slow 4G + 4× CPU | 2.18 s | 3.25 s | 4.17 s | 4.20 s |

With Pages' gzip (62 KB) the document leg would be ~0.4 s, so real-world
throttled first interaction is ~3 s, dominated by three.js (121 KB) and the
`runs` block. No console errors in any run. Nothing paints until both scripts
have run: the total reads "-" and the stage is black until `render()`.

### 15. Same-region route — informational, correct
France→France gives 0 km, freight 0, note "0 km by container ship …". Not a
blank, not a NaN. A short honest line ("no freight leg") would read better
than a zero-kilometre ship, but the number is right.

---

## What is good and must survive

- **One model, two languages, and a real test that they agree** — stage by
  stage, at 10⁻¹⁶. This is the discipline the atlas lacks. Keep the test;
  make it runnable (a `package.json`) and point it at the shipped file.
- **The tree sums at every node and the cutoff is proportional and reported.**
- **The producing-grid test** (a French dairy is not charged at India's grid)
  is the kind of test that encodes a bug's story so it cannot recur.
- **Lifetime as a control, log-scaled, "as published" at the default, carried
  in the URL.** The one place the page lets the reader argue with an
  assumption, and it is done well.
- **The notes.** The leak-rate range, the contrail factor-of-three, the
  land-use amortisation window, the almond water caveat, "occupancy is the
  lever nobody adjusts" — candid, specific, and the reason to trust the rest.
- **The list is a first-class view, not a fallback**, and it is the thing that
  works on a phone. Without WebGL the page opens into it and says why.
- **The idle loop sleeps** and is tested to.
- **`climate_chain_tomato.png` is traced from the live engine** by
  `build_allocation_chain.py`; every number on it reproduces (59.8 / 5.27 /
  3.20 / 0.386 g). That is the pattern the allocation figure should have used.
- **The download zip is byte-identical to the source** for all seven files.
- Quality pills, allocation rings (where alloc ≤ 1), the freight node pinned
  to the great-circle arc, arrow-key walking of the chain.

---

## Cross-check (read after everything above was established)

**DESLOP_AUDIT_2026-09-04.md.** Caught the 2.91:1 accent button in this app
(now fixed in the shipped file — but not in the template, finding 6), 31
sub-12 px elements (I count 42 text nodes in the list view; the scene adds
more), the 387 KB total. It did not open the engine, run a test, or look at
the data; nothing in Claims 1–2, findings 1–3, 5–9 or 13 is in it. Its weight
number does not separate the dead `runs` block from live code.

**DESIGN_AUDIT_EXTERNAL_2026-08-30.md.** Finding 8 saw the "one hide" figure
as a layout failure ("one bar, no axis, no comparison, 650 px tall") and took
11.65 kg at face value — it proposed two labelled bars at 3.66 and 11.65. The
second bar would be wrong. "What's missing" §8 asked for a worked example
before the calculator; that exists now (the tomato chain, traced from the
engine) and is the one figure on the page that is right. Its finding 12
("no AA failures in the core palette") was already corrected by the deslop
audit. Its small-type inventory did not include this app.

**The appendix checklist.**
- *engine.js and lca.py may have drifted, no parity test* — wrong on both
  counts: a parity test exists and passes at 10⁻¹⁶; the true problems are
  that it cannot run as checked out and tests the build output, not the
  shipped file.
- *"One hide" figure reads as broken* — confirmed, and worse: the number is
  not the model's.
- *20-item table with no inline bars* — agreed; it is a content-page point and
  the table's numbers are correct (all 20 reproduce).
- *Provenance thinner than implied* — confirmed (finding 5).
- *Cut-off unstated* — the numerical cutoff is stated (when non-zero); the
  boundary is not (finding 7).
- *Chain diagram unusable at 390 px* — confirmed with measurements (finding 4).
- *App CSS still carries 2.91:1* — the shipped file does not; the template
  does (finding 6).

**What both missed that this pass adds:** the dead precomputed block (44.9 %
of the page), allocation shown over 100 % on the default view, three
different quantities sharing the `allocation` field, the bus and gas-leak
note/number contradictions, the losses double-count question, the unsourced
driving yardstick that contradicts the model's own car, the URL never being
written, the motion contract, labels landing on balls at ~1:1, and the fact
that the download zip and the shipped page are both consistent with source
while the build template is not.

**What my method missed.** No real device: touch was measured as
`touch-action` and handler inventory, not with a thumb. No real network: the
throttled numbers are for an ungzipped local server. I did not evaluate the
literature bands in `test_lca.py` against the papers they cite. I did not
measure light mode on a phone.
