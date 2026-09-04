# Climate cost fix — Phase 1 — 2026-09-04

Acts on `AUDIT_CLIMATE_COST_2026-09-04.md` per `prompts/CLIMATE_COST_FIX.md`.
**Phase 1 only.** Nothing in `site/` was touched. Evidence and working files
in `_audit-climate-cost/fix/` (gitignored). Phase 2 sections are placeholders
until a product is chosen.

---

## 1a. The `allocation` field is now three fields

**What changed.** `climate-cost/data/processes.py`: every stage-level
`allocation=` is gone. Twenty-four occurrences became:

| new field | meaning | range | count | stages |
|---|---|---|---|---|
| `share` | co-product allocation: the fraction of the stage's burden that belongs to this product because the stage also makes something else | 0 < share ≤ 1 | 11 | beef slaughter 0.72, chicken slaughter 0.78, coffee wet-mill 0.55, almond hulling 0.62, cheese enteric/feed/manure/milking 0.85 ×4, cheesemaking 0.90, rice milling 0.80, leather hide 0.022 |
| `amortise` | capital-good amortisation: functional unit ÷ lifetime; the field the lifetime slider rescales | tiny | 8 | car/EV manufacture 0.0005, car/EV delivery 0.0005, bus 6.3×10⁻⁶, rail 8×10⁻⁸, short-haul 2×10⁻⁷, long-haul 9×10⁻⁸ |
| `freight_kg` | mass shipped on a transport stage, kilograms per functional unit (food ships 1 kg and omits it) | > 0, may exceed 1 | 7 | t-shirt 0.22 / 0.20, jeans 0.85, trainers 1.6, leather shoes 1.2, car delivery 1.4, EV delivery 1.6 (see the bug below) |

`lca.py` and `engine.js` read the three fields identically: `share ×
amortise` (× lifetime scale) multiplies everything in the stage, as `allocation`
did; `freight_kg` multiplies the freight leg only. A header comment in
`processes.py` defines the three fields and says why they were split.

**Proof that no total moved.** `_audit-climate-cost/fix/before_after.txt`:
before the edit every product's total, cut, every stage total and direct, every
child total, and three lifetimes per vehicle were frozen to
`baseline_before.json`; after the edit the same 20 products were re-run.
**Worst relative change in any emission number: 2.1×10⁻¹⁶.** `test_lca.py`
0 failures; `test_scene.js` 25/25 with the rebuilt `climate-cost/climate-cost.html`,
parity worst 2.17×10⁻¹⁶ (`test_scene_after.txt`).

**What did change, by design (display only).** The freight node used to carry
mass and the waste over-production factor inside its `alloc` field, which is
how a tomato's ship read "allocation 123.5 %" and trainers' "160 %". Now the
freight node's `alloc` is `share × amortise` like every other node, and the
mass and waste scale live in `amount` (tonne-km actually moved). Sixteen
freight nodes changed `alloc`/`amount` this way; the list is in
`before_after.txt`. The panel will now show "Allocation 100 % (all of it)"
for a tomato's ship and "Amount 13.8 tonne-km"; no ring is drawn. `scene.js`
was not edited.

**The second bug, as the brief predicted.** Disambiguating exposed a unit
slip. The engine reads the freight field in **kilograms** (`ef × km/1000 ×
mass` is kg CO2e when mass is in kg). The two car delivery stages shipped
`allocation=0.0007` and `0.0008`, which the notes describe as "0.7 kg of
vehicle moved" — i.e. 1400 kg × (100 km ÷ 200,000 km). But 1400 × 0.0005 =
0.7, and the field holds 0.0007: **the vehicle mass was typed in tonnes into a
field the engine reads in kilograms.** The delivery leg is a thousandth of its
true size. Preserved as `amortise=0.0005, freight_kg=1.4` (and `1.6` for the
EV, which also rounded 0.00075 up) so that this phase remains a rename, with a
comment at the site saying exactly this. Corrected values, for Phase 2:

| product | delivery leg as shipped | corrected (freight_kg 1400 / 1500) | total as shipped | corrected |
|---|---|---|---|---|
| car, petrol DE→TX | 0.0001 kg | 0.097 kg | 23.474 | 23.571 (+0.41 %) |
| car, electric CN→TX | 0.0002 kg | 0.148 kg | 12.664 | 12.812 (+1.17 %) |

Both stay inside their literature bands. Both published table entries
(23.47, 12.66) would change at the second decimal. **Stopped here on this
one; it is your call whether Phase 2 corrects it** (recommended: yes, and
re-verify the bands).

---

## 1b. Sensitivity of every product to its co-product share

Every product, every stage carrying a real `share`, default route. "share=1"
is the naïve footprint (the product carries the whole joint process);
"share/2" is a generic halving to show the lever's reach. Full output:
`_audit-climate-cost/fix/sensitivity.txt`.

| product | contested stage(s) | share | stage kg | of total | total | at share=1 | × | at share/2 | × |
|---|---|---|---|---|---|---|---|---|---|
| leather shoes | hide | 0.022 | 0.34 | 9.3 % | 3.66 | 18.79 | 5.13 | 3.49 | 0.95 |
| **cheese** | **enteric + feed + manure + milking** | **0.85** | **12.31** | **95.8 %** | **12.86** | **15.03** | **1.17** | **6.70** | **0.52** |
| coffee | wet mill | 0.55 | 0.39 | 12.8 % | 3.05 | 3.37 | 1.11 | 2.85 | 0.94 |
| almonds | hulling | 0.62 | 0.04 | 2.2 % | 1.74 | 1.76 | 1.01 | 1.72 | 0.99 |
| rice | milling | 0.80 | 0.05 | 1.5 % | 3.39 | 3.40 | 1.00 | 3.37 | 0.99 |
| chicken | slaughter | 0.78 | 0.05 | 1.0 % | 5.02 | 5.03 | 1.00 | 4.99 | 1.00 |
| cheese | cheesemaking (whey) | 0.90 | 0.08 | 0.6 % | 12.86 | 12.87 | 1.00 | 12.82 | 1.00 |
| beef | slaughter | 0.72 | 0.07 | 0.1 % | 75.49 | 75.52 | 1.00 | 75.46 | 1.00 |

Thirteen products carry no co-product share at all (both tomatoes, banana,
all six vehicles, all four non-leather garments).

**Reading it.** Only one product in the set has its total *sitting on* an
allocation decision: cheese, where 95.8 % of the kilogram is the herd stages
carrying the milk/meat split. Leather's ×5.13 is the share going to 1.0,
which no method proposes; at any published hide share it is ×1.2 (below).
Beef's slaughter share, which the brief guessed might matter, moves the total
by 0.1 %: the cow's methane and land are spine stages with no share on them,
so nothing an abattoir does reaches the number. Everything else is under 13 %.

---

## 1c. Sourcing the alternative factors

### Cheese — every factor sourced, and the shipped 0.85 turns out to be one of them

Flysjö, Cederberg, Henriksson & Ledgard 2011, *Int J Life Cycle Assess* 16:420–430,
"How does co-product handling affect the carbon footprint of milk? Case study
of milk production in New Zealand and Sweden", Table 1 (quoted from the paper
as reprinted in Flysjö's 2012 Aarhus PhD thesis, p. 118, saved as
`_audit-climate-cost/fix/Flysjo_2012_PhD_thesis_AU.pdf`):

> "The allocation factor for milk is calculated (using the equation provided
> in IDF (2010)) to 86% for NZ and 85% for SE."
> "For NZ, the economic allocation factor for milk is 92% (Ledgard et al.
> 2009b) and for SE 88% (Farm Economic Survey)."
> "Thus, the protein allocation factor for milk is 94% and 93% for NZ and SE,
> respectively."
> "The mass allocation factor for milk is 98% for both NZ and SE."
> "System expansion resulted in 63–76% of GHG emissions attributed directly to
> milk, while allocation resulted in 85–98%."

IDF Bulletin 479/2015, *A common carbon footprint approach for the dairy
sector*, pp. 34–36 (saved as `IDF_Bulletin479_2015.pdf`, text in `.txt`):

> "The approach recommended here is to use a physical allocation method. This
> aligns with step 2 in ISO 14044 …"
> "AF_milk = 1 – 6.04 × BMR" … "As a typical value for BMR, we can take 0.02
> kg meat/kg milk, yielding an allocation of 12% to meat and an allocation of
> 88% to milk."
> worked example, p. 36: "1 – 6.04 × 0.024 = 0.86"

Cheese, France → New York, herd stages at each sourced share
(`_audit-climate-cost/fix/candidates.txt`):

| basis | milk share | kg CO2e | × |
|---|---|---|---|
| system expansion, low end (Flysjö 2011) | 0.63 | 9.67 | 0.75 |
| system expansion, high end (Flysjö 2011) | 0.76 | 11.55 | 0.90 |
| IDF 2010 physical, Sweden (Flysjö 2011) — **as shipped** | 0.85 | 12.86 | 1.00 |
| IDF 2010 physical, New Zealand (Flysjö 2011) | 0.86 | 13.00 | 1.01 |
| IDF 2015 physical, typical BMR 0.02 (Bulletin 479 p. 35) | 0.88 | 13.29 | 1.03 |
| economic, Sweden (Flysjö 2011) | 0.88 | 13.29 | 1.03 |
| economic, New Zealand (Flysjö 2011) | 0.92 | 13.87 | 1.08 |
| protein (Flysjö 2011) | 0.93 | 14.02 | 1.09 |
| mass (Flysjö 2011) | 0.98 | 14.74 | 1.15 |
| no allocation — milk carries the whole cow | 1.00 | 15.03 | 1.17 |

Two things fall out. First, the shipped 0.85 is a real published number: the
IDF physical-causality factor for Swedish milk in Flysjö 2011. Second, the
data note is wrong about *what* it is: `processes.py` says "0.85 to milk is
the IDF standard **economic** split". IDF's method is physical (feed energy),
not economic; the Swedish economic factor in the same table is 0.88. That is
a third note-vs-number error to correct in Phase 2, alongside the gas-leak
GWP and the bus lifetime found in the audit.

### Leather — sourced, and it settles the shoe at ×1.2

Lunesu, Correddu, Carta, Sechi, Farina & Pulina 2025, *Animals* 15(24):3546,
"Attributing Farm-to-Slaughter Emissions to Hides: Evidence from Beef Supply
Chains" (open access, PMC12729734):

> "Physical allocation attributed an average of 5.9% of live weight to hides"
> — range "from a minimum of 4.2% in cull dairy cows … to a maximum of 6.9% in
> semi-heavy young bulls … with a mean of 5.88%."
> "economic allocation … averaging 2.68% for 2023."

| hide share | basis | kg CO2e | × |
|---|---|---|---|
| 0.022 | as shipped (unsourced "economic") | 3.66 | 1.00 |
| 0.027 | economic, 2023 mean (Lunesu 2025) | 3.74 | 1.02 |
| 0.059 | physical, live-weight mean (Lunesu 2025) | 4.23 | 1.16 |
| 0.069 | physical, maximum (Lunesu 2025) | 4.39 | 1.20 |
| 0.070 | "about 7 %" as the page claims (unsourced) | 4.40 | 1.20 |

So the Phase 2 correction of `processes.py:1079` can be fully sourced: hide
is 9.3 % of the shoe; moving from the economic mean (2.7 %) to the physical
mean (5.9 %) gives ×1.16; the page's "7 %" is Lunesu's upper bound and gives
×1.20. Not ×3.

### Coffee — disqualified

Wet-mill pulp/mucilage allocation at 0.55 is 12.8 % of the total, and I could
not find a published factor for that split in this pass (the coffee LCAs
found — Coltro, Killian, Noponen, Chéron-Bessou 2024 — treat cultivation as
the hotspot and do not give a pulp share). No sourced alternative, so no
showcase.

### Beef, chicken, rice, almonds — irrelevant

Under 2.2 % of total on the shared stage. Nothing to show.

---

## 1d. Candidates and recommendation

**The honest showcase with a large swing does not exist in this data.** No
product in the set moves by more than ×1.20 between the economic and physical
bases, and none triples under anything short of "charge the whole cow to the
shoe". *(Withdrawn wording, kept for the record: the Phase 2 definition —
highest ÷ lowest across all published bases including system expansion and
no allocation — gives cheese ×1.55 and the shoe ×1.17; see Phase 2.)*

What does exist:

**Candidate 1 — cheese (recommended).** The only product where the number is
*made of* the allocation decision (95.8 %). Every factor is a quoted, named
published value, and the shipped one is among them. The spread is real and
defensible: 9.7 kg to 15.0 kg for the same kilogram of the same cheese,
depending only on how the cow's meat is credited, with the IDF's own method
sitting in the middle. Preferred by the brief's own rule ("prefer a product
whose numbers are among the cited ones"): after this phase, cheese's herd
share is the best-sourced allocation in the database. The sentence I would
defend: *"The same kilogram of French cheese is 9.7 kg CO2e if the cow's meat
is credited by system expansion, 12.9 under the International Dairy
Federation's physical split, and 15.0 if milk carries the whole cow — every
one of those a published method, and a spread that no farming change
produces."* Six bars, sourced, generated from `lca.py`.

**Candidate 2 — the leather shoe, told truthfully.** Same asset slot, inverted
claim: "allocation is where footprints hide their assumptions — and for a
shoe it barely matters: ×1.16 between the economic and physical means." Fully
sourced (Lunesu 2025). Quieter, but it is the correction of the exact false
claim and it teaches that allocation matters where the shared stage is big,
which cheese then demonstrates. Could be the *second* panel of the cheese
figure rather than a competitor.

**Candidate 3 — coffee.** Disqualified on sourcing.

**Recommendation:** cheese as the showcase, with the shoe as a one-line
counter-example in the same figure ("and here is one where it does not
matter"). The figure generator in Phase 2 should draw both from `lca.py` with
the factors above hard-coded next to their citations.

---

# Phase 2 — cheese, with the shoe as the counter-example

Product chosen: cheese. The shoe stays in the same figure as the case where
allocation barely applies, which retires the false claim by replacing it with
the true one about the same product.

## The one framing of "how much it moves"

**Spread = highest total ÷ lowest total across the published bases shown.**
Not adjacent bases, not economic against physical, not the default against
anything. It is defined in the figure's footnote, in the generator's docstring,
and used in the page prose and nowhere is any other multiple used.

| product | published bases shown | lowest | highest | spread |
|---|---|---|---|---|
| Cheese, hard, France → New York | 63 % … 100 % milk (Flysjö 2011; IDF 2015) | 9.67 kg | 15.03 kg | **×1.55** |
| Shoes, leather, Italy → New York | 2.7 % … 6.9 % hide (Lunesu 2025) | 3.74 kg | 4.39 kg | **×1.17** |

The Phase 1 report's "nothing moves more than ×1.20 between any two published
bases" was the narrower quantity (excluding system expansion and no-allocation
as bases); it is withdrawn in favour of the definition above. The shoe's
shipped 2.2 % is an assumption, not a published value: it is drawn in grey and
not counted in the spread.

**The sentence the page now makes and I would defend:** *the same kilogram of
French cheese is 9.7 kg CO2e if the cow's meat is credited by system
expansion, 12.9 under the International Dairy Federation's physical split
(the model's default), and 15.0 if milk carries the whole cow; the spread
across the published bases is ×1.55, and for the leather shoe, where the
hide is 9 % of the pair, the same exercise gives ×1.17.*

## What was done

1. **False assets deleted.** `site/assets/climate_allocation.mp4` and
   `climate_allocation_poster.png` removed; the `<video>` block and its
   caption removed from `site/climate-cost.html`. No other reference existed
   (`grep` over `*.py`, `*.sh`, `*.html` outside audits and backups).
2. **`processes.py` corrected.** The leather note now gives the true
   sensitivity (hide ≈ 9 % of the pair; economic mean 2.7 % → physical mean
   5.9 % lifts the pair from 3.7 to 4.2 kg) with Lunesu et al. 2025 named, and
   records what the note used to claim and why it was wrong. The cheese note
   no longer calls 0.85 "the IDF standard economic split": it is the IDF
   physical split for Swedish milk in Flysjö 2011, and the note lists the
   economic, protein, mass and system-expansion values from the same table.
3. **Basis is a field.** Every `share` now carries `basis=` — either the
   named basis and source (`"physical, IDF feed-energy (Flysjo et al. 2011,
   Sweden)"`) or `"unstated (assumed)"` for the seven shares that have no
   published source (beef and chicken slaughter, coffee wet-mill, almond
   hulling, rice milling, cheesemaking whey, and the shoe's 2.2 %, marked
   economic-assumed with Lunesu's 2.7 % cited beside it). `lca.py` and
   `engine.js` carry `basis` into the spine node; the app's selection panel
   and list view print it beside the share, so a share is never shown without
   saying what kind it is. `test_lca.py` §10 fails on a share without a basis.
4. **Generator in the repo:** `climate-cost/build_allocation_figure.py`.
   Runs `lca.py` once per bar with the factor on the contested edge, refuses
   to draw if the shipped default no longer reproduces the page's table
   (12.86 / 3.66), audits its own type floor, overlaps and canvas, and writes
   `site/assets/climate_allocation_bases.png` (2280×1341, 107 KB, 0 audit
   problems). Every factor sits in the source next to its citation. The page
   caption names the script; the figure's footnote names it too. Added to the
   download zip (now 8 files, `code.html` row updated).
5. **Page.** New paragraph on cheese and the shoe with the defined spread;
   figure and caption; the Allocation section's "two careful studies … can
   differ twofold" — another unsourced flattering number — replaced with "by
   half again" and the 63–100 % range; "All nine items land inside their
   bands" → twenty; car table entries 23.47 → 23.57 and 12.66 → 12.81 (units
   fix, own write-up). Three sources added through `add_citations.py`
   (Flysjö 2011, IDF Bulletin 479, Lunesu 2025), applied to this page only
   because `longevity.html` currently has two anchors the script cannot find
   and a full `--apply` would drop them. `add_citations.py` also gained a
   one-line fix: it looked for the literal `<main>`, which the deslop pass
   had just turned into `<main class="notes">`, so its "inside main only"
   guard was silently off.
6. **Template reconciled before rebuild.** The 45-line shipped-vs-template
   diff (`--acc-fill` tokens, tab button, touch-action / dvh block) ported
   into `template.html`; the rebuilt CSS block is byte-identical to what was
   shipped. Then `lca.py --build` and the output copied to
   `site/climate-cost-app.html`.
7. **Verification.** `test_lca.py` 0 failures (now 11 checks);
   `test_scene.js` 25/25, parity 2.2×10⁻¹⁶; the 92-route / 846-number parity
   run against the *shipped* app 3.8×10⁻¹⁶; headless Chrome on the shipped app
   shows "Allocation 85.0 % — basis: physical, IDF feed-energy (Flysjo et al.
   2011, Sweden)" on the cheese herd stages, "×0.85 physical, IDF feed-energy"
   in the list heads, freight nodes at 100 % with the mass in the amount, car
   totals 23.571 / 12.812, no console errors; the content page serves the
   figure (HTTP 200), lists 8 sources, has no `<video>`.
8. `bust_cache.py` run (figure stamped `?v=24bb8306`). `HANDOFF.md` §8 gained
   trap 12. **Not published.**

## Left for a decision (found, not changed)

- **Cheesemaking gas has no combustion term** (0.12 kg gas, `direct=0.0`;
  every other gas use in the model charges 2.75 kg/kg for burning it). If it
  is burned, the cheese is 0.33 kg (+2.6 %) low. On the showcase product, so
  worth deciding before Phase 3c ships. Details in
  `CLIMATE_COST_UNITS_2026-09-04.md`.
- **Rail track borrows `road_infra`** at a 150× scale as "road-equivalent";
  should be its own process.
- The `D.runs` dead block (45 % of the app's weight) and the audit's other
  app findings are untouched; this brief was the false claim.

## Files touched in Phase 2

- `climate-cost/data/processes.py`, `lca.py`, `engine.js`, `scene.js`,
  `template.html`, `test_lca.py`, `build_allocation_figure.py` (new)
- `climate-cost/climate-cost.html` (rebuilt) → `site/climate-cost-app.html`
- `site/climate-cost.html`, `site/code.html`, `site/downloads/climate-cost-code.zip`
- `site/assets/climate_allocation_bases.png` (new); `climate_allocation.mp4`
  and `climate_allocation_poster.png` (deleted)
- `add_citations.py`, `HANDOFF.md`, this file, `CLIMATE_COST_UNITS_2026-09-04.md`
- `_audit-climate-cost/fix/` — baselines, proofs, sweep, sources, live-check
  screenshot `app-cheese-basis.png`
