"""
Tests for the climate-effort page (site/dissonance.html) and its build.

Each guard is tested by feeding it an input that must fail, not only by watching it pass: the review
check is given a wrong printed median, the template claims are given a payload where recycling saves the
most, and the page checks read the shipped page.

Run:  python dissonance/test_dissonance.py
"""
import copy
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import build_dissonance as B   # noqa: E402
import update_page as U        # noqa: E402

PAGE = os.path.join(ROOT, "site", "dissonance.html")
results = []


def say(ok, what):
    results.append(ok)
    print(("  ok   " if ok else "  FAIL ") + what)


def raises(fn):
    try:
        fn()
    except SystemExit:
        return True
    return False


def main():
    P = B.build()
    shipped = json.load(open(B.OUT, encoding="utf-8"))
    say(json.loads(json.dumps(P)) == shipped, "build: payload.json is what build_dissonance.py makes from data/")

    si = B.load_iva()
    say(B.check_paper(si) == len(B.PAPER), f"review: {len(B.PAPER)} printed medians and means reproduced")
    keep = list(B.PAPER)
    B.PAPER.append(("Transport", "Live car-free", "median", 2.4))
    say(raises(lambda: B.check_paper(si)), "review: a printed value of 2.4 for car-free (computed 2.07) stops the build")
    B.PAPER[:] = keep

    # the survey shares: every unrounded share rounds to the published whole percent
    bad = [r["code"] for r in P["items"] if abs(r["pct_calc"] - r["pct"]) > 0.5 + 1e-9]
    say(not bad, f"survey: 14 unrounded shares round to the published percent{' - ' + str(bad) if bad else ''}")
    say(len({r["code"] for r in P["items"]}) == 14, "survey: 14 distinct actions of the 2025 list")

    E = P["eb"]
    say(abs(E["top3_t"] - (0.21 + 0.161 + 0.0597) / 3) < 1e-4,
        f"arithmetic: mean of the three most named = {E['top3_t']:.4f} t, by hand (0.21 + 0.161 + 0.0597) / 3")
    say(abs(E["ratio"] - E["bot3_t"] / E["top3_t"]) < 1e-12, f"arithmetic: ratio {E['ratio']:.2f}")

    # claims() must stop a payload that contradicts the prose
    U.claims(P, {})
    say(True, "claims: the shipped payload satisfies every claim")
    Q = copy.deepcopy(P)
    for r in Q["items"]:
        if r["code"] == "QD6_13":
            r["t"] = 3.0
    say(raises(lambda: U.claims(Q, {})), "claims: recycling at 3 t (the largest saving) stops the generator")
    Q = copy.deepcopy(P)
    Q["eb"]["top3"] = ["QD6_13", "QD6_6", "QD6_14"]
    say(raises(lambda: U.claims(Q, {})), "claims: a different order of the three most named stops the generator")

    if not os.path.exists(PAGE):
        say(False, "page: site/dissonance.html exists")
        return
    t = open(PAGE, encoding="utf-8").read()
    say("{{" not in t, "page: no unfilled placeholder")
    say('"type":"rank"' in t and 'class="scrolly wide" id="dissonance-hero"' in t,
        "page: the hero is a kit rank chart")
    rows = re.findall(r"<tr><td>", t)
    say(len(rows) == 14 + 4, f"page: 14 action rows and 4 barrier rows ({len(rows)} found)")
    refs = re.findall(r'<li id="ref\d+">', t)
    cites = re.findall(r'<sup class="cite"', t)
    say(len(refs) == 14 and len(cites) == 14, f"page: 14 references, each cited once ({len(refs)}, {len(cites)})")
    body = re.sub(r"<[^>]+>", " ", t.split("<main>")[1])
    # prose only: the paragraphs between the h1 and the method, without the hero's chart (its SVG text
    # repeats every label in each step figure) and the tables
    prose = t.split("</h1>")[1].split('id="method"')[0]
    prose = re.sub(r"<(svg|script|table)\b.*?</\1>", " ", prose, flags=re.S)
    prose = " ".join(re.findall(r"<p[^>]*>(.*?)</p>", prose, flags=re.S))
    words = len(re.findall(r"[A-Za-z][A-Za-z'’-]*", re.sub(r"<[^>]+>", " ", prose)))
    say(1000 <= words <= 1800, f"page: {words} words of prose before the method (house range 1,000 to 1,800)")
    for n in [E["top3_t"], E["bot3_t"]]:
        say(f"{n:.2f}" in t, f"page: {n:.2f} t is printed")
    say("@" not in body, "page: no address in the text")

    print(f"\n{sum(results)}/{len(results)} passed")


if __name__ == "__main__":
    main()
    sys.exit(0 if all(results) else 1)
