"""
Write site/scales.html from template.html and outputs/payload.json.

Every number on the page comes from the payload (build_scales.py) or is a published figure the template cites
by name; the prose is in the template. The parts other scripts own - the nav (rebuild_nav.py), the citation
markers and Sources list (add_citations.py's table, applied here) and the ?v= stamps (bust_cache.py) - are kept
as the shipped page has them, so tests/test_generators.py can run this on the shipped tree and expect no change.
The idiom is oxygen/update_page.py's.

The hero is one log-log chart, mass (kg) against power per kilogram (W/kg), drawn here as two SVGs (900px and
320px) whose layers carry data-o, the step they belong to; site/assets/scales.js adds the layers as the reader
scrolls. The city chart is a static pair of SVGs drawn the same way.

claims() asserts every direction and range the template's words commit to. If a rebuild moves one, the
generator stops rather than ship prose the payload contradicts.

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import html
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "scales.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "scales-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

E = html.escape
SUP = str.maketrans("-0123456789", "−0123456789")


def sig(x, k=2):
    """x to k significant figures, with thousands separators, no trailing zeros."""
    if x == 0:
        return "0"
    d = k - 1 - int(math.floor(math.log10(abs(x))))
    r = round(x, d)
    s = f"{r:,.{max(d, 0)}f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


# ------------------------------------------------------------------ hero ---
X0, X1, Y0, Y1 = -17, 33, -6, 3       # log10 kg, log10 W/kg


def frame(wide):
    if wide:
        return dict(W=900, H=500, L=60, R=14, T=12, B=48, xt=range(-16, 33, 8), yt=range(-6, 4))
    return dict(W=320, H=440, L=44, R=8, T=12, B=44, xt=range(-16, 33, 16), yt=range(-6, 4, 1))


def scaler(f):
    pw, ph = f["W"] - f["L"] - f["R"], f["H"] - f["T"] - f["B"]

    def sx(x):
        return f["L"] + (x - X0) / (X1 - X0) * pw

    def sy(y):
        return f["T"] + (Y1 - y) / (Y1 - Y0) * ph
    return sx, sy


def pow10(n, unit=""):
    """10^n as SVG text: the exponent as a raised tspan at 12px."""
    if n == 0:
        return "1" + unit
    if n == 1:
        return "10" + unit
    return f'10<tspan dy="-5" font-size="12">{str(n).translate(SUP)}</tspan><tspan dy="5">{unit}</tspan>'


def axes(f, sx, sy, xlab, ylab, xticks, yticks, xfmt, yfmt, cls):
    out = []
    x_lo, x_hi = f["L"], f["W"] - f["R"]
    y_lo, y_hi = f["T"], f["H"] - f["B"]
    for t in yticks:
        y = sy(t)
        out.append(f'<path class="grid" d="M{x_lo:.1f} {y:.1f}H{x_hi:.1f}"/>')
        out.append(f'<text class="tick" x="{x_lo - 6:.1f}" y="{y + 4:.1f}" text-anchor="end">{yfmt(t)}</text>')
    for t in xticks:
        x = sx(t)
        out.append(f'<path class="ax" d="M{x:.1f} {y_hi:.1f}v5"/>')
        out.append(f'<text class="tick" x="{x:.1f}" y="{y_hi + 19:.1f}" text-anchor="middle">{xfmt(t)}</text>')
    out.append(f'<path class="ax" d="M{x_lo:.1f} {y_lo:.1f}V{y_hi:.1f}H{x_hi:.1f}"/>')
    out.append(f'<text class="axt" x="{(x_lo + x_hi) / 2:.1f}" y="{f["H"] - 6:.1f}" text-anchor="middle">{E(xlab)}</text>')
    out.append(f'<text class="axt" transform="translate(12 {(y_lo + y_hi) / 2:.1f}) rotate(-90)" '
               f'text-anchor="middle">{E(ylab)}</text>')
    return out


def squares(pts, sx, sy, s):
    return "".join(f"M{sx(x) - s / 2:.1f} {sy(y) - s / 2:.1f}h{s}v{s}h-{s}z" for x, y in pts)


def hero_svg(P, wide):
    f = frame(wide)
    sx, sy = scaler(f)
    L, F, St = P["life"], P["fuel"], P["stars"]
    cls = "plot-wide" if wide else "plot-phone"
    out = [f'<svg class="plot {cls}" viewBox="0 0 {f["W"]} {f["H"]}" width="{f["W"]}" height="{f["H"]}" '
           f'role="img" aria-labelledby="ladder-desc">']
    out += axes(f, sx, sy, "Mass (kg)", "Power per kilogram (W/kg)", f["xt"], f["yt"],
                lambda t: pow10(t), lambda t: pow10(t), cls)
    lab = (lambda x, y, s, a="start", c="": out.append(
        f'<text{" class=" + chr(34) + c + chr(34) if c else ""} x="{sx(x):.1f}" y="{sy(y):.1f}" '
        f'text-anchor="{a}">{s}</text>'))
    sq = 3 if wide else 2
    # step 0: life
    out.append('<g data-o="0">')
    for k, g in L["groups"].items():
        c = "life bact" if k == "bacteria" else "life"
        out.append(f'<path class="{c}" d="{squares(g["cloud"], sx, sy, sq)}"/>')
    if wide:
        lab(-14.3, -2.7, "Bacteria", "middle", "lab-dim")
        lab(-9.6, -2.7, "Protists", "middle")
        lab(-2.0, -2.7, "Animals and plants", "middle")
    else:
        lab(-6.5, -2.9, "Living things", "middle")
    out.append("</g>")
    # step 1: the band of group means, and one 3/4 law drawn through the mammals
    lo, hi = math.log10(L["band_lo"]), math.log10(L["band_hi"])
    e0, e1 = L["euk_lx_span"]
    out.append('<g data-o="1">')
    out.append(f'<rect class="band" x="{sx(e0):.1f}" y="{sy(hi):.1f}" width="{sx(e1) - sx(e0):.1f}" '
               f'height="{sy(lo) - sy(hi):.1f}"/>')
    m = L["groups"]["mammals"]
    ym = math.log10(m["gmean_wkg"])
    x_top = m["lx_mid"] - (Y1 - ym) / 0.25          # where the 3/4 line leaves the top of the chart
    x_end = e1
    out.append(f'<path class="law" d="M{sx(x_top):.1f} {sy(Y1):.1f}L{sx(x_end):.1f} '
               f'{sy(ym - 0.25 * (x_end - m["lx_mid"])):.1f}"/>')
    if wide:
        lab(x_top + 0.6, 2.62, "One 3/4-power law for all life")
        lab(4.6, lo - 0.08, f"Group averages, {sig(L['band_lo'], 1)} to {sig(L['band_hi'], 1)} W/kg")
    else:
        lab(x_top + 1.5, 2.62, "One 3/4 law")
        lab(5.0, lo - 0.12, f"Band {sig(L['band_lo'], 1)}–{sig(L['band_hi'], 1)} W/kg")
    out.append("</g>")
    # step 2: the fitted tilt inside each group
    out.append('<g data-o="2">')
    for k, g in L["groups"].items():
        a, b = g["icpt"], g["slope"] - 1
        out.append(f'<path class="fit" d="M{sx(g["lx_lo"]):.1f} {sy(a + b * g["lx_lo"]):.1f}'
                   f'L{sx(g["lx_hi"]):.1f} {sy(a + b * g["lx_hi"]):.1f}"/>')
    out.append("</g>")
    # step 3: one resting human
    hx, hy = math.log10(L["human"]["kg"]), math.log10(L["human"]["wkg"])
    out.append('<g data-o="3">')
    out.append(f'<circle class="me" cx="{sx(hx):.1f}" cy="{sy(hy):.1f}" r="{5 if wide else 4}"/>')
    if wide:
        lab(hx + 0.7, hy - 0.08, f"A resting adult, {sig(L['human']['wkg'])} W/kg")
    else:
        lab(hx + 1.6, hy - 0.08, "You, resting")
    out.append("</g>")
    # step 4: the same person with their share of the country's primary energy
    out.append('<g data-o="4">')
    top = math.log10(F["us"]["wkg"])
    out.append(f'<path class="stem" d="M{sx(hx):.1f} {sy(hy):.1f}V{sy(top):.1f}"/>')
    for k, name, short in (("india", "India", "India"), ("world", "World average", "World"),
                           ("us", "United States", "US")):
        y = math.log10(F[k]["wkg"])
        out.append(f'<circle class="me" cx="{sx(hx):.1f}" cy="{sy(y):.1f}" r="{4 if wide else 3}"/>')
        if wide:
            lab(hx + 0.7, y - 0.08, f"{name} with fuel, {sig(F[k]['wkg'])} W/kg")
        else:
            lab(hx + 1.6, y - 0.1, f"{short} {sig(F[k]['wkg'])}")
    out.append("</g>")
    # step 5: main-sequence stars and the Sun
    out.append('<g data-o="5">')
    out.append(f'<path class="star" d="{squares(St["pts"], sx, sy, sq)}"/>')
    xs = [p[0] for p in St["pts"]]
    a, b = St["wkg_icpt"], St["wkg_slope"]
    out.append(f'<path class="sfit" d="M{sx(min(xs)):.1f} {sy(a + b * min(xs)):.1f}'
               f'L{sx(max(xs)):.1f} {sy(a + b * max(xs)):.1f}"/>')
    sunx, suny = math.log10(St["msun"]), math.log10(St["sun_wkg"])
    out.append(f'<circle class="sun" cx="{sx(sunx):.1f}" cy="{sy(suny):.1f}" r="{6 if wide else 5}"/>')
    if wide:
        lab(sunx - 1.0, suny - 0.08, f"The Sun, {sig(St['sun_wkg'])} W/kg", "end", "lab-moss")
        lab(max(xs) + 0.3, a + b * max(xs) + 0.45, "Stars", "end", "lab-moss")
    else:
        lab(sunx - 2.2, suny - 0.1, "Sun", "end", "lab-moss")
        lab(max(xs) + 0.3, a + b * max(xs) + 0.55, "Stars", "end", "lab-moss")
    out.append("</g>")
    out.append("</svg>")
    return "".join(out)


def hero(P, v):
    steps = [
        (0, "Life &middot; fitted law",
         f"Each square is one or more of {v['n_species']} species in Hatton and colleagues' 2019 table: resting "
         f"power divided by body mass. The masses run from {v['bact_lo']} for the smallest bacterium to "
         f"{v['eleph_kg']} kg for an Asian elephant, more than {v['life_decades']} orders of magnitude."),
        (1, "One law for all? &middot; it fails",
         f"If a single three-quarter-power law ran from the smallest protist to the elephant, power per kilogram "
         f"would fall about {v['kspread']}-fold along the dashed line. Instead the average of every major group "
         f"lies between {v['band_lo']} and {v['band_hi']} W/kg, a range of only about {v['band_ratio']} times."),
        (2, "Inside each group &middot; fitted law",
         f"Within each group, bigger species do run slower per kilogram. The fitted exponents run from "
         f"{v['within_lo']} to {v['within_hi']}, so the familiar 3/4 is a typical tilt inside a group, not one "
         "line for all of life."),
        (3, "One person &middot; measured",
         f"A resting 70 kg adult gives off about {v['h_w']} W, or {v['h_wkg']} W/kg, inside the band. This is the "
         "page's reference unit."),
        (4, "People with fuel &middot; measured",
         f"Add each person's share of the country's primary energy and the average person in the world runs at "
         f"about {v['world_wkg']} W/kg, {v['world_x']} times the body. In the United States the figure is "
         f"{v['us_wkg']} W/kg."),
        (5, "Stars &middot; the opposite tilt",
         f"Main-sequence stars put out more power per kilogram the heavier they are, roughly as mass to the power "
         f"{v['star_slope']}. The Sun gives off {v['sun_wkg']} W/kg, about {v['sun_x']} times less than a resting body."),
    ]
    desc = (f"A log-log chart of power per kilogram against mass. Living things, from bacteria to an elephant, form "
            f"a flat cloud between about 0.04 and 23 W/kg; the averages of the major groups lie between "
            f"{v['band_lo']} and {v['band_hi']} W/kg, while a single three-quarter-power law would fall steeply. "
            f"Inside each group, short fitted lines tilt down. A resting human sits at {v['h_wkg']} W/kg; with "
            f"their share of fuel, the world average is {v['world_wkg']} and the United States {v['us_wkg']} W/kg. "
            f"Stars, at the far right, rise with mass, and the Sun is at {v['sun_wkg']} W/kg.")
    # A figure, not a section: tests/test_layout.js allows a centred figure on the wide track (oxygen's rule).
    out = ['<figure class="ladder wide" aria-label="Power per kilogram from bacteria to stars">',
           '<div class="ladder-fig">', f'<p id="ladder-desc" hidden>{E(desc)}</p>',
           hero_svg(P, True), hero_svg(P, False),
           '<p class="ladder-key">Blue: species, resting, 20 &deg;C for cold-blooded groups &middot; grey: bacteria '
           '&middot; brown: stars. Both axes are logarithmic.</p>', '</div>', '<div class="ladder-steps">']
    for k, head, text in steps:
        out.append(f'<div class="step" data-step="{k}"><p class="ev">{head}</p><p>{text}</p></div>')
    out.append("</div>\n</figure>")
    return "\n".join(out)


# ------------------------------------------------------------ city chart ---
def city_svg(P, wide):
    C = P["cities"]
    f = dict(W=720, H=380, L=74, R=16, T=14, B=48) if wide else dict(W=320, H=320, L=58, R=10, T=14, B=48)
    xs = [p[0] for p in C["pts"]]
    ys = [p[1] for p in C["pts"]]
    x0, x1 = math.floor(min(xs) * 2) / 2, math.ceil(max(xs) * 2) / 2
    y0, y1 = math.floor(min(ys) * 10) / 10 - 0.05, math.ceil(max(ys) * 10) / 10
    pw, ph = f["W"] - f["L"] - f["R"], f["H"] - f["T"] - f["B"]
    sx = lambda x: f["L"] + (x - x0) / (x1 - x0) * pw          # noqa: E731
    sy = lambda y: f["T"] + (y1 - y) / (y1 - y0) * ph          # noqa: E731
    out = [f'<svg class="plot" viewBox="0 0 {f["W"]} {f["H"]}" width="{f["W"]}" height="{f["H"]}">']
    xt = [t for t in (5, 5.5, 6, 6.5, 7, 7.5) if x0 <= t <= x1] if wide else [t for t in (5, 6, 7) if x0 <= t <= x1]
    yv = [t for t in (30000, 50000, 100000, 200000) if y0 <= math.log10(t) <= y1]
    pops = {5: "100,000", 5.5: "300,000", 6: "1 million", 6.5: "3 million", 7: "10 million", 7.5: "30 million"}
    out += axes(f, sx, sy, "Metro population, " + str(C["year"]), "GDP per person ($)", xt,
                [math.log10(t) for t in yv], lambda t: pops[t], lambda t: f"{round(10 ** t):,}", "")
    r = 2.6 if wide else 2.2
    out.append("".join(f'<circle class="pt" cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="{r}"/>' for x, y in C["pts"]))
    a, b = C["icpt"], C["slope"] - 1
    out.append(f'<path class="fit" d="M{sx(x0):.1f} {sy(a + b * x0):.1f}L{sx(x1):.1f} {sy(a + b * x1):.1f}"/>')
    # where per-person GDP would sit if output were proportional to size: flat, through the mean
    ym = sum(ys) / len(ys)
    out.append(f'<path class="flat" d="M{sx(x0):.1f} {sy(ym):.1f}L{sx(x1):.1f} {sy(ym):.1f}"/>')
    tx = x1 - 0.05
    out.append(f'<text x="{sx(tx):.1f}" y="{sy(a + b * tx) - 10:.1f}" text-anchor="end">'
               f'Fitted: exponent {C["slope"]:.2f}</text>')
    out.append(f'<text class="lab-dim" x="{sx(tx):.1f}" y="{sy(ym) + 20:.1f}" text-anchor="end">'
               f'{"Exponent 1: no gain" if not wide else "Exponent 1: output grows only with people"}</text>')
    out.append("</svg>")
    return "".join(out)


def city_chart(P, v):
    title = "Bigger US metros produce more per person"
    cap = (f"Each dot is one of {v['c_n']} metropolitan areas, {v['c_year']}: GDP (BEA, by county) divided by "
           f"population (Census). Fitted exponent {v['c_slope']} (95 percent interval {v['c_lo']} to {v['c_hi']}).")
    return ('<figure class="step-fig wide" role="img" aria-label="%s"><div class="snap-wide">%s</div>'
            '<div class="snap-phone">%s</div><figcaption class="dim"><b>%s.</b> %s</figcaption></figure>'
            % (E(title), city_svg(P, True), city_svg(P, False), E(title), cap))


# ---------------------------------------------------------------- claims ---
def claims(P, v):
    L, F, St, C = P["life"], P["fuel"], P["stars"], P["cities"]
    bad = []
    if not L["kleiber_spread"] > 100 * L["band_ratio"]:
        bad.append("the band is not far narrower than a single 3/4 law would give")
    if not (L["within_max"] < 1 and L["within_min"] > 0.5):
        bad.append("within-group exponents are not all between 1/2 and 1")
    if not L["band_lo"] < L["human"]["wkg"] < L["band_hi"]:
        bad.append("the resting human is not inside the band ('inside the band')")
    if not St["wkg_slope"] > 0 > L["euk_slope"] - 1:
        bad.append("stars and life do not tilt in opposite directions")
    if not L["band37"]["ratio"] < L["band_ratio"]:
        bad.append("a 37 C correction does not narrow the band")
    if not F["us"]["wkg"] > L["band_hi"] * 10:
        bad.append("US fuel is not an order of magnitude above the band's top")
    if not C["ci"][0] > 1:
        bad.append("city GDP exponent's interval includes 1 ('superlinear')")
    if not St["wkg_hi"] < L["human"]["wkg"] * 2:
        bad.append("the heaviest star in the sample is not near a resting body ('about as much as')")
    if not L["groups"]["coldvert"]["gmean_wkg"] > 1000 * St["sun_wkg"]:
        bad.append("cold-blooded vertebrates are not 'more than a thousand times' the Sun per kilogram")
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    L, F, St, C = P["life"], P["fuel"], P["stars"], P["cities"]
    g = L["groups"]
    v = {
        "n_rows": f"{L['n_rows']:,}", "n_species": f"{L['n_species']:,}",
        "bact_lo": "10<sup>−17</sup> kg" if round(math.log10(L["lightest_kg"]["bacteria"])) == -17 else "",
        "eleph_kg": f"{L['heaviest_kg']['mammals']:,.0f}",
        "life_decades": str(int(math.log10(L["heaviest_kg"]["mammals"] / L["lightest_kg"]["bacteria"]))),
        "euk_slope": f"{L['euk_slope']:.2f}", "euk_lo": f"{L['euk_ci'][0]:.2f}", "euk_hi": f"{L['euk_ci'][1]:.2f}",
        "within_lo": f"{L['within_min']:.2f}", "within_hi": f"{L['within_max']:.2f}",
        "band_lo": sig(L["band_lo"], 1), "band_hi": sig(L["band_hi"], 1),
        "band_ratio": sig(L["band_ratio"], 1), "kspread": sig(L["kleiber_spread"], 1),
        "b37_lo": sig(L["band37"]["lo"], 1), "b37_hi": sig(L["band37"]["hi"], 2), "b37_ratio": sig(L["band37"]["ratio"], 1),
        "sp_lo": sig(L["sp_p01"], 1), "sp_hi": sig(L["sp_p99"], 2),
        "g_birds": sig(g["birds"]["gmean_wkg"]), "g_mammals": sig(g["mammals"]["gmean_wkg"]),
        "g_cold": sig(g["coldvert"]["gmean_wkg"]), "g_plants": sig(g["plants"]["gmean_wkg"]),
        "h_w": f"{L['human']['w']:.0f}", "h_wkg": sig(L["human"]["wkg"]),
        "f_year": str(F["world"]["year"]),
        "world_w": sig(F["world"]["w"]), "world_wkg": sig(F["world"]["wkg"]), "world_x": f"{F['world']['x_body']:.0f}",
        "us_w": sig(F["us"]["w"]), "us_wkg": sig(F["us"]["wkg"]), "us_x": sig(F["us"]["x_body"], 1),
        "india_w": sig(F["india"]["w"]), "india_x": f"{F['india']['x_body']:.0f}",
        "world_kwh": f"{F['world']['kwh']:,.0f}", "owid_updated": F["updated"],
        "n_stars": str(St["n"]), "n_stars_all": str(St["n_all"]),
        "m_lo": f"{St['m_lo']:.2f}", "m_hi": f"{St['m_hi']:.0f}",
        "star_slope": f"{St['wkg_slope']:.0f}", "mlr": f"{St['mlr_slope']:.0f}",
        "star_hi": sig(St["wkg_hi"]), "star_lo": sig(St["wkg_lo"], 1),
        "sun_wkg": f"{St['sun_wkg']:.5f}".rstrip("0"), "sun_x": sig(P["sun_vs_human"]),
        "L_N": "3.828 &times; 10<sup>26</sup>", "msun": f"{St['msun'] / 1e30:.3f} &times; 10<sup>30</sup>",
        "sun_sci": f"{St['sun_wkg'] / 1e-4:.2f} &times; 10<sup>−4</sup>",
        "c_year": str(C["year"]), "c_n": str(C["n"]), "c_msa": str(C["n_msa"]),
        "c_slope": f"{C['slope']:.2f}", "c_lo": f"{C['ci'][0]:.2f}", "c_hi": f"{C['ci'][1]:.2f}",
        "c_r2": f"{C['r2']:.2f}", "c_x10": f"{100 * (C['x10'] - 1):.0f}",
        "c_dropped": str(C["dropped"]),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    v["stamp"] = insight.stamp(live=False)
    v["takeaways"] = insight.takeaways([
        f"Across {v['n_species']} species, from bacteria to an elephant, the resting power of each major group "
        f"averages between {v['band_lo']} and {v['band_hi']} watts per kilogram, where one three-quarter-power law "
        f"would spread them about {v['kspread']}-fold.",
        f"A resting human body gives off about {v['sun_x']} times more power per kilogram than the Sun, and "
        "heavier stars give off more per kilogram, the opposite of the tilt in animals.",
        f"Fuel lifts the average person to about {v['world_x']} times the power of their own body, and larger US "
        "metros produce more per person while, in published fits, using about the same energy per person."])
    claims(P, v)
    v["hero"] = hero(P, v)
    v["chart_cities"] = city_chart(P, v)
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "oxygen.html"), encoding="utf-8").read()
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
    used_in_code = {"bact_lo", "eleph_kg", "life_decades", "within_lo", "within_hi", "world_wkg", "us_wkg",
                    "star_slope", "sun_wkg", "c_n", "c_lo", "c_hi"}
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)) - used_in_code)
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("scales.html")
    if not refs:
        return text, ["scales.html has no entry in add_citations.PAGES"]
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
        print("  scales.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  scales.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
