"""Readers for the ethane page. Each reads a hash-checked raw file (netfetch.verified), so no number on the
page is typed: volumes, prices and the heat content are read out of EIA's own files, and every quotation is
matched in the article it comes from at render time.

ngpl()          US field production of natural gas plant liquids by product, thousand barrels a day, by
                month: ethane, propane, normal butane, isobutane, natural gasoline, and EIA's total.
ethane_btu()    the heat content of ethane, million Btu per barrel (MER Table A1).
article(name)   the date and title of an EIA article, read from its page.
quote(name, p)  the text a regular expression matches in a source.
"""
import datetime as dt
import html
import re

import pymupdf
import xlrd

from netfetch import verified

_cache = {}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def flat(name):
    """A source's text, whitespace collapsed; HTML stripped of scripts, styles and tags."""
    if name not in _cache:
        p, _ = verified(name)
        if name.endswith(".pdf"):
            t = " ".join(pg.get_text() for pg in pymupdf.open(p))
        else:
            t = _decode(p.read_bytes())
            t = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", t, flags=re.S)
            t = html.unescape(re.sub(r"<[^>]+>", " ", t))
        _cache[name] = re.sub(r"\s+", " ", t).replace("\ufeff", "").replace("\u2019", "'").strip()
    return _cache[name]


def _decode(b):
    """EIA serves most pages as UTF-8 and some older ones as Windows-1252 (the 2019 NGWU's apostrophes)."""
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("cp1252")


def quote(name, pat):
    m = re.search(pat, flat(name))
    if not m:
        raise LookupError(f"{name}: no match for {pat!r}")
    return m


def _xls(name):
    """(date, [values...]) rows of an EIA dnav workbook's 'Data 1' sheet, and its column names."""
    p, _ = verified(name)
    sh = xlrd.open_workbook(p).sheet_by_name("Data 1")
    cols = [str(c.value) for c in sh.row(2)]
    rows = []
    for r in range(3, sh.nrows):
        c = sh.row(r)
        d = xlrd.xldate_as_datetime(c[0].value, 0).date()
        rows.append((f"{d.year:04d}-{d.month:02d}", [x.value if x.value != "" else None for x in c[1:]]))
    return cols, rows


NGPL_COLS = {"ngl": "U.S. Field Production of Natural Gas Liquids (Thousand Barrels per Day)",
             "eth": "U.S. Field Production of Ethane (Thousand Barrels per Day)",
             "pro": "U.S. Field Production of Propane (Thousand Barrels per Day)",
             "nbu": "U.S. Field Production of Normal Butane (Thousand Barrels per Day)",
             "ibu": "U.S. Field Production of Isobutane (Thousand Barrels per Day)",
             "ngas": "U.S. Field Production of Natural Gasoline (Thousand Barrels per Day)"}


def ngpl():
    cols, rows = _xls("eia_ngpl_by_product_m.xls")
    ix = {}
    for k, title in NGPL_COLS.items():
        if title not in cols:                       # a renamed column must stop the build, not shift it
            raise LookupError(f"eia_ngpl_by_product_m.xls: no column {title!r}")
        ix[k] = cols.index(title) - 1
    out = {}
    for ym, v in rows:
        if all(v[i] is not None for i in ix.values()):
            out[ym] = {k: float(v[i]) for k, i in ix.items()}
    return out


def ethane_btu():
    """MER Table A1 prints its two-column table row by row: '... Ethane 2.783 Catalyst, ...'."""
    m = quote("eia_mer_a1.pdf", r"Hydrocarbon Gas Liquids .{0,120}?Ethane (\d\.\d{3}) ")
    v = float(m.group(1))
    head = quote("eia_mer_a1.pdf", r"Monthly Energy Review (\w+ 20\d\d)").group(1)
    return {"mmbtu_per_bbl": v, "edition": head}


def article(name):
    """Date and headline as the article prints them, e.g. ('2014-05-08', 'High value of liquids ...')."""
    t = flat(name)
    if name.startswith("eia_tie_"):
        m = re.search(r"Today in Energy .*?((?:%s) \d{1,2}, 20\d\d) (.+?) (?:Source|Data source):" % "|".join(MONTHS), t)
    else:
        m = re.search(r"Release date: ((?:%s) \d{1,2}, 20\d\d)" % "|".join(MONTHS), t)
        raw = _decode(verified(name)[0].read_bytes())
        h = re.search(r"In the News:</h2>\s*<p><strong>(.*?)</strong>", raw, flags=re.S)
        if not (m and h):
            raise LookupError(f"{name}: no date and headline")
        d = dt.datetime.strptime(m.group(1), "%B %d, %Y").date()
        return d.isoformat(), re.sub(r"\s+", " ", html.unescape(h.group(1))).replace("\u2019", "'").strip()
    if not m:
        raise LookupError(f"{name}: no date and headline")
    d = dt.datetime.strptime(m.group(1), "%B %d, %Y").date()
    return d.isoformat(), m.group(2).strip()
