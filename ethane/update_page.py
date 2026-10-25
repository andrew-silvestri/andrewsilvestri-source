"""
Write site/ethane.html from template.html and outputs/payload.json.

Every number on the page comes from the payload, from a quotation read out of an opened EIA article
(sources.py reads it at render time, so a quotation cannot drift from its file), or from a file this script
measures (the archive's size); the prose is in the template. The parts other scripts own - the nav
(rebuild_nav.py), the citation markers and Sources list (add_citations.py's table, applied here) and the ?v=
stamps (bust_cache.py) - are kept as the shipped page has them, so tests/test_generators.py can run this on
the shipped tree and expect no change. The idiom is uri/update_page.py's.

The page is archived (D-60, Andrew 2026-10-25: "make a note on the top/near the top that its an (Archived)
page"): the card under the h1 says what it is built from, through which month, and that it is not updated.

claims() asserts every direction and range the template's words commit to ("about 16 to 27 per cent",
"about what it was in 2010", "fell behind propane", ...). If a rebuild moves one, the generator stops rather
than ship prose the payload contradicts. quotes() refuses a quotation that forecasts (plan review 17).

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "ethane.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
MANIFEST = os.path.join(HERE, "data", "fetched.json")
ZIP = os.path.join(SITE, "downloads", "ethane-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
FORECAST = re.compile(r"\b(expect\w*|forecast\w*|will|project\w*)\b", re.I)


def mon(ym):
    y, m = ym.split("-")[:2]
    return f"{MONTHS[int(m) - 1]} {y}"


def long(iso):
    d = dt.date.fromisoformat(iso)
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def pct(x, k=1):
    return f"{100 * x:.{k}f}"


def art(P, name):
    return P["articles"][name]


def t_at(P, ym):
    xs = P["hero"]["x"]
    return xs.index(ym) / (len(xs) - 1)


# ------------------------------------------------------------ quotations ---
Q = {   # key: (article, pattern); group(1) if the pattern has one, else the whole match
    "q_stoves": ("eia_tie_18371.html", r"stoves and other gas-fueled appliances typically require natural gas to be within "
                                        r"a certain range of Btu content"),
    "q_places": ("eia_tie_18371.html", r"particularly evident in 2013 in the Marcellus Shale play in Pennsylvania, West "
                                       r"Virginia, and Ohio, as well as in the Bakken formation in North Dakota"),
    "q_unlike": ("eia_tie_28052.html", r"Unlike heavier natural gas plant liquids.such as propane, butanes, and natural "
                                       r"gasoline.significant amounts of ethane can be left in natural gas transported on "
                                       r"pipelines to natural gas customers"),
    "q_hub": ("eia_tie_64785.html", r"Mont Belvieu, Texas, (the main pricing hub for NGPLs)"),
    "q_costs": ("eia_tie_39712.html", r"recovered from natural gas (if ethane.s value is sufficient to cover the "
                                      r"additional costs to produce and distribute the ethane to markets)"),
    "q_wave": ("eia_tie_25632.html", r"Beginning in 2012, the availability of relatively inexpensive ethane encouraged a "
                                     r"wave of investments in ethane-consuming petrochemical plants and export facilities"),
    "q_crackers": ("eia_tie_39712.html", r"Several new petrochemical crackers were commissioned in the United States in 2018"),
    "q_2024_causes": ("eia_tie_64785.html", r"Increasing ethane recovery associated with natural gas production and "
                                            r"continued growth in the domestic and global petrochemical sectors drove these "
                                            r"increases"),
    "q_test": ("eia_ngwu_2019-02-14.html", r"Dry natural gas production increased much more slowly over this time period, "
                                           r"indicating that natural gas processors were extracting more, and consequently, "
                                           r"rejecting less ethane"),
    "q_closer": ("eia_tie_64785.html", r"when ethane prices and natural gas prices are closer, more ethane can be left in "
                                       r"the natural gas stream and sold for its heat value"),
    "q_estimates_full": ("eia_tie_16191.html", r"Estimates of ethane rejection volumes range between 200 and 400 Mbbl/d"),
}
PRICE_ROWS = [   # (article, [patterns quoted in order, joined with an ellipsis])
    ("eia_tie_9590.html", [r"It occurs when the price of ethane is low relative to natural gas, or when the cost of "
                           r"removing ethane is high relative to its price\."]),
    ("eia_tie_12291.html", [r"For the first six months of 2013, ethane prices averaged 27 cents per gallon, over 45% below "
                            r"the price for the first six months of 2012\.",
                            r"Ethane prices have been low compared with natural gas prices, prompting gas processors to "
                            r"leave it mixed in the natural gas stream"]),
    ("eia_tie_16191.html", [r"Ethane, which is currently priced below natural gas , is being left in the dry gas stream in "
                            r"large volumes by gas processors and sold as natural gas"]),
    ("eia_ngwu_2019-02-14.html", [r"Between late 2012 and mid-2017, ethane spot prices at the Mont Belvieu, Texas HGL "
                                  r"trading hub have been range-bound, staying within \$1\.00 per million British thermal "
                                  r"units \(MMBtu\) of the Henry Hub natural gas spot price on a heating-value equivalent "
                                  r"basis\."]),
    ("eia_tie_53659.html", [r"Since 2017, U\.S\. ethane prices have generally traded at a premium relative to natural gas "
                            r"prices, spurring natural gas plant operators to recover more ethane from raw natural gas "
                            r"streams\."]),   # not the $1.36: its paragraph is inconsistent (ledger 43)
    ("eia_tie_64785.html", [r"Ethane prices averaged under 20 cents per gallon \(gal\) for the year \(approximately \$3 per "
                            r"million British thermal units \[MMBtu\]\)",
                            r"the natural gas price at the Houston Ship Channel averaged \$1\.86/MMBtu in 2024",
                            r"when ethane prices and natural gas prices are closer, more ethane can be left in the natural "
                            r"gas stream and sold for its heat value\."]),
]


def tidy(s):
    """EIA's markup leaves a space before some commas (a link closed mid-sentence) and uses em dashes."""
    return re.sub(r" ([,.;:)])", r"\1", s).replace("—", "—")


def grab(name, pat):
    import sources as S
    m = S.quote(name, pat)
    s = tidy(m.group(1) if m.groups() else m.group(0))
    if FORECAST.search(s):
        raise SystemExit(f"{name}: a quotation that forecasts may not be quoted: {s!r}")
    return s


def heat_states():
    """TIE 18371: the two states' delivered gas, per cent above the national average, and the month's year."""
    import sources as S
    m = S.quote("eia_tie_18371.html", r"In July (20\d\d), natural gas delivered in West Virginia and North Dakota had "
                                      r"average heat contents (\d+)% and (\d+)% higher, respectively, than the national "
                                      r"average")
    return {"y_heat": m.group(1), "wv": m.group(2), "nd": m.group(3)}


def quotes():
    return {k: html.escape(grab(n, p), quote=False) for k, (n, p) in Q.items()}


def price_rows(P):
    rows = []
    for name, pats in PRICE_ROWS:
        d, _title = art(P, name)
        what = " &hellip; ".join(html.escape(grab(name, p), quote=False) for p in pats)
        kind = "Natural Gas Weekly Update" if "ngwu" in name else "Today in Energy"
        rows.append(f'<tr><td>{kind}, {long(d)}</td><td>&ldquo;{what}&rdquo;</td></tr>')
    return "\n".join(rows)


# ------------------------------------------------------------------ hero ---
def hero_spec(P):
    h = P["hero"]
    return {"id": "ethane-hero", "type": "series",
            "title": "Ethane's share of the liquids U.S. gas plants produce, per cent, by month, with ethane and "
                     "propane production below in million barrels a day",
            "x": h["x"], "y": {"label": "ethane share, %", "min": 30},
            "series": [{"key": "share", "label": "Ethane, share of all plant liquids", "color": "acc",
                        "values": h["share"]}],
            # million, not thousand, barrels a day: a panel's top tick sits in the plot's left margin, which is
            # sized for the share's labels ("45.0"), and "4,000" overflowed it (preview, 2026-10-25)
            "under": [{"kind": "line", "label": "Ethane, million barrels a day", "color": "acc",
                       "values": [round(v / 1000, 3) for v in h["eth"]], "height": 72},
                      {"kind": "line", "label": "Propane, million barrels a day", "color": "ink",
                       "values": [round(v / 1000, 3) for v in h["pro"]], "height": 72}],
            # dated by EIA's articles; no "record month" (ledger 24: on the share line it read as a record share)
            "annotations": [{"at": P["articles"]["eia_tie_9590.html"][0][:7], "text": "EIA reports rejection",
                             "short": "rejection"},
                            {"at": P["articles"]["eia_tie_16191.html"][0][:7],
                             "text": f"{P['rejection_2014']['lo']}-{P['rejection_2014']['hi']}k b/d estimate",
                             "short": "estimate"},
                            {"at": P["first_ship"][:7], "text": "first ship exports", "short": "ships"}]}


def hero(P):
    import insight
    A, t = P["annual"], P["ttm"]
    r = P["rejection_2014"]
    lo_y = P["low_share"][0]
    steps = [
        (f"<p><b>2009 to 2012: before the fall.</b> Ethane was {pct(A['2010']['share'])} per cent of the liquids "
         f"U.S. gas plants produced in 2010 and {pct(A['2012']['share'])} per cent in 2012.</p>",
         {"t": t_at(P, "2012-12")}),
        (f"<p><b>2013 to {lo_y}: ethane fell behind.</b> From 2012 to {lo_y} propane rose from "
         f"{A['2012']['pro']:,.0f} to {A[str(lo_y)]['pro']:,.0f} thousand barrels a day and ethane only from "
         f"{A['2012']['eth']:,.0f} to {A[str(lo_y)]['eth']:,.0f}; ethane's share fell to {pct(P['low_share'][1])} per "
         f"cent in {lo_y}.</p>", {"t": t_at(P, f"{lo_y}-12")}),
        (f"<p><b>2016 to 2019: more of it taken out.</b> The first ship exports left in {mon(P['first_ship'])}, and new "
         f"petrochemical plants came on. Ethane production rose {pct(A['2018']['eth'] / A['2017']['eth'] - 1, 0)} per "
         f"cent in 2018 alone, and its share climbed back to {pct(A['2018']['share'])} per cent.</p>",
         {"t": t_at(P, "2019-12")}),
        (f"<p><b>Since 2020: back near 2010's share.</b> Over the twelve months to {mon(t['to'])}, plants "
         f"produced {t['eth'] / 1000:.2f} million barrels a day of ethane, {pct(t['share'])} per cent of the liquids, "
         f"against {pct(A['2010']['share'])} per cent in 2010.</p>", {"t": 1}),
    ]
    return insight.scrolly(hero_spec(P), steps, from_state={"t": 0})


# ---------------------------------------------------------------- claims ---
def claims(P, v):
    A, r, t, g = P["annual"], P["rejection_2014"], P["ttm"], P["growth"]
    c = [
        ("standfirst 'about {plo} to {phi} per cent' is the payload's range, rounded",
         v["plo"] == f"{100 * r['frac_lo']:.0f}" and v["phi"] == f"{100 * r['frac_hi']:.0f}"),
        ("takeaway 2 'about what it was in 2010': latest twelve months within one point of 2010",
         abs(t["share"] - A["2010"]["share"]) < 0.01),
        ("hero step 2 'ethane fell behind': propane grew faster than ethane 2012 to the low year",
         A[str(P["low_share"][0])]["pro"] / A["2012"]["pro"] > A[str(P["low_share"][0])]["eth"] / A["2012"]["eth"]),
        ("the low year of the share is 2013 to 2016", 2013 <= P["low_share"][0] <= 2016),
        ("takeaway 3: ethane grew faster than the other liquids since 2015", g["eth"] > g["other"]),
        ("hero step 3 'climbed back': 2018's share above the low year's", A["2018"]["share"] > P["low_share"][1]),
        ("'EIA used the same measure': its 42 and 34 are the series' 2010 and 2015, rounded",
         round(100 * A["2010"]["share"]) == 42 and round(100 * A["2015"]["share"]) == 34),
        ("'the record year' 2024 was the highest when EIA wrote",
         A["2024"]["eth"] == max(x["eth"] for y, x in A.items() if y <= "2024")),
    ]
    bad = [n for n, ok in c if not ok]
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    A, r, t, g = P["annual"], P["rejection_2014"], P["ttm"], P["growth"]
    fetched = max(x["fetched"] for x in json.load(open(MANIFEST, encoding="utf-8")).values())
    years = sorted(int(d[:4]) for d, _ in P["articles"].values())
    y = {k: art(P, f"eia_tie_{k}.html")[0][:4] for k in (16191, 25632, 39712, 64785)}
    v = {
        "lo": f"{r['lo']:,},000", "hi": f"{r['hi']:,},000",
        "plo": f"{100 * r['frac_lo']:.0f}", "phi": f"{100 * r['frac_hi']:.0f}",
        "plo1": pct(r["frac_lo"]), "phi1": pct(r["frac_hi"]), "rec": f"{r['recovered']:,.0f}",
        "y_est": y[16191], "y_25632": y[25632], "y_39712": y[39712],
        "y_rec": str(int(y[64785]) - 1), "y_ngwu": art(P, "eia_ngwu_2019-02-14.html")[0][:4],
        "d_16191": long(art(P, "eia_tie_16191.html")[0]),
        **heat_states(),
        "first_year": str(years[0]), "last_year": str(years[-1]),
        # cold reader 1: "archived on the same day the data was fetched ... abandoned at birth"; the note now
        # says what the page is a record of, and that it will not be updated, in fewer words
        "archived": (f"A finished record from the monthly figures of the U.S. Energy Information Administration (EIA) "
                     f"through {mon(P['through'])} and its articles of "
                     f"{years[0]} to {years[-1]}; it will not be updated."),
        "takeaways": insight.takeaways([
            f"When plants leave ethane in the gas it falls behind the other liquids they produce: its share of "
            f"the five (ethane, propane, two butanes and natural gasoline) fell "
            f"from {pct(A['2010']['share'])} per cent in 2010 to {pct(P['low_share'][1])} per cent in "
            f"{P['low_share'][0]}, while propane output grew faster than ethane's.",
            f"The share was {pct(t['share'])} per cent over the twelve months to {mon(t['to'])}, about what it was "
            f"in 2010, after new plastics plants and the first ethane export ships began taking more of it.",
            f"Since 2015 ethane production has grown {g['eth']:.1f} times and the other plant liquids "
            f"{g['other']:.1f} times; for {int(y[64785]) - 1}, a record year, EIA credited more recovery as gas "
            f"production rose, and growing demand from petrochemical plants at home and abroad."]),
        "hero": hero(P), "price_rows": price_rows(P),
        "x0": mon(P["hero"]["x"][0]), "x1": mon(P["hero"]["x"][-1]), "fetched": long(fetched),
        "btu": f"{P['heat']['mmbtu_per_bbl']:.3f}",
        "first_ship": long(P["first_ship"]),
        "ttm_from": mon(t["from"]), "ttm_to": mon(t["to"]), "g_base": "2015",
        "s2010r": f"{100 * A['2010']['share']:.0f}", "s2015r": f"{100 * A['2015']['share']:.0f}",
        "y2018": f"{A['2018']['eth'] / 1000:.2f}", "y_rec1": y[64785],
        "y_28052": art(P, "eia_tie_28052.html")[0][:4],
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    v.update(quotes())
    claims(P, v)
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "uri.html"), encoding="utf-8").read()
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
    refs = add_citations.PAGES.get("ethane.html")
    if not refs:
        return text, ["ethane.html has no entry in add_citations.PAGES"]
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
        print("  ethane.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  ethane.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
