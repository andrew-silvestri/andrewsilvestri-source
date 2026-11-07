"""The oxygen page (oxygen.html)'s own failure modes. Each check has a --break that reproduces the fault it names,
and the run must exit 1 under it (HANDOFF traps 17, 26, 38). Checks recompute from the raw files through
sources.py, not from the payload they are checking (trap 20).

 1. units     MTBE is EIA's thousand barrels a month over the days in the month; 1997's mean is below EIA's
              printed 269 thousand b/d for all MTBE in gasoline and within 15% of it. --break units skips the
              division by days.
 2. share     Ethanol's share of gasoline in the latest full year is MER consumption over finished gasoline
              product supplied, as the payload has it. --break share divides by reformulated gasoline only.
 3. bans      EPA's table gives 25 states, and California's date in force is the delayed one, 31 December 2003.
              --break bans takes the first date in California's row (the original 2002 date).
 4. corn      The corn chart stops two years before the last year in USDA's file (an estimate and a projection
              follow it). --break corn keeps the projection year.
 5. switch    MTBE use fell by more than nine tenths from January to May 2006, recomputed. --break switch uses 2005.
 6. quotes    Every quotation is in its source and is under 15 words. --break quotes alters one word.
 7. page      The page is exactly what update_page.py renders. --break page moves one figure.
 8. tree      Every link in the causal tree runs from an order to the same or a later one, and every order
              0-4 has a step card. --break tree gives the policy node order 3.
 9. nojs      The shipped page draws every node: no element carries the live-only class "off".
              --break nojs adds one.
10. names     No company named in the MTBE lawsuits and not the employer is on the page.
              --break names writes one into the text read.

Run:  python test_oxygen.py [--break units|share|bans|corn|switch|quotes|page|tree|nojs|names]
"""
import calendar
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
import sources as S          # noqa: E402

BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
PAGE = os.path.join(ROOT, "site", "oxygen.html")
NAMES = ["ExxonMobil", "Exxon", "Shell", "Chevron", "ChevronTexaco", "Lyondell", "Valero", "Sunoco", "BP"]
# the internship employer, by the SHA-1 of its lower-cased name (the name may not appear in this tree)
EMPLOYER_SHA1 = "c0446e86c1b75316d035502707018d75dd2fc688"
fails = []


def check(name, ok, detail):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def page_text(t):
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", t, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    raw = open(PAGE, encoding="utf-8").read()
    # 1 units
    xl = S._xls("eia_mtbe_net_input_m.xls")
    days = (lambda y, m: 1) if BREAK == "units" else (lambda y, m: calendar.monthrange(y, m)[1])
    m97 = sum(xl[(1997, m)] / days(1997, m) * calendar.monthrange(1997, m)[1] for m in range(1, 13)) / 365
    if BREAK == "units":
        m97 = sum(xl[(1997, m)] for m in range(1, 13)) / 12
    ok = 0 < (269 - m97) / 269 < 0.15 and abs(m97 - P["annual"]["1997"]["mtbe"]) < 0.5
    check("1 units", ok, f"1997 MTBE {m97:.0f} thousand b/d against EIA's printed 269")
    # 2 share
    last = str(int(P["through"][:4]) - 1)
    eth = S.ethanol_annual()[last]
    den = S.rfg_annual()[last] if BREAK == "share" else S.gasoline_annual()[last]
    sh = eth / den
    check("2 share", abs(sh - P["annual"][last]["eth_share"]) < 1e-4 and 0.09 < sh < 0.12,
          f"ethanol {100 * sh:.2f}% of gasoline in {last}")
    # 3 bans
    rows = S.state_bans()
    ca = [r for r in rows if r[0] == "CA"][0][1]
    if BREAK == "bans":
        ca = "2002-12-31"
    check("3 bans", len(rows) == 25 and ca == "2003-12-31" and P["bans"]["n"] == 25,
          f"{len(rows)} states; California in force {ca}")
    # 4 corn
    years = sorted(S.corn())
    keep = [y for y in years if int(y) <= int(years[-1]) - (0 if BREAK == "corn" else 2)]
    check("4 corn", keep[-1] == P["corn"]["last_final"] and max(P["corn"]["share"]) == keep[-1],
          f"chart ends {keep[-1]}; USDA's file ends {years[-1]}")
    # 5 switch
    mt = S.mtbe_monthly()
    y = "2005" if BREAK == "switch" else "2006"
    jan, may = mt[f"{y}-01"], mt[f"{y}-05"]
    check("5 switch", may < 0.1 * jan and abs(jan - P["switch"]["jan"]) < 0.05,
          f"{y}: January {jan:.0f}, May {may:.0f} thousand b/d")
    # 6 quotes
    import update_page as UP
    bad = []
    for k, (src, pat) in UP.Q.items():
        m = S.quote(src, pat)
        q = html.escape(m.group(0), quote=False)
        if BREAK == "quotes" and k == "q_dole":
            q = q.replace("increase", "raise")
        if q not in raw or len(m.group(0).split()) >= 15:
            bad.append(k)
    check("6 quotes", not bad, "every quotation is in its source, on the page, under 15 words" + (f"; {bad}" if bad else ""))
    # 7 page
    t = UP.render(P)
    t, _ = UP.cite(t)
    if BREAK == "page":
        t = t.replace(f">{P['bans']['n']} states", f">{P['bans']['n'] + 1} states", 1).replace(
            f" {P['bans']['n']} states", f" {P['bans']['n'] + 1} states", 1)
    check("7 page", t == raw, "the page is exactly what update_page.py renders")
    # 8 tree
    order = {n[0]: n[1] for n in UP.NODES}
    if BREAK == "tree":
        order["P"] = 3
    back = [(a, b) for a, b in UP.EDGES if order[a] > order[b]]
    steps = sorted(int(s) for s in re.findall(r'class="step" data-step="(\d)"', raw))
    check("8 tree", not back and steps == [0, 1, 2, 3, 4], f"links backward {back}; step cards {steps}")
    # 9 nojs
    r9 = raw.replace('class="n ev-strong"', 'class="n ev-strong off"', 1) if BREAK == "nojs" else raw
    offs = re.findall(r'class="[^"]*\boff\b[^"]*"', re.search(r'<figure class="chain.*?</figure>', r9, re.S).group(0))
    check("9 nojs", not offs, "no node or link is hidden in the shipped markup" + (f"; {offs[:2]}" if offs else ""))
    # 10 names
    T = page_text(raw) + (" a settlement with Shell" if BREAK == "names" else "")
    hit = [n for n in NAMES if re.search(r"\b" + n + r"\b", T)]
    low = T.lower()
    emp = any(hashlib.sha1(w.encode()).hexdigest() == EMPLOYER_SHA1 for w in set(re.findall(r"[a-z]+", low)))
    check("10 names", not hit and not emp, "no litigant company or employer named" + (f"; found {hit}" if hit else ""))
    print(f"{len(fails)} failure(s)" + (f" (--break {BREAK})" if BREAK else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
