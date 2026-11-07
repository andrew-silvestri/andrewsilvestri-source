# LC-1 results: scorecard against research/SPEC.md

Every result below is SIMULATED (finite element model) or CALCULATED (from
published data). None is a physical test. The LCA has had no ISO 14044 critical
review. Re-run everything with:

    python cad/lc1_cad.py && python cad/upper_pattern.py && python cad/render.py
    python tests/fea_heel.py && python tests/fea_heel.py lattice && python tests/calc_tests.py
    python lca/run.py

(Python 3.12; cadquery, scikit-fem, numpy, scipy, matplotlib, trimesh, ezdxf.)
Two independent checks (research/v-01-lca-check.md, research/v-02-fea-check.md)
found errors in a first version; the numbers below are after their corrections
(DECISIONS.md, 2026-11-07).

## Scorecard

| ID | Target | Result | Pass/fail | Evidence |
|---|---|---|---|---|
| T1 | GHG per 100 km at most 50 % of baseline (Monte Carlo median) | Single life, renewable power at assembly and sole moulder: 0.40 against 0.79 kg CO2e per 100 km, **49.8 % lower** central; Monte Carlo median 47.1 % (5-95 %: 38.6-54.1), P(>= 50 %) = 0.26. With the upper kept for a second sole unit: **58.8 %** central; median 53.0 % with upper lives drawn between 1 and 2, P = 0.72. Design alone, grid power: 19.6 %. | **FAIL** as a single-life shoe (by the median rule); PASS only if the upper serves a second sole | `lca/results/lca_results.json` |
| T2 | Virgin fossil plastic at most 50 % of baseline | 198 g against 466 g per pair (42 %) | PASS | same, `pair.*.mass` |
| T3a | 90 % of mass separable by hand into single-polymer streams | 100 %: TPU sole unit (eTPU + TPU) and PET upper; the rTPU heel counter slides out of its pocket | PASS by design; needs a physical cut test | DESIGN.md section 3 |
| T3b | An operating post-consumer recycling route for the TPU sole | None open to an individual today | FAIL | `research/w2-06-eol-routes.md` |
| T4 | 5 J drop peak force within 15 % of the baseline | 897 N against 932 N (-3.8 %) at the calibrated rate factor; +7.9 % to -10.7 % across rate factors 1-2 | PASS (simulated) | `tests/results/fea.json` (`t4_sweep`) |
| T5 | Energy return at least 65 % | 75.9 % for an eTPU-midsole shoe (Hoogkamer et al. 2018); 82 % for the eTPU material (Aimar et al. 2024, derived as 1 - pi x loss factor) | PASS (published data for the material class) | `tests/results/energy_return.json` |
| T6 | At most 300 g per shoe | 229.9 g (range 196-290 g); baseline of the same midsole shape 242 g | PASS (calculated) | `tests/results/mass.json` |
| T7 | Outsole wear life at least the baseline's | Median 3,330 km against 2,150 km to wear through; P(LC-1 >= baseline) = 0.94 | PASS (calculated; ISO 4649 ranks, it does not predict) | `tests/results/wear.json` |
| T8 | Midsole keeps at least EVA's share of absorbed energy after 200,000 cycles | eTPU (240 kg/m3) keeps 54 %; filled EVA 28-32 % | PASS for the material class; LC-1's 200 kg/m3 foam is untested | Aimar et al. 2024, `research/data/aimar2024_digitised.csv` |
| T9 | Commercially available materials and processes | All are; the combination has not been made | PASS, with the caveat | DESIGN.md section 5 |

## What each simulated test did

**Midsole compression (FEA), `tests/fea_heel.py`.** Axisymmetric layered disc
(outsole, 26 mm midsole, 4 mm sockliner) on a rigid floor under a rigid flat
striker. Each foam element's secant modulus follows its foam's published
stress-strain curve (Aimar et al. 2024: EVA 170 kg/m3 and eTPU 240 kg/m3 from the
same rig; eTPU scaled to 200 kg/m3 by density squared), iterated to convergence.
One impact-rate factor (1.5) multiplies both curves; it is calibrated so that the
model reproduces Verdejo's measured 1.10 kN for a new EVA trainer heel, and it puts
the baseline at 932 N, inside the published 809-1,259 N for running shoes at 5 J.
Self-checks: the 1-D column force is reproduced exactly (0.0 % at 20, 40 and 60 %
strain); doubling the foam's stress raises the drop peak from 932 N to 1,227 N; an
independent rerun confirmed the weak form, the DOF ordering and mesh convergence
(peak forces within 0.3 % from 544 to 17,000 elements; research/v-02).

| Case | Baseline (EVA) | LC-1 (eTPU, 200 kg/m3) |
|---|---|---|
| ASTM F1976-style drop, 8.5 kg, 5 J, 45 mm striker: peak force | 932 N (11.2 g) | 897 N (10.8 g) |
| T4 difference across rate factors 1 / 1.5 / 2 | | +7.9 % / -3.8 % / -10.7 % |
| Heel under 1.12 body weights, rigid 28 mm heel: deflection ratio LC-1/baseline | | 1.63 |

The absolute heel deflections and the peak strains and stresses are not reliable
(small-strain kinematics at 60-85 % strain, and the stress at the striker edge is
not mesh-converged); only the ratio is reported. LC-1 is the softer shoe under
running load.

**Home-print lattice, `tests/fea_heel.py lattice`.** A printed TPU gyroid,
modelled as a Gibson-Ashby open-cell elastomer, matched the baseline's drop peak
within 15 % at relative densities 0.25-0.35 for solid-TPU moduli of 8-30 MPa (the
scan is in `tests/results/fea_lattice.json`; below 0.2 the lattice bottoms out).
At 0.3 the printed midsole weighs about 150 g per shoe. The model is crude for
gyroids; the coupon ladder in BUILD.md decides it physically.

**Energy return, outsole wear, mass:** `tests/calc_tests.py`, method and
assumptions in each JSON.

## The home-printed prototype is a test article, not a low-carbon shoe

Printing about 0.5 kg of TPU per pair at 11-80 kWh/kg (FDM; Gutowski et al. 2017)
on the US grid (384 g/kWh) adds 2-16 kg CO2e per pair: more than the whole
baseline shoe. Build it to test fit, cushioning, grip and the stitch joint. The LCA
covers the production route (moulded eTPU).

## Proven by calculation, and what needs a physical test

Calculated, given the inputs: the carbon accounting (T1, T2), the mass (T6), that
the eTPU stack absorbs a 5 J drop with a peak force close to the EVA stack's (T4).

Needs a physical test (BUILD.md): wet and dry grip of the TPU outsole; the stitch
rim's strength under running shear and over thousands of cycles; the in-mould
bond of eTPU to the TPU skin; the wear rate of the TPU skin; how long the upper
lasts (this decides T1); feel and stability of the softer eTPU stack; whether
worn soles are returned and recycled.

## Biggest uncertainties (largest first, one at a time)

1. Final-assembly electricity per pair (1.17-3.32 kWh): LC-1's cut moves 41-52 %.
2. Whether renewable electricity is really supplied (without it, 20 %).
3. The recycled-PET fibre factor (0.55-2.32 kg CO2e/kg): 45-54 %.
4. Upper mesh mass, eTPU density, bead-foaming energy (no data), the TPU factor
   (no producer publishes one; at 6.96 kg CO2e/kg from an ecoinvent-based EPD, 35 %).
5. Allocation of recycled content: 50:50 instead of cut-off gives 43 %.
6. How far shoes are run (held equal for both shoes) and how long the upper lasts.
