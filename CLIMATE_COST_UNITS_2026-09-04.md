# Climate cost — the car delivery unit bug, and the sweep for its siblings — 2026-09-04

A separate change from the allocation showcase (`CLIMATE_COST_FIX_2026-09-04.md`),
kept apart so its effect on published numbers is its own line in the history.

## The bug

`climate-cost/data/processes.py`, the two car products' delivery stages. The
engine computes a freight leg as `ef [kg CO2e / tonne-km] × km / 1000 × mass`,
which is kilograms of CO2e when `mass` is in **kilograms**. The delivery stage
held `0.0007` (petrol) and `0.0008` (electric). The notes beside them said
"0.7 kg of vehicle moved" and "0.75 kg of vehicle per 100 km", i.e. 1400 kg ×
(100 km ÷ 200,000 km) = 0.7 kg. But 1400 × 0.0005 = 0.7, and the field held
0.0007 = 0.0005 × **1.4**: the vehicle mass had been typed in tonnes into a
field the engine reads in kilograms. The delivery leg was a thousandth of its
size. The electric car's value was also rounded (0.00075 → 0.0008).

It was invisible because it was also tiny in the right units (delivery is
under half a percent of a car's per-kilometre figure) and because, before the
field split, the number lived in a field called `allocation` alongside genuine
shares like 0.72, where 0.0007 looked like just another small fraction.

## The fix

`freight_kg=1400.0` and `freight_kg=1500.0`, with `amortise=0.0005` carried
separately (the lifetime slider rescales it). The notes now state the mass in
kilograms and record what the field used to hold and why.

| product | delivery leg before | after | total before | total after |
|---|---|---|---|---|
| Car, petrol, Germany → Texas | 0.0001 kg | 0.0972 kg | 23.474 | 23.571 (+0.41 %) |
| Car, battery electric, China → Texas | 0.0002 kg | 0.1481 kg | 12.664 | 12.812 (+1.17 %) |

Every other product is unchanged to 10⁻⁹ (`_audit-climate-cost/fix/after_units_fix.txt`).
Both cars remain inside their `test_lca.py` literature bands (15–30 and 6–20).
The published table on `climate-cost.html` now reads 23.57 and 12.81.

## The sweep for siblings

Every stage input and every process input, with its amount and the unit the
receiving process declares, is listed in `_audit-climate-cost/fix/unit_sweep.txt`
(153 stage inputs, 23 process inputs, 24 stage multipliers). Judged one by one
against "is this number in the unit the field is read as":

- **Transport as an input** (`road`, 240 km etc.): read as km × kg/1000 →
  tonne-km. Correct for the 1 kg food units it is used on.
- **Capital goods with amortisation** (`vehicle_glider` 1400 / 1500 / 12,000 /
  400,000 kg; `li_battery` 60 kWh; `aluminium` 42,000 / 180,000 kg): kilograms
  and kWh, multiplied by `amortise`. Correct. Lifetime defaults equal
  100 / amortise for all six vehicles (now asserted by `test_lca.py` §10).
- **Fuels** (`petrol` 7 L/100 km, bus `diesel` 2.9 L/100 pkm, `jet_fuel`
  3.4 / 2.5 kg/100 pkm, EV `home_kwh` 18 kWh, rail 4.4 kWh): all in the
  process's declared unit and at plausible magnitudes.
- **Farm inputs** (`field_n2o` and `ammonia` in kg N, `tillage` in
  hectare-seasons, `irrigation_kwh`, `pesticide` kg active, `diesel` litres):
  consistent; the N mass is the same number on the N₂O and ammonia edges, as
  it should be.
- **Clothing freight** (`freight_kg` 0.22 / 0.20 / 0.85 / 1.6 / 1.2 kg): in
  kilograms. Trainers at 1.6 kg a pair is heavy but the note says why.
- **`tyres_maint` and `road_infra`** on the bus (0.02 and 0.008 per
  "1,000 km") are per-passenger shares of bus-km, not slips.

Two things that are not unit slips but were found by the same reading. They
were first reported, not changed, because each moves a published number by a
modelling decision rather than a units correction; **both were then corrected
on instruction the same day** (see the follow-up in
`CLIMATE_COST_FIX_2026-09-04.md`: `gas_boiler` for the cheesemaking flame,
cheese +0.32 kg; `rail_infra` at UIC 2016's 6.5 g/pkm, train 0.56 → 1.00 kg
per 100 pkm — the road proxy had understated rail threefold):

1. **Cheesemaking burns gas with no combustion term.** `cheesemaking` takes
   `natgas_extraction` 0.12 kg gas with `direct=0.0`. Everywhere else the model
   burns gas it charges the combustion: coffee roasting has `direct=0.21` for
   0.075 kg (= 0.075 × 2.75), and `greenhouse_heat` is a separate process with
   2.75 kg CO2e per kg burned plus the extraction input. Cheesemaking charges
   only the extraction. If the gas is burned, 0.12 × 2.75 = 0.33 kg CO2e is
   missing from the cheese, +2.6 % on the showcase product. This needs a
   decision (is the 0.12 kg a boiler fuel or a feedstock?), not a silent fix.
2. **Rail track reuses `road_infra`** at 0.05 "thousand vehicle-km" per 100
   passenger-km, which is 150× the actual train-km. The note says rail
   infrastructure is heavier per kilometre, so the field is being used as
   "road-equivalent kilometres". Labelled as a judgement in the note; it should
   become its own process (`rail_infra`, per train-km) rather than a scaled
   borrowing.

## Guard

`test_lca.py` §10 now fails on: a legacy `allocation` field; a `share` outside
(0, 1]; a `share` without a `basis`; an `amortise` on a stage the lifetime
does not scale, or not equal to 100 / lifetime default; a `freight_kg` on a
non-transport stage, or outside 0.05–20,000 kg (the car delivery bug would
have been 1.4 and would have failed the floor).

**And the sweep itself now lives in `tests/test_units.py`**, not in anyone's
head: every stage input and every process input is checked against a
plausibility band for the unit its receiving process declares (211 checks),
with the bands three to four orders of magnitude wide so they catch a wrong
unit and never argue with a modelling choice. Run against the 2 August data
it fails on exactly the two car delivery stages; against the current data it
passes. A unit with no band is itself a failure, so a new process cannot
arrive unchecked.
