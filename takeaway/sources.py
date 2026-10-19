"""Readers for the raw files, each returning {(year, month): value}.

Every reader opens its file through netfetch.verified(), which re-hashes it
against data/fetched.json, so nothing reaches a payload from a file no fetch
script wrote (HANDOFF trap 18).

Units are converted here and named in the function: every series comes out in
billion cubic feet per day (Bcf/d), averaged over the calendar month.

What "Permian" means differs by source, and each reader says which:
- rrc_permian(): Texas only. The RRC's "PERMIAN BASIN" area, which its own
  page says is "best represented in Railroad Commission of Texas production
  figures as districts 7C, 08, and 8A". The workbook equals the sum of those
  three districts' Production Data Query totals to the Mcf (checked in
  STAGE1.md). Gas well gas plus casinghead gas as reported on Form PR, i.e.
  gross withdrawals at the lease, before lease use, flaring or processing.
- steo_permian(): EIA's Permian region, Texas and New Mexico, marketed gas
  (STEO Table 5a series NGMPPM). January of four years before the release to
  the forecast horizon; `history_only` cuts at the release's last historical
  month.
- dpr_permian(): EIA's Drilling Productivity Report Permian region (51 Texas
  and 4 New Mexico counties, listed in its RegionCounties sheet), total
  natural gas production, Jan 2007 to Jun 2024. The last report (May 2024)
  estimated its recent months; the last twelve are dropped (`DPR_LAST_ACTUAL`).
"""
import calendar
import datetime as dt

import openpyxl

from netfetch import verified

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# dpr-data.xlsx (Last-Modified 2024-05-13) runs to 2024-06. "The DPR model
# estimates recent historical production and short-term future production"
# (DPR methodology, Aug 2014, p.3), and neither the file nor the methodology
# says how many trailing months are model output. Drop the last twelve
# rather than guess the boundary.
DPR_LAST_ACTUAL = (2023, 6)


def days(ym):
    return calendar.monthrange(*ym)[1]


def rrc_permian(product="gas"):
    """Monthly RRC Permian (7C+08+8A) production in Bcf/d.

    product: "gas" (gas well + casinghead), "gw", "csgd". Months the workbook
    reports as 0 (not yet filed) are omitted.
    """
    path, _ = verified("permian-basin-2008-to-current.xlsx")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb["Sheet1"].iter_rows(values_only=True))
    head = next(i for i, r in enumerate(rows) if r[0] == "Production Totals by Month")
    cols = rows[head + 1]
    assert cols[5] == "PR Casinghead Production Volume (MCF)", cols
    assert cols[6] == "PR Gas Production Volume (MCF)", cols
    out = {}
    for r in rows[head + 2:]:
        if r[0] != "PERMIAN BASIN":
            continue
        ym = (int(r[1]), int(r[3]))
        csgd, gw = r[5], r[6]
        if not (csgd or gw):
            continue
        mcf = {"gas": csgd + gw, "gw": gw, "csgd": csgd}[product]
        out[ym] = mcf / days(ym) / 1e6
    return out


def _steo_row(sheet, code):
    path, _ = verified("STEO_m.xlsx")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    dates = list(wb["Dates"].iter_rows(values_only=True))
    lab = {r[0].strip(" -"): r[3] for r in dates if r and r[0]}
    y0, last = lab["Table Beginning Year"], lab["Last Historical Month"]
    rows = list(wb[sheet].iter_rows(values_only=True))
    assert rows[3][2] == "Jan", rows[3][:4]
    row = next(r for r in rows if r[0] == code)
    vals = [v for v in row[2:] if v is not None]
    out = {}
    for k, v in enumerate(vals):
        out[(y0 + k // 12, k % 12 + 1)] = float(v)
    return out, (last // 100, last % 100), lab["Forecast Month"]


def steo_permian(history_only=True):
    """EIA STEO Permian region marketed gas, Bcf/d (Table 5a, NGMPPM)."""
    s, last, _ = _steo_row("5atab", "NGMPPM")
    return {k: v for k, v in s.items() if not history_only or k <= last}


def steo_release():
    _, last, month = _steo_row("5atab", "NGMPPM")
    return month, last


def steo_formation(history_only=True):
    """EIA STEO Permian formations shale dry gas, Bcf/d (Table 10b, SNGPRPM). Geological."""
    s, last, _ = _steo_row("10btab", "SNGPRPM")
    return {k: v for k, v in s.items() if not history_only or k <= last}


def dpr_permian():
    """EIA DPR Permian region total natural gas, Bcf/d (sheet 'Permian Region', Mcf/d)."""
    path, _ = verified("dpr-data.xlsx")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb["Permian Region"].iter_rows(values_only=True))
    assert rows[0][5] == "Natural gas (Mcf/d)" and rows[1][7] == "Total production", rows[:2]
    out = {}
    for r in rows[2:]:
        if isinstance(r[0], dt.datetime) and r[7] is not None:
            ym = (r[0].year, r[0].month)
            if ym <= DPR_LAST_ACTUAL:
                out[ym] = r[7] / 1e6
    return out
