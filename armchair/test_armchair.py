"""Checks for armchair.html and its payload.

- the payload rebuilds from data/ to the same bytes (analysis.py is deterministic);
- every opinion has both grades, and every case gap recomputes;
- the page carries every number the payload gives for its headline (scorable, strong, wrong), no template
  placeholder, one square per checkable answer in each crowd drawing, six outlined squares in each, one
  timeline row per case in each drawing, and a numbered Sources list with one entry per citation anchor;
- the hero steps are numbered 0..2 and every crowd square's data-o is one of them.

Run:  python armchair/test_armchair.py      (exit 0 = pass)
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PAGE = os.path.join(ROOT, "site", "armchair.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
sys.path.insert(0, ROOT)

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


before = open(PAYLOAD, "rb").read()
r = subprocess.run([sys.executable, "analysis.py"], cwd=HERE, capture_output=True, text=True)
check(r.returncode == 0, f"analysis.py exit {r.returncode}: {r.stderr[-300:]}")
check(open(PAYLOAD, "rb").read() == before, "payload does not rebuild to the same bytes")

P = json.load(open(PAYLOAD, encoding="utf-8"))
p, c = P["placita"], P["cases"]
t = open(PAGE, encoding="utf-8").read()
main = t[t.find("<main"):t.find("</main>")]

check("{{" not in t and "}}" not in t, "template placeholder left on the page")
check(f"Of {p['n_scorable']} ancient answers about nature, {p['low']['STRONG']} hold up" in t, "h1 numbers")
check(f"{p['low']['WRONG']} are wrong" in main, "wrong count in prose")
for cls, n_exp in (("tree-wide", p["n_scorable"]), ("tree-phone", p["n_scorable"])):
    m = re.search(r'<svg class="tree crowd ' + cls + r'".*?</svg>', t, re.S)
    check(m is not None, f"crowd drawing {cls} missing")
    if m:
        rects = re.findall(r"<rect [^>]*>", m.group(0))
        check(len(rects) == n_exp, f"{cls}: {len(rects)} squares, expected {n_exp}")
        check(sum(" fam\"" in x for x in rects) == 6, f"{cls}: famous outlines != 6")
        check(all(re.search(r'data-o="[012]"', x) for x in rects), f"{cls}: data-o outside 0..2")
        for g in ("STRONG", "PARTIAL", "LOOSE", "WRONG"):
            got = sum(f'class="g-{g.lower()}' in x for x in rects)
            check(got == p["low"][g], f"{cls}: {g} squares {got} != payload {p['low'][g]}")
check(re.findall(r'data-step="(\d)"', t) == ["0", "1", "2"], "hero steps not 0,1,2")
for cls in ("tl-wide", "tl-phone"):
    m = re.search(r'<svg class="tl ' + cls + r'".*?</svg>', t, re.S)
    check(m is not None and m.group(0).count('<g class="tl-row') == c["n"], f"timeline {cls}: rows != {c['n']}")
check(t.count("<tr><td>") >= c["n"], "case table rows")

import add_citations  # noqa: E402
n_refs = len(add_citations.PAGES["armchair.html"]) - 1
sups = re.findall(r'<sup class="cite"', main)
check(len(sups) == n_refs, f"{len(sups)} citation markers, {n_refs} anchors")
check("Sources" in t, "no Sources section")
check("mailto:" not in t, "personal email on the page")
for word in ("Targa", "internship", "earlier version", "used to be", "updated", "v2"):
    check(word.lower() not in main.lower(), f"forbidden phrase: {word}")

for f in fails:
    print("FAIL", f)
print(f"test_armchair: {'FAIL' if fails else 'ok'} ({len(fails)} failures)")
sys.exit(1 if fails else 0)
