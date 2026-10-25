"""Readers for the Uri page. Each reads a hash-checked raw file (netfetch.verified), so no number on the
page is typed: the schedules, coupons, charges and amounts are read out of the filings themselves.

tx_bonds()        the Texas Series 2023 bonds: closing date, tranches (principal, coupon, scheduled final
                  payment date, weighted average life as stated), and the expected amortization schedule.
tx_assets()       the regulatory asset amount of each participating utility and their total, as stated.
tx_outstanding()  the issuer's balances at 12/31/2025.
tx_rates()        the customer rate relief rate, $/Ccf, as the RRC and the utilities state it.
ok_bonds(u)       a gas utility's Oklahoma bonds ("ong" or "suo"): closing date, tranches with coupons and
                  stated weighted average life, and the expected sinking fund schedule row by row
                  (balance, interest, principal, total), as the Issuance Advice Letter prints it.
ok_charges(u)     the monthly charge by customer class: initial (IAL Attachment 3) and the latest true-up.
ok_costs(u)       the order's extreme purchase costs, their dates and the stated ongoing financing costs.
eia_home(st, y)   residential consumption per residential consumer, Mcf a year, EIA.
quote(name, pat)  the text a regular expression matches in a source, so quotations are read, not typed.
"""
import datetime as dt
import html
import re

import pymupdf
import xlrd

from netfetch import verified

_cache = {}


def pages(name):
    if name not in _cache:
        p, _ = verified(name)
        if name.endswith(".pdf"):
            _cache[name] = [pg.get_text() for pg in pymupdf.open(p)]
        else:
            t = p.read_bytes().decode("utf-8", "replace")
            t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S)
            _cache[name] = [html.unescape(re.sub(r"<[^>]+>", " ", t))]
    return _cache[name]


def flat(name, i=None):
    ps = pages(name) if i is None else [pages(name)[i - 1]]
    return re.sub(r"\s+", " ", " ".join(ps)).replace("�", "'")


def quote(name, pat, i=None):
    m = re.search(pat, flat(name, i))
    if not m:
        raise LookupError(f"{name}: no match for {pat!r}")
    return m


def money(s):
    return float(s.replace("$", "").replace(",", ""))


def mdy(s):
    m, d, y = (int(x) for x in s.split("/"))
    return dt.date(y + 2000 if y < 100 else y, m, d)


# ---------------------------------------------------------------- Texas ---
TX_OS = "tx_os_2023.pdf"


def tx_bonds():
    closing = quote(TX_OS, r"on or about (March \d+, 2023) \(the .Closing Date.\)", 1).group(1)
    closing = dt.datetime.strptime(closing, "%B %d, %Y").date()
    tr = {}
    for m in re.finditer(r"(A-[12]) \$([\d,]+) (20\d\d) (20\d\d) ([\d.]+)% ([\d.]+) 100\.00", flat(TX_OS, 2)):
        tr[m.group(1)] = {"principal": money(m.group(2)), "sched_final_year": int(m.group(3)),
                          "legal_final_year": int(m.group(4)), "coupon": float(m.group(5)) / 100,
                          "wal_stated": float(m.group(6))}
    if set(tr) != {"A-1", "A-2"}:
        raise LookupError(f"{TX_OS} p2: tranches {sorted(tr)}")
    t = flat(TX_OS, 39)
    body = t[t.index("Tranche A-1 Tranche A-2"):t.index("Totals")]
    sched = []
    for m in re.finditer(r"(\d+/\d+/20\d\d) (\$?[\d,]+|-) (\$?[\d,]+|-)", body):
        a1, a2 = (0.0 if x == "-" else money(x) for x in (m.group(2), m.group(3)))
        sched.append({"date": mdy(m.group(1)), "A-1": a1, "A-2": a2})
    tot = re.search(r"Totals \$([\d,]+) \$([\d,]+)", t)
    for k, g in (("A-1", 1), ("A-2", 2)):
        if abs(sum(r[k] for r in sched) - money(tot.group(g))) > 0.5 or money(tot.group(g)) != tr[k]["principal"]:
            raise ValueError(f"{TX_OS} p39: {k} schedule does not sum to its stated total and principal")
    # interest: from the closing date, first paid September 1, 2023, then each April 1 and October 1
    first = quote(TX_OS, r"Interest is payable on (September 1, 2023) and for each calendar year thereafter "
                         r"semi-annually on each April 1 and October 1", 2).group(1)
    basis = quote(TX_OS, r"360-day year of twelve 30-day months", 36).group(0)
    total = money(quote(TX_OS, r"^.*?\$([\d,]+) TEXAS NATURAL GAS SECURITIZATION", 1).group(1))
    return {"closing": closing, "tranches": tr, "schedule": sched, "first_interest": first, "basis": basis,
            "principal": total}


def tx_assets():
    t = flat(TX_OS, 30)
    i = t.index("Determination Amounts Atmos")
    seg = t[i + len("Determination Amounts "):t.index("Final Aggregated", i)]
    rows = {m.group(1).strip(): money(m.group(2)) for m in re.finditer(r"([A-Z][A-Za-z ]*?) \$([\d,]+)(?:\(a\))?", seg)}
    total = money(re.search(r"Final Aggregated Regulatory Asset Determination Amounts \$([\d,]+)", t[i:]).group(1))
    if abs(sum(rows.values()) - total) > 0.5:
        raise ValueError(f"{TX_OS} p30: asset rows sum to {sum(rows.values())}, total {total}")
    return {"by_utility": rows, "total": total}


def tx_outstanding():
    t = flat("tx_outstanding_2026.pdf")
    m = re.search(r"outstanding as of (\d+/\d+/\d{4}): Tranche A-1 ([\d,]+) \$ Tranche A-2 ([\d,]+)", t)
    admin = re.search(r"Estimated bond administrative expenses for Calendar Year (\d{4}) .*? Total ([\d,]+)", t)
    return {"as_of": mdy(m.group(1)), "A-1": money(m.group(2)), "A-2": money(m.group(3)),
            "admin_year": int(admin.group(1)), "admin": money(admin.group(2))}


def tx_west_texas():
    """The one division whose filed rate differs (plan review 7): rate, $/Ccf, and its stated effective date."""
    r = quote("tx_tariff_6931.pdf", r"West Texas Division Sales Customers shall be assessed the uniform volumetric charge "
                                    r"identified below\. E\.CRR CHARGE The CRR Charge will be a monthly volumetric rate of "
                                    r"\$ ([\d.]+)/Ccf", 13)
    d = quote("tx_tariff_6931.pdf", r"closing notice of initial charge.{0,200}?Rate to be effective (June 1, 2026)", 10)
    return {"per_ccf": float(r.group(1)), "from": d.group(1)}


def tx_rates():
    """$/Ccf as the sources state them. The statute makes the charge uniform and volumetric."""
    first = quote("tx_rrc_2023-10-04.html", r"\$([\d.]+) per Mcf \(\$([\d.]+) per Ccf\) will be included in the gas "
                                            r"cost portion of bills starting (October 1, 2023)")
    tgs = quote("tx_tgs_securitization.html", r"securitization charge is \$([\d.]+) per Mcf\. The average residential "
                                              r"customer will pay approximately \$([\d.]+) per month")
    uniform = quote("tx_utilcode_104.pdf", r"uniform monthly volumetric customer rate relief charges must be paid by "
                                           r"all current and future customers").group(0)
    return {"first": {"per_mcf": float(first.group(1)), "per_ccf": float(first.group(2)), "from": first.group(3)},
            "tgs": {"per_mcf": float(tgs.group(1)), "avg_res_month": float(tgs.group(2))},
            "uniform": uniform}


# ------------------------------------------------------------- Oklahoma ---
OK = {"ong": {"ial": "ok_ong_ial.pdf", "order": "ok_ong_order.pdf", "trueup": "ok_ong_trueup_2026-03.pdf",
              "sched_pages": (9, 10, 11)},
      "suo": {"ial": "ok_suo_ial.pdf", "order": "ok_suo_order.pdf", "trueup": "ok_suo_trueup_2026-03.pdf",
              "sched_pages": (9, 10)}}
_DATE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")
_NUM = re.compile(r"^\$?[\d,]+\.\d\d$|^-$")


def ok_bonds(u):
    ial = OK[u]["ial"]
    t = flat(ial, 2)
    closing = dt.datetime.strptime(re.search(r"Closing Date: (\w+ \d+)(?:st|nd|rd|th)?, (\d{4})", t).expand(r"\1 \2"),
                                   "%B %d %Y").date()
    amount = money(re.search(r"Amount Issued \(Authorized Amount\): \$([\d,.]+)", t).group(1))
    tr = {m.group(1): {"coupon": float(m.group(2)) / 100, "sched_final": mdy(m.group(3)), "legal_final": mdy(m.group(4))}
          for m in re.finditer(r"(A-\d) ([\d.]+)% (\d+/\d+/\d+) (\d+/\d+/\d+)", t)}
    wal = float(re.search(r"Weighted Average Life of Series: ([\d.]+) years", t).group(1))
    wavg = float(re.search(r"Weighted Average Interest Rate of the Ratepayer-Backed Bonds: ([\d.]+) ?%", t).group(1)) / 100
    # the sinking fund schedule: tokens, one tranche after another
    toks = []
    for i in OK[u]["sched_pages"]:
        toks += [x.strip() for x in pages(ial)[i - 1].split("\n") if x.strip()]
    rows, cur = {}, None
    k = 0
    while k < len(toks):
        x = toks[k]
        m = re.match(r"SERIES 2022, TRANCHE (A-\d)", x)
        if m:
            cur = m.group(1)
            rows[cur] = []
        elif cur and _DATE.match(x):
            vals = []
            k += 1
            while k < len(toks) and _NUM.match(toks[k]) and len(vals) < 4:
                vals.append(None if toks[k] == "-" else money(toks[k]))
                k += 1
            if len(vals) == 1:
                rows[cur].append({"date": mdy(x), "balance": vals[0], "interest": 0.0, "principal": 0.0, "total": 0.0})
            elif len(vals) == 4:
                if vals[1] is not None:
                    rows[cur].append({"date": mdy(x), "balance": vals[0] or 0.0, "interest": vals[1],
                                      "principal": vals[2] or 0.0, "total": vals[3]})
            else:
                raise ValueError(f"{ial}: row {x} has {len(vals)} values")
            continue
        k += 1
    if set(rows) != set(tr):
        raise LookupError(f"{ial}: schedule tranches {sorted(rows)} vs terms {sorted(tr)}")
    for name, rr in rows.items():
        tr[name]["principal"] = rr[0]["balance"]
        if abs(sum(r["principal"] for r in rr) - rr[0]["balance"]) > 0.05:
            raise ValueError(f"{ial} {name}: principal payments do not retire the balance")
        for r in rr[1:]:
            if abs(r["interest"] + r["principal"] - r["total"]) > 0.015:
                raise ValueError(f"{ial} {name} {r['date']}: interest + principal != total")
    if abs(sum(x["principal"] for x in tr.values()) - amount) > 0.05:
        raise ValueError(f"{ial}: tranches do not sum to the amount issued")
    return {"closing": closing, "amount": amount, "tranches": tr, "wal_stated": wal, "wavg_stated": wavg,
            "schedule": rows}


def ok_charges(u):
    """Residential monthly charges, $ per bill: initial (IAL) and latest true-up."""
    if u == "ong":
        t = flat(OK[u]["ial"], 14)
        a = re.search(r"Rate Choice A ([\d.]+)% \$([\d.]+) \$([\d.]+)", t)
        b = re.search(r"Rate Choice B ([\d.]+)% \$([\d.]+) \$([\d.]+)", t)
        n = flat(OK[u]["ial"], 14)
        na = int(re.search(r"Rate Choice A ([\d,]+) Tariff s?101", n[n.index("Threshold"):]).group(1).replace(",", ""))
        nb = int(re.search(r"Rate Choice B ([\d,]+) Tariffs 200", n[n.index("Threshold"):]).group(1).replace(",", ""))
        tu = flat(OK[u]["trueup"], 14)
        a2 = re.search(r"Rate Choice A ([\d.]+)% \$([\d.]+) \$([\d.]+)", tu)
        b2 = re.search(r"Rate Choice B ([\d.]+)% \$([\d.]+) \$([\d.]+)", tu)
        eff = re.search(r"(\d\d/\d\d/\d\d) WESCR Charge Estimate 1,2 (\d\d/\d\d/\d\d) WESCR Charge Estimate", tu)
        tier = quote(OK[u]["order"], r"[^.]{0,200}50 Dth[^.]{0,200}\.").group(0) if re.search(r"50 Dth", flat(OK[u]["order"])) else None
        return {"classes": {
            "A": {"alloc": float(a.group(1)) / 100, "initial": float(a.group(2)), "customers": na,
                  "latest": float(a2.group(2)), "next_est": float(a2.group(3)), "alloc_latest": float(a2.group(1)) / 100},
            "B": {"alloc": float(b.group(1)) / 100, "initial": float(b.group(2)), "customers": nb,
                  "latest": float(b2.group(2)), "next_est": float(b2.group(3)), "alloc_latest": float(b2.group(1)) / 100}},
            "latest_from": mdy(eff.group(1)), "next_from": mdy(eff.group(2)), "tier": tier}
    t = flat(OK[u]["ial"], 13)
    r = re.search(r"Residential ([\d.]+)% \$([\d.]+)", t)
    tu = flat(OK[u]["trueup"], 6)
    r2 = re.search(r"Residential \$([\d.]+)", tu)
    return {"classes": {"R": {"alloc": float(r.group(1)) / 100, "initial": float(r.group(2)), "latest": float(r2.group(1))}},
            "latest_from": None}


def ok_costs(u):
    """The order's extreme purchase costs and the dates it gives for them; raises if the sentence is gone."""
    m = quote(OK[u]["order"], r"Extreme Purchase Costs estimated to be in the total amount of \$([\d,]+)\. The Stipulating "
                              r"Parties further agree that this figure represents the Company.s Extreme Purchase Costs "
                              r"incurred beginning (\w+ \d+, 2021), and ending (\w+ \d+, 2021)")
    alloc = quote(OK[u]["order"], r"allocated among (?:WESCR )?Customer Classes based on actual usage during the month of "
                                  r"February 2021").group(0)
    ial = flat(OK[u]["ial"])
    reserve = money(re.search(r"Debt Service Reserve Subaccount \(DSRS\) \$([\d,.]+)", ial).group(1))
    # summed from the lines, because the two letters' "Total" rows differ: ONG's leaves out the non-utility
    # costs and Summit's includes them
    non = money(re.search(r"Total Non-Utility External Annual Ongoing Financing Costs \$([\d,.]+)", ial).group(1))
    fee = money(re.search(r"Ongoing Servicer Fees \(Utility as Servicer\) \$([\d,.]+)", ial).group(1))
    acct = money(re.search(r"Accounting Costs \(External\)\^? \$([\d,.]+)", ial).group(1))
    ongoing = non + fee + acct
    return {"extreme": money(m.group(1)), "from": m.group(2), "to": m.group(3), "alloc_basis": alloc,
            "reserve": reserve, "ongoing_year": ongoing}


def ok_first_bill_suo():
    """The first month the Summit workpaper shows charges collected (IAL p15; claims ledger 5)."""
    t = flat(OK["suo"]["ial"], 15)
    for m in re.finditer(r"(\d+)/(\d+)/(\d{4}) ([\d,]+|-) ", t):
        if m.group(4) != "-":
            return int(m.group(3)), int(m.group(1))
    raise LookupError("ok_suo_ial.pdf p15: no month with charges collected")


def eia_base():
    m = quote("eia_glossary_c.html", r"Cubic foot \(cf\), natural gas: .*?\((60 degrees Fahrenheit and ([\d.]+) pounds standard "
                                     r"per square inch)\)")
    return {"text": m.group(1), "psia": float(m.group(2))}


def ok_res_customers_suo():
    """Summit's residential customer count in the IAL workpaper's first period, at its last month."""
    t = flat(OK["suo"]["ial"], 15)
    return int(re.search(r"9/30/2023 ([\d,]+) [\d,]+ [\d,]+ \d+ Customer Count", t).group(1).replace(",", ""))


def tx_upfront():
    """The official statement's uses of proceeds (p28) and the reserve's application (p128)."""
    t = flat(TX_OS, 28)
    m = re.search(r"net of underwriters. discount of \$([\d,.]+), net of the deposit to the Up-Front Financing Costs "
                  r"Account of \$([\d,.]+) \(which includes 6 months of capitalized interest and 6 months of initial "
                  r"Bond Administrative Expenses\), net of the deposit to the Issuer Expense Reserve Account in the "
                  r"amount of \$([\d,.]+) .*?net of the deposit to the Reserve Subaccount of \$([\d,.]+)", t)
    applied = quote(TX_OS, r"reduced to zero upon application of the amount on deposit in the Reserve Subaccount to the "
                           r"last principal payment of the Bonds", 128).group(0)
    zero = quote(TX_OS, r"zero dollars \(\$0\.00\) per Mcf through September 2023").group(0)
    bills = quote(TX_OS, r"On March 2, 2023, Senate Bill 30 \(\"SB 30\"\) was filed, and on March 7, 2023, House Bill 500 "
                         r"\(\"HB 500\"\) was filed", 28).group(0)
    unused = quote(TX_OS, r"if the actual Up-Front Financing Costs are less than the Up-Front Financing Costs included in "
                          r"the principal amount of the Bonds, the Periodic Billing Requirement for the first Scheduled "
                          r"True-Up Adjustment will be reduced by the amount of such unused funds").group(0)
    return {"unused": unused, "underwriting": money(m.group(1)), "upfront_account": money(m.group(2)), "issuer_reserve": money(m.group(3)),
            "reserve": money(m.group(4)), "reserve_applied": applied, "zero_until": zero, "bills": bills}


def tx_rate_history():
    """[(first billing month, $ per Mcf at 14.65 psia, source)] as the filings state them. Each utility's
    true-up lands in late September or October; the page bills each rate from October of its year."""
    r = tx_rates()
    a = quote("tx_atmos_midtex_2025-07.pdf", r"EFFECTIVE DATE: (10/01/2024)", 104)
    a_rate = quote("tx_atmos_midtex_2025-07.pdf", r"monthly volumetric rate of \$([\d.]+)/Ccf", 104)
    g = quote("tx_tgs_crr.pdf", r"monthly volumetric rate of \$([\d.]+)/Ccf")
    gd = quote("tx_tgs_crr.pdf", r"Meters Read On and After September 25, 2024 (September 24, 2025)")
    m = quote("tx_tariff_6776.pdf", r"True-up Adjustment Letter dated September 10, 2026.{0,200}?Rate to be effective "
                                    r"(October 1, 2026)", 3)
    m_rate = quote("tx_tariff_6776.pdf", r"monthly volumetric rate of ([\d.]+)/Ccf", 6)
    c = quote("tx_tariff_6263.pdf", r"monthly volumetric rate of \$([\d.]+)/Ccf @14\.65 \$([\d.]+)/Ccf @14\.73", 39)
    return {"steps": [("2023-10", r["first"]["per_mcf"], "RRC, October 1, 2023"),
                      ("2024-10", 10 * float(a_rate.group(1)), "Atmos Mid-Tex, effective " + a.group(1)),
                      ("2025-09", 10 * float(g.group(1)), "Texas Gas Service, meters read on and after " + gd.group(1)),
                      ("2026-10", 10 * float(m_rate.group(1)), "Atmos Mid-Tex, effective " + m.group(1))],
            "tgs_now": r["tgs"]["per_mcf"], "cnp_1465": float(c.group(1)), "cnp_1473": float(c.group(2))}


def ok_class_table(u):
    """Every class's monthly charge in the latest true-up, as the letter names the class: [(class, $)]."""
    if u == "ong":
        t = flat(OK[u]["trueup"], 14)
        seg = t[t.index("Estimate 1,2 Tariffs") + len("Estimate 1,2 "):t.index("Total 100.00%")]
        rows = re.findall(r"(Tariffs? ?s?[\w &-]+?) [\d.]+% \$([\d,.]+) \$([\d,.]+)", seg)
    else:
        t = flat(OK[u]["trueup"], 6)
        rows = [(c, v, None) for c, v in re.findall(r"(Residential|GS1|CS1|LCS) \$([\d,.]+)", t)]
    if len(rows) < 4:
        raise LookupError(f"{OK[u]['trueup']}: class table has {len(rows)} rows")
    return [(c.strip(), money(v), None if n is None else money(n)) for c, v, n in rows]


# ------------------------------------------------------------------ EIA ---
def _eia(code):
    p, _ = verified(f"eia_{code}a.xls")
    sh = xlrd.open_workbook(str(p)).sheet_by_index(1)
    return {xlrd.xldate_as_tuple(sh.cell_value(r, 0), 0)[0]: sh.cell_value(r, 1)
            for r in range(3, sh.nrows) if sh.cell_value(r, 1) != ""}


def eia_home(st):
    """{year: Mcf per residential consumer} for the years both series carry."""
    cons, num = _eia(f"N3010{st}2"), _eia(f"NA1501_S{st}_8")
    return {y: cons[y] * 1000 / num[y] for y in sorted(set(cons) & set(num))}
