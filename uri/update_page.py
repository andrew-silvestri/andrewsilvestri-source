"""
Write site/uri.html from template.html and outputs/payload.json.

Every number on the page comes from the payload, from a quotation read out of an opened filing (sources.py
reads it at render time, so a quotation cannot drift from its file), or from a file this script measures (the
archive's size); the prose is in the template. The parts other scripts own - the nav (rebuild_nav.py), the
citation markers and Sources list (add_citations.py's table, applied here) and the ?v= stamps (bust_cache.py)
- are kept as the shipped page has them, so tests/test_generators.py can run this on the shipped tree and
expect no change. The idiom is lostgas/update_page.py's.

claims() asserts every direction and range the template's words commit to ("just over a third", "about $4 to
$8", "until 2039 and 2047", "the two zero rows", "lower" for what is still to come, ...). If a rebuild moves
one, the generator stops rather than ship prose the payload contradicts.

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import datetime as dt
import html
import os
import re
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "uri.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "uri-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def d(s):
    return dt.date.fromisoformat(s)


def long(s):
    x = d(s)
    return f"{MONTHS[x.month - 1]} {x.day}, {x.year}"


def mon(s):
    x = d(s)
    return f"{MONTHS[x.month - 1]} {x.year}"


def m1(x):
    return f"{x / 1e6:,.1f}"


def bn(x, k=1):
    return f"{x / 1e9:.{k}f}"


def pct(x, k=0):
    return f"{100 * x:.{k}f}"


def usd(x):
    return f"{x:,.2f}"


def r10(x):
    return f"{round(x, -1):,.0f}"


def t_at(P, ym):
    xs = P["hero"]["x"]
    return xs.index(ym) / (len(xs) - 1)


def hero_spec(P):
    h, tx, ok = P["hero"], P["tx"], P["ok"]
    today = P["today"][:7]
    return {"id": "uri-hero", "type": "series",
            "title": "Scheduled payments still to come on the three Winter Storm Uri gas bond issues, Texas and "
                     "Oklahoma together, billions of dollars, with the part that is principal",
            "x": h["x"], "y": {"label": "$ billion"},
            "series": [{"key": "total", "label": "Still to repay, as scheduled", "color": "acc",
                        "values": [round(v / 1e9, 4) for v in h["total"]]},
                       {"key": "prin", "label": "of it, principal", "color": "ink",
                        "values": [round(v / 1e9, 4) for v in h["principal"]]}],
            "band": {"a": "total", "b": "prin", "pos": {"color": "moss", "label": "interest"}, "neg": {"color": "moss"}},
            "annotations": [{"at": tx["closing"][:7], "text": "Texas bonds sold", "short": "Texas sold"},
                            {"at": today, "text": "today", "short": "today"},
                            {"at": tx["last_payment"][:7], "text": "Texas paid off", "short": "Texas done"}]}


def hero(P):
    import insight
    tx, ok, b = P["tx"], P["ok"], P["both"]
    today = P["today"][:7]
    peak = max(P["hero"]["total"])
    left_p = P["hero"]["principal"][P["hero"]["x"].index(today)]
    left_t = P["hero"]["total"][P["hero"]["x"].index(today)]
    after_tx = P["hero"]["total"][P["hero"]["x"].index(tx["last_payment"][:7])]
    i0 = P["hero"]["x"].index(tx["closing"][:7])
    band0 = P["hero"]["total"][i0] - P["hero"]["principal"][i0]
    steps = [
        (f"<p><b>${bn(peak)} billion to repay.</b> Oklahoma's two gas bond issues were sold in "
         f"{mon(ok['ong']['closing'])} and {mon(ok['suo']['closing'])}, and Texas's issue in {mon(tx['closing'])}. "
         f"From then on, customers' charges must cover ${bn(peak, 2)} billion. The shaded gap between the lines is the "
         f"interest still to pay, ${bn(band0)} billion. With the ${m1(tx['prepaid_interest'])} million that Texas paid "
         f"at the start, the interest is ${bn(b['interest'])} billion in total.</p>", {"t": t_at(P, tx["closing"][:7])}),
        (f"<p><b>{mon(P['today'])}: ${bn(left_t, 2)} billion to go.</b> ${bn(b['paid'], 2)} billion has been paid. "
         f"${bn(left_t - left_p)} billion of the interest, which is most of it, is still to be paid. The principal "
         f"decreases slowly at first, so interest continues to accumulate on a large balance for years.</p>",
         {"t": t_at(P, today)}),
        (f"<p><b>{mon(tx['last_payment'])}: Texas's last payment.</b> Summit's schedule ends earlier, in "
         f"{mon(ok['suo']['last_payment'])}. The amount left after Texas, ${bn(after_tx, 2)} billion, is for the "
         f"Oklahoma Natural Gas bonds.</p>",
         {"t": t_at(P, tx["last_payment"][:7])}),
        (f"<p><b>{mon(ok['ong']['last_payment'])}: the final payment.</b> The Oklahoma Natural Gas bonds have the "
         f"longest term, about twenty-five years from their sale.</p>", {"t": 1}),
    ]
    return insight.scrolly(hero_spec(P), steps, from_state={"t": 0})


def split(P):
    import insight
    b = P["both"]
    spec = {"type": "split", "id": "uri-split",
            "title": "What customers of the three bond issues repay, by what it pays for, billions of dollars",
            "unit": "", "decimals": 2,
            "total": {"label": "Customers repay, $ billion:", "value": round(b["repay"] / 1e9, 6)},
            "parts": [{"label": "The utilities' storm costs", "value": round(b["to_utilities"] / 1e9, 6), "color": "acc"},
                      {"label": "Interest", "value": round(b["interest"] / 1e9, 6), "color": "moss"},
                      {"label": "Issuing the bonds", "value": round(b["repay"] / 1e9, 6) - round(b["to_utilities"] / 1e9, 6)
                       - round(b["interest"] / 1e9, 6), "color": "ink"}]}
    steps = [(f"<p><b>${bn(b['repay'], 2)} billion.</b> This is the amount that the charges repay across the three "
              f"issues, as scheduled.</p>", {"s": 0}),
             (f"<p><b>Where the money goes.</b> ${bn(b['to_utilities'], 2)} billion repays the costs that the "
              f"commissions approved. ${bn(b['interest'], 2)} billion is interest. The remainder, ${m1(b['costs'])} "
              f"million, paid for the sale of the bonds and for the reserves that the proceeds funded.</p>", {"s": 1})]
    return insight.scrolly(spec, steps, from_state={"s": 0})


def quotes():
    import sources as S
    q = {}
    q["q_100x"] = S.quote("ok_suo_order.pdf", r"increases of as much as 100 times the typical purchase price, or more").group(0)
    q["q_1000"] = S.quote("ok_ong_order.pdf", r"monthly residential customer bills (in excess of \$1,000)").group(1)
    q["q_ong_dates"] = S.quote("ok_ong_order.pdf", r"incurred beginning February 11, 2021, and ending February 19, 2021").group(0)
    q["q_suo_dates"] = S.quote("ok_suo_order.pdf", r"incurred beginning February 7, 2021, and ending February 21, 2021").group(0)
    q["q_tx_cause"] = S.quote(S.TX_OS, r"In February 2021, prolonged frigid temperatures.*?in order to meet demand\.", 29).group(0)
    m = S.quote(S.TX_OS, r"On (March 2), 2023, Senate Bill 30 \(\"SB 30\"\) was filed, and on (March 7), 2023, House Bill "
                         r"500 \(\"HB 500\"\) was filed", 28)
    q["tx_bills"] = f"Senate Bill 30 on {m.group(1)}, 2023 and House Bill 500 on {m.group(2)}"
    q["q_tx_uniform"] = S.tx_rates()["uniform"]
    q["q_eia_base"] = S.eia_base()["text"]
    q["q_alloc"] = S.quote("ok_suo_order.pdf", r"based on actual usage during the month of February 2021").group(0)
    for k in ("ong", "suo"):
        S.quote(f"ok_{k}_order.pdf", r"based on actual usage during the month of February 2021")   # both orders say it
    return {k: html.escape(v, quote=False) for k, v in q.items()}


def S_q(key):
    """Figures read from a filing's text at render time."""
    import sources as S
    if key == "bill_pct":
        return S.quote(S.TX_OS, r"approximately ([\d.]+)% of the total bill received by an average residential customer").group(1)
    raise KeyError(key)


def claims(P, H):
    tx, ok, b = P["tx"], P["ok"], P["both"]
    months = [h["month"] for h in H.values()]
    c = [
        ("h1 'over a third of the total is interest'", 1 / 3 < b["interest_share"] < 0.40),
        ("h1 'about $lo to $hi a month': the homes' monthly charges round to the two ends",
         round(min(months)) >= 3 and round(max(months)) <= 9),
        ("h1 'until as late as <ONG>': Oklahoma Natural Gas's is the last payment of the three", tx["last_payment"] <
         ok["ong"]["last_payment"] and ok["suo"]["last_payment"] < ok["ong"]["last_payment"]),
        ("takeaway 2 'billed since late 2022': both Oklahoma issues closed in the second half of 2022",
         all(ok[u]["closing"][:4] == "2022" and int(ok[u]["closing"][5:7]) >= 7 for u in ("ong", "suo"))),
        ("'ten gas utilities': eight in Texas, two in Oklahoma", len(tx["assets"]) == 8),
        ("'a smaller part of each payment from now on', both states",
         tx["left_interest_share"] < tx["interest_share"] and ok["ong"]["left_interest_share"] < ok["ong"]["interest_share"]),
        ("hero step 4 'about twenty-five years from their sale'",
         24.5 <= (d(ok["ong"]["last_payment"]) - d(ok["ong"]["closing"])).days / 365.25 <= 25.5),
        ("hero step 2 'most of' the interest still to be paid",
         (P["hero"]["total"][P["hero"]["x"].index(P["today"][:7])] - P["hero"]["principal"][P["hero"]["x"].index(P["today"][:7])])
         > b["interest"] / 2),
        ("Method 'up to about $N million lower': the unused capacity is positive and under 0.5 per cent",
         0 < tx["six_months_interest"] - tx["prepaid_interest"] < 0.005 * tx["repay"]),
        ("takeaway 3 'about a third ... more for an Oklahoma Natural Gas home'",
         all(0.28 <= H[k]["interest_share"] <= 0.37 for k in ("TX", "SUO"))
         and H["ONG-A"]["interest_share"] > max(H["TX"]["interest_share"], H["SUO"]["interest_share"])),
        ("Texas card 'from now on' interest is a smaller part: still-to-come share below the home's whole-term share",
         tx["left_interest_share"] < H["TX"]["interest_share"]),
        ("'Summit's ends' before Texas's last payment", ok["suo"]["last_payment"] < tx["last_payment"]),
        ("'the two zero rows'", sum(1 for _, v, _n in ok["ong"]["classes"] if v == 0) == 2),
        ("'Oklahoma Natural Gas's have been' reset", H["ONG-A"]["alloc"] != H["ONG-A"]["alloc_latest"]),
        ("'what CenterPoint's tariff states': the pressure-raised rate rounds to its 14.73 figure",
         round(H["TX"]["per_mcf_eia"] / 10, 5) == H["TX"]["cnp_1473"]),
        ("Oklahoma reserves 'would change the total by' under one per cent",
         (ok["ong"]["reserve"] + ok["suo"]["reserve"]) / P["ok_all"]["repay"] < 0.01),
        ("the split's parts are non-negative and sum to the total", b["costs"] > 0),
    ]
    bad = [n for n, okk in c if not okk]
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def class_rows(ok):
    rows = []
    for u, name in (("ong", "Oklahoma Natural Gas"), ("suo", "Summit")):
        for cls, v, n in ok[u]["classes"]:
            nx = f" (${usd(n)})" if n is not None else ""
            rows.append(f"<tr><td>{name}: {html.escape(cls)}</td><td class=\"n\">${usd(v)}{nx}</td></tr>")
    return "\n".join(rows)


def values(P):
    import insight
    tx, ok, b, H = P["tx"], P["ok"], P["both"], P["homes"]
    claims(P, H)
    names = {"TGS": "Texas Gas Service", "UniGas": "UniGas (Universal Natural Gas)"}
    order = sorted(tx["assets"].items(), key=lambda kv: -kv[1])
    tx_all = ", ".join(f"{names.get(k, k)} ${v / 1e9:.2f} billion" if v >= 1e9 else
                       f"{names.get(k, k)} ${v / 1e6:,.1f} million" for k, v in order[:-1])
    tx_all += f" and {names.get(order[-1][0], order[-1][0])} ${order[-1][1] / 1e6:,.1f} million"
    T = H["TX"]
    steps = T["steps"]
    step_txt = []
    for k, (since, rate, _) in enumerate(steps):
        y, m = since.split("-")
        lab = f"{MONTHS[int(m) - 1]} {y}"
        step_txt.append(f"${rate:.2f} per thousand cubic feet from {lab}" if k == 0 else f"${rate:.2f} from {lab}")
    tx_steps = ", ".join(step_txt[:-1]) + " and " + step_txt[-1]
    months = {k: h["month"] for k, h in H.items()}
    ok_terms = [H[k]["term"] for k in ("ONG-A", "ONG-B", "SUO")]
    v = {
        # _INSIGHT rule 5: the page says its data does not update itself, and what it is as of. The kit's
        # stamp(live=False) printed a bare "This data does not update.", which the cold reader took for a
        # broken page (attempt 1, 2026-10-24), so the sentence says what is fixed and what moves.
        "charges_asof": (f"The bond schedules are fixed. Filings reset the charges at least once a year. "
                         f"This page shows the charges filed through October 2026 and does not update itself. "
                         f"What is still to come is counted from {long(P['today'])}."),
        "takeaways": insight.takeaways([
            f"In Texas, the law sets one charge on each unit of gas for all customers who buy gas from the utilities "
            f"in the program. The charge is now ${T['per_mcf']:.2f} per thousand cubic feet on most of their tariffs, "
            f"about ${T['month']:.0f} a month for an average home. It has been billed since October 2023, and it "
            f"continues until the bonds are repaid, in {mon(tx['last_payment'])}.",
            f"In Oklahoma, the charge is a flat amount on each monthly bill, billed since late 2022. An Oklahoma "
            f"Natural Gas home now pays ${usd(H['ONG-A']['month'])} or ${usd(H['ONG-B']['month'])}, until "
            f"{d(ok['ong']['last_payment']).year}. The amount depends on whether the home uses less or more than 50 "
            f"dekatherms of gas a year. A Summit home now pays ${usd(H['SUO']['month'])}, until "
            f"{d(ok['suo']['last_payment']).year}.",
            f"A home on the system for the whole term pays about ${r10(T['term'])} in Texas and "
            f"${r10(min(ok_terms))} to ${r10(max(ok_terms))} in Oklahoma. Interest is about a third of that, and "
            f"more for an Oklahoma Natural Gas home."]),
        "hero": hero(P), "split": split(P),
        "ok_last_year": str(d(ok["ong"]["last_payment"]).year),
        "lo_month": f"{round(min(months.values()))}", "hi_month": f"{round(max(months.values()))}",
        "to_util_bn": bn(b["to_utilities"], 2), "int_bn": bn(b["interest"], 2), "paid_bn": bn(b["paid"], 2), "repay_bn": bn(b["repay"], 2), "left_bn": bn(b["left_today"], 2),
        "tx_prepaid_m": m1(tx["prepaid_interest"]), "tx_reserve_m": m1(tx["reserve"]),
        "tx_closing": mon(tx["closing"]), "tx_principal": m1(tx["principal"]), "tx_to_util": m1(tx["to_utilities"]),
        "tx_interest": m1(tx["interest"]), "tx_repay": m1(tx["repay"]), "tx_last": mon(tx["last_payment"]),
        "tx_coupons": " and ".join(f"{100 * t['coupon']:.3f}%" for t in tx["tranches"].values()),
        "tx_to_util_bn": f"{tx['to_utilities'] / 1e9:.2f}", "tx_all": tx_all,
        "tx_bill_pct": S_q("bill_pct"), "ok_mcf": f"{P['ok_use']['mcf']:.0f}",
        "tx_six_m": m1(tx["six_months_interest"]), "tx_unused_m": f"{(tx['six_months_interest'] - tx['prepaid_interest']) / 1e6:.0f}",
        "tx_steps": tx_steps, "tx_wt": f"{tx['west_texas']['per_ccf']:.4f}",
        "tx_rate": f"{T['per_mcf']:.2f}", "tx_mcf": f"{T['mcf_year']:.0f}", "tx_y0": str(T["eia_years"][0]),
        "tx_y1": str(T["eia_years"][1]), "tx_month": usd(T["month"]), "tx_year": f"{T['year']:.0f}",
        "tx_term": r10(T["term"]), "tx_int": pct(T["interest_share"]),
        "tx_mcf_last": f"{T['eia_last']:.1f}", "tx_rate_eia": f"{T['per_mcf_eia']:.4f}", "cnp_1473": f"{T['cnp_1473']:.5f}",
        "tgs_avg": usd(T["tgs_avg_month"]), "p_tx": f"{P['pressure']['tx']:.2f}", "p_eia": f"{P['pressure']['eia']:.2f}",
        "tx_a1": m1(tx["tranches"]["A-1"]["principal"]) + " million", "tx_c1": f"{100 * tx['tranches']['A-1']['coupon']:.3f}%",
        "tx_a2": m1(tx["tranches"]["A-2"]["principal"]) + " million", "tx_c2": f"{100 * tx['tranches']['A-2']['coupon']:.3f}%",
        "tx_wal1": f"{tx['wal']['A-1']:.3f}", "tx_wal2": f"{tx['wal']['A-2']:.3f}",
        "tx_left_int": pct(tx["left_interest_share"]),
        "ok_left_int": pct((ok["ong"]["left_today"] * ok["ong"]["left_interest_share"] + ok["suo"]["left_today"]
                            * ok["suo"]["left_interest_share"]) / (ok["ong"]["left_today"] + ok["suo"]["left_today"])),
        "ok_reserve_m": m1(ok["ong"]["reserve"] + ok["suo"]["reserve"]),
        "ok_reserve_pct": f"{100 * (ok['ong']['reserve'] + ok['suo']['reserve']) / P['ok_all']['repay']:.1f}",
        "ongoing_m": f"{(tx['admin'] + ok['ong']['ongoing_year'] + ok['suo']['ongoing_year']) / 1e6:.1f}",
        "class_rows": class_rows(ok), "ong_from": "May 2026", "ong_next": "November 2026",
        "ong_a_alloc0": f"{100 * H['ONG-A']['alloc']:.2f}%", "ong_a_alloc1": f"{100 * H['ONG-A']['alloc_latest']:.2f}%",
        "onga_check": r10(H["ONG-A"]["term_check"]), "ongb_check": r10(H["ONG-B"]["term_check"]),
        "suo_check": r10(H["SUO"]["term_check"]),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    for k in ("ong", "suo"):
        x = ok[k]
        v.update({f"{k}_closing": mon(x["closing"]), f"{k}_principal": m1(x["principal"]),
                  f"{k}_to_util": m1(x["to_utilities"]), f"{k}_interest": m1(x["interest"]),
                  f"{k}_repay": m1(x["repay"]), f"{k}_last": mon(x["last_payment"]),
                  f"{k}_extreme_m": f"{x['extreme'] / 1e6:,.1f}", f"{k}_int": pct(x["interest_share"])})
    v["ong_coupon"] = f"{100 * ok['ong']['wavg_coupon']:.3f}%"
    v["suo_coupon"] = f"{100 * ok['suo']['wavg_coupon']:.3f}%"
    for k, key in (("ONG-A", "onga"), ("ONG-B", "ongb"), ("SUO", "suo")):
        h = H[k]
        v.update({f"{key}_month": usd(h["month"]), f"{key}_year": f"{h['year']:.0f}", f"{key}_term": r10(h["term"]),
                  f"{key}_init": usd(h["initial"])})
        if "next_est" in h:
            v[f"{key}_next"] = usd(h["next_est"])
    v.update(quotes())
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "lostgas.html"), encoding="utf-8").read()
        stamps = {}
    else:
        stamps = dict(re.findall(r'(?:href|src|srcset)="([^"?]+)\?v=([0-9a-f]+)"', shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    text = text.replace("{{nav}}", nav)

    def stamp(m):
        path = m.group(2)
        return f'{m.group(1)}="{path}?v={stamps[path]}"' if path in stamps else m.group(0)
    return re.sub(r'(href|src|srcset)="([^"?]+\.(?:css|js|png))"', stamp, text)


def render(P):
    t = open(TEMPLATE, encoding="utf-8").read()
    v = values(P)
    missing = sorted(set(re.findall(r"{{(\w+)}}", t)) - set(v) - {"nav"})
    if missing:
        raise SystemExit(f"template placeholders without a value: {missing}")
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)))
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("uri.html")
    if not refs:
        return text, ["uri.html has no entry in add_citations.PAGES"]
    tmp = PAGE + ".render.tmp"
    open(tmp, "w", encoding="utf-8", newline="\n").write(text)   # LF: trap 32
    try:
        out, probs = add_citations.build(os.path.basename(tmp), refs)
    finally:
        os.remove(tmp)
    return (out if out is not None else text), probs


def main(apply=False):
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    t = render(P)
    t, probs = cite(t)
    for p in probs:
        print("  " + p)
    if os.path.exists(PAGE):
        old = open(PAGE, "rb").read().decode("utf-8")          # bytes: trap 32
        print("  uri.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  uri.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
