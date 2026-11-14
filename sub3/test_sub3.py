"""The sub-3 page (sub3.html)'s own failure modes. Each check names a likely way the page goes wrong unseen; each
has a --break that reproduces that fault, and the run must exit 1 under it (HANDOFF traps 17, 26, 38). Checks 1 to
3 recompute from the raw files with code written here, not from the payload they check (trap 20); without the raw
files (a fresh clone: data/raw is gitignored) they report SKIP, and fetch_public.py restores them.

 1. band      The halfway window's count and success rate, recomputed from the results file with the csv module.
              --break band reads the window 30 seconds late.
 2. years     The 2024 and 2025 success rates the standfirst uses. --break years reads 2025 as 2024.
 3. weather   The race-morning temperatures of 2024 and 2025 from the DWD zip, local 09:00-13:00 = 07-11 UTC.
              --break weather reads the stamps as local time.
 4. hero      The hero's bars add up to the window's count, and each light is a subset of its bar.
              --break hero drops the tail bin.
 5. claims    update_page.claims() accepts the shipped payload. --break claims moves 2024's rate below half.
 6. page      The page equals what update_page.py renders from the payload. --break page moves one figure.
 7. private   The payload holds no runner's name: every string in it is a label this test knows.
              --break private writes a name-shaped string into it.
 8. names     No email address and not the internship employer (checked by the SHA-1 of each word).
              --break names writes an address into the text read.
 9. register  None of the words the house rules exclude, and no "had been" (test_retro). --break register writes
              one into the text read.

Run:  python test_sub3.py [--break band|years|weather|hero|claims|page|private|names|register]
"""
import csv
import hashlib
import html
import io
import json
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import update_page as UP   # noqa: E402

BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
RAW = os.path.join(HERE, "data", "raw", "berlin_1999_2025.csv")
DWD = os.path.join(HERE, "data", "raw", "stundenwerte_TU_00433_19510101_20251231_hist.zip")
EMPLOYER_SHA1 = "c0446e86c1b75316d035502707018d75dd2fc688"   # lower-cased name; the name itself is not in the tree
fails = []


def check(name, ok, detail):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def skip(name, why):
    print(f"  SKIP {name}: {why}")


def secs(s):
    try:
        h, m, x = s.split(":")
        v = int(h) * 3600 + int(m) * 60 + int(x)
        return v if v > 0 else None
    except (ValueError, AttributeError):
        return None


def page_text(t):
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", t, flags=re.S)
    t = re.sub(r'<sup class="cite".*?</sup>', "", t, flags=re.S)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    B = P["band"]

    # 1 band, 2 years ------------------------------------------------------------
    if os.path.exists(RAW):
        lo, hi = (5340, 5430) if BREAK == "band" else (5310, 5400)
        n = k = 0
        by = {}
        with open(RAW, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f, delimiter=";"):
                h, fin = secs(row["half"]), secs(row["final"])
                if h is None or fin is None or fin <= h or not lo <= h < hi:
                    continue
                n += 1
                k += fin < 10800
                y = int(row["year"])
                c = by.setdefault(y, [0, 0])
                c[0] += 1
                c[1] += fin < 10800
        check("1 band", n == B["n"] and k == B["sub3"],
              f"{n:,} runners in the window, {k:,} under 3:00 (payload {B['n']:,}, {B['sub3']:,})")
        Y = {x["year"]: x for x in B["by_year"]}
        y25 = by[2024] if BREAK == "years" else by[2025]
        ok = all(abs(100 * c[1] / c[0] - Y[y]["share"]) < 0.001 for y, c in ((2024, by[2024]), (2025, y25)))
        check("2 years", ok, f"2024 {100 * by[2024][1] / by[2024][0]:.1f} percent, 2025 {100 * y25[1] / y25[0]:.1f} percent")
    else:
        skip("1 band", "no raw results file (python fetch_public.py)")
        skip("2 years", "no raw results file")

    # 3 weather ------------------------------------------------------------------
    if os.path.exists(DWD):
        z = zipfile.ZipFile(DWD)
        name = next(x for x in z.namelist() if x.startswith("produkt_tu_stunde"))
        want = {"2024092907", "2024092908", "2024092909", "2024092910", "2024092911",
                "2025092107", "2025092108", "2025092109", "2025092110", "2025092111"}
        if BREAK == "weather":
            want = {w[:8] + "%02d" % (int(w[8:]) + 2) for w in want}
        temps = {}
        for row in csv.reader(io.StringIO(z.read(name).decode("latin-1")), delimiter=";"):
            if len(row) > 3 and row[1].strip() in want:
                temps.setdefault(row[1].strip()[:4], []).append(float(row[3]))
        W = {w["year"]: w["temp"] for w in P["weather"]["years"]}
        got = {y: round(sum(v) / len(v), 2) for y, v in temps.items()}
        ok = all(len(temps.get(str(y), [])) == 5 and abs(got[str(y)] - W[y]) < 0.006 for y in (2024, 2025))
        check("3 weather", ok, f"2024 {got.get('2024')} C, 2025 {got.get('2025')} C (payload {W[2024]}, {W[2025]})")
    else:
        skip("3 weather", "no DWD zip (python fetch_public.py)")

    # 4 hero ---------------------------------------------------------------------
    spec = UP.hero_spec(P)
    bins = spec["bins"][:-1] if BREAK == "hero" else spec["bins"]
    tot = sum(b["n"] for b in bins)
    subset = all(b[l["key"]] <= b["n"] for b in spec["bins"] for l in spec["lights"])
    check("4 hero", tot == B["n"] and subset, f"bars sum to {tot:,} (window {B['n']:,}); lights within bars: {subset}")

    # 5 claims -------------------------------------------------------------------
    P5 = json.loads(json.dumps(P))
    if BREAK == "claims":
        next(x for x in P5["band"]["by_year"] if x["year"] == 2024)["share"] = 45.0
    try:
        UP.claims(P5, {})
        ok = True
    except SystemExit as e:
        ok = False
        print("       " + str(e).replace("\n", "\n       "))
    check("5 claims", ok, "every direction the template commits to holds in the payload")

    # 6 page ---------------------------------------------------------------------
    P6 = json.loads(json.dumps(P))
    if BREAK == "page":
        P6["near"]["half_under_90"] += 5
    shipped = open(UP.PAGE, "rb").read().decode("utf-8")
    try:
        t, _ = UP.cite(UP.render(P6))
        same = t == shipped
    except SystemExit:
        same = False
    check("6 page", same, "the page is exactly what update_page.py renders from the payload")

    # 7 private ------------------------------------------------------------------
    P7 = json.loads(json.dumps(P))
    if BREAK == "private":
        P7["slowdown"][0]["label"] = "Mustermann, Erika"
    allowed = {"made", "missed", "under 3:00", "3:00 to 3:29", "3:30 to 3:59", "4:00 to 4:29", "4:30 to 4:59",
               "5:00 or more"}
    strings = []

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                strings.append(k)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str):
            strings.append(x)
    walk(P7)
    odd = [s for s in strings if s not in allowed and not re.fullmatch(r"[a-z0-9_]+|\d{4}|[MW]", s)]
    check("7 private", not odd, "every string in the payload is a key or a known label" + (f"; found {odd}" if odd else ""))

    # 8 names, 9 register -----------------------------------------------------------
    T = page_text(shipped)
    t8 = T + (" write to someone@example.com" if BREAK == "names" else "")
    words = {w.lower() for w in re.findall(r"[A-Za-z]+", t8)}
    emp = any(hashlib.sha1(w.encode()).hexdigest() == EMPLOYER_SHA1 for w in words)
    mail = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", t8)
    check("8 names", not emp and not mail, "no email address and not the employer")
    t9 = T + (" a crisis" if BREAK == "register" else "")
    hit = [w for w in ("boom", "crisis", "strain", "bubble", "glut", "had been") if re.search(r"\b" + w + r"\b", t9, re.I)]
    check("9 register", not hit, "none of the ruled-out words" + (f"; found {hit}" if hit else ""))

    print(f"{len(fails)} failure(s)" + (f" (--break {BREAK})" if BREAK else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
