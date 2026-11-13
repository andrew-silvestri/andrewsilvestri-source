"""The algae page (algae.html)'s own failure modes. Each check names the likeliest way the page goes wrong unseen;
each has a --break that reproduces that fault, and the run must exit 1 under it (HANDOFF traps 17, 26, 38).
Checks 1-3 recompute from the files the build reads, not from the payload they are checking (trap 20).

 1. known     The Global Carbon Budget ocean sink, 2015-2024 mean, recomputed from the raw workbook, is the
              3.2 GtC a year the paper prints. --break known reads the land-sink column instead.
 2. siegel    The retention table reproduces Siegel and colleagues' printed check: CO2 released at 208 m, plain
              mean over grid cells after 50 years, 15 percent (to 2 points). --break siegel takes the
              area-weighted mean, the weighting the page uses elsewhere.
 3. funnel    The net values the hero prints for sunk seaweed and buried pond algae are the products of
              params.py's fractions and the retention table. --break funnel uses the 1,022 m retention for the
              central seaweed case instead of 2,100 m.
 4. page      The page equals what update_page.py renders from the payload. --break page moves one figure.
 5. static    Without JS the hero shows every row's final value and hides the per-stage ones: in both drawings,
              six rows, each with .v0 and .v1 marked data-only and a .v2 that is not. --break static marks one
              .v2 data-only (a row that would show no value without JS).
 6. fits      No row's label meets its value in either drawing (update_page.fits at 900 and 320 px).
              --break fits checks a 300 px drawing.
 7. names     No email address and not the internship employer (checked by the SHA-1 of each word).
              --break names writes an address into the text read.
 8. register  None of the words the house rules exclude: hype ("studies show", "game-changing", "unprecedented",
              "revolutionary", "miracle", "silver bullet"), intensifiers, development history ("had been",
              "updated", "v2"), "per cent", and no first person singular. --break register writes one in.

Run:  python test_algae.py [--break known|siegel|funnel|page|static|fits|names|register]
"""
import csv
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
import params as PR          # noqa: E402
import update_page as UP     # noqa: E402

BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
EMPLOYER_SHA1 = "c0446e86c1b75316d035502707018d75dd2fc688"   # lower-cased name; the name itself is not in the tree
PAGE = os.path.join(ROOT, "site", "algae.html")
fails = []


def check(name, ok, detail):
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def raw_page():
    return open(PAGE, "rb").read().decode("utf-8")


def page_text(t=None):
    t = raw_page() if t is None else t
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", t, flags=re.S)
    t = re.sub(r'<sup class="cite".*?</sup>', "", t, flags=re.S)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))


def retention():
    rows = list(csv.DictReader(open(os.path.join(HERE, "data", "siegel2021_retention_by_depth.csv"), encoding="utf-8")))

    def get(depth, t, w):
        c = [r for r in rows if int(r["t_years"]) == t and r["weighting"] == w]
        return float(min(c, key=lambda r: abs(float(r["depth_m"]) - depth))["mean_fraction"])
    return get


def main():
    import pandas as pd
    from netfetch import verified
    P = json.load(open(os.path.join(HERE, "outputs", "payload.json"), encoding="utf-8"))

    # 1 known ---------------------------------------------------------------------
    path, _ = verified("gcb2025.xlsx")
    d = pd.read_excel(path, sheet_name="Global Carbon Budget", header=None)
    h = d.index[d[0].astype(str).str.strip() == "Year"][0]
    t = d.iloc[h + 1:, :8]
    t = t[pd.to_numeric(t[0], errors="coerce").notna()].astype(float).set_index(0)
    col = 5 if BREAK == "known" else 4          # 4 = ocean sink, 5 = land sink
    m = float(t.loc[2015:2024, col].mean())
    check("1 known", abs(m - 3.2) <= 0.05, f"GCB 2025 ocean sink 2015-2024 mean {m:.2f} GtC/yr (printed 3.2)")

    # 2 siegel --------------------------------------------------------------------
    get = retention()
    v = get(208, 50, "area" if BREAK == "siegel" else "none")
    check("2 siegel", abs(v - 0.15) <= 0.02, f"208 m after 50 years: {100 * v:.1f} percent retained (printed 15)")

    # 3 funnel --------------------------------------------------------------------
    f = {x["key"]: x for x in PR.FUNNEL}
    sw, pb = f["seaweed"], f["pondburied"]
    r_c = get(1022 if BREAK == "funnel" else 2100, 100, "area")
    sw_c = 100 * sw["from_air"][1] * sw["reach"][1] * r_c
    pb_c = 100 * pb["harvest"][1] * pb["from_air"][1] * pb["tomb"][1] - pb["energy"][1]
    page = raw_page()
    shown = {k: re.search(r'<g class="row r-%s">.*?<text class="val v2"[^>]*>([^<]+)</text>' % k, page, re.S).group(1)
             for k in ("seaweed", "pondburied")}
    ok = shown["seaweed"].startswith(f"{round(sw_c)} t ") and shown["pondburied"].startswith(f"{round(pb_c)} t ")
    check("3 funnel", ok, f"hero shows seaweed {shown['seaweed']!r} (recomputed {sw_c:.1f}), "
                          f"pond burial {shown['pondburied']!r} (recomputed {pb_c:.1f})")

    # 4 page ----------------------------------------------------------------------
    P2 = json.loads(json.dumps(P))
    if BREAK == "page":
        P2["gcb"]["fossil"] += 1
    try:
        t4, _ = UP.cite(UP.render(P2))
        same = t4 == page
    except SystemExit:
        same = False
    check("4 page", same, "the page is exactly what update_page.py renders from the payload")

    # 5 static --------------------------------------------------------------------
    p5 = page.replace('<text class="val v2" ', '<text class="val v2" data-only="2" ', 1) if BREAK == "static" else page
    svgs = re.findall(r'<svg class="f-(?:wide|phone) funnel".*?</svg>', p5, flags=re.S)
    ok = len(svgs) == 2
    for s in svgs:
        rows = re.findall(r'<g class="row .*?</g>', s, flags=re.S)
        ok = ok and len(rows) == 6
        for r in rows:
            ok = ok and bool(re.search(r'class="val v0" data-only="0"', r)) and \
                bool(re.search(r'class="val v1" data-only="1"', r)) and \
                bool(re.search(r'class="val v2" x=', r))
    check("5 static", ok, "both drawings: six rows, final value visible without JS, stage values hidden")

    # 6 fits ----------------------------------------------------------------------
    widths = (900, 300) if BREAK == "fits" else (900, 320)
    bad = [b for w in widths for b in UP.fits(P, w)]
    check("6 fits", not bad, f"labels and values clear at {widths} px" + (f": {bad}" if bad else ""))

    # 7 names ---------------------------------------------------------------------
    T = page_text()
    t7 = T + (" write to someone@example.com" if BREAK == "names" else "")
    words = {w.lower() for w in re.findall(r"[A-Za-z]+", t7)}
    emp = any(hashlib.sha1(w.encode()).hexdigest() == EMPLOYER_SHA1 for w in words)
    mail = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", t7)
    check("7 names", not emp and not mail, "no email address and not the employer")

    # 8 register ------------------------------------------------------------------
    # the prose only: author initials in the Sources list ("Cetinic I") are not first person
    t8 = page_text(re.sub(r'<ol class="refs">.*?</ol>', " ", page, flags=re.S))
    t8 += " studies show it" if BREAK == "register" else ""
    banned = ["studies show", "experts agree", "game-changing", "revolutionary", "unprecedented", "miracle",
              "silver bullet", "very", "extremely", "incredibly", "had been", "updated", "v2", "per cent",
              "I", "my", "me"]
    hit = [w for w in banned if re.search(r"\b" + re.escape(w) + r"\b", t8, 0 if w in ("I",) else re.I)]
    check("8 register", not hit, "none of the ruled-out words" + (f"; found {hit}" if hit else ""))

    print(f"{len(fails)} failure(s)" + (f" (--break {BREAK})" if BREAK else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
