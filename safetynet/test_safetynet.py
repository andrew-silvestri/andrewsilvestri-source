"""The safety-net page (safetynet.html)'s own failure modes. Each check names the likeliest way the page goes
wrong unseen, and each has a --break that reproduces that fault; the run must exit 1 under it (HANDOFF traps
17, 26, 38). Checks recompute from the raw files through build_safetynet's readers, not from the payload
they are checking (trap 20).

 1. method    DOL's national recipiency for 2006 to the year before the latest reproduces from the raw files
              (ETA 5159 c21 + c22 over 52, over the CPS annual average) to 0.05 points. --break method counts
              intrastate claims (c21) alone, a misread column.
 2. last      DOL's latest-year figures, national and for every state, are the zero-October ones (12/11 of
              the eleven-month mean), and the page's are the eleven-month mean. --break last compares DOL's
              figure with the eleven-month mean, as if DOL had no error to explain.
 3. payload   The payload's series are DOL's published values before the latest year and the recomputed ones
              in it. --break payload moves Florida's 2019 value by one point.
 4. who       Job losers per 100 unemployed and claimants per 100 job losers, recomputed from the CPS files.
              --break who divides by job losers on temporary layoff instead of all job losers.
 5. low       The states under 20 in the latest year and their share of residents, recomputed with the
              Census file. --break low uses DOL's published latest-year values, which carry the October error.
 6. hero      The hero chart's national series, as shipped in the page, is the payload's. --break hero shifts
              it by one year.
 7. documents Every figure the page takes from a report or a paper is matched in that document's text.
              --break documents changes one word of the BLS release as read.
 8. page      The page equals what update_page.py renders from the payload. --break page moves the latest
              national figure by half a point.
 9. names     No e-mail address and not the internship employer, in the page or in this folder's code
              (_RULES D-43, CLAUDE.md). --break names writes an address into the text read.
10. register  None of the words the house rules exclude or that take a side ("boom", "crisis", "strain",
              "bubble", "glut", "gutted", "draconian", "handout") in the page's own words. --break register
              writes one into the text read.

Run:  python test_safetynet.py [--break method|last|payload|who|low|hero|documents|page|names|register]
"""
import glob
import hashlib
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import build_safetynet as B  # noqa: E402
import sources as S          # noqa: E402
from fetch_public import FIPS, LAST, laus_id  # noqa: E402

BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
PAGE = os.path.join(ROOT, "site", "safetynet.html")
TOL = 0.05
# The internship employer, by the SHA-1 of its lower-cased name (ethane/test_ethane.py's constant): the name
# itself may not appear anywhere in this tree, the test included.
EMPLOYER_SHA1 = "c0446e86c1b75316d035502707018d75dd2fc688"
fails = []


def check(name, ok, detail):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def raw_page():
    return open(PAGE, "rb").read().decode("utf-8")


def page_text(t):
    t = re.sub(r"<script.*?</script>|<svg.*?</svg>|<nav.*?</nav>", " ", t, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def claims_c21_only():
    import csv
    from collections import defaultdict
    p, _ = B.verified("dol_ar5159.csv")
    cw = defaultdict(float)
    with open(p, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            cw[(r["st"], int(r["rptdate"][:4]))] += float(r["c21"] or 0)
    return cw


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    A12, A13 = B.a12(), B.a13()
    cw, _ = B.claims()
    m = B.bls()
    # 1 method -------------------------------------------------------------------
    cwx = claims_c21_only() if BREAK == "method" else cw
    worst = max(abs(B.nat_rate(cwx, m, y)[0] - A12[y]) for y in range(2006, LAST))
    check("1 method", worst <= TOL, f"DOL A.12 2006-{LAST - 1} reproduced from the raw files, worst gap {worst:.3f} pt")
    # 2 last ---------------------------------------------------------------------
    z, _ = B.nat_rate(cw, m, LAST, zero_missing=BREAK != "last")
    mean11, _ = B.nat_rate(cw, m, LAST)
    st_bad = [s for s in FIPS if abs(B.st_rate(cw, m, s, LAST, zero_missing=BREAK != "last")[0] - A13[(s, LAST)]) > TOL]
    check("2 last", abs(z - A12[LAST]) <= TOL and not st_bad and abs(P["us"][str(LAST)] - mean11) < 1e-3,
          f"DOL {LAST} is the zero-October figure (US {A12[LAST]:.2f} vs {z:.2f}; states off: {st_bad[:5]}); "
          f"page uses the eleven-month mean {mean11:.2f}")
    # 3 payload ------------------------------------------------------------------
    PS = json.loads(json.dumps(P["states"]))
    if BREAK == "payload":
        PS["FL"]["2019"] += 1
    bad = [(s, y) for s in FIPS for y in range(1976, LAST) if (s, y) in A13 and abs(PS[s][str(y)] - A13[(s, y)]) > 1e-3]
    bad += [(s, LAST) for s in FIPS if abs(PS[s][str(LAST)] - B.st_rate(cw, m, s, LAST)[0]) > 1e-3]
    bad += [("US", y) for y in A12 if y < LAST and abs(P["us"][str(y)] - A12[y]) > 1e-3]
    check("3 payload", not bad, f"payload series equal DOL's published values and the {LAST} recomputation"
                                + (f"; differs at {bad[:4]}" if bad else ""))
    # 4 who ----------------------------------------------------------------------
    bad = []
    for y in range(B.CPS_FROM, LAST + 1):
        u = B.annual(m, "LNU03000000", y)[0]
        jl = B.annual(m, "LNU03023653" if BREAK == "who" else "LNU03023621", y)[0]
        c = P["composition"][str(y)]
        if abs(100 * jl / u - c["job_loser_share"]) > 0.01 or abs(P["us"][str(y)] * u / jl - c["recip_per_100_losers"]) > 0.01:
            bad.append(y)
    check("4 who", not bad, "job losers per 100 unemployed and claimants per 100 job losers, recomputed from CPS"
                            + (f"; differ in {bad[:4]}" if bad else ""))
    # 5 low ----------------------------------------------------------------------
    val = {s: (A13[(s, LAST)] if BREAK == "low" else B.st_rate(cw, m, s, LAST)[0]) for s in FIPS}
    low = sorted(s for s in FIPS if val[s] < P["low_line"])
    share = sum(P["pop"][s] for s in low) / sum(P["pop"].values())
    check("5 low", low == P["low_states"] and abs(share - P["low_pop_share"]) < 1e-4,
          f"{len(low)} states under {P['low_line']:.0f} in {LAST}, {share:.1%} of residents")
    # 6 hero ---------------------------------------------------------------------
    t = raw_page()
    spec = json.loads(re.search(r'<section class="scrolly wide" id="safetynet-hero".*?<script type="application/json" '
                                r'class="scrolly-spec">(.*?)</script>', t, flags=re.S).group(1).replace("<\\/", "</"))
    us = spec["series"][0]["values"]
    if BREAK == "hero":
        us = us[1:] + us[-1:]
    want = [round(P["us"][x], 2) for x in spec["x"]]
    check("6 hero", us == want and spec["x"][-1] == str(LAST), f"hero's national series is the payload's, {spec['x'][0]}-{spec['x'][-1]}")
    # 7 documents ----------------------------------------------------------------
    import update_page as UP
    if BREAK == "documents":
        S.flat("bls_uisup_2022.pdf")
        S._cache["bls_uisup_2022.pdf"] = S._cache["bls_uisup_2022.pdf"].replace("had applied for UI benefits after", "had sought UI benefits after")
    try:
        L = UP.lit()
        ok = True
    except SystemExit as e:
        ok, L = False, str(e)
    check("7 documents", ok, "every figure taken from a report or paper matched in its text" + ("" if ok else f": {L}"))
    S._cache.clear()
    # 8 page ---------------------------------------------------------------------
    P2 = json.loads(json.dumps(P))
    if BREAK == "page":
        P2["us"][str(LAST)] += 0.5
    try:
        r, _ = UP.cite(UP.render(P2))
        same = r == t
    except SystemExit:
        same = False
    check("8 page", same, "the page is exactly what update_page.py renders from the payload")
    # 9 names --------------------------------------------------------------------
    texts = [t] + [open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(HERE, "*.py")) + [os.path.join(HERE, "template.html")]]
    if BREAK == "names":
        texts.append("write to someone" + chr(64) + "example.com")
    mail = [x for x in texts if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", x.replace("PressOffice" + chr(64) + "bls.gov", ""))]
    words = {w.lower() for x in texts for w in re.findall(r"[A-Za-z]+", x)}
    emp = [w for w in words if hashlib.sha1(w.encode()).hexdigest() == EMPLOYER_SHA1]
    check("9 names", not mail and not emp, "no e-mail address and not the employer" + (f"; {len(mail)} text(s) with an address" if mail else ""))
    # 10 register ----------------------------------------------------------------
    T = page_text(t) + (" benefits were gutted" if BREAK == "register" else "")
    hit = [w for w in ("boom", "crisis", "strain", "bubble", "glut", "gutted", "draconian", "handout")
           if re.search(r"\b" + w + r"\b", T, re.I)]
    check("10 register", not hit, "none of the ruled-out words" + (f"; found {hit}" if hit else ""))
    print(f"{len(fails)} failure(s)" + (f" (--break {BREAK})" if BREAK else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
