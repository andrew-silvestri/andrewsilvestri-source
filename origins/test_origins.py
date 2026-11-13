"""
Tests for site/origins.html and its pipeline.

  1. the generator reproduces the shipped page byte for byte (no hand edits);
  2. the payload's checks pass, and the page's figures are the payload's;
  3. the hero carries the five states in both drawings, and its steps are in order;
  4. the prose keeps the house rules: no first person, no personal email, a body of 1,000-2,400 words,
     every citation anchor found, every reference numbered;
  5. the Nernst factor and the field strength are recomputed here from first principles.

Run:  python origins/test_origins.py
"""
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PAGE = os.path.join(ROOT, "site", "origins.html")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

fails = []


def check(name, ok, detail=""):
    print(("  ok    " if ok else "  FAIL  ") + name + ("" if ok else "  " + detail))
    if not ok:
        fails.append(name)


def body_text(t):
    t = t[t.index("<main"):t.index('<h2 id="method">')]
    t = re.sub(r"<script.*?</script>|<svg.*?</svg>|<figure.*?</figure>|<nav.*?</nav>", " ", t, flags=re.S)
    t = re.sub(r"<sup class=\"cite\".*?</sup>", "", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"&[a-z]+;|&#\d+;", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def main():
    r = subprocess.run([sys.executable, "update_page.py"], cwd=HERE, capture_output=True, text=True)
    check("generator reproduces the shipped page", r.returncode == 0 and "origins.html: unchanged" in r.stdout,
          r.stdout + r.stderr)

    import build_origins as B
    P = json.load(open(os.path.join(HERE, "outputs", "payload.json"), encoding="utf-8"))
    try:
        B.checks(P)
        check("payload checks", True)
    except SystemExit as e:
        check("payload checks", False, str(e))

    t = open(PAGE, encoding="utf-8").read()
    A, g = P["ashrae"], P["gradient"]
    for label, s in [("vote count", f"{A['votes']:,}"), ("buildings", str(A["buildings"])),
                     ("balance point", f"{A['cross']['t']:.1f}&nbsp;&deg;C"),
                     ("neutral slope", f"{A['slope_neut']['v']:.2f}"), ("vent median pH", f"{P['vents']['ph_med']:.1f}"),
                     ("Nernst at 25 C", f"{g['s25']:.1f} millivolts"), ("record count", f"{A['rows_raw']:,}")]:
        check(f"page prints the payload's {label} ({s})", s in t)

    # 3. hero
    for cls in ("hero-wide", "hero-phone"):
        m = re.search(r'<svg class="og %s".*?</svg>' % cls, t, re.S)
        states = re.findall(r'data-s="(\d)"', m.group(0)) if m else []
        check(f"{cls} draws states 0-4 in order", states == list("01234"), str(states))
    steps = re.findall(r'<div class="step" data-step="(\d)">', t)
    check("hero steps 0-4 in order", steps == list("01234"), str(steps))

    # 4. prose
    body = body_text(t)
    words = len(body.split())
    check("body 1,000-2,400 words (%d)" % words, 1000 <= words <= 2400)
    fp = re.findall(r"\b(I|me|my|mine|I've|I'm|we found|our analysis)\b", body)
    check("no first person", not fp, str(fp[:5]))
    check("no email address", not re.search(r"[\w.]+@[\w.]+\.\w+|mailto:", t))
    import add_citations
    refs = add_citations.PAGES["origins.html"][1:]
    n_cite = len(set(re.findall(r'<sup class="cite"[^>]*>.*?#ref(\d+)', t)))
    n_ref = len(re.findall(r'<li id="ref\d+"', t))
    check("every reference numbered (%d of %d)" % (n_ref, len(refs)), n_ref == len(refs))
    check("every reference cited in the text", n_cite == len(refs), "%d cited" % n_cite)
    check("no 'updated' or version language", not re.search(r"\b(updated|v2|version 2|new version)\b", body, re.I))

    # 5. physics
    s25 = 1000 * 8.314462618 * 298.15 * math.log(10) / 96485.33212
    check("Nernst factor at 25 C is 59.16 mV", abs(s25 - 59.16) < 0.01 and abs(g["s25"] - s25) < 0.01)
    check("150-200 mV over 5 nm is 30-40 MV/m", (P["field"]["lo_mvm"], P["field"]["hi_mvm"]) == (30, 40))

    print("\n%d failed" % len(fails) if fails else "\nall passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
