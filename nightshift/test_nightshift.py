"""The night-work page (nightshift.html)'s own failure modes. Each check has a --break that reproduces the fault
it names, and the run must exit 1 under it (HANDOFF traps 17, 26, 38). Checks 1 and 2 recompute from the raw BLS
files, not from the payload they are checking (trap 20).

 1. table7   The usual night share of wage and salary workers, recomputed from the module with its weights,
             matches the payload and BLS's printed Table 7. --break table7 counts respondents unweighted.
 2. a3       The share of everyone 15+ asleep at 03:00 in 2025, recomputed from the activity file, matches
             Table A-3's 94.9. --break a3 reads the clock at 03:30.
 3. rings    In every ring and every ten-minute step, asleep plus at work is at most 100 percent.
             --break rings doubles the night ring's work share.
 4. claims   update_page.claims() accepts the payload. --break claims sets night workers' split-sleep share
             to the day workers'.
 5. page     The page is exactly what update_page.py renders. --break page moves one figure.
 6. nojs     The shipped page draws every layer: no element carries the live-only class "off".
             --break nojs adds one.
 7. employer The internship employer's name is not on the page (matched by SHA-1; the name is not in this tree).
             --break employer looks for the hash of "night" instead, a word that is on the page.

Run:  python test_nightshift.py [--break table7|a3|rings|claims|page|nojs|employer]
"""
import hashlib
import html
import json
import os
import re
import sys
import zipfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
RAW = os.path.join(HERE, "data", "raw")
BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
PAGE = os.path.join(ROOT, "site", "nightshift.html")
# the internship employer, by the SHA-1 of its lower-cased name (the name may not appear in this tree)
EMPLOYER_SHA1 = "c0446e86c1b75316d035502707018d75dd2fc688"
fails = []


def check(name, ok, detail):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def read(zipname, member, usecols=None):
    with zipfile.ZipFile(os.path.join(RAW, zipname)) as z, z.open(member) as h:
        return pd.read_csv(h, usecols=usecols)


def page_text(t):
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", t, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    raw_page = open(PAGE, encoding="utf-8").read()
    have_raw = os.path.exists(os.path.join(RAW, "lvresp-2425.zip"))
    # 1 table7
    if have_raw:
        lv = read("lvresp-2425.zip", "lvresp_2425.dat", ["LRSCHEDULE", "LUFINLWGT"])
        lv = lv[lv.LRSCHEDULE > 0]
        w = np.ones(len(lv)) if BREAK == "table7" else lv.LUFINLWGT.values
        share = (w * (lv.LRSCHEDULE.values == 3)).sum() / w.sum() * 100
        printed = P["checks"]["table7_night_printed"][4]
        check("1 table7", abs(share - printed) < 0.05 and abs(share - P["module"]["night_pct"]) < 0.01,
              f"night share {share:.2f}% against Table 7's {printed}")
    else:
        print("  SKIP 1 table7: data/raw not fetched (python fetch_public.py)")
    # 2 a3
    if have_raw:
        a = read("atusact-2025.zip", "atusact_2025.dat", ["TUCASEID", "TUACTDUR24", "TUCUMDUR24", "TRCODE"])
        r = read("atusresp-2025.zip", "atusresp_2025.dat", ["TUCASEID", "TUFINLWGT"]).set_index("TUCASEID")
        t = (23 * 60 + (30 if BREAK == "a3" else 0))             # minutes after 04:00 for 03:00 (03:30)
        end = a.TUCUMDUR24
        m = (end - a.TUACTDUR24 <= t) & (end > t) & (a.TRCODE // 100 == 101)
        ids = a.loc[m, "TUCASEID"].unique()
        pct = r.TUFINLWGT.loc[ids].sum() / r.TUFINLWGT.sum() * 100
        check("2 a3", abs(pct - 94.9) < 0.06, f"asleep at 03:00 in 2025: {pct:.2f}% against Table A-3's 94.9")
    else:
        print("  SKIP 2 a3: data/raw not fetched")
    # 3 rings
    worst = 0.0
    rings = [P["pop"]] + [P["groups"][g]["clock"] for g in ("night_work", "day_work")]
    for k, c in enumerate(rings):
        wk = [2 * x for x in c["work"]] if (BREAK == "rings" and k == 1) else c["work"]
        worst = max(worst, max(s + x for s, x in zip(c["sleep"], wk)))
    check("3 rings", worst <= 100.05, f"largest asleep + at work in any step: {worst:.1f}%")
    # 4 claims
    import update_page as U
    Q = json.loads(json.dumps(P))
    if BREAK == "claims":
        Q["groups"]["night_work"]["two_sleeps_pct"] = Q["groups"]["day_work"]["two_sleeps_pct"]
    try:
        U.claims(Q)
        check("4 claims", True, "every worded claim holds against the payload")
    except SystemExit as e:
        check("4 claims", False, str(e).splitlines()[-1].strip())
    # 5 page
    t, probs = U.cite(U.render(P))
    shipped = raw_page
    if BREAK == "page":
        shipped = shipped.replace(f"{P['module']['night_pct']:.1f} percent", "3.5 percent", 1)
    check("5 page", t == shipped and not probs, "shipped page is the rendered page" if t == shipped
          else "shipped page differs from update_page.py's render")
    # 6 nojs
    body = raw_page + ('<g class="off"></g>' if BREAK == "nojs" else "")
    check("6 nojs", not re.search(r'class="[^"]*\boff\b', body), "no element ships hidden")
    # 7 employer
    words = page_text(raw_page).lower()
    target = hashlib.sha1(b"night").hexdigest() if BREAK == "employer" else EMPLOYER_SHA1
    toks = set(re.findall(r"[a-z]+", words))
    hit = any(hashlib.sha1(w.encode()).hexdigest() == target for w in toks)
    check("7 employer", not hit, "the employer's name is not on the page")
    print(f"  {len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
