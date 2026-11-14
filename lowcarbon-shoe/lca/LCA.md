# LC-1 life cycle assessment (ISO 14040/14044 structure)

Comparative, screening-level LCA. **Not critically reviewed.** ISO 14044 (6.1, 6.3)
requires a panel review before a comparative assertion is disclosed to the public;
none has been done, so these results support a design decision and a published
explanation of method, not a claim against any brand's product. Results are
calculated. One impact category only (climate change).

Run: `python run.py` (numpy, matplotlib). Results: `results/lca_results.json`,
`results/factors_table.csv` (every factor with its source), `results/inventory.csv`,
`results/lca_summary.png`. Inputs: `params.py`, `../cad/out/volumes.json`.

## 1. Goal and scope

- **Goal.** Find whether LC-1 (DESIGN.md) emits at least 50 % less greenhouse gas
  per 100 km run than a mainstream daily running shoe, and which inputs decide it.
  Intended audience: the site's readers and anyone who builds LC-1.
- **Functional unit.** One pair, men's US 9, per 100 km run.
- **Reference flows.** Baseline: 1 pair per 550 km (assumed; 400-800). LC-1: 1 pair
  per 550 km (same life), or 1 upper + 2 sole units per 1,100 km (resole scenario).
- **Systems.** Baseline: cemented trainer, EVA midsole of the same CAD shape as
  LC-1's, carbon-rubber outsole, polyester mesh upper, PU foam parts, PU adhesive
  (bill of materials from Cheah et al. 2012 part shares and PEFCR footwear defaults,
  research/w2-03). LC-1: DESIGN.md section 2.
- **Boundary.** Cradle to grave: materials (cradle to gate, with manufacturing
  scrap), part making (yarn spinning, knitting, moulding, vulcanising, bead foaming),
  final assembly (electricity and fuels), packaging, sea and road freight, end of
  life. **Excluded for both:** dyeing and finishing (no open data), solvent
  production, retail, consumer travel, washing, capital goods, packaging end of life
  (assumed recycled; cut-off).
- **Cut-off criteria (ISO 14044 4.2.3.3.3).** Flows below 1 % of product mass are
  kept where data exist (labels, thread); flows with no open data are listed as
  excluded above rather than cut silently.
- **Geography and time.** Made in Viet Nam (grid 459 g CO2e/kWh, Ember 2025); sold
  and disposed of in the USA; data years 2006-2026.
- **Allocation.** Cut-off: recycled inputs carry only their recycling burden; no
  credit for recycling or energy recovery. Sensitivity: a 50:50 split of the
  recycling burden (scenario `lc1_cff_5050`).
- **Renewable electricity** is modelled at final assembly and the sole moulder
  only, at Ember's lifecycle factor for solar (48 g/kWh). In a real product this
  needs contractual instruments that meet ISO 14067 6.4.9.4 (on-site supply or a
  direct power purchase agreement with retired certificates); the model does not
  verify any.
- **Data quality requirements (4.2.3.6).** Public, free sources only; ecoinvent,
  ICE, Idemat, Higg MSI and EF 3.1 secondary datasets excluded, and so are published
  totals computed on an ecoinvent background (D-106, 2026-11-14: PET resin, the
  recycled-PET fibre band, the EVA high end and the TPU stress case were moved to open
  sources). Public industry eco-profiles computed on Sphera/GaBi background are kept. Every value is
  labelled published, derived or assumed in `params.py`; precursors 2014-2026,
  grid 2025, process energy 2006-2023.

## 2. Inventory

`params.py` lists every flow with central value, low, high, unit, basis and source;
`results/inventory.csv` lists the parts.

| Item | Baseline | LC-1 | Basis |
|---|---|---|---|
| Product mass per pair | 484 g | 460 g | BOM and CAD |
| Packaging per pair | 278 g | 120 g | PEFCR defaults / design choice |
| Final-assembly electricity | 2.88 kWh | 2.88 kWh (no discount assumed for the missing cement line) | FIF 2025, derived |
| Final-assembly fuels | 0.66 MJ gas + 0.61 MJ liquid | same | FIF 2025, derived |
| Midsole making | EVA moulding 2.5 kWh/kg (sole maker) | eTPU bead foaming 1.5 kWh/kg (bead supplier, grid) + moulding 2.5 kWh-eq/kg (half as gas-fired steam) | derived / assumed |
| Yarn spinning | 1.5 kWh/kg, all polyester | same | Ecobalyse default |
| Freight | 13,000 km ship + 1,500 km truck | same | assumed |
| Disposal | 19 % incinerated, 81 % landfilled | same | US EPA MSW 2018 |

## 3. Impact assessment (central case, kg CO2e per pair)

| Stage | Baseline | LC-1 design, grid power | LC-1 as specified |
|---|---|---|---|
| Materials | 1.81 | 1.02 | 1.02 |
| Part making | 0.43 | 0.51 | 0.37 |
| Final assembly | 1.40 | 1.40 | 0.22 |
| Packaging | 0.22 | 0.09 | 0.09 |
| Transport | 0.34 | 0.26 | 0.26 |
| End of life | 0.26 | 0.22 | 0.22 |
| **Per pair** | **4.46** | **3.49** | **2.17** |
| **Per 100 km** | **0.81** | **0.64** | **0.40** |
| Reduction per 100 km | | 21.7 % | 51.3 % |

Context, not inputs: published per-pair totals for running shoes run from 6.7 kg
(Footwear Innovation Foundation 2025, a budget shoe) to 14 kg (Cheah et al. 2012,
a 2010 factory with coal-fired steam). This model's baseline is lower: it excludes
dyeing, finishing and retail, uses a 2025 grid and a coal-free factory (FIF 2025
found no coal in 33 factories). `cheah_check` in the results is a factor check, not
a validation: both its inputs are worked back from the paper's own results.

## 4. Interpretation

- **Scenarios** (`results/lca_results.json`, "scenarios"): design only 21.7 %; LC-1
  as specified 51.3 %; with the upper kept for a second sole unit 59.9 %; with that
  and 15 % longer sole life 65.2 %. The BASELINE shoe moved to renewable electricity
  at the same two sites cuts 32.2 %. Allocation 50:50: 43.2 %. No separate
  sole-making energy (if final assembly already includes it): 49.6 %. Made in China:
  53.0 %; in Indonesia: 56.7 %. TPU at 4.79 kg CO2e/kg (built from the highest open
  raw-material figures; no producer publishes one): 45.0 %.
- **Monte Carlo** (10,000 draws, triangular on every swept input, the same draw for
  both shoes, grid held to Viet Nam): LC-1 as specified, median 47.6 %, 5-95 %
  39.4-54.2 %, P(>= 50 %) = 0.28. With upper lives uniform between 1 and 2 sole
  units: median 53.4 %, P = 0.75. Design only: median 24.9 %, never 50 %.
- **Sensitivity** (one at a time, `tornado`): final-assembly electricity per pair
  (43-53 %), the recycled-PET fibre factor (47-54 %), upper mesh mass, eTPU density,
  bead-foaming energy, the TPU factor, the EVA density, the recycled-TPU share.
- **Consistency check (4.5.3.4).** Both shoes use the same factors, grid, freight,
  disposal shares, life and midsole shape; LC-1 gets no assembly discount and
  carries bead-foaming energy set above EVA moulding. Asymmetries that remain and
  favour LC-1: no shoebox (equal packaging gives 46.8 %, 4.5 points less), cut-off
  allocation of recycled content (8.1 points; scenario above).
- **Completeness check.** Dyeing and finishing are missing from both; for polyester
  textiles they can be large, and they would add the same order of emissions to
  both uppers.
- **Data quality.** Weakest inputs: the TPU factor (no producer figure is public;
  built up from precursor eco-profiles), eTPU foaming and moulding energy (no data),
  the baseline bill of materials (no measured teardown), life in km (no primary
  source for the 300-500 mile rule), and upper life.
