"""
Write site/lead.html from template.html and outputs/payload.json.

Every number on the page comes from the payload, from a figure read out of an opened source at render time
(sources.text: Lanphear's slope, the Dunedin and Flynn-effect figures, Larsen's per-child mean), or from a
file this script measures (the archive's size). The prose is in the template. The parts other scripts own -
the nav (rebuild_nav.py), the citation markers and Sources list (add_citations.py's table, applied here) and
the ?v= stamps (bust_cache.py) - are kept as the shipped page has them, so tests/test_generators.py can run
this on the shipped tree and expect no change. The idiom is ethane/update_page.py's.

The hero is a kit "strip" chart, one bin per birth year: the kit's "series" chart reads its position out
as a month, and these are years.

claims() asserts every direction and range the template's words commit to ("the birth year with the
largest loss", "about the loss of the American peak birth years", "more than two decades of that rise",
"by a factor of more than two"). If a rebuild moves one, the generator stops rather than ship prose the
payload contradicts.

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "lead.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "lead-code.zip")
NAV_FROM = os.path.join(SITE, "longevity.html")   # first build only: a page in the same nav group
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def pct(x, k=1):
    return f"{100 * x:.{k}f}"


def read(name, pat, group=1):
    """A figure read out of a source's text at render time."""
    import sources as S
    m = re.search(pat, S.text(name))
    if not m:
        raise SystemExit(f"{name}: no match for {pat!r}")
    return m.group(group)


def lit():
    return {
        "lan_beta": read("lanphear2005_pmc.xml", r"Concurrent -4\.66 \(-5\.72 to -3\.60\) -(2\.70) \(-3\.74 to -1\.66\)"),
        "lan_floor": read("lanphear2005_pmc.xml", r"increase in concurrent blood lead levels from (2\.4) to 30"),
        "lan_early": read("lanphear2005_pmc.xml", r"Early childhood -3\.57 \(-4\.86 to -2\.28\) -(2\.04) \(-3\.27 to -0\.81\) "
                                                  r"4\.1-34\.8"),
        "reuben": read("reuben2017_pubmed.txt", r"each 5-µg/dL higher level of blood lead in childhood was associated "
                                                r"with a (1\.61)-point lower score"),
        "flynn": read("trahan2014_pubmed.txt", r"the meta-analytic mean was (2\.31), 95% CI"),
        "flynn_n": read("trahan2014_pubmed.txt", r"Across (\d+) studies"),
        "w_child": read("larsen2023.pdf", r"average IQ loss over these first years of life is (\d\.\d) \(95% CI"),
        "crump_beta": read("larsen2023.pdf", r"Crump and colleagues13 with β=(3\.246)"),
    }


# ------------------------------------------------------------------ hero ---
def hero_spec(P):
    U = P["us"]
    bins = []
    for r in U["per_year"]:
        c = r["cohort"]
        bins.append({"a": c, "b": c + 1, "n": round(r["mean"], 3),
                     "mid": round(r["mean"], 3) if 1951 <= c <= 1980 else 0,
                     "peak": round(r["mean"], 3) if 1966 <= c <= 1970 else 0})
    return {"id": "lead-hero", "type": "strip",
            "title": "Mean IQ points lost to lead in early childhood, by year of birth, people alive in the United "
                     "States in 2015, from McFarland, Hauer and Reuben (2022)",
            "bins": bins, "y": {"label": "IQ points lost, mean"}, "x": {"label": "year of birth", "years": True},
            "lights": [{"key": "mid", "color": "moss", "state": "m"},
                       {"key": "peak", "color": "acc", "state": "p"}],
            "range": {"lo": 1940, "hi": 1976, "label": "before 1976: predicted from gasoline", "state": "r"},
            "marks": [{"at": 1975, "label": "1975: unleaded cars", "state": "k"},
                      {"at": 1986, "label": "1986: 0.1 g/gallon", "state": "k"}]}


def hero(P, v):
    import insight
    U = P["us"]
    y = {r["cohort"]: r for r in U["per_year"]}
    mid = f"{100 * U['mid_century_share']:.0f}"
    steps = [
        (f"<p><b>One bar for each birth year.</b> Each bar's height is the mean number of IQ points that the people born "
         f"in that year lost to lead as small children. Before 1976 (shaded), their blood lead is "
         f"predicted from the gasoline series; from 1976 it is measured, with the years between surveys filled in.</p>", {"t": 1, "r": 1}),
        (f"<p><b>The peak: born 1966 to 1970.</b> This group lost {v['peak5']} points each on average. For those "
         f"born in {U['peak1']['cohort']}, the mean was {U['peak1']['mean']:.1f} points, the largest of any birth year. And in "
         f"{P['gasoline']['peak_year']}, the makers of the gasoline additive used more lead than in any other "
         f"year: {v['gpeak_t']} metric tons.</p>", {"t": 1, "p": 1}),
        (f"<p><b>Born 1951 to 1980: {mid} percent of the total.</b> Counted in people rather than bars, these thirty "
         f"birth years carry "
         f"{U['mid_century']['points'] / 1e6:,.0f} million of the {v['total_m']} million points.</p>",
         {"t": 1, "m": 1}),
        (f"<p><b>The fall.</b> From 1975, new cars needed unleaded gasoline, and from 1986 the standard for leaded "
         f"gasoline was 0.1 gram of lead a gallon. The mean loss was {y[1980]['mean']:.1f} points for the people "
         f"born in 1980, {y[1990]['mean']:.1f} for 1990 and {y[2000]['mean']:.2f} for 2000. The dip at 1975 is an echo: it "
         f"follows a dip in the gasoline series that year, which the model carries into blood lead.</p>",
         {"t": 1, "k": 1}),
    ]
    return insight.scrolly(hero_spec(P), steps, from_state={"t": 0})


def gas_spec(P):
    G = P["gasoline"]
    bins = [{"a": r["year"], "b": r["year"] + 1, "n": round(r["tonnes"] / 1000, 1),
             "pk": round(r["tonnes"] / 1000, 1) if r["year"] == G["peak_year"] else 0} for r in G["series"]]
    return {"id": "lead-gas", "type": "strip",
            "title": "Lead used by U.S. makers of the gasoline antiknock additive, thousand tonnes a year, "
                     f"{G['first']} to {G['last']}, U.S. Bureau of Mines",
            "bins": bins, "y": {"label": "thousand tonnes of lead"}, "x": {"label": "year", "years": True},
            "lights": [{"key": "pk", "color": "acc", "state": "p"}]}


def gas_chart(P):
    import insight
    G = P["gasoline"]
    steps = [(f"<p><b>{G['first']} to {G['last']}.</b> Lead in the additive reached its maximum in "
              f"{G['peak_year']}; by 1986 it was down to {G['t1986']:,.0f} metric tons.</p>", {"t": 1, "p": 1})]
    return insight.scrolly(gas_spec(P), steps, from_state={"t": 0})


# ---------------------------------------------------------------- tables ---
def cohort_rows(P):
    rows = []
    for g in P["us"]["fives"]:
        rows.append(f"<tr><td>{g['from']}&ndash;{str(g['to'])[2:]}</td><td>{g['pop'] / 1e6:,.1f}</td>"
                    f"<td>{pct(g['ge5'], 0)}%</td><td>{pct(g['ge10'], 0)}%</td><td>{g['mean']:.1f}</td></tr>")
    return "\n".join(rows)


def blood_rows(P):
    def num(x):
        return f"{x:g}"
    return "\n".join(f"<tr><td>{r['start']} to {r['end']}</td><td>{num(r['median'])}</td><td>{num(r['p95'])}</td></tr>"
                     for r in P["blood"]["rows"])


def curve_rows(P):
    C = P["curves"]
    names = {"paper": "McFarland and colleagues, as published (no loss below 5 µg/dL)",
             "lanphear_early": "Lanphear and colleagues (2005), early-childhood blood lead, from 4.1 µg/dL",
             "lanphear": "Lanphear and colleagues (2005), blood lead at the IQ test, from 2.4 µg/dL",
             "crump": "Crump and colleagues (2013), no threshold"}
    return "\n".join(f"<tr><td>{names[k]}</td><td>{C[k]['points'] / 1e6:,.0f}</td><td>{C[k]['peak5_mean']:.1f}</td></tr>"
                     for k in ("paper", "lanphear_early", "lanphear", "crump"))


def region_rows(P):
    return "\n".join(f"<tr><td>{r['name']}</td><td>{r['iq_m']:,.0f}</td><td>{r['lo']:,.0f} to {r['hi']:,.0f}</td></tr>"
                     for r in P["world"]["regions"])


# ---------------------------------------------------------------- claims ---
def claims(P, v, L):
    U, C, G, T, W = P["us"], P["curves"], P["gasoline"], P["tail"], P["world"]
    cal = G["above_cal"]
    c = [
        ("standfirst/hero: the peak five-year group is 1966-70", (U["peak5"]["from"], U["peak5"]["to"]) == (1966, 1970)),
        ("'the birth year with the largest loss' is the additive's peak year", U["peak1"]["cohort"] == G["peak_year"]),
        ("'by a factor of five': highest shown curve over lowest rounds to 5",
         round(C["crump"]["points"] / C["lanphear_early"]["points"]) == 5 and
         min(C[k]["points"] for k in ("paper", "lanphear", "lanphear_early", "crump")) == C["lanphear_early"]["points"] and
         max(C[k]["points"] for k in ("paper", "lanphear", "lanphear_early", "crump")) == C["crump"]["points"]),
        ("the early-childhood slope and floor are the article's", float(L["lan_early"]) == 2.04),
        ("'every child at or above 10 ug/dL' for 1966-70", round(P["us"]["fives"][5]["ge10"], 6) == 1.0 and
         (P["us"]["fives"][5]["from"], P["us"]["fives"][5]["to"]) == (1966, 1970)),
        ("'Anyone born ... between the 1950s and the 1970s ... carry most': 1951-80 share > 50%",
         U["mid_century_share"] > 0.5),
        ("'In every year from {cal_a} to {cal_b}': the above-calibration years are one unbroken run",
         cal == list(range(cal[0], cal[-1] + 1))),
        ("'more than two decades of that rise': 6 / Flynn rate > 2", 6 / float(L["flynn"]) > 2 and U["peak1"]["mean"] < 6.5),
        ("the 1975 dip: 1975 below 1974 and 1976 in both the bars and the gasoline series",
         [r["mean"] for r in U["per_year"] if r["cohort"] == 1975][0] <
         min(r["mean"] for r in U["per_year"] if r["cohort"] in (1974, 1976)) and
         {r["year"]: r["tonnes"] for r in G["series"]}[1975] <
         min(r["tonnes"] for r in G["series"] if r["year"] in (1974, 1976))),
        ("'six points': the peak birth years round to 6", round(U["peak5"]["mean"]) == 6 and round(U["peak1"]["mean"]) == 6),
        ("tail: the share above 130 falls and the share below 70 rises",
         T["share_1966_70"] < T["base_share"] and T["below70_1966_70"] > T["below70_base"]),
        ("hero step 4: losses fall 1980 > 1990 > 2000",
         [r["mean"] for r in U["per_year"] if r["cohort"] in (1980, 1990, 2000)] ==
         sorted([r["mean"] for r in U["per_year"] if r["cohort"] in (1980, 1990, 2000)], reverse=True)),
        ("the build's Lanphear slope and floor are the article's", float(L["lan_beta"]) == 2.70 and float(L["lan_floor"]) == 2.4),
        ("the build's Crump slope is Larsen's", float(L["crump_beta"]) == 3.246),
        ("blood lead fell between the first and last surveys", P["blood"]["last"]["median"] < P["blood"]["first"]["median"]),
        ("'the share above 130 decreases ... fewer people': at least a third fewer", T["fewer"] > 1 / 3),
    ]
    bad = [n for n, ok in c if not ok]
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    U, C, G, T, W, B = P["us"], P["curves"], P["gasoline"], P["tail"], P["world"], P["blood"]
    L = lit()
    v = {
        "peak5": f"{U['peak5']['mean']:.1f}", "total_m": f"{U['total'] / 1e6:,.0f}",
        "total_full": f"{U['total']:,.0f}", "per_person": f"{U['per_person']:.1f}", "alive": f"{U['alive_2015']:,}",
        "first_cohort": str(U["per_year"][0]["cohort"]), "last_cohort": str(U["per_year"][-1]["cohort"]),
        "b_first": f"{B['first']['median']:g}", "b_first_p": f"{B['first']['start']} to {B['first']['end']}",
        "b_last": f"{B['last']['median']:g}", "b_last_p": f"{B['last']['start']} to early {B['last']['end']}",
        "g_first": str(G["first"]), "g_last": str(G["last"]), "g_first_t": f"{G['series'][0]['tonnes']:,.0f}",
        "gpeak_t": f"{G['peak_tonnes']:,.0f}", "gpeak_y": str(G["peak_year"]), "g_fall": pct(G["fall_1970_1986"], 0),
        "cal_a": str(G["above_cal"][0]), "cal_b": str(G["above_cal"][-1]),
        "band1": f"{U['band_loss']['5-9.9']:.2f}",
        "tail_base": pct(T["base_share"]), "tail_shift": pct(T["share_1966_70"], 2), "tail_fewer": pct(T["fewer"], 0),
        "tail_pop": f"{T['pop'] / 1e6:.1f}", "tail_n_base": f"{round(T['n_base'], -4):,.0f}",
        "tail_n_shift": f"{round(T['n_shifted'], -4):,.0f}",
        "low_base": pct(T["below70_base"]), "low_shift": pct(T["below70_1966_70"]),
        "w_total": f"{W['total_m']:,.0f}", "w_lo": f"{W['lo']:,.0f}", "w_hi": f"{W['hi']:,.0f}",
        "w_lmic": f"{W['lmic_m']:,.0f}", "w_lmic_share": pct(W["lmic_share"]),
        "lan_beta": L["lan_beta"], "lan_early": L["lan_early"], "crump_peak": f"{C['crump']['peak5_mean']:.1f}",
        "born_before": f"{U['born_before'] / 1e6:.1f}", "reuben": L["reuben"], "flynn": L["flynn"], "flynn_n": L["flynn_n"], "w_child": L["w_child"],
        "stamp": (f"Data: estimates for the people alive in 2015; children's blood lead measured through March "
                  f"{B['last']['end']}; the world estimate for 2019. This page does not update."),
        "cohort_rows": cohort_rows(P), "blood_rows": blood_rows(P), "curve_rows": curve_rows(P),
        "region_rows": region_rows(P),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    v["takeaways"] = insight.takeaways([
        f"By the estimate of McFarland and colleagues, Americans born from 1966 to 1970 lost {v['peak5']} IQ points "
        f"each, on average, to lead in early childhood, more than any other group of birth years.",
        f"The total for the people alive in 2015 is {v['total_m']} million points, and the people born from 1951 to "
        f"1980 carry {100 * U['mid_century_share']:.0f} percent of it.",
        f"The total rests on one choice, the dose-response curve: applied to the same exposure, other published curves give "
        f"{C['lanphear_early']['points'] / 1e6:,.0f} million to {C['crump']['points'] / 1e9:.2f} billion points."])
    v["hero"] = hero(P, v)
    v["gas_chart"] = gas_chart(P)
    claims(P, v, L)
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(NAV_FROM, encoding="utf-8").read()
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
    refs = add_citations.PAGES.get("lead.html")
    if not refs:
        return text, ["lead.html has no entry in add_citations.PAGES"]
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
        print("  lead.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  lead.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
