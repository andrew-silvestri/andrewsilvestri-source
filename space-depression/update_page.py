"""
Write site/space-depression.html from template.html and outputs/payload.json.

Every number on the page comes from the payload, and every figure quoted from a paper or a NASA report was matched
in that document's text by the build (sources.FACTS); the prose is in the template. The parts other scripts own -
the nav (rebuild_nav.py), the citation markers and Sources list (add_citations.py's table, applied here) and the
?v= stamps (bust_cache.py) - are kept as the shipped page has them, so tests/test_generators.py can run this on
the shipped tree and expect no change. The idiom is oxygen/update_page.py's.

The hero is an evidence map drawn here as two SVGs (900px and 340px wide): one dot per person per flight, placed by
the flight's length (log scale) in a row for where it went - Earth orbit, the Moon - with the ground rehearsals in
a row below and NASA's Mars missions in an empty row above. Elements carry data-o, the step that introduces them;
site/assets/evmap.js sets data-step on the figure as the reader scrolls, and evmap.css dims and lights by step.
Without JS, or with reduced motion, every element shows.

claims() asserts every direction and range the template's words commit to ("less than half of NASA's reference
mission", "most trips are short", "about 13 times"). If a rebuild moves one, the generator stops rather than ship
prose the payload contradicts.

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
PAGE = os.path.join(SITE, "space-depression.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "space-depression-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

E = html.escape
YEAR = 365.25
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
CW = 0.56 * 12          # Perfidy Mono at 12px: 0.56 em a character (charts.js uses the same advance)


def num(x, k=0):
    return f"{x:,.{k}f}"


def day(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


# ------------------------------------------------------------------ hero ---
LO, HI = 0.05, 1200.0     # days; the shortest orbital flight is under two hours, the Mars box ends at 950


class Geo:
    def __init__(self, wide):
        self.wide = wide
        if wide:
            self.W, self.x0, self.x1 = 900, 186, 884
            self.rows = [("mars", 64), ("moon", 54), ("orbit", 176), ("ground", 92)]
            self.head = 0
        else:
            self.W, self.x0, self.x1 = 340, 8, 332
            self.rows = [("mars", 70), ("moon", 62), ("orbit", 168), ("ground", 104)]
            self.head = 20                      # a row's name sits on a line above its band on the phone
        self.top = {}
        y = 8
        for k, h in self.rows:
            self.top[k] = (y + self.head, h)
            y += self.head + h + 10
        self.H = y + 34                         # the axis

    def x(self, d):
        a, b = math.log10(LO), math.log10(HI)
        return self.x0 + (math.log10(d) - a) / (b - a) * (self.x1 - self.x0)


def _fits(text, x, anchor, g, lo=None, hi=None):
    """A label at x with this anchor stays inside [lo, hi] (default: the drawing). Mono advance is exact."""
    w = len(text) * CW
    a = x - w if anchor == "end" else x - w / 2 if anchor == "middle" else x
    lo = 0 if lo is None else lo
    hi = g.W if hi is None else hi
    if a < lo - 0.5 or a + w > hi + 0.5:
        raise SystemExit(f"hero label {text!r} ({w:.0f}px) does not fit at x={x:.0f} in [{lo}, {hi}] "
                         f"({'wide' if g.wide else 'phone'})")


def text(g, x, y, s, cls="", anchor="start", o=None, lo=None, hi=None):
    _fits(s, x, anchor, g, lo, hi)
    oa = f' data-o="{o}"' if o is not None else ""
    ca = f' class="{cls}"' if cls else ""
    an = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text{ca} x="{x:.1f}" y="{y:.1f}"{an}{oa}>{E(s)}</text>'


def hero_svg(P, wide):
    g = Geo(wide)
    S, A, D = P["stats"], P["analogs"], P["delay"]
    f = P["facts"]
    out = [f'<svg class="evmap-svg {"evmap-wide" if wide else "evmap-phone"}" viewBox="0 0 {g.W} {g.H}" '
           f'width="{g.W}" height="{g.H}" role="img" aria-labelledby="evmap-desc">']
    names = {"mars": "Mars", "moon": "To the Moon", "orbit": "Earth orbit", "ground": "Sealed on Earth"}
    subs = {"mars": f"{D['mars']['lo']['min']:.0f} to {D['mars']['hi']['min']:.0f} min away",
            "moon": f"{D['moon']['lo_s']:.1f} to {D['moon']['hi_s']:.1f} s away",
            "orbit": f"{S['n_orbit']:,} flights",
            "ground": "rehearsals"}
    # rows: a hairline band, its name and a line under the name
    for k, _ in g.rows:
        t, h = g.top[k]
        out.append(f'<rect class="band band-{k}" x="{g.x0}" y="{t}" width="{g.x1 - g.x0}" height="{h}"/>')
        if wide:
            out.append(text(g, 8, t + 20, names[k], "rname"))
            out.append(text(g, 8, t + 38, subs[k], "rsub"))
        else:
            out.append(text(g, g.x0, t - 6, f"{names[k]} · {subs[k]}", "rname-p"))
    # axis: decades of days, and a one-year rule
    base = g.top["ground"][0] + g.top["ground"][1]
    for d, lab in ((1, "1 day"), (10, "10 days"), (100, "100 days"), (1000, "1,000 days")):
        x = g.x(d)
        out.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="{g.top["mars"][0]}" y2="{base}"/>')
        anchor = "end" if d == 1000 else "middle"
        out.append(text(g, x + (10 if d == 1000 else 0), base + 18, lab, "tick", anchor))
    xy = g.x(YEAR)
    out.append(f'<line class="yr" x1="{xy:.1f}" x2="{xy:.1f}" y1="{g.top["mars"][0]}" y2="{base}"/>')
    out.append(text(g, xy - 4, g.top["mars"][0] + 14, "1 year", "tick", "end"))
    out.append(text(g, g.x1, base + 32, "length of one stay, log scale", "tick", "end") if wide else
               text(g, g.x1, base + 32, "length of stay, log scale", "tick", "end"))
    # dots: one per person-flight; y spread through the row by the golden-ratio sequence (repeatable, no RNG)
    paths = {"d-short": [], "d-long": [], "d-moon": []}
    strip = 40 if not wide else 26                # the orbit row keeps a strip at the top for the step notes
    for i, (days, moon, _yr) in enumerate(P["dots"]):
        k = "moon" if moon else "orbit"
        t, h = g.top[k]
        pad = 8
        t0 = t + (strip if k == "orbit" else pad)
        frac = (i * 0.6180339887) % 1
        y = t0 + frac * (t + h - pad - t0)
        cls = "d-moon" if moon else ("d-long" if days > 180 else "d-short")
        paths[cls].append(f"M{g.x(max(days, LO)):.1f} {y:.1f}h0")
    order = {"d-short": 0, "d-long": 1, "d-moon": 3}
    for cls, segs in paths.items():
        out.append(f'<path class="dots {cls}" data-o="{order[cls]}" d="{"".join(segs)}"/>')
    # step notes in the orbit row's top strip, kept apart so the static figure shows all of them
    t, _ = g.top["orbit"]
    n180 = f"{S['n_gt180']} flights over six months"
    meas = f"about {P['n_measured']} measured with a mood scale"
    if wide:
        out.append(text(g, g.x1 - 6, t + 17, n180 + " →", "note", "end", o=1, lo=g.x0, hi=g.x1))
        out.append(text(g, g.x0 + 6, t + 17, "■ " + meas + ", all in orbit", "note note-m", o=2, lo=g.x0, hi=g.x1))
    else:
        out.append(text(g, g.x1 - 4, t + 15, n180 + " →", "note", "end", o=1, lo=g.x0, hi=g.x1))
        out.append(text(g, g.x0 + 4, t + 32, "■ " + meas, "note note-m", o=2, lo=g.x0, hi=g.x1))
    # Moon note, right of its dots
    t, h = g.top["moon"]
    mx = g.x(S["moon_max_days"]) + 10
    moon_note = (f"{S['n_moon']} flights, {S['n_people_moon']} people, {S['py_moon']:.2f} person-years" if wide
                 else f"{S['py_moon']:.2f} person-years")
    out.append(text(g, mx, t + h / 2 + 4, moon_note, "note", o=3, lo=g.x0, hi=g.x1))
    # ground rehearsals: one sub-row each, a mark at the length (a span for HI-SEAS) and its label to the left
    t, h = g.top["ground"]
    sub = (h - 8) / len(A)
    for j, a in enumerate(A):
        y = t + 4 + sub * (j + 0.5)
        x = g.x(a["days"])
        out.append(f'<g class="analog" data-o="4">')
        if a["lo"]:
            out.append(f'<line class="span" x1="{g.x(a["lo"]):.1f}" x2="{x:.1f}" y1="{y:.1f}" y2="{y:.1f}"/>')
            xl = g.x(a["lo"])
        else:
            xl = x
        out.append(f'<path class="mark" d="M{x:.1f} {y - 5:.1f}l5 5l-5 5l-5-5z"/>')
        out.append(text(g, xl - 9, y + 4, f"{a['name']} · {a['n']}", "alab", "end", lo=g.x0, hi=g.x1))
        out.append("</g>")
    # Mars: NASA's reference missions, an empty box
    t, h = g.top["mars"]
    s1, s2 = (int(v) for v in f["dra_short"])
    l1, l2 = (int(v) for v in f["dra_long"])
    xa, xb = g.x(s1), g.x(l2)
    out.append(f'<g class="marsbox" data-o="5"><rect x="{xa:.1f}" y="{t + 6}" width="{xb - xa:.1f}" '
               f'height="{h - 12}" rx="2"/>')
    lab = f"NASA plans: {s1} to {l2} days" if wide else f"NASA plans: {s1}-{l2} days"
    out.append(text(g, xa - 8, t + h / 2 - 2, lab, "mlab", "end", lo=g.x0, hi=g.x1))
    out.append(text(g, xa - 8, t + h / 2 + 14, "no human data", "mlab mlab-2", "end", lo=g.x0, hi=g.x1))
    out.append("</g>")
    out.append("</svg>")
    return "".join(out)


def hero(P, v):
    S, f = P["stats"], P["facts"]
    steps = [
        (0, "Every flight &middot; " + v["first_year"] + " to " + v["through_y"],
         f"Each dot is one person on one flight to orbit or beyond: {v['n_rides']} flights by {v['n_people']} "
         f"people. Left is short, right is long, on a log scale. Most of the dots sit between a few days and two "
         f"weeks."),
        (1, "The long stays",
         f"{v['n_gt180']} flights lasted more than six months and {v['n_ge365']} a year or more, all of them in Earth "
         f"orbit. The longest ran {v['longest_days']} days."),
        (2, "Mood measured in flight",
         f"About {v['n_measured']} of these flights included a standard mood questionnaire, all on space stations "
         f"or the shuttle in Earth orbit. None of the studies found mood falling late in a mission. "
         f'<a href="#flights">The studies</a>'),
        (3, "Beyond Earth orbit",
         f"Only {v['n_people_moon']} people have gone further, all to the Moon, on flights of under two weeks: "
         f"{v['py_moon']} person-years in all, with signals {v['moon_s']} seconds from home."),
        (4, "Rehearsals on the ground",
         "The long-duration evidence comes from sealed habitats and polar stations. Mars-500 kept six men inside "
         f"for {v['m500_days']} days; Concordia's winter crews spent about {v['sandal_mo']} months on the Antarctic "
         'plateau. <a href="#ground">What they found</a>'),
        (5, "Mars",
         f"NASA's reference missions run from {v['dra_s1']} to {v['dra_l2']} days, with messages {v['lo_min']} to "
         f"{v['hi_min']} minutes each way. No human has spent a day in that box. NASA rates the risk of a behavioural "
         f'or psychiatric problem there red. <a href="#rating">The rating</a>'),
    ]
    desc = (f"A chart of every crewed flight to orbit or beyond, one dot per person per flight, placed by length "
            f"on a log scale from under two hours to over a thousand days. Earth orbit holds {v['n_orbit']} flights, "
            f"most under a month, the longest {v['longest_days']} days. The Moon row holds {v['n_moon']} flights, "
            f"all under two weeks. Below, ground rehearsals: Mars-500 at {v['m500_days']} days, CHAPEA, Concordia "
            f"and HI-SEAS. Above, the Mars row is empty except for NASA's planned missions of {v['dra_s1']} to "
            f"{v['dra_l2']} days.")
    out = ['<figure class="evmap wide" aria-label="Where the evidence comes from">',
           '<div class="evmap-fig">', f'<p id="evmap-desc" hidden>{E(desc)}</p>',
           hero_svg(P, True), hero_svg(P, False),
           '<p class="evmap-key">Dots: grey, flights in Earth orbit; blue, longer than six months; brown, to the '
           'Moon. Diamonds: ground rehearsals, with crew size.</p>', '</div>', '<div class="evmap-steps">']
    for k, head, body in steps:
        out.append(f'<div class="step" data-step="{k}"><p class="ev">{head}</p><p>{body}</p></div>')
    out.append("</div>\n</figure>")
    return "\n".join(out)


# ---------------------------------------------------------------- charts ---
def static_chart(spec, caption):
    import insight
    snaps = insight._render(spec, [{"t": 1}])
    return ('<figure class="step-fig wide" role="img" aria-label="%s"><div class="snap-wide">%s</div>'
            '<div class="snap-phone">%s</div><figcaption class="dim"><b>%s.</b> %s</figcaption></figure>'
            % (E(spec["title"]), snaps["wide"][0], snaps["phone"][0], E(spec["title"]), caption))


def chart_delay(P, v):
    m = P["delay"]["mars"]
    spec = {"id": "sd-delay", "type": "series",
            "title": "One-way signal time from Earth to Mars, minutes, 2033 to mid-2036",
            "x": m["x"], "y": {"label": "minutes", "max": 25},
            "series": [{"key": "lt", "label": "Light time, Earth to Mars", "color": "acc", "values": m["min"]}],
            "annotations": [{"at": 2034.63, "text": "Sun between", "short": "Sun"},
                            {"at": 2035.69, "text": "closest", "short": "near"}]}
    return static_chart(spec, f"The delay swings from {v['lo_min']} minutes on {day(m['lo']['date'])} to "
                              f"{v['hi_min']} minutes on {day(m['hi']['date'])}, when Mars is nearly behind the Sun. "
                              f"A question and its answer take from about {v['rt_lo']} minutes to "
                              f"{v['rt_hi']}, against about {v['moon_rt']} seconds for the Moon. Data: JPL Horizons, "
                              f"one-way light time from Earth's centre, daily (plotted weekly), computed "
                              f"{v['hz_date']}.")


def table_rating(P):
    f = P["facts"]
    rows = [("Earth orbit", "under 30 days", f["rr_leo_short"]),
            ("Earth orbit", "30 days to 1 year", f["rr_leo_long"]),
            ("Mars, preparatory", "under 1 year", f["rr_mars_prep"]),
            ("Mars, planetary", "730 to 1,224 days", f["rr_mars_plan"])]
    body = "".join(f'<tr><td>{a}</td><td>{b}</td><td class="n">{c.replace("x", " &times; ")}</td></tr>'
                   for a, b, c in rows)
    return ('<figure class="rating"><table><thead><tr><th>Mission</th><th>Length</th>'
            '<th class="n">Likelihood &times; consequence</th></tr></thead><tbody>' + body +
            '</tbody></table><figcaption class="dim">NASA\'s rating of the risk of adverse cognitive or behavioural '
            'conditions and psychiatric disorders during the mission, July 2024 board decision. Each factor runs '
            'from 1 to 5. Data: NASA Human System Risk Board, Behavioral Health risk record, Rev D.1.'
            '</figcaption></figure>')


# ---------------------------------------------------------------- claims ---
def claims(P, v):
    S, f, D, C = P["stats"], P["facts"], P["delay"], P["mars_crew"]
    c = [
        ("'less than half of NASA's reference mission'", S["longest"]["days"] < f["dra_916"] / 2),
        ("'most trips are short': over half under 30 days", S["share_under_30"] > 0.5),
        ("'the longest ... on the Mir station from 1994'", S["longest"]["mission"] == "Soyuz TM-18"),
        ("'two to three years away': DRA long stay 890-950 d", 2 * YEAR < int(f["dra_long"][0]) < 3 * YEAR
         and int(f["dra_long"][1]) < 3 * YEAR),
        ("'about {x_min} times': 12-14", 12 <= C["x_moon_min"] <= 14),
        ("Moon flights 'under two weeks'", S["moon_max_days"] < 14),
        ("'most of the dots sit between a few days and two weeks': half the flights 3-14 d",
         sum(3 <= d[0] <= 14 for d in P["dots"]) > len(P["dots"]) / 2),
        ("'all of them in Earth orbit': no Moon flight over 180 d", S["moon_max_days"] < 180),
        ("Mars delay 'up to {hi_min} minutes' is the maximum", abs(D["mars"]["hi"]["min"] - float(v["hi_min"])) < 0.5),
        ("'no fewer than four crew members' and the calculation uses four", C["crew_min"] == 4),
        ("Mars-500 conflict ratio is 'five'", f["m500_ctrl_x"] == "five"),
        ("'blackouts that can last weeks'", bool(f["comm_blackout"])),
        ("'Both kinds of Mars mission score' the same", f["rr_mars_prep"] == f["rr_mars_plan"]),
        ("'about 16 episodes': 0.074 x person-years rounds to 14-18", 14 <= f["nsduh_mde"] / 100 * S["py_total"] <= 18),
    ]
    bad = [n for n, ok in c if not ok]
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    S, f, D, C = P["stats"], P["facts"], P["delay"], P["mars_crew"]
    kus, kru = {"five": 5, "eight": 8}[f["kanas01_us"][0]], {"five": 5, "eight": 8}[f["kanas01_us"][1]]
    P["n_measured"] = kus + kru + f["kanas07_n"]
    words = {5: "five", 8: "eight"}
    lo, hi = D["mars"]["lo"]["min"], D["mars"]["hi"]["min"]
    v = {
        "n_measured": str(P["n_measured"]),
        "first_year": str(S["first_year"]), "through_y": P["through"][:4],
        "n_people": num(S["n_people"]), "n_rides": num(S["n_rides"]), "n_orbit": num(S["n_orbit"]),
        "py_total": num(S["py_total"]), "pct_under30": num(100 * S["share_under_30"]),
        "n_gt180": str(S["n_gt180"]), "n_ge365": {9: "nine"}.get(S["n_ge365"], str(S["n_ge365"])),
        "longest_name": S["longest"]["name"].split()[0] + " " + S["longest"]["name"].split()[-1],
        "longest_year": str(S["longest"]["year"]), "longest_days": num(S["longest"]["days"], 0),
        "kanas_us": words[kus], "kanas_ru": words[kru], "kanas07": str(f["kanas07_n"]),
        "iss_n": {9: "nine"}.get(f["er_iss_n"], str(f["er_iss_n"])), "iss_rate": f"{f['er_iss_rate']:.2f}",
        "nodx_year": str(f["er_nodx"]),
        "barger_h": f"{f['barger_iss_h']:.2f}", "barger_hyp": str(f["barger_hyp"]),
        "m500_days": str(f["m500_days"]), "m500_pct": str(f["m500_weeks_pct"]), "m500_ctrl": f["m500_ctrl_x"],
        "m500_period": f"{f['m500_period']:.2f}",
        "pal_n": str(int(f["pal_men"][0]) + int(f["pal_men"][1])), "pal_any": f"{f['pal_any']:.1f}",
        "pal_w": f"{f['pal_weighted']:.1f}",
        "bell_n": str(f["bell_n"]), "sandal_n": f["sandal_n"][0], "sandal_mo": f["sandal_n"][1],
        "q_hib": f["sandal_hib"],
        "dra_s1": f["dra_short"][0], "dra_s2": f["dra_short"][1], "dra_l1": f["dra_long"][0],
        "dra_l2": f["dra_long"][1], "dra_916": str(f["dra_916"]),
        "lo_min": f"{lo:.1f}", "hi_min": f"{hi:.0f}",
        "rt_lo": f"{2 * lo:.0f}", "rt_hi": f"{2 * hi:.0f}",
        "moon_s": f"{(D['moon']['lo_s'] + D['moon']['hi_s']) / 2:.1f}",
        "moon_rt": f"{D['moon']['lo_s'] + D['moon']['hi_s']:.1f}".rstrip("0").rstrip("."),
        "n_people_moon": str(S["n_people_moon"]), "n_moon": str(S["n_moon"]),
        "moon_pd": num(S["py_moon"] * YEAR, 0), "py_moon": f"{S['py_moon']:.2f}",
        "crew_pd": num(C["crew_min"] * C["mission_days"]), "py_min": f"{C['py_min']:.1f}",
        "x_min": f"{C['x_moon_min']:.0f}",
        "rr_leo_long": f["rr_leo_long"].replace("x", " &times; "), "rr_mars": f["rr_mars_plan"].replace("x", " &times; "),
        "q_underest": f["rr_underest"],
        "nsduh": f"{f['nsduh_mde']:.1f}", "expected": f"{f['nsduh_mde'] / 100 * S['py_total']:.0f}",
        "ihle_sent": f["ihle"][0], "ihle_back": f["ihle"][1],
        "ihle_pct": f"{100 * int(f['ihle'][1]) / int(f['ihle'][0]):.0f}",
        "table_date": day(S["table_date"]), "n_ongoing": str(S["n_ongoing"]),
        "hz_date": day(P["fetched"]["horizons_mars.txt"]["fetched"]),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    v["stamp"] = insight.stamp(through=P["through"], live=False)
    v["takeaways"] = insight.takeaways([
        f"The only validated mood scores taken in flight cover about {v['n_measured']} people, all in Earth orbit, "
        f"and none of those studies found mood falling late in a mission.",
        f"All human time beyond Earth orbit adds up to {v['py_moon']} person-years; a single four-person Mars "
        f"mission would log about {v['py_min']}, with messages taking up to {v['hi_min']} minutes each way.",
        "NASA rates the Mars risk red from ground rehearsals and an event rate it calls an underestimate, so the "
        "first Mars crew will produce the first real data."])
    claims(P, v)
    v["hero"] = hero(P, v)
    v["chart_delay"] = chart_delay(P, v)
    v["table_rating"] = table_rating(P)
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
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("space-depression.html")
    if not refs:
        return text, ["space-depression.html has no entry in add_citations.PAGES"]
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
        print("  space-depression.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  space-depression.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
