"""The scales page (scales.html)'s own failure modes. Each check has a --break that reproduces the fault it names,
and the run must exit 1 under it (HANDOFF traps 17, 26, 38). Checks recompute from the raw files through
sources.py, not from the payload they are checking (trap 20).

 1. sun       The Sun's W/kg is the IAU nominal luminosity over GM/G, read from the IAU paper's text, and it is
              the payload's. --break sun takes the luminosity in erg/s (x 1e7).
 2. human     The reference adult is the 70 kg Homo sapiens row of Hatton's table, at about 1.2 W/kg.
              --break human divides by the mass in grams.
 3. birds     Birds are not temperature-corrected and keep each species' lowest value: their geometric mean
              W/kg, recomputed from the raw CSV, is the payload's. --break birds averages instead of taking the
              lowest value.
 4. stars     Eker's calibration sample is the 509 rows marked "*", and every one gives off more power per
              kilogram than the lightest. --break stars uses all 586 rows.
 5. cities    The largest metro is New York's whole MSA (about 19.5 million), not one of its Metropolitan
              Divisions, and the county FIPS codes are five digits. --break cities reads a division too.
 6. fuel      World power per person is OWID's kWh a year over 8,766 hours. --break fuel uses 365 hours.
 7. page      The page is exactly what update_page.py renders. --break page moves one figure.
 8. steps     Every layer of the hero (data-o) has a step card, 0 to 5, in both drawings. --break steps adds a
              layer 6.
 9. nojs      The shipped page draws every layer: no element carries the live-only class "off".
              --break nojs adds one.
10. text      No SVG text is set below 12px. --break text sets one at 10px.
11. names     The internship employer is not named on the page. --break names checks a word that is there.

Run:  python test_scales.py [--break sun|human|birds|stars|cities|fuel|page|steps|nojs|text|names]
"""
import csv
import hashlib
import html
import json
import math
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
PAGE = os.path.join(ROOT, "site", "scales.html")
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
    # 1 sun
    t = S.flat("iau_2015_b3.pdf")
    L = float(re.search(r"1LN ⊙ = (\d\.\d+) × 1026 W", t).group(1)) * 1e26
    GM = float(re.search(r"= (\d\.\d{7}) × 1020 m3 s−2", t).group(1)) * 1e20
    if BREAK == "sun":
        L *= 1e7
    sun = L / (GM / 6.67430e-11)
    check("1 sun", abs(sun / P["stars"]["sun_wkg"] - 1) < 1e-9 and 1.9e-4 < sun < 1.95e-4, f"{sun:.4e} W/kg")
    # 2 human
    rows = S.metabolism()
    h = [r for r in rows if r["Species"] == "Homo sapiens" and float(r["Mass_g"]) == 70000][0]
    wkg = float(h["Metabolism_W"]) / (float(h["Mass_g"]) / (1 if BREAK == "human" else 1000))
    check("2 human", abs(wkg - P["life"]["human"]["wkg"]) < 1e-9 and 1.0 < wkg < 1.4, f"{wkg:.3f} W/kg")
    # 3 birds
    by = {}
    for r in rows:
        if r["Plot2"] == "7":
            by.setdefault(r["Species"], []).append((float(r["Metabolism_W"]), float(r["Mass_g"])))
    vals = []
    for sp, v in by.items():
        if sp == "Unknown":
            vals += [w / (m / 1000) for w, m in v]
        elif BREAK == "birds":
            vals.append(sum(w for w, _ in v) / len(v) / (sum(m for _, m in v) / len(v) / 1000))
        else:
            w, m = min(v)
            vals.append(w / (m / 1000))
    gm = math.exp(sum(math.log(x) for x in vals) / len(vals))
    check("3 birds", abs(gm / P["life"]["groups"]["birds"]["gmean_wkg"] - 1) < 1e-9,
          f"birds {gm:.3f} W/kg, payload {P['life']['groups']['birds']['gmean_wkg']:.3f}")
    # 4 stars
    st = S.stars()
    cal = st if BREAK == "stars" else [s for s in st if s[4].startswith("*")]
    check("4 stars", len(cal) == P["stars"]["n"] == 509 and len(P["stars"]["pts"]) <= 509,
          f"{len(cal)} stars used of {len(st)}")
    # 5 cities
    p, _ = S.verified("census_cbsa_2023.csv")
    crow = list(csv.DictReader(open(p, encoding="latin-1")))
    keep = ("Metropolitan Statistical Area", "Metropolitan Division") if BREAK == "cities" else \
        ("Metropolitan Statistical Area",)
    msa = {}
    for r in crow:
        if r["LSAD"] in keep:
            msa[r["CBSA"]] = (r["NAME"], float(r["POPESTIMATE2023"]))
    ny = msa["35620"]
    _, counties = S.msa_population(2023)
    five = all(len(f) == 5 for fs in counties.values() for f in fs)
    check("5 cities", ny[1] == P["cities"]["big"]["pop"] and 18e6 < ny[1] < 21e6 and five,
          f"{ny[0]}: {ny[1]:,.0f}; five-digit FIPS {five}")
    # 6 fuel
    E = S.energy_per_capita()["World"]
    y = max(E)
    w = E[y] * 1000 / (365 if BREAK == "fuel" else 8766)
    check("6 fuel", abs(w - P["fuel"]["world"]["w"]) < 1e-6 and 1500 < w < 3500, f"World {y}: {w:,.0f} W a person")
    # 7 page
    import update_page as UP
    t = UP.render(P)
    t, _ = UP.cite(t)
    if BREAK == "page":
        t = t.replace(f"{P['stars']['n']} stars", f"{P['stars']['n'] + 1} stars", 1)
    check("7 page", t == raw, "the page is exactly what update_page.py renders")
    # 8 steps
    fig = re.search(r'<figure class="ladder.*?</figure>', raw, re.S).group(0)
    if BREAK == "steps":
        fig = fig.replace('<g data-o="5">', '<g data-o="6">', 1)
    layers = sorted({int(x) for x in re.findall(r'data-o="(\d+)"', fig)})
    cards = sorted(int(x) for x in re.findall(r'class="step" data-step="(\d+)"', fig))
    per_svg = [sorted({int(x) for x in re.findall(r'data-o="(\d+)"', s)})
               for s in re.findall(r"<svg class=\"plot plot-.*?</svg>", fig, re.S)]
    check("8 steps", layers == cards == list(range(6)) and len(per_svg) == 2 and all(s == cards for s in per_svg),
          f"layers {layers}; cards {cards}")
    # 9 nojs
    f9 = fig.replace('<g data-o="1">', '<g data-o="1" class="off">', 1) if BREAK == "nojs" else fig
    offs = re.findall(r'class="[^"]*\boff\b[^"]*"', f9)
    check("9 nojs", not offs, "no layer is hidden in the shipped markup" + (f"; {offs[:2]}" if offs else ""))
    # 10 text
    r10 = raw.replace('font-size="12"', 'font-size="10"', 1) if BREAK == "text" else raw
    small = [s for s in re.findall(r'font-size="(\d+(?:\.\d+)?)"', r10) if float(s) < 12]
    check("10 text", not small, "no SVG text under 12px" + (f"; {small[:3]}" if small else ""))
    # 11 names
    T = page_text(raw).lower()
    target = hashlib.sha1(b"sun").hexdigest() if BREAK == "names" else EMPLOYER_SHA1
    emp = any(hashlib.sha1(w.encode()).hexdigest() == target for w in set(re.findall(r"[a-z]+", T)))
    check("11 names", not emp, "the employer is not named")
    print(f"{len(fails)} failure(s)" + (f" (--break {BREAK})" if BREAK else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
