"""
Write site/safetynet.html from template.html and outputs/payload.json.

Every number on the page comes from the payload (build_safetynet.py), from a figure read out of a
fetched document at render time (sources.py), or from a file this script measures (the archive's
size); the prose is in the template. The parts other scripts own - the nav (rebuild_nav.py), the
citation markers and Sources list (add_citations.py's table, applied here) and the ?v= stamps
(bust_cache.py) - are kept as the shipped page has them, so tests/test_generators.py can run this on
the shipped tree and expect no change. The idiom is ethane/update_page.py's.

claims() asserts every direction and range the template's words commit to ("three in four", "about
half the share of the 1950s", "most of the low states are in the South", ...). If a rebuild moves
one, the generator stops rather than ship prose the payload contradicts.

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import csv
import io
import json
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
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def r0(x):
    return f"{x:.0f}"


def r1(x):
    return f"{x:.1f}"


# ------------------------------------------------------- figures read from documents ---
def lit():
    """Each figure the page takes from a report or paper, matched in that document's own text."""
    import sources as S

    def one(name, pat, k=1):
        return S.quote(name, pat).group(k)
    d = {}
    m = S.quote("bls_uisup_2022.pdf", r"In 2022, (\d+) percent of the unemployed who worked in the past 12 months "
                                      r"had applied for UI benefits")
    d["bls_applied"] = m.group(1)
    d["bls_received"] = one("bls_uisup_2022.pdf", r"In 2022, (\d+) percent of unemployed people who had applied for "
                                                  r"UI benefits after separating from their last job received benefits")
    d["bls_inelig"] = one("bls_uisup_2022.pdf", r"Among unemployed people who had not applied for UI benefits, (\d+) "
                                                r"percent did not apply because they thought they were ineligible")
    d["cn_elig"] = one("cramer_nunn_2026.pdf", r"by contrast to its actual 2024 rate of ([\d.]+)%")
    d["cn_mix"] = one("cramer_nunn_2026.pdf", r"a ([\d.]+) percentage point difference accounted for by shifting "
                                              r"composition")
    d["cn_drop"] = one("cramer_nunn_2026.pdf", r"Eligibility has declined by ([\d.]+) percentage points since 2000, "
                                               r"while recipiency has fallen by more than 9 percentage points")
    d["cn_weeks"] = one("cramer_nunn_2026.pdf", r"([\d.]+) percentage points of the gap between actual and "
                                                r"counterfactual eligibility rates can be accounted for by reductions "
                                                r"in the maximum weeks allowed")
    S.quote("cramer_nunn_2026.pdf", r"As of Spring 2025, three states \(Florida, Kentucky, and North Carolina\) provide "
                                    r"only 12 weeks of benefits, with eight more states providing less than 26 weeks")
    m = S.quote("bls_cpsaat01.htm", r"Annual estimates for 2025 are (\d+)-month averages that exclude October")
    d["bls_months"] = m.group(1)
    m = S.quote("dol_solvency_2026.pdf", r"As of January 1, 2026, the solvency levels of state UI trust funds in (\d+) "
                                         r"states met the recommended minimum solvency standard\. This remains down "
                                         r"from the start of 2020 prior to the pandemic when (\d+) states")
    d["solv_now"], d["solv_2020"] = m.group(1), m.group(2)
    m = S.quote("dahl_knepper_w30152.pdf", r"receiving any UI benefits plunged from (\d+)% to just (\d+)% in the three "
                                           r"years following the reform, while recipiency rates held steady in "
                                           r"control states")
    d["nc_from"], d["nc_to"] = m.group(1), m.group(2)
    m = S.quote("dahl_knepper_w30152.pdf", r"North Carolina July 2013 26→20 weeks1 \$(\d+)→\$(\d+)")
    d["nc_wba0"], d["nc_wba1"] = m.group(1), m.group(2)
    S.quote("dahl_knepper_w30152.pdf", r"cuts were implemented based on the insolvency of North Carolina's state UI "
                                       r"fund")
    S.quote("dahl_knepper_w30152.pdf", r"duration drops to 12 weeks when the state UR rate is less than 5\.5%")
    S.quote("dahl_knepper_w30152.pdf", r"The reduction in use is partly mechanical")
    d["fl_date"] = one("dahl_knepper_w30152.pdf", r"Florida (January 2012) 26→20 weeks")
    d["dk_emp"] = one("dahl_knepper_w30152.pdf", r"experience ([\d.]+-[\d.]+)% faster employment growth").replace("-", "&ndash;")
    d["dk_sal"] = one("dahl_knepper_w30152.pdf", r"starting salaries are ([\d.]+-[\d.]+)% lower in reform states").replace("-", "&ndash;")
    d["ccw"] = one("ccw_w12639.htm", r"from 20 weeks to 30 weeks similarly lowers job-finding rates in the first 20 "
                                     r"weeks of search by (\d+-\d+)%").replace("-", " to ")
    d["hmm"] = one("hmm_w20884.htm", r"In levels, ([\d.]+) million individuals secured employment in 2014 due to the "
                                     r"benefit cut")
    d["crck"] = one("crck_qje2019.htm", r"increased the unemployment rate by at most ([\d.]+) percentage point")
    d["gruber"] = one("gruber_w4750.htm", r"the average fall in consumption for the unemployed was (\d+)%; my results "
                                          r"imply that, in the absence of unemployment insurance, this fall would have "
                                          r"been over three times as large")
    S.quote("ganong_noel_w25417.htm", r"spending drops sharply at the large and predictable decrease in income arising "
                                      r"from the exhaustion of unemployment insurance \(UI\) benefits")
    m = S.quote("blank_card_w2871.htm", r"takeup rates declined abruptly between 1980 and 1982, leading to a (\d+) "
                                        r"percentage point decline in the fraction of the unemployed who receive "
                                        r"benefits")
    d["bc_pts"] = m.group(1)
    return d


# ------------------------------------------------------------------- charts ---
def years(P, key="us"):
    return sorted(int(y) for y in P[key])


def t_at(xs, y):
    return (y - xs[0]) / (xs[-1] - xs[0])


def hero(P, L):
    import insight
    us = {int(k): v for k, v in P["us"].items()}
    xs = years(P)
    lo = P["ranked"][0]
    st = {int(k): v for k, v in P["states"][lo].items()}
    last, a50 = P["last"], statistics.mean(us[y] for y in range(1950, 1960))
    spec = {"id": "safetynet-hero", "type": "series",
            "title": f"Claimants of state unemployment insurance per 100 unemployed people, United States "
                     f"{xs[0]} to {last} and {NAMES[lo]} 1976 to {last}, annual averages",
            "x": [str(y) for y in xs], "y": {"label": "claimants per 100 unemployed", "min": 0},
            "series": [{"key": "us", "label": "United States", "color": "acc",
                        "values": [round(us[y], 2) for y in xs]},
                       {"key": lo, "label": NAMES[lo], "color": "moss",
                        "values": [round(st[y], 2) if y in st else None for y in xs]}],
            "annotations": [{"at": "1981", "text": "take-up falls, 1980-82", "short": "1980-82"},
                            {"at": "2012", "text": f"{NAMES[lo]} cuts weeks", "short": "cut"}]}
    hi_y = max(range(1950, 1960), key=lambda y: us[y])
    steps = [
        (f"<p><b>The 1950s: about half.</b> From 1950 to 1959, an average of {r0(a50)} of every 100 unemployed "
         f"people claimed state unemployment insurance in a typical week. The highest year was {hi_y}, at "
         f"{r0(us[hi_y])}.</p>", {"t": t_at(xs, 1959)}),
        (f"<p><b>1980 to 1984: a step down.</b> The figure decreased from {r0(us[1980])} in 1980 to {r0(us[1984])} "
         f"in 1984. Rebecca Blank and David Card found that fewer of the eligible unemployed claimed after 1980, "
         f"which by itself took about {L['bc_pts']} points off the share.</p>", {"t": t_at(xs, 1990)}),
        (f"<p><b>2007 to 2019: {NAMES[lo]}.</b> In 2007, {r0(st[2007])} of every 100 unemployed people in "
         f"{NAMES[lo]} claimed. From {L['fl_date']} the state paid at most 20 weeks instead of 26, on a scale that "
         f"falls as unemployment falls. By 2019 the figure was {r0(st[2019])}.</p>", {"t": t_at(xs, 2019)}),
        (f"<p><b>2020 to {last}: a spike, then back.</b> When millions were laid off at once in 2020, the national "
         f"figure rose to {r0(us[2020])}. In {last} it was {r0(us[last])} nationally and {r0(st[last])} in "
         f"{NAMES[lo]}.</p>", {"t": 1}),
    ]
    return insight.scrolly(spec, steps, from_state={"t": 0})


def strip(P):
    import insight
    last = P["last"]
    v = {s: P["states"][s][str(last)] for s in P["ranked"]}
    lo, hi = P["ranked"][0], P["ranked"][-1]
    w = 5
    a0 = int(min(v.values()) // w * w)
    b1 = int(-(-max(v.values()) // w) * w)
    bins = [{"a": a, "b": a + w, "n": sum(1 for x in v.values() if a <= x < a + w)} for a in range(a0, b1, w)]
    assert sum(b["n"] for b in bins) == len(v)
    low = P["low_states"]
    spec = {"id": "safetynet-states", "type": "strip",
            "title": f"States and the District of Columbia by claimants of unemployment insurance per 100 "
                     f"unemployed people, {last}, in steps of {w}",
            "bins": bins,
            "range": {"lo": a0, "hi": P["low_line"], "label": f"under {P['low_line']:.0f}: {len(low)} states",
                      "state": "under"},
            "marks": [{"at": v[lo], "label": f"{NAMES[lo]} {r0(v[lo])}", "state": "ends"},
                      {"at": P["us"][str(last)], "label": f"U.S. {r0(P['us'][str(last)])}", "state": "us"},
                      {"at": v[hi], "label": f"{NAMES[hi]} {r0(v[hi])}", "state": "ends"}],
            "y": {"label": "states"},
            "x": {"label": f"claimants per 100 unemployed, {last}"}}
    med = statistics.median(v.values())
    steps = [
        (f"<p><b>{len(v)} programs.</b> Each bar counts the states, with the District of Columbia, whose figure "
         f"for {last} falls in a step of {w}. The middle state had {r0(med)} claimants per 100 unemployed people; "
         f"the national figure, {r0(P['us'][str(last)])}, is higher because large states such as California and "
         f"New York are above the middle.</p>", {"t": 1, "us": 1}),
        (f"<p><b>Under one in five.</b> In {len(low)} states, fewer than {P['low_line']:.0f} of every 100 "
         f"unemployed people were claiming. They are home to {r0(100 * P['low_pop_share'])} per cent of the "
         f"country&rsquo;s residents.</p>", {"t": 1, "us": 1, "under": 1}),
        (f"<p><b>Six to one.</b> {NAMES[lo]} was lowest, at {r1(v[lo])}; {NAMES[hi]} was highest, at "
         f"{r1(v[hi])}.</p>", {"t": 1, "us": 1, "under": 1, "ends": 1}),
    ]
    return insight.scrolly(spec, steps, from_state={"t": 0})


def comp(P):
    import insight
    C = {int(k): v for k, v in P["composition"].items()}
    xs = sorted(C)
    us = {int(k): v for k, v in P["us"].items()}
    last = P["last"]
    spec = {"id": "safetynet-who", "type": "series",
            "title": f"Job losers and claimants of state unemployment insurance per 100 unemployed people, "
                     f"{xs[0]} to {last}, with claimants per 100 job losers below",
            "x": [str(y) for y in xs], "y": {"label": "per 100 unemployed", "min": 0, "max": 80},
            "series": [{"key": "losers", "label": "Job losers", "color": "ink",
                        "values": [round(C[y]["job_loser_share"], 2) for y in xs]},
                       {"key": "claim", "label": "Claimants", "color": "acc",
                        "values": [round(us[y], 2) for y in xs]}],
            "under": [{"kind": "line", "label": "Claimants per 100 job losers", "color": "moss",
                       "values": [round(C[y]["recip_per_100_losers"], 1) for y in xs], "height": 72}],
            "annotations": []}
    non_rec = [C[y]["job_loser_share"] for y in xs if y not in RECESSION]
    steps = [
        (f"<p><b>{xs[0]} to 1979: close together.</b> Job losers, the group the program is for, were "
         f"{r0(C[1970]['job_loser_share'])} of every 100 unemployed people in 1970. Claimants were "
         f"{r0(us[1970])}: about {r0(C[1970]['recip_per_100_losers'])} for every 100 job losers.</p>",
         {"t": t_at(xs, 1979)}),
        (f"<p><b>1980 to {last}: apart.</b> Outside recession years, job losers stayed between "
         f"{r0(min(non_rec))} and {r0(max(non_rec))} of every 100 unemployed people. Claimants fell. In {last}, "
         f"job losers were {r0(C[last]['job_loser_share'])} and claimants {r0(us[last])}: about "
         f"{r0(C[last]['recip_per_100_losers'])} for every 100 job losers.</p>", {"t": 1}),
    ]
    return insight.scrolly(spec, steps, from_state={"t": 0})


# NBER recession years (any month in recession) from 1967: the job-loser share jumps in them
RECESSION = {1969, 1970, 1973, 1974, 1975, 1980, 1981, 1982, 1990, 1991, 2001, 2007, 2008, 2009, 2020}


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
    """Census South (REGION 3) among the states under the line."""
    from netfetch import verified
    reg = {}
    for r in csv.DictReader(io.StringIO(verified("census_nst_est.csv")[0].read_text(encoding="latin-1"))):
        if r["SUMLEV"] == "040":
            reg[r["STATE"]] = r["REGION"]
    import fetch_public as F
    return sum(1 for s in P["low_states"] if reg[F.FIPS[s]] == "3")


# ------------------------------------------------------------------- claims ---
def claims(P, L):
    us = {int(k): v for k, v in P["us"].items()}
    last = P["last"]
    a50 = statistics.mean(us[y] for y in range(1950, 1960))
    lo, hi = P["ranked"][0], P["ranked"][-1]
    C = {int(k): v for k, v in P["composition"].items()}
    c = [
        ("h1 'three in four ... get no unemployment check': 72 to 78 of 100 do not claim", 72 <= 100 - us[last] <= 78),
        ("takeaway 1 and standfirst 'about half' of the 1950s: last year 40-60% of the 1950s mean",
         0.4 <= us[last] / a50 <= 0.6),
        ("hero step 2 'a step down' 1980 to 1984", us[1984] < us[1980] - 5),
        ("hero step 3: the lowest state fell from 2007 to 2019", P["states"][lo]["2019"] < P["states"][lo]["2007"]),
        ("hero step 3: the lowest state is Florida, whose law the step describes", lo == "FL"),
        ("'most of the low states are in the South'", south(P) > len(P["low_states"]) / 2),
        ("strip step 1: the national figure is above the middle state",
         P["us"][str(last)] > statistics.median(P["states"][s][str(last)] for s in NAMES)),
        ("strip step 1: California and New York are above the middle state",
         all(P["states"][s][str(last)] > statistics.median(P["states"][x][str(last)] for x in NAMES)
             for s in ("CA", "NY"))),
        ("strip step 3 'six to one': highest / lowest rounds to 6", round(P["states"][hi][str(last)] /
                                                                          P["states"][lo][str(last)]) == 6),
        ("comp step 1 'close together' in 1970: claimants within 5 points of job losers",
         abs(us[1970] - C[1970]["job_loser_share"]) < 5),
        ("comp step 2: claimants per 100 job losers fell from 1970 to the last year",
         C[last]["recip_per_100_losers"] < C[1970]["recip_per_100_losers"] - 25),
        ("comp: job-loser share in the last year within 5 points of 1970",
         abs(C[last]["job_loser_share"] - C[1970]["job_loser_share"]) < 5),
        ("Method: BLS's annual average uses the months the payload averages",
         int(L["bls_months"]) == 12 - len(P["missing_months_last"])),
        ("Method 'makes each of DOL's figures 12/11': DOL / ours = 12/11 nationally",
         abs(P["us_dol_last"] / us[last] - 12 / 11) < 1e-3),
        ("OECD paragraph 'paid nothing' after a year", P["oecd"]["us_m12_ui"] == 0),
        ("OECD paragraph: U.S. first month below the OECD average", P["oecd"]["us_m1_ui"] < P["oecd"]["oecd_m1_all"]),
        ("Limits 'five states and the District of Columbia' above 100 in 2020",
         sorted(s for s in NAMES if P["states"][s]["2020"] > 100) == ["DC", "GA", "ME", "MN", "NY", "VT"]),
        ("takeaway 2 'the share of job losers had not changed much': last year within 5 points of 1970",
         abs(C[last]["job_loser_share"] - C[1970]["job_loser_share"]) < 5),
    ]
    bad = [n for n, ok in c if not ok]
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    L = lit()
    us = {int(k): v for k, v in P["us"].items()}
    last = P["last"]
    lo, hi = P["ranked"][0], P["ranked"][-1]
    fetched = max(x["fetched"] for x in json.load(open(MANIFEST, encoding="utf-8")).values())
    a50 = statistics.mean(us[y] for y in range(1950, 1960))
    o = P["oecd"]
    v = {
        "last": str(last), "prev": str(last - 1), "us_first": str(min(us)),
        "us_last": r0(us[last]), "us_last1": r1(us[last]), "us_dol": r1(P["us_dol_last"]), "us_50s": r0(a50),
        "lo_name": NAMES[lo], "lo_val": r0(P["states"][lo][str(last)]),
        "hi_name": NAMES[hi], "hi_val": r0(P["states"][hi][str(last)]),
        "stamp": insight.stamp_annual(last, "U.S. Department of Labor and Bureau of Labor Statistics", fetched,
                                      "a new year is added when both have published it"),
        "takeaways": insight.takeaways([
            f"In an average week of {last}, about {r0(us[last])} of every 100 unemployed Americans were claiming "
            f"state unemployment insurance; in the 1950s about {r0(a50)} of every 100 were claiming it.",
            f"Job losers, the group the program is built for, have made up close to half of the unemployed since "
            f"1970; claimants were about as many as job losers in 1970, and about "
            f"{r0(P['composition'][str(last)]['recip_per_100_losers'])} for every 100 of them in {last}, though the "
            f"share of job losers had not changed much.",
            f"In {len(P['low_states'])} states, home to {r0(100 * P['low_pop_share'])} per cent of Americans, fewer "
            f"than one in five unemployed people were claiming; {NAMES[lo]} was lowest at "
            f"{r0(P['states'][lo][str(last)])} in 100 and {NAMES[hi]} highest at {r0(P['states'][hi][str(last)])}, "
            f"about six times as many."]),
        "hero": hero(P, L), "strip": strip(P), "comp": comp(P), "state_rows": state_rows(P),
        "oecd_year": str(o["year"]), "us_m1": r0(o["us_m1_ui"]), "oecd_m1": r0(o["oecd_m1_all"]),
        "oecd_m12_ui": r0(o["oecd_m12_ui"]), "oecd_m12_all": r0(o["oecd_m12_all"]),
        "us_m12_all": r0(o["us_m12_all"]),
        "tol": f"{P['repro']['tol']:g}", "repro_us0": str(P["repro"]["us_years"][0]),
        "repro_us1": str(P["repro"]["us_years"][1]), "repro_st0": str(P["repro"]["state_years"][0]),
        "repro_st1": str(P["repro"]["state_years"][1]),
        "n_months": {11: "eleven", 10: "ten", 12: "twelve"}[12 - len(P["missing_months_last"])],
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    v.update({k: L[k] for k in ("bls_applied", "bls_received", "bls_inelig", "cn_elig", "cn_drop", "cn_weeks",
                                "cn_mix", "solv_now", "solv_2020", "nc_from", "nc_to", "nc_wba0", "nc_wba1",
                                "ccw", "hmm", "crck", "dk_emp", "dk_sal", "gruber")})
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
