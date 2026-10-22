"""
Write site/lauf.html from template.html and outputs/payload.json.

Every number on the page comes from the payload, from a quotation read out of an opened source file
(build_lauf.py stores them), or from a file this script measures (the archive's size); the prose is in
the template. The parts of the shipped page that other scripts own - the nav (rebuild_nav.py), the
citation markers and Sources list (add_citations.py's table, applied here), the ?v= stamps
(bust_cache.py) and image dimensions - are kept as the shipped page has them, so
tests/test_generators.py can run this on the shipped tree and expect no change. The idiom is
takeaway/update_page.py's.

claims() asserts every direction the template's words commit to ("about a third", "did not move",
"tends to stay", "middle but not the tails", "no single scale"). If a rebuild moves one, the generator
stops rather than ship prose the payload contradicts.

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
PAGE = os.path.join(SITE, "lauf.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "lauf-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import inspect   # noqa: E402
import model as M   # noqa: E402


def f1(x):
    return f"{x:.1f}"


def f2(x):
    return f"{x:.2f}"


def sp(x):
    """A signed change in points, as printed."""
    return f"{x:+.1f}".replace("-", "−")


def pctv(x):
    """A reported percentage: whole numbers stay whole, others to two places."""
    return f"{x:.0f}" if float(x).is_integer() else f"{x:.2f}"


def width(q):
    return q["p75"] - q["p25"]


def best_scale(m, ch):
    """The swept scale whose middle half of year-to-year change is closest in width to the reported one."""
    return min(m, key=lambda k: abs(width(m[k]["change"]) - width(ch)))


def claims(P, y0, y1, lez, rho, m, ch):
    # ch here is the change on systems not zero, whole or repeated in either year (finding 3)
    rule = P["rule_year"]
    rep = P["reporting"]
    c = [
        ("'about a third ... every year': at or below zero within 0.28-0.36 in every year",
         all(0.28 <= v <= 0.36 for v in lez)),
        ("'did not change when the rule did': the year before and the rule year differ by under 2 points",
         abs(rep[str(rule)]["at_or_below_zero"] - rep[str(rule - 1)]["at_or_below_zero"]) < 0.02),
        ("and over the whole span the averages before and after differ by under 3 points",
         abs(sum(rep[str(y)]["at_or_below_zero"] for y in range(rule, y1 + 1)) / (y1 - rule + 1)
             - sum(rep[str(y)]["at_or_below_zero"] for y in range(y0, rule)) / (rule - y0)) < 0.03),
        ("'one report in all the years before' (alt text): exactly one negative report before the rule year",
         sum(round(rep[str(y)]["negative"] * rep[str(y)]["n"]) for y in range(y0, rule)) == 1),
        ("'did not allow a negative figure': under 0.2% negative before the rule year",
         all(rep[str(y)]["negative"] < 0.002 for y in range(y0, rule))),
        ("'negatives rose from none': the first rule year has negatives", rep[str(rule)]["negative"] > 0),
        ("'exact zeros fell'", rep[str(y1)]["zero"] < rep[str(rule - 1)]["zero"]),
        ("'heaped and repeated': whole numbers and repeats both over a sixth of reports every year",
         all(rep[str(y)]["whole_of_nonzero"] > 1 / 6 for y in range(y0, y1 + 1))
         and all(rep[str(y)]["repeat_of_pairs"] > 1 / 6 for y in range(y0 + 1, y1 + 1))),
        ("'tends to stay where it was': rank correlation above 0.5 every year", min(rho) > 0.5),
        ("'as much as that in the middle': the closest scale's middle half is within 0.3 points of the reported width",
         abs(width(m[best_scale(m, ch)]["change"]) - width(ch)) < 0.3),
        ("'but not in the tails': at that scale the reported 90th percentile is beyond the model's by a point",
         ch["p90"] - m[best_scale(m, ch)]["change"]["p90"] > 1.0),
        ("'no single scale gives both': where the doubled or tripled model reaches the reported tails, its "
         "middle half is already wider than reported",
         all(not (m[k]["change"]["p90"] >= ch["p90"]) or (m[k]["change"]["p75"] - m[k]["change"]["p25"]
                                                          > (ch["p75"] - ch["p25"]) * 1.5)
             for k in ("2.0", "3.0", "4.0"))),
        ("'the lower quartile is zero in every year' (figure alt text)",
         all(P["distribution"][str(y)]["US"]["all"]["p25"] == 0 for y in range(y0, y1 + 1))),
    ]
    bad = [name for name, ok in c if not ok]
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def values(P):
    rep, dist, per, mod = P["reporting"], P["distribution"], P["persistence"], P["model"]
    y0, y1 = P["years"]
    rule = P["rule_year"]
    lez = [rep[str(y)]["at_or_below_zero"] for y in range(y0, y1 + 1)]
    whole = [rep[str(y)]["whole_of_nonzero"] for y in range(y0, y1 + 1)]
    repv = [rep[str(y)]["repeat_of_pairs"] for y in range(y0 + 1, y1 + 1)]
    rho = [per[str(y)]["rank_corr"] for y in range(y0 + 1, y1 + 1)]
    last = dist[str(y1)]
    ch = per[str(y1)]["change"]
    chi = per[str(y1)]["change_informative"]
    m = mod["scale_sweep"]
    claims(P, y0, y1, lez, rho, m, chi)
    q = P["quotes"]
    d = mod["defaults"]
    tx_cap = float(re.search(r"distribution system is ([\d.]+)%", q["tx_cap"]).group(1))
    ok_q = re.search(r"shall be measured (in order that.*?distribution may be accurately determined)", q["ok_measure"])
    v = {
        "y0": y0, "y1": y1, "y1m": y1 - 1, "rule_year": rule, "rule_prev": rule - 1,
        "n_reports": f"{sum(rep[str(y)]['n'] for y in range(y0, y1 + 1)):,}",
        "n_last": f"{rep[str(y1)]['n']:,}", "n_excluded": f"{P['excluded_non_natural_gas']:,}",
        "commodity_from": P["commodity_from"],
        "lez_last": f1(100 * rep[str(y1)]["at_or_below_zero"]), "lez_min": f1(100 * min(lez)), "lez_max": f1(100 * max(lez)),
        "neg_last": f1(100 * rep[str(y1)]["negative"]),
        "zero_prev": f1(100 * rep[str(rule - 1)]["zero"]), "zero_last": f1(100 * rep[str(y1)]["zero"]),
        "neg_rule": P["rule_change"]["negative_2018"], "neg_rule_zero": P["rule_change"]["were_zero_2017"],
        "whole_last": f1(100 * rep[str(y1)]["whole_of_nonzero"]), "whole_min": f1(100 * min(whole)),
        "whole_max": f1(100 * max(whole)),
        "rep_last": f1(100 * rep[str(y1)]["repeat_of_pairs"]), "rep_min": f1(100 * min(repv)), "rep_max": f1(100 * max(repv)),
        "rho_last": f2(per[str(y1)]["rank_corr"]), "rho_min": f2(min(rho)), "rho_max": f2(max(rho)),
        "p25_last": pctv(last["US"]["all"]["p25"]), "p75_last": pctv(last["US"]["all"]["p75"]),
        "med_last": pctv(last["US"]["all"]["p50"]),
        "ip25_last": pctv(last["US"]["informative"]["p25"]), "ip75_last": pctv(last["US"]["informative"]["p75"]),
        "imed_last": pctv(last["US"]["informative"]["p50"]),
        "tx_n": last["TX"]["all"]["n"], "tx_p25": pctv(last["TX"]["all"]["p25"]), "tx_p75": pctv(last["TX"]["all"]["p75"]),
        "ok_n": last["OK"]["all"]["n"], "ok_p25": pctv(last["OK"]["all"]["p25"]), "ok_p75": pctv(last["OK"]["all"]["p75"]),
        "ok_top": f"{100 * P['concentration_top_share']['OK'][str(y1)]:.0f}",
        "ch_p25": sp(ch["p25"]), "ch_p75": sp(ch["p75"]), "ch_p90": f1(ch["p90"]), "ch_p10": sp(ch["p10"]),
        "ch_p10a": f1(-ch["p10"]),
        "ch_i_n": f"{chi['n']:,}", "chi_p25": sp(chi["p25"]), "chi_p75": sp(chi["p75"]), "chi_p90": f1(chi["p90"]),
        "chi_p10a": f1(-chi["p10"]), "q_zero": q["report_zero"],
        "tx_cap": f1(tx_cap), "tx_cap_c": f2(100 * tx_cap / (100 - tx_cap)),
        "q_mix": q["report_mix"], "q_proxy": q["report_proxy"], "q_meters": q["report_meters"],
        "q_ok": ok_q.group(1).replace('"', "’").replace("’lost", "‘lost"),
        # end at "consumption": the PDF's text runs "for the12 months" together
        "q_partg": q["partg"][:q["partg"].index("total consumption") + len("total consumption")],
        "m_n": f"{d['n_meters']:,}", "m_cg": f1(d["cg_u"]), "m_fleet": f1(d["fleet_mean_sd"]),
        "m_drift": f1(d["fleet_drift"]), "m_meter": f1(d["meter_sd"]), "m_uncomp": f"{100 * d['uncomp_share']:.0f}",
        "m_temp": f"{d['gas_temp_f']:.0f}", "m_tempsd": f1(d["gas_temp_sd_f"]), "m_timing": f1(d["timing_sd"]),
        "m_tbase": f"{M.T_BASE_F:.0f}",
        "m_systems": f"{inspect.signature(M.summary).parameters['n_systems'].default:,}",
    }
    for k, key in (("m1", "1.0"), ("m2", "2.0"), ("m3", "3.0")):
        c = m[key]["change"]
        v[f"{k}_p25"], v[f"{k}_p75"] = sp(c["p25"]), sp(c["p75"])
        v[f"{k}_p10"], v[f"{k}_p90"] = sp(c["p10"]), (sp(c["p90"]) if k != "m1" else f1(c["p90"]))
    k = best_scale(m, chi)
    v["mk"] = f"{float(k):g}"
    v["mk_p25"], v["mk_p75"], v["mk_p90"] = sp(m[k]["change"]["p25"]), sp(m[k]["change"]["p75"]), f1(m[k]["change"]["p90"])
    v["zip_kb"] = f"{os.path.getsize(ZIP) / 1024:,.0f}" if os.path.exists(ZIP) else "0"
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "meter.html"), encoding="utf-8").read()
        stamps = {}
    else:
        stamps = dict(re.findall(r'(?:href|src|srcset)="([^"?]+)\?v=([0-9a-f]+)"', shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    text = text.replace("{{nav}}", nav)

    def stamp(mm):
        path = mm.group(2)
        return f'{mm.group(1)}="{path}?v={stamps[path]}"' if path in stamps else mm.group(0)
    return re.sub(r'(href|src|srcset)="([^"?]+\.(?:css|js|png))"', stamp, text)


def image_dims(text):
    from PIL import Image

    def dims(mm):
        attr, src, rest = mm.group(1), mm.group(2), mm.group(3)
        w, h = Image.open(os.path.join(SITE, src)).size
        return f'{attr}="{src}{rest}" width="{w}" height="{h}"'
    text = re.sub(r'(srcset)="(assets/[^"?]+)([^"]*)" width="[^"]*" height="[^"]*"', dims, text)
    return re.sub(r'(src)="(assets/[^"?]+)([^"]*)" loading="lazy" width="[^"]*" height="[^"]*"',
                  lambda mm: dims(mm).replace('" width', '" loading="lazy" width', 1), text)


def span(text):
    """The marginalia asides span the grid rows after them (beauty/update_page.py's rule)."""
    main = text[text.index("<main"):text.index("</main>")]
    body = re.sub(r"<aside.*?</aside>", "", main, flags=re.S)
    body = body[body.index(">") + 1:]
    depth, n = 0, 0
    for mm in re.finditer(r"<(/?)(\w+)[^>]*?>", body):
        close, tag = mm.group(1), mm.group(2)
        if tag in ("img", "br", "hr", "meta", "link", "input", "source"):
            n += depth == 0
            continue
        if close:
            depth -= 1
        else:
            n += depth == 0
            depth += 1
    return n + 1


def render(P):
    t = open(TEMPLATE, encoding="utf-8").read()
    v = values(P)
    missing = sorted(set(re.findall(r"{{(\w+)}}", t)) - set(v) - {"nav", "span"})
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
    t = t.replace("{{span}}", str(span(t)))
    return t


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("lauf.html")
    if not refs:
        return text, ["lauf.html has no entry in add_citations.PAGES"]
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
        print("  lauf.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  lauf.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
