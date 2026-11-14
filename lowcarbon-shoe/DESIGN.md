# LC-1: a lower-carbon daily running shoe (digital prototype)

Status: a digital prototype. Every performance and carbon figure in this package is
SIMULATED or CALCULATED. Nobody has built or run in an LC-1. BUILD.md says how to
build a test article and what to test.

## 1. Concept in one paragraph

In this package's baseline model a running shoe's footprint splits into the
plastics it is made of (1.81 kg CO2e per pair) and the energy of the factories that
make it (1.84 kg: 1.40 at final assembly, 0.43 making the sole parts), out of
4.46 kg. LC-1 works on both. It is two parts joined by thread, with no adhesive: a
**sole unit** of thermoplastic polyurethane (TPU) only, and an **upper** of
recycled polyester. The sole unit is an expanded-TPU (eTPU) bead-foam midsole
moulded together with a thin solid TPU outsole skin and a solid TPU stitch rim. The
upper is stitched through the rim (stitchdown, the construction of resoleable
boots). Cutting the thread separates the shoe into one polymer family per part, and
a cobbler can stitch a new sole unit onto a sound upper. LC-1 is specified to be
assembled, and its sole moulded, on renewable electricity.

Result (central case, `lca/results/lca_results.json`): per 100 km, the design alone
cuts 22 %; with renewable electricity at the two sites, 51 % (Monte Carlo median
48 %); with the upper kept for a second sole unit, 60 %.

## 2. Bill of materials (one shoe, men's US 9)

Sole masses are CAD volume (`cad/out/volumes.json`) x density. Upper masses follow
the baseline bill of materials (`research/w2-03-baseline-bom.md`). "Supplier type"
names a class of supplier, not a company; nothing was ordered.

| Part | Material | Mass, g | Supplier type | Data source |
|---|---|---|---|---|
| Midsole | Expanded TPU bead foam, 200 kg/m3 | 83.7 | Bead-foam moulder (steam-chest moulding) | CAD 418 cm3; density chosen by the calibrated FEA (tests/) |
| Outsole skin, 1.5 mm, arch window | TPU 95A, 75 % post-industrial recycled | 34.9 | Injection moulder; recycled-TPU compounder | CAD 29.1 cm3 x 1.20 g/cm3 |
| Stitch rim, 3 x 8 mm | Same TPU as the skin, moulded with it | 17.7 | Same | CAD 14.8 cm3 |
| Sockliner, 4 mm | Recycled-PET 3-D spacer fabric | 11.6 | Technical-textile mill | CAD 77.5 cm3 x 0.15 g/cm3 (assumed) |
| Upper mesh and lining, cut and sewn | Recycled PET | 46 | Warp-knit mesh mill; cutting room | as baseline mesh + lining |
| Collar padding | Recycled-PET spacer fabric | 8 | Technical-textile mill | as baseline padding (PU foam) |
| Strobel sock | Recycled PET | 10 | | as baseline strobel |
| Heel counter | Recycled TPU sheet 1.0-1.5 mm | 9 | Thermoformer | as baseline |
| Laces | Recycled PET | 5 | | as baseline |
| Stitchdown thread | Recycled PET, bonded | 3 | Thread maker | assumed |
| Label | Recycled PET | 1 | | assumed |
| **Shoe** | | **229.9** (range 196-290) | | `tests/results/mass.json` |

Packaging per pair: a 60 g paper sleeve and a 60 g share of the shipping carton,
in place of a 180 g shoebox, 26 g tissue and a polybag (278 g in the baseline).

Fossil-based virgin polymer per pair: **198 g** against 466 g for the baseline
(both with the same midsole shape). Total polymer per pair: 460 g against 484 g.
LC-1 is still a plastic shoe; less of the plastic is virgin.

## 3. How it goes together

1. Mould the sole unit in one tool: inject the TPU skin and rim, then fill the
   cavity with eTPU beads and fuse them with steam (eTPU bonds to TPU in the mould;
   no primer or cement).
2. Cut and sew the upper from recycled-PET mesh with a spacer-fabric collar; sew
   the strobel sock to the lasting edge, leaving a 10 mm flange outside the seam;
   slip the thermoformed heel counter into its pocket.
3. Last the upper. Turn the flange outward over the rim and lockstitch through
   flange and rim (about 3 stitches per cm; two rows at the heel).
4. Lace. Insert the sockliner.
Disassembly: cut the stitch rows; the upper lifts off. A replacement sole unit is
stitched on through the same holes in the flange.

## 4. Why each choice, and what it beat

| Choice | Rejected alternatives | Reason |
|---|---|---|
| Expanded TPU midsole | EVA (baseline); sugarcane bio-EVA; PEBA; printed TPU lattice; cork | eTPU kept 54 % of its absorbed energy after 200,000 compression cycles against 21-32 % for filled EVA and 28 % for PEBA (Aimar et al. 2024), and returns 75.9 % of impact energy against 65.5 % for an EVA trainer (Hoogkamer et al. 2018). It is thermoplastic and fuses to a TPU skin without glue. **Cost: it is the largest single source of LC-1's emissions (0.75 kg CO2e per pair at the central values, against 0.55 for the baseline's EVA midsole), and its durability earns nothing in the central accounting**, because shoes are assumed retired at the same distance. Bio-EVA's negative footprint rests on a biogenic credit (DECISIONS.md); PEBA degraded fastest in the same test; a printed lattice adds 11-80 kWh of print energy per kg (Gutowski et al. 2017) and has no fatigue data; agglomerated cork is 2.5-6 MPa stiff (Jardin 2015). |
| TPU outsole skin, 75 % recycled | Carbon rubber (SBR/BR/NR); natural rubber | One polymer family with the midsole, so no adhesive and one recycling stream. Moulded TPU loses 25-40 mm3 in ISO 4649 abrasion against 157 mm3 for a shoe-sole SBR, so a 1.5 mm skin outlasts a 3 mm rubber outsole in the wear model. Cost: wet grip is unproven (section 6). |
| Stitchdown through a TPU rim | Solvent PU cement (baseline); lace loops and clips; heat-welded TPU film | Stitching is an existing, resoleable construction. The critic review (research/w2-05) ranked a clip-and-loop joint the most likely failure; welding cannot be undone by a cobbler. |
| Recycled-PET mesh, cut and sewn | Knit-to-shape upper; virgin polyester; wool; nylon | Recycled PET fibre 1.26 kg CO2e/kg against 3.19 virgin (Franklin Associates 2011, cut-off, plus the same fibre-processing step). Knit-to-shape avoids the 32 % cutting loss, but fully-fashioned knitting uses about 3 kWh/kg (JRC IMPRO 2014) against 0.26 for fabric knitting, which costs more than the recycled scrap it saves. Wool is about 21 kg CO2e/kg at the farm gate (Wiedemann et al. 2016). |
| Renewable electricity at assembly and the sole moulder | Grid power (Viet Nam 459 g CO2e/kWh, Ember 2025) | Final-assembly electricity per pair is the largest single swing in the model (tornado). The same change on the baseline shoe cuts 32 %: it is a factory decision as much as a design decision, and the results keep the two apart. |
| No shoebox | Shoebox | 158 g less board per pair. |

## 5. What is commercially available and what is not

All materials and processes in section 2 are sold today: eTPU bead foam and
steam-chest moulding, injection-moulded TPU, post-industrial recycled TPU grades,
recycled-PET mesh and spacer fabric, stitchdown construction, thermoformed
counters. Nothing is lab-only. What has not been done is this combination in a
running shoe. In-mould bonding of eTPU to a TPU skin is an industrial process but
its peel strength for this geometry is unknown; eTPU midsoles are usually made
denser than 200 kg/m3 (Aimar's sample: 240), and the fatigue data are for 240.

## 6. Known weaknesses (research/w2-05-critic.md, research/v-02-fea-check.md)

- Wet grip of a TPU outsole: no open data; likely worse than rubber. Test before
  running on wet roads (BUILD.md test 5).
- Softer underfoot: under a running heel load the simulated eTPU stack deflects
  about 1.6 times as much as the EVA stack (absolute values are not reliable;
  the ratio is). Stability and feel need a physical test.
- Stitch rim under running shear: the most likely point of failure. Pull and
  cyclic tests are in BUILD.md.
- No operating post-consumer recycling route for a TPU sole unit is open to an
  individual today (research/w2-06). The sole is designed for one; the route does
  not exist yet.
- How long the upper lasts is unknown, and the 50 % target is reached only if it
  outlasts one sole unit.
