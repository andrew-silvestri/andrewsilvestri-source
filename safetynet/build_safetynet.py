"""Build outputs/payload.json for the safety-net page from the hash-checked raw files.

What the page measures: the recipiency rate, DOL's name for the average number of people claiming
regular state unemployment insurance (UI) in a week, per 100 unemployed people. Regular state
programs only: no Extended Benefits, no federal pandemic programs, no federal-employee or ex-service
programs.

How each year is obtained
- 1950 to LAST-1, United States: DOL UI Chartbook A.12 as published.
- 1976 to LAST-1, states: DOL UI Chartbook A.13 as published.
- LAST (2025): recomputed from the raw files with DOL's own method, which this script first
  reproduces. Numerator: state UI continued weeks claimed (ETA 5159 columns c21 + c22) summed over the
  year's twelve monthly reports, divided by 52. Denominator: the annual average of unemployed people,
  BLS CPS for the nation and BLS LAUS for a state. The method is checked against every published
  year it can reach (REPRO_FROM to LAST-1) to 0.05 points before it is used.
  BLS published no October 2025 household data (the lapse in federal appropriations). DOL's 2025
  figures reproduce only when that month counts as zero in a twelve-month average, which raises every
  2025 rate by 12/11. The script asserts that, then uses the mean of the eleven months BLS published,
  as BLS does for its own 2025 annual average. USE_DOL_LAST = True ships DOL's figure instead.

Also computed: who the unemployed are (CPS by reason, 1967 on), the share of residents living in
states where fewer than 20 in 100 unemployed people claim, and OECD's net replacement rates.

Run:  python build_safetynet.py
"""
import csv
import io
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fetch_public import FIPS, LAST, CPS_FROM, laus_id  # noqa: E402
from netfetch import verified  # noqa: E402

OUT = os.path.join(HERE, "outputs", "payload.json")
USE_DOL_LAST = False
REPRO_FROM = 2006       # first year the national reproduction is checked (CPS pulled from 1967)
STATE_REPRO = (2020, LAST - 1)   # A.13 reproduces exactly on the current LAUS vintage from 2020
TOL = 0.05              # points
LOW = 20.0              # the "fewer than 1 in 5" line


def rows(name):
    p, _ = verified(name)
    return list(csv.reader(io.StringIO(p.read_text(encoding="utf-8-sig"))))


def a12():
    r = rows("dol_a12.csv")
    assert r[0][0] == "Year", r[0]
    return {int(x[0]): float(x[1]) for x in r[1:] if x and x[1] not in ("", "NA")}


def a13():
    out = {}
    for y in range(1976, LAST + 1):
        r = rows(f"dol_a13_{y}.csv")
        assert r[0][:3] == ["Year", "State", "Insured Unemployment"], r[0]
        for x in r[1:]:
            if x and x[2] not in ("", "NA"):
                assert int(x[0]) == y
                out[(x[1], y)] = 100 * float(x[2])
    return out


def claims():
    """Continued weeks claimed, state UI (c21 + c22), by (state, year), with the count of monthly reports."""
    p, _ = verified("dol_ar5159.csv")
    cw, n = defaultdict(float), defaultdict(int)
    with open(p, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            y = int(r["rptdate"][-4:]) if "/" in r["rptdate"] else int(r["rptdate"][:4])
            cw[(r["st"], y)] += float(r["c21"] or 0) + float(r["c22"] or 0)
            n[(r["st"], y)] += 1
    return cw, n


def bls():
    """{(series, year, month): value or None}; None where BLS printed '-' (no data)."""
    m = {}
    for name in sorted(os.listdir(os.path.join(HERE, "data", "raw"))):
        if not (name.startswith("bls_") and name.endswith(".json")):
            continue
        p, _ = verified(name)
        for s in json.loads(p.read_text(encoding="utf-8"))["Results"]["series"]:
            for x in s["data"]:
                if x["period"].startswith("M") and x["period"] != "M13":
                    m[(s["seriesID"], int(x["year"]), int(x["period"][1:]))] = (
                        None if x["value"].strip() == "-" else float(x["value"]))
    return m


def annual(m, sid, y, zero_missing=False):
    have = [(k, m[(sid, y, k)]) for k in range(1, 13) if (sid, y, k) in m]
    if len(have) != 12:
        raise SystemExit(f"{sid} {y}: {len(have)} monthly rows, not 12")
    got = [v for _, v in have if v is not None]
    return sum(got) / (12 if zero_missing else len(got)), [k for k, v in have if v is None]


def nat_rate(cw, m, y, zero_missing=False):
    num = sum(v for (st, yy), v in cw.items() if yy == y) / 52
    den, gaps = annual(m, "LNU03000000", y, zero_missing)
    return 100 * num / (den * 1000), gaps


def st_rate(cw, m, st, y, zero_missing=False):
    den, gaps = annual(m, laus_id(st), y, zero_missing)
    return 100 * cw[(st, y)] / 52 / den, gaps


def main():
    A12, A13 = a12(), a13()
    cw, nrep = claims()
    m = bls()
    problems = []

    # --- the method, reproduced where DOL published it
    for y in range(REPRO_FROM, LAST):
        r, gaps = nat_rate(cw, m, y)
        if gaps or abs(r - A12[y]) > TOL:
            problems.append(f"US {y}: reproduced {r:.2f}, DOL A.12 {A12[y]:.2f}, missing months {gaps}")
    for y in range(STATE_REPRO[0], STATE_REPRO[1] + 1):
        for st in FIPS:
            r, gaps = st_rate(cw, m, st, y)
            if abs(r - A13[(st, y)]) > TOL:
                problems.append(f"{st} {y}: reproduced {r:.2f}, DOL A.13 {A13[(st, y)]:.2f}")
    # --- the latest year: DOL's figure is the zero-month one; ours is the eleven-month mean
    r0, gaps = nat_rate(cw, m, LAST, zero_missing=True)
    r1, _ = nat_rate(cw, m, LAST)
    if abs(r0 - A12[LAST]) > TOL:
        problems.append(f"US {LAST}: DOL {A12[LAST]:.2f} is not the zero-month figure {r0:.2f}")
    if any(nrep[(st, LAST)] != 12 for st in FIPS):
        problems.append(f"{LAST}: a state has fewer than 12 monthly ETA 5159 reports")
    st_last, st_gaps = {}, set()
    for st in FIPS:
        z, g = st_rate(cw, m, st, LAST, zero_missing=True)
        st_gaps.update(g)
        if abs(z - A13[(st, LAST)]) > TOL:
            problems.append(f"{st} {LAST}: DOL {A13[(st, LAST)]:.2f} is not the zero-month figure {z:.2f}")
        st_last[st] = A13[(st, LAST)] if USE_DOL_LAST else st_rate(cw, m, st, LAST)[0]
    if problems:
        raise SystemExit("method check failed:\n  " + "\n  ".join(problems))

    us = {y: v for y, v in A12.items() if y < LAST}
    us[LAST] = A12[LAST] if USE_DOL_LAST else r1
    states = {st: {y: A13[(st, y)] for y in range(1976, LAST) if (st, y) in A13} for st in FIPS}
    for st in FIPS:
        states[st][LAST] = st_last[st]

    # --- who the unemployed are (CPS by reason), and recipients per 100 job losers
    comp = {}
    for y in range(CPS_FROM, LAST + 1):
        u, _ = annual(m, "LNU03000000", y)
        jl, _ = annual(m, "LNU03023621", y)
        tl, _ = annual(m, "LNU03023653", y)
        comp[y] = {"unemployed_k": round(u, 1), "job_losers_k": round(jl, 1), "temp_layoff_k": round(tl, 1),
                   "job_loser_share": round(100 * jl / u, 2),
                   "recip_per_100_losers": round(us[y] * u / jl, 2)}

    # --- residents of states under the line
    pop = {}
    for r in csv.DictReader(io.StringIO(verified("census_nst_est.csv")[0].read_text(encoding="latin-1"))):
        if r["SUMLEV"] == "040" and r["STATE"] in FIPS.values():
            pop[r["STATE"]] = int(r[f"POPESTIMATE{LAST}"])
    if len(pop) != len(FIPS):
        raise SystemExit(f"census: {len(pop)} states found, not {len(FIPS)}")
    low = sorted(st for st in FIPS if st_last[st] < LOW)
    pop_low = sum(pop[FIPS[s]] for s in low) / sum(pop.values())

    # --- OECD net replacement rates, latest year
    nrr = {}
    for r in csv.DictReader(io.StringIO(verified("oecd_nrr.csv")[0].read_text(encoding="utf-8-sig"))):
        key = (r["REF_AREA"], r["UNEMP_DURATION"], r["SOC_ASS_BENEFIT"], r["HOUSE_BENEFIT"])
        nrr.setdefault(key, {})[int(r["TIME_PERIOD"])] = float(r["OBS_VALUE"])
    oy = max(max(v) for v in nrr.values())

    def o(area, mo, sa):
        return nrr[(area, mo, sa, sa)][oy]

    ranked = sorted(FIPS, key=lambda s: st_last[s])
    _, last_gaps = annual(m, "LNU03000000", LAST)
    P = {
        "last": LAST, "use_dol_last": USE_DOL_LAST,
        "us": {str(y): round(v, 3) for y, v in sorted(us.items())},
        "us_dol_last": round(A12[LAST], 3), "us_zero_month_last": round(r0, 3),
        "missing_months_last": last_gaps, "state_missing_months_last": sorted(st_gaps),
        "states": {st: {str(y): round(v, 3) for y, v in sorted(states[st].items())} for st in FIPS},
        "states_dol_last": {st: round(A13[(st, LAST)], 3) for st in FIPS},
        "composition": {str(y): v for y, v in comp.items()},
        "low_line": LOW, "low_states": low, "low_pop_share": round(pop_low, 4),
        "pop": {st: pop[FIPS[st]] for st in FIPS},
        "ranked": ranked,
        "repro": {"us_years": [REPRO_FROM, LAST - 1], "state_years": list(STATE_REPRO), "tol": TOL},
        "oecd": {"year": oy,
                 "us_m1_all": o("USA", "M1", "YES"), "us_m12_all": o("USA", "M12", "YES"),
                 "us_m1_ui": o("USA", "M1", "NO"), "us_m12_ui": o("USA", "M12", "NO"),
                 "oecd_m1_all": o("OECD", "M1", "YES"), "oecd_m12_all": o("OECD", "M12", "YES"),
                 "oecd_m12_ui": o("OECD", "M12", "NO")},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(P, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"US {LAST}: {us[LAST]:.2f} (DOL {A12[LAST]:.2f}, zero-month {r0:.2f}); missing months {last_gaps}")
    print(f"lowest {ranked[:3]} {[round(st_last[s], 2) for s in ranked[:3]]}; "
          f"highest {ranked[-3:]} {[round(st_last[s], 2) for s in ranked[-3:]]}")
    print(f"{len(low)} states under {LOW:.0f}: {pop_low:.1%} of residents")
    print(f"reproduced US {REPRO_FROM}-{LAST - 1} and states {STATE_REPRO[0]}-{STATE_REPRO[1]} to {TOL} pt")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
