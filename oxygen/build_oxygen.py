"""Build outputs/payload.json for the oxygen page from the hash-checked raw files (sources.py).

The page follows one clause of the 1990 Clean Air Act Amendments, the oxygen requirement for gasoline, through
three orders of effects. Every number it prints is computed here or read here out of the document that states
it, and the checks at the bottom compare the series with figures the sources themselves printed, so a reader
that misreads a file (a wrong column, thousand barrels a month taken as a day) stops the build.

Run:  python build_oxygen.py            writes outputs/payload.json
"""
import calendar
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sources as S   # noqa: E402

OUT = os.path.join(HERE, "outputs", "payload.json")
BBL_GAL = 42


def num(s):
    return float(s.replace(",", ""))


def annual_mean(monthly, year):
    ms = [f"{year}-{m:02d}" for m in range(1, 13)]
    if not all(m in monthly for m in ms):
        return None
    days = [calendar.monthrange(year, m)[1] for m in range(1, 13)]
    return sum(monthly[m] * d for m, d in zip(ms, days)) / sum(days)


def documents():
    """Figures the page takes from reports, each read out of the report's text."""
    d = {}
    m = S.quote("uscode_7545_2000.html", r"oxygen content of the gasoline shall equal or exceed (\d\.\d) percent by weight")
    d["o2_rfg"] = float(m.group(1))
    m = S.quote("uscode_7545_2000.html", r"contain not less than (\d\.\d) percent oxygen by weight")
    d["o2_oxy"] = float(m.group(1))
    m = S.quote("eia_mtbe_1999.pdf", r"MTBE demand increased from ([\d,]+) in (\d{4}) to ([\d,]+) barrels per day in (\d{4})")
    d["mtbe_a"] = {"year": int(m.group(2)), "kbd": num(m.group(1)) / 1000}
    d["mtbe_b"] = {"year": int(m.group(4)), "kbd": num(m.group(3)) / 1000}
    m = S.quote("eia_mtbe_1999.pdf", r"MTBE contained in motor gasoline increased to ([\d,]+) barrels per day by (\d{4})")
    d["mtbe_c"] = {"year": int(m.group(2)), "kbd": num(m.group(1)) / 1000}
    m = S.quote("epa_brp_1999.pdf", r"Over (\d+) percent of RFG contains the oxygenate methyl tertiary butyl ether "
                                    r"\(MTBE\) and approximately (\d+) percent contains ethanol")
    d["brp_mtbe_pct"], d["brp_eth_pct"] = int(m.group(1)), int(m.group(2))
    m = S.quote("usgs_wri034200.pdf", r"varied from (\d\.\d) for drinking water to (\d\.\d) for ground water")
    d["usgs_lo"], d["usgs_hi"] = float(m.group(1)), float(m.group(2))
    m = S.quote("eia_mtbe2006.pdf", r"about (\d+) thousand barrels per day of additional ethanol")
    d["eia2006_kbd"] = int(m.group(1))
    m = S.quote("fr_2006_26691.pdf", r"This final rule is effective on (\w+ \d+, \d{4})")
    d["repeal_effective"] = m.group(1)
    d["rfs"] = S.rfs_volumes()
    return d


def main():
    mtbe = S.mtbe_monthly()
    eth = S.ethanol_monthly()
    gas = S.gasoline_annual()
    rfg = S.rfg_annual()
    corn = S.corn()
    bans = S.state_bans()
    doc = documents()

    last_eth = max(eth)
    years = range(1993, int(last_eth[:4]) + (1 if last_eth.endswith("-12") else 0))
    annual = {}
    for y in years:
        a = {"eth": annual_mean(eth, y), "gas": gas.get(str(y)), "rfg": rfg.get(str(y))}
        mt = annual_mean(mtbe, y) if y <= 2010 else None
        a["mtbe"] = mt
        if a["gas"]:
            a["eth_share"] = a["eth"] / a["gas"]
            a["rfg_share"] = (a["rfg"] / a["gas"]) if a["rfg"] is not None else None
            a["mtbe_share"] = (mt / a["gas"]) if mt is not None else None
        annual[str(y)] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in a.items()}

    peak_y = max((y for y in annual if annual[y]["mtbe"] is not None), key=lambda y: annual[y]["mtbe"])
    # corn: the ERS file's last two marketing years are an estimate and a projection; the page uses the years before
    cy = sorted(corn)
    final = [y for y in cy if int(y) <= int(cy[-1]) - 2]
    corn_share = {y: corn[y][1] / corn[y][0] for y in final if int(y) >= 1993}

    ban_dates = sorted(b[1] for b in bans)
    bans_by_year = {str(y): sum(1 for d in ban_dates if d <= f"{y}-12-31") for y in range(1999, 2010)}

    # the chart series
    x_mtbe = [m for m in sorted(mtbe) if "1993-01" <= m <= "2008-12"]
    x_all = [m for m in sorted(eth) if m >= "1993-01"]
    rfs_gal = {y: v for y, v in doc["rfs"].items()}
    eth_bgal = {y: annual[y]["eth"] * 365 * BBL_GAL / 1e6 for y in annual if annual[y]["eth"]}

    P = {
        "through": last_eth,
        "doc": doc,
        "annual": annual,
        "peak": {"year": int(peak_y), "kbd": annual[peak_y]["mtbe"], "share": annual[peak_y]["mtbe_share"]},
        "switch": {"jan": mtbe["2006-01"], "may": mtbe["2006-05"], "dec": mtbe["2006-12"]},
        # the first year in which ethanol's annual use exceeds MTBE's
        "cross": min(int(y) for y in annual if annual[y]["mtbe"] is not None and annual[y]["eth"] > annual[y]["mtbe"]),
        "mtbe_last": max(mtbe),
        "bans": {"n": len(bans), "complete": sum(1 for b in bans if b[2]), "first": ban_dates[0],
                 "last": ban_dates[-1], "by_year": bans_by_year,
                 "rows": bans},
        "corn": {"share": {y: round(v, 6) for y, v in corn_share.items()}, "last_final": final[-1],
                 "file_last": cy[-1]},
        "rfs": {"mandate_bgal": rfs_gal, "actual_bgal": {y: round(eth_bgal[y], 3) for y in ("2006", "2007", "2008")}},
        "series": {
            "mtbe": {"x": x_mtbe, "v": [round(mtbe[m], 1) for m in x_mtbe]},
            "swap": {"x": x_all, "mtbe": [round(mtbe[m], 1) if m in mtbe else None for m in x_all],
                     "eth": [round(eth[m], 1) for m in x_all]},
        },
    }
    check(P)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"payload: data through {P['through']}; MTBE peak {P['peak']['year']} {P['peak']['kbd']:.0f} kb/d; "
          f"ethanol {annual[str(int(last_eth[:4]) - 1)]['eth_share']:.1%} of gasoline; {len(bans)} state bans")


def check(P):
    """Known answers from the sources' own text: if a reader is off, these fail."""
    A, d = P["annual"], P["doc"]
    errs = []
    # EIA 1999 printed 269 kb/d of MTBE in gasoline in 1997. Refinery and blender net input is a narrower
    # measure (it misses MTBE blended elsewhere), so it must come in below EIA's figure, and not far below:
    # 236 kb/d when first built (2026-11-07), 12% under.
    if not 0 < (d["mtbe_c"]["kbd"] - A["1997"]["mtbe"]) / d["mtbe_c"]["kbd"] < 0.15:
        errs.append(f"1997 MTBE {A['1997']['mtbe']:.0f} kb/d vs EIA's printed {d['mtbe_c']['kbd']:.0f}")
    # EIA 2006 put the MTBE still used in RFG at the start of 2006 near 130 kb/d of ethanol to replace it
    if not 80 < P["switch"]["jan"] < 160:
        errs.append(f"January 2006 MTBE {P['switch']['jan']:.0f} kb/d is not near EIA's early-2006 volume")
    # EIA's FAQ and MER: ethanol is about ten per cent of gasoline in the 2020s
    last = str(int(P["through"][:4]) - 1)
    if not 0.09 < A[last]["eth_share"] < 0.12:
        errs.append(f"ethanol share {A[last]['eth_share']:.3f} in {last} is not about one tenth")
    # RFG is about a third of US gasoline (EIA)
    if not 0.25 < A["1999"]["rfg_share"] < 0.40:
        errs.append("RFG share in 1999 not about a third")
    if P["bans"]["complete"] != 7:
        errs.append(f"EPA's 2007 table has seven complete bans (MN, CO, CA, MI, CT, NY, VT); read {P['bans']['complete']}")
    if P["bans"]["n"] != 25:
        errs.append(f"EPA's 2007 table lists 25 states; read {P['bans']['n']}")
    if d["o2_rfg"] != 2.0 or d["o2_oxy"] != 2.7:
        errs.append("oxygen percentages")
    if P["rfs"]["mandate_bgal"]["2006"] != 4.0:
        errs.append("RFS 2006 volume")
    if errs:
        raise SystemExit("payload checks failed:\n  " + "\n  ".join(errs))


if __name__ == "__main__":
    main()
