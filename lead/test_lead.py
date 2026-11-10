"""The lead page (lead.html)'s own failure modes. Each check names the likeliest way the page goes wrong unseen;
each has a --break that reproduces that fault, and the run must exit 1 under it (HANDOFF traps 17, 26, 38). Every
check recomputes from the raw files through sources.py, not from the payload it is checking (trap 20).

 1. known      The paper's printed figures reproduce from its own datasets: 824,097,690 points, 2.6 per person,
               53.5 percent at or above 5 ug/dL, and the means 4.8, 5.9 and 5.7 for 1961-65, 1966-70 and
               1971-75. --break known charges the 0-4.9 band at the 5-9.9 slope (a band read off by one).
 2. slopes     The per-band losses parsed from Dataset S03's formulas use the slopes the SI Appendix prints
               (0.513, 0.19, 0.11). --break slopes reads 0.19 as 0.91.
 3. gasoline   Every yearbook value is in the yearbook's text, and the tonnes are the printed value converted.
               --break gasoline moves one year's value by 1,000 short tons.
 4. world      Every row of the Larsen table the page prints is in the paper's table 2. --break world changes
               one region's total.
 5. blood      The blood-lead table on the page is EPA's indicator B1, period by period. --break blood
               swaps the median and the 95th percentile.
 6. hero       The hero's bars, as shipped in the page, are the mean loss by birth year recomputed from the
               datasets. --break hero shifts the series by one year.
 7. curves     The other two curves' totals recompute from the slopes printed in their sources. --break curves
               counts Lanphear's fit from 1 ug/dL instead of 2.4.
 8. page       The page equals what update_page.py renders from the payload. --break page moves one figure.
 9. names      No email address and not the internship employer (checked by the SHA-1 of each word, so the name
               is nowhere in this tree). --break names writes an address into the text read.
10. register   None of the words the house rules exclude ("boom", "crisis", "strain", "bubble", "glut") and no
               "had been" (test_retro). --break register writes one into the text read.

Run:  python test_lead.py [--break known|slopes|gasoline|world|blood|hero|curves|page|names|register]
"""
import hashlib
import html
import json
import math
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sources as S        # noqa: E402

BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
PAGE = os.path.join(ROOT, "site", "lead.html")
EMPLOYER_SHA1 = "c0446e86c1b75316d035502707018d75dd2fc688"   # lower-cased name; the name itself is not in the tree
fails = []


def check(name, ok, detail):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def raw_page():
    return open(PAGE, "rb").read().decode("utf-8")


def page_text(t=None):
    t = raw_page() if t is None else t
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", t, flags=re.S)
    t = re.sub(r'<sup class="cite".*?</sup>', "", t, flags=re.S)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))


def cohorts(loss):
    pop = defaultdict(lambda: defaultdict(float))
    for r in S.s01():
        if r["year"] == 2015:
            pop[r["cohort"]][r["band"]] += r["leadpop"]
    return pop


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    import update_page as UP

    # 1 known ---------------------------------------------------------------------
    loss = S.band_loss()
    if BREAK == "known":
        loss = dict(loss, **{"0-4.9": loss["5-9.9"]})
    pop = cohorts(loss)
    alive = S.s03_population()
    total = sum(n * loss[b] for c, d in pop.items() if c >= 1940 for b, n in d.items())

    def mean(a, z):
        ys = range(a, z + 1)
        return sum(n * loss[b] for c in ys for b, n in pop[c].items()) / sum(sum(pop[c].values()) for c in ys)
    ge5 = sum(sum(d.values()) - d["0-4.9"] for c, d in pop.items() if c >= 1940) / alive
    ok = (round(total) == 824097690 and round(total / alive, 1) == 2.6 and round(100 * ge5, 1) == 53.5 and
          [round(mean(a, z), 1) for a, z in ((1961, 1965), (1966, 1970), (1971, 1975))] == [4.8, 5.9, 5.7])
    check("1 known", ok, f"total {total:,.0f}, {total / alive:.2f} per person, {ge5:.1%} >= 5 ug/dL, "
                         f"means {mean(1961, 1965):.2f} / {mean(1966, 1970):.2f} / {mean(1971, 1975):.2f}")

    # 2 slopes --------------------------------------------------------------------
    si = S.text("pnas_si_appendix.pdf")
    want = {"0.513", "0.19", "0.11"}
    got = S.band_loss()
    steps = [round(got["5-9.9"] / 7.5, 3)] + [round((got[b] - got[a]) / 5, 3) for a, b in
                                              zip(S.BANDS[1:-1], S.BANDS[2:])]
    if BREAK == "slopes":
        steps[1] = 0.91
    used = {f"{s:g}" for s in steps}
    check("2 slopes", used == want and all(w in si for w in want),
          f"S03 slopes {sorted(used)} are the SI Appendix's {sorted(want)}")

    # 3 gasoline ------------------------------------------------------------------
    group = re.compile(r"(\d)[,.] (\d{3})")
    bad = []
    for r in S.gasoline():
        row = r["row"]
        ov = float(row["original_value"]) + (1000 if BREAK == "gasoline" and r["year"] == 1970 else 0)
        unit = row["original_unit"]
        conv = {"short tons": 0.90718474, "metric tons": 1.0, "thousand metric tons": 1000.0}[unit]
        if abs(ov * conv - r["tonnes"]) > 1:
            bad.append(f"{r['year']} conversion")
        if row["in_ocr"] == "yes":
            txt = group.sub(lambda g: g.group(1) + "," + g.group(2), S.text(row["ocr_file"]))
            shown = f"{int(ov):,}" if unit != "thousand metric tons" else f"{ov:g}"
            if shown not in txt:
                bad.append(f"{r['year']} not in {row['ocr_file']}")
        elif not re.search(r"page image|OCR text|\d = [\d,]+ \+ ", row["note"]):   # image, or a printed subtotal
            bad.append(f"{r['year']} unread and unexplained")
    check("3 gasoline", not bad, "every yearbook value is in its volume's text or its note says what the page "
                                 "image shows" + (f"; {bad[:5]}" if bad else ""))

    # 4 world ---------------------------------------------------------------------
    lt = S.text("larsen2023.pdf")
    rows = S.larsen_regions()
    if BREAK == "world":
        rows[-1] = dict(rows[-1], iq_m=rows[-1]["iq_m"] + 1)
    miss = [r["name"] for r in rows if r["group"].startswith("region") and
            f"{r['name']} {r['iq_m']:g} ({r['lo']:g}-{r['hi']:g}) {r['cost_pct_gdp']:g}%" not in lt]
    tot = next(r for r in rows if r["name"] == "Worldwide")
    ok = not miss and f"lost {tot['iq_m']:g} million (95% CI {tot['lo']:g}-{tot['hi']:,g})".replace(",", "") in lt
    check("4 world", ok, "the world total and every region row are in Larsen's table 2" + (f"; missing {miss}" if miss else ""))

    # 5 blood ---------------------------------------------------------------------
    b1 = S.epa_b1()
    rp = raw_page()
    tbl = re.search(r"<th>NHANES survey years</th>.*?</tbody>", rp, flags=re.S).group(0)
    cells = re.findall(r"<tr><td>(\d{4}) to (\d{4})</td><td>([\d.]+)</td><td>([\d.]+)</td></tr>", tbl)
    shown = [(int(a), int(b), float(m), float(p)) for a, b, m, p in cells]
    want = [(r["start"], r["end"], r["median"], r["p95"]) for r in b1]
    if BREAK == "blood":
        shown = [(a, b, p, m) for a, b, m, p in shown]
    check("5 blood", shown == want and len(want) >= 10, f"{len(shown)} survey periods match EPA's indicator B1")

    # 6 hero ----------------------------------------------------------------------
    spec = json.loads(re.search(r'<section class="scrolly wide" id="lead-hero".*?<script type="application/json" '
                                r'class="scrolly-spec">(.*?)</script>', rp, flags=re.S).group(1))
    L0 = S.band_loss()
    p0 = cohorts(L0)
    want = {c: sum(n * L0[b] for b, n in p0[c].items()) / sum(p0[c].values()) for c in range(1940, 2016)}
    bins = spec["bins"]
    if BREAK == "hero":
        bins = [dict(b, a=b["a"] + 1) for b in bins]
    ok = len(bins) == len(want) and all(abs(b["n"] - want.get(b["a"], -9)) < 0.001 for b in bins)
    check("6 hero", ok, f"{len(bins)} bars equal the mean loss by birth year recomputed from S01 and S03")

    # 7 curves --------------------------------------------------------------------
    lan = S.text("lanphear2005_pmc.xml")
    beta = float(re.search(r"Concurrent -4\.66 \(-5\.72 to -3\.60\) -(\d\.\d+)", lan).group(1))
    floor = float(re.search(r"concurrent blood lead levels from (\d\.\d) to 30", lan).group(1))
    if BREAK == "curves":
        floor = 1.0
    crump = float(re.search(r"Crump and colleagues13 with β=(\d\.\d+)", lt).group(1))
    mid = {"0-4.9": 2.5, "5-9.9": 7.5, "10-14.9": 12.5, "15-19.9": 17.5, "20-24.9": 22.5, "25-29.9": 27.5, "30+": 32.5}
    lan_t = sum(n * (beta * math.log(mid[b] / floor) if mid[b] > floor else 0) for c, d in p0.items() if c >= 1940
                for b, n in d.items())
    cr_t = sum(n * crump * math.log(mid[b] + 1) for c, d in p0.items() if c >= 1940 for b, n in d.items())
    ok = abs(lan_t - P["curves"]["lanphear"]["points"]) < 1 and abs(cr_t - P["curves"]["crump"]["points"]) < 1
    check("7 curves", ok, f"Lanphear {lan_t / 1e6:,.0f} M (slope {beta}, from {floor}), Crump {cr_t / 1e6:,.0f} M "
                          f"(slope {crump})")

    # 8 page ----------------------------------------------------------------------
    P2 = json.loads(json.dumps(P))
    if BREAK == "page":
        P2["us"]["total"] += 1e6
    try:
        t, _ = UP.cite(UP.render(P2))
        same = t == raw_page()
    except SystemExit:
        same = False
    check("8 page", same, "the page is exactly what update_page.py renders from the payload")

    # 9 names ---------------------------------------------------------------------
    T = page_text()
    t9 = T + (" write to someone@example.com" if BREAK == "names" else "")
    words = {w.lower() for w in re.findall(r"[A-Za-z]+", t9)}
    emp = any(hashlib.sha1(w.encode()).hexdigest() == EMPLOYER_SHA1 for w in words)
    mail = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", t9)
    check("9 names", not emp and not mail, "no email address and not the employer")

    # 10 register -----------------------------------------------------------------
    t10 = T + (" a crisis" if BREAK == "register" else "")
    hit = [w for w in ("boom", "crisis", "strain", "bubble", "glut", "had been") if re.search(r"\b" + w + r"\b", t10, re.I)]
    check("10 register", not hit, "none of the ruled-out words" + (f"; found {hit}" if hit else ""))
    print(f"{len(fails)} failure(s)" + (f" (--break {BREAK})" if BREAK else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
