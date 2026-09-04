# 01 — Industrial Heat Electrification Break-Even (Texas)

LCOH ($/MMBtu delivered) comparison of a resistive electric boiler vs a conventional
natural-gas boiler, per the locked scope in `industrialHeatingBEpointAbstractCreation.pdf`
(UT Energy Week packet) and the inputs doc `Industrial Heat Electrification for Process
Steam in Texas...`. This fills in the skeleton started in `industrialHeatingExcelMaster.xlsx`.

## Contents

| File | What it is |
|---|---|
| `model.py` | Reference implementation (verified, runnable). Writes all figures + `outputs/summary.csv/json`. |
| `lcoh_model.xlsx` | Formula-driven workbook: `Inputs` (yellow cells) → `Model` → `Sensitivity` break-even grid. Recalculates on edit; verified error-free. |
| `julia/model.jl` + `Project.toml` | Faithful Julia port. **Untested in this sandbox** (Julia's servers are off the network allowlist) — run locally: `julia --project=. model.jl`. Logic is line-for-line identical to `model.py`. |
| `octave/model.m` | MATLAB/GNU Octave port (Julia-adjacent alternative). Untested in sandbox (no root to install Octave); ported line-for-line from the verified `model.py`. `octave model.m`. |
| `outputs/` | fig1 break-even price curve · fig2 LCOH stacked bars · fig3 cost-gap contour (Pe×Pg) · fig4 tornado · fig5 emissions parity · summary.csv |
| `data/eia_price_template.csv` | Drop-in template for real EIA monthly series (couldn't fetch here — eia.gov blocked in sandbox). |

## Headline result (placeholder prices: Pe=6.5¢/kWh, Pg=$3.50/MMBtu)

- LCOH gas ≈ **$5.13/MMBtu**, LCOH electric ≈ **$20.00/MMBtu** → gap ≈ $14.86.
- Break-even electricity price ≈ **1.53 ¢/kWh** (full LCOH; 1.38 ¢ fuel-only). The spark
  gap dominates: capex/O&M shift the threshold by only ~0.15 ¢/kWh.
- Emissions parity requires grid CI ≤ **0.209 tCO₂/MWh**; at the ERCOT average
  of **0.333** (eGRID2023, 733.862 lb CO₂/MWh) the e-boiler emits 99.6 kg/MMBtu
  against the gas boiler's 62.4, so it emits more than gas. Marginal-emissions (Cambium) framing is the
  sensitivity to run next.

## Before poster use

1. Replace `P_e`, `P_g`, `grid_ci` with current EIA / eGRID values (links in the source
   doc's download list; sandbox couldn't reach eia.gov).
2. State boundary explicitly: retail all-in vs ERCOT wholesale energy-only.
3. Capex numbers are scaling placeholders (±50% sensitivity already included) — cite the
   LBNL IAC Tipsheet #3 range and dollar-year when finalizing.
