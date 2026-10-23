"""Readers for the lost-gas page. Each reads a hash-checked raw file (netfetch.verified).

phmsa_reports()  every gas distribution annual report 2010-2025 that carries a percent unaccounted
                 for, as dicts: year, operator_id, operator_name (as PHMSA publishes it), state (STOP,
                 the state of operation; NOT OFFICE_ADDRESS_STATE, which is where the office is),
                 commodity, operator_type, services, lauf (%).
natural_gas(r)   whether a report is a natural gas system. COMMODITY exists from 2015; before that
                 every report is kept and the page says so.
eia_a1(year)     EIA Natural Gas Annual Table A1 rows for Texas, Oklahoma and the U.S. total.
quote(name, needle, span)  the text around a phrase in one of the opened documents, so a quotation
                 on the page is read from the source file rather than typed.
"""
import io
import json
import re
import zipfile

import openpyxl
from pypdf import PdfReader

from netfetch import verified

ZIP = "annual_gas_distribution_2010_present.zip"
YEARS = range(2010, 2026)


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def phmsa_reports():
    """Read once per zip: the parsed rows are cached beside the raw file under the zip's SHA-1,
    which verified() has just recomputed from the bytes, so a changed zip is always re-read."""
    path, row = verified(ZIP)
    cache = path.parent.parent / f"_cache_reports_{row['sha1'][:12]}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    out = _read_reports(path)
    cache.write_text(json.dumps(out), encoding="utf-8")
    return out


def _read_reports(path):
    z = zipfile.ZipFile(path)
    out = []
    for year in YEARS:
        ws = openpyxl.load_workbook(io.BytesIO(z.read(f"annual_gas_distribution_{year}.xlsx")),
                                    read_only=True).worksheets[0]
        it = ws.iter_rows(values_only=True)
        for r in it:                       # two note rows precede the header
            if r and r[0] == "DATAFILE_AS_OF":
                hdr = list(r)
                break
        else:
            raise RuntimeError(f"{year}: no header row")
        for r in it:
            d = dict(zip(hdr, r))
            lauf = _num(d.get("PERCENT_UNACC_GAS"))
            if lauf is None:
                continue
            out.append({"year": year, "operator_id": d.get("OPERATOR_ID"),
                        "operator_name": d.get("OPERATOR_NAME"), "state": d.get("STOP"),
                        "commodity": d.get("COMMODITY"), "operator_type": d.get("OPERATOR_TYPE"),
                        "services": _num(d.get("NUM_SRVS_PART_B3_TOTAL")), "lauf": float(lauf)})
    return out


def natural_gas(r):
    c = r["commodity"]
    return c is None if r["year"] < 2015 else (c or "").replace("OTHER GAS: ", "").strip() == "Natural Gas"


def _text(name):
    path, _ = verified(name)
    t = "\n".join(p.extract_text() or "" for p in PdfReader(path).pages)
    # EIA's archive editions use no-break spaces, U+2010/U+2212 for minus and print the
    # minus apart from its number (2022-2023); without this their rows do not match
    t = re.sub(r"[   �]", " ", t).replace("‐", "-").replace("−", "-")
    return re.sub(r"-\s+(?=\d)", "-", t)


def eia_a1(year):
    t = _text(f"eia_a1_{year}.pdf")
    if not re.search(rf"Table A1\.[^\n]*{year}", t):
        raise RuntimeError(f"eia_a1_{year}.pdf is not the {year} Table A1")
    num = r"(-?[\d,]+)"
    out = {}
    for name in ("Texas", "Oklahoma", "Total"):
        m = re.search(rf"(?m)^\s*{name}\s+{num}\s+{num}\s+{num}\s+(-?[\d.]+|<)", t)
        if not m:
            raise RuntimeError(f"Table A1 {year}: no {name} row")
        loss, uaf, cons = (float(m.group(i).replace(",", "")) for i in (1, 2, 3))
        out[name] = {"losses_mmcf": loss, "uaf_mmcf": uaf, "consumption_mmcf": cons,
                     "printed_pct": m.group(4), "pct": 100 * (loss + uaf) / cons}
    return out


def quote(name, needle, span=400):
    t = re.sub(r"\s+", " ", _text(name))
    i = t.find(needle)
    if i < 0:
        raise RuntimeError(f"{name}: phrase not found: {needle!r}")
    return t[i:i + span]


def data_as_of():
    """PHMSA's own as-of date for the newest year's file (its DATAFILE_AS_OF column), ISO."""
    path, _ = verified(ZIP)
    ws = openpyxl.load_workbook(io.BytesIO(zipfile.ZipFile(path).read(f"annual_gas_distribution_{YEARS[-1]}.xlsx")),
                                read_only=True).worksheets[0]
    it = ws.iter_rows(values_only=True)
    for r in it:
        if r and r[0] == "DATAFILE_AS_OF":
            break
    v = next(it)[0]
    return v.date().isoformat() if hasattr(v, "date") else str(v)
