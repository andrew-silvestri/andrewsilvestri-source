"""PHMSA gas distribution annual report data, 2010 to present (Form PHMSA F 7100.1-1).

Linked as "Gas Distribution Annual Data - 2010 to present (ZIP)" from
https://www.phmsa.dot.gov/data-and-statistics/pipeline/gas-distribution-gas-gathering-gas-transmission-hazardous-liquids
PHMSA collects lost and unaccounted-for gas for distribution operators only.

Writes data/raw/annual_gas_distribution_2010_present.zip and a row in
data/fetched.json. The site answers 403 to scripted clients; netfetch falls
back to a visible Chrome window.
Run:  python fetch_phmsa.py
"""
from netfetch import fetch

URL = ("https://www.phmsa.dot.gov/sites/phmsa.dot.gov/files/data_statistics/pipeline/"
       "annual_gas_distribution_2010_present.zip")

if __name__ == "__main__":
    fetch(URL, "annual_gas_distribution_2010_present.zip")
