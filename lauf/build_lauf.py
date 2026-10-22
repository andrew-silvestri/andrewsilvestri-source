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

Run:  python build_lauf.py
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
            persist[y] = {"rank_corr": round(spearman(x, z), 3), "change": pct(ch), "pairs": len(pairs),
                          "abs_change_median": round(float(np.median(np.abs(ch))), 3)}
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
        "fr_change": S.quote("fr_2018-01324.pdf", "PHMSA will calculate the percent of LAUF gas", 190),
        "partg": S.quote("gd_annual_form_cy2018_forward.pdf", "Unaccounted for gas as a percent of total consumption", 70),
        "tx_cap": S.quote("tx_16tac_ch7_2024.pdf", "The maximum allowable for a distribution system", 160),
        "tx_presumed": S.quote("tx_16tac_ch7_2024.pdf", "All lost and unaccounted for gas shall be presumed", 120),
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
    payload = {
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
