"""Read ERCOT's historical hub and load-zone settlement point prices.

One zip per year per market (fetch_ercot.py): DAM is hourly, RTM is
15-minute. Each zip holds one xlsx with a sheet per month. Rows are put in
delivery order (date, hour, repeated-hour flag, interval), so the
daylight-saving days come out as ERCOT settled them: 23 hours in March, 25 in
November, and a year of 8,760 or 8,784 hours either way. The reader asserts
that count; a year that comes out any other length is refused, not padded.

Older files (2011-2014) carry a stale sheet dimension that makes openpyxl's
read-only mode see one cell; reset_dimensions() is what makes them readable.

    year_prices(path_to_zip) -> {"market": "DAM"|"RTM", "year": int,
                                 "points": [names], "price": float array [points, steps],
                                 "steps_per_hour": 1|4, "start": "YYYY-MM-DD"}
Cached per zip as .npz in storage/data/cache (gitignored, not shipped), keyed by the zip's SHA-1, so a
replaced file (ERCOT rewrites the current year in place) is re-read.
"""
import calendar
import datetime as dt
import hashlib
import os
import re
import zipfile
from zoneinfo import ZoneInfo

import numpy as np
import openpyxl


def _sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _rows(path):
    z = zipfile.ZipFile(path)
    (name,) = [n for n in z.namelist() if n.lower().endswith(".xlsx")]
    wb = openpyxl.load_workbook(z.open(name), read_only=True)
    for sheet in wb.sheetnames:
        ws = wb[sheet]
        ws.reset_dimensions()
        it = ws.iter_rows(values_only=True)
        head = next(it)
        yield head, it


CT = ZoneInfo("America/Chicago")
MAX_FILLED = 4


def _hours_in(day):
    a = dt.datetime(day.year, day.month, day.day, tzinfo=CT)
    n = day + dt.timedelta(1)
    b = dt.datetime(n.year, n.month, n.day, tzinfo=CT)
    return round((b.astimezone(dt.timezone.utc) - a.astimezone(dt.timezone.utc)).total_seconds() / 3600)


def parse(path):
    market = "RTM" if "RTM" in os.path.basename(path).upper() else "DAM"
    recs = {}
    points = set()
    for head, it in _rows(path):
        col = {h: i for i, h in enumerate(head) if h}
        if market == "DAM":
            iD, iH, iR, iP, iV = (col["Delivery Date"], col["Hour Ending"], col["Repeated Hour Flag"],
                                  col["Settlement Point"], col["Settlement Point Price"])
        else:
            iD, iH, iI, iR, iP, iV = (col["Delivery Date"], col["Delivery Hour"], col["Delivery Interval"],
                                      col["Repeated Hour Flag"], col["Settlement Point Name"],
                                      col["Settlement Point Price"])
        for r in it:
            # footer rows (a "last updated" stamp in 2011-2013 files) carry no settlement point
            if r[iD] is None or r[iP] is None or r[iV] is None:
                continue
            m, d, y = (int(x) for x in str(r[iD]).split("/"))
            h = int(str(r[iH]).split(":")[0]) if market == "DAM" else int(r[iH])
            k = (y, m, d, h, r[iR] == "Y", 1 if market == "DAM" else int(r[iI]))
            recs.setdefault(k, {})[r[iP]] = float(r[iV])
            points.add(r[iP])
    # A 15-minute interval ERCOT's file leaves out is filled from the mean of
    # the same hour's other intervals, and counted. RTM 2013 lacks one: 02:00
    # (first pass) on 3 November 2013, the fall-back day, has 3 intervals of 4.
    # More than MAX_FILLED in a year, or an hour short by more than one, is
    # refused rather than filled.
    filled = []
    if market == "RTM":
        hours_seen = {}
        for k in recs:
            hours_seen.setdefault(k[:5], set()).add(k[5])
        for hk, ivs in hours_seen.items():
            missing = {1, 2, 3, 4} - ivs
            if len(missing) > 1:
                raise RuntimeError("%s: hour %s has %d of 4 intervals" % (path, hk, len(ivs)))
            for iv in missing:
                pts_ = set.intersection(*(set(recs[hk + (j,)]) for j in ivs))
                recs[hk + (iv,)] = {p: float(np.mean([recs[hk + (j,)][p] for j in ivs])) for p in pts_}
                filled.append("%04d-%02d-%02d h%d%s i%d" % (hk[:4] + ("r" if hk[4] else "", iv)))
        if len(filled) > MAX_FILLED:
            raise RuntimeError("%s: %d missing intervals, more than %d" % (path, len(filled), MAX_FILLED))
    keys = sorted(recs)
    years = {k[0] for k in keys}
    if len(years) != 1:
        raise RuntimeError("%s: rows from years %s" % (path, sorted(years)))
    year = years.pop()
    spp = 1 if market == "DAM" else 4
    first = dt.date(*keys[0][:3])
    last = dt.date(*keys[-1][:3])
    days = (last - first).days + 1
    full = 366 if calendar.isleap(year) else 365
    if first != dt.date(year, 1, 1):
        raise RuntimeError("%s: starts %s, not 1 January" % (path, first))
    # hours actually in those days in Central time: 23 on the spring change, 25 on the fall one
    hours = sum(_hours_in(first + dt.timedelta(n)) for n in range(days))
    if len(keys) != hours * spp:
        raise RuntimeError("%s: %d steps for %d days; expected %d" % (path, len(keys), days, hours * spp))
    pts = sorted(points)
    price = np.full((len(pts), len(keys)), np.nan)
    for j, k in enumerate(keys):
        row = recs[k]
        for i, p in enumerate(pts):
            if p in row:
                price[i, j] = row[p]
    return {"market": market, "year": year, "points": pts, "price": price, "steps_per_hour": spp,
            "start": first.isoformat(), "days": days, "complete": days == full,
            "through": last.isoformat(), "filled": np.array(filled, dtype=str)}


def year_prices(path, cache_dir):
    os.makedirs(cache_dir, exist_ok=True)
    sha = _sha1(path)
    c = os.path.join(cache_dir, os.path.basename(path).replace(".zip", "") + "_" + sha[:12] + ".npz")
    if os.path.exists(c):
        z = np.load(c, allow_pickle=False)
        out = {k: z[k] for k in z.files}
        out["points"] = [str(p) for p in out["points"]]
        for k in ("market", "start", "through"):
            out[k] = str(out[k])
        for k in ("year", "steps_per_hour", "days"):
            out[k] = int(out[k])
        out["complete"] = bool(out["complete"])
        return out
    d = parse(path)
    np.savez_compressed(c, **{k: (np.array(v) if not isinstance(v, np.ndarray) else v) for k, v in d.items()})
    return d


def hourly(d, point):
    """One point's price per hour; an RTM year is averaged over its four intervals."""
    p = d["price"][d["points"].index(point)]
    if d["steps_per_hour"] == 4:
        p = p.reshape(-1, 4).mean(axis=1)
    return p
