"""Build uri/outputs/payload.json from the filings (through sources.py) and the bond arithmetic (model.py).

What customers repay is not the bonds' principal plus interest (plan review, finding 4). In Texas the first
interest payment, September 1, 2023, came out of the proceeds set aside for it (the charge was zero until
October 2023), and the reserve subaccount, also held back from the proceeds, pays the last principal
instalment. So Texas customers repay principal - reserve + interest - interest paid from proceeds, and all of
the interest is still theirs: the part paid at the start through the principal. Oklahoma's reserve
subaccounts are not netted (their use is not stated in what was opened; 0.3 per cent), and the Method says so.

A home's total over the term (review 10):
- Texas: the filed rate history (one rate per year from each October), then the latest rate, times EIA's
  average residential use over the ten latest years, at EIA's pressure base (review 3).
- Oklahoma: the filings' own mechanism, the class's allocation share of the scheduled payments plus the stated
  ongoing costs, divided by the class's customers at issue; latest charge x months is kept as the check.

The build date is the "today" the "still to come" figures are taken at, written into the payload.

Run:  python build_uri.py [--today YYYY-MM-DD]
"""
import argparse
import datetime as dt
import json
import os

import model as M
import sources as S

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs", "payload.json")
TX_BASE = 14.65                        # psia: the Texas charge's base (its tariffs state the rate @14.65)
HOME_YEARS = 10


def month_end(y, m):
    return dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)


def ym_date(s):
    y, m = s.split("-")
    return dt.date(int(y), int(m), 1)


def first_bill(closing):
    """Oklahoma charges begin with the bills after closing (the IALs' first period runs from closing)."""
    return dt.date(closing.year + (closing.month == 12), closing.month % 12 + 1, 1)


def build(today):
    TXB, A, O, U = S.tx_bonds(), S.tx_assets(), S.tx_outstanding(), S.tx_upfront()
    EIA_BASE = S.eia_base()["psia"]          # EIA's glossary: a cubic foot at 60 F and 14.73 psia
    H = S.tx_rate_history()
    TXP = M.payments("TX")
    ONG, SUO = S.ok_bonds("ong"), S.ok_bonds("suo")
    costs = {u: S.ok_costs(u) for u in ("ong", "suo")}

    # ---------------------------------------------------------------- Texas
    tx_first = ym_date(H["steps"][0][0])
    pre = [p for p in TXP if p["date"] < tx_first]          # paid before any charge was billed
    prepaid = sum(p["interest"] for p in pre)
    if any(p["principal"] for p in pre):
        raise SystemExit("a principal payment falls before the first charge; the netting below assumes none")
    tx_last = TXP[-1]["date"]

    def tx_left(d):
        """What Texas customers still have to pay, as scheduled, after date d."""
        _, t = M.remaining(TXP, d)
        if d < tx_last:
            t -= U["reserve"]
        if d < pre[-1]["date"]:
            t -= prepaid
        return max(t, 0.0)

    tx_int = sum(p["interest"] for p in TXP)
    tx_repay = TXB["principal"] - U["reserve"] + tx_int - prepaid
    tx = {"principal": TXB["principal"], "to_utilities": A["total"], "assets": A["by_utility"],
          "reserve": U["reserve"], "prepaid_interest": prepaid, "prepaid_date": pre[-1]["date"].isoformat(),
          "upfront_account": U["upfront_account"], "underwriting": U["underwriting"], "issuer_reserve": U["issuer_reserve"],
          "costs": TXB["principal"] - A["total"] - U["reserve"] - prepaid,
          "interest": tx_int, "repay": tx_repay, "interest_share": tx_int / tx_repay,
          "closing": TXB["closing"].isoformat(), "last_payment": tx_last.isoformat(),
          "tranches": {k: {"principal": v["principal"], "coupon": v["coupon"], "sched_final_year": v["sched_final_year"]}
                       for k, v in TXB["tranches"].items()},
          "outstanding_check": {"as_of": O["as_of"].isoformat(), "A-1": O["A-1"], "A-2": O["A-2"]},
          "left_today": tx_left(today), "admin_year": O["admin_year"], "admin": O["admin"],
          "west_texas": S.tx_west_texas(),
          "wal": {k: M.wal([(r["date"], r[k]) for r in TXB["schedule"]], TXB["closing"]) for k in TXB["tranches"]},
          "wal_stated": {k: v["wal_stated"] for k, v in TXB["tranches"].items()}}
    rp, rt = M.remaining(TXP, today)
    tx["left_interest_share"] = (rt - rp) / rt
    # "6 months of capitalized interest" at the coupons on the full principal, against the 158 days the first
    # payment needed; what the account did not use reduces the first true-up (claims ledger 13)
    tx["six_months_interest"] = sum(t["principal"] * t["coupon"] / 2 for t in TXB["tranches"].values())
    tx["admin_term"] = O["admin"] * M.years(TXB["closing"], tx_last)

    # ------------------------------------------------------------- Oklahoma
    ok, okP = {}, {}
    for u, b in (("ong", ONG), ("suo", SUO)):
        acc = {}
        for rows in b["schedule"].values():
            for r in rows[1:]:
                a = acc.setdefault(r["date"], {"principal": 0.0, "interest": 0.0})
                a["principal"] += r["principal"]
                a["interest"] += r["interest"]
        P = [dict(date=d, **acc[d]) for d in sorted(acc)]
        okP[u] = P
        q = S.money(S.quote(S.OK[u]["ial"], r"A\. Qualified costs authorized in Cause No\. PUD \d+ \(including any "
                                            r"adjustment to carrying costs\) \$ ?([\d,]+(?:\.\d\d)?)", 7).group(1))
        i = sum(p["interest"] for p in P)
        rp, rt = M.remaining(P, today)
        c = costs[u]
        yrs = M.years(b["closing"], P[-1]["date"])
        ok[u] = {"principal": b["amount"], "to_utilities": q, "costs": b["amount"] - q, "reserve": c["reserve"],
                 "interest": i, "repay": b["amount"] + i, "interest_share": i / (b["amount"] + i),
                 "closing": b["closing"].isoformat(), "last_payment": P[-1]["date"].isoformat(),
                 "tranches": {k: {"principal": v["principal"], "coupon": v["coupon"], "sched_final": v["sched_final"].isoformat()}
                              for k, v in b["tranches"].items()},
                 "wavg_coupon": b["wavg_stated"], "extreme": c["extreme"], "extreme_from": c["from"], "extreme_to": c["to"],
                 "alloc_basis": c["alloc_basis"], "ongoing_year": c["ongoing_year"], "ongoing_term": c["ongoing_year"] * yrs,
                 "left_today": rt, "left_interest_share": (rt - rp) / rt, "classes": S.ok_class_table(u)}
    okall = {k: ok["ong"][k] + ok["suo"][k] for k in ("principal", "to_utilities", "costs", "interest", "repay", "left_today")}
    okall["interest_share"] = okall["interest"] / okall["repay"]

    both = {k: tx[k] + okall[k] for k in ("to_utilities", "costs", "interest", "repay", "left_today")}
    both["interest_share"] = both["interest"] / both["repay"]
    both["paid"] = both["repay"] - both["left_today"]

    # ----------------------------------------------------------------- hero
    start = dt.date(ONG["closing"].year, ONG["closing"].month, 1)
    end = max(tx_last, *(okP[u][-1]["date"] for u in okP))
    xs, tot, prin = [], [], []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        e = month_end(y, m)
        t = p = 0.0
        if e >= TXB["closing"]:
            t += tx_left(e)
            pp, _ = M.remaining(TXP, e)
            p += pp - (U["reserve"] if e < tx_last else 0.0)
        for u, b in (("ong", ONG), ("suo", SUO)):
            if e >= b["closing"]:
                pp, tt = M.remaining(okP[u], e)
                t += tt
                p += pp
        xs.append(f"{y}-{m:02d}")
        tot.append(t)
        prin.append(max(p, 0.0))
        y, m = (y + (m == 12), m % 12 + 1)
    hero = {"x": xs, "total": tot, "principal": prin}

    # ---------------------------------------------------------------- homes
    use = S.eia_home("TX")
    yrs = sorted(use)[-HOME_YEARS:]
    mcf = sum(use[y] for y in yrs) / len(yrs)
    f = EIA_BASE / TX_BASE
    steps = H["steps"]
    term = 0.0
    for k, (since, rate, _) in enumerate(steps):
        a = ym_date(since)
        b = ym_date(steps[k + 1][0]) if k + 1 < len(steps) else dt.date(tx_last.year, tx_last.month, 1)
        term += rate * f * mcf / 12 * M.months(a, b)
    now = steps[-1][1]
    homes = {"TX": {"per_mcf": now, "per_mcf_eia": now * f, "cnp_1465": H["cnp_1465"], "cnp_1473": H["cnp_1473"],
                    "steps": steps, "mcf_year": mcf, "eia_years": [yrs[0], yrs[-1]], "eia_last": use[yrs[-1]],
                    "eia_last_year": yrs[-1],
                    "month": now * f * mcf / 12, "year": now * f * mcf,
                    "months": M.months(tx_first, dt.date(tx_last.year, tx_last.month, 1)), "term": term,
                    "interest_share": tx["interest"] / (tx["repay"] + tx["admin_term"]), "tgs_avg_month": S.tx_rates()["tgs"]["avg_res_month"]}}
    ok_use = S.eia_home("OK")
    ok_yrs = sorted(ok_use)[-HOME_YEARS:]
    oc = S.ok_charges("ong")
    for k in ("A", "B"):
        c = oc["classes"][k]
        mths = M.months(first_bill(ONG["closing"]), dt.date.fromisoformat(ok["ong"]["last_payment"]))
        share = c["alloc"] * (ok["ong"]["repay"] + ok["ong"]["ongoing_term"]) / c["customers"]
        homes[f"ONG-{k}"] = {"initial": c["initial"], "month": c["latest"], "latest_from": oc["latest_from"].isoformat(),
                             "next_est": c["next_est"], "next_from": oc["next_from"].isoformat(), "year": 12 * c["latest"],
                             "months": mths, "term": share, "term_check": c["latest"] * mths,
                             "alloc": c["alloc"], "alloc_latest": c["alloc_latest"], "customers": c["customers"],
                             "interest_share": ok["ong"]["interest"] / (ok["ong"]["repay"] + ok["ong"]["ongoing_term"])}
    sc = S.ok_charges("suo")["classes"]["R"]
    n = S.ok_res_customers_suo()
    fy, fm = S.ok_first_bill_suo()
    mths = M.months(dt.date(fy, fm, 1), dt.date.fromisoformat(ok["suo"]["last_payment"]))
    homes["SUO"] = {"initial": sc["initial"], "month": sc["latest"], "year": 12 * sc["latest"], "months": mths,
                    "term": sc["alloc"] * (ok["suo"]["repay"] + ok["suo"]["ongoing_term"]) / n,
                    "term_check": sc["latest"] * mths, "alloc": sc["alloc"], "customers": n,
                    "interest_share": ok["suo"]["interest"] / (ok["suo"]["repay"] + ok["suo"]["ongoing_term"])}
    return {"today": today.isoformat(), "tx": tx, "ok": ok, "ok_all": okall, "both": both, "hero": hero,
            "homes": homes, "pressure": {"tx": TX_BASE, "eia": EIA_BASE},
            "ok_use": {"years": [ok_yrs[0], ok_yrs[-1]], "mcf": sum(ok_use[y] for y in ok_yrs) / len(ok_yrs)}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default=dt.date.today().isoformat())
    a = ap.parse_args()
    P = build(dt.date.fromisoformat(a.today))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(P, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")
    b = P["both"]
    print(f"payload: today {P['today']}; customers repay {b['repay'] / 1e9:.3f} bn, interest {b['interest_share']:.3f}; "
          f"still to come {b['left_today'] / 1e9:.3f} bn; to utilities {b['to_utilities'] / 1e9:.3f} bn")
    for k, h in P["homes"].items():
        print(f"  {k}: ${h['month']:.2f}/month, ${h['year']:.0f}/yr, {h['months']} months, term ${h['term']:,.0f}"
              + (f" (check ${h['term_check']:,.0f})" if "term_check" in h else ""))
