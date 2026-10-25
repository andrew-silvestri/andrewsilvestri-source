"""The arithmetic of the Uri bonds: scheduled payments, interest, what is left, and what one home pays.

Nothing here is an estimate of anything a filing does not already fix. The schedules are the issuers'
expected ones; the interest is the coupon on the scheduled balance; a home's charge is the filed charge.
The one assumption is labelled where it is made: that a charge stays near its latest filed level.

payments(st)       every scheduled payment date in a state with its principal and interest ($), Texas
                   from the official statement's amortization table and coupons (interest computed
                   here, 30/360, from the closing date), Oklahoma as the Issuance Advice Letters print
                   them (both utilities summed by date).
tx_interest()      Texas interest by date and tranche, 30/360 from the closing date.
wal(rows, close)   weighted average life, years, of a principal schedule: a check against the stated one.
remaining(P, d)    principal and principal + interest still scheduled after date d.
"""
import datetime as dt

import sources as S


def d360(a, b):
    """30/360 day count (the bonds' basis), a to b."""
    da, db = min(a.day, 30), b.day if not (b.day == 31 and min(a.day, 30) == 30) else 30
    return 360 * (b.year - a.year) + 30 * (b.month - a.month) + (db - da)


def years(a, b):
    return d360(a, b) / 360.0


def tx_interest(B=None):
    B = B or S.tx_bonds()
    first = dt.datetime.strptime(B["first_interest"], "%B %d, %Y").date()
    dates = [first] + [r["date"] for r in B["schedule"]]
    paid = {k: 0.0 for k in B["tranches"]}
    out, prev = [], B["closing"]
    by = {r["date"]: r for r in B["schedule"]}
    for d in dates:
        row = {"date": d}
        for k, t in B["tranches"].items():
            bal = t["principal"] - paid[k]
            row[k] = bal * t["coupon"] * d360(prev, d) / 360.0
        for k in B["tranches"]:
            paid[k] += by.get(d, {}).get(k, 0.0)
        out.append(row)
        prev = d
    return out


def payments(st):
    """[{date, principal, interest}] in date order."""
    acc = {}
    if st == "TX":
        B = S.tx_bonds()
        for r in B["schedule"]:
            a = acc.setdefault(r["date"], {"principal": 0.0, "interest": 0.0})
            a["principal"] += r["A-1"] + r["A-2"]
        for r in tx_interest(B):
            a = acc.setdefault(r["date"], {"principal": 0.0, "interest": 0.0})
            a["interest"] += sum(v for k, v in r.items() if k != "date")
    else:
        for u in ("ong", "suo"):
            for rows in S.ok_bonds(u)["schedule"].values():
                for r in rows[1:]:
                    a = acc.setdefault(r["date"], {"principal": 0.0, "interest": 0.0})
                    a["principal"] += r["principal"]
                    a["interest"] += r["interest"]
    return [dict(date=d, **acc[d]) for d in sorted(acc)]


def wal(pairs, close):
    """pairs: [(date, principal)]."""
    tot = sum(p for _, p in pairs)
    return sum(p * years(close, d) for d, p in pairs) / tot


def remaining(P, d):
    after = [p for p in P if p["date"] > d]
    return sum(p["principal"] for p in after), sum(p["principal"] + p["interest"] for p in after)


def months(a, b):
    """Whole billing months from the month of a to the month of b, inclusive of a, exclusive of b."""
    return 12 * (b.year - a.year) + (b.month - a.month)
