# Battery revenue on ERCOT's real prices

The code behind andrewsilvestri.com/storage.html: a battery that trades energy on
ERCOT's hub and load-zone prices, every year from 2011, with perfect foresight, and
what that says about when a battery makes its money.

Every figure the page prints is in `outputs/payload.json`, written by
`build_storage.py`. This README carries no numbers of its own, so it cannot go
stale against them.

## Run it

    python fetch_ercot.py        # ERCOT's yearly DAM and RTM files into data/raw/ (~230 MB), recorded in data/fetched.json
    python build_storage.py      # every year, 1/2/4/8 h, hub average; zones; the EIA ICE check -> outputs/payload.json (~20 min)
    python update_page.py        # what the page would say (--apply writes ../site/storage.html inside the site's repo)
    python test_storage.py       # the checks; --break NAME puts each one's fault back and must exit 1

Python 3.12 with numpy, pandas, openpyxl, xlrd and pulp (CBC).

## The pieces

| File | What it is |
|---|---|
| `fetch_ercot.py`, `netfetch.py` | Downloads ERCOT MIS reports 13060 (Historical DAM Load Zone and Hub Prices) and 13061 (Historical RTM Load Zone and Hub Prices), one zip a year, and records URL, date, bytes and SHA-1. ERCOT replaces the current year's file in place; the listing is read each run. |
| `ercot_prices.py` | Reads a year: rows in delivery order, daylight-saving days of 23 and 25 hours checked against Central time, footer rows skipped, a missing 15-minute interval filled from its hour (at most four a year, listed). Caches each year by the zip's SHA-1 in `data/cache/`. |
| `model.py` | `optimize()`: the dispatch. Perfect foresight over 30-day windows with the charge carried across, round trip split as the square root per leg, a cycling cost per MWh charged and discharged, and a binary per hour so the battery never charges and discharges at once. Also the NREL ATB 2024 cost reference. Its `main()` still runs the old synthetic price year, which only `test_storage.py` uses. |
| `build_storage.py` | The payload: per year and market, the ceilings for 1, 2, 4 and 8 hours, the 4-hour battery's daily profit, days for half, share from the best ten days; the 4-hour battery at every hub and zone for two years; ERCOT's day-ahead North hub against EIA's ICE trades for 2015 (`data/ice_electric-2015final.xls`). |
| `update_page.py`, `template.html` | The page. Every number comes from the payload or `data/imm.json` (the market monitor's quotes, and Figure 17's values read by eye, labelled so). `claims()` stops the build if the payload contradicts the page's words. |
| `test_storage.py` | Eight checks, seven with a break that must fail. |
| `julia/`, `octave/`, `storage_arbitrage.xlsx` | Ports of the dispatch (JuMP + HiGHS; Octave + glpk) and a workbook of the same arithmetic, from the synthetic-year version of this project; they do not read ERCOT's files. |

## What it is not

A ceiling, not a forecast: no real battery knows next month's prices. Energy only:
no reserve services, which is where ERCOT's batteries earned most of their money
before 2024. Hourly average prices at hubs and load zones, not 15-minute prices at a
battery's own node. An explainer, not investment advice.
