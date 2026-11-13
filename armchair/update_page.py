"""
Write site/armchair.html from template.html and outputs/payload.json (analysis.py builds the payload).

Every number on the page comes from the payload; the prose is in the template. The parts other scripts own -
the nav (rebuild_nav.py), the citation markers and Sources list (add_citations.py's table, applied here) and
the ?v= stamps (bust_cache.py) - are kept as the shipped page has them, so tests/test_generators.py can run
this on the shipped tree and expect no change. The idiom is oxygen/update_page.py's.

The hero is the handbook's crowd: every checkable answer in the Placita as one square, grouped by question,
coloured by its consensus grade, drawn twice (a 900px drawing and a 320px one). Squares carry data-o: 0 for
six answers that histories of science cite, 1 for the other answers to those same six questions, 2 for the
rest. site/assets/chain.js (oxygen's, used unchanged) reveals them in that order as the step cards scroll.
The timeline is a static drawing: one line per case from the year of the idea to the year of the event.

claims() asserts every proportion the template's words commit to ("about one in", "between six and eight",
"the only one close to right"); if a rebuild moves one, the generator stops.

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
PAGE = os.path.join(SITE, "armchair.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "armchair-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import insight  # noqa: E402

E = html.escape
GRADES = ["STRONG", "PARTIAL", "LOOSE", "WRONG"]
# The six answers that popular histories cite: the Moon's borrowed light, the solar eclipse, a spherical Earth,
# the Milky Way as stars, atoms, and a moving Earth. Fixed by id; the build checks each is in the table.
FAMOUS = ["B2.28.3", "B2.24.1", "B3.10.1", "B3.1.7", "B1.3.8", "B3.13.2"]
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}


def year(y):
    return f"{-y} BCE" if y < 0 else f"AD {y}" if y < 1000 else str(y)


# ------------------------------------------------------------------ hero ---
def crowd(T, width, sq, gap, ggap, cls):
    """Squares in reading order, one group per question, a group never split across lines."""
    groups = []
    for t in T:
        if t["consensus"] is None:
            continue
        key = (t["book"], t["chapter"])
        if not groups or groups[-1][0] != key:
            groups.append((key, []))
        groups[-1][1].append(t)
    fam_q = {(t["book"], t["chapter"]) for t in T if t["id"] in FAMOUS}
    x = y = 0
    step = sq + gap
    cells = []
    for key, rows in groups:
        w = len(rows) * step - gap
        if x and x + w > width:
            x, y = 0, y + step
        for i, t in enumerate(rows):
            o = 0 if t["id"] in FAMOUS else 1 if key in fam_q else 2
            fam = " fam" if t["id"] in FAMOUS else ""
            cells.append(f'<rect class="g-{t["consensus"].lower()}{fam}" data-o="{o}" '
                         f'x="{x + i * step}" y="{y}" width="{sq}" height="{sq}"/>')
        x += w + ggap
    h = y + sq
    pad = 3
    return (f'<svg class="tree crowd {cls}" viewBox="{-pad} {-pad} {width + 2 * pad} {h + 2 * pad}" '
            f'width="{width + 2 * pad}" height="{h + 2 * pad}" role="img" aria-labelledby="crowd-desc">'
            + "".join(cells) + "</svg>")


def hero(P, v):
    T = P["placita"]["table"]
    fam = [t for t in T if t["id"] in FAMOUS]
    assert len(fam) == len(FAMOUS)
    fq = {(t["book"], t["chapter"]) for t in fam}
    riv = [t for t in T if (t["book"], t["chapter"]) in fq and t["id"] not in FAMOUS and t["consensus"]]
    riv_w = sum(t["consensus"] == "WRONG" for t in riv)
    fam_s = sum(t["consensus"] == "STRONG" for t in fam)
    v.update(fam_s=str(fam_s), riv_n=str(len(riv)), riv_w=str(riv_w))
    steps = [
        (0, "Six famous answers",
         "Six answers in this handbook appear in most histories of science: the Moon shines by the Sun's light, an "
         "eclipse of the Sun is the Moon in front of it, the Earth is a sphere, the Milky Way is many stars, matter "
         f"is atoms, and the Earth moves. Graded against present science, {WORDS.get(fam_s, fam_s)} of the six are strong; "
         "the other three are partial."),
        (1, "Their rivals",
         f"Each was one answer among several to the same question. The handbook gives {len(riv)} other checkable "
         f"answers to these six questions, and {riv_w} of them are wrong: the Moon has its own light, the Earth is a "
         "drum or a table, the Milky Way is the old path of the Sun."),
        (2, "The whole handbook",
         f"All {v['n_sc']} checkable answers to {v['q_sc']} questions. {v['s_lo']} are strong and {v['w_lo']} are "
         f"wrong. Where a question drew a strong answer, a median of {v['riv_med']} other answers stood beside it. "
         '<a href="#crowd">The count</a>'),
    ]
    desc = (f"A grid of {v['n_sc']} squares, one for each checkable answer in the Placita, grouped by question in "
            f"the handbook's order and coloured by grade: {v['s_lo']} strong, {v['p_lo']} partial, {v['l_lo']} "
            f"loose, {v['w_lo']} wrong. Six famous answers are outlined; most squares are wrong.")
    key = ('<p class="chain-key crowd-key">'
           '<span class="sw g-strong"></span>strong &middot; <span class="sw g-partial"></span>partial &middot; '
           '<span class="sw g-loose"></span>loose &middot; <span class="sw g-wrong"></span>wrong. '
           'One square is one answer; squares side by side answer the same question. Outlined: the six famous '
           'answers.</p>')
    out = ['<figure class="chain wide" aria-label="Every checkable answer in the handbook">',
           '<div class="chain-fig">', f'<p id="crowd-desc" hidden>{E(desc)}</p>',
           crowd(P["placita"]["table"], 880, 14, 3, 9, "tree-wide"),
           crowd(P["placita"]["table"], 314, 12, 2, 7, "tree-phone"),
           key, '</div>', '<div class="chain-steps">']
    for k, head, text in steps:
        out.append(f'<div class="step" data-step="{k}"><p class="ev">{head}</p><p>{text}</p></div>')
    out.append("</div>\n</figure>")
    return "\n".join(out)


# -------------------------------------------------------------- timeline ---
SHORT = {
    "A01": "Democritus: atoms", "A02": "Democritus: atoms uncuttable", "A03": "Democritus: Milky Way",
    "A04": "Epicurus: equal fall in a void", "A05": "Empedocles: light travels", "A06": "Anaxagoras: Moon's light",
    "A07": "Anaximander: Earth unsupported", "A08": "Philolaus: Earth moves", "A09": "Epicurus: nothing from nothing",
    "A10": "Lucretius: motes in a sunbeam",
    "M01": "Aristotle: heavy falls faster", "M02": "Aristotle: no void", "M03": "Aristotle: unchanging heavens",
    "M04": "Empedocles: four elements", "M05": "Thales: all is water", "M06": "Plato: elements as solids",
    "M07": "Plato: sight from the eye", "M08": "Aristotle: spontaneous generation",
    "M09": "Aristotle: eternal universe", "M10": "Zeno: paradoxes of motion", "M11": "Heraclitus: fire exchange",
    "M12": "Lucretius: the swerve", "M13": "Anaximander: humans from fish", "M14": "Empedocles: survival of fit",
    "M15": "Augustine: time created",
    "E01": "Cusa: Earth moves", "E02": "Bruno: other suns' planets", "E03": "Descartes: vortices",
    "E04": "Descartes: quantity of motion", "E05": "Leibniz: vis viva", "E06": "Leibniz: relational space",
    "E07": "Maupertuis: least action", "E08": "Leibniz: extremal paths", "E09": "Kant: nebular disc",
    "E10": "Kant: island universes", "E11": "Kant: tidal braking", "E12": "Kant: Euclid a priori",
    "E13": "Comte: stars' chemistry unknowable", "E14": "Hume: time from succession",
    "E15": "Boscovich: point atoms",
    "R01": "Poe: dark night sky", "R02": "Poe: primordial particle", "R03": "Grosseteste: point of light",
    "R04": "Nietzsche: recurrence", "R05": "Stoics: cyclic fire", "R06": "Ostwald: no atoms",
    "R07": "Mach: no atoms", "R08": "Mach: inertia from distant mass", "R09": "EPR: local realism",
    "R10": "Leibniz: indiscernibles", "R11": "Laplace: determinism", "R12": "Pius XII: creation",
}
Y0, Y1 = -600, 2030


def tl_svg(rows, W, gut, rh, cls, fs):
    """gut > 0: labels in a left gutter, right-aligned. gut == 0 (phones): each label sits above its line."""
    stacked = gut == 0
    x0, x1 = (8, W - 10) if stacked else (gut + 8, W - 10)
    top = 26

    def X(y):
        return x0 + (y - Y0) / (Y1 - Y0) * (x1 - x0)
    parts = []
    ticks = (-500, 500, 1000, 1500, 2000) if stacked else (-500, 0, 500, 1000, 1500, 2000)
    for t in ticks:
        xx = X(t)
        lab = "500 BCE" if t == -500 else "AD 1" if t == 0 else str(t)
        anchor = "start" if stacked and t == -500 else "end" if stacked and t == 2000 else "middle"
        parts.append(f'<line class="tl-grid" x1="{xx:.1f}" y1="{top - 6}" x2="{xx:.1f}" '
                     f'y2="{top + rh * len(rows)}"/><text class="tl-ax" x="{xx:.1f}" y="{top - 10}" '
                     f'text-anchor="{anchor}">{lab}</text>')
    for i, r in enumerate(rows):
        y = top + rh * i + (rh - 7 if stacked else rh / 2)
        a, b = X(r["idea_year"]), X(r["confirm_year"])
        g = r["grade"].lower()
        lab = (f'<text class="tl-lab" x="{x0}" y="{y - 9:.1f}">{E(SHORT[r["id"]])}</text>' if stacked else
               f'<text class="tl-lab" x="{gut}" y="{y + fs * 0.35:.1f}" text-anchor="end">{E(SHORT[r["id"]])}</text>')
        parts.append(
            f'<g class="tl-row g-{g}">{lab}'
            f'<line class="tl-line" x1="{a:.1f}" y1="{y:.1f}" x2="{b:.1f}" y2="{y:.1f}"/>'
            f'<circle class="tl-idea" cx="{a:.1f}" cy="{y:.1f}" r="3.5"/>'
            f'<rect class="tl-end" x="{b - 3.5:.1f}" y="{y - 3.5:.1f}" width="7" height="7"/>'
            f'<title>{E(SHORT[r["id"]])}: {year(r["idea_year"])} to {year(r["confirm_year"])}, '
            f'{r["gap"]:,} years, {r["grade"].lower()}</title></g>')
    H = top + rh * len(rows) + 6
    return (f'<svg class="tl {cls}" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-labelledby="tl-desc">' + "".join(parts) + "</svg>")


def timeline(P, v):
    rows = P["cases"]["rows"]
    assert set(SHORT) == {r["id"] for r in rows}, "every case needs a short label"
    desc = (f"{v['c_n']} cases, one line each from the year of the idea (circle) to the year of the decisive "
            f"event (square), sorted by the year of the idea and coloured by grade. The ancient lines cross about "
            f"two thousand years; the lines that start after 1600 are short.")
    cap = (f"Each line runs from a philosopher's idea to the event that confirmed or refuted it. The ancient "
           f"hits waited a median of {v['gap_anc']} years; among ideas from 1400 on, wrong ones lasted a median of "
           f"{v['gap_modmiss']} and right ones waited {v['gap_mod']}.")
    return "\n".join([
        '<figure class="wide tl-fig" aria-label="From idea to decisive event">',
        f'<p id="tl-desc" hidden>{E(desc)}</p>',
        tl_svg(rows, 900, 250, 17, "tl-wide", 13), tl_svg(rows, 340, 0, 30, "tl-phone", 12),
        '<p class="chain-key crowd-key"><span class="sw g-strong"></span>strong &middot; '
        '<span class="sw g-partial"></span>partial &middot; <span class="sw g-loose"></span>loose &middot; '
        '<span class="sw g-wrong"></span>wrong. Circle: the idea. Square: the event.</p>',
        f"<figcaption>{cap}</figcaption>", "</figure>"])


def cases_table(P):
    # Open, not in a <details>: test_invariants rule 5 must reach the scroller by Tab. A figure on the wide track: tests/test_layout.js allows one left edge for main's
    # children, and a figure is a picture centred on the measure (oxygen's hero makes the same move).
    out = ['<figure class="wide cases"><figcaption>All {} cases, with the event that decided each</figcaption>'
           .format(len(P["cases"]["rows"])),
           '<p class="small dim" id="cases-cue">On a narrow screen the table scrolls sideways.</p>'
           '<table tabindex="0" data-scroll-affordance="#cases-cue" aria-label="All cases"><thead><tr><th>Idea</th><th class="n">Year</th><th>Decisive event</th><th class="n">Year</th>'
           '<th class="n">Gap, years</th><th>Grade</th></tr></thead><tbody>']
    for r in P["cases"]["rows"]:
        out.append(f'<tr><td>{E(r["thinker"])}: {E(r["claim"])}</td><td class="n">{year(r["idea_year"])}</td>'
                   f'<td>{E(r["confirm_event"])}</td><td class="n">{year(r["confirm_year"])}</td>'
                   f'<td class="n">{r["gap"]:,}</td><td>{r["grade"].lower()}</td></tr>')
    out.append("</tbody></table></figure>")
    return "\n".join(out)


# ---------------------------------------------------------------- values ---
def pct(a, b):
    return f"{100 * a / b:.0f}"


def values(P):
    p, c = P["placita"], P["cases"]
    lo, hi = p["low"], p["high"]
    T = p["table"]
    rec = p["record"]
    rows = {r["id"]: r for r in c["rows"]}
    mw = [t for t in T if (t["book"], t["chapter"]) == (3, 1) and t["consensus"]]
    v = {
        "n_op": str(p["n_opinions"]), "n_ch": str(p["n_chapters"]), "n_sc": str(p["n_scorable"]),
        "s_lo": str(lo["STRONG"]), "p_lo": str(lo["PARTIAL"]), "l_lo": str(lo["LOOSE"]), "w_lo": str(lo["WRONG"]),
        "s_hi": str(hi["STRONG"]), "w_hi": str(hi["WRONG"]),
        "s_lo_pct": pct(lo["STRONG"], p["n_scorable"]), "w_lo_pct": pct(lo["WRONG"], p["n_scorable"]),
        "one_in": str(round(p["n_scorable"] / lo["STRONG"])),
        "ratio_lo": WORDS[round(lo["WRONG"] / lo["STRONG"])], "ratio_hi": WORDS[round(hi["WRONG"] / hi["STRONG"])],
        "agree5": f"{100 * p['agree5']:.0f}", "kappa5": f"{p['kappa5']:.2f}", "kappa2": f"{p['kappa2']:.2f}",
        "agree2": f"{100 * p['agree2']:.0f}",
        "q_sc": str(p["q_scorable"]), "q_all_wrong": str(p["q_all_wrong"]),
        "q_hit": str(p["q_with_strong"]), "q_rival": str(p["q_strong_with_rival"]),
        "riv_med": WORDS.get(int(p["rivals_median"]), str(p["rivals_median"])),
        "s_book2": str(p["by_book"]["2"]["STRONG"]),
        "dem_n": str(rec["Democritus"]["n"]), "dem_s": WORDS[rec["Democritus"]["STRONG"]],
        "dem_p": str(rec["Democritus"]["PARTIAL"]), "dem_w": str(rec["Democritus"]["WRONG"]),
        "sto_n": str(rec["the Stoics"]["n"]), "sto_s": str(rec["the Stoics"]["STRONG"]),
        "sto_w": str(rec["the Stoics"]["WRONG"]),
        "mw_n": WORDS.get(len(mw), str(len(mw))),
        "c_n": str(c["n"]), "c_s": WORDS.get(c["tally"]["STRONG"], str(c["tally"]["STRONG"])),
        "c_p": str(c["tally"]["PARTIAL"]), "c_l": str(c["tally"]["LOOSE"]), "c_w": str(c["tally"]["WRONG"]),
        "gap_anc": f"{c['gap_med_ancient_hit']:,.0f}", "gap_mod": f"{c['gap_med_modern_hit']:,.0f}",
        "gap_modmiss": f"{c['gap_med_modern_miss']:,.0f}",
        "gap_kant": str(rows["E10"]["gap"]), "gap_epr": str(rows["R09"]["gap"]),
        "line_a": f"{min(t['line_start'] for t in T):,}", "line_b": f"{max(t['line_end'] for t in T):,}",
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    v["stamp"] = insight.stamp(live=False)
    v["takeaways"] = insight.takeaways([
        f"An ancient handbook lists the philosophers' answers to {v['q_sc']} checkable questions about nature; "
        f"graded against present science, {v['s_lo']} of its {v['n_sc']} checkable answers hold up in full and "
        f"{v['w_lo']} are wrong.",
        f"The famous anticipations are real, but they seldom stood alone: of the {v['q_hit']} questions that drew a "
        f"strong answer, {v['q_rival']} list rival answers beside it, a median of {v['riv_med']}.",
        f"Ancient hits waited a median of {v['gap_anc']} years for confirmation; among ideas from 1400 on, wrong "
        f"ones were refuted in a median of {v['gap_modmiss']} years, faster than right ones were confirmed (a median "
        f"of {v['gap_mod']})."])
    claims(P, v, mw)
    v["hero"] = hero(P, v)
    v["timeline"] = timeline(P, v)
    v["cases_table"] = cases_table(P)
    return v


def claims(P, v, mw):
    p, c = P["placita"], P["cases"]
    lo, hi = p["low"], p["high"]
    bad = []
    if not 2 <= round(hi["WRONG"] / hi["STRONG"]) < round(lo["WRONG"] / lo["STRONG"]) <= 9:
        bad.append("'between {ratio_hi} and {ratio_lo} wrong ones' per strong answer (rounded, distinct)")
    if not hi["STRONG"] > lo["STRONG"] and hi["WRONG"] < lo["WRONG"]:
        bad.append("'strong answers rise ... wrong ones fall'")
    if p["by_book"]["2"]["STRONG"] * 2 <= lo["STRONG"]:
        bad.append("most strong answers in the book on the heavens")
    mwg = {t["id"]: t["consensus"] for t in mw}
    if mwg.get("B3.1.7") != "PARTIAL" or any(g != "WRONG" for i, g in mwg.items() if i != "B3.1.7"):
        bad.append("Milky Way: Democritus's is the only one close to right")
    rec = p["record"]
    if max(rec, key=lambda k: rec[k]["STRONG"]) != "the Stoics":
        bad.append("Stoics have the most strong answers")
    if rec["Democritus"]["STRONG"] != 1:
        bad.append("Democritus: 'one strong'")
    if c["gap_med_ancient_hit"] < 1000 or c["gap_med_modern_miss"] > c["gap_med_modern_hit"]:
        bad.append("ancient hits wait millennia; modern misses die faster than modern hits wait")
    if bad:
        raise SystemExit("prose contradicted by payload: " + "; ".join(bad))


# ------------------------------------------------------------- assembly ---
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
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)) - {"fam_s", "riv_n", "riv_w", "riv_med", "q_hit", "q_rival"})
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("armchair.html")
    if not refs:
        return text, ["armchair.html has no entry in add_citations.PAGES"]
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
        print("  armchair.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  armchair.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
