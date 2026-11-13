"""The messaging page (messaging.html)'s own failure modes. Each check has a --break that reproduces the fault it
names, and the run must exit 1 under it (HANDOFF traps 17, 26, 38). Checks recompute from the tracked tables and
the hash-checked raw file, not from the payload they are checking (trap 20).

 1. rows      Every field trial's two shares differ by its printed effect, to 0.5 points, and the payload carries
              the printed effect. --break rows swaps one trial's two shares.
 2. tournament  The tree-task effects, recomputed from the raw deposit with country fixed effects, equal the
              payload's to 0.005 pages and the paper's Table S4 to 0.06. --break tournament drops the fixed
              effects (a plain difference of means).
 3. md5       The tournament file is the one on Zenodo: its MD5 equals the checksum in Zenodo's record.
              --break md5 changes one character of the expected checksum.
 4. page      The page is exactly what update_page.py renders. --break page moves one figure.
 5. nojs      The shipped page draws every row: no element carries the live-only classes "off" or "is-live".
              --break nojs adds one.
 6. split     Every trial that changes words moved the share by less than every trial that changes the choice,
              the split the headline rests on. --break split gives one words trial a 10-point effect.
 7. kit       Every kit row has a grade A, B or C and no unfilled {placeholder}. --break kit leaves one.
 8. cited     Every trial in the hero chart has a source in add_citations.PAGES["messaging.html"], matched by the
              first author's surname. --break cited drops one source.

Run:  python test_messaging.py [--break rows|tournament|md5|page|nojs|split|kit|cited]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import sources as S  # noqa: E402

BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
PAGE = os.path.join(ROOT, "site", "messaging.html")
fails = []


def check(name, ok, detail):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    pay = {r["id"]: r for r in P["effects"]}
    # 1 rows
    rows = S.table("effects.csv")
    if BREAK == "rows":
        rows[0]["baseline"], rows[0]["treated"] = rows[0]["treated"], rows[0]["baseline"]
    bad = [r["id"] for r in rows
           if abs(float(r["treated"]) - float(r["baseline"]) - float(r["printed_effect"])) > 0.5
           or abs(pay[r["id"]]["effect"] - float(r["printed_effect"])) > 1e-9
           or abs(pay[r["id"]]["treated"] - float(r["treated"])) > 1e-9]
    check("1 rows", not bad, f"{len(rows)} trials; shares that disagree with the printed effect: {bad or 'none'}")
    # 2 tournament
    import build_messaging as B
    t = S.tournament()
    est = B.ols_fe(t, "wept")["arms"]
    if BREAK == "tournament":                       # a plain difference of means, no country effects
        mean = lambda c: sum(float(r["wept"]) for r in t if r["cond"] == c) / sum(r["cond"] == c for r in t)  # noqa: E731
        est = {a: {"est": mean(a) - mean("Control")} for a in B.ARMS}
    off = {a: round(est[a]["est"], 3) for a in B.ARMS
           if abs(est[a]["est"] - P["tournament"]["wept"]["arms"][a]["est"]) > 0.005
           or abs(est[a]["est"] - B.PAPER_S4[a]) > B.S4_TOL}
    check("2 tournament", not off, f"11 tree-task effects recomputed from data63.xlsx; off: {off or 'none'}")
    # 3 md5
    import fetch_public as F
    want = F.zenodo_md5("data63.xlsx")
    if BREAK == "md5":
        want = ("0" if want[0] != "0" else "1") + want[1:]
    got = F.md5(S.RAW / "data63.xlsx")
    check("3 md5", want == got, f"data63.xlsx {got} against Zenodo's {want}")
    # 4 page
    import update_page as U
    text, _ = U.cite(U.render(P))
    shipped = open(PAGE, "rb").read().decode("utf-8")
    if BREAK == "page":
        shipped = shipped.replace(f"{pay['ebeling']['treated']:.1f} percent", "70.1 percent", 1)
    check("4 page", text == shipped, "site/messaging.html is what update_page.py renders")
    # 5 nojs
    if BREAK == "nojs":
        shipped = shipped.replace('class="row d"', 'class="row d off"', 1)
    live = re.findall(r'class="[^"]*\b(off|is-live|now)\b[^"]*"', shipped)
    check("5 nojs", not live, f"live-only classes in the shipped page: {live or 'none'}")
    # 6 split
    eff = [dict(r) for r in rows] if BREAK != "rows" else S.table("effects.csv")
    if BREAK == "split":
        [r for r in eff if r["group"] == "words"][0]["printed_effect"] = "10"
    words = [float(r["printed_effect"]) for r in eff if r["group"] == "words"]
    design = [float(r["printed_effect"]) for r in eff if r["group"] != "words"]
    check("6 split", max(words) < 2 <= min(design), f"words at most {max(words)}, choice changes at least {min(design)}")
    # 7 kit
    kit = P["kit"]
    if BREAK == "kit":
        kit = [dict(kit[0], effect=kit[0]["effect"] + " {menu_lo}")] + kit[1:]
    badk = [k["id"] for k in kit if k["grade"] not in ("A", "B", "C") or re.search(r"\{\w+\}", k["effect"])]
    check("7 kit", not badk, f"{len(kit)} rows; bad: {badk or 'none'}")
    # 8 cited
    import add_citations
    srcs = [s for _, s, _ in add_citations.PAGES["messaging.html"][1:]]
    if BREAK == "cited":
        srcs = [s for s in srcs if "Ebeling" not in s]
    import html
    import unicodedata

    def fold(x):
        return unicodedata.normalize("NFKD", html.unescape(x)).encode("ascii", "ignore").decode()
    plain = [fold(s) for s in srcs]
    missing = [r["id"] for r in rows if not any(fold(r["cite"].split()[0]) in p for p in plain)]
    check("8 cited", not missing, f"hero trials without a source: {missing or 'none'}")


if __name__ == "__main__":
    main()
    print(f"{'FAIL' if fails else 'OK'}: {len(fails)} failed" + (f" ({', '.join(fails)})" if fails else ""))
    sys.exit(1 if fails else 0)
