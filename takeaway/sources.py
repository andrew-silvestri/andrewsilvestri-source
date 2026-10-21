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
import html
import re

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


PDQ_DISTRICTS = ("7C", "08", "8A")
PDQ_SPANS = ("2008", "2023")


def pdq_district(d):
    """One district's PDQ web monthly totals, Mcf/month: {(y, m): (csgd, gw)}.

    Columns as the page prints them: Date, Oil (BBL), Casinghead (MCF),
    GW Gas (MCF), Condensate (BBL). Cells are parsed from the result table's
    rows, whose first cell is a month and year.
    """
    out = {}
    for y0 in PDQ_SPANS:
        path, _ = verified(f"pdq_{d}_{y0}.html")
        t = path.read_text(encoding="utf-8")
        head = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
        assert "Date Oil (BBL) Casinghead (MCF) GW Gas (MCF) Condensate (BBL)" in head, path
        n = int(re.search(r"(\d+) results", head).group(1))
        got = 0
        for tr in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", t):
            cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", c))).strip()
                     for c in re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)]
            if len(cells) == 5 and re.fullmatch(r"[A-Z][a-z]{2} \d{4}", cells[0]):
                mon, yr = cells[0].split()
                out[(int(yr), MONTHS.index(mon) + 1)] = (int(cells[2]), int(cells[3]))
                got += 1
        assert got == n, f"{path.name}: page says {n} results, parsed {got}"
    return out


def _eia_annual(name, year):
    """One year's row of an EIA dnav annual workbook, as {sourcekey: value}."""
    import xlrd
    path, _ = verified(name)
    sh = xlrd.open_workbook(path).sheet_by_name("Data 1")
    keys = [sh.cell_value(1, c) for c in range(sh.ncols)]
    for r in range(3, sh.nrows):
        if xlrd.xldate_as_datetime(sh.cell_value(r, 0), 0).year == year:
            return {k: sh.cell_value(r, c) for c, k in enumerate(keys) if c}
    raise KeyError(f"{name}: no row for {year}")


def residue_share(year):
    """EIA's statewide ratios standing in for the Permian's k (PLAN 3.2), for one year.

    Returns, for "TX", "NM" and "both": dry / marketed, and (dry - lease fuel -
    plant fuel) / marketed. Series: marketed N9050xx2, dry NA1160_Sxx_2, lease
    fuel NA1840_Sxx_2, plant fuel NA1850_Sxx_2, all MMcf.
    """
    raw = {}
    for st, code in (("TX", "STX"), ("NM", "SNM")):
        p = _eia_annual(f"NG_PROD_SUM_DC_{code}_MMCF_A.xls", year)
        c = _eia_annual(f"NG_CONS_SUM_DCU_{code}_A.xls", year)
        raw[st] = {"marketed": p[f"N9050{st}2"], "dry": p[f"NA1160_{code}_2"],
                   "lease": c[f"NA1840_{code}_2"], "plant": c[f"NA1850_{code}_2"]}
    raw["both"] = {k: raw["TX"][k] + raw["NM"][k] for k in raw["TX"]}
    out = {}
    for st, v in raw.items():
        out[st] = {"dry": v["dry"] / v["marketed"],
                   "net": (v["dry"] - v["lease"] - v["plant"]) / v["marketed"], "raw": v}
    return out


def rrc_permian_mcf():
    """The RRC workbook's monthly cells as filed, Mcf/month: {(y, m): (csgd, gw)}."""
    path, _ = verified("permian-basin-2008-to-current.xlsx")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb["Sheet1"].iter_rows(values_only=True))
    head = next(i for i, r in enumerate(rows) if r[0] == "Production Totals by Month")
    return {(int(r[1]), int(r[3])): (r[5], r[6]) for r in rows[head + 2:]
            if r[0] == "PERMIAN BASIN" and (r[5] or r[6])}


def eia_vented_flared(state_code, years):
    """EIA annual vented and flared (N9040xx2) and gross withdrawals (N9010xx2), MMcf."""
    st = state_code[1:]
    return {y: (_eia_annual(f"NG_PROD_SUM_DC_{state_code}_MMCF_A.xls", y)[f"N9040{st}2"],
                _eia_annual(f"NG_PROD_SUM_DC_{state_code}_MMCF_A.xls", y)[f"N9010{st}2"]) for y in years}


def eia_vented_flared_monthly(state_code):
    """EIA monthly vented and flared and gross withdrawals, MMcf/month:
    {(y, m): (vented_flared, gross)}, months where both are filled."""
    import xlrd
    path, _ = verified(f"NG_PROD_SUM_DC_{state_code}_MMCF_M.xls")
    sh = xlrd.open_workbook(path).sheet_by_name("Data 1")
    st = state_code[1:]
    keys = [sh.cell_value(1, c) for c in range(sh.ncols)]
    cv, cg = keys.index(f"N9040{st}2"), keys.index(f"N9010{st}2")
    out = {}
    for r in range(3, sh.nrows):
        v, g = sh.cell_value(r, cv), sh.cell_value(r, cg)
        if v != "" and g != "":
            d = xlrd.xldate_as_datetime(sh.cell_value(r, 0), 0)
            out[(d.year, d.month)] = (float(v), float(g))
    return out


PDQ_CODES = {"7C": "09", "08": "10", "8A": "11"}   # the dump's DISTRICT_NO for each name
PDQ_UNSETTLED = 6                                   # PLAN 3.5: the last six months still fill in


def pdq_reduced():
    """data/pdq_district_month.csv (pdq_dump.py), after re-hashing it against its meta file.
    Returns (meta, rows as dicts)."""
    import csv
    import hashlib
    import json
    from pathlib import Path
    d = Path(__file__).resolve().parent / "data"
    meta = json.loads((d / "pdq_district_month.json").read_text(encoding="utf-8"))
    raw = (d / "pdq_district_month.csv").read_bytes()
    got = hashlib.sha1(raw).hexdigest()
    if got != meta["csv_sha1"]:
        raise RuntimeError(f"pdq_district_month.csv sha1 {got} != {meta['csv_sha1']}: rerun pdq_dump.py")
    return meta, list(csv.DictReader(raw.decode("utf-8").splitlines()))


def rrc_vented_flared():
    """Monthly vented or flared (disposition code 4) and production, the three Permian
    districts summed, Mcf/month: {(y, m): (vented_flared, produced)}. The last
    PDQ_UNSETTLED cycle months before the dump's newest are dropped."""
    meta, rows = pdq_reduced()
    codes = set(PDQ_CODES.values())
    ny = meta["dump"]["newest_prod_cycle"]
    n = int(ny[:4]) * 12 + int(ny[4:]) - 1 - PDQ_UNSETTLED
    last = (n // 12, n % 12 + 1)
    out = {}
    for r in rows:
        if r["district_no"] not in codes:
            continue
        ym = (int(r["cycle_year_month"][:4]), int(r["cycle_year_month"][4:]))
        if ym > last:
            continue
        v, g = out.get(ym, (0, 0))
        out[ym] = (v + int(r["vf_gas_mcf"]) + int(r["vf_csgd_mcf"]),
                   g + int(r["prod_gas_mcf"]) + int(r["prod_csgd_mcf"]))
    return {k: v for k, v in out.items() if v[1] > 0}


def dpr_region_counties():
    """Counties in EIA's Permian region by state, from dpr-data.xlsx RegionCounties."""
    path, _ = verified("dpr-data.xlsx")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb["RegionCounties"].iter_rows(values_only=True))
    assert rows[0][:5] == ("State", "County", "StateID", "CountyID", "Region"), rows[0]
    out = {}
    for r in rows[1:]:
        if r and r[4] and "Permian" in str(r[4]):
            out.setdefault(r[0], []).append(r[1])
    return out
