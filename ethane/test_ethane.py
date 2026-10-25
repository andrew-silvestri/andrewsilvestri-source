"""The ethane page (ethane.html, Q11)'s own failure modes. Each check exists because the fault it names happened
while the page was planned or built, or is the likeliest way it goes wrong unseen; each has a --break that
reproduces that fault, and the run must exit 1 under it (HANDOFF traps 17, 26, 38). Every check recomputes from
EIA's raw files through sources.py, not from the payload it is checking (trap 20).

 1. known      Figures EIA printed reproduce from the series: ethane's share 42% (2010) and 34% (2015), 1.1
               million b/d in 2015, 1.71 in 2018. --break known reads the propane column as ethane (a shifted
               or misread column, the fault the column-title check in sources.ngpl exists for).
 2. total      EIA's NGPL total is the five products every month, so the share is ethane over all of them.
               --break total drops natural gasoline from the sum (a share of the wrong total).
 3. fraction   The standfirst's "about 15 to 27 per cent" is EIA's 200-400 thousand b/d against what plants recovered
               on average in 2014. --break fraction uses January-April 2014, the build's earlier base, which the
               claims ledger (57) found the article does not support.
 4. share      The share the page prints for the latest twelve months is that, recomputed. --break share uses
               the latest month alone (plan review 10: a preliminary single month in a headline figure).
 5. growth     "grown 2.9 times and the other plant liquids 2.0 times" is the twelve months against 2015.
               --break growth uses the latest month (review 10 again).
 6. hero       The chart's data, as shipped in the page, is the share and the volumes by month, recomputed.
               --break hero shifts the share series by one month.
 7. quotes     Every quotation on the page is in the EIA article it comes from, and none forecasts (review 17).
               --break quotes alters one word of the first.
 8. page       The page equals what update_page.py renders from the payload. --break page moves one figure.
 9. archived   The Archived note follows the standfirst and names the payload's last month (D-60, Andrew's
               note). --break archived reads the page without the card.
10. names      No company the EIA articles name, no data vendor, and not the employer, is on the page (D-61 A,
               plan review 16). --break names writes one of the articles' companies into the text read.
11. register   No word the packet rules out ("boom", "crisis", "strain", "bubble", "glut") in the page's own
               words. --break register writes one into the text read.

Run:  python test_ethane.py [--break known|total|fraction|share|growth|hero|quotes|page|archived|names|register]
"""
import html
import json
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sources as S        # noqa: E402

BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
PAGE = os.path.join(ROOT, "site", "ethane.html")
fails = []
# The companies EIA's articles name (TIE 28052, 39712, 64785) and the data vendors EIA credits.
NAMES = ["Enterprise", "Chevron", "Phillips", "ExxonMobil", "Exxon", "Indorama", "Utopia", "Shell", "Bloomberg",
         "Refinitiv", "LSEG", "OPIS", "Reuters"]
# The internship employer, by the SHA-1 of its lower-cased name: the name itself may not appear anywhere in this
# tree, the test included (_RULES: the employer grep blocks a commit on any match).
EMPLOYER_SHA1 = "c0446e86c1b75316d035502707018d75dd2fc688"


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


def ymean(series, y):
    ms = [m for m in series if m.startswith(f"{y}-")]
    return st.fmean(series[m] for m in ms)


def main():
    N = S.ngpl()
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    T = page_text()
    eth = {m: (r["pro"] if BREAK == "known" else r["eth"]) for m, r in N.items()}
    tot = {m: r["ngl"] for m, r in N.items()}
    share = {m: eth[m] / tot[m] for m in N}
    # 1 known ---------------------------------------------------------------------
    got = (round(100 * ymean(share, 2010)), round(100 * ymean(share, 2015)), round(ymean(eth, 2015) / 1000, 1),
           round(ymean(eth, 2018) / 1000, 2))
    check("1 known", got == (42, 34, 1.1, 1.71), f"share 2010/2015, 2015 and 2018 volumes {got}; EIA (42, 34, 1.1, 1.71)")
    # 2 total ---------------------------------------------------------------------
    bad = [m for m, r in N.items() if m >= "2009-01" and abs(r["ngl"] - (r["eth"] + r["pro"] + r["nbu"] + r["ibu"]
           + (0 if BREAK == "total" else r["ngas"]))) > 2]
    check("2 total", not bad, "EIA's NGPL total equals the five products every month from 2009"
          + (f"; differs in {len(bad)} months, first {bad[0]}" if bad else ""))
    # 3 fraction ------------------------------------------------------------------
    lo = int(S.quote("eia_tie_16191.html", r"range between (\d+) and (\d+) Mbbl/d").group(1))
    hi = int(S.quote("eia_tie_16191.html", r"range between (\d+) and (\d+) Mbbl/d").group(2))
    rec = st.fmean(eth[m] for m in ("2014-01", "2014-02", "2014-03", "2014-04")) if BREAK == "fraction" else ymean(eth, 2014)
    words = f"about {100 * lo / (rec + lo):.0f} to {100 * hi / (rec + hi):.0f} per cent of the ethane in the gas the plants processed"
    check("3 fraction", words in T, f"the standfirst carries '{words}'")
    # 4 share ---------------------------------------------------------------------
    xs = sorted(N)
    ttm = xs[-1:] if BREAK == "share" else xs[-12:]
    sh = sum(eth[m] for m in ttm) / sum(tot[m] for m in ttm)
    s_words = f"The share was {100 * sh:.1f} per cent over the twelve months to"
    check("4 share", s_words in T, f"the page says '{s_words}'")
    # 5 growth --------------------------------------------------------------------
    other = {m: tot[m] - eth[m] for m in N}
    span = xs[-1:] if BREAK == "growth" else xs[-12:]
    ge = st.fmean(eth[m] for m in span) / ymean(eth, 2015)
    go = st.fmean(other[m] for m in span) / ymean(other, 2015)
    g_words = f"grown {ge:.1f} times and the other plant liquids {go:.1f} times"
    check("5 growth", g_words in T, f"the page says '{g_words}'")
    # 6 hero ----------------------------------------------------------------------
    spec = json.loads(re.search(r'<script type="application/json" class="scrolly-spec">(.*?)</script>', raw_page(),
                                flags=re.S).group(1).replace("<\\/", "</"))
    hx = spec["x"]
    want = [round(100 * share[m], 2) for m in hx]
    if BREAK == "hero":
        want = want[1:] + want[-1:]
    vols = [round(eth[m] / 1000, 3) for m in hx]
    ok6 = spec["series"][0]["values"] == want and spec["under"][0]["values"] == vols and hx[0] == "2009-01" and hx[-1] == xs[-1]
    check("6 hero", ok6, f"{len(hx)} months, {hx[0]} to {hx[-1]}: the shipped chart data is the raw series")
    # 7 quotes --------------------------------------------------------------------
    qs = []
    body = page_text(raw_page().split("<h2>Sources</h2>")[0])     # the Sources list cites titles, which may forecast
    for q in re.findall(r'["“]([^"”]{12,})["”]', body):
        qs += [p.strip() for p in q.split("…")]
    if BREAK == "quotes":
        w = qs[0].split()                     # change one word, whatever the first quotation says; a replace()
        w[len(w) // 2] = w[len(w) // 2] + "s"  # of a word that is no longer there mutated nothing (2026-10-25)
        qs[0] = " ".join(w)
    arts = [S.flat(n) for n in sorted(os.listdir(os.path.join(HERE, "data", "raw")))
            if n.startswith(("eia_tie_", "eia_ngwu_"))]
    norm = [re.sub(r" ([,.;:)])", r"\1", a) for a in arts]
    missing = [q for q in qs if not any(q.rstrip(".") in a for a in norm)]
    fore = [q for q in qs if re.search(r"\b(expect\w*|forecast\w*|will|project\w*)\b", q, re.I)]
    check("7 quotes", qs and not missing and not fore, f"{len(qs)} quotations found in EIA's articles"
          + (f"; missing {missing[:2]}" if missing else "") + (f"; forecasting {fore[:1]}" if fore else ""))
    # 8 page ----------------------------------------------------------------------
    import update_page as UP
    P2 = json.loads(json.dumps(P))
    if BREAK == "page":
        P2["ttm"]["share"] += 0.002
    try:
        t, _ = UP.cite(UP.render(P2))
        same = t == raw_page()
    except SystemExit:
        same = False
    check("8 page", same, "the page is exactly what update_page.py renders from the payload")
    # 9 archived ------------------------------------------------------------------
    rp = raw_page()
    if BREAK == "archived":
        rp = re.sub(r'<p class="stamp archived">.*?</p>', "", rp, flags=re.S)
    m = re.search(r"</h1>\s*<p class=\"dim\">.*?</p>\s*<p class=\"stamp archived\"><b>Archived page\.</b>(.*?)</p>",
                  rp, flags=re.S)
    want_m = UP.mon(xs[-1])
    check("9 archived", bool(m) and want_m in m.group(1) and "not be updated" in m.group(1),
          f"the Archived note follows the standfirst and says 'through {want_m}' and 'not be updated'")
    # 10 names --------------------------------------------------------------------
    t10 = T + (" a cracker built by Shell" if BREAK == "names" else "")
    hit = [n for n in NAMES if re.search(r"\b" + n + r"\b", t10)]
    check("10 names", not hit, "no company, data vendor or employer named" + (f"; found {hit}" if hit else ""))
    # 11 register -----------------------------------------------------------------
    t11 = T + (" a glut" if BREAK == "register" else "")
    hit = [w for w in ("boom", "crisis", "strain", "bubble", "glut") if re.search(r"\b" + w + r"\b", t11, re.I)]
    check("11 register", not hit, "none of the ruled-out words" + (f"; found {hit}" if hit else ""))
    print(f"{len(fails)} failure(s)" + (f" (--break {BREAK})" if BREAK else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
