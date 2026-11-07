"""Readers for the lead page. Each reads a hash-checked raw file (netfetch.verified) or a tracked transcription
in data/, so no number on the page is typed.

s01()            McFarland et al. 2022, SI Dataset S01: one row per (calendar year, age, cohort, blood-lead band).
band_loss()      the IQ points the paper assigns to each band, parsed from the formulas in SI Dataset S03.
s03_population() the denominator the paper divides by for its per-person figure (S03).
epa_b1()         EPA ACE Indicator B1: median and 95th percentile blood lead, children aged 1-5, by survey period.
gasoline()       lead consumed by U.S. makers of gasoline antiknock additives, by year (data/gasoline_lead_myb.csv).
larsen_regions() Larsen and Sanchez-Triana 2023, Table 2: IQ points lost in 2019 by income group and region
                 (data/larsen2023_table2.csv, checked against the PDF by test_lead.py).
text(name)       a source's text, whitespace collapsed (PDF, XML or plain text).
"""
import csv
import re

import openpyxl
import pymupdf

from netfetch import HERE, verified

BANDS = ["0-4.9", "5-9.9", "10-14.9", "15-19.9", "20-24.9", "25-29.9", "30+"]
_cache = {}


def text(name):
    if name not in _cache:
        p, _ = verified(name)
        if name.endswith(".pdf"):
            t = " ".join(pg.get_text() for pg in pymupdf.open(p))
        else:
            t = p.read_bytes().decode("utf-8", errors="replace")
            if name.endswith(".xml"):
                t = re.sub(r"<[^>]+>", " ", t)
        t = t.replace("·", ".").replace("–", "-").replace("−", "-")
        _cache[name] = re.sub(r"\s+", " ", t).strip()
    return _cache[name]


def s01():
    """Rows of SI Dataset S01 as dicts: year, age, cohort, band, share, leadpop."""
    if "s01" not in _cache:
        p, _ = verified("pnas_sd01.xlsx")
        ws = openpyxl.load_workbook(p, read_only=True, data_only=True).worksheets[0]
        it = ws.iter_rows(values_only=True)
        head = next(it)
        assert head[:8] == ("YEAR", "AGE", "POPULATION", "COHORT", "condition", "estimate", "se", "leadpop"), head
        rows = []
        for r in it:
            if r[0] is None:
                continue
            band = r[4].split(" ")[0]
            assert band in BANDS, r[4]
            rows.append({"year": r[0], "age": r[1], "cohort": r[3], "band": band, "share": r[5], "leadpop": r[7]})
        _cache["s01"] = rows
    return _cache["s01"]


def _s03():
    p, _ = verified("pnas_sd03.xlsx")
    return list(openpyxl.load_workbook(p, read_only=True, data_only=False).worksheets[0].iter_rows(values_only=True))


def band_loss():
    """IQ points lost per person in each band, from S03's formulas: the 5-9.9 band is mid-point x slope, each
    later band adds 5 ug/dL x its slope. The 0-4.9 band is not in the sheet: the paper counts no loss there."""
    loss = {"0-4.9": 0.0}
    rows = _s03()
    start = next(i for i, r in enumerate(rows) if r[1] == "BLL Range") + 1
    prev = None
    for r in rows[start:start + 6]:
        band, f = str(r[1]), str(r[3])
        m = re.fullmatch(r"=(\d+(?:\.\d+)?)\*(\d+(?:\.\d+)?)", f)
        if m:
            v = float(m.group(1)) * float(m.group(2))
        else:
            m = re.fullmatch(r"=D\d+\+\((\d+)\*(\d+(?:\.\d+)?)\)", f)
            assert m and prev is not None, f
            v = prev + float(m.group(1)) * float(m.group(2))
        loss[band] = v
        prev = v
    assert list(loss) == BANDS, loss
    return loss


def s03_population():
    for r in _s03():
        for c in r:
            m = re.fullmatch(r"=H5/(\d+)", str(c))
            if m:
                return int(m.group(1))
    raise RuntimeError("S03: no per-person denominator")


def epa_b1():
    p, _ = verified("epa_ace_b1.xlsx")
    out = []
    for r in openpyxl.load_workbook(p, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True):
        if r[0] and re.match(r"\d{4}", str(r[0])) and isinstance(r[2], (int, float)):
            yrs = re.findall(r"\d{4}", str(r[0]))
            out.append({"period": "%s-%s" % (yrs[0], yrs[-1]), "start": int(yrs[0]), "end": int(yrs[-1]),
                        "p95": float(r[1]), "median": float(r[2])})
    return sorted(out, key=lambda d: d["start"])


def _csv(name):
    with open(HERE / "data" / name, encoding="utf-8") as f:
        return list(csv.DictReader(r for r in f if not r.startswith("#")))


def gasoline():
    return [{"year": int(r["year"]), "tonnes": float(r["tonnes"]), "row": r} for r in _csv("gasoline_lead_myb.csv")]


def larsen_regions():
    out = []
    for r in _csv("larsen2023_table2.csv"):
        out.append({"group": r["group"], "name": r["name"], "iq_m": float(r["iq_points_lost_million"]),
                    "lo": float(r["iq_lo95"]), "hi": float(r["iq_hi95"]), "cost_pct_gdp": float(r["iq_cost_pct_gdp"])})
    return out
