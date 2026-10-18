"""EIA Natural Gas Annual, Table A1: losses and unaccounted for, by state.

https://www.eia.gov/naturalgas/annual/pdf/table_a01.pdf (public domain with
attribution). Read for what it measures, not as a meter figure: it is a
supply-disposition balance item, which carries every reason supply and
disposition fail to agree, metering among them.

Writes data/raw/eia_nga_table_a01.pdf and a row in data/fetched.json.
Run:  python fetch_eia_a1.py
"""
from netfetch import fetch

URL = "https://www.eia.gov/naturalgas/annual/pdf/table_a01.pdf"

if __name__ == "__main__":
    fetch(URL, "eia_nga_table_a01.pdf")
