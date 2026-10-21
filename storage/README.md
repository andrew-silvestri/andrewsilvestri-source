# 03 — Storage Revenue Stack Simulator (ERCOT-style arbitrage)

This is **Model 1 from your two-year plan** (storage revenue stack simulator, baseline +
sensitivity framework), and it covers poster options #1 (ERCOT battery arbitrage
backtest) and #24 (2h vs 4h vs 8h duration value).

Perfect-foresight LP dispatch of a 1 MW battery against hourly prices, solved in monthly
chunks with SoC carry-over. Objective includes a cycling (degradation) cost per MWh of
throughput; efficiency split symmetrically (η = √RTE per leg).

## Headline results (synthetic price year, seed 42)

Net of the cycling cost, as `model.py` writes them to `outputs/summary.csv`;
rerun it and that file, not this table, is the record.

| Duration | Net revenue $/kW-yr | Equivalent cycles |
|---|---|---|
| 2h | 98.1 | 1361 |
| 4h | 107.1 | 786 |
| 8h | 111.0 | 424 |

Duration value flattens hard past 4h on energy arbitrage alone — the classic result; the
next revenue stack layers (AS, capacity-like payments) are the roadmap extension.

## Prices — important caveat

ercot.com is blocked from this sandbox, so the model generates a **documented synthetic
ERCOT-like year** (diurnal solar-belly + evening peak, summer scarcity spikes, 152
negative hours (1.7%); mean ≈ $40/MWh). The moment you drop a real ERCOT DAM CSV at
`data/prices.csv` (columns `timestamp,price_usd_mwh`), `model.py` uses it automatically.
Perfect foresight is an upper bound — real DAM bidding captures roughly 70–90%.

## Contents

| File | What it is |
|---|---|
| `model.py` | Verified reference (PuLP/CBC LP). Writes all figures, `outputs/dispatch_4h.csv`, summaries. |
| `storage_arbitrage.xlsx` | `Dispatch` (8760 hourly rows) + `Summary` (live SUMPRODUCT aggregation, 730-hour blocks as in fig5). `python sync_workbook.py` writes `outputs/dispatch_4h.csv` into it; `--check` exits 1 if it is behind. |
| `julia/model.jl` + `Project.toml` | **JuMP + HiGHS** port — the industry-standard stack for this model class. Untested in sandbox (Julia blocked); run locally. |
| `octave/model.m` | MATLAB/Octave port using built-in `glpk` (1-week demo window; set `ndays=365` for full year). |
| `outputs/` | fig1 price duration + diurnal shape · fig2 summer dispatch week · fig3 duration value · fig4 RTE×degradation sensitivity · fig5 monthly revenue · summary.csv |

## Next steps (per the two-year plan)

Add ancillary-service co-optimization (revenue stack layer 2), then a degradation model
(cycle-depth counting) feeding a cash-flow sheet — that's Model 2 (Fall 2026) done.
