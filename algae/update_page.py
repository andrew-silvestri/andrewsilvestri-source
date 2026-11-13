"""
Write site/algae.html from template.html and outputs/payload.json.

Every number on the page comes from the payload or from a file this script measures (the archive's
size). The prose is in the template. The parts other scripts own - the nav (rebuild_nav.py), the
citation markers and Sources list (add_citations.py's table, applied here) and the ?v= stamps
(bust_cache.py) - are kept as the shipped page has them, so tests/test_generators.py can run this on
the shipped tree and expect no change. The idiom is lead/update_page.py's.

The hero is a funnel drawn in SVG here: one row per route, three nested bars per row (carbon fixed,
carbon that reaches 1,000 m or burial, net carbon held out of the air for 100 years) and a cost line.
Two drawings ship, 900 px and 320 px, each shown at its drawn size (HANDOFF trap 22). fits() checks
that no row's words collide before the page is written.

claims() asserts the directions and ranks the template's words commit to. If a rebuild moves one,
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
PAGE = os.path.join(SITE, "algae.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "algae-code.zip")
NAV_FROM = os.path.join(SITE, "climate-cost.html")   # first build only: a page in the same nav group
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

MINUS = "−"
LO, HI = -70, 100          # the funnel's axis, t C per 100 t fixed
CH_SANS, CH_MONO = 7.4, 7.6  # generous px per character at 13 px sans / 12 px mono, for fits()


def n(x):
    """A per-100 figure as words show it: whole tonnes, a true minus sign."""
    r = round(x)
    return (MINUS if r < 0 else "") + f"{abs(r):,}"


def rng(t):
    return f"{n(t[0])} to {n(t[2])}"


def usd(x):
    return f"${x:,.0f}"


# ------------------------------------------------------------------ hero ---
def row_text(f, C):
    """(label, value at each stage, cost line) for one route."""
    k = f["key"]
    fixed = "100 t fixed"
    if f["deep"][1] is None:
        deep = "no global estimate"
    else:
        deep = f"{n(f['deep'][1])} t deep"
    if f["gross"]:
        net = f"0 net ({n(f['gross'][1])} gross)"
    else:
        net = f"{n(f['held'][1])} t ({rng(f['held'])})"
    cost = {"plankton": "natural cycle, no cost",
            "kelp": "natural cycle, no cost",
            "iron": f"under {usd(C['iron']['lo'])} to over {usd(C['iron']['hi'])} per t CO2, model",
            "seaweed": f"{usd(C['seaweed']['lo'])} to {usd(C['seaweed']['hi'])} per t CO2, model",
            "pondfuel": "not a removal",
            "pondburied": f"{usd(C['pondburied']['lo'])} to {usd(C['pondburied']['hi'])} per t CO2, model"}[k]
    return f["label"], (fixed, deep, net), cost


ROW_H, TOP, AXIS_H = 84, 6, 34


def funnel_svg(P, W, cls):
    F, C = P["funnel"], P["costs"]
    H = TOP + ROW_H * len(F) + AXIS_H
    x = lambda v: round(W * (v - LO) / (HI - LO), 1)
    out = [f'<svg class="{cls} funnel" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-labelledby="algae-desc">']
    for i, f in enumerate(F):
        y0 = TOP + i * ROW_H
        label, vals, cost = row_text(f, C)
        by = y0 + 22                                   # bar band: by .. by+24
        out.append(f'<g class="row r-{f["key"]}">')
        out.append(f'<text class="lab" x="0" y="{y0 + 14}">{html.escape(label)}</text>')
        for k, v in enumerate(vals):
            only = "" if k == 2 else f' data-only="{k}"'
            out.append(f'<text class="val v{k}"{only} x="{W}" y="{y0 + 14}" text-anchor="end">{html.escape(v)}</text>')
        # stage 0: 100 t fixed
        out.append(f'<rect class="b0" data-o="0" x="{x(0)}" y="{by}" width="{x(100) - x(0)}" height="24"/>')
        # stage 1: deep or buried
        if f["deep"][1] is not None and f["deep"][1] > 0:
            out.append(f'<rect class="b1" data-o="1" x="{x(0)}" y="{by + 4}" '
                       f'width="{max(x(f["deep"][1]) - x(0), 1.5)}" height="16"/>')
        # stage 2: net held at 100 years, with its range
        lo, c, hi = f["held"]
        if f["gross"]:
            g = f["gross"][1]
            out.append(f'<rect class="bg" data-o="2" x="{x(0)}" y="{by + 7}" width="{x(g) - x(0)}" height="10"/>')
        elif c != 0:
            a, b = sorted((x(0), x(c)))
            out.append(f'<rect class="b2{" neg" if c < 0 else ""}" data-o="2" x="{a}" y="{by + 7}" '
                       f'width="{round(b - a, 1)}" height="10"/>')
        if hi != lo:
            cy = by + 12
            out.append(f'<path class="wh" data-o="2" d="M{x(lo)},{cy}H{x(hi)}M{x(lo)},{cy - 6}V{cy + 6}'
                       f'M{x(hi)},{cy - 6}V{cy + 6}"/>')
        out.append(f'<path class="zero" d="M{x(0)},{by - 3}V{by + 27}"/>')
        out.append(f'<text class="cost" data-o="3" x="0" y="{by + 40}">{html.escape(cost)}</text>')
        out.append('</g>')
    ya = TOP + ROW_H * len(F) - 4
    for v in (-50, 0, 50, 100):
        t = (MINUS + "50" if v < 0 else str(v)) + (" t" if v == 100 else "")
        anchor = "end" if v == 100 else "middle"
        out.append(f'<path class="tick" d="M{x(v)},{ya}v6"/>'
                   f'<text class="ax" x="{x(v)}" y="{ya + 20}" text-anchor="{anchor}">{t}</text>')
    out.append("</svg>")
    return "\n".join(out)


def fits(P, W):
    """Label and the widest value on a row must not meet; nor may a cost line overrun."""
    bad = []
    for f in P["funnel"]:
        label, vals, cost = row_text(f, P["costs"])
        need = len(label) * CH_SANS + max(len(v) for v in vals) * CH_MONO + 12
        if need > W:
            bad.append(f"{W}px: {label!r} + value needs {need:.0f}px")
        if len(cost) * CH_MONO > W:
            bad.append(f"{W}px: cost line {cost!r}")
    return bad


def desc(P):
    parts = []
    for f in P["funnel"]:
        label, vals, cost = row_text(f, P["costs"])
        if f["deep"][1] is None:
            d = "no global estimate of the share that reaches 1,000 meters"
        else:
            k = round(f["deep"][1])
            d = f"{n(k)} {'tonne reaches' if k == 1 else 'tonnes reach'} 1,000 meters or burial"
        parts.append(f"{label}: of 100 tonnes of carbon fixed, {d}; net held out of the air after 100 years: "
                     f"{vals[2].replace(' t ', ' tonnes ')}; cost: {cost}.")
    return " ".join(parts)


def hero(P, steps):
    bad = fits(P, 900) + fits(P, 320)
    if bad:
        raise SystemExit("hero words collide:\n  " + "\n  ".join(bad))
    cards = "\n".join(f'<div class="step" data-step="{k}"><p>{s}</p></div>' for k, s in enumerate(steps))
    return (f'<figure class="funnelfig wide" aria-label="Carbon funnel, per 100 tonnes fixed">\n'
            f'<div class="funnel-fig">\n<p id="algae-desc" hidden>{html.escape(desc(P))}</p>\n'
            f'{funnel_svg(P, 900, "f-wide")}\n{funnel_svg(P, 320, "f-phone")}\n'
            f'<p class="funnel-key"><span class="k0"></span>fixed <span class="k1"></span>deep or buried '
            f'<span class="k2"></span>net at 100 years <span class="k3"></span>natural gross flow '
            f'<span class="k4"></span>net emission</p>\n</div>\n'
            f'<div class="funnel-steps">\n{cards}\n</div>\n</figure>')


# --------------------------------------------------------------- depth chart ---
def depth_svg(P, W, cls):
    cur = P["siegel"]["curve"]
    H, L, R, T, B = 300, 64 if W > 400 else 52, 16, 14, 40
    dmax = 3600
    x = lambda f: round(L + (W - L - R) * f, 1)
    y = lambda d: round(T + (H - T - B) * d / dmax, 1)
    band = " ".join(f"{x(r['p10'])},{y(r['depth'])}" for r in cur) + " " + \
           " ".join(f"{x(r['p90'])},{y(r['depth'])}" for r in reversed(cur))
    line = " ".join(f"{x(r['mean'])},{y(r['depth'])}" for r in cur)
    out = [f'<svg class="{cls} depth" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-labelledby="depth-desc">',
           f'<polygon class="band" points="{band}"/>', f'<polyline class="mean" points="{line}"/>']
    for d in (0, 1000, 2000, 3000):
        out.append(f'<path class="grid" d="M{L},{y(d)}H{W - R}"/><text class="ax" x="{L - 6}" y="{y(d) + 4}" '
                   f'text-anchor="end">{d:,} m</text>')
    for f in (0, .5, 1):
        a = {0: "start", .5: "middle", 1: "end"}[f]
        out.append(f'<text class="ax" x="{x(f)}" y="{H - 20}" text-anchor="{a}">{int(f * 100)}%</text>')
    out.append(f'<text class="ax" x="{(L + W - R) / 2}" y="{H - 4}" text-anchor="middle">'
               f'share still out of the air after 100 years</text>')
    for d, v in sorted(P["siegel"]["at100"].items(), key=lambda kv: int(kv[0])):
        if int(d) in (208, 530, 1022, 2100):
            px, py = x(v), y(int(d))
            if v < .6:      # shallow: the curve runs right of the point, so the label sits above it
                lab = f'<text class="lab" x="{px + 8}" y="{py - 6}" text-anchor="start">{round(100 * v)}%</text>'
            else:           # deep: the curve runs down and right, so the label sits below and left
                lab = f'<text class="lab" x="{px - 10}" y="{py + 18}" text-anchor="end">{round(100 * v)}%</text>'
            out.append(f'<circle class="pt" cx="{px}" cy="{py}" r="4"/>' + lab)
    out.append("</svg>")
    return "\n".join(out)


def depth_chart(P):
    a = P["siegel"]["at100"]
    d = (f"Share of carbon dioxide released at a given depth that is still out of contact with the air after 100 "
         f"years, ocean average: {round(100 * a['208'])} percent at 208 meters, {round(100 * a['530'])} percent at "
         f"530 meters, {round(100 * a['1022'])} percent at 1,022 meters, {round(100 * a['2100'])} percent at 2,100 meters.")
    return (f'<figure class="depthfig">\n<p id="depth-desc" hidden>{html.escape(d)}</p>\n'
            f'{depth_svg(P, 600, "d-wide")}\n{depth_svg(P, 320, "d-phone")}\n</figure>')


# ---------------------------------------------------------------- claims ---
def by(P):
    return {f["key"]: f for f in P["funnel"]}


def claims(P):
    F, S, G, N, C = by(P), P["siegel"]["at100"], P["gcb"], P["npp"], P["costs"]
    best = max(P["funnel"], key=lambda f: f["held"][1])
    c = [
        ("'nearly half' of all NPP is ocean", .4 < N["ocean"] / (N["ocean"] + N["land"]) < .5),
        ("'about four times' fossil emissions, both NPP figures", 3.5 < N["sat"][0] / G["fossil"] and
         N["ocean"] / G["fossil"] < 5),
        ("ocean sink is a small share of ocean NPP (under a tenth)", G["ocean10"] / N["ocean"] < .1),
        ("retention rises with depth", S["208"] < S["530"] < S["1022"] < S["2100"] < S["3083"]),
        ("'under a tenth' at 208 m", S["208"] < .1),
        ("'about two thirds' at 1,022 m", .6 < S["1022"] < .72),
        ("'nearly nine in ten' at 2,100 m", .85 <= S["2100"] < .9),
        ("sunk seaweed has the largest central net figure", best["key"] in ("seaweed",)),
        ("buried pond algae second", sorted(P["funnel"], key=lambda f: -f["held"][1])[1]["key"] == "pondburied"),
        ("fuel route is net negative in every case", F["pondfuel"]["held"][2] < 0),
        ("iron central is a few tonnes", 0 < F["iron"]["held"][1] < 5),
        ("'Thirteen open-ocean experiments'", P["record"]["iron_experiments"] == 13),
        ("iron: net central exceeds deep central (text explains why)", F["iron"]["held"][1] > F["iron"]["deep"][1]),
        ("'about 1 to 2 tonnes of every 100' past 1,000 m", 1 <= round(100 * N["flux1000"][0] / N["ocean"]) and
         round(100 * N["flux1000"][1] / N["ocean"]) == 2),
        ("seaweed central air share below DeAngelo's 0.6 threshold for costs under $400",
         F["seaweed"]["from_air"][1] < C["seaweed"]["below400_air"]),
        ("'less than half a tonne of each 100' buried", 100 * N["burial"][1] / N["ocean"] < .5),
        ("seaweed sunk on a shelf keeps under 5 t", F["seaweed"]["shelf"] < 5),
        ("seaweed best case above the CDR.fyi average price", C["seaweed"]["best"] > C["cdrfyi_2024"]),
        ("'even the high case leaves a quarter on the table' (seaweed high < 75)", F["seaweed"]["held"][2] < 75),
    ]
    bad = [name for name, ok in c if not ok]
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    F, S, G, N, C, R = by(P), P["siegel"]["at100"], P["gcb"], P["npp"], P["costs"], P["record"]
    sw, pb, fe, ir, pl, kp = F["seaweed"], F["pondburied"], F["pondfuel"], F["iron"], F["plankton"], F["kelp"]
    v = {
        "npp": f"{N['ocean']:g}", "npp_share": f"{100 * N['ocean'] / (N['ocean'] + N['land']):.0f}",
        "npp_macro": f"{N['macro']:g}", "npp_sat_lo": f"{N['sat'][0]:g}", "npp_sat_hi": f"{N['sat'][1]:g}",
        "fossil": f"{G['fossil']:.1f}", "gcb_year": str(G["last"]), "npp_x": f"{N['ocean'] / G['fossil']:.1f}",
        "npp_x_lo": f"{N['sat'][0] / G['fossil']:.1f}", "npp_span_lo": f"{N['span'][0]:g}",
        "npp_span_hi": f"{N['span'][1]:g}", "npp_round_lo": f"{round(N['sat'][0], -1):.0f}",
        "npp_round_hi": f"{round(N['ocean'], -1):.0f}",
        "ocean_sink": f"{G['ocean10']:.1f}", "sink_from": str(G["from"]), "sink_to": str(G["last"]),
        "export_lo": str(N["export"][0]), "export_hi": str(N["export"][1]), "flux_lo": f"{N['flux1000'][0]:g}", "flux_hi": f"{N['flux1000'][1]:g}",
        "burial_lo": f"{N['burial'][0]:g}", "burial_hi": f"{N['burial'][1]:g}",
        "pl_deep": n(pl["deep"][1]), "pl_gross_r": rng(pl["gross"]),
        "kp_gross_r": rng(kp["gross"]),
        "r208": f"{100 * S['208']:.0f}", "r530": f"{100 * S['530']:.0f}", "r1022": f"{100 * S['1022']:.0f}",
        "r2100": f"{100 * S['2100']:.0f}", "s208_50": f"{100 * P['siegel']['check_208_50']:.0f}",
        "sw_air": f"{sw['from_air'][1]:.2f}", "sw_reach": f"{sw['reach'][1]:.2f}", "sw_ret": f"{sw['retained'][1]:.2f}",
        "sw_air_hi": f"{sw['from_air'][2]:.2f}",
        "sw_after_air": n(100 * sw["from_air"][1]), "sw_after_reach": f"{100 * sw['from_air'][1] * sw['reach'][1]:.1f}",
        "sw_held": n(sw["held"][1]), "sw_range": rng(sw["held"]), "sw_shelf": f"{sw['shelf']:.1f}",
        "dea_lo": f"{R['deangelo_range'][0]:.1f}", "dea_hi": f"{R['deangelo_range'][1]:g}",
        "lit_lo": f"{R['lit_range'][0]:.1f}", "lit_hi": f"{R['lit_range'][1]:.2f}",
        "c_below400": f"{C['seaweed']['below400_air']:.1f}", "berger_lo": f"{R['berger_with_feedback']:.2f}",
        "ir_held": n(ir["held"][1]), "ir_range": rng(ir["held"]), "ir_export": n(ir["export"][1]),
        "ir_ratio_hi": f"{ir['ratio'][2]:.2f}", "ir_n": str(R["iron_experiments"]),
        "ir_first": str(R["iron_first"]), "ir_last": str(R["iron_last"]), "eifex": str(R["eifex_year"]),
        "lohafex": str(R["lohafex_year"]), "lohafex_t": str(R["lohafex_iron_t"]), "haida": str(R["haida_year"]),
        "haida_t": str(R["haida_t"]),
        "fe_held": n(fe["held"][1]), "fe_range": rng(fe["held"]),
        "pb_held": n(pb["held"][1]), "pb_range": rng(pb["held"]),
        "rt_t": f"{R['running_tide_t']:,}", "rt_year": str(R["running_tide_year"]), "rt_shut": R["running_tide_shut"],
        "bp_admin": R["brilliant_planet_admin"],
        "c_iron_lo": usd(C["iron"]["lo"]), "c_iron_hi": usd(C["iron"]["hi"]),
        "c_sw_best": usd(C["seaweed"]["best"]), "c_sw_nut": usd(C["seaweed"]["nutrient"]),
        "c_sw_hi": usd(C["seaweed"]["hi"]), "c_sw_nasem": usd(C["seaweed_nasem"]),
        "c_pb_lo": usd(C["pondburied"]["lo"]), "c_pb_hi": usd(C["pondburied"]["hi"]),
        "c_dac": usd(C["dac_paid"]), "c_cdrfyi": usd(C["cdrfyi_2024"]), "c_sw_typ": usd(C["seaweed"]["typ_lo"]),
        "s208_printed": f"{100 * P['siegel']['printed_208_50']:.0f}", "ocean_printed": f"{G['printed']:g}",
        "oschlies": f"{R['oschlies_ratio']:.2f}", "co2_dry": f"{R['co2_per_dry_t']:.1f}",
        "nrel_energy": f"{R['nrel_energy']:.2f}",
        "stamp": (f'<p class="stamp">Data: Global Carbon Budget 2025 (through {G["last"]}); ocean retention from '
                  f'Siegel and colleagues (2021); route figures from papers published 1998 to 2026. '
                  f'This page does not update.</p>'),
        "depth_chart": depth_chart(P),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    v["takeaways"] = insight.takeaways([
        f"Ocean algae fix about {v['npp_round_lo']} to {v['npp_round_hi']} billion tonnes of carbon a year, about "
        f"four times what fossil fuels emit, but that flow was in balance before industry and removes almost none "
        f"of the added carbon.",
        f"Of 100 tonnes of carbon fixed by farmed seaweed and sunk in deep water, about {v['sw_held']} tonnes are "
        f"still out of the air after a century in the central case, against about {sw['shelf']:.1f} tonnes if "
        f"the same crop is released at 208 meters.",
        f"Algae turned into fuel or feed remove nothing: the carbon goes back to the air, and the energy used "
        f"leaves a net emission."])
    steps = [
        f"<b>Start with 100 tonnes.</b> Each row is one route. The gray bar is 100 tonnes of carbon fixed by "
        f"photosynthesis, the same for every route.",
        f"<b>How much goes deep.</b> The darker gray bar is the part that sinks below 1,000 meters or is buried. For natural "
        f"plankton it is about {v['pl_deep']} tonnes. Sunk seaweed and buried pond algae send most of their carbon "
        f"down by design.",
        f"<b>How much stays out of the air.</b> The blue bar is the net carbon taken from the air and still out of it "
        f"100 years later; the whisker is the published range. Sunk seaweed keeps about {v['sw_held']} tonnes, buried "
        f"pond algae about {v['pb_held']}, iron about {v['ir_held']}. Natural algae keep none net: their dashed "
        f"gross flow is matched by carbon coming back up. Fuel ends below zero, a net emission.",
        f"<b>What it costs.</b> The line under each bar is the published cost estimate per tonne of CO2, all from "
        f"models. For comparison, Frontier lists an average contracted price of {v['c_dac']} a tonne for direct air "
        f"capture, which stores carbon for thousands of years.",
    ]
    v["hero"] = hero(P, steps)
    claims(P)
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


# values used only inside generated parts (takeaways, step cards), not as template placeholders
INTERNAL = {"npp_round_lo", "npp_round_hi", "pl_deep", "ir_n", "ir_ratio_hi"}


def render(P):
    t = open(TEMPLATE, encoding="utf-8").read()
    v = values(P)
    missing = sorted(set(re.findall(r"{{(\w+)}}", t)) - set(v) - {"nav"})
    if missing:
        raise SystemExit(f"template placeholders without a value: {missing}")
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)) - INTERNAL)
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("algae.html")
    if not refs:
        return text, ["algae.html has no entry in add_citations.PAGES"]
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
        print("  algae.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  algae.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
