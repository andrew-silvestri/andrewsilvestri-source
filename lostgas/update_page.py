"""
Write site/lostgas.html from template.html, outputs/payload.json and, for the appendix,
meter/outputs/payload.json (through meter/update_page.py's own values(), so the meter numbers
are the ones that model's generator would print).

Every number on the page comes from a payload, from a quotation read out of an opened source file
(build_lostgas.py stores them), or from a file this script measures (the archives' sizes); the prose
is in the template. The parts of the shipped page other scripts own - the nav (rebuild_nav.py), the
citation markers and Sources list (add_citations.py's table, applied here) and the ?v= stamps
(bust_cache.py) - are kept as the shipped page has them, so tests/test_generators.py can run this on
the shipped tree and expect no change. The idiom is takeaway/update_page.py's.

claims() asserts every direction and range the template's words commit to ("a third", "a dollar or
two", "about N points", "if anything the range is narrow", the Texas owners). If a rebuild moves one,
the generator stops rather than ship prose the payload contradicts.

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
PAGE = os.path.join(SITE, "lostgas.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
METER = os.path.join(ROOT, "meter")
ZIP = os.path.join(SITE, "downloads", "lostgas-code.zip")
METER_ZIP = os.path.join(SITE, "downloads", "meter-code.zip")
CLIP = os.path.join(SITE, "assets", "clips", "lostgas-meter.json")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]


def f1(x):
    return f"{x:.1f}"


def f2(x):
    return f"{x:.2f}"


def pct(x):
    return f"{100 * x:.0f}"


def num(x):
    """A range end as printed: a true minus sign."""
    return f"{x:.1f}".replace("-", "−")


def meter_values():
    """The meter page's own numbers, from its own generator, run on its own payload, in its own
    process: both projects have a model.py, and importing one shadows the other."""
    import subprocess
    code = ("import json,sys,update_page as u;"
            "sys.stdout.write(json.dumps(u.values(json.load(open('outputs/payload.json',encoding='utf-8')))))")
    r = subprocess.run([sys.executable, "-c", code], cwd=METER, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit("meter/update_page.py values() failed: " + r.stderr[-2000:])
    return json.loads(r.stdout)


def width(q):
    return q["p75"] - q["p25"]


def best_scale(m, ch):
    """The swept scale whose middle half of year-to-year change is closest in width to the reported one
    (on systems not zero, whole or repeated in either year: Q6 claims check, finding 3)."""
    return min(m, key=lambda k: abs(width(m[k]["change"]) - width(ch)))


def hero_spec(P):
    h, b = P["hero"], P["model"]["band"]
    return {"id": "lostgas-hero", "type": "strip",
            "title": f"{h['n']:,} reports of lost and unaccounted-for gas for {h['year']}, by the share reported, "
                     f"with the range a system that loses nothing reports",
            "bins": [{k: x[k] for k in ("a", "b", "n", "le0", "inside")} for x in h["bins"]],
            "lights": [{"key": "le0", "color": "acc", "state": "neg"},
                       {"key": "inside", "color": "moss", "state": "inside"}],
            # the label says it is a model, so the chart alone does not read as an observation
            # (skeptical-reader review, 2026-10-23)
            "range": {"lo": b["lo"], "hi": b["hi"], "label": "modelled: no loss, meter error only", "state": "band"},
            "marks": [{"at": h["median"], "label": f"median {h['median']:g}%", "state": "med"},
                      {"at": 0, "label": "zero or less", "state": "neg"}],
            "y": {"label": "reports"},
            "x": {"label": "% reported lost and unaccounted for"}}


def hero(P, I):
    import insight
    h, b = P["hero"], P["model"]["band"]
    d = I["defaults"]
    steps = [
        (f"<p><b>{h['n']:,} reports for {h['year']}.</b> Each bar counts the reports that put a share of "
         f"their gas, in quarter-point steps, as lost and unaccounted for. The median report is {h['median']:g} per "
         f"cent. The two end bars gather the {h['tail_lo']} reports at −{abs(h['lo']):g} or below and the "
         f"{h['tail_hi']} above {h['hi']:g}.</p>", {"t": 1, "med": 1}),
        (f"<p><b>Zero or less: {pct(h['le0'] / h['n'])} per cent.</b> {h['zero']} reports say exactly zero and "
         f"{h['neg']} are negative: the meters say more gas went out than came in. A negative cannot be a "
         f"physical loss.</p>", {"t": 1, "med": 1, "neg": 1}),
        (f"<p><b>A system that loses nothing.</b> The shaded range is what this page's model of ordinary meter "
         f"error reports for systems with no loss at all: the middle 90 per cent of them land between "
         f"{num(b['lo'])} and {num(b['hi'])} per cent. Where the range sits depends on two assumptions, the gas's "
         f"temperature and how many customer meters correct for it; its width, about {I['width_min']:.0f} points, "
         f"hardly does.</p>", {"t": 1, "band": 1}),
        (f"<p><b>Inside it: {pct(d['all'])} per cent of reports</b> at this page's assumptions, "
         f"{pct(d['no_zero'])} per cent of those that are not exactly zero, and {pct(I['services_weighted'])} per "
         f"cent of customers, counted by their service lines. That share moves with the two assumptions (the "
         f"table in the appendix); the width does not. The typical report, {h['median']:g} per cent, is smaller "
         f"than the spread meter error alone produces, and at these assumptions a real two-point loss read by perfect "
         f"meters would land inside the range too.</p>", {"t": 1, "band": 1, "inside": 1}),
        (f"<p><b>Far outside it.</b> {h['tail_hi']} reports for {h['year']} are above {h['hi']:g} per cent, and "
         f"{h['tail_lo']} are at −{abs(h['lo']):g} or below. Meter errors of the ordinary kind modelled here do not "
         f"produce figures like those. That is where the number can say something: not what is happening, but "
         f"that something other than ordinary meter error is.</p>", {"t": 1, "band": 1}),
    ]
    return insight.scrolly(hero_spec(P), steps, from_state={"t": 0})


def grid_rows(I):
    rows = []
    for g in I["grid"]:
        rows.append(f'<tr><td>{g["gas_temp_f"]:.0f} °F</td><td class="n">{100 * g["uncomp_share"]:.0f}%</td>'
                    f'<td class="n">{num(g["lo"])} to {num(g["hi"])}</td><td class="n">{pct(g["all"])}%</td>'
                    f'<td class="n">{pct(g["no_zero"])}%</td></tr>')
    return "\n".join(rows)


def claims(P, I, D, mk, chi, m):
    h, own = P["hero"], P["owners"]
    c = [
        ("standfirst 'a third of reports are zero or negative': 0.28-0.38", 0.28 <= h["le0"] / h["n"] <= 0.38),
        ("'a dollar or two a year' in each state at the median customer's system",
         all(0.5 <= D[s]["at_median"] < 2.5 for s in ("TX", "OK"))),
        ("'about N points' wide: the band's width moves by under a point across the grid",
         I["width_max"] - I["width_min"] < 1.0),
        ("'a real two-point loss lands inside': 2.0 is inside the band at the defaults",
         P["model"]["band"]["lo"] <= 2.0 <= P["model"]["band"]["hi"]),
        ("'the typical report is smaller than the spread': median below the band's width",
         h["median"] < I["width_min"]),
        ("'if anything the range is narrow': the scale matching reported change is at least 1",
         float(mk) >= 1.0),
        ("the scale match is close: within 0.3 points of the reported middle half",
         abs(width(m[mk]["change"]) - width(chi)) < 0.3),
        ("'most Texas reports come from systems owned by cities' (stated as a count, true as a majority)",
         own["TX"].get("Municipal Owned", 0) * 2 > sum(own["TX"].values())),
        ("'not a figure to lean on': the inside share moves by more than 20 points across the grid",
         I["max_all"] - I["min_all"] > 0.20),
        ("'cold gas ... under-counts': the shared temperature error raises reported LAUF at the default temperature",
         P["clip"]["shared_temp_pct"] > 0 and P["model"]["defaults"]["gas_temp_f"] < 60),
        ("'a negative cannot be a physical loss' sits beside a year with negatives", h["neg"] > 0),
        ("'beyond anything ordinary meter error produces': the tail cut-offs are over six model standard "
         "deviations from the model's median on both sides",
         h["hi"] > P["model"]["band"]["median"] + 6 * P["model"]["at_defaults"]["level_sd"]
         and h["lo"] < P["model"]["band"]["median"] - 6 * P["model"]["at_defaults"]["level_sd"]),
    ]
    bad = [name for name, ok in c if not ok]
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    import model as M
    h, I, D, q, mod = P["hero"], P["inside"], P["dollars"], P["quotes"], P["model"]
    d = mod["defaults"]
    y1 = P["years"][1]
    chi = P["persistence"][str(y1)]["change_informative"]
    m = mod["scale_sweep"]
    mk = best_scale(m, chi)
    claims(P, I, D, mk, chi, m)
    tx_cap = float(re.search(r"distribution system is ([\d.]+)%", q["tx_cap"]).group(1))
    ok_q = re.search(r"shall be measured (in order that.*?distribution may be accurately determined)", q["ok_measure"])
    tb = -float(M.temp_bias_pct(d["gas_temp_f"]))
    mv = meter_values()
    v = {
        "stamp": insight.stamp_annual(h["year"], "PHMSA's gas distribution annual reports", P["data_as_of"],
                                      "PHMSA adds each year's reports to the file"),
        "takeaways": insight.takeaways([
            f"Customers carry the cost of lost gas: Texas's rule, for the utilities its Railroad Commission "
            f"regulates, disallows lost-gas costs above {tx_cap:g} per cent of the gas a utility takes in unless the "
            f"Commission allows more, and in Oklahoma at least one large utility's approved tariff collects it "
            f"through the gas charge.",
            f"The figure says most where it is far from the rest: {h['tail_hi']} reports for {h['year']} are above "
            f"{h['hi']:g} per cent, beyond anything ordinary meter error produces, though a report cannot say why.",
            "Where gas runs colder than 60 °F, some gas reported as lost was in fact delivered: cold gas is denser, "
            "a meter that does not correct for temperature counts too little of it, and that gas is then charged "
            "to every customer through the gas charge instead."]),
        "hero": hero(P, I),
        "clip": insight.clip(CLIP, "How an orifice meter infers flow, why an error every meter shares does "
                                   "not average away, and where it lands. Captions on; about "
                                   f"{round(json.load(open(CLIP, encoding='utf-8'))['duration_s'])} seconds."),
        "h_median": f"{h['median']:g}", "h_year": str(h["year"]), "h_n": f"{h['n']:,}",
        "h_zero": str(h["zero"]), "h_neg": str(h["neg"]),
        "band_lo_r": num(P["model"]["band"]["lo"]), "band_hi_r": num(P["model"]["band"]["hi"]),
        "ok_muni": str(P["owners"]["OK"].get("Municipal Owned", 0)), "ok_n": str(sum(P["owners"]["OK"].values())),
        "q_mix": html.escape(q["report_mix"]), "q_proxy": html.escape(q["report_proxy"]),
        "q_zero": html.escape(q["report_zero"]), "q_partg": html.escape(re.match(r"Unaccounted for gas as a percent of total consumption", q["partg"]).group(0)),
        "q_tx_meter": html.escape(q["tx_meter"]), "q_ok": html.escape(ok_q.group(1)),
        "q_ok_pga": html.escape(q["ok_pga"]),
        "tx_cap": f"{tx_cap:.1f}", "tx_cap_c": f"{100 * tx_cap / (100 - tx_cap):.2f}",
        "tx_muni": str(P["owners"]["TX"].get("Municipal Owned", 0)), "tx_n": str(sum(P["owners"]["TX"].values())),
        "rule_year": str(P["rule_year"]), "rule_prev": str(P["rule_year"] - 1),
        "neg_rule": str(P["rule_change"]["negative_2018"]), "neg_rule_zero": str(P["rule_change"]["were_zero_2017"]),
        "y0": str(P["years"][0]), "y1": str(y1), "commodity_from": str(P["commodity_from"]),
        "n_excluded": f"{P['excluded_non_natural_gas']:,}",
        "m_n": f"{d['n_meters']:,}", "m_cg": f"{d['cg_u']:g}", "m_fleet": f"{d['fleet_mean_sd']:g}",
        "m_drift": f"{d['fleet_drift']:g}", "m_meter": f"{d['meter_sd']:g}", "m_uncomp": f"{100 * d['uncomp_share']:.0f}",
        "m_temp": f"{d['gas_temp_f']:.0f}", "m_tempsd": f"{d['gas_temp_sd_f']:g}", "m_timing": f"{d['timing_sd']:g}",
        "m_tbias": f"{tb:.1f}", "m_shared": f"{P['clip']['shared_temp_pct']:.1f}",
        "m_systems": "200,000", "m_scale": f"{float(mk):g}",
        "grid_rows": grid_rows(I),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
        "meter_zip_kb": f"{round(os.path.getsize(METER_ZIP) / 1024) if os.path.exists(METER_ZIP) else 0:,}",
    }
    for st in ("TX", "OK"):
        x = D[st]
        v.update({f"{st.lower()}_year": str(x["year"]), f"{st.lower()}_mcf": f"{x['mcf_per_household']:.0f}",
                  f"{st.lower()}_cg": f"{x['citygate']:.2f}", f"{st.lower()}_pp": f"{x['per_point']:.2f}",
                  f"{st.lower()}_wmed": f"{x['wmedian_pct']:g}", f"{st.lower()}_at": f"{x['at_median']:.2f}",
                  f"{st.lower()}_bill": f"{x['bill']:,.0f}"})
    for k in ("one_beta", "one_u", "one_top_u", "n_r", "n_d", "mmcfd", "imb0_u", "imb1_u", "imb2_u",
              "usd0", "usd1", "usd2", "price_med", "price_first", "price_last"):
        v[k] = mv[k]
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "takeaway.html"), encoding="utf-8").read()
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
    refs = add_citations.PAGES.get("lostgas.html")
    if not refs:
        return text, ["lostgas.html has no entry in add_citations.PAGES"]
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
        print("  lostgas.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  lostgas.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
