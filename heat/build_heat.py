"""Build the heat page's payload (R4): an electric boiler against a gas one, on Texas prices.

Every number the page prints comes from here, and update_page.py writes them.

1. The average buyer, every month since 2001. EIA's Texas industrial electricity price (retail
   sales, cents/kWh) against the break-even electricity price: model.breakeven_Pe() at the model's
   defaults with that month's EIA Texas industrial gas price (N3035TX3, $/Mcf, converted with EIA's
   Texas heat content of deliveries for the year; outside 2007 to the latest year EIA gives, the
   nearest year).
2. The flexible buyer, every year since 2011. An electric boiler ADDED beside a gas one and run hour
   by hour on fuel cost alone, buying ERCOT real-time energy at the hub average (storage/'s price
   files) plus a delivery-and-other-charges adder (data/sources.json: low, central, high). Its
   savings against its own annualised capital and fixed O&M (model.py's capex_e, fom_e, r, life).
   Needs ERCOT's files under storage/data/raw (storage/fetch_ercot.py).
3. Emissions per unit of heat at the average and the marginal grid rate (data/sources.json).

    python build_heat.py          # writes outputs/payload.json
"""
import datetime as dt
import json
import os
import sys
from dataclasses import asdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import model as H  # noqa: E402


def _load(path, name):
    """storage/ercot_prices.py by its path: storage/ also has a model.py, so putting storage/ on
    sys.path would let `import model` pick up the wrong one."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _load(os.path.join(ROOT, "storage", "ercot_prices.py"), "ercot_prices")

RAW = os.path.join(HERE, "data", "raw")
OUT = os.path.join(HERE, "outputs", "payload.json")
SRC = json.load(open(os.path.join(HERE, "data", "sources.json"), encoding="utf-8"))
ERCOT_RAW = os.path.join(ROOT, "storage", "data", "raw")
ERCOT_CACHE = os.path.join(ROOT, "storage", "data", "cache")
FLEX_FIRST = 2011


def rows(name):
    return json.load(open(os.path.join(RAW, name), encoding="utf-8"))["response"]["data"]


def monthly():
    el = {r["period"]: float(r["price"]) for r in rows("eia_tx_ind_elec_price.json") if r["price"] not in (None, "")}
    gs = {r["period"]: float(r["value"]) for r in rows("eia_tx_ind_gas_price.json") if r["value"] not in (None, "")}
    hc = {int(r["period"]): float(r["value"]) for r in rows("eia_tx_gas_heat_content.json")}
    p0 = H.Params()
    out = []
    for per in sorted(set(el) & set(gs)):
        y = int(per[:4])
        hy = min(hc, key=lambda k: abs(k - y))
        pg = gs[per] / (hc[hy] / 1000.0)
        p = H.Params(**{**asdict(p0), "P_g": pg, "P_e": el[per] / 100})
        lc = H.lcoh(p)
        out.append({"period": per, "elec_c_kwh": el[per], "gas_usd_mcf": gs[per], "heat_content_year": hy,
                    "heat_content_btu_cf": hc[hy], "gas_usd_mmbtu": pg,
                    "breakeven_c_kwh": H.breakeven_Pe(p) * 100, "fuel_only_c_kwh": H.breakeven_Pe(p, full=False) * 100,
                    "heat_cost_gas": lc["gas"]["total"], "heat_cost_elec": lc["elec"]["total"]})
    for r in out:
        r["ratio"] = r["elec_c_kwh"] / r["breakeven_c_kwh"]
    return out, el, gs, hc


def gas_needed(elec_c):
    """The gas price at which `elec_c` cents/kWh electricity breaks even, by bisection on breakeven_Pe."""
    p0 = H.Params()
    lo, hi = 0.0, 500.0
    for _ in range(80):
        mid = (lo + hi) / 2
        be = H.breakeven_Pe(H.Params(**{**asdict(p0), "P_g": mid})) * 100
        lo, hi = (mid, hi) if be < elec_c else (lo, mid)
    return (lo + hi) / 2


FLAG_X = 2.0   # a month whose gas average is more than this times its neighbours' is set aside


def flagged_months(months):
    """Months whose average gas price is distorted by a few days inside them: more than FLAG_X
    times the mean of the month before and after. February 2021 (Winter Storm Uri) is the case
    that made this necessary: the boiler did not run during the storm week, yet the month's
    average, inflated by it, made the ordinary days either side look like cheap-electricity days
    (plan and claims reviews, 2026-10-23: $19.34 of 2021's $23.18 came from that February)."""
    g = [m["gas_usd_mmbtu"] for m in months]
    out = []
    for k in range(1, len(months) - 1):
        if g[k] > FLAG_X * (g[k - 1] + g[k + 1]) / 2:
            out.append(months[k]["period"])
    return out


def flexible(months):
    """A second, electric boiler beside the gas one, run hour by hour on fuel cost alone. Per kW
    of the boiler's electric input: the energy saved in the hours electricity (plus the per-MWh
    market charges) is cheaper than gas, less the per-kW delivery charges, against the boiler's
    own annualised capital and fixed O&M at three sizes (LBNL Figure B-1, and the model's own)."""
    p0 = H.Params()
    gas = {m["period"]: m["gas_usd_mmbtu"] for m in months}
    flags = set(flagged_months(months))
    ch = SRC["charges"]
    cap = SRC["electric_boiler_capital_usd_kw"]
    own = p0.capex_e / (H.KWH_PER_MMBTU / p0.eta_e)
    factor = H.crf(p0.r, p0.life) + p0.fom_e
    sizes = {"large": cap["large"], "model": own, "small": cap["small"]}
    cost = {k: v * factor for k, v in sizes.items()}
    years = []
    for y in range(FLEX_FIRST, 2100):
        f = os.path.join(ERCOT_RAW, "RTM_%d.zip" % y)
        if not os.path.exists(f):
            break
        d = E.year_prices(f, ERCOT_CACHE)
        p = E.hourly(d, "HB_HUBAVG")
        mon = []
        for k in range(d["days"]):
            dd = dt.date(y, 1, 1) + dt.timedelta(k)
            mon += ["%04d-%02d" % (dd.year, dd.month)] * E._hours_in(dd)
        mon = np.array(mon)
        keep = np.array([m in gas for m in mon])
        if not keep.any():
            break
        p, mon = p[keep], mon[keep]
        g = np.array([gas[m] for m in mon]) * (p0.eta_e * 1000 / H.KWH_PER_MMBTU) / p0.eta_g   # $ of gas per MWh of electricity
        clean = np.array([m not in flags for m in mon])
        row = {"year": y, "hours": int(len(p)), "complete": bool(keep.all() and d["complete"]),
               "through": str(max(mon.tolist())), "flagged": sorted({str(m) for m in mon if m in flags}),
               "neg_hours": int((p < 0).sum()), "cases": {}}
        for c in ("low", "central", "high"):
            win = (p + ch["energy_usd_mwh"][c]) < g
            gain = (g - p - ch["energy_usd_mwh"][c]) * win / 1000
            dem = ch["demand_usd_kw_yr"][c]
            row["cases"][c] = {"hours": int(win.sum()), "hours_set_aside": int((win & ~clean).sum()),
                               "energy_saving": float(gain.sum()), "energy_saving_clean": float(gain[clean].sum()),
                               "demand": dem, "net": float(gain.sum() - dem), "net_clean": float(gain[clean].sum() - dem)}
        years.append(row)
    return {"sizes_usd_kw": sizes, "annual_cost_kw_yr": cost, "factor": factor, "flagged": sorted(flags), "years": years}


def emissions():
    p0 = H.Params()
    g = SRC["gas_co2_kg_per_mmbtu"]["value"] / p0.eta_g
    out = {"gas_kg_mmbtu": g, "parity_t_mwh": SRC["gas_co2_kg_per_mmbtu"]["value"] / p0.eta_g * p0.eta_e / H.KWH_PER_MMBTU}
    for k in ("average", "marginal", "marginal_check"):
        t = SRC["grid_co2"][k]["lb_per_mwh"] * 0.45359237 / 1000
        out[k] = {"t_mwh": t, "kg_mmbtu": t * H.KWH_PER_MMBTU / p0.eta_e, "ratio_to_gas": t * H.KWH_PER_MMBTU / p0.eta_e / g}
    return out


def main():
    months, el, gs, hc = monthly()
    last = months[-1]
    years = {}
    for m in months:
        years.setdefault(m["period"][:4], []).append(m)
    annual = {y: {"elec_c_kwh": float(np.mean([m["elec_c_kwh"] for m in ms])),
                  "breakeven_c_kwh": float(np.mean([m["breakeven_c_kwh"] for m in ms])),
                  "gas_usd_mmbtu": float(np.mean([m["gas_usd_mmbtu"] for m in ms])), "months": len(ms)}
              for y, ms in years.items()}
    for a in annual.values():
        a["ratio_of_means"] = a["elec_c_kwh"] / a["breakeven_c_kwh"]
    ratios = np.array([m["ratio"] for m in months])
    # The default gas efficiency (0.85) is above the 70-80% LBNL-2001436 gives for existing fossil
    # boilers, and a better gas boiler makes the electric one look worse, which flatters the page's
    # "never". So the same months at 0.70, the case most favourable to electricity.
    p0 = H.Params()
    low = []
    for m in months:
        q = H.Params(**{**asdict(p0), "P_g": m["gas_usd_mmbtu"], "eta_g": 0.70})
        low.append(m["elec_c_kwh"] / (H.breakeven_Pe(q) * 100))
    low = np.array(low)
    g70 = SRC["gas_co2_kg_per_mmbtu"]["value"] / 0.70
    robust = {"eta_g": 0.70, "below": int((low < 1).sum()), "ratio_min": float(low.min()),
              "ratio_min_period": months[int(low.argmin())]["period"],
              "emissions_ratio": {k: SRC["grid_co2"][k]["lb_per_mwh"] * 0.45359237 / 1000 * H.KWH_PER_MMBTU / p0.eta_e / g70
                                  for k in ("average", "marginal")}}
    lo = months[int(ratios.argmin())]
    P = {"defaults": asdict(H.Params()), "months": months, "annual": annual,
         "summary": {"n_months": len(months), "first": months[0]["period"], "last": last["period"],
                     "below": int((ratios < 1).sum()), "ratio_min": float(ratios.min()), "ratio_min_period": lo["period"],
                     "ratio_median": float(np.median(ratios)), "ratio_max": float(ratios.max()),
                     "ratio_max_period": months[int(ratios.argmax())]["period"],
                     "under_2x": int((ratios < 2).sum()),
                     "last_gas_needed_usd_mmbtu": gas_needed(last["elec_c_kwh"]),
                     "elec_last_month": max(el), "gas_last_month": max(gs), "heat_content_years": [min(hc), max(hc)]},
         "robust_eta_g": robust, "flexible": flexible(months), "emissions": emissions(),
         "sources": json.load(open(os.path.join(HERE, "data", "fetched.json"), encoding="utf-8"))}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1, sort_keys=True)
        f.write("\n")
    s = P["summary"]
    print("heat payload: %d months %s..%s, below %d, ratio %.2f..%.2f (median %.2f), flexible %d years -> %s"
          % (s["n_months"], s["first"], s["last"], s["below"], s["ratio_min"], s["ratio_max"], s["ratio_median"],
             len(P["flexible"]["years"]), OUT))


if __name__ == "__main__":
    main()
