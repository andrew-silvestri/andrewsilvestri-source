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
    paid = [y["year"] for y in full if y["by_adder"]["central"]["savings_kw_yr"] > fl["annual_cost_kw_yr"]]
    return dict(s=s, fl=fl, last=last, full=full, paid=paid, cost=fl["annual_cost_kw_yr"])


def claims(F, P):
    bad = []
    s, last = F["s"], F["last"]
    if s["below"] != 0:
        bad.append(f"{s['below']} month(s) below the break-even; 'not in any month' fails")
    if P["robust_eta_g"]["below"] != 0:
        bad.append("at the LBNL low-end gas efficiency a month falls below; the page says none does")
    mult = s["last_gas_needed_usd_mmbtu"] / last["gas_usd_mmbtu"]
    if abs(mult - round(mult)) > 0.5:
        bad.append("gas multiple")
    if not F["full"]:
        bad.append("no full year of the flexible case")
    if not F["paid"] or len(F["paid"]) > len(F["full"]) / 2:
        bad.append(f"years paid {F['paid']}: the standfirst's 'paid for itself in ... only' needs at least one and a minority")
    if not all(y["by_adder"]["low"]["savings_kw_yr"] >= y["by_adder"]["central"]["savings_kw_yr"] >=
               y["by_adder"]["high"]["savings_kw_yr"] for y in F["fl"]["years"]):
        bad.append("savings do not fall as the adder rises")
    e = P["emissions"]
    if not (e["average"]["t_mwh"] > e["parity_t_mwh"] and e["marginal"]["t_mwh"] > e["average"]["t_mwh"]):
        bad.append("emissions: the average grid is not above parity, or the marginal not above the average")
    lf = F["fl"]["years"][-1]
    if not lf["complete"] and lf is F["full"][-1]:
        bad.append("the latest flexible year is both partial and counted as full")
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
            "annotations": [{"at": lo, "text": f"closest: {s['ratio_min']:.1f}x", "short": f"{s['ratio_min']:.1f}x"},
                            {"at": s["ratio_max_period"], "text": f"widest: {s['ratio_max']:.1f}x",
                             "short": f"{s['ratio_max']:.1f}x"}]}


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
        (f"<p><b>{ms2[0]['period'][:4]} to {e2[:4]}.</b> Shale gas brought the gas price down to as little as "
         f"${g2lo:.2f}, and the break-even fell with it, while the price of electricity did not. Industry paid "
         f"{r2lo:.1f} to {r2hi:.1f} times the break-even.</p>", {"t": t_at(e2)}),
        (f"<p><b>Since {ms3[0]['period'][:4]}.</b> In {month(last['period'])}, the last month with both prices, industry "
         f"paid {last['elec_c_kwh']:.2f} cents and the break-even was {last['breakeven_c_kwh']:.2f}: {last['ratio']:.1f} "
         f"times. For an electric boiler to have broken even that month, gas would have had to cost about "
         f"${s['last_gas_needed_usd_mmbtu']:.2f} per million Btu instead of ${last['gas_usd_mmbtu']:.2f}.</p>", {"t": 1}),
    ]
    return insight.scrolly(hero_spec(P, F), steps, from_state={"t": 0})


def flex_rows(F):
    rows = []
    for y in F["fl"]["years"]:
        b = y["by_adder"]
        star = "" if y["complete"] else "*"
        pays = "yes" if b["central"]["savings_kw_yr"] > F["cost"] else "no"
        cls = ' class="lit"' if pays == "yes" else ""
        rows.append(f'<tr{cls}><td>{y["year"]}{star}</td><td class="n">{b["central"]["hours"]:,}</td>'
                    f'<td class="n">{b["low"]["savings_kw_yr"]:.2f} / {b["central"]["savings_kw_yr"]:.2f} / '
                    f'{b["high"]["savings_kw_yr"]:.2f}</td><td>{pays}</td></tr>')
    return "\n".join(rows)


def values(P, S):
    import insight
    F = facts(P)
    claims(F, P)
    s, last, fl = F["s"], F["last"], F["fl"]
    d = P["defaults"]
    e = P["emissions"]
    full = F["full"]
    lastfull = full[-1]
    lc = lastfull["by_adder"]["central"]
    part = [y for y in fl["years"] if not y["complete"]]
    note = f"The electric boiler's own cost: ${F['cost']:.2f} per kilowatt a year. Highlighted: the years its savings at the central charges cover it."
    if part:
        note = f"* {part[-1]['year']} to {month(part[-1]['through'])}, the last month of EIA's gas price; not a full year. " + note
    sav_c = [y["by_adder"]["central"]["savings_kw_yr"] for y in full if y["year"] not in F["paid"]]
    nonfuel = P["months"][-1]["breakeven_c_kwh"] - P["months"][-1]["fuel_only_c_kwh"]
    cov = S["eia_coverage_pct"]
    covs = [v for k, v in cov.items() if k.isdigit()]
    paid_txt = " and ".join(str(y) for y in F["paid"]) if F["paid"] else "none"
    by_year = {y["year"]: y for y in full}
    paid_detail = "; ".join(f"{y}: ${by_year[y]['by_adder']['central']['savings_kw_yr']:.2f}" for y in F["paid"])
    v = {
        "stamp": insight.stamp(s["last"], "EIA's Texas industrial electricity and natural gas prices"),
        "takeaways": insight.takeaways([
            f"In the {s['n_months']} months from {month(s['first'])} to {month(s['last'])}, Texas industrial "
            f"electricity never cost less than the electric boiler's break-even: it ran {s['ratio_min']:.1f} to "
            f"{s['ratio_max']:.1f} times it, and {last['ratio']:.1f} times in the last month.",
            f"An electric boiler kept beside a gas one and run only in cheap wholesale hours, with typical delivery "
            f"charges, saved ${min(sav_c):.2f} to ${max(sav_c):.2f} a year per kilowatt of its size in the full years "
            f"other than {paid_txt} ({paid_detail}), against ${F['cost']:.2f} a year to build and run it.",
            f"Per unit of heat the electric boiler emits about {e['average']['ratio_to_gas']:.1f} times the carbon "
            f"dioxide of the gas boiler on the average Texas grid, and about {e['marginal']['ratio_to_gas']:.1f} times on "
            f"the power plants that run when demand rises."]),
        "hero": hero(P, F),
        "flex_paid_years": paid_txt, "flex_n": str(len(full)),
        "frac_word": word(last["breakeven_c_kwh"] / last["elec_c_kwh"]),
        "last_month": month(last["period"]), "last_be": f"{last['breakeven_c_kwh']:.2f}", "last_elec": f"{last['elec_c_kwh']:.2f}",
        "gas_mult": {4: "four", 5: "five", 6: "six", 7: "seven"}.get(round(s["last_gas_needed_usd_mmbtu"] / last["gas_usd_mmbtu"]),
                                                                       str(round(s["last_gas_needed_usd_mmbtu"] / last["gas_usd_mmbtu"]))),
        "flex_last": str(lastfull["year"]), "flex_last_sav": f"{lc['savings_kw_yr']:.2f}",
        "flex_cost": f"{F['cost']:.2f}", "flex_cap": f"{fl['capital_per_kw_in']:.0f}",
        "marg_x": f"{e['marginal']['ratio_to_gas']:.1f}", "avg_x": f"{e['average']['ratio_to_gas']:.1f}",
        "marg_t": f"{e['marginal']['t_mwh']:.2f}", "avg_t": f"{e['average']['t_mwh']:.3f}", "parity": f"{e['parity_t_mwh']:.3f}",
        "eta_e": f"{100 * d['eta_e']:.0f}", "eta_g": f"{100 * d['eta_g']:.0f}",
        "robust_min": f"{P['robust_eta_g']['ratio_min']:.2f}", "robust_month": month(P["robust_eta_g"]["ratio_min_period"]),
        "first_year": s["first"][:4], "first_month": month(s["first"]),
        "flex_rows": flex_rows(F), "flex_note": note,
        "a_low": f"{S['delivery_adders_usd_mwh']['low']}", "a_central": f"{S['delivery_adders_usd_mwh']['central']}",
        "a_high": f"{S['delivery_adders_usd_mwh']['high']}",
        "life": str(d["life"]), "r_pct": f"{100 * d['r']:.0f}", "hours": f"{d['hours']:,.0f}",
        "capex_e": f"{d['capex_e']:,.0f}", "capex_g": f"{d['capex_g']:,.0f}",
        "fom_e": f"{100 * d['fom_e']:.0f}", "fom_g": f"{100 * d['fom_g']:.0f}",
        "nonfuel": f"{nonfuel:.2f}", "hc_lo": str(s["heat_content_years"][0]), "hc_hi": str(s["heat_content_years"][1]),
        "flex_first": str(fl["years"][0]["year"]), "gas_cov": f"{min(covs):.0f} to {max(covs):.0f}",
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
