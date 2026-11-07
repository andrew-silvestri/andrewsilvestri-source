"""The public files the safety-net page reads, fetched into safetynet/data/raw/ and recorded in
data/fetched.json (URL, POST body, date, bytes, SHA-1).

U.S. Department of Labor, Employment and Training Administration (public domain)
- dol_a12.csv            UI Chartbook A.12: insured unemployment (regular state programs) as a per cent
                         of total unemployment, United States, annual, 1950 on.
- dol_a13_<year>.csv     UI Chartbook A.13: the same by state, one year per request (the form takes a
                         single year for an all-state chart), 1976 on.
- dol_ar5159.csv         ETA 5159 monthly claims and payment activity by state, 1971 on: c21 + c22 are
                         state UI continued weeks claimed (intrastate, and interstate filed from the
                         agent state). The build recomputes the latest year from it.
U.S. Bureau of Labor Statistics, public API v1 (no key; 25 series and 10 years a request)
- bls_cps_<y0>.json      Current Population Survey, not seasonally adjusted, thousands, monthly: total
                         unemployed (LNU03000000), job losers (LNU03023621), job losers on temporary
                         layoff (LNU03023653).
- bls_laus_<n>.json      Local Area Unemployment Statistics, unemployed, statewide, not seasonally
                         adjusted (LAUST<fips>0000000000004), monthly, the latest full year.
U.S. Census Bureau
- census_nst_est.csv     Vintage 2025 state population estimates (NST-EST2025-ALLDATA).
OECD
- oecd_nrr.csv           Benefits and Wages, net replacement rates in unemployment, single person
                         without children at 67% of the average wage, months 1, 12 and 24.

Documents the page quotes or reads figures from (sources.py reads them at render time)
- DOCS below: the BLS 2022 survey of UI applicants, BLS's 2025 annual-average table and its October
  note, DOL's 2026 trust fund solvency report, and the research papers' own PDFs or abstract pages.

When the keyless BLS quota for the day is spent, import_research_pull.py records the research step's
identical LAUS responses instead.

Run:  python fetch_public.py [name ...]
"""
import json
import sys
import time

from netfetch import fetch

LAST = 2025          # the latest full calendar year the page reports
DOL = "https://oui.doleta.gov/unemploy/Chartbook/createdf.php"
BLS = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
FORM = "application/x-www-form-urlencoded"
FIPS = {"AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10",
        "DC": "11", "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
        "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27",
        "MS": "28", "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35",
        "NY": "36", "NC": "37", "ND": "38", "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44",
        "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53",
        "WV": "54", "WI": "55", "WY": "56"}
CPS = ["LNU03000000", "LNU03023621", "LNU03023653"]
CPS_FROM = 1967


def laus_id(st):
    return f"LAUST{FIPS[st]}0000000000004"


DOCS = {
    "bls_uisup_2022.pdf": "https://www.bls.gov/news.release/archives/uisup_03292023.pdf",
    "bls_cpsaat01.htm": "https://www.bls.gov/cps/cpsaat01.htm",
    "dol_solvency_2026.pdf": "https://oui.doleta.gov/unemploy/docs/trustFundSolvReport2026.pdf",
    "cramer_nunn_2026.pdf": "https://www.minneapolisfed.org/-/media/assets/papers/community-development-working-"
                            "papers/2026/understanding-eligibility-and-take-up-in-state-unemployment-insurance-"
                            "programs.pdf",
    "dahl_knepper_w30152.pdf": "https://www.nber.org/system/files/working_papers/w30152/w30152.pdf",
    "ccw_w12639.htm": "https://www.nber.org/papers/w12639",
    "gruber_w4750.htm": "https://www.nber.org/papers/w4750",
    "ganong_noel_w25417.htm": "https://www.nber.org/papers/w25417",
    "hmm_w20884.htm": "https://www.nber.org/papers/w20884",
    "crck_qje2019.htm": "https://ideas.repec.org/a/oup/qjecon/v134y2019i1p227-279..html",
    "blank_card_w2871.htm": "https://www.nber.org/papers/w2871",
}


def jobs():
    """(name, url, kwargs) for every file, in the order they are fetched."""
    out = [("dol_a12.csv", DOL, dict(body=f"begyr=1950&endyr={LAST + 1}&states=US&chartnum=a12",
                                     content_type=FORM))]
    for y in range(1976, LAST + 1):
        out.append((f"dol_a13_{y}.csv", DOL, dict(body=f"begyr={y}&endyr={y}&states=US&chartnum=a13",
                                                  content_type=FORM)))
    out.append(("dol_ar5159.csv", "https://oui.doleta.gov/unemploy/csv/ar5159.csv", {}))
    for y0 in range(CPS_FROM, LAST + 1, 10):
        body = json.dumps({"seriesid": CPS, "startyear": str(y0), "endyear": str(min(y0 + 9, LAST))})
        out.append((f"bls_cps_{y0}.json", BLS, dict(body=body, content_type="application/json")))
    sts = list(FIPS)
    for i in range(0, len(sts), 25):
        body = json.dumps({"seriesid": [laus_id(s) for s in sts[i:i + 25]],
                           "startyear": str(LAST), "endyear": str(LAST)})
        out.append((f"bls_laus_{i // 25}.json", BLS, dict(body=body, content_type="application/json")))
    out.append(("census_nst_est.csv", "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/"
                                      "state/totals/NST-EST2025-ALLDATA.csv", {}))
    out.append(("oecd_nrr.csv", "https://sdmx.oecd.org/public/rest/data/OECD.ELS.JAI,DSD_TAXBEN_NRR@DF_NRR,1.0/"
                                "OECD+USA.NHIDU.PT_INC_DISP_HH_BJL.S_C0..AW67._Z.M1+M12+M24.YES+NO.YES+NO.A"
                                "?startPeriod=2001",
                dict(accept="application/vnd.sdmx.data+csv;version=1.0.0")))
    for name, url in DOCS.items():
        out.append((name, url, {}))
    return out


def check(name, p):
    t = p.read_bytes()
    if name.endswith(".json"):
        d = json.loads(t)
        if d.get("status") != "REQUEST_SUCCEEDED":
            raise SystemExit(f"{name}: BLS says {d.get('status')}: {d.get('message')}")
    elif len(t) < 200:
        raise SystemExit(f"{name}: {len(t)} bytes, not a data file")


if __name__ == "__main__":
    only = sys.argv[1:]
    for name, url, kw in jobs():
        if only and not any(name.startswith(o) for o in only):
            continue
        check(name, fetch(url, name, **kw))
        if "api.bls.gov" in url or "createdf" in url:
            time.sleep(0.5)
