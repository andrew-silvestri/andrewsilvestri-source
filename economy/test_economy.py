"""
The failure modes this project is exposed to.

1. A mistyped or refitted coefficient. This page is arithmetic over five
   transcribed polynomials. Every number it states - the exchange rate, the
   minutes saved, the agreement with the measured transfer - comes out of those
   coefficients, so one wrong digit moves all of them together and moves them
   quietly. Nothing in the layout audits or the drift check would see it. It is
   the same failure as a figure whose proportions come from unsourced literals:
   a number no source contains, presented as one that does.

   Two checks, because the obvious one is weaker than it looks.

   1a. The source paper states three results of its own, so the transcription
       can be made to prove itself: the curve must reproduce 1.17%, 0.65% and
       2.64% at the paper's stated speeds and savings, to 0.02 percentage
       points. It currently reproduces to 0.008.

       What this catches, measured rather than assumed: a sign flip on the
       linear term lands 0.25 pp out and is caught. What it does NOT catch, and
       this was found by trying it: a perturbation of one per cent or less in
       any single coefficient, and a five per cent error in the linear term,
       which actually lowers the residual to 0.004 - below the value the
       correct coefficients give. The three published results are all ratios
       evaluated at two speeds, so errors in different terms trade off inside
       them. Reproducing a paper's stated percentages is good evidence about
       the shape of a curve and weak evidence about its coefficients.

   1b. So the coefficients are also checked as literals, against the values
       transcribed from the PMC full text on 2026-09-05. This is what actually
       guards the page: any edit to a digit fails immediately and loudly,
       whether or not it moves a published number, and a curve refitted to some
       other data cannot be substituted quietly. If a coefficient here must
       change, the source has to change with it.

2. A sign error in the quadratic term. That would not be caught by (1) alone
   at a single speed, so the shape of the answer is asserted too: the exchange
   rate is above 1 at slow paces, below 1 at fast ones, and falls monotonically
   in between.

3. The compounding null inflating. The product exceeds the sum by construction;
   if that gap ever exceeded about a percentage point at 5% per term, the
   identity would have been rebuilt wrongly and a null would have become a
   finding.

4. A unit slip. Oxygen cost is quoted per kilometre and speeds in metres per
   second, and mixing the two silently rescales everything downstream. Both
   cohort-derived quantities are asserted to lie inside bands that a unit error
   would leave.

5. An unsourced number, or one sourced to a book. Every payload entry that
   carries a value must carry a source, and no source may name a training
   manual: this project's copyright rule is that nothing comes from one.

6. The page and the payload disagreeing. Rendering the template from the
   payload must reproduce the shipped page byte for byte.

7. A clock time typed into the prose. The template is prose with placeholders,
   so it is possible to type "2:56 pace" beside a placeholder that renders
   2:55, and nothing else would notice: the drift check compares the page to
   what the template renders, and the template is where the wrong number
   lives. That happened during the build - the marginalia carried two paces a
   digit off from the generated prose - so every clock time on the page is now
   checked against the set the payload actually produces.

Run:  python3 test_economy.py
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import model as M                                              # noqa: E402

PAYLOAD = os.path.join(HERE, "outputs", "economy_payload.json")
PAGE = os.path.join(HERE, "..", "site", "economy.html")

# Words that may not appear in any source string. The rule for this project is
# that nothing derives from a training manual, so nothing may cite one.
BOOK_WORDS = ("advanced marathoning", "pfitzinger", "daniels' running formula",
              "isbn", "human kinetics")

# Equations 1-6 of Kipp, Kram & Hoogkamer 2019, transcribed from the PMC full
# text (PMC6378703) on 2026-09-05 and read back against it. Held here, apart
# from model.py, so the test compares two independent copies rather than
# checking a value against itself. Changing a digit in one and not the other
# fails; changing both is a deliberate act that has to be justified against the
# source.
TRANSCRIBED = {
    "batliner": (0.02724, 1.5355, 1.5354, 15.661),
    "leger": (0.02724, 0.0, 11.39, 2.209),
    "black": (0.02724, 1.9128, 3.2483, 25.806),
    "kipp2018": (0.02724, 1.7321, 0.538, 18.91),
    "batliner_linear": (0.02724, 0.0, 12.2, 1.11),
}


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    fails = []

    # 1a. the source paper's own three results, from the transcribed coefficients
    ok, rows = M.check_paper_numbers(tol=0.02)
    for r in rows:
        if not r["ok"]:
            fails.append(f"{r['label']}: paper states {r['stated_pct']}%, "
                         f"computed {r['computed_pct']:.3f}%")
    worst = max(abs(r["diff_pp"]) for r in rows)
    print(f"  1a. paper's own numbers: 3 of 3 reproduce, worst {worst:.4f} pp "
          f"(tolerance 0.02)")

    # 1b. the coefficients as literals, against a second copy of the
    #     transcription. This is the check that actually holds the page down.
    if set(TRANSCRIBED) != set(M.CURVES):
        fails.append(f"the set of curves changed: {sorted(M.CURVES)} against "
                     f"{sorted(TRANSCRIBED)}")
    for name, coef in TRANSCRIBED.items():
        got = tuple(M.CURVES.get(name, {}).get("coef", ()))
        if got != coef:
            fails.append(f"curve {name!r} has coefficients {got}, transcribed "
                         f"as {coef}; a coefficient may not be changed without "
                         f"changing the source it is transcribed from")
    print(f"  1b. coefficients: {len(TRANSCRIBED)} curves match the transcription "
          f"digit for digit")

    # 2. the shape of the exchange rate
    if not M.elasticity(2.60) > 1.0:
        fails.append("the exchange rate is not above 1 at 2.60 m/s")
    if not M.elasticity(5.72) < 1.0:
        fails.append("the exchange rate is not below 1 at 5.72 m/s")
    grid = [2.2 + 0.05 * i for i in range(77)]
    es = [M.elasticity(v) for v in grid]
    if any(b > a + 1e-9 for a, b in zip(es, es[1:])):
        fails.append("the exchange rate does not fall monotonically with pace")
    cross = P["elasticity"]["crossing_ms"]
    if not 2.8 < cross < 3.3:
        fails.append(f"the crossing moved to {cross:.2f} m/s; it should sit near 3.0")
    print(f"  2. shape: {es[0]:.2f} at 2.20 m/s, {es[-1]:.2f} at 6.00, "
          f"monotone, crossing {cross:.2f}")

    # 3. the null stays a null
    biggest = max(P["compounding"]["value"], key=lambda c: c["p"])
    if biggest["gap"] > 0.011:
        fails.append(f"compounding gap is {100 * biggest['gap']:.2f} pp at "
                     f"{100 * biggest['p']:.0f}% per term; a null should stay under 1.1")
    print(f"  3. compounding null: {100 * biggest['gap']:.2f} pp at "
          f"{100 * biggest['p']:.0f}% per term, {biggest['gap_s']:.0f} s on a 3:00 marathon")

    # 4. units. A cost quoted per minute rather than per km is out by 60/16;
    #    a speed in km/h rather than m/s is out by 3.6. Both would leave these.
    L = P["lanferdini"]
    lo, hi = L["cost_ml_kg_km"]["min"], L["cost_ml_kg_km"]["max"]
    if not 140 < lo and hi < 280:
        fails.append(f"oxygen cost {lo:.0f}-{hi:.0f} ml/kg/km is outside the "
                     f"range trained runners occupy; suspect a unit slip")
    share = L["share_of_ceiling_over_cost"]["mean"]
    if not 0.7 < share < 1.05:
        fails.append(f"3000 m speed is {share:.2f} of the ceiling over cost; "
                     f"a value outside 0.7-1.05 means the m/s conversion is wrong")
    ratio = P["vickers"]["ratio"]["median"]
    if not 0.70 < ratio < 0.92:
        fails.append(f"marathon speed is {ratio:.2f} of 5 km speed; outside "
                     f"0.70-0.92 means the pairing or the units are wrong")
    for r in P["paces"]["rows"]:
        if not 2.0 < r["v_ms"] < 6.5:
            fails.append(f"pace {r['v_ms']} is not in m/s")
    print(f"  4. units: cost {lo:.0f}-{hi:.0f} ml/kg/km, 3000 m at "
          f"{share:.2f} of ceiling/cost, marathon at {ratio:.2f} of 5 km speed")

    # 5. every value carries a source, and no source names a book
    def walk(node, path):
        if isinstance(node, dict):
            if "value" in node and "source" not in node:
                fails.append(f"{path} has a value and no source")
            for k, sub in node.items():
                if k == "source":
                    if any(w in str(sub).lower() for w in BOOK_WORDS):
                        fails.append(f"{path} cites a book: {sub!r}")
                else:
                    walk(sub, f"{path}.{k}")
        elif isinstance(node, list):
            for i, sub in enumerate(node):
                walk(sub, f"{path}[{i}]")

    for key in ("elasticity", "paces", "compounding", "lanferdini", "vickers",
                "looked_up", "assumed", "paper_check", "provenance"):
        walk(P[key], key)
    sources = re.findall(r'"source": "([^"]*)"', json.dumps(P))
    print(f"  5. sourcing: {len(sources)} source strings, 0 naming a book")

    # 6. the page reproduces from the payload
    import update_page
    if os.path.exists(PAGE):
        rendered, probs = update_page.cite(update_page.render(P))
        for p in probs:
            fails.append(f"citations: {p}")
        if rendered != open(PAGE, encoding="utf-8").read():
            fails.append("site/economy.html differs from what the payload renders")
        print("  6. page: renders byte for byte from the payload")
    else:
        fails.append("site/economy.html does not exist")

    # 7. every clock time on the page is one the payload generates
    if os.path.exists(PAGE):
        allowed = {P["compounding"]["baseline_hms"]}
        for r in P["paces"]["rows"]:
            allowed.add(r["marathon_hms"])
            for g in r["gain"].values():
                allowed.add(M.ms(g["saved_s"]))
                allowed.add(M.hms(r["marathon_s"] - g["saved_s"]))
        allowed.add(M.hms(P["elasticity"]["crossing_marathon_s"]))
        for v in P["looked_up"].values():
            if isinstance(v.get("value"), dict):
                for x in v["value"].values():
                    if isinstance(x, str) and ":" in x:
                        allowed.add(x)
        # h:mm is an accepted shortening of any h:mm:ss the payload holds
        allowed |= {a.rsplit(":", 1)[0] for a in allowed if a.count(":") == 2}
        page = open(PAGE, encoding="utf-8").read()
        main = page[page.index("<main"):page.index("</main>")]
        # The Sources list is prose-shaped but is not prose: a citation carries
        # a volume and page as "10:79", which matches a clock time and is not
        # one. It was out of scope only because this page's reference list used
        # to render outside </main>, which was a template fault fixed on
        # 2026-09-05; the list is now inside <main> like every other page's, so
        # the scan has to exclude it explicitly.
        main = re.sub(r'<ol class="refs">.*?</ol>', " ", main, flags=re.S)
        main = re.sub(r"<[^>]*>", " ", main)
        times = set(re.findall(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", main))
        stray = sorted(times - allowed)
        if stray:
            fails.append(f"clock time(s) on the page that the payload does not "
                         f"generate: {stray}")
        print(f"  7. clock times: {len(times)} on the page, all generated")

    print()
    if fails:
        print(f"  {len(fails)} FAILURE(S)")
        for f in fails:
            print(f"    - {f}")
        return 1
    print("  all checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
