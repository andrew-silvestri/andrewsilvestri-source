"""
Write site/greatfilter.html from template.html, sources.py and outputs/payload.json.

Every number on the page comes from sources.py (published figures, one source a row) or from the payload
(build_greatfilter.py's computations); the prose is in the template. The parts other scripts own - the nav
(rebuild_nav.py), the citation markers and Sources list (add_citations.py's table, applied here) and the ?v=
stamps (bust_cache.py) - are kept as the shipped page has them, so tests/test_generators.py can run this on the
shipped tree and expect no change. The idiom is oxygen/update_page.py's.

The hero is a timeline drawn here as two SVGs (900px with every label, 320px compact) whose rows carry data-o,
the order they belong to; site/assets/chain.js (unchanged, shared with oxygen.html) reveals one row per card as
the reader scrolls, and with no JS or reduced motion every row shows. The two figures are static SVGs drawn the
same way. Text in them is Perfidy: Mono at 12px (0.56 em, 6.72px a character) and Text at 13px (about 0.45 em a
character, oxygen's measurement); fits() checks every label against its column.

claims() asserts every direction, ratio and range the template's words commit to ("three happened only once",
"about a ninth", "about half"). If a rebuild moves one, the generator stops rather than ship prose the numbers
contradict.

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
PAGE = os.path.join(SITE, "greatfilter.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "greatfilter-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import sources as S  # noqa: E402

E = html.escape
MONO = 6.72          # Perfidy Mono at 12px, px a character
SANS = 0.45 * 13     # Perfidy Text at 13px, px a character (average)


def g1(x):
    """A duration or date in billions of years, to the precision the sources give."""
    return f"{x:.2f}".rstrip("0").rstrip(".") if x < 10 else f"{x:,.0f}"


# ------------------------------------------------------------- the timeline ---
TMAX, TMIN = 4.6, -1.5           # Ga; negative is the future


def ga_label(x):
    if x >= 1:
        return f"{g1(x)} Ga"
    if x >= 0.01:
        return f"{x * 1000:.0f} Ma"
    return f"{x * 1000:.1f} Ma"


ROW_NAMES = {   # key: (wide name, phone name, wide date line, phone date line)
    "window": ("Habitable window", "Window", "4.4 Ga to ~1 Gyr ahead", "4.4 Ga"),
    "left": ("Time left", "Left", "about 1 Gyr", "~1 Gyr"),
}


def rows(P):
    """The timeline's rows: the window, the five steps, the time left."""
    W = S.WINDOW
    out = [{"key": "window", "o": 0}]
    prev = W["start_ga"]
    waits = {r["key"]: r["wait"] for r in P["chain"]["rows"]}
    for i, s in enumerate(S.STEPS):
        out.append({"key": s["key"], "o": i + 1, "name": s["name"], "short": s["short"], "best": s["best"],
                    "band": s["band"], "prev": prev, "wait": waits[s["key"]], "count": s["count"],
                    "count_word": s["count_word"], "date": ga_label(s["best"])})
        prev = s["best"]
    out.append({"key": "left", "o": len(S.STEPS) + 1})
    return out


def timeline(P, wide):
    W = S.WINDOW
    if wide:
        Wd, X0, X1, WAIT_R, ORIG_X, RH, top = 900, 200, 690, 790, 806, 46, 46
    else:
        Wd, X0, X1, WAIT_R, ORIG_X, RH, top = 320, 72, 232, 274, 282, 36, 40
    R = rows(P)
    H = top + len(R) * RH + 4

    def x(t):
        return X0 + (TMAX - t) / (TMAX - TMIN) * (X1 - X0)
    o = [f'<svg class="tree gf gf-time {"tree-wide" if wide else "tree-phone"}" viewBox="0 0 {Wd} {H}" '
         f'width="{Wd}" height="{H}" role="img" aria-labelledby="gf-desc">']
    # header and axis: order 0
    o.append('<g data-o="0">')
    o.append(f'<text class="dim" x="{(X0 + X1) / 2:.1f}" y="13" text-anchor="middle">'
             f'{"Billions of years ago" if wide else "Ga"}</text>')
    o.append(f'<text class="dim" x="{WAIT_R}" y="13" text-anchor="end">{"Wait" if wide else "Gyr"}</text>')
    o.append(f'<text class="dim" x="{ORIG_X}" y="13">{"Happened" if wide else "Times"}</text>')
    for t in (4, 3, 2, 1, 0, -1):
        lab = {0: "now", -1: "+1"}.get(t, str(t)) if wide else {-1: "+1"}.get(t, str(t))
        o.append(f'<line class="tick" x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top - 12}" y2="{top - 6}"/>')
        o.append(f'<text class="dim" x="{x(t):.1f}" y="{top - 16}" text-anchor="middle">{lab}</text>')
    o.append(f'<line class="now-line" x1="{x(0):.1f}" x2="{x(0):.1f}" y1="{top - 6}" y2="{H - 2}"/>')
    o.append("</g>")
    for i, r in enumerate(R):
        y = top + i * RH
        by = y + (20 if wide else 16)                 # the bar's centre line
        o.append(f'<g class="row" data-o="{r["o"]}">')
        if r["key"] in ROW_NAMES:
            wn, pn, wd, pd = ROW_NAMES[r["key"]]
            name, sub = (wn, wd) if wide else (pn, pd)
        else:
            name, sub = (r["name"], r["date"]) if wide else (r["short"], r["date"])
        o.append(f'<text class="nm" x="0" y="{y + (16 if wide else 13)}">{E(name)}</text>')
        o.append(f'<text class="dim" x="0" y="{y + (34 if wide else 28)}">{E(sub)}</text>')
        if r["key"] == "window":
            s, e = W["start_ga"], -W["end_gyr"]
            o.append(f'<rect class="win" x="{x(s):.1f}" y="{by - 5}" width="{x(e) - x(s):.1f}" height="10"/>')
            for a, b in (W["start_band"], (-W["end_band"][0], -W["end_band"][1])):
                o.append(f'<rect class="win-band" x="{x(a):.1f}" y="{by - 8}" width="{x(b) - x(a):.1f}" height="16"/>')
        elif r["key"] == "left":
            o.append(f'<line class="left-bar" x1="{x(0):.1f}" x2="{x(-W["end_gyr"]):.1f}" y1="{by}" y2="{by}"/>')
            o.append(f'<text class="dim" x="{WAIT_R}" y="{by + 4}" text-anchor="end">~1{" Gyr" if wide else ""}</text>')
        else:
            hi, lo = r["band"]
            o.append(f'<rect class="band" x="{x(hi):.1f}" y="{by - 7}" width="{max(x(lo) - x(hi), 2):.1f}" height="14"/>')
            o.append(f'<line class="wait" x1="{x(r["prev"]):.1f}" x2="{x(r["best"]):.1f}" y1="{by}" y2="{by}"/>')
            o.append(f'<circle class="dot" cx="{x(r["best"]):.1f}" cy="{by}" r="{5 if wide else 4}"/>')
            o.append(f'<text x="{WAIT_R}" y="{by + 4}" text-anchor="end">{g1(r["wait"])}{" Gyr" if wide else ""}</text>')
            word = r["count_word"] if wide else {"once": "once", "unknown": "?"}.get(
                r["count_word"] if r["count"] != "unknown" else "unknown", str(r["count"]))
            if r["count"] == "unknown":
                word = "unknown" if wide else "?"
            cls = "acc" if r["count"] == 1 else "dim"
            o.append(f'<text class="{cls}" x="{ORIG_X}" y="{by + 4}">{E(word)}</text>')
        o.append("</g>")
    o.append("</svg>")
    return "".join(o)


def hero(P, v):
    c = P["chain"]
    w = {r["key"]: g1(r["wait"]) for r in c["rows"]}
    X = S.EXTRA
    cards = [
        (0, "The window &middot; 4.4 billion years ago to about 1 billion years ahead",
         f"Earth formed {g1(S.WINDOW['earth_ga'])} billion years ago. Zircon crystals show liquid water by "
         f"{g1(S.WINDOW['start_ga'])} billion years ago. The Sun grows brighter, and models put the end of an "
         f"oxygen-rich atmosphere about {g1(S.WINDOW['end_gyr'])} billion years from now. That gives complex life a "
         f"window of about {g1(c['T'])} billion years, of which about {v['used']} percent has passed."),
        (1, f"Life &middot; {g1(S.STEPS[0]['best'])} billion years ago &middot; origins unknown",
         f"The oldest widely accepted fossils are {g1(S.STEPS[0]['best'])} billion years old; disputed traces "
         f"reach {g1(X['contested_life_ga'])}. A molecular clock puts the last common ancestor of all life near "
         f"{g1(S.STEPS[0]['early'])} billion years ago. So life took at most {w['life']} billion years after "
         "the first water, and perhaps much less. Every living thing descends from one ancestor, but how many times "
         "life began is unknown."),
        (2, f"Oxygen-making photosynthesis &middot; by {g1(S.STEPS[1]['best'])} billion years ago &middot; once",
         "Every plant and alga that splits water to make oxygen uses machinery invented once, by the ancestors of "
         f"cyanobacteria; plants and algae took it in whole. Rocks show oxygen being made by "
         f"{g1(S.STEPS[1]['best'])} billion years ago, about {w['photo']} billion years after the first fossils; "
         f"one reading of the genes puts the origin later, near 2.5. Oxygen built up in the air from "
         f"{g1(X['goe_ga'])} billion years ago."),
        (3, f"Complex cell &middot; {g1(S.STEPS[2]['best'])} billion years ago &middot; once",
         "The cell with a nucleus and mitochondria, from which every plant, animal and fungus descends, arose once, "
         f"when one microbe came to live inside another. The oldest accepted fossils are {g1(S.STEPS[2]['best'])} "
         f"billion years old. The wait, about {w['cell']} billion years, is the longest in the chain. "
         '<a href="#once">Once, or many times?</a>'),
        (4, f"Complex multicellular life &middot; {ga_label(S.STEPS[3]['best'])} &middot; {S.STEPS[3]['count']} times",
         f"Large fossils appear {ga_label(S.STEPS[3]['best']).replace(' Ma', ' million years ago')}, about "
         f"{w['multi']} billion years after the complex cell. But life with tissues and organs evolved "
         f"{S.STEPS[3]['count']} separate times, in animals, plants, algae and fungi. A step that happened six times "
         "is a poor candidate for a filter."),
        (5, "Technology &middot; 3.3 million years ago to 1895 &middot; once",
         f"Stone tools are {ga_label(S.STEPS[4]['best']).replace(' Ma', ' million')} years old, Homo sapiens about "
         f"{X['sapiens_ka']} thousand, and radio dates from {X['radio_year']}. Many animals use tools; one lineage "
         f"built technology that accumulates. The wait from the first large fossils was about {w['tech']} billion "
         "years."),
        (6, "Time left &middot; about 1 billion years",
         f"The five waits lie between {g1(c['wait_min'])} and {g1(c['wait_max'])} billion years, and the time left is "
         "about the same. A simple model predicts that pattern whatever the steps' difficulty. "
         '<a href="#longest">Does the longest wait mark the hardest step?</a>'),
    ]
    desc = ("A timeline from 4.6 billion years ago to 1.5 billion years ahead. The habitable window runs from 4.4 "
            "billion years ago to about 1 billion years ahead. Five steps, each with the wait since the one before "
            "and how many times it happened: " +
            "; ".join(f"{s['name']}, {ga_label(s['best'])}, wait {g1(r['wait'])} billion years, {s['count_word']}"
                      for s, r in zip(S.STEPS, c["rows"])) +
            ". About 1 billion years of habitable time are left.")
    out = ['<figure class="chain wide" aria-label="The chain of steps">',
           '<div class="chain-fig">', f'<p id="gf-desc" hidden>{E(desc)}</p>',
           timeline(P, True), timeline(P, False),
           '<p class="chain-key">Dot: the oldest accepted evidence. Shaded box: the published range. Line: the wait '
           'since the step before. Blue &ldquo;once&rdquo;: happened a single time on Earth.</p>', '</div>',
           '<div class="chain-steps">']
    for k, head, text in cards:
        out.append(f'<div class="step" data-step="{k}"><p class="ev">{head}</p><p>{text}</p></div>')
    out.append("</div>\n</figure>")
    return "\n".join(out)


# --------------------------------------------------------------- the figures ---
def fig(title, wide_svg, phone_svg, caption):
    return (f'<figure class="gf-fig wide" role="img" aria-label="{E(title)}"><div class="gf-figbox">{wide_svg}'
            f'{phone_svg}</div><figcaption class="dim"><b>{E(title)}.</b> {caption}</figcaption></figure>')


PHONE_TRAIT = {"CAM photosynthesis": "CAM plants", "C4 photosynthesis": "C4 plants",
               "Simple multicellularity": "Simple multicell", "Farming, by humans": "Farming, human",
               "Farming, by insects": "Farming, insect", "Complex multicellularity": "Complex multicell",
               "Complex cognition": "Cognition", "Powered flight": "Flight",
               "Oxygen-making photosynthesis": "O2 photosynth.", "Complex (eukaryotic) cell": "Complex cell",
               "Cumulative technology": "Technology"}


def origins_svg(wide):
    import math
    if wide:
        Wd, X0, X1, RH, top = 900, 270, 790, 26, 34
    else:
        Wd, X0, X1, RH, top = 320, 124, 272, 24, 34
    H = top + len(S.ORIGINS) * RH + 4

    def x(c):
        return X0 + math.log10(c) / 2 * (X1 - X0)
    o = [f'<svg class="gf gf-orig" viewBox="0 0 {Wd} {H}" width="{Wd}" height="{H}" aria-hidden="true">']
    o.append(f'<text class="dim" x="{X0}" y="12">{"Independent origins (log scale)" if wide else "Origins"}</text>')
    for c in (1, 2, 5, 10, 20, 50, 100):
        if not wide and c in (2, 20):
            continue
        o.append(f'<line class="grid" x1="{x(c):.1f}" x2="{x(c):.1f}" y1="{top - 8}" y2="{H - 2}"/>')
        o.append(f'<text class="dim" x="{x(c):.1f}" y="{top - 12}" text-anchor="middle">{c}</text>')
    for i, (name, c, lab, chain, _src, _note) in enumerate(S.ORIGINS):
        y = top + i * RH + RH / 2
        nm = name if wide else PHONE_TRAIT.get(name, name)
        cls = "nm acc" if chain and c == 1 else ("nm" if wide else "")
        o.append(f'<text class="{cls}" x="0" y="{y + 4:.1f}">{E(nm)}</text>')
        k = "on" if c == 1 else "off"
        o.append(f'<line class="stem-{k}" x1="{X0}" x2="{x(c):.1f}" y1="{y:.1f}" y2="{y:.1f}"/>')
        if "-" in lab:
            hi = float(lab.split("-")[1])
            o.append(f'<line class="range" x1="{x(c):.1f}" x2="{x(hi):.1f}" y1="{y:.1f}" y2="{y:.1f}"/>')
        o.append(f'<circle class="pt-{k}" cx="{x(c):.1f}" cy="{y:.1f}" r="4.5"/>')
        end = x(float(lab.split("-")[1])) if "-" in lab else x(c)
        o.append(f'<text class="{"acc" if c == 1 else "dim"}" x="{end + 8:.1f}" y="{y + 4:.1f}">{E(lab)}</text>')
    o.append("</svg>")
    return "".join(o)


def hard_svg(P, wide):
    h = P["hard"]
    rows_ = [(f"{g1(m)} Gyr" if wide else g1(m), d) for m, d in zip(h["means"], h["dur"])]
    rows_.append(("Time left", h["left"]))
    if wide:
        Wd, LR, X0, X1, RH, top, VMAX = 900, 170, 190, 790, 30, 40, 1.5
    else:
        Wd, LR, X0, X1, RH, top, VMAX = 320, 70, 80, 262, 28, 40, 1.5
    H = top + len(rows_) * RH + 4

    def x(v):
        return X0 + v / VMAX * (X1 - X0)
    o = [f'<svg class="gf gf-hard" viewBox="0 0 {Wd} {H}" width="{Wd}" height="{H}" aria-hidden="true">']
    o.append(f'<text class="dim" x="{LR}" y="12" text-anchor="end">{"Average wait, alone" if wide else "Alone"}</text>')
    o.append(f'<text class="dim" x="{X0}" y="12">{"Average wait in the histories that finish in time, Gyr" if wide else "In time, Gyr"}</text>')
    for t in (0, 0.5, 1.0, 1.5):
        o.append(f'<line class="grid" x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top - 8}" y2="{H - 2}"/>')
        o.append(f'<text class="dim" x="{x(t):.1f}" y="{top - 12}" text-anchor="middle">{g1(t) if t else "0"}</text>')
    o.append(f'<line class="flat" x1="{x(h["flat"]):.1f}" x2="{x(h["flat"]):.1f}" y1="{top - 4}" y2="{H - 2}"/>')
    for i, (lab, d) in enumerate(rows_):
        y = top + i * RH + RH / 2
        last = i == len(rows_) - 1
        o.append(f'<text class="{"dim" if last else ""}" x="{LR}" y="{y + 4:.1f}" text-anchor="end">{E(lab if wide or not last else "Left")}</text>')
        o.append(f'<rect class="{"bar-left" if last else "bar"}" x="{X0}" y="{y - 7:.1f}" width="{x(d) - X0:.1f}" height="14"/>')
        o.append(f'<text x="{x(d) + 6:.1f}" y="{y + 4:.1f}">{f"{d:.2f}"}</text>')
    o.append("</svg>")
    return "".join(o)


def fig_origins(v):
    return fig("Independent origins of traits, by published count",
               origins_svg(True), origins_svg(False),
               "Each dot is the number of times a trait evolved separately; a line to the right shows a published range. "
               "Blue: steps of this page's chain that happened once. Counts marked + are minimums. "
               "Sources: Gilman et al. 2023; Sage et al. 2011; Salvini-Plawen and Mayr 1977, via Lamb et al. 2009; "
               "Grosberg and Strathmann 2007; Larson et al. 2014; Mueller et al. 2005; Knoll 2011; Emery and "
               "Clayton 2004 (this page's tally); Dudley et al. 2007; Woods 2010; Ponce-Toledo et al. 2017; "
               "Fischer et al. 2016; Roger et al. 2017; Tennie et al. 2009.")


def fig_hard(P, v):
    h = P["hard"]
    return fig("Hard steps look equally long in hindsight",
               hard_svg(P, True), hard_svg(P, False),
               f"Five steps, each with an exponential waiting time; the left column gives each step's average wait "
               f"if it ran alone. Bars: the average wait over the {v['n_kept']} simulated histories in which all five "
               f"finish inside a {g1(h['T'])}-billion-year window. The dashed line is the window divided by "
               f"{int(round(h['T'] / h['flat']))}, the number of hard steps plus one. Spread is wide: in any one "
               f"history a hard step can take from almost nothing to over {g1(2 * h['flat'])} billion years. "
               "Model after Carter 1983, Hanson 1998 and Watson 2008; this page's simulation.")


def table_ahead():
    o = ['<table class="gf-ahead">', '<thead><tr><th>Estimate</th><th class="n">Value</th><th>Kind, by whom</th>'
         '</tr></thead>', '<tbody>']
    for what, val, kind, who, year, _src in S.AHEAD:
        o.append(f'<tr><td>{E(what)}</td><td class="n">{E(val)}</td><td>{E(kind)}; {E(who)}, {year}</td></tr>')
    o.append("</tbody></table>")
    return "\n".join(o)


def fits():
    """Every label inside its column, at the sizes in the module docstring."""
    bad = []
    for key, (wn, pn, wd, pd) in ROW_NAMES.items():
        if len(pn) * MONO > 66 or len(pd) * MONO > 66:
            bad.append(pn)
        if len(wn) * SANS > 190 or len(wd) * MONO > 190:
            bad.append(wn)
    for s in S.STEPS:
        if len(s["short"]) * MONO > 66:
            bad.append(s["short"])
        if len(s["name"]) * SANS > 190:
            bad.append(s["name"])
    for name, *_ in S.ORIGINS:
        if len(PHONE_TRAIT.get(name, name)) * MONO > 118:
            bad.append(name)
        if len(name) * SANS > 260:
            bad.append(name)
    if bad:
        raise SystemExit(f"labels too long for their columns: {bad}")


# ---------------------------------------------------------------- claims ---
def claims(P, v):
    c, h, sdo = P["chain"], P["hard"], P["sdo"]
    once = [s for s in S.STEPS if s["count"] == 1]
    eyes = [o for o in S.ORIGINS if o[0] == "Eyes"][0]
    k = [
        ("h1: 'five big steps', 'three happened only once'", len(S.STEPS) == 5 and len(once) == 3),
        ("'the longest wait ... from oxygen-making photosynthesis to the complex cell'", c["longest"] == "cell"),
        ("hard steps 'about {h_dur}': every step with mean > T within 10% of T/(n+1)",
         all(abs(d - h["flat"]) / h["flat"] < 0.10 for d, m in zip(h["dur"], h["means"]) if m > h["T"])),
        ("'the time left over at the end is the same size'", abs(h["left"] - h["flat"]) / h["flat"] < 0.05),
        ("'a step a thousand times harder ... does not take longer': 1,000 Gyr and 10,000 Gyr steps within 2%",
         abs(h["dur"][-1] - h["dur"][-2]) / h["dur"][-1] < 0.02 and h["means"][-2] / h["means"][1] >= 100),
        ("'Earth fits that pattern': mean wait within 25% of T/(n+1) for five steps",
         abs(c["wait_mean"] - c["T"] / 6) / (c["T"] / 6) < 0.25),
        ("'about {left} billion years ... remain' is about the size of the waits",
         c["wait_min"] <= S.WINDOW["end_gyr"] <= c["wait_max"]),
        ("'about four fifths' / used share 0.77-0.85", 0.77 <= c["used"] <= 0.85),
        ("'about {p_alone} percent': our reproduction within 1 point of the paper",
         abs(sdo["p_alone"] - S.SDO["paper_p_alone"]) < 0.01),
        ("'about a ninth of humanity's total energy supply': 0.10-0.125",
         0.10 <= v["_bl_share"] <= 0.125),
        ("'a {xpt_ratio}-fold gap'", round(S.AHEAD_NUM["xpt_ex"] / S.AHEAD_NUM["xpt_sf"]) == 6),
        ("'about half of Earth's history': Mills 0.45-0.55", 0.45 <= S.COUNTER["mills_frac"] <= 0.55),
        ("'a few percent of rocks thrown off Mars reach Earth': 1-5%", 0.01 <= S.COUNTER["worth_mars"] <= 0.05),
        ("'short beside Earth's 4.5 billion': crossing under a tenth of Earth's age",
         S.SKY["cross_myr"] / 1000 < 0.1 * S.WINDOW["earth_ga"]),
        ("'a trait that appeared 40 to 65 separate times, as eyes did'", eyes[1] == 40 and eyes[2] == "40-65"),
        ("'Six times' in card 4", S.STEPS[3]["count"] == 6),
        ("'less than 1 in a few billion' plain rejection vs sampler acceptance above 1%", h["accept"] > 0.01),
        ("'a hard step can take ... over {2 flat}': sd comparable to mean", min(h["sd"][1:]) > 0.7 * h["flat"]),
    ]
    bad = [n for n, ok in k if not ok]
    if bad:
        raise SystemExit("numbers contradict the template's words:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    c, h, sdo, K = P["chain"], P["hard"], P["sdo"], S.SKY
    org = {o[0]: o for o in S.ORIGINS}
    human_w = K["human_ej"] * 1e18 / (365.25 * 86400)
    v = {
        "n_eyes": "40 to 65", "n_traits": str(len(S.ORIGINS)),
        "n_multi": "six" if org["Complex multicellularity"][1] == 6 else str(org["Complex multicellularity"][1]),
        "n_simple": str(org["Simple multicellularity"][1]), "n_farm": str(org["Farming, by humans"][1]),
        "n_insect": {9: "nine"}.get(org["Farming, by insects"][1], str(org["Farming, by insects"][1])),
        "w_cell": g1([r for r in c["rows"] if r["key"] == "cell"][0]["wait"]),
        "n_hard": {5: "five"}[len(h["means"])], "h_min": g1(h["means"][0]), "h_max": f"{h['means'][-1]:,.0f}",
        "T": g1(c["T"]), "h_dur": f"{h['flat']:.1f}", "h_left": f"{h['left']:.1f}",
        "w_min": g1(c["wait_min"]), "w_max": g1(c["wait_max"]), "w_mean": g1(c["wait_mean"]),
        "left": g1(S.WINDOW["end_gyr"]), "end_lo": g1(S.WINDOW["end_band"][0]), "end_hi": g1(S.WINDOW["end_band"][1]),
        "start": g1(S.WINDOW["start_ga"]), "earth": "4.5",
        "wat_T": g1(S.WATSON["T"]), "wat_left": g1(S.WATSON["left"]), "wat_n": str(S.WATSON["n"]),
        "mills_frac": "half",
        "sdo_dex": str(S.SDO["lnR_sd_dex"]), "p_alone": f"{100 * S.SDO['paper_p_alone']:.0f}",
        "p_alone_ours": f"{100 * sdo['p_alone']:.1f}", "sdo_n": f"{sdo['n']:,}",
        "post_lo": f"{100 * S.SDO['post_lo']:.0f}", "post_hi": f"{100 * S.SDO['post_hi']:.1f}",
        "ghat": f"{K['ghat_galaxies']:,}", "ghat_frac": f"{100 * K['ghat_max_frac']:.0f}",
        "bl_stars": f"{K['bl_stars']:,}", "bl_frac": f"{100 * K['bl_frac']:.2f}", "bl_tw": f"{K['bl_eirp_w'] / 1e12:.1f}",
        "bl_share": "a ninth", "_bl_share": K["bl_eirp_w"] / human_w,
        "haystack": "6.0 &times; 10<sup>&minus;18</sup>" if K["haystack"] == 6.0e-18 else None,
        "litres": f"{K['haystack_litres']:,}", "cross": str(K["cross_myr"]),
        "xpt_sf": f"{100 * S.AHEAD_NUM['xpt_sf']:.0f}", "xpt_ex": f"{100 * S.AHEAD_NUM['xpt_ex']:.0f}",
        "xpt_ratio": {6: "six"}[round(S.AHEAD_NUM["xpt_ex"] / S.AHEAD_NUM["xpt_sf"])],
        "accept_inv": f"{round(1 / h['accept']):,}", "n_kept": f"{h['n']:,}",
        "used": f"{100 * c['used']:.0f}",
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    claims(P, v)
    fits()
    v["stamp"] = insight.stamp(live=False)
    life_wait = g1(c["rows"][0]["wait"])
    v["takeaways"] = insight.takeaways([
        f"Life appeared within {life_wait} billion years of the first water on Earth, but oxygen-making "
        "photosynthesis, the complex cell and technology each arose only once, so if a Great Filter lies behind "
        "us, it is most likely one of those three.",
        f"The five waits between the big steps all lie between {v['w_min']} and {v['w_max']} billion years; a "
        "simple model shows that steps of very different difficulty look evenly spaced in hindsight, so the longest "
        "wait does not mark the hardest step.",
        "Searches rule out galaxies whose civilizations turn most starlight into heat, but radio searches have "
        "covered a tiny fraction of the possible signals, and estimates of a filter ahead are judgements that "
        "differ six-fold even within one survey."])
    v["hero"] = hero(P, v)
    v["fig_origins"] = fig_origins(v)
    v["fig_hard"] = fig_hard(P, v)
    v["table_ahead"] = table_ahead()
    del v["_bl_share"]
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
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)) - {"used"})   # "used" is in the hero cards
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        if val is None:
            raise SystemExit(f"{k}: no wording for this value")
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("greatfilter.html")
    if not refs:
        return text, ["greatfilter.html has no entry in add_citations.PAGES"]
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
        print("  greatfilter.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  greatfilter.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
