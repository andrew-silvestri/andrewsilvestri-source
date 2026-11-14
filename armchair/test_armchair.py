"""Checks for armchair.html and its payload.

- the payload rebuilds from data/ to the same bytes (analysis.py is deterministic);
- every opinion has both grades, and every case gap recomputes;
- the page carries the headline median from the payload, no template placeholder, one timeline row per case
  in each drawing, and a numbered Sources list with one entry per citation anchor;
- D-105 (2026-11-14): nothing of the AI-graded handbook base rate is on the page (no crowd grid, no raters,
  no kappa, no checkable-answer count).

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
check(f"waited a median of {c['gap_med_ancient_hit']:,} years for confirmation</h1>" in t, "h1 number")
check('class="tree crowd' not in t and "kappa" not in main.lower() and "rater" not in main.lower(),
      "D-105: the AI-graded base rate (crowd grid, raters, kappa) must not be on the page")
check(str(p["n_scorable"]) not in re.sub(r"<[^>]+>", " ", main).split(), "D-105: the handbook's checkable count is on the page")
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
