"""
Tests for site/lowcarbon-shoe.html. Each check recomputes from the shipped code
and inputs, never from the payload under test (trap 20), and each has a --break
that must make the suite exit 1 (traps 17, 26).

 1 lca       the LCA's central case, re-run from lca/*.py, equals the payload's totals and reductions
 2 groups    the hero's six groups sum to each shoe's total, per state
 3 hero      the hero's state table in the page equals hero.py recomputed from a fresh build
 4 numbers   the takeaways' and standfirst's numbers equal values recomputed from the LCA
 5 page      update_page.render + cite reproduces the shipped page byte for byte
 6 simulated every 'tested' on the page is a test by simulation; the page never claims a physical test
 7 register  no 'sustainable', 'carbon neutral', 'eco-friendly', 'green shoe', 'boom', 'crisis'
 8 names     no brand or company name, and not the internship employer (by SHA-1 of its name)
 9 fit       every SVG label fits its figure at 12 px Plex Mono (7.2 px a character)
10 lf        every text file in this folder uses LF line endings

Run:  python test_lowcarbon_shoe.py [--break lca|groups|hero|numbers|page|simulated|register|names|fit|lf]
"""
import hashlib
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "lca"))
BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
PAGE = os.path.join(ROOT, "site", "lowcarbon-shoe.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
fails = []
NAMES = ["Nike", "Adidas", "adidas", "ASICS", "Asics", "Allbirds", "Salomon", "Brooks", "Hoka", "Vibram", "BASF",
         "Covestro", "Lubrizol", "Huntsman", "Braskem", "Arkema", "Reebok", "Boost", "Infinergy", "On Cyclon"]
# The internship employer, by the SHA-1 of its lower-cased name (the same digest as ethane/test_ethane.py).
EMPLOYER_SHA1 = "c0446e86c1b75316d035502707018d75dd2fc688"
REGISTER = ["sustainable", "carbon neutral", "carbon-neutral", "eco-friendly", "green shoe", "boom", "crisis", "glut"]


def check(name, ok, detail):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def raw_page():
    return open(PAGE, "rb").read().decode("utf-8")


def page_text(t=None, refs=True):
    """Visible prose. refs=False drops the generated Sources list, whose titles
    (an EPA report, a case study of one brand's scheme) are the sources' own words."""
    t = raw_page() if t is None else t
    if not refs:
        t = re.sub(r'<ol class="refs">.*?</ol>', " ", t, flags=re.S)
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", t, flags=re.S)
    t = re.sub(r'<sup class="cite".*?</sup>', "", t, flags=re.S)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))


def main():
    import lca
    import build_lowcarbon_shoe as B
    import hero as H
    import update_page as UP
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    T = page_text()
    raw = raw_page()
    # 1 lca -------------------------------------------------------------------------
    x, vol = lca.central(), lca.load_volumes()
    if BREAK == "lca":
        x["F.TPU"] *= 1.2
    r = lca.evaluate(x, vol, upper_lives=1, clean_lc1=True)
    rd = lca.evaluate(x, vol, upper_lives=1, clean_lc1=False)
    ok = (abs(r["baseline"]["total"] - P["pair"]["baseline"]) < 2e-3 and abs(r["lc1"]["total"] - P["pair"]["lc1"]) < 2e-3
          and abs(r["reduction_pct"] - P["scenarios"]["lc1"]) < 0.06 and abs(rd["reduction_pct"] - P["scenarios"]["design_only"]) < 0.06)
    check("1 lca", ok, f"re-run {r['baseline']['total']:.3f} / {r['lc1']['total']:.3f} kg, {r['reduction_pct']:.1f} % / "
          f"{rd['reduction_pct']:.1f} %; payload {P['pair']['baseline']} / {P['pair']['lc1']} kg, {P['scenarios']['lc1']} / {P['scenarios']['design_only']} %")
    # 2 groups ----------------------------------------------------------------------
    fresh = B.build()
    if BREAK == "groups":
        fresh["groups"]["lc1"]["mid"] += 0.2
    bad = [k for k in ("baseline", "lc1_design_only", "lc1") if abs(sum(fresh["groups"][k].values()) - fresh["pair"][k]) > 0.01]
    check("2 groups", not bad, "hero groups sum to each pair total" + (f"; not for {bad}" if bad else ""))
    # 3 hero ------------------------------------------------------------------------
    spec = json.loads(re.search(r'<script type="application/json" class="shoe-spec">(.*?)</script>', raw, flags=re.S)
                      .group(1).replace("<\\/", "</"))
    want = {f: H.states_json(fresh, f)["states"] for f in ("wide", "phone")}
    if BREAK == "hero":
        want["wide"][4]["bmid"]["width"] += 5
    check("3 hero", all(spec[f]["states"] == want[f] for f in want), "the page's state table equals hero.py on a fresh build")
    # 4 numbers ---------------------------------------------------------------------
    st = r["baseline"]["stages"]
    fac = round(100 * (st["part_making"] + st["assembly"]) / r["baseline"]["total"])
    red = round(rd["reduction_pct"]) if BREAK != "numbers" else round(rd["reduction_pct"]) + 1
    rb = lca.evaluate(x, vol, upper_lives=1, clean_lc1=True, clean_base=True)
    bc = round(100 * (1 - rb["baseline"]["total"] / r["baseline"]["total"]))
    phrases = [f"{fac} percent of it is factory energy", f"the LC-1 redesign alone cuts {red} percent",
               f"cuts that by {bc} percent", f"emits {r['baseline']['total']:.1f} kg of greenhouse gas per pair",
               f"a cut of just over half ({round(r['reduction_pct'])} percent in the central case)"]
    miss = [p for p in phrases if p not in T]
    check("4 numbers", not miss, "takeaways and standfirst carry the re-run numbers" + (f"; missing {miss}" if miss else ""))
    # 5 page ------------------------------------------------------------------------
    out, probs = UP.cite(UP.render(P))
    if BREAK == "page":
        out = out.replace("LC-1", "LC-2", 1)
    check("5 page", out == raw and not probs, "render + cite == shipped page" + (f"; problems {probs}" if probs else ""))
    # 6 simulated -------------------------------------------------------------------
    t6 = T + (" The shoe was tested on a track." if BREAK == "simulated" else "")
    loose = [m.start() for m in re.finditer(r"\btested\b", t6) if "simulat" not in t6[max(0, m.start() - 60): m.start() + 60]]
    phys = re.search(r"\b(lab|field|wear)[- ]tested\b|we tested|was tested on", t6, flags=re.I)
    check("6 simulated", not loose and not phys, "every 'tested' is by simulation" + (f"; {len(loose)} loose" if loose else ""))
    # 7 register --------------------------------------------------------------------
    T0 = page_text(refs=False)
    t7 = (T0 + (" a sustainable shoe" if BREAK == "register" else "")).lower()
    hit = [w for w in REGISTER if w in t7]
    check("7 register", not hit, "no marketing or alarm words" + (f"; found {hit}" if hit else ""))
    # 8 names -----------------------------------------------------------------------
    t8 = T0 + (" a midsole like Boost" if BREAK == "names" else "")
    words = set(re.findall(r"[A-Za-z][A-Za-z\-]+(?: [A-Z][A-Za-z]+)?", t8))
    hit = [n for n in NAMES if re.search(r"(?<![A-Za-z])" + re.escape(n) + r"(?![A-Za-z])", t8)]
    emp = [w for w in words if hashlib.sha1(w.lower().encode()).hexdigest() == EMPLOYER_SHA1
           or hashlib.sha1(w.split()[0].lower().encode()).hexdigest() == EMPLOYER_SHA1]
    check("8 names", not hit and not emp, "no brand, company or employer name in the prose (Sources excepted)" + (f"; {hit}" if hit else ""))
    # 9 fit -------------------------------------------------------------------------
    over = []
    for svg in re.findall(r"<svg class=\"chart\".*?</svg>", raw, flags=re.S):
        W = float(re.search(r'viewBox="0 0 ([\d.]+) ', svg).group(1))
        for m in re.finditer(r'<text[^>]*x="([\d.]+)"[^>]*>([^<]*)</text>', svg):
            n = len(html.unescape(m.group(2))) + (40 if BREAK == "fit" else 0)
            if float(m.group(1)) + 7.2 * n > W:
                over.append(html.unescape(m.group(2)))
    check("9 fit", not over, "every label fits its figure" + (f"; over: {over[:3]}" if over else ""))
    # 10 lf -------------------------------------------------------------------------
    crlf = []
    for dp, dn, fn in os.walk(HERE):
        if "__pycache__" in dp:
            continue
        for f in fn:
            if os.path.splitext(f)[1].lower() in (".py", ".md", ".json", ".csv", ".html", ".svg", ".dxf", ".step", ".txt"):
                b = open(os.path.join(dp, f), "rb").read()
                if b"\r\n" in b:
                    crlf.append(f)
    if BREAK == "lf":
        crlf.append("(break)")
    check("10 lf", not crlf, "LF only" + (f"; CRLF in {crlf[:5]}" if crlf else ""))
    print(f"{len(fails)} failure(s)" + (f" (--break {BREAK})" if BREAK else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
