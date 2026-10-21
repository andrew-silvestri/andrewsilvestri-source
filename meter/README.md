# What a meter's error is worth

The model behind andrewsilvestri.com/meter.html: orifice gas meters to ISO
5167-2 (Reader-Harris/Gallagher), a synthetic system of them, and Monte Carlo
propagation of their errors after JCGM 101:2008.

An explainer. It gives no engineering advice and states no uncertainty for
any real installation.

## Run it

Python 3.12 with numpy, matplotlib, Pillow, xlrd, openpyxl and `fluids`
(`python -m pip install fluids`), and a C++ compiler (g++) for NIST's code.

    python build_aga8.py            compile aga8/ (NIST GERG-2008, DETAIL, GROSS) to _build/
    python fetch_aga8_testdata.py   NIST's test workbooks, pinned to the vendored commit
    python fetch_henry_hub.py       EIA Henry Hub spot price, monthly (RNGWHHD)
    python fetch_eia_a1.py          EIA Natural Gas Annual, Table A1
    python fetch_phmsa.py           PHMSA gas distribution annual data (opens a Chrome window: the site refuses scripts)
    python checks/check_rhg.py      fluids against its documentation and an independent transcription
    python checks/check_z.py        the compiled NIST code against NIST's test points and tables
    python test_meter.py            the model's known-answer tests; --break NAME for each deliberate fault
    python build_meter.py           every case on the page, to outputs/payload.json (about 45 minutes)
    python fig_meter.py             the three figures, at 714 and 350 px
    python build_app.py             outputs/app_table.json and the simulator page
    python update_page.py --apply   the page

Every fetch records its URL, date and SHA-1 in data/fetched.json, and the
model refuses a raw file that does not match it. The raw data is not in this
archive.

## Files

- `model.py`: the meter equation, the error model, the system, JCGM 101 7.9.4.
- `aga8lib.py`: ctypes access to the compiled NIST code.
- `engine.js`: the browser port the simulator runs; tests/test_parity_meter.py
  in the site's repository holds it to the Python.
- `aga8/`: NIST's AGA8 C++ (github.com/usnistgov/AGA8), public domain under
  17 USC 105, unchanged except line endings; LICENSE and the commit beside it.

## Sources

Every default's source is in a comment beside it in `model.py` and in the
page's Sources list. The discharge coefficient's uncertainty is the ISO
5167-2 figure as quoted by a manufacturer's technical note, because the
standard is not openly published.
