"""
Write site/safetynet.html from template.html and outputs/payload.json.

Every number on the page comes from the payload (build_safetynet.py), from a figure read out of a
fetched document at render time (sources.py), or from a file this script measures (the archive's
size); the prose is in the template. The parts other scripts own - the nav (rebuild_nav.py), the
citation markers and Sources list (add_citations.py's table, applied here) and the ?v= stamps
(bust_cache.py) - are kept as the shipped page has them, so tests/test_generators.py can run this on
the shipped tree and expect no change. The idiom is ethane/update_page.py's.

claims() asserts every direction and range the template's words commit to ("three in four", "about
half the share of the 1950s", "most of the states below 20 are in the South", ...). If a rebuild
moves one, the generator stops rather than ship prose the payload contradicts.

The series charts place each annual average at mid-year ("YYYY-07"): the kit puts a date's tick at
its start, so a year plotted at January would sit on the last tick, at the plot's right edge, where
its label is clipped (cold-critic review, 2026-11-07).

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import csv
import io
import json
import math
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "safetynet.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
MANIFEST = os.path.join(HERE, "data", "fetched.json")
ZIP = os.path.join(SITE, "downloads", "safetynet-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

NAMES = {"AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
         "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
         "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana",
         "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
         "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
         "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
         "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
         "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
         "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
         "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"}


def r0(x):
    return f"{x:.0f}"


def r1(x):
    return f"{x:.1f}"


def mid(y):
    return f"{y}-07"


# ------------------------------------------------------- figures read from documents ---
def lit():
    """Each figure the page takes from a report or paper, matched in that document's own text."""
    import sources as S

    def one(name, pat, k=1):
        return S.quote(name, pat).group(k)
    d = {}
    d["bls_applied"] = one("bls_uisup_2022.pdf", r"In 2022, (\d+) percent of the unemployed who worked in the past "
                                                 r"12 months had applied for UI benefits")
    d["bls_received"] = one("bls_uisup_2022.pdf", r"In 2022, (\d+) percent of unemployed people who had applied for "
                                                  r"UI benefits after separating from their last job received benefits")
    d["bls_inelig"] = one("bls_uisup_2022.pdf", r"Among unemployed people who had not applied for UI benefits, (\d+) "
                                                r"percent did not apply because they thought they were ineligible")
    d["cn_elig"] = one("cramer_nunn_2026.pdf", r"by contrast to its actual 2024 rate of ([\d.]+)%")
    d["cn_mix"] = one("cramer_nunn_2026.pdf", r"a ([\d.]+) percentage point difference accounted for by shifting "
                                              r"composition")
    S.quote("cramer_nunn_2026.pdf", r"the share of short-term \(26 weeks or less\) unemployment in the U\.S\. has tended "
                                    r"to decline since 2000")
    d["cn_drop"] = one("cramer_nunn_2026.pdf", r"Eligibility has declined by ([\d.]+) percentage points since 2000, "
                                               r"while recipiency has fallen by more than 9 percentage points")
    d["cn_weeks"] = one("cramer_nunn_2026.pdf", r"([\d.]+) percentage points of the gap between actual and "
                                                r"counterfactual eligibility rates can be accounted for by reductions "
                                                r"in the maximum weeks allowed")
    S.quote("cramer_nunn_2026.pdf", r"As of Spring 2025, three states \(Florida, Kentucky, and North Carolina\) provide "
                                    r"only 12 weeks of benefits, with eight more states providing less than 26 weeks")
    d["bls_months"] = one("bls_cpsaat01.htm", r"Annual estimates for 2025 are (\d+)-month averages that exclude October")
    m = S.quote("dol_solvency_2026.pdf", r"As of January 1, 2026, the solvency levels of state UI trust funds in (\d+) "
                                         r"states met the recommended minimum solvency standard\. This remains down "
                                         r"from the start of 2020 prior to the pandemic when (\d+) states")
    d["solv_now"], d["solv_2020"] = m.group(1), m.group(2)
    S.quote("dol_solvency_2026.pdf", r"UI taxes, paid primarily by employers on the wages paid to employees")
    m = S.quote("dahl_knepper_w30152.pdf", r"receiving any UI benefits plunged from (\d+)% to just (\d+)% in the three "
                                           r"years following the reform, while recipiency rates held steady in "
                                           r"control states")
    d["nc_from"], d["nc_to"] = m.group(1), m.group(2)
    m = S.quote("dahl_knepper_w30152.pdf", r"North Carolina July 2013 26→20 weeks1 \$(\d+)→\$(\d+)")
    d["nc_wba0"], d["nc_wba1"] = m.group(1), m.group(2)
    S.quote("dahl_knepper_w30152.pdf", r"cuts were implemented based on the insolvency of North Carolina's state UI "
                                       r"fund")
    S.quote("dahl_knepper_w30152.pdf", r"its cuts were far larger than any previous rollback implemented in the "
                                       r"United States")
    d["nc_ur12"] = one("dahl_knepper_w30152.pdf", r"tion drops to 12 weeks when the state UR rate is less than "
                                                  r"([\d.]+)%, and increases by 1 week for each 0\.5% increase until "
                                                  r"reaching a maximum of 20 weeks when the state UR reaches 9%")
    S.quote("dahl_knepper_w30152.pdf", r"The reduction in use is partly mechanical")
    S.quote("dahl_knepper_w30152.pdf", r"In response, 7 states passed legislation that permanently cut the number of "
                                       r"weeks available through regular UI")
    S.quote("dahl_knepper_w30152.pdf", r"trust funds in sev- ?eral states neared insolvency")
    m = S.quote("dahl_knepper_w30152.pdf", r"Florida (January 2012) 26→20 weeks2")
    d["fl_date"] = m.group(1)
    m = S.quote("dahl_knepper_w30152.pdf", r"2 Maximum duration drops to (\d+) weeks when the state UR rate is less "
                                           r"than (\d+)%, and increased by 1 week for each 0\.5% increase until "
                                           r"reaching a maximum of (\d+) weeks")
    d["fl_min"], d["fl_ur"], d["fl_max"] = m.group(1), m.group(2), m.group(3)
    d["dk_emp"] = one("dahl_knepper_w30152.pdf", r"experience ([\d.]+-[\d.]+)% faster employment growth relative to "
                                                 r"the same firm's establishments in other states").replace("-", " to ")
    d["dk_sal"] = one("dahl_knepper_w30152.pdf", r"starting salaries are ([\d.]+-[\d.]+)% lower in reform states").replace("-", " to ")
    d["ccw"] = one("ccw_w12639.htm", r"from 20 weeks to 30 weeks similarly lowers job-finding rates in the first 20 "
                                     r"weeks of search by (\d+-\d+)%").replace("-", " to ")
    d["hmm"] = one("hmm_w20884.htm", r"In levels, ([\d.]+) million individuals secured employment in 2014 due to the "
                                     r"benefit cut")
    d["crck"] = one("crck_qje2019.htm", r"increased the unemployment rate by at most ([\d.]+) percentage point")
    d["gruber"] = one("gruber_w4750.htm", r"the average fall in consumption for the unemployed was (\d+)%; my results "
                                          r"imply that, in the absence of unemployment insurance, this fall would have "
                                          r"been over three times as large")
    S.quote("gruber_w4750.htm", r"food consumption expenditures for 1968-1987 from the Panel Study of Income Dynamics")
    S.quote("ganong_noel_w25417.htm", r"spending drops sharply at the large and predictable decrease in income arising "
                                      r"from the exhaustion of unemployment insurance \(UI\) benefits")
    d["bc_pts"] = one("blank_card_w2871.htm", r"takeup rates declined abruptly between 1980 and 1982, leading to a "
                                              r"(\d+) percentage point decline in the fraction of the unemployed who "
                                              r"receive benefits")
    return d


# ------------------------------------------------------------------- charts ---
def t_at(xs, y):
    return (y - xs[0]) / (xs[-1] - xs[0])


def US(P):
    return {int(k): v for k, v in P["us"].items()}


def ST(P, s):
    return {int(k): v for k, v in P["states"][s].items()}


def hero(P, L):
    import insight
    us = US(P)
    xs = sorted(us)
    last, a50 = P["last"], statistics.mean(us[y] for y in range(1950, 1960))
    hi_y = max(range(1950, 1960), key=lambda y: us[y])
    mid_lo, mid_hi = min(us[y] for y in range(1985, 2008)), max(us[y] for y in range(1985, 2008))
    spec = {"id": "safetynet-hero", "type": "series",
            "title": f"Claimants of state unemployment insurance per 100 unemployed people, United States, "
                     f"{xs[0]} to {last}, annual averages",
            "x": [mid(y) for y in xs], "y": {"label": "claimants per 100 unemployed", "min": 0},
            "series": [{"key": "us", "label": "United States", "color": "acc",
                        "values": [round(us[y], 2) for y in xs]}],
            "annotations": []}
    steps = [
        (f"<p><b>The 1950s: about half.</b> From 1950 to 1959, the figure averaged {r0(a50)} claimants per 100 "
         f"unemployed people. The highest year was {hi_y}, at {r0(us[hi_y])}.</p>", {"t": t_at(xs, 1959)}),
        (f"<p><b>1980 to 1984: a step down.</b> The figure decreased from {r0(us[1980])} in 1980 to "
         f"{r0(us[1984])} in 1984. Rebecca Blank and David Card found that fewer eligible unemployed people "
         f"claimed between 1980 and 1982. That decrease alone took about {L['bc_pts']} points off the figure.</p>",
         {"t": t_at(xs, 1984)}),
        (f"<p><b>1985 to 2019: lower.</b> From 1985 to 2007, the figure stayed between {r0(mid_lo)} and "
         f"{r0(mid_hi)}. After the recession of 2008 and 2009 it decreased again, to {r0(us[2019])} in 2019.</p>",
         {"t": t_at(xs, 2019)}),
        (f"<p><b>2020 to {last}: up, then down.</b> When employers laid off millions of workers at once in 2020, "
         f"the figure increased to {r0(us[2020])}. In {last}, it was {r0(us[last])}.</p>", {"t": 1}),
    ]
    return insight.scrolly(spec, steps, from_state={"t": 0})


def cuts(P, L):
    """The two states whose cuts the page describes, against the nation, 1976 to the last year."""
    import insight
    us, fl, nc = US(P), ST(P, "FL"), ST(P, "NC")
    last = P["last"]
    xs = list(range(1976, last + 1))
    spec = {"id": "safetynet-cuts", "type": "series",
            "title": f"Claimants of state unemployment insurance per 100 unemployed people, United States, "
                     f"Florida and North Carolina, 1976 to {last}, annual averages",
            "x": [mid(y) for y in xs], "y": {"label": "claimants per 100 unemployed", "min": 0},
            "series": [{"key": "us", "label": "United States", "color": "acc", "values": [round(us[y], 2) for y in xs]},
                       {"key": "fl", "label": "Florida", "color": "moss", "values": [round(fl[y], 2) for y in xs]},
                       {"key": "nc", "label": "North Carolina", "color": "ink",
                        "values": [round(nc[y], 2) for y in xs]}],
            "annotations": []}
    steps = [
        (f"<p><b>1976 to 2007.</b> Florida&rsquo;s figure was below the national one in most of these years; "
         f"North Carolina&rsquo;s was close to it. In 2007, the figure was {r0(fl[2007])} in Florida, "
         f"{r0(nc[2007])} in North Carolina and {r0(us[2007])} for the nation.</p>", {"t": t_at(xs, 2007)}),
        (f"<p><b>2008 to 2013: the cuts.</b> In the recession, several state trust funds came close to insolvency. "
         f"Seven states, Florida and North Carolina among them, then cut the maximum number of weeks. Florida&rsquo;s "
         f"figure had already decreased to {r0(fl[2011])} by 2011. From {L['fl_date']}, Florida paid at most "
         f"{L['fl_max']} weeks instead of 26, and {L['fl_min']} when its unemployment rate is below {L['fl_ur']} "
         f"per cent. North Carolina&rsquo;s cut followed in July 2013.</p>", {"t": t_at(xs, 2013)}),
        (f"<p><b>2014 to {last}: low.</b> In 2019, the figure was {r0(fl[2019])} in Florida and {r0(nc[2019])} in "
         f"North Carolina, against {r0(us[2019])} for the nation. In {last}, it was {r0(fl[last])}, "
         f"{r0(nc[last])} and {r0(us[last])}.</p>", {"t": 1}),
    ]
    return insight.scrolly(spec, steps, from_state={"t": 0})


def _clean_ticks(mx):
    """True when the strip's y step for a tallest bar of mx is a whole number other than 2.5 (charts.js niceStep
    with n = 4, labels printed with no decimals)."""
    raw = mx / 4
    p = 10 ** math.floor(math.log10(raw))
    best = max(k * p for k in (1, 2, 2.5, 5, 10) if k * p <= raw * 1.0001)
    return best >= 1 and best == int(best)


def strip(P):
    import insight
    last = P["last"]
    v = {s: P["states"][s][str(last)] for s in P["ranked"]}
    lo, hi = P["ranked"][0], P["ranked"][-1]
    for w in (5, 4, 6, 10):
        a0 = int(min(v.values()) // w * w)
        b1 = int(-(-max(v.values()) // w) * w)
        bins = [{"a": a, "b": a + w, "n": sum(1 for x in v.values() if a <= x < a + w)} for a in range(a0, b1, w)]
        if _clean_ticks(max(b["n"] for b in bins)):
            break
    assert sum(b["n"] for b in bins) == len(v)
    low = P["low_states"]
    spec = {"id": "safetynet-states", "type": "strip",
            "title": f"States and the District of Columbia by claimants of unemployment insurance per 100 "
                     f"unemployed people, {last}, in steps of {w}",
            "bins": bins,
            "range": {"lo": a0, "hi": P["low_line"], "label": f"below {P['low_line']:.0f}: {len(low)} states",
                      "state": "under"},
            "marks": [{"at": v[lo], "label": f"{NAMES[lo]} {r0(v[lo])}", "state": "ends"},
                      {"at": P["us"][str(last)], "label": f"U.S. {r0(P['us'][str(last)])}", "state": "us"},
                      {"at": v[hi], "label": f"{NAMES[hi]} {r0(v[hi])}", "state": "ends"}],
            "y": {"label": "states"},
            "x": {"label": f"claimants per 100 unemployed, {last}"}}
    med = statistics.median(v.values())
    steps = [
        (f"<p><b>{len(v)} programs.</b> Each bar shows how many states have a {last} figure in one {w}-point step. "
         f"The count includes the District of Columbia. The middle state had {r0(med)} claimants per 100 "
         f"unemployed people. The national figure, {r0(P['us'][str(last)])}, is higher because large states such "
         f"as California and New York are above the middle.</p>", {"t": 1, "us": 1}),
        (f"<p><b>Below one in five.</b> In {len(low)} states, fewer than {P['low_line']:.0f} of every 100 "
         f"unemployed people claimed. These {len(low)} states are home to {r0(100 * P['low_pop_share'])} per cent "
         f"of U.S. residents.</p>", {"t": 1, "us": 1, "under": 1}),
        (f"<p><b>Six to one.</b> {NAMES[lo]} had the lowest figure, {r1(v[lo])}. {NAMES[hi]} had the highest, "
         f"{r1(v[hi])}.</p>", {"t": 1, "us": 1, "under": 1, "ends": 1}),
    ]
    return insight.scrolly(spec, steps, from_state={"t": 0})


def comp(P):
    import insight
    C = {int(k): v for k, v in P["composition"].items()}
    xs = sorted(C)
    us = US(P)
    last = P["last"]
    spec = {"id": "safetynet-who", "type": "series",
            "title": f"Job losers and claimants of state unemployment insurance per 100 unemployed people, "
                     f"{xs[0]} to {last}, annual averages",
            "x": [mid(y) for y in xs], "y": {"label": "per 100 unemployed", "min": 0},
            "series": [{"key": "losers", "label": "Job losers", "color": "ink",
                        "values": [round(C[y]["job_loser_share"], 2) for y in xs]},
                       {"key": "claim", "label": "Claimants", "color": "acc",
                        "values": [round(us[y], 2) for y in xs]}],
            "annotations": []}
    steps = [
        (f"<p><b>{xs[0]} to 1979: close together.</b> In 1970, job losers were "
         f"{r0(C[1970]['job_loser_share'])} of every 100 unemployed people. Claimants were also "
         f"{r0(us[1970])} per 100 unemployed people.</p>", {"t": t_at(xs, 1979)}),
        (f"<p><b>1980 to {last}: apart.</b> The share of job losers increases in recessions and decreases after "
         f"them. In 2019, before the pandemic, job losers were {r0(C[2019]['job_loser_share'])} of every 100 "
         f"unemployed people, close to the {r0(C[1970]['job_loser_share'])} of 1970. Claimants did not return "
         f"to the 1970 level. They were {r0(us[2019])} per 100 unemployed people in 2019 and {r0(us[last])} in "
         f"{last}. In {last}, that was about {r0(C[last]['recip_per_100_losers'])} claimants for every 100 job "
         f"losers, against about {r0(C[1970]['recip_per_100_losers'])} in 1970.</p>", {"t": 1}),
    ]
    return insight.scrolly(spec, steps, from_state={"t": 0})


def state_rows(P):
    last = str(P["last"])
    out = []
    for s in sorted(NAMES, key=lambda s: NAMES[s]):
        a, b = P["states"][s]["2007"], P["states"][s][last]
        ch = round(b) - round(a)
        out.append(f'<tr><td>{NAMES[s]}</td><td class="n">{r0(a)}</td><td class="n">{r0(b)}</td>'
                   f'<td class="n">{"&minus;" if ch < 0 else "+" if ch > 0 else ""}{abs(ch)}</td></tr>')
    return "\n".join(out)


def south(P):
    """Census South (REGION 3) among the states below the line."""
    from netfetch import verified
    import fetch_public as F
    reg = {}
    for r in csv.DictReader(io.StringIO(verified("census_nst_est.csv")[0].read_text(encoding="latin-1"))):
        if r["SUMLEV"] == "040":
            reg[r["STATE"]] = r["REGION"]
    return sum(1 for s in P["low_states"] if reg[F.FIPS[s]] == "3")


# ------------------------------------------------------------------- claims ---
def claims(P, L):
    us = US(P)
    last = P["last"]
    a50 = statistics.mean(us[y] for y in range(1950, 1960))
    lo, hi = P["ranked"][0], P["ranked"][-1]
    C = {int(k): v for k, v in P["composition"].items()}
    fl, nc = ST(P, "FL"), ST(P, "NC")
    med = statistics.median(P["states"][s][str(last)] for s in NAMES)
    c = [
        ("h1 'three in four ... are not claiming': 72 to 78 of 100 do not claim", 72 <= 100 - us[last] <= 78),
        ("standfirst 'in the 1950s the figure was about' half again: last year 40-60% of the 1950s mean",
         0.4 <= us[last] / a50 <= 0.6),
        ("hero step 2 'a step down' 1980 to 1984", us[1984] < us[1980] - 5),
        ("hero step 3 'decreased again' to 2019: 2019 below the 1985-2007 minimum",
         us[2019] < min(us[y] for y in range(1985, 2008))),
        ("cuts step 1: Florida below the nation in most years 1976-2007",
         sum(fl[y] < us[y] for y in range(1976, 2008)) > 16),
        ("cuts step 1: North Carolina 'close to' the nation, within 6 points in most years 1976-2007",
         sum(abs(nc[y] - us[y]) < 6 for y in range(1976, 2008)) > 16),
        ("cuts step 2: Florida 'had already decreased' by 2011 from 2007", fl[2011] < fl[2007] - 10),
        ("cuts step 3 'low': both states below half the national figure in 2019 and the last year",
         all(s[y] < us[y] / 2 for s in (fl, nc) for y in (2019, last))),
        ("the lowest state is Florida, which the takeaway and standfirst name with Minnesota", (lo, hi) == ("FL", "MN")),
        ("'most of the states below 20 are in the South'", south(P) > len(P["low_states"]) / 2),
        ("strip step 1: the national figure is above the middle state", P["us"][str(last)] > med),
        ("strip step 1: California and New York are above the middle state",
         all(P["states"][s][str(last)] > med for s in ("CA", "NY"))),
        ("strip step 3 'six to one': highest / lowest rounds to 6",
         round(P["states"][hi][str(last)] / P["states"][lo][str(last)]) == 6),
        ("comp step 1 'close together' in 1970: claimants within 3 points of job losers",
         abs(us[1970] - C[1970]["job_loser_share"]) < 3),
        ("comp step 2 'close to the 44 of 1970': 2019 within 3 points of 1970",
         abs(C[2019]["job_loser_share"] - C[1970]["job_loser_share"]) < 3),
        ("comp step 2 'claimants did not return': 2019 at least 10 below 1970", us[2019] < us[1970] - 10),
        ("intro 'the household survey shows little change of this kind': last year within 5 points of 1970",
         abs(C[last]["job_loser_share"] - C[1970]["job_loser_share"]) < 5),
        ("Method: BLS's annual average uses the months the payload averages",
         int(L["bls_months"]) == 12 - len(P["missing_months_last"])),
        ("Method 'each of DOL's figures is 12/11': DOL / ours = 12/11 nationally",
         abs(P["us_dol_last"] / us[last] - 12 / 11) < 1e-3),
        ("Limits 'five states and the District of Columbia' above 100 in 2020",
         sorted(s for s in NAMES if P["states"][s]["2020"] > 100) == ["DC", "GA", "ME", "MN", "NY", "VT"]),
    ]
    bad = [n for n, ok in c if not ok]
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    L = lit()
    us = US(P)
    last = P["last"]
    lo, hi = P["ranked"][0], P["ranked"][-1]
    fetched = max(x["fetched"] for x in json.load(open(MANIFEST, encoding="utf-8")).values())
    a50 = statistics.mean(us[y] for y in range(1950, 1960))
    C = P["composition"]
    v = {
        "last": str(last), "prev": str(last - 1), "us_first": str(min(us)),
        "us_last": r0(us[last]), "us_last1": r1(us[last]), "us_dol": r1(P["us_dol_last"]), "us_50s": r0(a50),
        "lo_name": NAMES[lo], "lo_val": r0(P["states"][lo][str(last)]),
        "hi_name": NAMES[hi], "hi_val": r0(P["states"][hi][str(last)]),
        "stamp": insight.stamp_annual(last, "U.S. Department of Labor and Bureau of Labor Statistics", fetched,
                                      "the page adds each year after both agencies publish it"),
        "takeaways": insight.takeaways([
            f"Most unemployed people who receive nothing never applied: in a 2022 BLS survey, "
            f"{L['bls_applied']} per cent of the unemployed who had worked in the past year had applied, and "
            f"{L['bls_received']} per cent of those who applied received benefits.",
            f"Job losers, the group the program is for, were about the same share of the unemployed in {last} as "
            f"in 1970, {r0(C[str(last)]['job_loser_share'])} against {r0(C['1970']['job_loser_share'])} in 100, "
            f"while claimants decreased from {r0(us[1970])} in 100 to {r0(us[last])} in 100 over the same years.",
            f"In {len(P['low_states'])} states, home to {r0(100 * P['low_pop_share'])} per cent of U.S. residents, "
            f"fewer than 20 of every 100 unemployed people claimed in {last}; {NAMES[lo]}, at "
            f"{r0(P['states'][lo][str(last)])}, was lowest and {NAMES[hi]}, at {r0(P['states'][hi][str(last)])}, "
            f"highest."]),
        "hero": hero(P, L), "cuts": cuts(P, L), "strip": strip(P), "comp": comp(P), "state_rows": state_rows(P),
        "tol": f"{P['repro']['tol']:g}", "repro_us0": str(P["repro"]["us_years"][0]),
        "repro_us1": str(P["repro"]["us_years"][1]), "repro_st0": str(P["repro"]["state_years"][0]),
        "repro_st1": str(P["repro"]["state_years"][1]),
        "n_months": {11: "eleven", 10: "ten", 12: "twelve"}[12 - len(P["missing_months_last"])],
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    v.update({k: L[k] for k in ("bls_applied", "bls_received", "bls_inelig", "cn_elig", "cn_drop", "cn_weeks",
                                "cn_mix", "solv_now", "solv_2020", "nc_from", "nc_to", "nc_wba0", "nc_wba1",
                                "nc_ur12", "ccw", "hmm", "crck", "dk_emp", "dk_sal", "gruber")})
    claims(P, L)
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "ethane.html"), encoding="utf-8").read()
        stamps = {}
    else:
        stamps = dict(re.findall(r'(?:href|src|srcset)="([^"?]+)\?v=([0-9a-f]+)"', shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    text = text.replace("{{nav}}", nav)

    def stamp(m):
        path = m.group(2)
        return f'{m.group(1)}="{path}?v={stamps[path]}"' if path in stamps else m.group(0)
    return re.sub(r'(href|src|srcset)="([^"?]+\.(?:css|js|png))"', stamp, text)


def render(P):
    t = open(TEMPLATE, encoding="utf-8").read()
    v = values(P)
    missing = sorted(set(re.findall(r"{{(\w+)}}", t)) - set(v) - {"nav"})
    if missing:
        raise SystemExit(f"template placeholders without a value: {missing}")
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)))
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("safetynet.html")
    if not refs:
        return text, ["safetynet.html has no entry in add_citations.PAGES"]
    tmp = PAGE + ".render.tmp"
    open(tmp, "w", encoding="utf-8", newline="\n").write(text)   # LF: trap 32
    try:
        out, probs = add_citations.build(os.path.basename(tmp), refs)
    finally:
        os.remove(tmp)
    return (out if out is not None else text), probs


def main(apply=False):
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    t = render(P)
    t, probs = cite(t)
    for p in probs:
        print("  " + p)
    if os.path.exists(PAGE):
        old = open(PAGE, "rb").read().decode("utf-8")          # bytes: trap 32
        print("  safetynet.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  safetynet.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
