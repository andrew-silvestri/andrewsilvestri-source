"""
Write site/heat.html from template.html and outputs/payload.json (build_heat.py).

Every number on the page comes from the payload, from data/sources.json, from model.py's defaults
or from a file this script measures (the archive's size); the prose is in the template. The nav
(rebuild_nav.py), the citation markers and Sources (add_citations.py's table, applied here) and
the ?v= stamps (bust_cache.py) are kept as the shipped page has them, so tests/test_generators.py
can run this on the shipped tree and expect no change. The idiom is storage/update_page.py's.

claims() asserts every statement the template's words make about the data ("not in any month",
"about a fifth", "five times", "paid for itself in N of M years", the emissions multiples); if a
refresh moves one, the generator stops rather than ship prose the payload contradicts.

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
PAGE = os.path.join(SITE, "heat.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
SOURCES = os.path.join(HERE, "data", "sources.json")
ZIP = os.path.join(SITE, "downloads", "heat-code.zip")
sys.path.insert(0, ROOT)

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]
FRACTIONS = {"a quarter": 0.25, "a fifth": 0.2, "a sixth": 1 / 6, "a third": 1 / 3}


def month(ym):
    y, m = ym.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


def short(ym):
    y, m = ym.split("-")
    return f"{MONTHS[int(m) - 1][:3]} {y}"


def word(x):
    w = min(FRACTIONS, key=lambda k: abs(FRACTIONS[k] - x))
    if abs(FRACTIONS[w] - x) > 0.025:
        raise SystemExit(f"heat/update_page.py: {x:.3f} is no plain fraction")
    return w


def facts(P):
    s, fl = P["summary"], P["flexible"]
    last = P["months"][-1]
    full = [y for y in fl["years"] if y["complete"]]
    cost = fl["annual_cost_kw_yr"]

    def paid(size, case):
        return [y["year"] for y in full if y["cases"][case]["net_clean"] > cost[size]]
    return dict(s=s, fl=fl, last=last, full=full, cost=cost, paid=paid)


def years_txt(ys):
    if not ys:
        return "none of them"
    if len(ys) == 1:
        return f"one ({ys[0]})"
    words = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
    return f"{words.get(len(ys), len(ys))} ({', '.join(str(y) for y in ys[:-1])} and {ys[-1]})"


def claims(F, P):
    bad = []
    s = F["s"]
    if s["below"] != 0:
        bad.append(f"{s['below']} month(s) below the break-even; 'not in any month' fails")
    if P["robust_eta_g"]["below"] != 0:
        bad.append("at a 70% gas boiler a month falls below; the page says none does")
    if not F["full"]:
        bad.append("no full year of the flexible case")
    lc = F["paid"]("large", "central")
    if not lc or len(lc) > len(F["full"]) / 3:
        bad.append(f"large boiler, central charges, paid back in {lc}: the standfirst's 'even then' needs few")
    if F["paid"]("model", "central"):
        bad.append("a mid-size boiler pays back at central charges; the page says it does not")
    if not all(y["cases"]["low"]["net_clean"] >= y["cases"]["central"]["net_clean"] >= y["cases"]["high"]["net_clean"]
               for y in F["fl"]["years"]):
        bad.append("savings do not fall as the charges rise")
    hrs = [y["cases"]["central"]["hours"] for y in F["full"]]
    if len(hrs) < 10 or sum(hrs[-5:]) <= 2 * sum(hrs[-10:-5]):
        bad.append("cheap hours: the last five full years are not more than double the five before")
    if F["full"][-1]["neg_hours"] <= 0:
        bad.append("no hours below zero in the latest full year")
    e = P["emissions"]
    if not (e["average"]["t_mwh"] > e["parity_t_mwh"] and e["marginal"]["t_mwh"] > e["average"]["t_mwh"]):
        bad.append("emissions: the average grid is not above parity, or the marginal not above the average")
    if bad:
        raise SystemExit("heat/update_page.py: the payload contradicts the page's words:\n  " + "\n  ".join(bad))


def hero_spec(P, F):
    M = P["months"]
    s = F["s"]
    lo, lastp = s["ratio_min_period"], M[-1]["period"]
    return {"id": "heat-hero", "type": "series",
            "title": f"Texas industrial electricity price and the price at which an electric boiler breaks even "
                     f"against gas, monthly, {short(M[0]['period'])} to {short(lastp)}",
            "x": [m["period"] for m in M], "y": {"label": "cents per kWh"},
            "series": [{"key": "paid", "label": "What Texas industry paid", "color": "acc",
                        "values": [round(m["elec_c_kwh"], 3) for m in M]},
                       {"key": "be", "label": "Break-even for an electric boiler", "color": "moss",
                        "values": [round(m["breakeven_c_kwh"], 3) for m in M]}],
            "band": {"a": "paid", "b": "be", "pos": {"color": "acc", "label": "Electric costs more"},
                     "neg": {"color": "moss"}},
            "annotations": [{"at": lo, "text": f"closest {s['ratio_min']:.1f}x", "short": f"{s['ratio_min']:.1f}x"}] +
                           [{"at": f, "text": "gas spike", "short": "spike"} for f in F["fl"]["flagged"]]}
    # "widest" is not annotated: beside the spike label it found no lane between 640 and 670 px
    # (Charts.check, 2026-10-23); step 3's text names the widest month instead.


def hero(P, F):
    import insight
    M, s, last = P["months"], F["s"], F["last"]
    n = len(M)
    idx = {m["period"]: i for i, m in enumerate(M)}

    def t_at(per):
        return round(idx[per] / (n - 1), 4)

    def span(a, b):
        ms = [m for m in M if a <= m["period"] <= b]
        r = [m["ratio"] for m in ms]
        g = [m["gas_usd_mmbtu"] for m in ms]
        return ms, min(r), max(r), min(g), max(g)
    e1 = "2008-12" if "2008-12" in idx else M[n // 3]["period"]
    e2 = "2020-12" if "2020-12" in idx else M[2 * n // 3]["period"]
    ms1, r1lo, r1hi, g1lo, g1hi = span(M[0]["period"], e1)
    ms2, r2lo, r2hi, g2lo, g2hi = span(M[idx[e1] + 1]["period"], e2)
    ms3, r3lo, r3hi, g3lo, g3hi = span(M[idx[e2] + 1]["period"], last["period"])
    steps = [
        (f"<p><b>{ms1[0]['period'][:4]} to {e1[:4]}.</b> Gas cost ${g1lo:.2f} to ${g1hi:.2f} per million Btu, "
         f"and the break-even rose and fell with it. This is as close as the two lines came: in "
         f"{month(s['ratio_min_period'])} industry paid {s['ratio_min']:.2f} times the break-even, and in no month "
         f"less.</p>", {"t": t_at(e1)}),
        (f"<p><b>{ms2[0]['period'][:4]} to {e2[:4]}.</b> The gas price fell to as little as ${g2lo:.2f}, and the "
         f"break-even fell with it; the price of electricity fell by less. Industry paid {r2lo:.1f} to {r2hi:.1f} "
         f"times the break-even.</p>", {"t": t_at(e2)}),
        (f"<p><b>Since {ms3[0]['period'][:4]}.</b> {flag_step(P, F)}In {month(last['period'])}, the last month with both prices, industry "
         f"paid {last['elec_c_kwh']:.2f} cents and the break-even was {last['breakeven_c_kwh']:.2f}: {last['ratio']:.1f} "
         f"times. For an electric boiler to have broken even that month, gas would have had to cost about "
         f"${s['last_gas_needed_usd_mmbtu']:.2f} per million Btu instead of ${last['gas_usd_mmbtu']:.2f}.</p>", {"t": 1}),
    ]
    return insight.scrolly(hero_spec(P, F), steps, from_state={"t": 0})


def flag_step(P, F):
    out = ""
    by = {m["period"]: m for m in P["months"]}
    for f in F["fl"]["flagged"]:
        m = by[f]
        out += (f"In {month(f)} a week of extreme gas prices pushed the month's break-even to {m['breakeven_c_kwh']:.1f} "
                f"cents, and electricity to {m['elec_c_kwh']:.1f}. ")
    sm = F["s"]
    out += f"The widest gap came in {month(sm['ratio_max_period'])}, {sm['ratio_max']:.1f} times, with gas cheap. "
    return out


def flex_rows(F):
    rows = []
    for y in F["fl"]["years"]:
        c = y["cases"]
        star = "" if y["complete"] else "*"
        dag = "&dagger;" if y["flagged"] else ""
        pays = "yes" if c["central"]["net_clean"] > F["cost"]["large"] else "no"
        cls = ' class="lit"' if pays == "yes" and y["complete"] else ""
        rows.append(f'<tr{cls}><td>{y["year"]}{star}{dag}</td><td class="n">{c["central"]["hours"]:,}</td>'
                    f'<td class="n">{c["low"]["net_clean"]:.2f} / {c["central"]["net_clean"]:.2f} / '
                    f'{c["high"]["net_clean"]:.2f}</td><td>{pays}</td></tr>')
    return "\n".join(rows)


def values(P, S):
    import insight
    F = facts(P)
    claims(F, P)
    s, last, fl = F["s"], F["last"], F["fl"]
    d = P["defaults"]
    e = P["emissions"]
    full = F["full"]
    first, lastfull = full[0], full[-1]
    lc, ll, ml = F["paid"]("large", "central"), F["paid"]("large", "low"), F["paid"]("model", "low")
    hrs = [y["cases"]["central"]["hours"] for y in full]
    recent, before = sum(hrs[-5:]) / 5, sum(hrs[-10:-5]) / 5
    part = [y for y in fl["years"] if not y["complete"]]
    by = {y["year"]: y for y in fl["years"]}
    note = (f"Highlighted: the full years in which a large boiler's savings, at the central charges, pay back its "
            f"${F['cost']['large']:.2f} a year.")
    if part:
        note = f"* {part[-1]['year']} to {month(part[-1]['through'])}, the last month of EIA's gas price; not a full year. " + note
    flag_text = ""
    for f in fl["flagged"]:
        y = int(f[:4])
        c = by[y]["cases"]["central"]
        gm = [m for m in P["months"] if m["period"] == f][0]["gas_usd_mmbtu"]
        note = (f"&dagger; {month(f)} set aside: its average gas price was more than twice the months either side, "
                f"from a few days of extreme prices; counted, it would add ${c['net'] - c['net_clean']:.2f} to {y}'s "
                f"central figure, earned on ordinary days. ") + note
        flag_text = (f"A month whose average gas price is more than twice the average of the months either side is set "
                     f"aside: {month(f)}, when a week of extreme gas prices lifted the month's average to "
                     f"${gm:.2f} per million Btu. The boiler would not have run in that week, when electricity was "
                     f"dearer still, but the inflated average would have made the ordinary days either side look like "
                     f"cheap-electricity days.")
    nonfuel = last["breakeven_c_kwh"] - last["fuel_only_c_kwh"]
    covs = [v for k, v in S["eia_coverage_pct"].items() if k.isdigit()]
    ch, cap = S["charges"], S["electric_boiler_capital_usd_kw"]
    mult = s["last_gas_needed_usd_mmbtu"] / last["gas_usd_mmbtu"]
    words = {3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight"}
    mult_txt = (f"more than {words.get(int(mult), int(mult))}" if mult - int(mult) > 0.15
                else f"about {words.get(round(mult), round(mult))}")
    v = {
        "stamp": insight.stamp(s["last"], "EIA's Texas industrial electricity and natural gas prices"),
        "takeaways": insight.takeaways([
            f"In the {s['n_months']} months from {month(s['first'])} to {month(s['last'])}, the average Texas industrial "
            f"electricity price never fell below the electric boiler's break-even: it ran {s['ratio_min']:.1f} to "
            f"{s['ratio_max']:.1f} times it, and {last['ratio']:.1f} times in the last month.",
            f"A large electric boiler kept beside a gas one, run only when wholesale power is cheaper than gas, would "
            f"have saved enough to cover a year of its own cost in {years_txt(lc)} of the {len(full)} full years with "
            f"typical delivery charges, and in {years_txt(ll)} with the lowest charges.",
            f"Per unit of heat an electric boiler running all year emits about {e['average']['ratio_to_gas']:.1f} times "
            f"the carbon dioxide of a gas boiler on the average Texas grid, and about {e['marginal']['ratio_to_gas']:.1f} "
            f"times on the power plants that run when demand rises."]),
        "hero": hero(P, F),
        "frac_word": word(last["breakeven_c_kwh"] / last["elec_c_kwh"]), "gas_mult": mult_txt,
        "last_month": month(last["period"]),
        "lg_central_n": {1: "one", 2: "two", 3: "three"}.get(len(lc), str(len(lc))), "flex_n": str(len(full)),
        "flex_first": str(first["year"]), "flex_last": str(lastfull["year"]),
        "lg_central": years_txt(lc), "lg_low": years_txt(ll),
        "md_low": "in no year, even at the lowest charges" if not ml else f"only at the lowest charges, in {years_txt(ml)}",
        "hours_recent": f"{recent:,.0f}", "hours_before": f"{before:,.0f}",
        "neg_last": f"{lastfull['neg_hours']:,}",
        "e_low": f"{ch['energy_usd_mwh']['low']:.2f}", "e_high": f"{ch['energy_usd_mwh']['high']:.2f}",
        "tcrf_kw": f"{ch['demand_usd_kw_yr']['high'] - ch['demand_usd_kw_yr']['central']:.2f}",
        "d_central": f"{ch['demand_usd_kw_yr']['central']:.2f}", "d_high": f"{ch['demand_usd_kw_yr']['high']:.2f}",
        "cap_small": f"{cap['small']}", "cap_large": f"{cap['large']}", "small_mw": f"{cap['small_mw']:g}",
        "large_mw": f"{cap['large_mw']:g}", "cost_small": f"{F['cost']['small']:.2f}", "cost_large": f"{F['cost']['large']:.2f}",
        "cap_model": f"{fl['sizes_usd_kw']['model']:.0f}", "cost_model": f"{F['cost']['model']:.2f}",
        "flex_rows": flex_rows(F), "flex_note": note, "flag_text": flag_text,
        "marg_x": f"{e['marginal']['ratio_to_gas']:.1f}", "avg_x": f"{e['average']['ratio_to_gas']:.1f}",
        "marg_t": f"{e['marginal']['t_mwh']:.2f}", "avg_t": f"{e['average']['t_mwh']:.3f}", "parity": f"{e['parity_t_mwh']:.3f}",
        "e70_avg": f"{P['robust_eta_g']['emissions_ratio']['average']:.1f}",
        "e70_marg": f"{P['robust_eta_g']['emissions_ratio']['marginal']:.1f}",
        "eta_e": f"{100 * d['eta_e']:.0f}", "eta_g": f"{100 * d['eta_g']:.0f}",
        "robust_min": f"{P['robust_eta_g']['ratio_min']:.2f}", "robust_month": month(P["robust_eta_g"]["ratio_min_period"]),
        "first_year": s["first"][:4], "first_month": month(s["first"]),
        "life": str(d["life"]), "r_pct": f"{100 * d['r']:.0f}", "hours": f"{d['hours']:,.0f}",
        "capex_e": f"{d['capex_e']:,.0f}", "capex_g": f"{d['capex_g']:,.0f}",
        "fom_e": f"{100 * d['fom_e']:.0f}", "fom_g": f"{100 * d['fom_g']:.0f}",
        "nonfuel": f"{nonfuel:.2f}", "hc_lo": str(s["heat_content_years"][0]), "hc_hi": str(s["heat_content_years"][1]),
        "gas_cov": f"{min(covs):.0f} to {max(covs):.0f}",
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    return v


def keep_from_shipped(text, shipped):
    stamps = dict(re.findall(r'(?:href|src|srcset)="([^"?]+)\?v=([0-9a-f]+)"', shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    text = text.replace("{{nav}}", nav)

    def stamp(m):
        path = m.group(2)
        return f'{m.group(1)}="{path}?v={stamps[path]}"' if path in stamps else m.group(0)
    return re.sub(r'(href|src|srcset)="([^"?]+\.(?:css|js|png))"', stamp, text)


def render(P, S):
    t = open(TEMPLATE, encoding="utf-8").read()
    v = values(P, S)
    missing = sorted(set(re.findall(r"{{(\w+)}}", t)) - set(v) - {"nav"})
    if missing:
        raise SystemExit(f"template placeholders without a value: {missing}")
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)))
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    return keep_from_shipped(t, open(PAGE, encoding="utf-8").read())


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("heat.html")
    if not refs:
        return text, ["heat.html has no entry in add_citations.PAGES"]
    tmp = PAGE + ".render.tmp"
    open(tmp, "w", encoding="utf-8", newline="\n").write(text)   # LF: trap 32
    try:
        out, probs = add_citations.build(os.path.basename(tmp), refs)
    finally:
        os.remove(tmp)
    return (out if out is not None else text), probs


def main(apply=False):
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    S = json.load(open(SOURCES, encoding="utf-8"))
    t, probs = cite(render(P, S))
    for p in probs:
        print("  " + p)
    old = open(PAGE, "rb").read().decode("utf-8")   # bytes: trap 32
    print("  heat.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
