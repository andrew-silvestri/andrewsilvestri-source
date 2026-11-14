"""
Write site/origins.html from template.html and outputs/payload.json.

Every number on the page comes from the payload (build_origins.py) or is typed in the template beside the
source the reference list gives for it; claims() asserts the directions and ranges the words commit to. The
parts other scripts own - the nav (rebuild_nav.py), the citation markers and Sources list
(add_citations.PAGES["origins.html"], applied here) and the ?v= stamps (bust_cache.py) - are kept as the
shipped page has them, so tests/test_generators.py can run this on the shipped tree and expect no change.
The idiom is oxygen/update_page.py's.

The hero is one drawing of the same membrane in five states (vent, mitochondrion, nerve at rest, spike,
equilibrium), drawn here twice: 900px wide with words and 340px for phones. site/assets/origins.js makes
it sticky and lights one state per step card as the reader scrolls; without JS or with reduced motion
every state shows and the cards follow as plain text. The three charts are inline SVG drawn here at the
two widths the kit ships (720 and 320), styled by scrolly.css's .chart classes so dark mode applies.

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
PAGE = os.path.join(SITE, "origins.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "origins-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

E = html.escape
CW = 0.56 * 12          # Perfidy Mono advance at 12px (charts.js CW)


def tw(s):
    return len(s) * CW


def f(x, k=0):
    s = f"{x:,.{k}f}"
    return "&minus;" + s[1:] if s.startswith("-") else s


class Fit(SystemExit):
    pass


def fits(label, width, what):
    if tw(label) > width:
        raise Fit(f"{what}: label {label!r} is {tw(label):.0f}px, room {width:.0f}px")


# ------------------------------------------------------------------ hero ---
STATES = [   # key, title (wide), word (phone), level difference in mV (outside minus inside), readout, gate
    ("vent", "Vent wall", "vent", None, None, None),
    ("mito", "Mitochondrion", "mito", 172, "172 mV", "make"),
    ("rest", "Nerve at rest", "rest", 70, "70 mV", "pump"),
    ("spike", "Spike", "spike", -40, "+40 mV", "open"),
    ("dead", "Equilibrium", "equil.", 0, "0 mV", None),
]


def panel(i, s, x0, w, top, base, k, wide):
    key, title, word, d, read, gate = s
    cx = x0 + w / 2
    lo_out = 28                          # the lower side's water height above the floor, px
    hi_in = lo_out + max(0, -d) * k      # inside level
    hi_out = lo_out + max(0, d) * k      # outside level
    floor = base
    g = [f'<g class="st" data-s="{i}">']
    g.append(f'<rect class="st-frame" x="{x0 + 4:.1f}" y="{top - 26}" width="{w - 8:.1f}" height="{base - top + 52}" rx="4"/>')
    label = title if wide else word
    fits(label, w - 12, "hero title")
    g.append(f'<text class="st-t" x="{cx:.1f}" y="{top - 8}" text-anchor="middle">{E(label)}</text>')
    # water, inside left of the wall, outside right
    wall_w = 6
    g.append(f'<rect class="st-in" x="{x0 + 10:.1f}" y="{floor - hi_in:.1f}" width="{cx - wall_w / 2 - x0 - 10:.1f}" height="{hi_in:.1f}"/>')
    g.append(f'<rect class="st-out" x="{cx + wall_w / 2:.1f}" y="{floor - hi_out:.1f}" width="{x0 + w - 10 - cx - wall_w / 2:.1f}" height="{hi_out:.1f}"/>')
    g.append(f'<rect class="st-wall" x="{cx - wall_w / 2:.1f}" y="{top + 4}" width="{wall_w}" height="{floor - top - 4}"/>')
    if gate:
        gy = floor - lo_out - 4
        if gate == "make":
            g.append(f'<circle class="st-gate" cx="{cx:.1f}" cy="{gy:.1f}" r="9"/>')
        elif gate == "pump":
            g.append(f'<rect class="st-gate" x="{cx - 8:.1f}" y="{gy - 8:.1f}" width="16" height="16" rx="2"/>')
        else:
            g.append(f'<rect class="st-gap" x="{cx - 4:.1f}" y="{gy - 9:.1f}" width="8" height="18"/>')
        # three ions that cross the wall when the state is lit and motion is on
        dirn = "in" if gate in ("make", "open") else "out"
        for j in range(3):
            g.append(f'<circle class="ion ion-{dirn} ion-{j}" cx="{cx + (14 if dirn == "in" else -14):.1f}" '
                     f'cy="{gy + (j - 1) * 6:.1f}" r="3"/>')
    if wide:
        g.append(f'<text class="st-side" x="{x0 + 12:.1f}" y="{floor + 16}">in</text>')
        g.append(f'<text class="st-side" x="{x0 + w - 12:.1f}" y="{floor + 16}" text-anchor="end">out</text>')
    g.append(f'<text class="st-v" x="{cx:.1f}" y="{base + (34 if wide else 18)}" text-anchor="middle">{E(read)}</text>')
    g.append("</g>")
    return "".join(g)


def hero_svg(mv, wide):
    states = list(STATES)
    states[0] = ("vent", "Vent wall", "vent", int(mv), "%s mV*" % mv, None)
    W, H = (900, 300) if wide else (340, 236)
    top, base = (52, 236) if wide else (40, 196)
    k = 0.62 if wide else 0.5
    w = W / 5
    cls = "hero-wide" if wide else "hero-phone"
    out = [f'<svg class="og {cls}" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-labelledby="og-desc">']
    for i, s in enumerate(states):
        out.append(panel(i, s, i * w, w, top, base, k, wide))
    out.append("</svg>")
    return "".join(out)


def hero(P, v):
    steps = [
        (0, "1 &middot; A wall at a vent &middot; hypothesis",
         f"Imagine a thin mineral wall in a sea-floor vent, with alkaline vent fluid on one side and the more "
         f"acidic early ocean on the other. The difference in protons across it, about {v['dph']} pH units, is "
         f"worth up to about {v['mv25']} millivolts. The star marks a calculated upper bound, not a measurement. "
         f'<a href="#vent">The vent</a>'),
        (1, "2 &middot; The same push in every cell",
         "A mitochondrion pumps protons out and lets them fall back through ATP synthase, a rotor in its "
         "membrane; the fall makes ATP. It holds about 172 millivolts, the same order as the vent. "
         '<a href="#harvest">The machinery</a>'),
        (2, "3 &middot; A nerve pays to stay ready",
         "A neuron runs the machinery the other way: it spends ATP on a pump that moves sodium out and "
         "potassium in. Potassium leaking back out then holds the inside tens of millivolts below the outside, "
         "about 70 in many mammalian neurons."),
        (3, "4 &middot; Harm opens the gate",
         "A touch or a burn opens channels. Sodium falls in, the inside swings to tens of millivolts above the "
         "outside, and the swing runs along the fibre to the spinal cord, which signals a muscle to pull away. "
         "A single-celled Paramecium "
         "does the same with calcium and backs off. "
         '<a href="#pain">Pain and set points</a>'),
        (4, "5 &middot; Equilibrium",
         "Stop paying and the levels run down towards even. A blocked mould cell falls from about 200 "
         "millivolts to about 30 within a minute. At equilibrium nothing is left to push, so nothing can be made "
         'or sent. For a cell that is death. <a href="#goal">The end goal</a>'),
    ]
    desc = ("Five panels show the same membrane as a wall with water on each side; the difference in level is the "
            "push. Vent wall: up to about %s millivolts, calculated from pH. Mitochondrion: 172. Nerve at rest: 70, "
            "after a pump has sorted the ions. Spike: the inside rises 40 above the outside. Equilibrium: 0."
            % v["mv25"])
    out = ['<figure class="grad wide" aria-label="One membrane, five states">',
           '<div class="grad-fig">', f'<p id="og-desc" hidden>{E(desc)}</p>',
           hero_svg(v["mv25"], True), hero_svg(v["mv25"], False),
           '<p class="grad-key">Left of each wall: inside; right: outside. The gap between the levels is the push: '
           'a pH difference stated as millivolts at the vent, proton-motive force in the mitochondrion, membrane '
           'voltage in the nerve. Circle: ATP synthase. Square: the sodium-potassium pump. Bar: an open channel. '
           'Dots: ions crossing. * calculated from pH, an upper bound.</p>', '</div>', '<div class="grad-steps">']
    for k, head, text in steps:
        out.append(f'<div class="step" data-step="{k}"><p class="ev">{head}</p><p>{text}</p></div>')
    out.append("</div>\n</figure>")
    return "\n".join(out)


# ---------------------------------------------------------------- charts ---
def figure(title, wide_svg, phone_svg, caption):
    return ('<figure class="step-fig wide" role="img" aria-label="%s"><div class="snap-wide">%s</div>'
            '<div class="snap-phone">%s</div><figcaption class="dim"><b>%s.</b> %s</figcaption></figure>'
            % (E(title), wide_svg, phone_svg, E(title), caption))


def svg_open(W, H):
    return f'<svg class="chart" viewBox="0 0 {W} {H}" width="{W}" height="{H}" aria-hidden="true">'


def ladder_rows(P):
    g = P["gradient"]
    rows = [{"label": "Vent pH gradient, as millivolts*", "short": "vent, calculated*", "lo": g["lo"], "hi": g["hi"],
             "mid": g["mv25"], "est": True}]
    rows += [{"label": r["label"], "short": r["short"], "lo": r["lo"], "hi": r["hi"], "mid": r["mid"], "est": False}
             for r in P["ladder"]]
    return rows


def chart_ladder(P):
    rows = ladder_rows(P)
    xmax = 300

    def draw(W, wide):
        if wide:
            lab_w, x0, x1, row_h, top = 246, 262, W - 16, 30, 14
        else:
            lab_w, x0, x1, row_h, top = W - 16, 8, W - 12, 44, 8
        H = top + row_h * len(rows) + 30
        sx = lambda v: x0 + (x1 - x0) * v / xmax
        o = [svg_open(W, H)]
        for t in range(0, xmax + 1, 50):
            o.append(f'<line class="ch-grid" x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="{top}" y2="{H - 24}"/>')
            o.append(f'<text class="ch-tick" x="{sx(t):.1f}" y="{H - 8}" text-anchor="middle">{t}</text>')
        o.append(f'<text class="ch-tick" x="{x1:.1f}" y="{top - 2 if not wide else H - 8}" text-anchor="end">'
                 f'{"" if wide else "mV"}</text>' if not wide else "")
        for i, r in enumerate(rows):
            y = top + i * row_h
            label = r["label"] if wide else r["short"]
            if wide:
                fits(label, lab_w, "ladder label")
                o.append(f'<text x="{x0 - 10}" y="{y + 16}" text-anchor="end">{E(label)}</text>')
                by = y + 6
            else:
                fits(label + "  %d-%d" % (r["lo"], r["hi"]), lab_w, "ladder phone label")
                o.append(f'<text x="{x0}" y="{y + 12}">{E(label)}</text>')
                o.append(f'<text class="ch-tick" x="{x1}" y="{y + 12}" text-anchor="end">{r["lo"]}&#8211;{r["hi"]}</text>')
                by = y + 18
            cls = "f-moss" if r["est"] else "f-acc"
            o.append(f'<rect class="ch-band {cls}" x="{sx(0):.1f}" y="{by}" width="{sx(r["lo"]) - sx(0):.1f}" height="14"/>')
            o.append(f'<rect class="{cls}" x="{sx(r["lo"]):.1f}" y="{by}" width="{max(2, sx(r["hi"]) - sx(r["lo"])):.1f}" height="14"/>')
            if wide:
                o.append(f'<text class="ch-tick" x="{sx(r["hi"]) + 6:.1f}" y="{by + 11}">{r["lo"]}&#8211;{r["hi"]}</text>')
        o.append(f'<text class="ch-tick" x="{x1:.1f}" y="{H - 8 - (14 if wide else 0)}" text-anchor="end">'
                 f'{"millivolts" if wide else ""}</text>' if wide else "")
        o.append("</svg>")
        return "".join(o)
    cap = ("The solid part of each bar is the reported range or spread; the paler part runs from zero. The vent "
           "bar is calculated from pH: the Lost City median against the 95 percent range of the modelled early "
           "ocean, at 25 and 70&nbsp;&deg;C. The others are measured. Magnitudes only: at rest the inside of each cell "
           "is negative. Data: MARHYS 3.0; "
           "Krissansen-Totton et al. 2018; BioNumbers; Reyer et al. 2020; Lo et al. 2007; Hodgkin and Huxley 1939.")
    return figure("Push across a membrane or barrier, millivolts", draw(720, True), draw(320, False), cap)


TL = [   # key, wide label, phone label
    ("earth", "Earth forms", "Earth forms"),
    ("water", "liquid water (zircon)", "liquid water"),
    ("luca", "common ancestor, est.", "common ancestor"),
    ("life", "oldest accepted life", "oldest accepted life"),
    ("goe", "oxygen in the air", "oxygen in the air"),
    ("euk", "complex cells", "complex cells"),
    ("animals", "first animal fossils", "first animals"),
    ("brain", "oldest fossil brain", "oldest fossil brain"),
]


def chart_time(P):
    T = P["timeline"]

    def wide_svg():
        W, x0, x1 = 720, 20, 700
        H, axis = 190, 120
        sx = lambda ma: x0 + (x1 - x0) * (4600 - ma) / 4600
        o = [svg_open(W, H)]
        o.append(f'<rect class="ch-band f-moss" x="{sx(T["life"]["ma"]):.1f}" y="{axis - 14}" '
                 f'width="{sx(T["brain"]["ma"]) - sx(T["life"]["ma"]):.1f}" height="14"/>')
        o.append(f'<text x="{(sx(T["life"]["ma"]) + sx(T["brain"]["ma"])) / 2:.1f}" y="{axis - 20}" '
                 f'text-anchor="middle">life with no fossil nervous system, {f(T["gap"])} million years</text>')
        o.append(f'<line class="ch-axis" x1="{x0}" x2="{x1}" y1="{axis}" y2="{axis}"/>')
        for t in range(0, 4601, 1000):
            o.append(f'<line class="ch-axis" x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="{axis}" y2="{axis + 5}"/>')
            o.append(f'<text class="ch-tick" x="{sx(t):.1f}" y="{H - 6}" text-anchor="middle">'
                     f'{"now" if t == 0 else "%s" % f(t / 1000, 0) + " bn yr ago"}</text>')
        # labels alternate between two rows below the axis, and the top for the first four
        prev = {}
        for i, (k, lab, _) in enumerate(TL):
            x = sx(T[k]["ma"])
            row = i % 2
            y = axis + 22 + row * 18 if i >= 3 else 18 + row * 18 + (36 if i == 2 else 0)
            anchor = "start" if x < 360 else "end"
            tx = x + 4 if anchor == "start" else x - 4
            o.append(f'<line class="ch-grid" x1="{x:.1f}" x2="{x:.1f}" y1="{min(y, axis)}" y2="{max(y - 10, axis)}"/>')
            o.append(f'<circle class="f-acc" cx="{x:.1f}" cy="{axis}" r="3.5"/>')
            o.append(f'<text x="{tx:.1f}" y="{y}" text-anchor="{anchor}">{E(lab)}</text>')
            lo = tx if anchor == "start" else tx - tw(lab)
            hi = lo + tw(lab)
            if y in prev and lo < prev[y] + 6:
                raise Fit(f"timeline label {lab!r} overlaps the one before it on its row")
            prev[y] = hi
        o.append("</svg>")
        return "".join(o)

    def phone_svg():
        W, y0, y1 = 320, 14, 300
        H = 324
        sy = lambda ma: y0 + (y1 - y0) * (4600 - ma) / 4600
        ax = 70
        o = [svg_open(W, H)]
        o.append(f'<rect class="ch-band f-moss" x="{ax - 7}" y="{sy(T["life"]["ma"]):.1f}" width="14" '
                 f'height="{sy(T["brain"]["ma"]) - sy(T["life"]["ma"]):.1f}"/>')
        o.append(f'<line class="ch-axis" x1="{ax}" x2="{ax}" y1="{y0}" y2="{y1}"/>')
        for t in range(0, 4601, 1000):
            o.append(f'<text class="ch-tick" x="{ax - 12}" y="{sy(t) + 4:.1f}" text-anchor="end">'
                     f'{"now" if t == 0 else "%s bn" % f(t / 1000, 0)}</text>')
        last = -99
        for k, _, lab in TL:
            y = sy(T[k]["ma"])
            ty = max(y + 4, last + 15)
            fits(lab, W - ax - 24, "timeline phone label")
            o.append(f'<circle class="f-acc" cx="{ax}" cy="{y:.1f}" r="3.5"/>')
            o.append(f'<text x="{ax + 14}" y="{ty:.1f}">{E(lab)}</text>')
            last = ty
        o.append(f'<text class="ch-tick" x="{ax + 14}" y="{H - 4}">shaded: no fossil nervous system</text>')
        o.append("</svg>")
        return "".join(o)
    cap = ("Dates in billions of years before present. The shaded span runs from the oldest widely accepted "
           f"traces of life, about {f(T['life']['ma'])} million years ago, to the oldest fossil brain, about "
           f"{f(T['brain']['ma'])} million: some {f(T['gap'])} million years. Fossils give minimum ages, so nerves may be "
           "older. The common ancestor is a 2024 model estimate (4.09 to 4.33 billion years). Data: ICS chart 2024; "
           "Wilde et al. 2001; Moody et al. 2024; Djokic et al. 2017; Ma et al. 2012; and others in the "
           "page's archive (timeline.csv).")
    return figure("From Earth's formation to the first brains", wide_svg(), phone_svg(), cap)


def chart_comfort(P):
    A = P["ashrae"]
    B = A["bins"]
    lines = [("w", "wanted warmer", "c-acc", "f-acc"), ("nc", "no change", "c-ink", "f-ink"),
             ("c", "wanted cooler", "c-moss", "f-moss")]

    def draw(W, wide):
        x0, x1 = (52, W - 130) if wide else (36, W - 10)
        top, H = 16, (300 if wide else 290)
        y1 = H - 34
        lo, hi = A["bin_lo"], A["bin_hi"]
        sx = lambda t: x0 + (x1 - x0) * (t - lo) / (hi - lo)
        sy = lambda s: y1 - (y1 - top) * s
        o = [svg_open(W, H)]
        for s in (0, .25, .5, .75, 1):
            o.append(f'<line class="ch-grid" x1="{x0}" x2="{x1}" y1="{sy(s):.1f}" y2="{sy(s):.1f}"/>')
            o.append(f'<text class="ch-tick" x="{x0 - 6}" y="{sy(s) + 4:.1f}" text-anchor="end">{int(s * 100)}%</text>')
        for t in range(int(lo + (5 - lo % 5) % 5), int(hi) + 1, 5):
            o.append(f'<text class="ch-tick" x="{sx(t):.1f}" y="{H - 16}" text-anchor="middle">{t}</text>')
        o.append(f'<text class="ch-tick" x="{x1:.1f}" y="{H - 2}" text-anchor="end">indoor air temperature, &#176;C</text>')
        o.append(f'<line class="ch-axis" x1="{x0}" x2="{x1}" y1="{y1}" y2="{y1}"/>')
        xc = sx(A["cross"]["t"])
        o.append(f'<line class="ch-axis" x1="{xc:.1f}" x2="{xc:.1f}" y1="{top}" y2="{y1}" stroke-dasharray="3 3"/>')
        lab = "balance %s&#176;C" % f(A["cross"]["t"], 1)
        o.append(f'<text class="ch-tick" x="{xc + 5:.1f}" y="{top + 10}">{lab}</text>')
        ends = []
        for key, name, cs, fs in lines:
            pts = " ".join(f"{sx(b['t'] + 0.5):.1f},{sy(b[key]):.1f}" for b in B)
            o.append(f'<polyline class="ch-line {cs}" points="{pts}"/>')
            if wide and key != "nc":
                ends.append([sy(B[-1][key]) + 4, name, fs])
        if wide:
            pk = max(B, key=lambda b: b["nc"])     # "no change" is labelled at its peak, not its tail
            o.append(f'<text class="f-ink" x="{sx(pk["t"] + 0.5):.1f}" y="{sy(pk["nc"]) - 10:.1f}" '
                     f'text-anchor="middle">no change</text>')
            ends.sort()
            for i in range(1, len(ends)):
                ends[i][0] = max(ends[i][0], ends[i - 1][0] + 15)
            for y, name, fs in ends:
                o.append(f'<text class="{fs}" x="{x1 + 8}" y="{y:.1f}">{name}</text>')
        else:
            # direct labels inside the plot, where the lines are apart
            o.append(f'<text class="f-acc" x="{sx(lo + 0.6):.1f}" y="{sy(B[0]["w"]) + 18:.1f}">warmer</text>')
            o.append(f'<text class="f-moss" x="{sx(hi - 0.6):.1f}" y="{sy(B[-1]["c"]) + 18:.1f}" text-anchor="end">cooler</text>')
            pk = max(B, key=lambda b: b["nc"])
            o.append(f'<text class="f-ink" x="{sx(pk["t"] + 0.5):.1f}" y="{sy(pk["nc"]) - 8:.1f}" text-anchor="middle">no change</text>')
        o.append("</svg>")
        return "".join(o)
    cap = (f"Share of votes by indoor air temperature, in the unbroken run of 1 &deg;C bins from {f(A['bin_lo'])} "
           f"to {f(A['bin_hi'])}&nbsp;&deg;C that each hold at least {A['min_n']} votes ({f(A['n_chart'])} of "
           f"{f(A['votes'])} votes, from {A['buildings']} buildings). The dashed line is where requests for warmer and cooler "
           "balance. Data: ASHRAE Global Thermal Comfort Database II, version 2.1.0 (CC BY 4.0); this page's "
           "analysis.")
    return figure("What people asked for, by indoor temperature", draw(720, True), draw(320, False), cap)


# ---------------------------------------------------------------- claims ---
def claims(P, v):
    A, g, L = P["ashrae"], P["gradient"], {r["key"]: r for r in P["ladder"]}
    c = [
        ("'Between 23 and 24 C, {peak_pct} percent wanted no change': the peak bin is 23", A["peak"]["t"] == 23),
        ("'half wanted to be warmer between 18 and 19 C': 0.45-0.55", 0.45 <= A["at_18"]["w"] <= 0.55),
        ("'two thirds wanted to be cooler between 30 and 31 C': 0.62-0.70", 0.62 <= A["at_30"]["c"] <= 0.70),
        ("'four people in ten wanted something else' at the balance point: no-change peak 0.55-0.65",
         0.55 <= A["peak"]["nc"] <= 0.65),
        ("'close to the 0.31': neutral slope within 0.05", abs(A["slope_neut"]["v"] - 0.31) <= 0.05),
        ("'A working mitochondrion holds about 172'", L["mito"]["mid"] == 172),
        ("'the same size as the one every complex cell runs on': vent 0.8-1.5x mitochondrion",
         0.8 <= g["mv25"] / L["mito"]["mid"] <= 1.5),
        ("'Dry air breaks down at about 3'; field 'ten times'", P["field"]["air"] == 3 and P["field"]["x_lo"] >= 10),
        ("'swing was 80 to 95 millivolts'", (L["squid_ap"]["lo"], L["squid_ap"]["hi"]) == (80, 95)),
        ("'some 50 to 70 millivolts below the outside'", L["squid_rest"]["hi"] == 50),
        ("timeline gap rounds to 2,960", P["timeline"]["gap"] == 2960),
    ]
    bad = [n for n, ok in c if not ok]
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    A, g, V, T = P["ashrae"], P["gradient"], P["vents"], P["timeline"]
    v = {
        "n_ph": str(V["n_ph"]), "n_ph_hf": str(V["n_ph_hf"]), "n_ph_em": str(V["n_ph_em"]), "ph_papers": {8: "eight"}.get(V["ph_papers"], str(V["ph_papers"])),
        "ph_med": f(V["ph_med"], 1), "n_t": str(V["n_t"]), "t_med": f(V["t_med"]), "n_rows": str(V["n_rows"]),
        "ocean": f(g["ocean"], 1), "ocean_lo": f(g["ocean_lo"], 1), "ocean_hi": f(g["ocean_hi"], 1),
        "s25": f(g["s25"], 1), "s70": f(g["s70"], 1), "dph": f(g["dph"], 1),
        "mv25": f(round(g["s25"] * round(g["dph"], 1))), "mv70": f(round(g["s70"] * round(g["dph"], 1))),
        "g_lo": str(g["lo"]), "g_hi": str(g["hi"]),
        "f_lo": str(P["field"]["lo_mvm"]), "f_hi": str(P["field"]["hi_mvm"]), "air": str(P["field"]["air"]),
        "life": f(T["life"]["ma"]), "gap": f(T["gap"]),
        "rows_raw_c": f(A["rows_raw"]), "votes_c": f(A["votes"]), "buildings": str(A["buildings"]),
        "peak_pct": f(100 * A["peak"]["nc"]),
        "cross": f(A["cross"]["t"], 1), "cross_lo": f(A["cross"]["lo"], 1), "cross_hi": f(A["cross"]["hi"], 1),
        "sl_neut": f(A["slope_neut"]["v"], 2), "sl_pref": f(A["slope_pref"]["v"], 2),
        "sl_logit": f(A["slope_pref_logit"]["v"], 2), "sl_logit_lo": f(A["slope_pref_logit"]["lo"], 2),
        "sl_logit_hi": f(A["slope_pref_logit"]["hi"], 2),
        "min_n": str(A["min_n"]), "bin_lo": f(A["bin_lo"]), "bin_hi": f(A["bin_hi"]),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    v["stamp"] = insight.stamp(live=False)
    v["takeaways"] = insight.takeaways([
        f"A mitochondrion holds 150 to 200 millivolts across a membrane about 5 nanometres thick, a field of "
        f"{v['f_lo']} to {v['f_hi']} million volts a metre, about ten times what makes dry air spark; other cells "
        f"hold from about ten to two hundred.",
        f"A leading hypothesis says life began on a ready-made gradient: modern Lost City vent fluid against a "
        f"modelled early ocean is worth up to about {v['mv25']} millivolts, the same order as a mitochondrion's "
        f"172, though no experiment has shown a vent making life.",
        f"In {v['votes_c']} comfort votes, {v['peak_pct']} percent wanted no change at 23 to 24 &deg;C and requests "
        f"to change rose on both sides, the U-shape a set point predicts, though thermal preference is not pain."])
    claims(P, v)
    v["hero"] = hero(P, v)
    v["chart_ladder"] = chart_ladder(P)
    v["chart_time"] = chart_time(P)
    v["chart_comfort"] = chart_comfort(P)
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
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)))
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("origins.html")
    if not refs:
        return text, ["origins.html has no entry in add_citations.PAGES"]
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
        print("  origins.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  origins.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
