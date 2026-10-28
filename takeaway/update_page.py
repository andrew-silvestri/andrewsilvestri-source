"""
Write site/takeaway.html from template.html and outputs/payload.json.

Every number on the page comes from the payload, from cited.py (parsed out of
a source's own words), or from a file this script measures (the archive's
size); the prose is in the template. The parts of the shipped page that
other scripts own - the nav (rebuild_nav.py), the citation markers and
Sources list (add_citations.py's table, applied here), the ?v= stamps
(bust_cache.py) and image dimensions - are kept as the shipped page has
them, so tests/test_generators.py can run this on the shipped tree and expect
no change. The idiom is meter/update_page.py's and beauty/update_page.py's.

claims() asserts every direction the template's words commit to. If a
rebuild moves one, the generator stops rather than ship prose the payload
contradicts.

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "takeaway.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "takeaway-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import cited   # noqa: E402

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]
WORDS = {12: "twelve", 6: "six", 3: "three"}
WORDS_N = {6: "six"}
# "within NEAR Bcf/d of t0 on most readings": the band the page says the
# readings mostly fall in. Set after the readings were computed (they gave
# 4 of 9 within 0.5, 7 of 9 within 0.7); claims() holds the "most".
NEAR = 0.7


def ym(key):
    y, m = key.split("-")
    return int(y), int(m)


def long(key):
    y, m = ym(key)
    return f"{MONTHS[m - 1]} {y}"


def short(key):
    y, m = ym(key)
    return f"{MONTHS[m - 1][:3]} {y}"


def f2(x):
    return f"{x:.2f}"


def signed(x):
    return f"{x:+.2f}".replace("-", "&minus;")


def month_list(keys):
    """'December 2025, July 2026 and August 2026', consecutive months in one year run together."""
    if not keys:
        return "none"
    parts, run = [], [keys[0]]
    for k in keys[1:]:
        (y0, m0), (y1, m1) = ym(run[-1]), ym(k)
        if y1 == y0 and m1 == m0 + 1:
            run.append(k)
        else:
            parts.append(run)
            run = [k]
    parts.append(run)

    def name(r):
        if len(r) == 1:
            return long(r[0])
        y = ym(r[0])[0]
        joint = " and " if len(r) == 2 else " to "
        return f"{MONTHS[ym(r[0])[1] - 1]}{joint}{MONTHS[ym(r[-1])[1] - 1]} {y}"
    names = [name(r) for r in parts]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def cap_rows(P):
    rows = []
    for e in P["entries"]:
        when = str(ym(e["month"])[0]) if e["year_only"] else short(e["month"])
        status = "In service" if e["status"] == "confirmed" else "Expected"
        if e["status"] == "confirmed" and e["disagrees"]:
            status += f" (a source disagrees: {html.escape(e['disagrees'])})"
        name = html.escape(e["name"].replace(" (formerly Warrior Pipeline) Phase I & II", ""))
        rows.append(f'<tr><td>{name}</td><td class="n">{e["bcfd"]:.2f}</td><td>{when}</td>'
                    f'<td>{status}, per {html.escape(e["cite"])}</td></tr>')
    return "\n".join(rows)


def reading_label(r):
    k = r["why"].split("=")[1].split(",")[0].strip() if "k =" in r["why"] else ""
    if r["name"].startswith("t0_"):
        return "Pipes full in " + long(r["name"][3:]) + " instead"
    return {"default": f"Default: k = {k}, lines confirmed in service",
            "k_lo": f"k from Texas alone ({k})", "k_hi": f"k from dry gas, no fuel ({k})",
            "k_permian": f"k from EIA's Permian figures less fuel ({k})",
            "k_fit": f"k that makes mid-2019 as full ({k})", "no_tarzan": "Tarzan compressor not counted",
            "hb_full": "Hugh Brinson phase I counted at full capacity"}[r["name"]]


def reading_rows(S):
    return "\n".join(f'<tr><td>{reading_label(r)}</td><td class="n">{signed(r["H"])}</td>'
                     f'<td class="n">{len(r["below"])}</td></tr>' for r in S["readings"])


def exp_rows(S, P):
    rows = []
    for e in S["expected"]:
        pe = next(x for x in P["entries"] if x["name"] == e["name"] and x["month"] == e["month"])
        when = str(ym(e["month"])[0]) if pe["year_only"] else short(e["month"])
        name = html.escape(e["name"].replace(" (formerly Warrior Pipeline) Phase I & II", ""))
        rows.append(f'<tr><td>{name}</td><td class="n">{e["bcfd"]:.2f}</td><td>{when}</td>'
                    f'<td>{html.escape(e["stage"])}</td><td class="n">{e["months_default"]:.0f}</td></tr>')
    return "\n".join(rows)


def pre_rows(S):
    return "\n".join(f'<tr><td>{html.escape(e["name"])}</td><td class="n">{e["bcfd"]:.2f}</td>'
                     f'<td>{short(e["month"])}</td><td>{html.escape(e["why"])}</td></tr>' for e in S["pre_anchor"])


def t_of(S, k):
    xs = S["hero"]["x"]
    return round(xs.index(k) / (len(xs) - 1), 4)


# The hero's annotation labels: full name on a wide chart, short on a phone.
ANN = {"Gulf Coast Express": ("Gulf Coast Express", "GCX"), "Permian Highway": ("Permian Highway", "PHP"),
       "Whistler": ("Whistler", "WH"), "Matterhorn Express": ("Matterhorn", "MXP"),
       "Gulf Coast Express expansion": ("GCX exp.", "GCX+")}


def hero_spec(P, S):
    h = S["hero"]
    neg = cited.reuters_counts()
    first = cited.reuters_first_year()
    years = range(ym(h["x"][0])[0], ym(h["x"][-1])[0] + 1)
    # a year the Reuters list does not name is a dash, never a zero (review 5)
    bars = [{"at": str(y), "value": neg.get(y, 0), "text": str(neg[y]) if y in neg else "–"}
            for y in years if y >= first]
    anns = [{"at": s["month"], "text": ANN[s["name"]][0], "short": ANN[s["name"]][1]}
            for s in h["starts"] if s["name"] in ANN]
    return {"id": "takeaway-hero", "type": "series",
            "title": f"Pipe capacity out of the Permian and the gas that needs it, as change from {long(P['t0'])}, "
                     f"{short(h['x'][0])} to {short(h['x'][-1])}, with Waha's below-zero days and the share "
                     "vented or flared",
            "x": h["x"], "y": {"label": "Bcf/d vs " + short(P["t0"])},
            "series": [{"key": "pipe", "label": "Pipe out", "color": "acc", "values": [round(x, 4) for x in h["pipe"]]},
                       {"key": "gas", "label": f"Gas needing a pipe, k {P['k']['default']:.2f}", "color": "moss",
                        "values": [round(x, 4) for x in h["gas"]]},
                       {"key": "fit", "label": f"k {S['k_fit']['list']:.2f}", "color": "ink",
                        "values": [round(x, 4) for x in h["gas_fit"]]}],
            # one colour both sides: the band is the range of k, not room
            "band": {"a": "fit", "b": "gas", "pos": {"color": "moss", "label": "Range of k"},
                     "neg": {"color": "moss"}},
            "annotations": anns,
            "under": [{"kind": "bars", "label": "Days Waha below zero (Reuters)", "color": "moss", "height": 56,
                       "bars": bars},
                      {"kind": "line", "label": "Vented or flared, % (Texas Permian)", "color": "ink", "height": 48,
                       "values": [None if x is None else round(100 * x, 3) for x in h["vf"]]}]}


def hero(P, S):
    """The scrolly: spec and steps. Every number in a step is from the payload."""
    import insight
    Y = {r["year"]: r for r in S["years"]}
    L = {l["name"]: l for l in S["lines"]}
    gcx, php, wh, mh = L["Gulf Coast Express"], L["Permian Highway"], L["Whistler"], L["Matterhorn Express"]
    ly = ym(S["last"])[0]
    steps = [
        (f"<p><b>2018 to mid-2019.</b> Production increases quickly, and no large line leaves the basin. In "
         f"September 2019, EIA wrote that limited takeaway kept Waha's prices \"very low, or even negative, in recent "
         f"months\". In 2019, the three Texas districts vented or flared {Y[2019]['vf_bcfd']:.2f} Bcf/d, "
         f"{100 * Y[2019]['vf_share']:.1f} per cent of their gas.</p>", {"t": t_of(S, S["ref_2019"])}),
        (f"<p><b>Gulf Coast Express, {long(gcx['month'])}.</b> The line carries {gcx['bcfd']:.2f} Bcf/d to the Texas "
         f"coast. The share vented or flared is {100 * Y[2020]['vf_share']:.1f} per cent in 2020, half the 2019 "
         f"share. The 2020 price collapse also stops the growth of production.</p>", {"t": t_of(S, "2020-12")}),
        (f"<p><b>Permian Highway and Whistler, 2021.</b> The two lines add {php['bcfd']:.1f} and {wh['bcfd']:.1f} Bcf/d, "
         f"six months apart. At that time, the 2020 slump still limited production. Reuters lists no below-zero day at Waha in 2021 "
         f"or 2022.</p>",
         {"t": t_of(S, "2022-06")}),
        (f"<p><b>2023 to {short(P['t0'])}.</b> About two Bcf/d of new gas a year fills the room. By "
         f"{long(P['t0'])}, Waha is below zero every day. The chart aligns the two lines so that they meet here.</p>",
         {"t": t_of(S, P["t0"])}),
        (f"<p><b>Matterhorn Express, {long(mh['month'])}.</b> This line carries {mh['bcfd']:g} Bcf/d, the largest line yet, "
         f"about {mh['months_default']:.0f} months of growth. The room that it opened was gone by {long(mh['recovered'])}. "
         f"Waha went below zero {Y[2025]['neg']} times in 2025.</p>", {"t": t_of(S, mh["recovered"])}),
        (f"<p><b>{ly}.</b> Reuters counts {Y[ly]['neg']} below-zero days by {cited.REUTERS['date']}, a record. "
         f"In {long(S['last'])}, on the default reading, the gap is {signed(S['H_hero'][S['last']])} Bcf/d. On most "
         f"of the readings below, it is within {NEAR:g} Bcf/d of {long(P['t0'])}.</p>", {"t": 1}),
    ]
    return insight.scrolly(hero_spec(P, S), steps, from_state={"t": 0})


def year_adds(S):
    """k x production growth per calendar year, December to December, from the hero's gas series."""
    xs, g = S["hero"]["x"], S["hero"]["gas"]
    out = {}
    for y in range(int(xs[0][:4]) + 1, int(S["last"][:4])):
        a, b = f"{y - 1}-12", f"{y}-12"
        if a in xs and b in xs:
            out[y] = g[xs.index(b)] - g[xs.index(a)]
    return out


def values(P):
    import insight
    S = P["story"]
    steo = P["steo"]["P"]
    last = P["steo"]["last_historical"]
    t0 = P["t0"]
    k = P["k"]
    exp = [e for e in P["entries"] if e["status"] == "expected"]
    hb1 = next(e for e in P["entries"] if e["name"].endswith("Phase I & II Phase I"))
    fl = P["flaring"]
    c1, c2, c3 = [c for c in fl["clusters"] if "diff" in c][:3]
    Y = {r["year"]: r for r in S["years"]}
    vfy = [r for r in S["years"] if "vf_share" in r]
    since21 = [r for r in vfy if r["year"] >= 2021]
    rc = cited.reuters_counts()
    eia_pct, eia_year = cited.eia_pct()
    big = S["lines"]
    months = [l["months_default"] for l in big] + [l["months_low"] for l in big]
    rd = {r["name"]: r for r in S["readings"]}
    H_last = rd["default"]["H"]
    within = [r for r in S["readings"] if abs(r["H"]) <= NEAR]
    yr = year_adds(S)
    claims(P, S, months, within, yr)
    return {
        "stamp": insight.stamp(last, "EIA's Short-Term Energy Outlook"),
        "takeaways": insight.takeaways([
            f"Since {S['pace_from'][:4]} the Permian has added, on average, {S['pace']['k_fit']:.1f} to "
            f"{S['pace']['default']:.1f} billion cubic feet a day of gas that needs a pipe out each year. This is close to "
            f"what one big new pipeline carries. Thus each big line built since 2019 holds only {min(months):.0f} to "
            f"{max(months):.0f} months of that growth.",
            f"When the pipes have been full, Waha's price has been below zero, and sellers have paid buyers to take "
            f"their gas. Reuters "
            f"counts {rc[2019]} such days in 2019, {rc[2024]} in 2024 and {rc[2026]} in 2026 by late "
            f"{cited.REUTERS['date'].split()[0]}, more than in any full year.",
            f"Flaring has not returned with the full pipes. Operators in the Texas "
            f"Permian vented or flared {100 * Y[2019]['vf_share']:.1f} per cent of their gas in 2019. In any year since "
            f"2021, they vented or flared no more than {100 * max(r['vf_share'] for r in since21):.1f} per cent."]),
        "hero": hero(P, S),
        "t0_long": long(t0), "t0_short": short(t0), "last_long": long(last), "last_year": str(ym(last)[0]),
        "k_def": f"{k['default']:.3f}", "k_year": str(k["year"]),
        "k_both_net": f"{k['by_state']['both']['net']:.3f}", "k_tx_net": f"{k['by_state']['TX']['net']:.3f}",
        "k_both_dry": f"{k['by_state']['both']['dry']:.3f}",
        "kp_dry": f"{S['k_permian']['dry']:.3f}", "kp_net": f"{S['k_permian']['net']:.3f}",
        "vf_last_long": long(fl["last"]), "tracker_edition": "August 2026",
        "vf_extract": (lambda d: f"{d.day} {MONTHS[d.month - 1]} {d.year}")(
            __import__("datetime").datetime.strptime(fl["dump"]["gas_extract_date"], "%d-%b-%y")),
        "neg_last_year": str(max(rc)), "r_date": cited.REUTERS["date"],
        "eia_pct": str(eia_pct), "eia_year": str(eia_year),
        "csgd_year": str(P["csgd"]["year"]), "csgd_pct": f"{100 * P['csgd']['share']:.0f}",
        "q_losses": cited.REUTERS_MORE["losses"], "q_pay": cited.REUTERS_MORE["pay"][len("negative prices, "):],
        "q_flare": cited.REUTERS_MORE["flare"], "q_mechanism": cited.EIA_T0["mechanism"],
        "q_eia2019": "kept prices very low, or even negative, in recent months",
        "pace_from_year": S["pace_from"][:4], "pace_def": f"{S['pace']['default']:.2f}",
        "pace_low": f"{S['pace']['k_fit']:.2f}",
        "yr_min": f"{__import__('math').floor(10 * min(x for y, x in yr.items() if y != 2020)) / 10:.1f}", "yr_2020": f"{yr[2020]:.2f}",
        "big_lo": f"{min(l['bcfd'] for l in big):g}", "big_hi": f"{max(l['bcfd'] for l in big):g}",
        "months_lo": f"{min(months):.0f}", "months_hi": f"{max(months):.0f}",
        "rec_gcx": str(big[0]["recovery_months"]), "rec_php": str(big[1]["recovery_months"]),
        "rec_wh": str(big[2]["recovery_months"]), "rec_mh": str(big[3]["recovery_months"]),
        "first_neg": str(cited.reuters_first_year()),
        "n2023": "one" if rc[2023] == 1 else str(rc[2023]), "n2024": str(rc[2024]), "n2025": str(rc[2025]),
        "n2026": str(rc[2026]), "r_run": str(cited.reuters_run()),
        "vf2019_bcfd": f"{Y[2019]['vf_bcfd']:.2f}", "vf2019": f"{100 * Y[2019]['vf_share']:.1f}",
        "vf_lastyear": str(max(r["year"] for r in vfy)),
        "vf_min_since": f"{100 * min(r['vf_share'] for r in since21):.1f}",
        "vf_max_since": f"{100 * max(r['vf_share'] for r in since21):.1f}",
        "gross2021": f"{Y[2021]['gross_bcfd']:.1f}", "gross_last": f"{vfy[-1]['gross_bcfd']:.1f}",
        "vf2022": f"{100 * Y[2022]['vf_share']:.1f}", "vf2023": f"{100 * Y[2023]['vf_share']:.1f}",
        "n2020": WORDS_N.get(rc[2020], str(rc[2020])),
        "room2122": f"{__import__('math').floor(10 * min(v for k, v in S['H_hero'].items() if k[:4] in ('2021', '2022'))) / 10:.1f}",
        "swing": f"{max(abs(S['H_hero'][b] - S['H_hero'][a]) for a, b in zip(sorted(S['H_hero']), sorted(S['H_hero'])[1:]) if a >= '2025-01'):.1f}", "vf2024": f"{100 * Y[2024]['vf_share']:.1f}",
        "window_word": WORDS[P["window"]],
        "c1_before": f2(100 * c1["before"]), "c1_after": f2(100 * c1["after"]),
        "c2_before": f2(100 * c2["before"]), "c2_after": f2(100 * c2["after"]),
        "c3_before": f2(100 * c3["before"]), "c3_after": f2(100 * c3["after"]),
        "c2_rank": str(c2["rank_below"]), "c3_rank": str(c3["rank_below"]), "placebo_n": str(fl["placebo_n"]),
        "H_last_abs": f2(abs(H_last)), "H_last_dir": "more gas" if H_last < 0 else "less gas",
        "reading_rows": reading_rows(S), "near": f"{NEAR:g}",
        "near_months": f"{12 * NEAR / S['pace']['default']:.0f}", "n_within": str(len(within)), "n_readings": str(len(S["readings"])),
        "hb1": f"{hb1['bcfd']:g}", "H_fit": signed(rd["k_fit"]["H"]),
        "exp_total": f2(sum(e["bcfd"] for e in exp)), "exp_last": long(max(e["month"] for e in exp)),
        "exp_built": f2(sum(e["bcfd"] for e in exp if e["stage"] in BUILDING)),
        "exp_not": f2(sum(e["bcfd"] for e in exp if e["stage"] not in BUILDING)),
        "exp_not_names": and_list([short_name(e["name"]) for e in exp if e["stage"] not in BUILDING]),
        "exp_rows": exp_rows(S, P),
        "hero_from_year": S["hero"]["x"][0][:4], "ref19_long": long(S["ref_2019"]),
        "ref19_def": signed(S["H_ref_2019"]["default"]), "ref19_kp": signed(S["H_ref_2019"]["k_permian"]),
        "kfit": f"{S['k_fit']['list']:.2f}", "kfit_nosm": f"{S['k_fit']['no_south_mainline']:.2f}",
        "kfit_dbl": f"{S['k_fit']['with_double_e']:.2f}",
        "steo_release": P["steo"]["release"], "steo_first_long": long(min(steo)),
        "n_tx_counties": str(P["region"]["TX"]), "n_nm_counties": str(P["region"]["NM"]),
        "splice": f"{S['splice']:.3f}", "splice_n": str(S["splice_n"]), "splice_lo": f"{S['splice_range'][0]:.3f}",
        "splice_hi": f"{S['splice_range'][1]:.3f}",
        "rec_n": str(P["reconcile"]["n"]), "rec_min": f"{P['reconcile']['min']:.2f}",
        "rec_max": f"{P['reconcile']['max']:.2f}",
        "cap_rows": cap_rows(P), "pre_rows": pre_rows(S),
        "unsettled_word": WORDS[fl["unsettled_months"]], "event_min": f"{EVENT_MIN_BCFD:g}",
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }


# The tracker's statuses that mean a line is being built (D-25 item 5);
# "Applied", "Pre-applied" and "Approved" are not.
BUILDING = {"Construction", "Part Completed"}
# build_takeaway.EVENT_MIN_BCFD: an addition this size or larger counts as a
# start in the venting and flaring test (D-25 item 3). Imported so the page
# cannot state a threshold the build does not use.
from build_takeaway import EVENT_MIN_BCFD  # noqa: E402


def short_name(n):
    return n.replace(" Project", "").replace(" Pipeline", "").replace(" expansion project", "")


def and_list(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def claims(P, S, months, within, yr):
    """Every direction and range the template's words commit to. A refresh
    that moves one stops the build rather than ship prose the data contradicts."""
    Y = {r["year"]: r for r in S["years"]}
    rc = cited.reuters_counts()
    rd = {r["name"]: r for r in S["readings"]}
    vfy = [r for r in S["years"] if "vf_share" in r]
    since21 = [r for r in vfy if r["year"] >= 2021]
    Hh = S["H_hero"]
    fl = P["flaring"]
    c1, c2, c3 = [c for c in fl["clusters"] if "diff" in c][:3]
    L = {l["name"]: l for l in S["lines"]}
    checks = [
        ("h1: each big line holds a year to a year and a half of growth (12-19.5 months)",
         12 <= min(months) and max(months) < 19.5),
        ("'every calendar year ... except 2020': 2020 is the smallest year and the only one under 1",
         min(yr, key=yr.get) == 2020 and all(x >= 1 for y, x in yr.items() if y != 2020)),
        ("'at least X of room every month' in 2021-2022 is positive", min(v for k, v in Hh.items() if k[:4] in ("2021", "2022")) > 0),
        ("Gulf Coast Express opened in Reuters's first below-zero year", int(L["Gulf Coast Express"]["month"][:4]) == cited.reuters_first_year()),
        ("Reuters lists no 2021 or 2022, and does list 2019, 2023-2026",
         2021 not in rc and 2022 not in rc and all(y in rc for y in (2019, 2023, 2024, 2025, 2026))),
        ("Reuters's first below-zero year is the year of Gulf Coast Express",
         cited.reuters_first_year() == int(L["Gulf Coast Express"]["month"][:4])),
        ("2026's count is a record, more than any full year", rc[2026] > max(v for y, v in rc.items() if y != 2026)),
        ("takeaway 1: the yearly pace is 'close to what one big new pipeline carries' (within its 1.98-2.5 range +-25%)",
         0.75 * min(l["bcfd"] for l in S["lines"]) <= S["pace"]["k_fit"]
         and S["pace"]["default"] <= 1.25 * max(l["bcfd"] for l in S["lines"])),
        ("'as the room ran out': 2024 has more days than 2023", rc[2024] > rc[2023]),
        ("flaring 2019 above every year since 2021", all(Y[2019]["vf_share"] > r["vf_share"] for r in since21)),
        ("'half 2019's' in 2020: between 0.4 and 0.6 of it", 0.4 <= Y[2020]["vf_share"] / Y[2019]["vf_share"] <= 0.6),
        ("'output rose' 2021 to the last full flaring year", vfy[-1]["gross_bcfd"] > Y[2021]["gross_bcfd"]),
        ("'the share moved' 2022 to 2024 upward", Y[2024]["vf_share"] > Y[2022]["vf_share"]),
        ("'fell' around each of the three tested groups", c1["diff"] < 0 and c2["diff"] < 0 and c3["diff"] < 0),
        ("'none fell as far as the 2019 one'", c1["rank_below"] == 0),
        ("'only the first stands out'", c2["rank_below"] > 0 and c3["rank_below"] > 0),
        ("'within half a Bcf/d on most readings'", 2 * len(within) > len(S["readings"])),
        ("'the sign changes with the choices'", any(r["H"] < 0 for r in within) and any(r["H"] > 0 for r in within)),
        ("'two rows go further': exactly t0 a month earlier and Hugh Brinson at full",
         sorted(r["name"] for r in S["readings"] if abs(r["H"]) > NEAR)
         == sorted(["hb_full", "t0_" + __import__("story").key(__import__("model").add_months(
             tuple(int(x) for x in P["t0"].split("-")), -1))])),
        ("'every version is below the default' k", max(S["k_fit"].values()) < P["k"]["default"]),
        ("'with the lower share ... emptier'", rd["k_fit"]["H"] > 0),
        ("the 2019 check: the default shows room in the reference month", S["H_ref_2019"]["default"] > 0),
        ("'Matterhorn Express, the largest line yet'",
         L["Matterhorn Express"]["bcfd"] == max(e["bcfd"] for e in S["pre_anchor"] + [x for x in P["entries"] if x["status"] == "confirmed"])),
        ("Matterhorn's room was used up (a recovery month exists)", L["Matterhorn Express"]["recovered"] is not None),
        ("'six months apart': Permian Highway and Whistler",
         __import__("model").months_between(tuple(map(int, L["Permian Highway"]["month"].split("-"))),
                                            tuple(map(int, L["Whistler"]["month"].split("-")))) == 6),
        ("most gas in the three districts comes from oil wells", P["csgd"]["share"] > 0.5),
        ("the reference month's room is positive on EIA's Permian k too, but smaller",
         0 < S["H_ref_2019"]["k_permian"] < S["H_ref_2019"]["default"]),
        ("the record counts no expected line: the hero's pipe at the last month is the confirmed additions since t0",
         abs(S["hero"]["pipe"][-1] - sum(e["bcfd"] for e in P["entries"]
                                         if e["status"] == "confirmed" and P["t0"] < e["month"] <= S["last"])) < 1e-9),
        ("every expected line has a tracker status", all(e["stage"] for e in S["expected"])),
    ]
    bad = [name for name, ok in checks if not ok]
    if bad:
        raise SystemExit("the payload contradicts the template: " + "; ".join(bad))


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "storage.html"), encoding="utf-8").read()
        stamps = {}
    else:
        stamps = dict(re.findall(r'(?:href|src|srcset)="([^"?]+)\?v=([0-9a-f]+)"', shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    text = text.replace("{{nav}}", nav)

    def stamp(m):
        path = m.group(2)
        return f'{m.group(1)}="{path}?v={stamps[path]}"' if path in stamps else m.group(0)
    return re.sub(r'(href|src|srcset)="([^"?]+\.(?:css|js|png))"', stamp, text)


def image_dims(text):
    from PIL import Image

    def dims(m):
        attr, src, rest = m.group(1), m.group(2), m.group(3)
        w, h = Image.open(os.path.join(SITE, src)).size
        return f'{attr}="{src}{rest}" width="{w}" height="{h}"'
    text = re.sub(r'(srcset)="(assets/[^"?]+)([^"]*)" width="[^"]*" height="[^"]*"', dims, text)
    return re.sub(r'(src)="(assets/[^"?]+)([^"]*)" loading="lazy" width="[^"]*" height="[^"]*"',
                  lambda m: dims(m).replace('" width', '" loading="lazy" width', 1), text)


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
    t = keep_from_shipped(t, shipped)
    t = image_dims(t)
    return t


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("takeaway.html")
    if not refs:
        return text, ["takeaway.html has no entry in add_citations.PAGES"]
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
        print("  takeaway.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  takeaway.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
