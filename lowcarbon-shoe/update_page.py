"""
Write site/lowcarbon-shoe.html from template.html and outputs/payload.json.

Every number on the page comes from the payload (build_lowcarbon_shoe.py, which
re-runs the LCA from the shipped code) or from a file this script measures (the
archive's size); the prose is in the template. The parts other scripts own - the
nav (rebuild_nav.py), the citation markers and Sources list (add_citations.py's
table, applied here) and the ?v= stamps (bust_cache.py) - are kept as the shipped
page has them, so tests/test_generators.py can run this on the shipped tree and
expect no change. The idiom is ethane/update_page.py's.

The hero is page-local (hero.py + an inline script), not the insight kit: the
kit's four chart kinds cannot draw an exploded shoe that changes from one design
to another, and adding a kind to the shared charts.js is outside this page's
scope (eco-shoe DECISIONS.md, 2026-11-07).

claims() asserts every direction and comparison the template's words commit to;
if a rebuild moves one, the generator stops rather than ship prose the payload
contradicts.

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
PAGE = os.path.join(SITE, "lowcarbon-shoe.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "lowcarbon-shoe-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import hero as H  # noqa: E402

TORNADO_LABELS = {
    "P.t1_kwh": ("Final-assembly electricity per pair", "{lo:g}-{hi:g} kWh"),
    "F.rPET_FIBRE": ("Footprint of recycled polyester fibre", "{lo:g}-{hi:g} kg CO2e/kg"),
    "M.lc1.Upper mesh and lining (recycled PET)": ("Mass of LC-1's upper mesh and lining", "{lo:g}-{hi:g} g"),
    "P.etpu_density": ("Density of LC-1's foam", "{lo:g}-{hi:g} kg/m3"),
    "P.etpu_bead_kwh_kg": ("Energy to foam TPU beads (assumed)", "{lo:g}-{hi:g} kWh/kg"),
    "F.TPU": ("Footprint of TPU", "{lo:g}-{hi:g} kg CO2e/kg"),
    "P.eva_density": ("Density of the trainer's EVA foam", "{lo:g}-{hi:g} kg/m3"),
    "P.rtpu_share": ("Recycled share of LC-1's TPU skin", "{lo:g}-{hi:g}"),
}


def pc(x):
    """A percentage as the page prints it: whole numbers."""
    return f"{round(x):,}"


def hero_steps(P):
    g = P["groups"]
    b, bc, d, l = g["baseline"], g["baseline_clean"], g["lc1_design_only"], g["lc1"]
    return [
        f"<p><b>A typical daily trainer.</b> About {round(P['mass_g']['baseline']['product_g'])} g a pair: a foam midsole of EVA, "
        f"a rubber outsole, a polyester mesh upper, foam padding and plastic stiffeners, held together with glue. Making, shipping "
        f"and disposing of one pair emits {P['pair']['baseline']:.1f} kg CO2e in this model.</p>",
        f"<p><b>Taken apart.</b> Of the materials, the upper ({b['upper']:.2f} kg) and the midsole foam ({b['mid']:.2f} kg) are the "
        f"largest. The largest single item is not a part at all: the electricity and fuel of the factories, {b['factory']:.2f} kg. "
        f"The box, the freight and the bin add {b['rest']:.2f} kg.</p>",
        f"<p><b>The same shoe, renewable power.</b> With renewable electricity at final assembly and at the sole maker, factory "
        f"energy falls to {bc['factory']:.2f} kg and the pair to {P['pair']['baseline_clean']:.1f} kg. Nothing about the shoe "
        f"has changed.</p>",
        f"<p><b>LC-1, made on grid power.</b> Recycled polyester, a sole of one plastic and no glue cut the upper to "
        f"{d['upper']:.2f} kg and the outsole to {d['out']:.2f} kg; without a shoebox, the box, freight and bin fall to "
        f"{d['rest']:.2f} kg. The expanded-TPU midsole emits more than the EVA one, {d['mid']:.2f} kg against {b['mid']:.2f} kg, "
        f"and foaming and moulding it takes more energy, so factory energy rises slightly, to {d['factory']:.2f} kg. "
        f"The pair comes to {P['pair']['lc1_design_only']:.1f} kg.</p>",
        f"<p><b>LC-1 as specified.</b> With renewable electricity at final assembly and at the sole moulder, factory energy "
        f"falls to {l['factory']:.2f} kg and the pair to {P['pair']['lc1']:.1f} kg.</p>",
    ]


def tornado_rows(P):
    rows = []
    for t in P["tornado"]:
        name, fmt = TORNADO_LABELS[t["input"]]
        lo, hi = t["low"], t["high"]
        if t["input"] == "P.rtpu_share":
            rng = f"{round(100 * lo)}-{round(100 * hi)} percent"
        else:
            rng = fmt.format(lo=lo, hi=hi)
        rows.append(f'<tr><td>{name}</td><td>{rng}</td><td class="n">{pc(t["red_at_low"])}</td>'
                    f'<td class="n">{pc(t["red_at_high"])}</td></tr>')
    return "\n".join(rows)


def claims(P, v):
    s, g = P["scenarios"], P["groups"]
    st = P["stages"]["baseline"]
    checks = [
        ("factory energy is slightly more than materials",
         st["part_making"] + st["assembly"] > st["materials"] and (st["part_making"] + st["assembly"]) / st["materials"] < 1.25),
        ("the redesign delivers less than half of the cut", s["design_only"] < s["lc1"] / 2 + 1e-9),
        ("just under half: central between 45 and 50", 45 <= s["lc1"] < 50),
        ("renewable power alone is about a third", 28 <= s["baseline_clean_power"] <= 38),
        ("the redesign is about a fifth", 15 <= s["design_only"] <= 25),
        ("materials-and-construction step is most of the design step", s["design_with_box"] > s["design_only"] / 2),
        ("electricity is the largest step", P["per100_steps"][3][1] > max(P["per100_steps"][1][1], P["per100_steps"][2][1])),
        ("fossil plastic less than half", P["mass_g"]["lc1"]["fossil_virgin_g"] < P["mass_g"]["baseline"]["fossil_virgin_g"] / 2),
        ("factory energy rises slightly on grid power", 1.0 <= g["lc1_design_only"]["factory"] / g["baseline"]["factory"] < 1.1),
        ("LC-1 drop peak is lower", P["fea"]["diff_pct"] < 0),
        ("life is inside 300-500 miles, low end", 483 <= P["life_km"] < 644),
        ("LC-1 does not halve emissions as a single-life shoe (MC median)", P["mc"]["reduction_pct"]["lc1"]["50"] < 50),
        ("a second sole takes the central case past half", s["lc1_resole"] > 50),
        ("clean power alone cuts the trainer by more than the design", s["baseline_clean_power"] > s["design_only"]),
        ("factory energy is the largest single item", g["baseline"]["factory"] == max(g["baseline"].values())),
        ("upper and midsole are the largest material items",
         sorted(["upper", "sock", "mid", "out"], key=lambda k: -g["baseline"][k])[:2] == ["upper", "mid"]),
        ("LC-1 midsole emits more than the EVA one", g["lc1_design_only"]["mid"] > g["baseline"]["mid"]),
        ("LC-1 is lighter", P["shoe_g"]["lc1"] < P["shoe_g"]["base"]),
        ("LC-1 outsole lasts longer", P["wear_km"]["lc1"] > P["wear_km"]["base"]),
        ("baseline drop peak inside the published range", P["fea"]["published"][0] <= P["fea"]["base_N"] <= P["fea"]["published"][1]),
        ("LC-1 softer under a running heel", P["fea"]["heel_ratio"] > 1.2),
        ("energy return higher", P["energy_return"]["lc1"] > P["energy_return"]["base"]),
        ("baseline total below published 6.7-14 kg", P["pair"]["baseline"] < 6.7),
        ("less polymer overall", P["mass_g"]["lc1"]["polymer_g"] < P["mass_g"]["baseline"]["polymer_g"]),
    ]
    bad = [n for n, ok in checks if not ok]
    if bad:
        raise SystemExit("payload contradicts the prose: " + "; ".join(bad))


def values(P):
    import insight
    s = P["scenarios"]
    st = P["stages"]["baseline"]
    mc = P["mc"]
    fac = st["part_making"] + st["assembly"]
    m = P["mass_g"]
    v = {
        "base_pair": f"{P['pair']['baseline']:.1f}",
        "factory_pct": pc(100 * fac / P["pair"]["baseline"]),
        "red_design": pc(s["design_only"]),
        "red_lc1": pc(s["lc1"]),
        "red_resole": pc(s["lc1_resole"]),
        "red_designbox": pc(s["design_with_box"]),
        "life_mi": f"{round(P['life_km'] / 1.609344, -1):.0f}",
        "red_baseclean": pc(s["baseline_clean_power"]),
        "takeaways": insight.takeaways([
            f"In this model a typical trainer emits {P['pair']['baseline']:.1f} kg of greenhouse gas per pair, and "
            f"{pc(100 * fac / P['pair']['baseline'])} percent of it is factory energy rather than material.",
            f"Renewable electricity at final assembly and at the sole maker cuts that by {pc(s['baseline_clean_power'])} percent; "
            f"the LC-1 redesign alone cuts {pc(s['design_only'])} percent, and the two together just under half.",
            "LC-1 needs less than half as much new fossil plastic, but no scheme open to a runner recycles its sole back "
            "into plastic today.",
        ]),
        "hero": H.hero_section(P, hero_steps(P)),
        "waterfall": H.figure(P, "<p>Kg CO2e per 100 km, central case: the typical trainer, the three changes, LC-1, "
                                 "and LC-1 with a second sole unit on the same upper.</p>", H.waterfall_svg),
        "life": f"{round(P['life_km']):,}",
        "b100": f"{P['base_per100']:.2f}",
        "l100": f"{P['per100']['lc1']:.2f}",
        "mc_med": pc(mc["reduction_pct"]["lc1"]["50"]),
        "mc_lo": pc(mc["reduction_pct"]["lc1"]["5"]),
        "mc_hi": pc(mc["reduction_pct"]["lc1"]["95"]),
        "mc_p": pc(100 * mc["p_lc1_ge_50"]),
        "mc_rmed": pc(mc["reduction_pct"]["lc1_resole_U"]["50"]),
        "mc_rp": pc(100 * mc["p_lc1_resole_U_ge_50"]),
        "poly_lc1": f"{round(m['lc1']['polymer_g'])}",
        "poly_base": f"{round(m['baseline']['polymer_g'])}",
        "fossil_lc1": f"{round(m['lc1']['fossil_virgin_g'])}",
        "fossil_base": f"{round(m['baseline']['fossil_virgin_g'])}",
        "part_lc1": f"{P['particles']['lc1']:.1f}",
        "part_base": f"{P['particles']['baseline']:.1f}",
        "drop_base": f"{round(P['fea']['base_N']):,}",
        "drop_lc1": f"{round(P['fea']['lc1_N']):,}",
        "drop_diff": pc(abs(P["fea"]["diff_pct"])),
        "er_lc1": f"{P['energy_return']['lc1']:.1f}",
        "er_base": f"{P['energy_return']['base']:.1f}",
        "shoe_lc1": f"{round(P['shoe_g']['lc1'])}",
        "shoe_base": f"{round(P['shoe_g']['base'])}",
        "wear_lc1": f"{round(P['wear_km']['lc1'], -1):,.0f}",
        "wear_base": f"{round(P['wear_km']['base'], -1):,.0f}",
        "heel_ratio": f"{P['fea']['heel_ratio']:.1f}",
        "tornado_rows": tornado_rows(P),
        "tpu_factor": f"{P['inputs']['tpu']:.1f}",
        "tpu_stress": pc(s["lc1_tpu_stress"]),
        "cff": pc(s["lc1_cff_5050"]),
        "t1_kwh": f"{P['inputs']['t1_kwh']:.1f}",
        "grid": f"{round(1000 * P['inputs']['grid'])}",
        "script": H.SCRIPT,
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
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
    refs = add_citations.PAGES.get("lowcarbon-shoe.html")
    if not refs:
        return text, ["lowcarbon-shoe.html has no entry in add_citations.PAGES"]
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
        print("  lowcarbon-shoe.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  lowcarbon-shoe.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
