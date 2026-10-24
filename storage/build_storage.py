"""Build the storage page's payload from ERCOT's real prices (R4, D-20).

Every number the page prints comes from here, and update_page.py writes them;
nothing on the page is typed.

For each year in data/raw (2011 to the current year to date), real-time
(RTM, hourly mean of the four 15-minute prices) and day-ahead (DAM) at the
ERCOT Hub Average, HB_HUBAVG: model.optimize() for 1, 2, 4 and 8 hours. For
the 4-hour battery, the cash it makes each hour (sale minus purchase minus
the cycling cost), summed by day, and how concentrated the year's earnings
are. Plus the same 4-hour battery at every hub and load zone for the years
named in ZONE_YEARS.

Perfect foresight throughout: optimize() sees the whole month's prices before
it acts, so every dollar figure is a ceiling no real battery reaches.

    python build_storage.py          # writes outputs/payload.json
"""
import datetime as dt
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ercot_prices as E  # noqa: E402
import model as M  # noqa: E402

RAW = os.path.join(HERE, "data", "raw")
CACHE = os.path.join(HERE, "data", "cache")
OUT = os.path.join(HERE, "outputs", "payload.json")
POINT = "HB_HUBAVG"
DURS = (1, 2, 4, 8)
FIRST_YEAR = 2011          # ERCOT's nodal market opened 1 December 2010; 2010's file is that month alone
ZONE_YEARS = (2023, 2025)


def daily(cash, start, n_days):
    """Cash per hour -> cash per calendar day, with the DST days' 23 and 25 hours."""
    out, i = [], 0
    for k in range(n_days):
        h = E._hours_in(start + dt.timedelta(k))
        out.append(float(cash[i:i + h].sum()))
        i += h
    assert i == len(cash), (i, len(cash))
    return np.array(out)


def concentration(cash, days):
    """Shares are of the year's earnings (hours, or days, where cash > 0), not of
    the net: charging happens in other hours, so a share of the net can pass
    100% (2021 DAM 4h: the best 1% of hours were 137% of the net)."""
    pos = np.sort(cash[cash > 0])[::-1]
    earn = float(pos.sum())
    half_h = int(np.searchsorted(np.cumsum(pos), earn / 2) + 1)
    dpos = np.sort(days[days > 0])[::-1]
    half_d = int(np.searchsorted(np.cumsum(dpos), dpos.sum() / 2) + 1)
    return {"earnings": earn, "hours_for_half": half_h, "days_for_half": half_d,
            "best10_days_share": float(dpos[:10].sum() / dpos.sum()),
            "hours_earning": int(len(pos))}


def year_result(path, with_days):
    d = E.year_prices(path, CACHE)
    p = E.hourly(d, POINT)
    row = {"year": d["year"], "market": d["market"], "through": d["through"], "complete": d["complete"],
           "hours": int(len(p)), "mean": float(p.mean()), "p99": float(np.percentile(p, 99)),
           "max": float(p.max()), "neg_hours": int((p < 0).sum()),
           "filled_intervals": [str(x) for x in d.get("filled", [])], "dur": {}}
    for h in DURS:
        r = M.optimize(p, h)
        ent = {"net_per_kw": r["revenue"] / 1000, "net_per_kw_yr": r["rev_per_kw_yr"],
               "cycles": r["cycles"]}
        if h == 4:
            cash = p * (r["dis"] - r["ch"]) - r["c_deg"] * 0.5 * (r["dis"] + r["ch"])
            days = daily(cash, dt.date.fromisoformat(d["start"]), d["days"])
            assert abs(days.sum() - r["revenue"]) < 1e-6 * max(1, abs(r["revenue"]))
            ent.update(concentration(cash, days))
            if with_days:
                ent["daily_per_kw"] = [round(v / 1000, 4) for v in days]
                order = np.argsort(-days)
                ent["half_days"] = sorted(int(i) for i in order[:ent["days_for_half"]])
        row["dur"][str(h)] = ent
    return row


def zones(year):
    d = E.year_prices(os.path.join(RAW, "RTM_%d.zip" % year), CACHE)
    out = {}
    for pt in d["points"]:
        if pt == "HB_BUSAVG":     # the bus average is not a place a battery sits
            continue
        out[pt] = M.optimize(E.hourly(d, pt), 4)["rev_per_kw_yr"]
    return out


def ice_check(year=2015):
    """ERCOT's DAM HB_NORTH, on-peak (HE07-HE22, weekdays), against EIA's record
    of next-day on-peak ICE trades at "ERCOT North 345KV Peak" for the same
    delivery days (data/ice_electric-2015final.xls, EIA Wholesale Electricity
    and Natural Gas Market Data). 2015 is the last year EIA's file trades it
    daily (224 days; 7 in 2019; none from 2023). See test_storage.py for the
    tolerance and the breaks."""
    import pandas as pd
    ice = pd.read_excel(os.path.join(HERE, "data", "ice_electric-%dfinal.xls" % year))
    ice = ice[ice["Price hub"] == "ERCOT North 345KV Peak"]
    ice = ice.groupby(pd.to_datetime(ice["Delivery start date"]).dt.date)["Wtd avg price $/MWh"].mean()
    d = E.year_prices(os.path.join(RAW, "DAM_%d.zip" % year), CACHE)
    p = E.hourly(d, "HB_NORTH")
    by_day, i, day = {}, 0, dt.date(year, 1, 1)
    while day.year == year:
        n = E._hours_in(day)
        he = list(range(1, 25)) if n == 24 else ([1, 2] + list(range(4, 25)) if n == 23 else [1, 2, 2] + list(range(3, 25)))
        for h in he:
            if day.weekday() < 5 and 7 <= h <= 22:
                by_day.setdefault(day, []).append(p[i])
            i += 1
        day += dt.timedelta(1)
    common = sorted(set(by_day) & set(ice.index))
    a = np.array([np.mean(by_day[k]) for k in common]); b = np.array([ice[k] for k in common])
    months = np.array([k.month for k in common])
    mdiff = [float(100 * (a[months == m].mean() / b[months == m].mean() - 1)) for m in range(1, 13)]
    return {"year": year, "days": len(common), "ice_days": int(len(ice)),
            "annual_pct": float(100 * abs(a.mean() / b.mean() - 1)),
            "month_pct_max": float(max(abs(x) for x in mdiff)), "r": float(np.corrcoef(a, b)[0, 1])}


def main():
    years = sorted({int(os.path.basename(f)[4:8]) for f in glob.glob(os.path.join(RAW, "RTM_*.zip"))})
    years = [y for y in years if y >= FIRST_YEAR]
    P = {"point": POINT, "durations": list(DURS), "rte": 0.86, "c_deg": 2.0, "rtm": {}, "dam": {}, "zones": {}}
    for y in years:
        P["rtm"][str(y)] = year_result(os.path.join(RAW, "RTM_%d.zip" % y), with_days=True)
        P["dam"][str(y)] = year_result(os.path.join(RAW, "DAM_%d.zip" % y), with_days=False)
        print(y, "RTM 4h %.1f, DAM 4h %.1f $/kW-yr" % (P["rtm"][str(y)]["dur"]["4"]["net_per_kw_yr"],
                                                     P["dam"][str(y)]["dur"]["4"]["net_per_kw_yr"]), flush=True)
    for y in ZONE_YEARS:
        P["zones"][str(y)] = zones(y)
    P["ice"] = ice_check()
    last = P["rtm"][str(years[-1])]
    P["through"] = last["through"]
    P["sources"] = json.load(open(os.path.join(HERE, "data", "fetched.json"), encoding="utf-8"))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1, sort_keys=True)
        f.write("\n")
    print("payload: %d years, through %s -> %s" % (len(years), P["through"], OUT))


if __name__ == "__main__":
    main()
