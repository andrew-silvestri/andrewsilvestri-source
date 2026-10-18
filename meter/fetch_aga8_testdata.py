"""NIST AGA8 test workbooks, pinned to the commit the vendored code came from.

checks/check_z.py reads `Test Data.xls` (P at T, d for ~200 gases, GERG-2008
and DETAIL) and `Tables.xls` (the five AGA8 example gases). Public domain
(github.com/usnistgov/AGA8, LICENSE in aga8/). Fetched rather than committed:
3.5 MB of binary the model itself never reads.

Writes data/raw/aga8_test_data.xls, data/raw/aga8_tables.xls and rows in
data/fetched.json.
Run:  python fetch_aga8_testdata.py
"""
from pathlib import Path

from netfetch import fetch

COMMIT = (Path(__file__).resolve().parent / "aga8" / "NIST_COMMIT.txt").read_text().split()[0]
BASE = f"https://raw.githubusercontent.com/usnistgov/AGA8/{COMMIT}/TESTDATA/"

if __name__ == "__main__":
    fetch(BASE + "Test%20Data.xls", "aga8_test_data.xls")
    fetch(BASE + "Tables.xls", "aga8_tables.xls")
