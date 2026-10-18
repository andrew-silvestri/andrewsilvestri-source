"""Henry Hub natural gas spot price, monthly, from EIA.

Series RNGWHHD, monthly frequency (dollars per million Btu), from EIA's
natural gas price pages: https://www.eia.gov/dnav/ng/hist/rngwhhdm.htm
EIA data are public domain with attribution (https://www.eia.gov/about/copyrights_reuse.php).

Writes data/raw/RNGWHHDm.xls and a row in data/fetched.json.
Run:  python fetch_henry_hub.py
"""
from netfetch import fetch

URL = "https://www.eia.gov/dnav/ng/hist_xls/RNGWHHDm.xls"

if __name__ == "__main__":
    fetch(URL, "RNGWHHDm.xls")
