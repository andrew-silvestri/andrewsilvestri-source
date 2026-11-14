"""The space-depression page (space-depression.html)'s own failure modes. Each check has a --break that reproduces
the fault it names, and the run must exit 1 under it (HANDOFF traps 17, 26). Checks recompute from the raw files
through sources.py, not from the payload they are checking (trap 20).

 1. counts    Person-flights, people and person-years recomputed from McDowell's tables match the payload, and
              suborbital hops are out. --break counts keeps the suborbital hops.
 2. moon      Every flight flagged deep space is under 14 days and there are 28 such people (Apollo and
              Artemis II). --break moon counts every flight of a ship named Apollo, which adds Skylab and
              Apollo-Soyuz crews.
 3. delay     Mars one-way light time recomputed from Horizons spans the payload's minimum and maximum, and equals
              range over the speed of light. --break delay doubles it (a round trip).
 4. calc      The page's one calculation: four crew x 916 days / 365.25 = the payload's person-years, and its
              ratio to all time beyond Earth orbit. --break calc uses six crew.
 5. facts     Every quoted figure is matched in its source, and the value the page prints is the matched one.
              --break facts changes Barger's 6.09 hours to 6.9.
 6. page      The page is exactly what update_page.py renders. --break page moves one figure.
 7. nojs      The shipped page shows everything: no element carries the live-only class "off".
              --break nojs adds one.
 8. steps     Six step cards (0-5), and every data-o in the map names one of them. --break steps gives the Mars
              box step 6.
 9. words     None of the words the house style and the neutral register exclude appears in the page text.
              --break words writes "very" into the text read.
10. quotes    Each quotation is in its source, on the page, and under 15 words. --break quotes alters one word.
11. names     The internship employer is not named and no email address appears. --break names writes one.

Each --break was run on 2026-11-13 and exited 1; the clean run exits 0.

Run:  python test_space_depression.py [--break counts|moon|delay|calc|facts|page|nojs|steps|words|quotes|names]
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
sys.path.insert(0, ROOT)
import sources as S          # noqa: E402

BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
PAGE = os.path.join(ROOT, "site", "space-depression.html")
# the internship employer, by the SHA-1 of its lower-cased name (the name may not appear in this tree)
EMPLOYER_SHA1 = "c0446e86c1b75316d035502707018d75dd2fc688"
BANNED = ["very", "extremely", "incredibly", "Furthermore", "Additionally", "Moreover", "studies show",
          "experts agree", "game-changing", "revolutionary", "unprecedented", "boom", "crisis", "strain", "bubble",
          "glut", "had been", "used to be", "per cent", "It is important to note"]
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
    st = P["stats"]
    # 1 counts
    hdr, lines = S._tsv("mcd_rides.tsv")
    rows = []
    for ln in lines:
        if ln.startswith("# Chimp"):
            break
        if not ln.startswith("#") and ln.strip():
            rows.append(dict(zip(hdr, [x.strip() for x in ln.split("\t")])))
    mh, ml = S._tsv("mcd_missions.tsv")
    M = {r["HSFID"]: r for r in (dict(zip(mh, [x.strip() for x in ln.split("\t")])) for ln in ml
                                 if not ln.startswith("#") and ln.strip())}
    keep = [r for r in rows if BREAK == "counts" or not M[r["HSFID"]]["OrbID"].startswith("SO")]
    pd = sum(S._dur(r["Duration"])[0] for r in keep)
    ok = len(keep) == st["n_rides"] and len({r["ID"] for r in keep}) == st["n_people"] \
        and abs(pd / 365.25 - st["py_total"]) < 0.01
    check("1 counts", ok, f"{len(keep):,} person-flights, {len({r['ID'] for r in keep})} people, "
                          f"{pd / 365.25:.2f} person-years")
    # 2 moon
    if BREAK == "moon":
        deep = [r for r in keep if "Apollo" in r["Mission"] or "Apollo" in M[r["HSFID"]].get("Ship", "")]
    else:
        deep = [r for r in keep if M[r["HSFID"]]["DS"] not in ("", "-", "0")]
    days = [S._dur(r["Duration"])[0] for r in deep]
    ok = max(days) < 14 and len({r["ID"] for r in deep}) == 28 == st["n_people_moon"] and len(deep) == st["n_moon"]
    check("2 moon", ok, f"{len(deep)} flights beyond Earth orbit by {len({r['ID'] for r in deep})} people, "
                        f"longest {max(days):.1f} days")
    # 3 delay
    mars = S.horizons("horizons_mars.txt")
    k = 2 if BREAK == "delay" else 1
    lo, hi = min(m[1] for m in mars) * k, max(m[1] for m in mars) * k
    t = S.verified("horizons_mars.txt")[0].read_text(encoding="utf-8")
    first = t[t.index("$$SOE") + 5:].strip().splitlines()[0].split(",")
    c_ok = abs(float(first[3]) * 149597870.7 / 299792.458 / 60 * k / float(first[5]) - 1) < 1e-3
    ok = abs(lo - P["delay"]["mars"]["lo"]["min"]) < 0.01 and abs(hi - P["delay"]["mars"]["hi"]["min"]) < 0.01 and c_ok
    check("3 delay", ok, f"Mars one-way light time {lo:.2f} to {hi:.2f} minutes")
    # 4 calc
    f = S.facts()
    crew = 6 if BREAK == "calc" else int({"four": 4}[f["arch_four"]])
    py = crew * f["dra_916"] / 365.25
    x = py / st["py_moon"]
    shown = f"{crew * f['dra_916']:,} person-days, and {crew * f['dra_916']:,} divided by 365.25 is {py:.1f} person-years"
    ok = abs(py - P["mars_crew"]["py_min"]) < 0.01 and f"about {x:.0f} times" in page_text(raw) and shown in page_text(raw)
    check("4 calc", ok, f"{crew} x {f['dra_916']} / 365.25 = {py:.2f} person-years, {x:.1f} times all time beyond orbit")
    # 5 facts
    f5 = dict(f)
    if BREAK == "facts":
        f5["barger_iss_h"] = 6.9
    bad = [k for k in f5 if k not in P["facts"] or (f5[k] != P["facts"][k] and k != "pal_men")]
    T = page_text(raw)
    on_page = all(s in T for s in (f"{f5['barger_iss_h']:.2f} hours", f"{f5['m500_period']:.2f} hours",
                                   f"{f5['pal_weighted']:.1f} percent", f"{f5['nsduh_mde']:.1f} percent"))
    check("5 facts", not bad and on_page, f"{len(f)} figures matched in their sources and printed as matched"
                                          + (f"; differ {bad}" if bad else ""))
    # 6 page
    import update_page as UP
    r = UP.render(P)
    r, _ = UP.cite(r)
    if BREAK == "page":
        r = r.replace(f"{st['n_gt180']} flights", f"{st['n_gt180'] + 1} flights", 1)
    check("6 page", r == raw, "the page is exactly what update_page.py renders")
    # 7 nojs
    r7 = raw.replace('class="dots d-long"', 'class="dots d-long off"', 1) if BREAK == "nojs" else raw
    fig = re.search(r'<figure class="evmap.*?</figure>', r7, re.S).group(0)
    offs = re.findall(r'class="[^"]*\boff\b[^"]*"', fig)
    check("7 nojs", not offs, "nothing in the map is hidden in the shipped markup" + (f"; {offs[:2]}" if offs else ""))
    # 8 steps
    steps = sorted(int(s) for s in re.findall(r'class="step" data-step="(\d)"', fig))
    os_ = {int(o) for o in re.findall(r'data-o="(\d+)"', fig)}
    if BREAK == "steps":
        os_.add(6)
    check("8 steps", steps == [0, 1, 2, 3, 4, 5] and os_ <= set(steps), f"step cards {steps}; data-o {sorted(os_)}")
    # 9 words
    T9 = T + (" a very long stay" if BREAK == "words" else "")
    hit = [w for w in BANNED if re.search(r"\b" + re.escape(w) + r"\b", T9, flags=re.I if w[0].islower() else 0)]
    check("9 words", not hit, "no excluded word in the page text" + (f"; found {hit}" if hit else ""))
    # 10 quotes
    qs = {"q_hib": ("sandal2018.html", f["sandal_hib"]), "q_underest": ("hsrb_rr.pdf", f["rr_underest"])}
    bad = []
    for k, (src, q) in qs.items():
        q2 = q.replace("hibernation", "sleep") if BREAK == "quotes" and k == "q_hib" else q
        if q2 not in S.flat(src) or q2 not in T or len(q2.split()) >= 15:
            bad.append(k)
    check("10 quotes", not bad, "every quotation is in its source, on the page, under 15 words" + (f"; {bad}" if bad else ""))
    # 11 names
    T11 = T + (" write to someone@example.com" if BREAK == "names" else "")
    low = T11.lower()
    emp = any(hashlib.sha1(w.encode()).hexdigest() == EMPLOYER_SHA1 for w in set(re.findall(r"[a-z]+", low)))
    mail = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", raw + (" someone@example.com" if BREAK == "names" else ""))
    check("11 names", not emp and not mail, "no employer named and no email address" + (f"; {mail.group(0)}" if mail else ""))
    print(f"{len(fails)} failure(s)" + (f" (--break {BREAK})" if BREAK else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
