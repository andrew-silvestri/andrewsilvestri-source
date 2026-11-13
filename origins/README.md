# The gradient of life - code and data

Source for andrewsilvestri.com/origins.html. Python 3 with pandas, numpy and openpyxl.

## Run

    python fetch_public.py      # downloads the two databases into data/raw and checks their SHA-1
    python analyse_ashrae.py    # comfort votes -> outputs/ashrae_*.csv (1,000 bootstrap resamples, about 2 minutes)
    python marhys_lostcity.py data/raw/MARHYS_DB_3_0.xlsx data/lost_city_marhys3.csv
    python build_origins.py     # -> outputs/payload.json, with checks against the page's words
    python update_page.py       # renders the page (needs the site tree; --apply writes it)
    python test_origins.py

## Data

| File | Source | Licence |
|---|---|---|
| data/raw/db_measurements_v2.1.0.csv.gz, db_metadata.csv | ASHRAE Global Thermal Comfort Database II, v2.1.0, https://zenodo.org/records/4993952 (Foldvary Licina et al. 2018, Building and Environment 142:502-512) | CC BY 4.0 |
| data/raw/MARHYS_DB_3_0.xlsx | Diehl and Bach, MARHYS Database 3.0, https://doi.org/10.1594/PANGAEA.958978 | CC BY 4.0 |
| data/lost_city_marhys3.csv | the Lost City rows of MARHYS 3.0, cut by marhys_lostcity.py | CC BY 4.0 |
| data/timeline.csv | dated events, one source and URL per row | facts with citations |

The raw files are not in the archive; fetch_public.py names each URL and SHA-1. Downloaded 7 November 2026.

## What the numbers are

- Vent gradient: the median pH of Lost City raw-fluid and end-member samples against an early-ocean pH of 6.6
  (Krissansen-Totton et al. 2018), converted at RT ln10 / F millivolts per pH unit. An upper bound for an ideal
  barrier, not a measured potential.
- Comfort: indoor air temperature in 1 C bins with at least 200 votes; the balance point is where the shares
  wanting warmer and cooler cross; intervals resample whole buildings.
- Membrane voltages (LADDER in build_origins.py): each row names its paper or BioNumbers entry.
