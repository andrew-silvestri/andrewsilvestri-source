"""Checks for the R5 repair of the longevity page (D-28).

    python test_lq.py                    every check; exit 1 on any failure
    python test_lq.py --break fallback   amphibians lose the global fallback
    python test_lq.py --break effort     the study-effort rescaling is skipped
    python test_lq.py --break dropped    the thin-effort records are kept in
    python test_lq.py --break page       a Limits figure on the page is stale
    python test_lq.py --break rail       the margin rail is put back

Each --break replays the fault the check exists for and must exit 1.

1. fallback: every order of four or more A/B species has a group quotient, and
   the amphibian orders are scored against the global fit. The historical
   fault: Anura and Urodela had a blank quotient, so "81 orders" was 83 less
   the two the page said fell back (QA 2026-10-22, D-28 item 2).
2. effort: the effort-corrected run reproduces the audit's V3/family figures
   (qa-audit/lq_rev_rerun_out.txt, run by QA with its own script): birds
   against mammals 1.79, mammal at 1 kg 13.6 yr, mammal slope 0.190, human
   4.13, Brandt's bat 7.76, naked mole-rat 4.32. Recomputed here from the raw
   data, not read from summary.json. The cruder bound (V2, thin-effort
   records left out) reproduces the audit's 1.45, 0.120, human 4.30, Brandt's
   bat 4.30, naked mole-rat 2.68, bats 1.48.
3. page: every figure in the page's Limits table, h1 and standfirst is the
   one in summary.json, so a build that moves a figure cannot leave the page
   behind.
4. rail: no margin rail on the page (_INSIGHT rule 4).
"""
import argparse
import contextlib
import io
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PAGE = os.environ.get("LQ_PAGE") or os.path.join(HERE, "..", "site", "longevity.html")
SUMMARY = os.path.join(HERE, "outputs", "summary.json")

FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  FAIL  ") + msg)
    if not ok:
        FAIL.append(msg)


def main(brk=None):
    with contextlib.redirect_stdout(io.StringIO()):
        import build_lq as B
    if brk == "fallback":
        B.own_lq = lambda r, metric="maximum": r["lq_class_" + metric]

    # 1 and 2 share one load of the raw merge
    with contextlib.redirect_stdout(io.StringIO()):
        rows = B.load(B.DATA)
        B.demote_outliers(rows)
        fit_rows = [r for r in rows if B.in_fit(r)]
        B.score(rows, fit_rows)
        groups = B.rank_summary([r for r in rows if r["quality"] != "C"])
    orders = [g for g in groups["order"] if g["n"] >= 4]
    blank = [g["group"] for g in orders if not g["geo_lq"]]
    check(not blank, f"fallback: every order of 4+ species has a quotient "
                     f"({len(orders)} orders; blank: {blank or 'none'})")
    by = {g["group"]: g for g in orders}
    for k in ("Urodela", "Anura"):
        g = by.get(k)
        check(bool(g and g["geo_lq"] and g["baseline"] == "global"),
              f"fallback: {k} scored against the global fit "
              f"({g and g['geo_lq'] and round(g['geo_lq'], 2)}, "
              f"{g and g['baseline']})")

    if brk == "effort":
        B.effort_offsets = lambda rows, fe=B.EFFORT_FE: {}
    if brk == "dropped":
        B.THIN_EFFORT = ()
    with contextlib.redirect_stdout(io.StringIO()):
        full = B.effort_check()
    ec, dr = full["corrected"], full["dropped"]
    want = [("birds vs mammals at 1 kg", ec["bird_mammal_1kg"], 1.79, .005),
            ("mammal at 1 kg, yr", ec["mammal_1kg_yr"], 13.6, .05),
            ("mammal slope", ec["mammal_b"], .190, .0005),
            ("human", ec["species"]["Human"], 4.13, .005),
            ("Brandt's bat", ec["species"]["Brandt's bat"], 7.76, .005),
            ("naked mole-rat", ec["species"]["Naked mole-rat"], 4.32, .005)]
    bats = {o[0]: o[1] for o in dr["orders"]}.get("Chiroptera", 0)
    want += [("dropped: birds vs mammals", dr["bird_mammal_1kg"], 1.45, .005),
             ("dropped: mammal slope", dr["mammal_b"], .120, .0005),
             ("dropped: human", dr["species"]["Human"], 4.30, .005),
             ("dropped: Brandt's bat", dr["species"]["Brandt's bat"], 4.30, .005),
             ("dropped: naked mole-rat", dr["species"]["Naked mole-rat"], 2.68, .005),
             ("dropped: bats", bats, 1.48, .005)]
    for name, got, ref, tol in want:
        check(abs(got - ref) <= tol,
              f"effort: {name} {got:.3f} against the audit's {ref}")

    # 3: the page against summary.json
    s = json.load(open(SUMMARY, encoding="utf-8"))
    t = open(PAGE, encoding="utf-8").read()
    if brk == "page":
        t = t.replace("<td>4.1&times;</td>", "<td>5.0&times;</td>", 1)
        t = t.replace("bats come to 2.4", "bats come to 2.5", 1)
    ec_s = s["effort_check"]
    runs = (s["headline"], ec_s["corrected"], ec_s["dropped"])
    lim = t[t.index("<h2>Limits</h2>"):t.index("<h2>The code</h2>")]
    cells = re.findall(r"<tr><td>([^<]+)</td><td>([^<]+)</td><td>([^<]+)"
                       r"</td><td>([^<]+)</td></tr>", lim)
    cell = {a.split(" (")[0]: (b, d, f) for a, b, d, f in cells}
    for sp in ("Human", "Brandt's bat", "Naked mole-rat"):
        got = cell.get(sp, ("",) * 3)
        check(got == tuple(f"{x['species'][sp]:.1f}&times;" for x in runs),
              f"page: Limits row {sp} {' / '.join(got)}")
    got = cell.get("Birds against mammals of equal mass", ("",) * 3)
    check(got == tuple(f"{x['bird_mammal_1kg']:.1f}&times;" for x in runs),
          f"page: Limits row birds vs mammals {' / '.join(got)}")
    sf = re.search(r'<p class="dim">(.*?)</p>', t, re.S).group(1)
    o = [{q[0]: q[1] for q in x["orders"]} for x in runs]
    for k, v in (("pooled", o[0]["Chiroptera"]), ("corrected", o[1]["Chiroptera"]),
                 ("dropped", o[2]["Chiroptera"])):
        check(f"{v:.1f}" in sf, f"page: standfirst carries bats {k} {v:.1f}")
    allv = [x[k] for x in o for k in ("Chiroptera", "Primates") if k in x]
    lo, hi = min(allv), max(allv)
    halves = {1.5: "one and a half", 2.0: "two", 2.5: "two and a half"}
    span = f"{halves[round(lo * 2) / 2]} to {halves[round(hi * 2) / 2]}"
    # the claim the h1 once carried now leads the standfirst
    check(sf.startswith(f"Bats and primates live {span} times"),
          f"page: standfirst span '{span}' matches {lo:.2f} to {hi:.2f}")
    gall = [x["Galliformes"] for x in o]
    check("their kin, half as long." in sf
          and all(.45 <= v < .55 for v in gall),
          f"page: standfirst 'half' for Galliformes {[round(v, 2) for v in gall]}")

    # 4
    if brk == "rail":
        t = t.replace("<main class=\"notes\">",
                      "<main class=\"notes\">\n<aside class=\"marginalia long\">"
                      "<b>Brandt's bat</b>11.87&times; prediction</aside>", 1)
    check("marginalia" not in t and "Species in the margin" not in t,
          "rail: no margin rail on the page")

    print(f"\n{len(FAIL)} failure(s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--break", dest="brk",
                    choices=["fallback", "effort", "dropped", "page", "rail"])
    raise SystemExit(main(ap.parse_args().brk))
