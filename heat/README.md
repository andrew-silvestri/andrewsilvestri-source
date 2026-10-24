# Industrial heat break-even (Texas)

The code behind andrewsilvestri.com/heat.html: a resistive electric boiler against a natural-gas
boiler for process heat, on EIA's monthly Texas industrial prices since 2001, and a second,
flexible electric boiler on ERCOT's hourly real-time prices since 2011.

Every figure the page prints is in `outputs/payload.json`, written by `build_heat.py`. This README
carries no numbers of its own.

The model's scope was first set for a UT Energy Week poster; its inputs are now each taken from a
public source, listed in `data/sources.json` and on the page.

## Run it

    python fetch_eia.py      # EIA API v2 (needs EIA_API_KEY in the environment; the key is never written) -> data/raw/
    python build_heat.py     # -> outputs/payload.json; the flexible case also reads ERCOT's files in ../storage/data/raw
    python update_page.py    # what the page would say (--apply writes ../site/heat.html inside the site's repo)
    python test_heat.py      # the checks; --break NAME puts each one's fault back and must exit 1

## The pieces

| File | What it is |
|---|---|
| `fetch_eia.py` | Texas industrial electricity price (retail sales), Texas industrial gas price (N3035TX3) and Texas heat content of deliveries, recorded in `data/fetched.json` without the key. |
| `model.py` | `lcoh()` and `breakeven_Pe()`: levelised cost of heat for each boiler (fuel over efficiency, capital recovery, fixed operations) and the electricity price at which they are equal. Its `main()` still draws the old example figures into `outputs/`; the page does not use them. |
| `build_heat.py` | The payload: the break-even every month against what industry paid; the same at a 70% gas efficiency; the flexible second boiler by year at low, central and high delivery charges; emissions at the average and marginal grid rates. |
| `update_page.py`, `template.html` | The page; `claims()` stops the build if the payload contradicts its words. |
| `test_heat.py` | The checks, each with a break that must fail. |
| `lcoh_model.xlsx`, `julia/`, `octave/` | The same levelised-cost arithmetic as a formula workbook and as Julia and Octave ports, at the model's example prices. |

An explainer and teaching tool, not a design study or an investment case.
