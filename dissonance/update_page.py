"""
Write site/dissonance.html from template.html and outputs/payload.json.

Every number on the page that comes from the survey, the review, the Meta and Yale data or the Global
Carbon Budget is taken from the payload here. The figures quoted from papers (Attari, Ipsos, Wynes and
Nicholas's textbook count, Carbone 4, the IPCC, HOPE, Gifford, Kormos and Gifford) are in the template's
prose, each with its reference. The parts other scripts own - the nav (rebuild_nav.py), the citation
markers and Sources list (add_citations.py's table, applied here) and the ?v= stamps (bust_cache.py) -
are kept as the shipped page has them, so tests/test_generators.py can run this on the shipped tree and
expect no change. The idiom is lead/update_page.py's.

The hero is a kit "rank" chart: the fourteen actions sorted by the share who report them, then by the
tonnes they save.

claims() asserts every direction and comparison the template's words commit to ("the three named most
often", "none is named by more than", "the second group still saves"). If a rebuild moves one, the
generator stops rather than ship prose the payload contradicts.

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
PAGE = os.path.join(SITE, "dissonance.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "dissonance-code.zip")
NAV_FROM = os.path.join(SITE, "climate-cost.html")   # first build only: a page in the same nav group
sys.path.insert(0, ROOT)

TOP = ["QD6_13", "QD6_14", "QD6_6"]      # the template names these three, in this order
BOT = ["QD6_8", "QD6_2", "QD6_5"]
ORD = {7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth", 11: "eleventh", 12: "twelfth"}
BARRIER_ROWS = [("ev", "Electric car"), ("heatpump", "Heat pump"), ("solar", "Rooftop solar"),
                ("meat", "Eat less meat")]


def t2(x):
    return f"{x:.2f}"


def hero_spec(P):
    items = []
    for r in P["items"]:
        color = "acc" if r["code"] in TOP else "moss" if r["code"] in BOT else "dim"
        items.append({"label": r["label"], "a": round(r["pct_calc"], 2), "b": round(r["t"], 4), "color": color})
    return {"id": "dissonance-hero", "type": "rank",
            "title": "Fourteen climate actions, sorted by the share of people in the EU aged 15 and over who say "
                     "they apply to them "
                     "(Special Eurobarometer 565, 2025), then by the median tonnes of CO2e each saves per "
                     "person a year (Ivanova and colleagues, 2020)",
            "items": items,
            "a": {"label": "Say it applies, % of people 15+", "unit": "%", "decimals": 0},
            "b": {"label": "Tonnes CO2e saved a year, median", "unit": " t", "decimals": 2}}


def hero(P, v):
    import insight
    by_t = sorted(P["items"], key=lambda r: -r["t"])
    rec_rank = 1 + [r["code"] for r in by_t].index("QD6_13")
    steps = [
        (f"<p><b>Sorted by what people say.</b> Each bar is the share of people in the EU aged 15 and over who "
         f"say an action applies to them. Recycling leads at {v['rec_pct']} percent. An electric car and a low-energy home come last, at "
         f"{v['ev_pct']} and {v['home_pct']} percent.</p>", {"m": 0}),
        (f"<p><b>Sorted by tonnes.</b> The same fourteen actions, each bar now the median saving per person per "
         f"year. The electric car moves to the top at {v['ev_t']} tonnes. Recycling, at {v['rec_t']} tonnes, is "
         f"number {rec_rank} of 14.</p>", {"m": 1}),
        (f"<p><b>The order reverses at the ends.</b> The three actions named most often (blue) save "
         f"{v['top3_t']} tonnes each on average. The three named least often (brown) save {v['bot3_t']} tonnes. "
         f"The middle of the list keeps no clear order.</p>", {"m": 1, "f": 1}),
    ]
    return insight.scrolly(hero_spec(P), steps, from_state={"m": 0})


def action_rows(P):
    out = []
    for r in sorted(P["items"], key=lambda r: -r["pct_calc"]):
        mid = "one value" if r["p25"] is None else f"{r['p25']:.2f}&ndash;{r['p75']:.2f}"
        out.append(f"<tr><td>{r['label']}</td><td class=\"n\">{r['pct']}</td><td class=\"n\">{r['t']:.2f}</td>"
                   f"<td class=\"n\">{mid}</td><td class=\"n\">{r['n']}</td><td>{r['match']}</td></tr>")
    return "\n".join(out)


def barrier_rows(P):
    B = P["metayale"]["barriers"]
    out = []
    for k, name in BARRIER_ROWS:
        a, b = B[k][0], B[k][1]
        out.append(f"<tr><td>{name}</td><td>&ldquo;{a['reason']}&rdquo;</td><td class=\"n\">{a['pct']:.0f}</td>"
                   f"<td>&ldquo;{b['reason']}&rdquo;</td><td class=\"n\">{b['pct']:.0f}</td></tr>")
    return "\n".join(out).replace("'", "&rsquo;")


def claims(P, v):
    E, I = P["eb"], {r["code"]: r for r in P["items"]}
    bad = []

    def need(ok, what):
        if not ok:
            bad.append(what)
    need(E["top3"] == TOP, f"the three named most often are {E['top3']}, the template names {TOP}")
    need(sorted(E["bot3"]) == sorted(BOT), f"the three named least often are {E['bot3']}, the template names {BOT}")
    need(E["ratio"] > 5, "the bottom three no longer save several times the top three")
    need(E["ratio_adverse"] > 2, "'the second group still saves' more than twice: adverse ratio below 2")
    need(E["weighted_t"] < E["unweighted_t"], "the weighted tick is no longer worth less than the even spread")
    need(E["spearman"] < 0, "the rank correlation is no longer negative")
    need(E["at_least_one"] >= 85, "'Nine in ten name at least one': the share naming one is below 85%")
    need(max(I, key=lambda c: I[c]["pct_calc"]) == "QD6_13", "recycling is no longer the most named action")
    need(max(I, key=lambda c: I[c]["t"]) == "QD6_2", "the electric car is no longer the largest saving")
    need(I["QD6_2"]["pct"] <= I["QD6_5"]["pct"] + 1 and I["QD6_5"]["pct"] == min(r["pct"] for r in I.values()),
         "an electric car and a low-energy home no longer come last")
    need(E["best_gov"] > E["best_you"], "Europeans no longer name national governments before themselves")
    if bad:
        raise SystemExit("the payload contradicts the template:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    E, I, M, U = P["eb"], {r["code"]: r for r in P["items"]}, P["metayale"], P["eu"]
    A = M["adoption"]
    v = {
        "serious": f"{E['serious']:.0f}", "atleast": f"{E['at_least_one']:.0f}", "eb_n": f"{E['n']:,}",
        "top3_t": t2(E["top3_t"]), "bot3_t": t2(E["bot3_t"]),
        "ratio": f"about {round(E['ratio'])}", "ratio_adv": f"{E['ratio_adverse']:.1f}",
        "spearman": f"{E['spearman']:.2f}".replace("-", "&minus;"),
        "weighted_t": t2(E["weighted_t"]), "unweighted_t": t2(E["unweighted_t"]),
        "n_over_half": f"{len(E['over_half'])}", "over_half_max_pct": f"{E['over_half_max_pct']}",
        "iva_rows": f"{E['ivanova_rows']}", "paper_checks": f"{E['paper_checks']}",
        "gov_best": f"{E['best_gov']}", "you_best": f"{E['best_you']}",
        "eu_t": f"{U['consumption_t']:.1f}", "eu_year": f"{U['year']}",
        "rec_share_eu": f"{100 * I['QD6_13']['t'] / U['consumption_t']:.0f}",
        "ev_share_eu": f"{100 * I['QD6_2']['t'] / U['consumption_t']:.0f}",
        "my_countries": f"{M['countries']}",
        "ev_done": f"{A['ev']['done']:.0f}", "ev_want": f"{A['ev']['want']:.0f}",
        "solar_done": f"{A['solar']['done']:.0f}", "solar_want": f"{A['solar']['want']:.0f}",
        "action_rows": action_rows(P), "barrier_rows": barrier_rows(P),
        "stamp": ("Data: Special Eurobarometer 565, interviews in February and March 2025; savings from the studies "
                  "collected by Ivanova and colleagues (2020). This page does not update."),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    for key, code in [("rec", "QD6_13"), ("disp", "QD6_14"), ("app", "QD6_6"), ("ev", "QD6_2"), ("hp", "QD6_8"),
                      ("home", "QD6_5"), ("car", "QD6_3"), ("meat", "QD6_12"), ("travel", "QD6_11"),
                      ("green", "QD6_7")]:
        v[key + "_pct"] = f"{I[code]['pct']}"
        v[key + "_t"] = t2(I[code]["t"])
    for k in ("car_pct", "meat_pct", "travel_pct", "green_pct"):   # the template quotes only their tonnes
        del v[k]
    rec, ev = I["QD6_13"], I["QD6_2"]
    v["takeaways"] = insight.takeaways([
        f"Recycling is the action Europeans name most often ({rec['pct']} percent); by a published estimate it "
        f"saves {t2(rec['t'])} tonnes a year, about one-{ORD[round(ev['t'] / rec['t'])]} of the median saving from "
        f"replacing a car with an electric one.",
        f"Weighted by how often each action is named, the average reported action saves {v['weighted_t']} tonnes "
        f"a year; spread evenly over the fourteen, it would save {v['unweighted_t']}.",
        "Surveys point to two causes: people misjudge which actions matter most, and the large ones need money, "
        "a home of one's own or a suitable building."])
    v["hero"] = hero(P, v)
    claims(P, v)
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
    refs = add_citations.PAGES.get("dissonance.html")
    if not refs:
        return text, ["dissonance.html has no entry in add_citations.PAGES"]
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
        print("  dissonance.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  dissonance.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
