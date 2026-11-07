"""Readers for the oxygen page. Each reads a hash-checked raw file (netfetch.verified), so no number on the
page is typed: volumes are read out of EIA's and USDA's own files, the state bans out of EPA's table, and
every figure quoted from a report is matched in that report's text at build or render time.

mtbe_monthly()      refinery and blender net input of MTBE, US, {YYYY-MM: thousand barrels a day}.
ethanol_monthly()   fuel ethanol consumption, US (MER Table 10.3), {YYYY-MM: thousand barrels a day}.
ethanol_annual()    the same, {YYYY: thousand barrels a day}, from MER's annual rows.
gasoline_annual()   finished motor gasoline product supplied, {YYYY: thousand barrels a day}.
rfg_annual()        reformulated gasoline product supplied, {YYYY: thousand barrels a day}.
corn()              {marketing year: (production, fuel alcohol use)}, million bushels (ERS Tables 4 and 31).
state_bans()        [(state, phaseout date ISO, complete?)] from EPA420-B-07-013.
rfs_volumes()       {year: billion gallons} from EPAct 2005 section 1501's table.
flat(name)          a source's text, whitespace collapsed.
quote(name, p)      the match of a regular expression in a source; raises if absent.
"""
import calendar
import csv
import datetime as dt
import html
import re

import pymupdf
import xlrd

from netfetch import verified

_cache = {}


def flat(name):
    if name not in _cache:
        p, _ = verified(name)
        if name.endswith(".pdf"):
            t = " ".join(pg.get_text() for pg in pymupdf.open(p))
        else:
            b = p.read_bytes()
            try:
                t = b.decode("utf-8")
            except UnicodeDecodeError:
                t = b.decode("cp1252")
            t = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", t, flags=re.S)
            t = html.unescape(re.sub(r"<[^>]+>", " ", t))
        t = t.replace("﻿", "").replace("’", "'").replace("­", "")
        _cache[name] = re.sub(r"\s+", " ", t).strip()
    return _cache[name]


def quote(name, pattern):
    m = re.search(pattern, flat(name))
    if not m:
        raise LookupError(f"{name}: no match for {pattern!r}")
    return m


def _xls(name):
    p, _ = verified(name)
    s = xlrd.open_workbook(p).sheet_by_name("Data 1")
    out = {}
    for i in range(3, s.nrows):
        d, v = s.row_values(i)[:2]
        if v == "" or d == "":
            continue
        y, m, _d, *_ = xlrd.xldate_as_tuple(d, 0)
        out[(y, m)] = float(v)
    return out


def mtbe_monthly():
    """Thousand barrels in the month, divided by the days in it."""
    return {f"{y}-{m:02d}": v / calendar.monthrange(y, m)[1] for (y, m), v in _xls("eia_mtbe_net_input_m.xls").items()}


def _mer(msn):
    p, _ = verified("eia_mer_t1003.csv")
    rows = [r for r in csv.DictReader(open(p, encoding="utf-8-sig")) if r["MSN"] == msn]
    return {r["YYYYMM"]: float(r["Value"]) for r in rows if r["Value"] not in ("", "Not Available", "Not Meaningful")}


def ethanol_monthly():
    out = {}
    for k, v in _mer("ENTCPUS").items():
        y, m = int(k[:4]), int(k[4:])
        if m <= 12:
            out[f"{y}-{m:02d}"] = v / calendar.monthrange(y, m)[1]
    return out


def ethanol_annual():
    out = {}
    for k, v in _mer("ENTCPUS").items():
        if k.endswith("13"):
            y = int(k[:4])
            out[str(y)] = v / (366 if calendar.isleap(y) else 365)
    return out


def gasoline_annual():
    return {str(y): v for (y, _m), v in _xls("eia_gasoline_supplied_a.xls").items()}


def rfg_annual():
    return {str(y): v for (y, _m), v in _xls("eia_rfg_supplied_a.xls").items()}


def corn():
    p, _ = verified("ers_feed_grains.csv")
    prod, fuel = {}, {}
    for r in csv.DictReader(open(p, encoding="utf-8-sig")):
        if r["commodity"] != "Corn" or r["geography"] != "United States" or r["frequency"] != "Annual":
            continue
        if r["amount"] in ("", "NA"):
            continue
        if r["table_name"].startswith("Table 4--") and r["attribute"] == "Production":
            prod[r["year"]] = float(r["amount"])
        elif r["table_name"].startswith("Table 31--") and r["attribute"] == "Alcohol for fuel use":
            fuel[r["year"]] = float(r["amount"])
    return {y: (prod[y], fuel[y]) for y in sorted(set(prod) & set(fuel))}


_STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA",
           "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
           "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]


def state_bans():
    """Each row of EPA's table opens 'XX (region)' followed by the phaseout date. California's row reads
    'Originally12/31/ 02; delayed to 12/31/03': the date in force is the one after 'delayed to'."""
    t = flat("epa_state_bans_2007.pdf")
    rows = []
    for m in re.finditer(r"\b([A-Z]{2}) \((\d{1,2})\) ?(?=(.{0,140}))", t):   # lookahead: rows overlap
        st, rest = m.group(1), m.group(3)
        if st not in _STATES:
            continue
        nxt = re.search(r"\b[A-Z]{2} \(\d{1,2}\)", rest)          # the row ends where the next state's begins
        rest = rest[:nxt.start()] if nxt else rest
        d = re.search(r"delayed to (\d{1,2}/\d{1,2}/\d{2})", rest) or re.search(r"(\d{1,2}/\d{1,2}/\d{2})", rest)
        mo, da, yy = (int(x) for x in d.group(1).split("/"))
        complete = "complete" in rest.lower()   # Minnesota's row: "Partial/then complete"
        rows.append((st, dt.date(2000 + yy, mo, da).isoformat(), complete))
    return rows


def rfs_volumes():
    m = quote("plaw_109_58.html", r"\(in billions of gallons\):\.* ((?:20\d\d \d+\.\d ){6}20\d\d \d+\.\d)")
    toks = m.group(1).split()
    return {toks[i]: float(toks[i + 1]) for i in range(0, len(toks), 2)}
