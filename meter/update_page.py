"""
Write site/meter.html from template.html and outputs/payload.json.

Every number on the page comes from the payload or from a file this script
measures (the archive's size); the prose is in the template. The parts of
the shipped page that other scripts own - the nav (rebuild_nav.py), the
citation markers and Sources list (add_citations.py's table, applied here),
the ?v= stamps (bust_cache.py) and image dimensions - are kept as the
shipped page has them, so tests/test_generators.py can run this on the
shipped tree and expect no change. The idiom is beauty/update_page.py's.

Each printed Monte Carlo figure is rounded to the numerical tolerance JCGM
101 7.9.4 reached for it (payload "delta"), never to a precision it does not
have.

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "meter.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "meter-code.zip")
sys.path.insert(0, ROOT)

LABELS = {"C": "discharge coefficient", "dp": "differential pressure", "p1": "static pressure",
          "T1": "temperature", "d": "bore diameter", "D": "pipe diameter",
          "composition": "gas composition", "Z": "compressibility equation"}


def dec_for(delta):
    """Decimal places that a figure with numerical tolerance delta can carry."""
    return max(0, -int(math.floor(math.log10(delta)))) if delta > 0 else 3


def pc(r, key="u", scale=100.0):
    """A Monte Carlo result r[key] as a percentage, to its own tolerance."""
    return f"{r[key] * scale:.{dec_for(r['delta'] * scale)}f}"


def money(x, sig=2):
    """Dollars to sig significant figures, written out."""
    v = float(f"{x:.{sig}g}")
    if v >= 1e6:
        return f"{v / 1e6:g} million"
    return f"{v:,.0f}"


def values(P):
    s0, s1, s2 = (P["system"][k]["results"] for k in ("fC0", "fC1", "fC1r"))
    m0, m1, m2 = (P["money"][k] for k in ("fC0", "fC1", "fC1r"))
    single = P["single"]
    groups = [g for g in LABELS]
    top = max(groups, key=lambda g: single[g]["u"])
    second = sorted(groups, key=lambda g: -single[g]["u"])[1]
    sw = P["sweep"]
    by0 = P["system"]["fC0"]["by_input"]
    by1 = P["system"]["fC1"]["by_input"]
    big0 = max(groups, key=lambda g: by0[g]["u"])
    big1 = max(groups, key=lambda g: by1[g]["u"])
    n_r = sum(1 for m in P["meters"] if m["role"] == "R")
    n_d = sum(1 for m in P["meters"] if m["role"] == "D")
    zip_kb = round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0
    a1 = P["eia_a1"]
    ph = P["phmsa"]
    hh = P["price"]
    last = lambda fc, k: sw[fc][-1][k]   # noqa: E731
    first = lambda fc, k: sw[fc][0][k]   # noqa: E731
    v = {
        "n_r": n_r, "n_d": n_d,
        "mmcfd": f"{P['throughput']['mmcfd']:.0f}",
        "mmbtud": f"{P['throughput']['mmbtud']:,.0f}",
        "one_u": pc(single["all"]), "one_U95": f"{2 * single['all']['u'] * 100:.{dec_for(2 * single['all']['delta'] * 100)}f}",
        "one_top": LABELS[top], "one_top_u": pc(single[top]),
        "one_second": LABELS[second], "one_second_u": pc(single[second]),
        "one_dp_u": pc(single["dp"]), "one_T_u": pc(single["T1"]), "one_comp_u": pc(single["composition"]),
        "one_Z_u": pc(single["Z"]),
        "imb0_u": pc(s0["imb_e"]), "imb1_u": pc(s1["imb_e"]),
        "imb0_lo": pc(s0["imb_e"], "low"), "imb0_hi": pc(s0["imb_e"], "high"),
        "imb1_lo": pc(s1["imb_e"], "low"), "imb1_hi": pc(s1["imb_e"], "high"),
        "imb2_u": pc(s2["imb_e"]), "imb2_lo": pc(s2["imb_e"], "low"), "imb2_hi": pc(s2["imb_e"], "high"),
        "tot2_u": pc(s2["rec_v"]), "usd2": money(m2["u_usd_yr"]), "usd2_95": money(m2["half95_usd_yr"]),
        "mmbtu2": f"{m2['u_mmbtud']:,.0f}",
        "C2_u": pc(P["system"]["fC1r"]["by_input"]["C"]),
        "sw_tot2_100": f"{last('fC1r', 'u_total') * 100:.2f}", "sw_imb2_100": f"{last('fC1r', 'u_imb') * 100:.3f}",
        "tot0_u": pc(s0["rec_v"]), "tot1_u": pc(s1["rec_v"]),
        "usd0": money(m0["u_usd_yr"]), "usd1": money(m1["u_usd_yr"]),
        "usd0_95": money(m0["half95_usd_yr"]), "usd1_95": money(m1["half95_usd_yr"]),
        "mmbtu0": f"{m0['u_mmbtud']:,.0f}", "mmbtu1": f"{m1['u_mmbtud']:,.0f}",
        "big0": LABELS[big0], "big1": LABELS[big1],
        "big0_u": pc(by0[big0]), "big1_u": pc(by1[big1]),
        "C0_u": pc(by0["C"]), "C1_u": pc(by1["C"]),
        "sw_tot0_1": f"{first('fC0', 'u_total') * 100:.2f}", "sw_tot0_100": f"{last('fC0', 'u_total') * 100:.3f}",
        "sw_tot1_1": f"{first('fC1', 'u_total') * 100:.2f}", "sw_tot1_100": f"{last('fC1', 'u_total') * 100:.2f}",
        "sw_imb0_100": f"{last('fC0', 'u_imb') * 100:.3f}", "sw_imb1_100": f"{last('fC1', 'u_imb') * 100:.3f}",
        "price_med": f"{hh['median']:.2f}", "price_mean": f"{hh['mean']:.2f}",
        "price_first": hh["first"], "price_last": hh["last"], "price_max": f"{hh['max']:.2f}",
        "price_max_month": hh["max_month"],
        "a1_year": a1["year"], "a1_pct": f"{a1['printed_pct']:.1f}",
        "a1_cons_tcf": f"{a1['consumption_mmcf'] / 1e6:.1f}",
        "ph_year": ph["year"], "ph_n": f"{ph['reports']:,}", "ph_median": f"{ph['median']:.2f}",
        "ph_neg": f"{ph['negative']:,}", "ph_p10": f"{ph['p10']:.2f}", "ph_p90": f"{ph['p90']:.2f}",
        "cd_u": f"{P['defaults']['cd_u_pct']:.2f}",
        "trials_min": f"{min(r['imb_e']['trials'] for r in (s0, s1, s2)):,}",
        "one_D_mm": f"{P['single_design']['D_mm']:.1f}", "one_beta": f"{P['single_design']['beta']:.2f}",
        "zip_kb": f"{zip_kb:,}",
    }
    claims(P, single, top, s0, s1, s2, m0, m1, m2, by0, by1, sw)
    return v


def claims(P, single, top, s0, s1, s2, m0, m1, m2, by0, by1, sw):
    """The template's words that depend on which way the numbers fall. If a rebuild moves
    one, the generator stops here rather than shipping prose the payload contradicts."""
    u = lambda r: r["u"]   # noqa: E731
    others = [single[g]["u"] for g in LABELS if g != "C"]
    checks = [
        ("the discharge coefficient is the largest input for one meter", top == "C"),
        ("its bar is longer than every other input's put together (figure 1 alt text)", single["C"]["u"] > sum(others)),
        ("doubled single-meter figure sits beside the 0.55% example", 0.4 <= 2 * u(single["all"]) * 100 <= 0.8),
        ("shared-and-alike is the smallest imbalance, ends-apart the largest",
         u(s1["imb_e"]) < u(s0["imb_e"]) < u(s2["imb_e"])),
        ("shared-and-alike: C's share is negligible ('all of it from the rest')", u(by1["C"]) < 0.01 * u(s1["imb_e"])),
        ("ends apart roughly doubles C's effect", 1.7 <= P["system"]["fC1r"]["by_input"]["C"]["u"] / u(by0["C"]) <= 2.3),
        ("money is ordered between the alike and apart cases", m1["u_usd_yr"] < m0["u_usd_yr"] < m2["u_usd_yr"]),
        ("independent: total falls with N", sw["fC0"][-1]["u_total"] < 0.2 * sw["fC0"][0]["u_total"]),
        ("shared: a hundred meters no better than one", sw["fC1"][-1]["u_total"] >= 0.9 * sw["fC1"][0]["u_total"]),
        ("median used because the mean is pulled up", P["price"]["mean"] > P["price"]["median"]),
        ("PHMSA: some reports negative", P["phmsa"]["negative"] > 0),
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


def span(text):
    """The marginalia asides span the grid rows after them (beauty/update_page.py's rule)."""
    main = text[text.index("<main"):text.index("</main>")]
    body = re.sub(r"<aside.*?</aside>", "", main, flags=re.S)
    body = body[body.index(">") + 1:]
    depth, n = 0, 0
    for m in re.finditer(r"<(/?)(\w+)[^>]*?>", body):
        close, tag = m.group(1), m.group(2)
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
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    t = keep_from_shipped(t, shipped)
    t = image_dims(t)
    t = t.replace("{{span}}", str(span(t)))
    return t


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("meter.html")
    if not refs:
        return text, ["meter.html has no entry in add_citations.PAGES"]
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
        print("  meter.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  meter.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
