"""The Uri page (uri.html, Q12)'s own failure modes. Each check exists because the fault it names happened while
the page was planned or built, or is the likeliest way it goes wrong unseen; each has a --break that reproduces
that fault, and the run must exit 1 under it (HANDOFF traps 17, 26, 38). Every check recomputes from the raw
filings through sources.py, not from the payload it is checking (trap 20).

 1. tx-wal      Texas interest and lives run from the closing date: the weighted average lives recomputed from
                the amortization schedule equal the official statement's 5.958 and 13.424. --break tx-wal
                measures from a month later.
 2. tx-balance  The schedule's balance at 12/31/2025 equals the issuer's report to the dollar. --break
                tx-balance drops one scheduled payment.
 3. ok-interest Every Oklahoma interest row is coupon x balance on 30/360. --break ok-interest uses actual/365.
 4. ok-charge   ONG's initial Choice A charge reproduces from its workpaper ($6.33). --break ok-charge takes
                Choice B's allocation share.
 5. tx-repay    What Texas customers repay nets the interest paid from the proceeds (charge $0.00 until
                October 2023) and the reserve applied to the last payment (plan review 4). --break tx-repay
                counts principal + all interest, the plan's original error.
 6. split       The split's parts are the costs approved, the interest, and the rest; they sum to what
                customers repay. --break split puts the prepaid interest in "issuing the bonds" too (the
                double count review 4 found in the plan's second visual).
 7. hero        The hero series, at sampled months, equals what is still scheduled, recomputed here; the band
                is never negative. --break hero recomputes Texas gross of the reserve.
 8. tx-home     A Texas home: the ten latest years' mean use, at EIA's 14.73 psia (review 3); the result is
                CenterPoint's stated $0.11362/Ccf. --break tx-home uses the latest year alone (the plan's
                $3.50, the review's most-likely-wrong assumption).
 9. suo-cert    Summit's schedule after the October 1, 2026 payment equals its servicer's certificate.
                --break suo-cert reads the balance one row early.
10. quotes      Every quotation on the page is in its source file. --break quotes alters one.
11. page        The page equals what update_page.py renders from the payload. --break page moves one payload
                figure.
12. labels      The page carries its own qualifiers: "as scheduled", "Scheduled, not measured", "a home on the
                system for the whole term", "approximations", the West Texas footnote, SB 30. --break labels
                removes "Scheduled, not measured".
13. register    No word the packet rules out ("crisis", "boom", "strain", "bubble", "gouging", "profiteering",
                "windfall") in the page's own words. --break register writes one into the text read.

Run:  python test_uri.py [--break tx-wal|tx-balance|ok-interest|ok-charge|tx-repay|split|hero|tx-home|
                          suo-cert|quotes|page|labels|register]
"""
import datetime as dt
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import model as M          # noqa: E402
import sources as S        # noqa: E402

BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
PAGE = os.path.join(ROOT, "site", "uri.html")
fails = []


def check(name, ok, detail):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


def page_text():
    t = open(PAGE, encoding="utf-8").read()
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r'<sup class="cite".*?</sup>', "", t, flags=re.S)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))


def main():
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    B = S.tx_bonds()
    # 1 tx-wal ------------------------------------------------------------------
    close = B["closing"] + (dt.timedelta(days=31) if BREAK == "tx-wal" else dt.timedelta(0))
    bad = []
    for k, t in B["tranches"].items():
        w = M.wal([(r["date"], r[k]) for r in B["schedule"]], close)
        if round(w, 3) != t["wal_stated"]:
            bad.append(f"{k} {w:.4f} vs {t['wal_stated']}")
    check("1 tx-wal", not bad, "lives from the closing date equal the stated ones" + (f": {bad}" if bad else ""))
    # 2 tx-balance --------------------------------------------------------------
    O = S.tx_outstanding()
    sched = B["schedule"][:3] + B["schedule"][4:] if BREAK == "tx-balance" else B["schedule"]
    bad = []
    for k in ("A-1", "A-2"):
        left = B["tranches"][k]["principal"] - sum(r[k] for r in sched if r["date"] <= O["as_of"])
        if abs(left - O[k]) >= 1:
            bad.append(f"{k} {left:,.0f} vs {O[k]:,.0f}")
    check("2 tx-balance", not bad, f"schedule at {O['as_of']} equals the issuer's report" + (f": {bad}" if bad else ""))
    # 3 ok-interest -------------------------------------------------------------
    worst = 0.0
    for u in ("ong", "suo"):
        b = S.ok_bonds(u)
        for k, rows in b["schedule"].items():
            c = b["tranches"][k]["coupon"]
            for a, r in zip(rows, rows[1:]):
                days = (r["date"] - a["date"]).days / 365 if BREAK == "ok-interest" else M.d360(a["date"], r["date"]) / 360
                worst = max(worst, abs(a["balance"] * c * days - r["interest"]))
    check("3 ok-interest", worst < 0.02, f"every interest row reproduced to ${worst:.4f}")
    # 4 ok-charge ---------------------------------------------------------------
    ch = S.ok_charges("ong")["classes"]
    wp = S.flat("ok_ong_ial.pdf", 16)
    req = S.money(re.search(r"\$([\d,]+) Agrees to Issuance Advice Letter", wp).group(1))
    n = int(re.search(r"Choice A .*? 206,467 ([\d,]+) 13\.84%", wp).group(1).replace(",", ""))
    alloc = ch["B" if BREAK == "ok-charge" else "A"]["alloc"]
    check("4 ok-charge", round(req * alloc / n, 2) == ch["A"]["initial"],
          f"${req:,.0f} x {alloc:.4f} / {n:,} = ${req * alloc / n:.4f}; filed ${ch['A']['initial']}")
    # 5 tx-repay ----------------------------------------------------------------
    U = S.tx_upfront()
    TXP = M.payments("TX")
    first = dt.date(2023, 10, 1)
    assert "zero dollars ($0.00) per Mcf through September 2023" in U["zero_until"]
    pre = sum(p["interest"] for p in TXP if p["date"] < first)
    gross = B["principal"] + sum(p["interest"] for p in TXP)
    repay = gross if BREAK == "tx-repay" else gross - pre - U["reserve"]
    check("5 tx-repay", abs(repay - P["tx"]["repay"]) < 1,
          f"Texas customers repay ${repay:,.0f}; payload ${P['tx']['repay']:,.0f} (prepaid interest ${pre:,.0f}, "
          f"reserve ${U['reserve']:,.0f})")
    # 6 split -------------------------------------------------------------------
    b = P["both"]
    tx_costs = B["principal"] - S.tx_assets()["total"] - U["reserve"] - (0 if BREAK == "split" else pre)
    ok_costs = sum(P["ok"][u]["principal"] - P["ok"][u]["to_utilities"] for u in ("ong", "suo"))
    parts = b["to_utilities"] + b["interest"] + tx_costs + ok_costs
    check("6 split", abs(parts - b["repay"]) < 1 and abs(tx_costs + ok_costs - b["costs"]) < 1,
          f"parts sum to ${parts:,.0f}; customers repay ${b['repay']:,.0f}")
    # 7 hero --------------------------------------------------------------------
    h = P["hero"]
    bad = []
    for ym in ("2023-03", "2026-10", "2033-04", "2039-03", "2039-04", "2046-12"):
        y, m = (int(x) for x in ym.split("-"))
        e = dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)
        _, t = M.remaining(TXP, e)
        if BREAK != "hero" and e < TXP[-1]["date"]:
            t -= U["reserve"]
        if e < dt.date(2023, 9, 1):
            t -= pre
        for u in ("ong", "suo"):
            bb = S.ok_bonds(u)
            for rows in bb["schedule"].values():
                t += sum(r["interest"] + r["principal"] for r in rows[1:] if r["date"] > e)
        if abs(t - h["total"][h["x"].index(ym)]) > 1:
            bad.append(f"{ym} {t:,.0f} vs {h['total'][h['x'].index(ym)]:,.0f}")
    neg = [x for x, a, c in zip(h["x"], h["total"], h["principal"]) if a < c - 1e-6]
    check("7 hero", not bad and not neg, "sampled months equal what is still scheduled; band never negative"
          + (f": {bad}" if bad else "") + (f"; negative band {neg[:3]}" if neg else ""))
    # 8 tx-home -----------------------------------------------------------------
    use = S.eia_home("TX")
    yrs = sorted(use)[-1:] if BREAK == "tx-home" else sorted(use)[-10:]
    mcf = sum(use[y] for y in yrs) / len(yrs)
    H = S.tx_rate_history()
    rate = H["steps"][-1][1] * 14.73 / 14.65
    month = rate * mcf / 12
    check("8 tx-home", abs(month - P["homes"]["TX"]["month"]) < 0.005 and round(rate / 10, 5) == H["cnp_1473"],
          f"{mcf:.2f} Mcf/yr x ${rate:.4f} = ${month:.2f}/month; payload ${P['homes']['TX']['month']:.2f}; "
          f"CenterPoint @14.73 ${H['cnp_1473']}")
    # 9 suo-cert ----------------------------------------------------------------
    cert = S.money(S.quote("ok_suo_servicer_2026-09.pdf", r"Principal balance to be Outstanding \(following payment on "
                                                         r"Current Payment Date\): i\. Tranche A-1 \$([\d,.]+)").group(1))
    rows = S.ok_bonds("suo")["schedule"]["A-1"]
    i = [r["date"] for r in rows].index(dt.date(2026, 10, 1)) - (1 if BREAK == "suo-cert" else 0)
    check("9 suo-cert", abs(rows[i]["balance"] - cert) < 0.005,
          f"schedule after {rows[i]['date']} ${rows[i]['balance']:,.2f}; certificate ${cert:,.2f}")
    # 10 quotes -----------------------------------------------------------------
    T = page_text()
    qs = re.findall(r'"([^"]{12,})"', T)
    if BREAK == "quotes":
        qs[0] = qs[0].replace("100", "1,000")
    srcs = [S.flat(n) for n in ("ok_suo_order.pdf", "ok_ong_order.pdf", S.TX_OS, "tx_utilcode_104.pdf",
                                "eia_glossary_c.html")]
    missing = [q for q in qs if not any(q.rstrip(".") in s for s in srcs)]
    check("10 quotes", qs and not missing, f"{len(qs)} quotations found in their sources" + (f"; missing {missing}" if missing else ""))
    # 11 page -------------------------------------------------------------------
    import update_page as UP
    P2 = json.loads(json.dumps(P))
    if BREAK == "page":
        P2["both"]["interest"] *= 1.01
    try:
        t, _ = UP.cite(UP.render(P2))
        same = t == open(PAGE, "rb").read().decode("utf-8")
    except SystemExit as e:                 # claims() refusing the moved figure is also a failure to match
        same, t = False, str(e)
    check("11 page", same, "the page is exactly what update_page.py renders from the payload")
    # 12 labels -----------------------------------------------------------------
    t12 = T.replace("Scheduled, not measured", "") if BREAK == "labels" else T
    need = ["as scheduled", "Scheduled, not measured", "a home on the system for the whole term", "approximations",
            "West Texas division", "Senate Bill 30", "does not update itself"]
    gone = [n for n in need if n.lower() not in t12.lower()]
    check("12 labels", not gone, "the page's qualifiers are on it" + (f"; missing {gone}" if gone else ""))
    # 13 register ---------------------------------------------------------------
    t13 = T + (" a crisis" if BREAK == "register" else "")
    hit = [w for w in ("crisis", "boom", "strain", "bubble", "gouging", "profiteering", "windfall")
           if re.search(r"\b" + w + r"\b", t13, re.I)]
    check("13 register", not hit, "none of the ruled-out words" + (f"; found {hit}" if hit else ""))
    print(f"{len(fails)} failure(s)" + (f" (--break {BREAK})" if BREAK else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
