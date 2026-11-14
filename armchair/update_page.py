"""
Write site/armchair.html from template.html and outputs/payload.json (analysis.py builds the payload).

Every number on the page comes from the payload; the prose is in the template. The parts other scripts own -
the nav (rebuild_nav.py), the citation markers and Sources list (add_citations.py's table, applied here) and
the ?v= stamps (bust_cache.py) - are kept as the shipped page has them, so tests/test_generators.py can run
this on the shipped tree and expect no change. The idiom is oxygen/update_page.py's.

The hero is the timeline, a static drawing: one line per case from the year of the idea to the year of the
event, drawn twice (900px and 340px). D-105 (2026-11-14): the page no longer shows the AI-graded base rate of
the Placita (the crowd grid, its counts and the rater agreement); analysis.py still builds that part of the
payload, and the download keeps it, but nothing on the page reads it.

claims() asserts every ordering the template's words commit to; if a rebuild moves one, the generator stops.

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
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}


def year(y):
    return f"{-y} BCE" if y < 0 else f"AD {y}" if y < 1000 else str(y)


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
    c = P["cases"]
    rows = {r["id"]: r for r in c["rows"]}
    v = {
        "c_n": str(c["n"]), "c_s": WORDS.get(c["tally"]["STRONG"], str(c["tally"]["STRONG"])),
        "c_p": str(c["tally"]["PARTIAL"]), "c_l": str(c["tally"]["LOOSE"]), "c_w": str(c["tally"]["WRONG"]),
        "gap_anc": f"{c['gap_med_ancient_hit']:,.0f}", "gap_mod": f"{c['gap_med_modern_hit']:,.0f}",
        "gap_modmiss": f"{c['gap_med_modern_miss']:,.0f}",
        "gap_kant": str(rows["E10"]["gap"]), "gap_epr": str(rows["R09"]["gap"]),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    v["stamp"] = insight.stamp(live=False)
    v["takeaways"] = insight.takeaways([
        f"Followed from the year each was written to the dated event that settled it, right guesses about "
        f"nature from antiquity waited a median of {v['gap_anc']} years, mostly for an instrument to be built.",
        f"Among ideas from 1400 on, wrong ones were refuted in a median of {v['gap_modmiss']} years, faster than "
        f"right ones were confirmed (a median of {v['gap_mod']}).",
        f"Of the {v['c_n']} ideas, {v['c_s']} are strong matches to present science and {v['c_w']} are wrong; the "
        f"cases are the ones histories cite, so they show waiting times, not how often guesses were right."])
    claims(P, v)
    v["hero"] = timeline(P, v)
    v["cases_table"] = cases_table(P)
    return v


def claims(P, v):
    c = P["cases"]
    bad = []
    if c["gap_med_ancient_hit"] < 1000 or c["gap_med_modern_miss"] > c["gap_med_modern_hit"]:
        bad.append("ancient hits wait millennia; modern misses die faster than modern hits wait")
    if c["tally"]["WRONG"] <= c["tally"]["STRONG"]:
        bad.append("takeaway pairs strong and wrong counts; check the wording still reads right")
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
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)))
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
