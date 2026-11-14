"""Checks for aiweb.html and its payload.

- the payload rebuilds from sources.py to the same bytes, and every figure names a known source;
- the page carries no template placeholder, the headline numbers from the payload, every future on the map in
  both drawings, both of today's markers, both strip points, one scorecard row per forecast, and a numbered
  Sources list with one citation marker per anchor in add_citations.PAGES["aiweb.html"];
- house style: no first person in the article text, "percent" not "%", no forbidden phrases.
- --break: drops one future from the payload before checking the page; must exit 1.

Run:  python aiweb/test_aiweb.py      (exit 0 = pass)
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PAGE = os.path.join(ROOT, "site", "aiweb.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
sys.path.insert(0, ROOT)
BREAK = "--break" in sys.argv

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


before = open(PAYLOAD, "rb").read()
r = subprocess.run([sys.executable, "build_aiweb.py"], cwd=HERE, capture_output=True, text=True)
check(r.returncode == 0, f"build_aiweb.py exit {r.returncode}: {r.stderr[-300:]}")
check(open(PAYLOAD, "rb").read() == before, "payload does not rebuild to the same bytes")

P = json.load(open(PAYLOAD, encoding="utf-8"))
if BREAK:
    P["scenarios"].append({"key": "ghost", "name": "Ghost future", "x": 50, "y": 50})
f = {k: v["value"] for k, v in P["fig"].items()}
check(all(v["source"] in P["refs"] for v in P["fig"].values()), "a figure names an unknown source")

t = open(PAGE, encoding="utf-8").read()
main = t[t.find("<main"):t.find("</main>")]
text = re.sub(r"<[^>]+>", " ", main[:main.find('id="code"')])

check("{{" not in t and "}}" not in t, "template placeholder left on the page")
check("<h1>People still search, but fewer of them reach the web</h1>" in t, "h1")
for k in ("gartner_drop", "pew_click_ai", "pew_click_no", "bot_share", "graphite_articles", "graphite_serp"):
    check(f" {f[k]:g} percent" in text or f"{f[k]:g} percent" in text, f"headline figure {k} not on the page")
for cls in ("m-wide", "m-phone"):
    m = re.search(r'<svg class="aimap ' + cls + r'".*?</svg>', t, re.S)
    check(m is not None, f"map {cls} missing")
    if m:
        for s in P["scenarios"]:
            check(f'class="fut f-{s["key"]}"' in m.group(0), f"{cls}: future {s['key']} not drawn")
        check(m.group(0).count("<rect x=") == 2, f"{cls}: today's two markers")
for cls in ("s-wide", "s-phone"):
    m = re.search(r'<svg class="aistrip ' + cls + r'".*?</svg>', t, re.S)
    check(m is not None and m.group(0).count('<g class="gate">') == len(P["strip"]), f"strip {cls} points")
check(t.count("<tr><td>") >= len(P["scorecard"]), "scorecard rows")

import add_citations  # noqa: E402
n_refs = len(add_citations.PAGES["aiweb.html"]) - 1
sups = re.findall(r'<sup class="cite"', main)
check(len(sups) == n_refs, f"{len(sups)} citation markers, {n_refs} anchors")
check("Sources" in t, "no Sources section")
check("mailto:" not in t, "personal email on the page")
for w in (r"\bI\b", r"\bmy\b", r"\bwe\b", r"\bour\b"):
    check(not re.search(w, text), f"first person in the article: {w}")
check(not re.search(r"\d\s?%", text), "a % sign in the prose; the house style is 'percent'")
for word in ("Targa", "internship", "earlier version", "used to be", "v2"):
    check(word.lower() not in main.lower(), f"forbidden phrase: {word}")

for x in fails:
    print("FAIL", x)
print(f"test_aiweb: {'FAIL' if fails else 'ok'} ({len(fails)} failures)")
sys.exit(1 if fails else 0)
