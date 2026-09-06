"""
Write site/shoes.html from template.html and outputs/shoes_payload.json.

Every number on the page comes from the payload; the prose is in the template.
The page that ships also carries things other scripts own - the nav
(rebuild_nav.py), the citation markers and Sources list (add_citations.py), the
?v= cache stamps (bust_cache.py) and the image dimensions (sync_img_dims.py) -
so this keeps each of those as the shipped page has it, and the drift check
(tests/test_generators.py) can run it on the shipped tree and expect no change.

The shape is food/update_page.py's, which is the newest project on the site and
the one that already solved this.

Run:  python3 update_page.py            report only
      python3 update_page.py --apply
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "shoes.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "shoes_payload.json")
ZIP = os.path.join(SITE, "downloads", "shoes-code.zip")
sys.path.insert(0, ROOT)


def values(P):
    s = P["spread"]
    ind = P["individual"]
    tr = P["transfer"]
    pred = P["predicted"]
    lim = P["limits"]
    aft = P["aft"]

    trail = next(a for a in aft if a["outdoor"])
    proto = next(a for a in aft if a["key"] == "hoogkamer2018_proto_vs_streak")
    alt = sorted((m for m in P["contradiction"]),
                 key=lambda m: abs(m["effect_pct"]))
    mass_ci = tr["metabolic_ci"]
    zip_kb = round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0

    return {
        "n_aft": s["n"], "lo": f"{s['lo']:.1f}", "hi": f"{s['hi']:.1f}",
        "ratio": f"{s['ratio']:.1f}", "median": f"{s['median']:.1f}",
        "n_with_sd": s["n_with_sd"], "n_without": s["n_without"],
        "widest": f"{ind['widest']:.1f}", "n_ind": ind["n"],
        "n_span": ind["n_spanning_zero"],
        "trail": f"{trail['effect_pct']:.1f}",
        "trail_speed": f"{trail['speed_kmh']:.1f}",
        "proto_speed": f"{proto['speed_kmh']:.0f}",
        "transfer": f"{tr['value']:.2f}",
        "transfer_lo": f"{tr['lo']:.2f}", "transfer_hi": f"{tr['hi']:.2f}",
        "mass_rule": f"{abs(tr['metabolic']):.2f}",
        "time_rule": f"{abs(tr['time']):.2f}",
        "mass_ci": f"{abs(mass_ci[1]):.2f} to {abs(mass_ci[0]):.2f}",
        "mass_alt_lo": f"{abs(alt[0]['effect_pct']):.2f}",
        "mass_alt_hi": f"{abs(alt[1]['effect_pct']):.2f}",
        "mass_ratio_lo": f"{alt[0]['ratio_to_rule']:.0f}",
        "mass_ratio_hi": f"{alt[1]['ratio_to_rule']:.0f}",
        "pred_lo": f"{pred['lo']:.1f}", "pred_hi": f"{pred['hi']:.1f}",
        "race_n": 22,
        "n_rows": lim["n_rows"], "n_female": lim["n_female"],
        "n_outdoor": lim["n_outdoor"], "n_time": lim["n_time"],
        "stephen_studies": P["meta"]["stephen2025"]["studies"],
        "stephen_n": P["meta"]["stephen2025"]["n"],
        "xiao_studies": P["meta"]["xiao2025"]["studies"],
        "smd": f"{P['meta']['stephen2025']['smd']:.2f}",
        "zip_kb": zip_kb,
    }


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "heat.html"), encoding="utf-8").read()
        stamps = {}
    else:
        stamps = dict(re.findall(r'(?:href|src)="([^"?]+)\?v=([0-9a-f]+)"', shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    text = text.replace("{{nav}}", nav)

    def stamp(m):
        path = m.group(2)
        return f'{m.group(1)}="{path}?v={stamps[path]}"' if path in stamps else m.group(0)
    return re.sub(r'(href|src)="([^"?]+\.(?:css|js|png))"', stamp, text)


def image_dims(text):
    from PIL import Image

    def dims(m):
        src = m.group(1)
        w, h = Image.open(os.path.join(SITE, src)).size
        return (f'src="assets/{src.split("/", 1)[1]}{m.group(2)}" '
                f'loading="lazy" width="{w}" height="{h}"')
    return re.sub(r'src="(assets/[^"?]+)([^"]*)" loading="lazy" '
                  r'width="[^"]*" height="[^"]*"', dims, text)


def span(text):
    """The marginalia asides span the grid rows that follow them: the count of
    top-level elements in <main> after the asides, plus one."""
    main = text[text.index("<main"):text.index("</main>")]
    body = re.sub(r"<aside.*?</aside>", "", main, flags=re.S)
    body = body[body.index(">") + 1:]
    depth, n = 0, 0
    for m in re.finditer(r"<(/?)(\w+)[^>]*?>", body):
        close, tag = m.group(1), m.group(2)
        if tag in ("img", "br", "hr", "meta", "link", "input"):
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
    return t.replace("{{span}}", str(span(t)))


# Which phrase in the prose each source supports. The phrase must be unique on
# the page; add_citations numbers the markers by order of first appearance, not
# by the order here.
#
# The citation TEXT is not repeated here. It lives once, in data/studies.py,
# and reaches this through the payload. add_citations.PAGES deliberately has no
# shoes.html entry: duplicating a source string into that table is how
# heat.html's entry drifted from the page it claims to describe, which
# tests/test_generators.py now catches. This page owns its own reference list
# and borrows only add_citations' marker machinery.
ANCHORS = [
    ("study", "hoogkamer2018", "mass-matched against a racing flat",
     "The 4% figure: a prototype against two established racing shoes, mass "
     "matched, at three elite paces."),
    ("study", "joubert2026", "an advanced trail shoe at",
     "The only comparison measured outdoors, and the smallest."),
    ("study", "knopp2023", "in world-class runners",
     "Individual running-economy responses in world-class and amateur "
     "runners, and the range they span."),
    ("study", "barnes2019", "the two Barnes and Kilding rows another",
     "Per-athlete ranges in 24 highly trained runners of both sexes, "
     "including a runner the shoe made less economical."),
    ("study", "hoogkamer2016", "It was measured at",
     "The per-100 g mass effect on metabolic rate, with the only confidence "
     "interval in the table, and on 3000 m time."),
    ("study", "guinness2020", "reading shoes off public race photographs",
     "Observed marathon-time effects for men and for women, from public race "
     "results and photographs."),
    ("study", "rodrigocarranza2020", "A later trial performed the same manipulation",
     "The added-mass trial that disagrees with the per-100 g rule by six to "
     "nine times."),
    ("meta", "stephen2025", "only their interaction did",
     "Bending stiffness alone and midsole energy return alone are each "
     "non-significant; the interaction is not."),
    ("meta", "rodrigocarranza2022", "a curved plate improved economy while a flat plate did not",
     "Plate geometry, rather than the presence of carbon, is what the data "
     "separates."),
    ("meta", "ortega2021", "about 3% deterioration to about 3% improvement",
     "The range of published bending-stiffness effects, in both directions."),
    ("meta", "xiao2025", "both arrive at a standardised mean difference",
     "The second of the two meta-analyses agreeing on the pooled effect."),
    ("meta", "fuller2015", "treats shoe weight as a design constraint",
     "The association between shoe mass and metabolic cost across the earlier "
     "literature."),
]

# Sources that are not rows in the table: the regulation, and the 1984 origin
# of the mass rule, which is a book chapter and not indexed.
EXTRA = [
    ("The oldest number in this field",
     "Frederick EC, Daniels JT, Hayes JW, &ldquo;The effect of shoe weight on "
     "the aerobic demands of running&rdquo;, in <i>Current Topics in Sports "
     "Medicine</i>, Urban &amp; Schwarzenberg, 1984, 616-625.",
     "The origin of the roughly 1% per 100 g rule, measured directly by "
     "Hoogkamer and colleagues in 2016."),
    ("World Athletics publishes a list of approved shoes",
     "World Athletics, <i>Book C - C2.1A Athletic Shoe Regulations</i>, "
     "approved 2 December 2025, effective 1 January 2026; and the World "
     "Athletics approved shoe list.",
     "The stack-height and single-plate rules, and what the approved list "
     "does and does not contain."),
]


def refs_from(P):
    """The reference list, built from the payload rather than kept in a second
    table that can drift from it."""
    out = [("Anchor phrase", "Source", "What it supports")]
    for kind, key, phrase, what in ANCHORS:
        rec = P["studies"][key] if kind == "study" else P["meta"][key]
        src = rec["source"]
        doi = rec.get("doi")
        if doi:
            src += (f' <a href="https://doi.org/{doi}">doi:{doi}</a>')
        out.append((phrase, src, what))
    out.extend(EXTRA)
    return out


def cite(text, P):
    """Citation markers and the Sources list, applied to the rendered text so a
    re-run reproduces the shipped page exactly."""
    import add_citations
    tmp = PAGE + ".render.tmp"
    open(tmp, "w", encoding="utf-8").write(text)
    try:
        out, probs = add_citations.build(os.path.basename(tmp), refs_from(P))
    finally:
        os.remove(tmp)
    return (out if out is not None else text), probs


def main(apply=False):
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    t = render(P)
    t, probs = cite(t, P)
    for p in probs:
        print("  " + p)
    if os.path.exists(PAGE):
        old = open(PAGE, encoding="utf-8").read()
        print("  shoes.html: " + ("unchanged" if old == t
                                  else "would change" if not apply
                                  else "rewritten"))
    else:
        print("  shoes.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8").write(t)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
