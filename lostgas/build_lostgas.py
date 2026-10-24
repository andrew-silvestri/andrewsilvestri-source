"""Build outputs/payload.json, the one file the figures, the page and the app read, and
outputs/operator_lauf.csv, the downloadable table (PHMSA's operator names as PHMSA publishes them).

What it computes, natural gas systems only (sources.natural_gas), 2010-2025:
- how the figure is reported: the share at or below zero, exactly zero, negative; the share of
  non-zero values that are whole numbers; the share of operator-state pairs that repeat last year's
  value exactly;
- the distribution of operator percentages (10th, 25th, 50th, 75th, 90th percentiles) on all reports
  and on "informative" reports (non-zero, not a whole number, not a repeat of last year), for the U.S.
  and for TX and OK;
- persistence: the rank correlation of an operator's figure between consecutive years, and the
  distribution of its year-to-year change;
- the 2018 change: of 2018's negative reports, how many came from pairs that reported exactly 0 in 2017;
- concentration: the largest operator's share of a state's services;
- EIA Table A1 for TX, OK and the U.S., 2018-2024;
- the quotations the page uses, read from the opened source files.

Run:  python build_lostgas.py
"""
import csv
import datetime as dt
import json
import os

import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import model as M     # noqa: E402
import sources as S   # noqa: E402
import xlrd           # noqa: E402
from netfetch import verified   # noqa: E402

OUT = os.path.join(HERE, "outputs", "payload.json")
CSV = os.path.join(HERE, "outputs", "operator_lauf.csv")
Q = (10, 25, 50, 75, 90)
RULE_YEAR = 2018          # first reports on the consumption denominator, negatives allowed (83 FR 3462)


def pct(v, qs=Q):
    a = np.array(v, float)
    return {f"p{q}": round(float(np.percentile(a, q, method="lower")), 3) for q in qs} | {"n": len(v)}


def spearman(x, y):
    """Rank correlation, average ranks for ties (the data are heaped, so ties matter)."""
    def rank(v):
        v = np.asarray(v, float)
        order = np.argsort(v, kind="mergesort")
        r = np.empty(len(v))
        r[order] = np.arange(len(v), dtype=float)
        for u in np.unique(v):
            m = v == u
            r[m] = r[m].mean()
        return r
    return float(np.corrcoef(rank(x), rank(y))[0, 1])


HERO_YEAR = 2025          # the newest PHMSA reports; the hero draws this year
BIN, LO, HI = 0.25, -5.0, 10.0
BAND_Q = (5, 95)          # the measurement-only band: the middle 90% of no-loss systems
DOLLAR_STATES = ("TX", "OK")


def hero(R, band):
    """The 2025 reports binned for the strip chart. Bins are right-inclusive, (a, b], so the bin
    ending at 0 holds the exact zeros and every lit "at or below zero" bin ends at or below 0.
    The two end bins gather the tails (<= LO, > HI). Per bin: all reports, those at or below
    zero, those inside the band; the counters are computed from the values, not the bins."""
    v = np.array([r["lauf"] for r in R if r["year"] == HERO_YEAR])
    edges = np.round(np.arange(LO, HI + BIN / 2, BIN), 6)
    bins = [{"a": None, "b": LO}] + [{"a": float(a), "b": float(b)} for a, b in zip(edges[:-1], edges[1:])] + [{"a": HI, "b": None}]
    lo, hi = band
    for b in bins:
        m = np.ones(len(v), bool)
        if b["a"] is not None:
            m &= v > b["a"]
        if b["b"] is not None:
            m &= v <= b["b"]
        b["n"] = int(m.sum()); b["le0"] = int((m & (v <= 0)).sum()); b["inside"] = int((m & (v >= lo) & (v <= hi)).sum())
    assert sum(b["n"] for b in bins) == len(v)
    return {"year": HERO_YEAR, "n": int(len(v)), "bins": bins, "bin": BIN, "lo": LO, "hi": HI,
            "median": float(np.percentile(v, 50, method="lower")),
            "le0": int((v <= 0).sum()), "neg": int((v < 0).sum()), "zero": int((v == 0).sum()),
            "inside": int(((v >= lo) & (v <= hi)).sum()), "below": int((v < lo).sum()), "above": int((v > hi).sum()),
            "tail_lo": bins[0]["n"], "tail_hi": bins[-1]["n"]}


def eia_series(code):
    p, _ = verified(f"eia_{code}a.xls")
    sh = xlrd.open_workbook(p).sheet_by_index(1)
    title = sh.cell_value(2, 1)
    return title, {xlrd.xldate_as_tuple(sh.cell_value(r, 0), 0)[0]: float(sh.cell_value(r, 1))
                   for r in range(3, sh.nrows) if sh.cell_value(r, 1) != ""}


def wmedian(vals, weights):
    """The value at which half the weight lies at or below (weights: services)."""
    o = np.argsort(vals, kind="mergesort")
    v, w = np.asarray(vals, float)[o], np.asarray(weights, float)[o]
    c = np.cumsum(w)
    return float(v[np.searchsorted(c, 0.5 * c[-1])])


def dollars(R):
    """What a point of LAUF is on a household's year, by state. Lost gas is LAUF% of consumption
    (PHMSA's denominator from 2018), valued at the citygate price, what the utility pays for gas:
    the residential price also carries delivery, which gas that never reaches a meter does not use.
    The year is the newest one EIA has every series for (household counts lag a year). The LAUF a
    typical household's system reports is the SERVICES-weighted median of the state's reports that
    year: an unweighted median counts a town of 300 services as much as a utility of 900,000 (plan
    review, finding 4)."""
    out = {}
    for st in DOLLAR_STATES:
        tc, cons = eia_series(f"N3010{st}2"); tn, num = eia_series(f"NA1501_S{st}_8")
        tg, cg = eia_series(f"N3050{st}3"); tr, res = eia_series(f"N3010{st}3")
        for t, unit in ((tc, "(MMcf)"), (tn, "(Count)"), (tg, "Citygate"), (tr, "Residential")):
            if unit not in t:
                raise RuntimeError(f"EIA series title does not say {unit}: {t}")
        y = max(set(cons) & set(num) & set(cg) & set(res))
        rs = [r for r in R if r["year"] == y and r["state"] == st and r["services"]]
        med = wmedian([r["lauf"] for r in rs], [r["services"] for r in rs])
        mcf = cons[y] * 1000.0 / num[y]
        per_pt = mcf * cg[y] / 100.0
        out[st] = {"year": y, "mcf_per_household": round(mcf, 2), "citygate": cg[y], "residential_price": res[y],
                   "bill": round(mcf * res[y], 0), "per_point": round(per_pt, 3), "wmedian_pct": med,
                   "reports": len(rs), "at_median": round(per_pt * med, 2)}
    return out


def inside_grid(R, year):
    """Share of one year's reports inside the measurement-only band, over the two assumptions
    that set the band's position, with and without exact zeros (plan review, findings 1 and 7),
    and weighted by services at the defaults."""
    rs = [r for r in R if r["year"] == year]
    v = np.array([r["lauf"] for r in rs]); nz = v[v != 0]
    w = np.array([r["services"] or 0 for r in rs], float)
    grid = []
    for T in (50.0, 55.0, 60.0, 65.0, 70.0):
        for u in (0.0, 0.35, 0.7, 1.0):
            a, _ = M.simulate({"gas_temp_f": T, "uncomp_share": u}, 200000, np.random.default_rng(M.SEED))
            lo, hi = (float(np.percentile(a, q)) for q in BAND_Q)
            grid.append({"gas_temp_f": T, "uncomp_share": u, "lo": round(lo, 2), "hi": round(hi, 2),
                         "all": round(float(((v >= lo) & (v <= hi)).mean()), 3),
                         "no_zero": round(float(((nz >= lo) & (nz <= hi)).mean()), 3)})
    d = [g for g in grid if g["gas_temp_f"] == M.DEFAULTS["gas_temp_f"] and g["uncomp_share"] == M.DEFAULTS["uncomp_share"]][0]
    m = (v >= d["lo"]) & (v <= d["hi"])
    return {"year": year, "grid": grid, "defaults": d,
            "services_weighted": round(float(w[m].sum() / w.sum()), 3), "services_from": 2015,
            "width_min": min(round(g["hi"] - g["lo"], 2) for g in grid), "width_max": max(round(g["hi"] - g["lo"], 2) for g in grid),
            "min_all": min(g["all"] for g in grid), "max_all": max(g["all"] for g in grid),
            "min_no_zero": min(g["no_zero"] for g in grid), "max_no_zero": max(g["no_zero"] for g in grid)}


def whole(v):
    return float(v).is_integer()


def main():
    R = [r for r in S.phmsa_reports() if S.natural_gas(r)]
    by = {}
    for r in R:
        by.setdefault(r["year"], {})[(r["operator_id"], r["state"])] = r   # one per pair (dups are rare)
    years = sorted(by)
    rep, dist, persist = {}, {}, {}
    prev = None
    for y in years:
        cur = by[y]
        v = [r["lauf"] for r in cur.values()]
        nz = [x for x in v if x != 0]
        pairs = [k for k in cur if prev and k in prev]
        repeat = sum(1 for k in pairs if cur[k]["lauf"] == prev[k]["lauf"])
        info = [r["lauf"] for k, r in cur.items()
                if r["lauf"] != 0 and not whole(r["lauf"]) and not (prev and k in prev and prev[k]["lauf"] == r["lauf"])]
        rep[y] = {"n": len(v), "at_or_below_zero": round(sum(x <= 0 for x in v) / len(v), 4),
                  "zero": round(sum(x == 0 for x in v) / len(v), 4), "negative": round(sum(x < 0 for x in v) / len(v), 4),
                  "whole_of_nonzero": round(sum(whole(x) for x in nz) / len(nz), 4),
                  "repeat_of_pairs": round(repeat / len(pairs), 4) if pairs else None, "pairs": len(pairs),
                  "informative": len(info)}
        d = {"US": {"all": pct(v), "informative": pct(info)}}
        for s in ("TX", "OK"):
            vs = [r["lauf"] for r in cur.values() if r["state"] == s]
            d[s] = {"all": pct(vs)}
        dist[y] = d
        if prev:
            x = [prev[k]["lauf"] for k in pairs]; z = [cur[k]["lauf"] for k in pairs]
            ch = [b - a for a, b in zip(x, z)]
            # the same change on pairs whose figure is informative in both years and not repeated:
            # 19-35% of pairs repeat exactly (change 0), which pulls the middle of "all pairs" in
            # (page claims check, finding 3)
            inf = [(a, b) for a, b in zip(x, z) if a != b and a != 0 and b != 0 and not whole(a) and not whole(b)]
            persist[y] = {"rank_corr": round(spearman(x, z), 3), "change": pct(ch), "pairs": len(pairs),
                          "abs_change_median": round(float(np.median(np.abs(ch))), 3),
                          "change_informative": pct([b - a for a, b in inf])}
        prev = cur
    # the 2018 change: negatives that had reported exactly zero the year before
    neg18 = [k for k, r in by[RULE_YEAR].items() if r["lauf"] < 0]
    was_zero = sum(1 for k in neg18 if k in by[RULE_YEAR - 1] and by[RULE_YEAR - 1][k]["lauf"] == 0)
    # concentration of services (from 2015, the first year with the column)
    conc = {}
    for y in years:
        if y < 2015:
            continue
        for s in ("TX", "OK"):
            rs = [r for r in by[y].values() if r["state"] == s and r["services"]]
            tot = sum(r["services"] for r in rs)
            conc.setdefault(s, {})[y] = round(max(r["services"] for r in rs) / tot, 4)
    eia = {y: S.eia_a1(y) for y in range(2018, 2025)}
    quotes = {
        "report_mix": S.quote("report_congress_lauf_2017.pdf", "LAUF gas is a combination", 135).rsplit(".", 1)[0] + ".",
        "report_proxy": S.quote("report_congress_lauf_2017.pdf", "LAUF gas is not a valid proxy", 84).rsplit(".", 1)[0] + ".",
        "report_meters": S.quote("report_congress_lauf_2017.pdf", "Volume meters have a tendency", 80).rsplit(".", 1)[0] + ".",
        "report_zero": S.quote("report_congress_lauf_2017.pdf", "PHMSA instructs companies that calculate a negative value", 110).rsplit(".", 1)[0] + ".",
        "fr_change": S.quote("fr_2018-01324.pdf", "PHMSA will calculate the percent of LAUF gas", 190),
        "partg": S.quote("gd_annual_form_cy2018_forward.pdf", "Unaccounted for gas as a percent of total consumption", 70),
        "tx_cap": S.quote("tx_16tac_ch7_2024.pdf", "The maximum allowable for a distribution system", 160),
        "tx_presumed": S.quote("tx_16tac_ch7_2024.pdf", "All lost and unaccounted for gas shall be presumed", 120),
        "tx_meter": S.quote("tx_16tac_ch7_2024.pdf", "meter errors due to inaccurate calibration or temperature and pressure fluctuations", 84),
        "ok_pga": S.quote("ok_tariff_1001.pdf", "LUFG shall be collected through the PGA", 39),
        "ok_measure": S.quote("ok_oac165_ch45_2024.pdf", "All gas transmitted by any utility shall be measured accurately by proper apparatus, and", 320),
    }
    # measurement alone (model.py): the defaults, and every uncertainty input scaled together, so the
    # page can say what scale reproduces the middle of the observed spread and what it cannot reach
    scaled = ("cg_u", "fleet_mean_sd", "fleet_drift", "meter_sd", "gas_temp_sd_f", "timing_sd")
    sweep = {}
    for k in (0.5, 1.0, 1.5, 2.0, 3.0, 4.0):
        p = {name: M.DEFAULTS[name] * k for name in scaled}
        sweep[str(k)] = M.summary(p)
    model_block = {"defaults": M.DEFAULTS, "at_defaults": M.summary({}), "scale_sweep": sweep,
                   "scaled_inputs": list(scaled), "limits": M.LIMITS}
    y1, _ = M.simulate({}, 200000, np.random.default_rng(M.SEED))
    band = tuple(round(float(np.percentile(y1, q)), 2) for q in BAND_Q)
    sens = {}
    for name, vals in (("gas_temp_f", (50.0, 60.0, 70.0)), ("uncomp_share", (0.0, 1.0))):
        for val in vals:
            a, _ = M.simulate({name: val}, 200000, np.random.default_rng(M.SEED))
            sens[f"{name}={val:g}"] = [round(float(np.percentile(a, q)), 2) for q in BAND_Q] + [round(float(np.median(a)), 2)]
    model_block["band"] = {"q": list(BAND_Q), "lo": band[0], "hi": band[1], "median": round(float(np.median(y1)), 2),
                           "neg_share": round(float((y1 < 0).mean()), 3), "sensitivity": sens}
    payload = {
        "hero": hero(R, band), "dollars": dollars(R), "inside": inside_grid(R, HERO_YEAR),
        "clip": {"shared_temp_pct": round(-float(M.DEFAULTS["uncomp_share"] * M.temp_bias_pct(M.DEFAULTS["gas_temp_f"])), 2),
                 "gas_temp_f": M.DEFAULTS["gas_temp_f"]},
        "data_as_of": S.data_as_of(),
        "owners": {st: dict(sorted(__import__("collections").Counter(
            r["operator_type"] or "" for r in R if r["year"] == HERO_YEAR and (st == "US" or r["state"] == st)).items()))
            for st in ("US", "TX", "OK")},
        "model": model_block,
        "built": dt.date.today().isoformat(), "years": [years[0], years[-1]], "rule_year": RULE_YEAR,
        "reporting": rep, "distribution": dist, "persistence": persist,
        "rule_change": {"negative_2018": len(neg18), "were_zero_2017": was_zero},
        "concentration_top_share": conc, "eia_a1": eia, "quotes": quotes,
        "tx_cap_on_consumption_pct": round(100 * 5.0 / 95.0, 2),
        "excluded_non_natural_gas": sum(1 for r in S.phmsa_reports() if not S.natural_gas(r)),
        "commodity_from": min(r["year"] for r in S.phmsa_reports() if r["commodity"] is not None),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
        f.write("\n")
    with open(CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["report_year", "operator_id", "operator_name", "state_of_operation", "commodity",
                    "operator_type", "services", "percent_unaccounted_for"])
        for r in sorted(R, key=lambda r: (r["year"], r["state"] or "", r["operator_id"] or 0)):
            w.writerow([r["year"], r["operator_id"], r["operator_name"], r["state"], r["commodity"] or "",
                        r["operator_type"] or "", r["services"] if r["services"] is not None else "", r["lauf"]])
    print(f"wrote {OUT} and {CSV} ({len(R)} natural gas reports)")


if __name__ == "__main__":
    main()
