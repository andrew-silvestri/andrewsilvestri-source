# Building and testing an LC-1 test article at home

This builds a TEST ARTICLE of LC-1: same shape, same construction (a TPU sole
unit with a stitch rim, a polyester upper stitched through it, no glue), but with
a 3-D printed TPU lattice in place of the moulded expanded-TPU midsole. It tests
fit, cushioning, grip and the stitch joint. It does not test the carbon claim
(RESULTS.md: printing adds 2-16 kg CO2e per pair).

Nothing here was ordered or priced by contacting anyone. Prices are what public
pages showed on 2026-11-07 (research/w2-07-build-sourcing.md); check them.

## Safety first

- A home-made shoe has had no quality check. Walk in it before you run in it; run
  first on a track or treadmill, short distances, dry surfaces.
- TPU outsoles can be slippery on wet surfaces (DESIGN.md section 6). Do not run on
  wet roads, metal covers, painted lines or tiles until test 5 says the grip is
  acceptable.
- Changing shoe type abruptly raises injury risk: a 2026 meta-analysis of
  transitions to minimalist shoes found a moderate rise in injury risk and suggested
  at least 12 weeks of graded transition (PMID 42612386). Build mileage gradually.
- Stop using the shoe if the stitching loosens, the rim cracks, or a lattice strut
  breaks under the heel.
- Print TPU in a ventilated room. Dry the filament before printing.

## 1. What to print, and on what

| Part | File | Material | Settings |
|---|---|---|---|
| Sole unit (midsole + rim + outsole skin) | `cad/out/lc1_midsole.stl`, `lc1_rim.stl`, `lc1_outsole.stl` (print as one body; merge in the slicer) | TPU 95A filament | direct-drive extruder; 220-240 C nozzle, 50-60 C bed (Prusa's TPU guidance); 20-30 mm/s; dry the filament first |
| Heel counter (optional) | cut from 1.0-1.5 mm TPU sheet using the pattern | | |

- **Midsole as infill.** Print the midsole envelope with 3 perimeters, a solid
  2 mm skin at the bottom (this is the outsole skin and tread), 3 solid layers on
  top, and gyroid infill inside. The infill percentage is the lattice relative
  density: the model (RESULTS.md) puts the match to an EVA trainer at 28-45 %;
  find it with test 2 before printing a full sole.
- **Bed size.** The sole is 283 mm long (US 9). It does not fit 250 x 210 or
  250 x 220 mm beds at any angle (research/w2-07); use a 300 x 300 mm printer
  (e.g. Prusa CORE One L, listed at 300 x 300 mm) or split the sole at the arch into
  two halves and join them with a TPU-welded seam (a soldering iron at 220-240 C).
- **Filament.** TPU 95A: NinjaTek Cheetah 95A (580 % elongation, USD 106/kg),
  MatterHackers MH Build TPU (USD 34/kg); recycled: FormFutura ReForm rTPU 95A
  (1.21 g/cm3, 32 MPa, 355 % elongation, EUR 24.75/kg, listed as not available on
  2026-11-07). One pair needs about 0.5-0.6 kg.
- **Print service** if you have no large printer: JLC3DP prints TPU 95A by FDM
  from USD 3 per part with a 250 mm maximum (split the sole).

## 2. Tools and materials

Upper: about 0.5 m of polyester fabric (a stretch knit or a 3-D spacer mesh; a
recycled-polyester fabric if you can find one), the pattern printed 1:1 from
`cad/out/lc1_upper_pattern.svg`, a lasting form (a printed or second-hand shoe last
in US 9, or your own old shoe stuffed firm), bonded polyester thread (size 69 or
heavier), a stitching awl or two harness needles, a 1.5 mm drill bit, binder clips,
a sewing machine for the upper seams, laces. Testing: a kitchen scale (0.1 g), a
ruler and a tread-depth gauge, a smartphone with phyphox (free, open source) for
acceleration, an 8-9 kg mass (a dumbbell or a bag of sand), a bathroom scale.

## 3. Build

1. **Print test coupons first.** Print five 60 x 60 mm heel blocks, 30 mm tall, at
   20, 25, 30, 35 and 40 % gyroid infill, with the same skin settings. Weigh each.
2. **Choose the infill (test 2 below).** Pick the coupon whose drop peak is closest
   to the heel of a worn-in EVA trainer you own.
3. **Print the sole unit** at that infill. Weigh it. Drill the stitch holes: one
   row, 4 mm below the top edge of the rim, 3.5 mm apart (about 3 per cm),
   1.5 mm diameter. Add a second row 3 mm lower round the heel.
4. **Cut and fit the upper.** Cut the wrap piece and tongue in scrap cloth first;
   pin it round the last; mark where it gaps or bunches (the toe will need two
   small darts); correct the paper pattern; then cut the real fabric with the
   10 mm flange.
5. **Sew the upper.** Close the centre-back heel seam. Sew the tongue in. Sew the
   strobel sock (pattern piece 1) to the lower edge, leaving the 10 mm flange
   free outside the seam. Slide the heel counter into a pocket sewn inside the heel.
6. **Last and stitch down.** Put the upper on the last, set it on the sole unit,
   turn the flange outward over the rim, clip it, and saddle-stitch through the
   flange and the rim holes with two needles. Pull each stitch firm, not tight
   enough to cut the TPU. Lock the ends with three back-stitches.
7. **Lace, insert a sockliner (a 4 mm spacer mesh or your old insole), weigh the
   finished shoe.** Record everything in the log.
To take it apart: cut the thread on the flange and pull it out.

## 4. Cheap physical tests

Record date, distance, surface and mass in a log for every run.

| # | Test | How | Pass mark |
|---|---|---|---|
| 1 | Mass | kitchen scale | at most 300 g per shoe (the printed version will be heavier; record it) |
| 2 | Drop (ASTM F1976-like, NOT the standard) | tape the phone flat to the top of the 8.5 kg mass; drop it from 60 mm (5 J) onto the heel of the shoe on a concrete floor, guided by a tube; read peak acceleration in phyphox (use the highest sample rate the phone offers; a phone may sample too slowly to catch the true peak, so compare shoes, do not trust the absolute g); 5 drops per shoe | within 15 % of your EVA trainer on the same rig |
| 3 | Compression | stand on one heel on a bathroom scale with the shoe on a hard floor; measure the midsole thickness with a ruler at rest and loaded | record mm per 100 N; compare with the EVA trainer |
| 4 | Stitch pull | hang the 8.5 kg mass from the heel loop with the sole clamped; then rock the shoe sideways 200 times by hand | no stitch pull-through, no rim crack |
| 5 | Grip | stand on a tilting board (painted plywood) dry and wet; raise until the shoe slips; read the angle with the phone's inclinometer | not lower than your rubber-soled trainer; never run wet if lower |
| 6 | Wear log | weigh the shoe and measure tread depth at the forefoot hot spot every 50 km | compare with 0.14 mm per 100 km for rubber outsoles (Ohno et al. 2024) |
| 7 | Upper | inspect the flange and the stitch line every 50 km | no fabric tearing at the stitch line |

Send nothing anywhere; keep the log with the shoe. If the stitch joint passes 300 km
and the grip test passes, the construction has shown what the simulation cannot.
