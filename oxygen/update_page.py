"""
Write site/oxygen.html from template.html and outputs/payload.json.

Every number on the page comes from the payload or from a quotation read out of an opened source (sources.py
reads it at render time, so a quotation cannot drift from its file); the prose is in the template. The parts
other scripts own - the nav (rebuild_nav.py), the citation markers and Sources list (add_citations.py's table,
applied here) and the ?v= stamps (bust_cache.py) - are kept as the shipped page has them, so
tests/test_generators.py can run this on the shipped tree and expect no change. The idiom is
ethane/update_page.py's.

The hero is a causal tree drawn here as two SVGs (the full tree at 900px, a compact map at 320px) whose
nodes carry data-o, the order they belong to; site/assets/chain.js grows it as the reader scrolls. The three
charts are the insight kit's series charts, rendered static by kit_render.js (charts.js in node).

claims() asserts every direction and range the template's words commit to ("more than tripled", "about one
gallon in ten", "about a third of the corn crop", "above the mandate"). If a rebuild moves one, the generator
stops rather than ship prose the payload contradicts.

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
PAGE = os.path.join(SITE, "oxygen.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "oxygen-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
E = html.escape


def pct(x, k=1):
    return f"{100 * x:.{k}f}"


# ------------------------------------------------------------ quotations ---
Q = {   # key: (source, pattern); group(1) if the pattern has one, else the whole match
    "q_dole": ("dole_1990.pdf", r"significantly increase the market share for grain-based alternative fuels"),
    "q_usgs": ("usgs_wri034200.pdf", r"about 5 to 7\.5 times higher in areas of relatively high MTBE use"),
    "q_unanticipated": ("crec_2000_s3514.html", r"unanticipated development"),
    "q_daschle": ("crec_2000_s3514.html", r"a fair tradeoff for the establishment of a renewable fuels standard"),
    "q_nrc": ("nrc_1999_ozone.html", r"little impact on improving ozone air quality"),
}


def quotes():
    import sources as S
    out = {}
    for k, (n, p) in Q.items():
        m = S.quote(n, p)
        s = m.group(1) if m.groups() else m.group(0)
        if len(s.split()) >= 15:
            raise SystemExit(f"{k}: a quotation of {len(s.split())} words; the house limit is under 15")
        out[k] = E(s, quote=False)
    return out


# ------------------------------------------------------------------ tree ---
# (id, order, evidence, wide lines, phone word). Evidence: policy | strong | moderate | contested.
NODES = [
    ("P", 0, "policy", ["1990 law: gasoline", "in smoggy cities must", "contain oxygen"], "1990"),
    ("A", 1, "strong", ["Refiners meet it", "with MTBE, not", "corn ethanol"], "MTBE"),
    ("B", 2, "strong", ["MTBE leaks from", "tanks into", "groundwater"], "Wells"),
    ("C", 2, "strong", ["{nbans} states ban or", "limit MTBE; water", "suppliers sue"], "Bans"),
    ("D", 3, "strong", ["2005 law ends the", "oxygen rule and", "mandates biofuel"], "Deal"),
    ("F", 3, "strong", ["Ethanol replaces", "MTBE, late 2003", "to 2006"], "Swap"),
    ("G", 4, "moderate", ["Ethanol: 1 gallon", "in 10 of U.S.", "gasoline today"], "1 in 10"),
    ("H", 4, "contested", ["A third of corn;", "land and carbon", "effects disputed"], "Corn"),
]
EDGES = [("P", "A"), ("A", "B"), ("B", "C"), ("C", "D"), ("C", "F"), ("D", "F"), ("F", "G"), ("G", "H")]
COLS = ["Policy", "1st order", "2nd order", "3rd order", "Beyond"]
TAG = {"policy": "the policy", "strong": "strong evidence", "moderate": "moderate", "contested": "contested"}
GLYPH = {"strong": "full", "moderate": "half", "contested": "open"}
# where each node sits: column, and row 0 (top), 1 (bottom) or 0.5 (centred)
SLOT = {"P": (0, .5), "A": (1, .5), "B": (2, 0), "C": (2, 1), "D": (3, 0), "F": (3, 1), "G": (4, 0),
        "H": (4, 1)}


def glyph(cx, cy, kind):
    r = 4.5
    if kind == "full":
        return f'<circle class="ah" cx="{cx}" cy="{cy}" r="{r}"/>'
    if kind == "half":
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="var(--dim)" stroke-width="1.2"/>'
                f'<path class="ah" d="M{cx} {cy - r}A{r} {r} 0 0 0 {cx} {cy + r}Z"/>')
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="var(--moss)" stroke-width="1.2"/>'


def tree(P, wide):
    if wide:
        W, cw, gap, nh, top, rowgap = 900, 164, 20, 92, 26, 36
    else:
        W, cw, gap, nh, top, rowgap = 320, 58, 7.5, 30, 22, 16
    H = top + 2 * nh + rowgap + 4

    def box(i):
        c, r = SLOT[i]
        x = c * (cw + gap)
        y = top + r * (nh + rowgap)
        return x, y

    out = [f'<svg class="tree {"tree-wide" if wide else "tree-phone"}" viewBox="0 0 {W} {H}" width="{W}" '
           f'height="{H}" role="img" aria-labelledby="chain-desc">']
    out.append('<defs><marker id="ah-%s" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" '
               'orient="auto-start-reverse"><path class="ah" d="M0 0L8 4L0 8Z"/></marker></defs>' % ("w" if wide else "p"))
    for k, lab in enumerate(COLS if wide else ["Law", "1st", "2nd", "3rd", "Beyond"]):
        x = k * (cw + gap) + cw / 2
        out.append(f'<text class="col" x="{x:.1f}" y="13" text-anchor="middle" data-o="{k}">{E(lab)}</text>')
    ev = {n[0]: n[2] for n in NODES}
    order = {n[0]: n[1] for n in NODES}
    for a, b in EDGES:
        ax, ay = box(a)
        bx, by = box(b)
        if SLOT[a][0] == SLOT[b][0]:              # same column: straight down
            x1, y1, x2, y2 = ax + cw / 2, ay + nh, bx + cw / 2, by - 2
            d = f"M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}"
        else:                                     # next column: right edge to left edge, a soft S
            x1, y1, x2, y2 = ax + cw, ay + nh / 2, bx - 2, by + nh / 2
            mx = (x1 + x2) / 2
            d = f"M{x1:.1f} {y1:.1f}C{mx:.1f} {y1:.1f} {mx:.1f} {y2:.1f} {x2:.1f} {y2:.1f}"
        cls = "e ev-contested" if ev[b] == "contested" else "e"
        out.append(f'<path class="{cls}" d="{d}" marker-end="url(#ah-{"w" if wide else "p"})" data-o="{order[b]}"/>')
    for i, o, kind, lines, word in NODES:
        x, y = box(i)
        out.append(f'<g class="n ev-{kind}" data-o="{o}">')
        out.append(f'<rect x="{x + .75:.2f}" y="{y + .75:.2f}" width="{cw - 1.5:.2f}" height="{nh - 1.5:.2f}" rx="3"/>')
        if wide:
            ty = y + 18
            if kind in GLYPH:
                out.append(glyph(x + 13, ty - 4, GLYPH[kind]))
            out.append(f'<text class="tag" x="{x + (24 if kind in GLYPH else 10)}" y="{ty}">{E(TAG[kind])}</text>')
            for j, ln in enumerate(lines):
                out.append(f'<text x="{x + 10}" y="{ty + 21 + 17 * j}">{E(ln.format(nbans=P["bans"]["n"]))}</text>')
        else:
            out.append(f'<text class="lab" x="{x + cw / 2:.1f}" y="{y + nh / 2 + 4:.1f}" text-anchor="middle">'
                       f'{E(word)}</text>')
        out.append("</g>")
    out.append("</svg>")
    return "".join(out)


def tree_fits():
    """A node's text box is 144px. Measured with fontTools on 2026-11-08, when the site moved from IBM
    Plex to Perfidy: Perfidy Text at 13px averages 0.450 em a character on these lines (Plex Sans
    0.468), and the widest line, "in smoggy cities must", is 121.8px (Plex 125.7). The 22-character
    limit below was set for Plex and still holds with room to spare.
    The phone map's words are Perfidy Mono at 12px, 6.72px a character (Plex Mono was 7.2), in a 58px
    box: the 7-character limit is 47px."""
    bad = [ln for n in NODES for ln in n[3] if len(ln.format(nbans=25)) > 22]
    bad += [n[4] for n in NODES if len(n[4]) > 7]
    if bad:
        raise SystemExit(f"tree labels too long for their boxes: {bad}")


def hero(P, v):
    steps = [
        (0, "The policy &middot; 1990",
         f"The Clean Air Act Amendments of 1990 required at least {v['o2_rfg']} per cent oxygen by weight in the "
         f"gasoline of the areas with the worst ozone, from 1995, and {v['o2_oxy']} per cent in winter gasoline where "
         f"carbon monoxide was too high, from 1992. Senator Bob Dole's office said the amendment would "
         f"&ldquo;{v['q_dole']}&rdquo;, such as ethanol."),
        (1, "First order &middot; strong evidence",
         "Refiners met the rule mostly with MTBE, not ethanol. MTBE could go through pipelines with the gasoline; "
         "ethanol picks up water and was blended at terminals. EIA attributed the growth in MTBE use to the oxygen "
         'programmes. <a href="#first">The data</a>'),
        (2, "Second order &middot; strong evidence",
         "MTBE dissolves easily in water and breaks down slowly. It reached groundwater from leaking tanks. The USGS "
         "detected it more often where gasoline carried more of it. States banned or limited it, and water suppliers "
         'sued the oil companies that made and sold it. <a href="#second">The data</a>'),
        (3, "Third order &middot; strong evidence",
         "California, New York and Connecticut banned MTBE at the end of 2003, and the gasoline sold there moved "
         "to ethanol. The Energy Policy Act of 2005 ended the oxygen requirement for reformulated gasoline and required "
         "renewable fuel. It gave MTBE no shield from liability, and refiners removed the rest of it in spring 2006. "
         '<a href="#third">The data</a>'),
        (4, "Beyond &middot; moderate, then contested",
         "Ethanol is now about one gallon in ten of U.S. gasoline. A 2007 law and other policies share the credit for "
         "that level, so the link is moderate. About a third of the corn crop goes to make it. One study finds that "
         "the 2007 mandate added cropland and made corn ethanol's carbon intensity no lower than gasoline's, and "
         'likely higher; other researchers dispute it. <a href="#anyway">The objections</a>'),
    ]
    desc = ("A causal tree. 1990: the Clean Air Act requires oxygen in the gasoline of smoggy cities. First "
            "order: refiners use MTBE. Second order: MTBE leaks into groundwater, and %d states ban or limit it. Third "
            "order: state bans and a 2005 law that ends the oxygen rule and mandates renewable fuel; ethanol "
            "replaces MTBE from late 2003 to 2006. Beyond: ethanol is one gallon in ten of gasoline (moderate), and "
            "the corn, land and carbon effects are contested." % P["bans"]["n"])
    # A figure, not a section: tests/test_layout.js measures main's children for one left edge, and a
    # figure on the wide track is a picture centred on the measure, which that rule allows.
    out = ['<figure class="chain wide" aria-label="The chain of effects">',
           '<div class="chain-fig">', f'<p id="chain-desc" hidden>{E(desc)}</p>',
           tree(P, True), tree(P, False),
           '<p class="chain-key">Border: solid, strong evidence &middot; dashed, moderate &middot; '
           'dotted, contested. The shaded nodes are the step you are reading.</p>', '</div>', '<div class="chain-steps">']
    for k, head, text in steps:
        out.append(f'<div class="step" data-step="{k}"><p class="ev">{head}</p><p>{text}</p></div>')
    out.append("</div>\n</figure>")
    return "\n".join(out)


# ---------------------------------------------------------------- charts ---
def static_chart(spec, caption):
    import insight
    snaps = insight._render(spec, [{"t": 1}])
    return ('<figure class="step-fig wide" role="img" aria-label="%s"><div class="snap-wide">%s</div>'
            '<div class="snap-phone">%s</div><figcaption class="dim"><b>%s.</b> %s</figcaption></figure>'
            % (E(spec["title"]), snaps["wide"][0], snaps["phone"][0], E(spec["title"]), caption))


def chart_mtbe(P):
    s = P["series"]["mtbe"]
    spec = {"id": "oxy-mtbe", "type": "series",
            "title": "MTBE blended by U.S. refiners and blenders, thousand barrels a day, by month, 1993 to 2008",
            "x": s["x"], "y": {"label": "thousand b/d"},
            "series": [{"key": "mtbe", "label": "MTBE, refinery and blender net input", "color": "acc",
                        "values": s["v"]}],
            "annotations": [{"at": "1995-01", "text": "RFG starts", "short": "RFG"},
                            {"at": "2004-01", "text": "state bans", "short": "bans"},
                            {"at": "2006-05", "text": "rule ends", "short": "ends"}]}
    return static_chart(spec, "Data: EIA, refinery and blender net input of MTBE (MMTRIUS1), monthly. "
                              "RFG is reformulated gasoline.")


def chart_bans(P):
    by = P["bans"]["by_year"]
    xs = [f"{y}-12" for y in range(int(min(by)), int(max(by)) + 1)]
    spec = {"id": "oxy-bans", "type": "series",
            "title": "U.S. states with an MTBE ban or limit in effect at the end of each year, 1999 to 2009",
            "x": xs, "y": {"label": "states", "max": 25},
            "series": [{"key": "bans", "label": "States with a ban or limit in effect", "color": "moss",
                        "values": [by[x[:4]] for x in xs]}],
            "annotations": [{"at": "2004-12", "text": "CA, NY, CT in force", "short": "CA, NY"}]}
    return static_chart(spec, "Data: EPA, State Actions Banning MTBE (Statewide), EPA420-B-07-013, August 2007, "
                              "phaseout dates.")


def chart_swap(P):
    s = P["series"]["swap"]
    share = P["corn"]["share"]
    spec = {"id": "oxy-swap", "type": "series",
            "title": "MTBE and fuel ethanol used in U.S. gasoline, thousand barrels a day, by month, with the share "
                     "of the corn crop used for fuel ethanol below",
            "x": s["x"], "y": {"label": "thousand b/d"},
            "series": [{"key": "mtbe", "label": "MTBE", "color": "moss", "values": s["mtbe"]},
                       {"key": "eth", "label": "Fuel ethanol", "color": "acc", "values": s["eth"]}],
            "annotations": [{"at": "2004-01", "text": "CA, NY, CT bans", "short": "bans"},
                            {"at": "2006-05", "text": "rule ends", "short": "ends"},
                            {"at": "2007-12", "text": "2007 mandate", "short": "2007 law"}],
            "under": [{"kind": "bars", "label": "Corn to fuel ethanol, %% of crop (%s-%s)" % (pct(min(share.values()), 0),
                                                                               pct(max(share.values()), 0)),
                       "color": "acc", "height": 64,
                       "bars": [{"at": y, "value": round(100 * v, 1), "text": ""} for y, v in sorted(share.items())]}]}
    return static_chart(spec, "Data: EIA, MTBE net input (MMTRIUS1) and Monthly Energy Review Table 10.3 fuel "
                              "ethanol consumption, monthly (EIA stops reporting MTBE net input after %s); USDA ERS Feed "
                              "Grains Database, corn for fuel alcohol over production, marketing years to %s/%s."
                              % (P["mtbe_last"][:4], P["corn"]["last_final"],
                                                                              str(int(P["corn"]["last_final"]) + 1)[2:]))


# ---------------------------------------------------------------- claims ---
def claims(P, v):
    A, d = P["annual"], P["doc"]
    last = str(int(P["through"][:4]) - 1)
    share = P["corn"]["share"]
    rfg = [A[str(y)]["rfg_share"] for y in range(1996, 2008)]
    c = [
        ("'more than tripled': EIA's 1997 MTBE over its 1990 figure", 3 < d["mtbe_c"]["kbd"] / d["mtbe_a"]["kbd"] < 4),
        ("'about one gallon in ten': latest full year's ethanol share 9-12%", 0.09 < A[last]["eth_share"] < 0.12),
        ("'about a third of the corn crop': latest final year 28-40%", 0.28 < share[P["corn"]["last_final"]] < 0.40),
        ("'about a third of U.S. gasoline from 1996 on': RFG share 0.30-0.36 every year 1996-2007",
         all(0.30 <= x <= 0.36 for x in rfg)),
        ("'above the mandate' in 2006 and 2007",
         P["rfs"]["actual_bgal"]["2006"] > P["rfs"]["mandate_bgal"]["2006"]
         and P["rfs"]["actual_bgal"]["2007"] > P["rfs"]["mandate_bgal"]["2007"]),
        ("'use is high each winter in 1993 and 1994': Jan above Jul both years",
         all(P["series"]["mtbe"]["v"][P["series"]["mtbe"]["x"].index(f"{y}-01")]
             > P["series"]["mtbe"]["v"][P["series"]["mtbe"]["x"].index(f"{y}-07")] for y in (1993, 1994))),
        ("'the summer low disappears' from 1995: July 1995 more than twice July 1994",
         P["series"]["mtbe"]["v"][P["series"]["mtbe"]["x"].index("1995-07")]
         > 2 * P["series"]["mtbe"]["v"][P["series"]["mtbe"]["x"].index("1994-07")]),
        ("'decreased from January to May 2006' by more than 90%", P["switch"]["may"] < 0.1 * P["switch"]["jan"]),
        ("peak year is in the RFG era", 1995 <= P["peak"]["year"] <= 2001),
        ("'from late 1994 ... the summer low disappears': November 1994 above November 1993",
         P["series"]["mtbe"]["v"][P["series"]["mtbe"]["x"].index("1994-11")]
         > P["series"]["mtbe"]["v"][P["series"]["mtbe"]["x"].index("1993-11")]),
        ("first state ban took effect in 2000 (the chart's first non-zero year)", P["bans"]["first"].startswith("2000")),
        ("'ethanol use passes MTBE use in {cross} and stays above it': October 2003, the month before the CA bans",
         P["cross"] == "2003-10"),
        ("'the share has stayed near one tenth since {y_tenth}': 9.5-11% every full year since",
         all(0.095 <= A[str(y)]["eth_share"] <= 0.11 for y in range(int(v["y_tenth"]), int(last) + 1))),
        ("'seven of them banned MTBE completely'", P["bans"]["complete"] == 7),
        ("'net input understates MTBE use by about an eighth (12 per cent in 1997)'",
         round(100 * (1 - A["1997"]["mtbe"] / d["mtbe_c"]["kbd"])) == 12),
    ]
    bad = [n for n, ok in c if not ok]
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    A, d = P["annual"], P["doc"]
    last = str(int(P["through"][:4]) - 1)
    v = {
        "nbans": str(P["bans"]["n"]),
        "o2_rfg": f"{d['o2_rfg']:.1f}", "o2_oxy": f"{d['o2_oxy']:.1f}",
        "mtbe_a": f"{d['mtbe_a']['kbd']:.0f}", "y_a": str(d["mtbe_a"]["year"]),
        "mtbe_b": f"{d['mtbe_b']['kbd']:.0f}", "y_b": str(d["mtbe_b"]["year"]),
        "mtbe_c": f"{d['mtbe_c']['kbd']:.0f}", "y_c": str(d["mtbe_c"]["year"]),
        "brp_mtbe": str(d["brp_mtbe_pct"]), "brp_eth": str(d["brp_eth_pct"]), "y_brp": "1999",
        "peak_y": str(P["peak"]["year"]), "peak_kbd": f"{P['peak']['kbd']:.0f}", "peak_share": pct(P["peak"]["share"]),
        "usgs_lo": f"{d['usgs_lo']:g}", "usgs_hi": f"{d['usgs_hi']:g}",
        "rfs06": f"{d['rfs']['2006']:.1f}", "rfs07": f"{d['rfs']['2007']:.1f}", "rfs12": f"{d['rfs']['2012']:.1f}",
        "act06": f"{P['rfs']['actual_bgal']['2006']:.1f}", "act07": f"{P['rfs']['actual_bgal']['2007']:.1f}",
        "repeal": d["repeal_effective"],
        "sw_jan": f"{P['switch']['jan']:.0f}", "sw_may": f"{P['switch']['may']:.0f}",
        "eia2006": str(d["eia2006_kbd"]),
        "corn_last": f"{P['corn']['last_final']}/{str(int(P['corn']['last_final']) + 1)[2:]}",
        "chk_1997": f"{A['1997']['mtbe']:.0f}", "eth_share": pct(A[last]["eth_share"]), "y_last": last,
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
        "ncomplete": {7: "seven"}.get(P["bans"]["complete"], str(P["bans"]["complete"])),
        "y_lastban": P["bans"]["last"][:4], "cross": "late " + P["cross"][:4] if int(P["cross"][5:]) >= 9 else str(P["cross"]), "mtbe_last": str(int(P["mtbe_last"][:4])),
        "y_tenth": "2011",
        "corn_lo": pct(min(P["corn"]["share"].values()), 0), "corn_hi": pct(max(P["corn"]["share"].values()), 0),
    }
    v.update(quotes())
    v["stamp"] = insight.stamp(through=P["through"], live=False)
    v["takeaways"] = insight.takeaways([
        f"The oxygen rule more than tripled U.S. use of MTBE: EIA put it at {v['mtbe_a']} thousand barrels a day "
        f"in {v['y_a']} and {v['mtbe_c']} thousand in {v['y_c']}, most of it in the cities the rule covered.",
        f"Where gasoline carried much MTBE, the U.S. Geological Survey detected it in water {v['usgs_lo']} to "
        f"{v['usgs_hi']} times as often as elsewhere, and {v['nbans']} states banned or limited it.",
        "State bans and the end of the oxygen rule in 2006 moved refiners from MTBE to corn ethanol, which is now "
        "about one gallon in ten of U.S. gasoline; a 2007 law did much of that work."])
    claims(P, v)
    tree_fits()
    v["hero"] = hero(P, v)
    v["chart_mtbe"] = chart_mtbe(P)
    v["chart_bans"] = chart_bans(P)
    v["chart_swap"] = chart_swap(P)
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "longevity.html"), encoding="utf-8").read()
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
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)) - {"o2_rfg", "o2_oxy", "q_dole", "mtbe_c"})
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("oxygen.html")
    if not refs:
        return text, ["oxygen.html has no entry in add_citations.PAGES"]
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
        print("  oxygen.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  oxygen.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
