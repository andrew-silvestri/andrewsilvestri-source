"""Checks for the takeaway page (03 RESEARCH/takeaway/PLAN.md section 6).

Each check has a --break that injects the fault it exists to catch, and the
broken run must exit 1 (HANDOFF trap 26). Run them all:

    python test_takeaway.py
    python test_takeaway.py --break month|district|days|tracker|employer|sign|page|pdq
                                    |preanchor|gap|t0|tarzan|count|app

1. Reconciliation (the packet's test). The monthly ratio of the RRC's Texas
   Permian (gross) to EIA's Permian region (marketed), over the settled
   overlap, stays inside BAND and its standard deviation under SD_MAX. BAND
   is frozen: mean 0.7119 +/- 4 sd (sd 0.0159), fitted on 2022-01..2026-01
   from the October 2026 STEO and the RRC extract of 2026-09-18. It is
   in-sample by construction; its job is to catch a broken join, unit or
   month alignment, not to forecast the ratio, whose annual mean fell from
   0.732 (2022) to 0.698 (2025). Its blind spot is stated and printed: a
   month at the mean, pushed 5% off, stays inside the band (0.7475 against
   0.776); only months already near an edge would be caught. A refit is a change with
   its own commit.
   --break month: one RRC month x 1.15. Must fail.
2. District identity. The RRC workbook equals districts 7C + 08 + 8A from
   the stored PDQ web files, every filed month, to the Mcf.
   --break district: drop 8A. Must fail.
3. Units. Mcf/month to Bcf/d uses the month's own day count; checked on
   2024-01 (31 days) and 2024-02 (29). An identity check, named as one: no
   source prints the RRC series in Bcf/d.
   --break days: 30 days for every month. Must fail.
4. Capacity. An independent openpyxl read of the tracker (not
   capacity._tracker) agrees with every tracker-derived capacity and date;
   every overlay carries a source and a quote; no EXCLUDED name is listed.
   And the internship employer's name is nowhere under takeaway/ or on the
   rendered page: each word and adjacent word pair is hashed against a
   stored SHA-256, so the name itself is not in the tree.
   --break tracker: one capacity altered in capacity's copy only. Must fail.
   --break employer: a fixture containing the name (built from bytes at run
   time, so the name is still not in the file). Must fail.
5. Headroom, where the sign matters. Synthetic: capacity flat, production
   up 1.0 Bcf/d at month m, so H = 0 before m and exactly -k from m;
   production flat, a pipe of s at m, so H = +s from m. On the payload: H at
   the last historical month equals a hand sum of that month's additions
   since t0 less k times EIA's change.
   --break sign: the production term's sign flipped. Must fail.
6. Page numbers against the payload (R2 page): numbers re-derived here from
   the payload (not through update_page.values) must be the ones the shipped
   page prints, takeaways and readings table included.
   --break page: the default reading perturbed before deriving. Must fail.
7. The PDQ dump reduction (Q2, PLAN 3.5), read from the file the build reads
   (data/pdq_district_month.csv, re-hashed by sources.pdq_reduced): no
   disposition row with vented or flared gas lacks a lease-cycle row; lease
   sums equal the dump's own district table for every Permian district and
   month; the dump's district numbers 09, 10, 11 are named 7C, 08, 8A; and
   the production side that sources.rrc_vented_flared() divides by equals the
   RRC Permian workbook, every month both carry, to the Mcf.
   --break pdq: read the dump's DISTRICT_NO as if it were the district's
   name, the likeliest slip (the dump's "08" is district 7B). Must fail.

8. (R2) The lines counted before the May 2022 anchor agree with an
   independent read of the tracker, and the hero's pipe line at its first
   month is minus exactly those and the confirmed lines up to t0.
   --break preanchor: a line (Gulf Coast Express) missing. Must fail.
9. (R2) The DPR splice: the frozen ratio inside its fitted range; the live
   overlap, while it is 12 months or more, still inside it; and a STEO window
   that no longer meets DPR (the 2028 release) stops the build (review 1).
   --break gap: p_long without its gap check. Must fail.
10. (R2) The hero's gap is model.headroom() from the raw files, every month,
   and the default reading equals the record's own H.
   --break t0: recompute with t0 a month later. Must fail.
11. (R2) Readings: Hugh Brinson at full = H_with_expected; Tarzan dropped =
   default less its capacity; the k readings in k order.
   --break tarzan: the Tarzan reading set to the default. Must fail.
12. (R2) The hero's bars are Reuters's counts as cited.py parses them from the
   quote; a year the list does not name is a dash, never 0 (review 5).
   --break count: one bar's value moved. Must fail.
13. (R2) The page has no rail, no app link and no old figure, and has its stamp
   and hero.
   --break app: a link to takeaway-app.html. Must fail.

The app, its engine and tests/test_parity_takeaway.py were dropped in R2.
"""
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import capacity        # noqa: E402
import model as M      # noqa: E402
import reconcile       # noqa: E402
import sources         # noqa: E402

BAND = (0.648, 0.776)
SD_MAX = 0.03
EMPLOYER_SHA256 = "1ef1fd8191049565d677cad32dcd9c696ab37863567dea7bcc447c97f27d2c1d"
PAGE = os.path.join(ROOT, "site", "takeaway.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")

BREAK = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
fails = []


def check(name, ok, detail=""):
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
    if not ok:
        fails.append(name)


# ------------------------------------------------------------------ 1
def reconciliation():
    rrc = reconcile.rrc_settled()
    steo = sources.steo_permian()
    if BREAK == "month":
        # A month inside the overlap: the first version took the middle of the
        # whole RRC series, 2017, which the check never reads, and the broken
        # run passed. So the mutation now proves it landed.
        overlap = sorted(set(rrc) & set(steo))
        k = overlap[len(overlap) // 2]
        before = reconcile.ratio_table(rrc, steo)[k]
        rrc[k] *= 1.15
        assert reconcile.ratio_table(rrc, steo)[k] != before, "the month mutation did not reach the ratio"
    r = reconcile.ratio_table(rrc, steo)
    s = reconcile.summary(r)
    check("1 reconciliation: every month inside the band", BAND[0] <= s["min"] and s["max"] <= BAND[1],
          f"n={s['n']} {s['first']}..{s['last']}, range {s['min']:.4f}..{s['max']:.4f}, band {BAND}")
    check("1 reconciliation: sd under the limit", s["sd"] < SD_MAX, f"sd {s['sd']:.4f} < {SD_MAX}")
    print(f"       blind spot, printed not asserted: the largest ratio x 1.05 = {s['max'] * 1.05:.4f}, "
          f"the mean x 1.05 = {s['mean'] * 1.05:.4f}; a single month 5% off passes if under {BAND[1]}")


# ------------------------------------------------------------------ 2
def district_identity():
    mcf = sources.rrc_permian_mcf()
    D = {d: sources.pdq_district(d) for d in sources.PDQ_DISTRICTS if not (BREAK == "district" and d == "8A")}
    bad = []
    for t, (cs, gw) in mcf.items():
        s = [D[d].get(t) for d in D]
        if any(x is None for x in s):
            bad.append((t, "missing"))
            continue
        if sum(c for c, _ in s) != cs or sum(g for _, g in s) != gw:
            bad.append(t)
    check("2 RRC workbook = 7C + 08 + 8A, every filed month, to the Mcf", not bad,
          f"{len(mcf)} months, {len(bad)} differ" + (f", first {bad[0]}" if bad else ""))


# ------------------------------------------------------------------ 7
def pdq_check():
    meta, rows = sources.pdq_reduced()
    orig = dict(sources.PDQ_CODES)
    codes = dict(orig)
    if BREAK == "pdq":
        sources.PDQ_CODES = {name: name for name in codes}
        codes = dict(sources.PDQ_CODES)
    perm = [r for r in rows if r["district_no"] in codes.values()]
    check("7 PDQ: no vented-or-flared row without a lease-cycle row",
          sum(int(r["join_misses"]) for r in rows) == 0 and meta["rows"]["disp_with_vf"] > 0,
          f"{meta['rows']['disp_with_vf']:,} rows with code 4, "
          f"{sum(int(r['join_misses']) for r in rows)} unmatched")
    bad = [r["cycle_year_month"] for r in perm if r["dist_table_gas_mcf"] != "" and (
        r["prod_gas_mcf"] != r["dist_table_gas_mcf"] or r["prod_csgd_mcf"] != r["dist_table_csgd_mcf"])]
    check("7 PDQ: lease sums = the dump's district table, every Permian district-month", perm and not bad,
          f"{len(perm)} district-months, {len(bad)} differ")
    names = {r["district_no"]: r["district_name"] for r in perm}
    check("7 PDQ: the dump's district numbers carry the names the page uses",
          all(names.get(code) == name for name, code in codes.items()), f"{names}")
    vf = sources.rrc_vented_flared()
    mcf = sources.rrc_permian_mcf()
    common = sorted(set(vf) & set(mcf))
    diff = [t for t in common if vf[t][1] != sum(mcf[t])]
    check("7 PDQ: the share's denominator = the RRC Permian workbook, to the Mcf", len(common) > 200 and not diff,
          f"{len(common)} months in both, {len(diff)} differ" + (f", first {diff[0]}" if diff else ""))
    sources.PDQ_CODES = orig


# ------------------------------------------------------------------ 3
def units():
    import calendar
    mcf = sources.rrc_permian_mcf()
    got = sources.rrc_permian()
    for t in ((2024, 1), (2024, 2)):
        days = 30 if BREAK == "days" else calendar.monthrange(*t)[1]
        want = sum(mcf[t]) / days / 1e6
        check(f"3 units: {t[0]}-{t[1]:02d} Mcf/month to Bcf/d over {days} days", abs(got[t] - want) < 1e-12,
              f"{got[t]:.6f} vs {want:.6f}")


# ------------------------------------------------------------------ 4
def _tracker_independently():
    import openpyxl
    path, _ = sources.verified(capacity.TRACKER)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = {}
    for sheet in ("Natural Gas Pipeline Projects", "Historical Projects (1996-2024)"):
        rows = list(wb[sheet].iter_rows(values_only=True))
        hdr = list(rows[1])
        ic, icd, ist = hdr.index("Additional Capacity (MMcf/d)"), hdr.index("Completed Date"), hdr.index("Status")
        for r in rows[2:]:
            if r[1]:
                out[r[1].strip()] = (r[ic], r[icd], str(r[ist]).strip())
    return out


def capacity_check():
    t = _tracker_independently()
    if BREAK == "tracker":
        orig = capacity._mmcfd
        capacity._mmcfd = lambda v, _o=orig: _o(v) * (1.1 if _o(v) == 2500 else 1.0)
    bad = []
    for e, p in zip(capacity.entries_unsorted(), capacity.PROJECTS):
        cap_raw, cd, status = t[p["name"].strip()]
        mmcfd = float(str(cap_raw).split()[0]) * (p["phase"][1] if "phase" in p else 1.0)
        if abs(e["bcfd"] * 1000 - mmcfd) > 1e-9:
            bad.append((e["name"], "capacity", e["bcfd"], mmcfd))
        if "overlay" not in p:
            if not (status == "Completed" and isinstance(cd, dt.datetime) and e["month"] == (cd.year, cd.month)):
                bad.append((e["name"], "date"))
        else:
            ov = p["overlay"]
            if not (ov["source"][0] and ov["source"][2]):
                bad.append((e["name"], "overlay without source or quote"))
    check("4 capacity list agrees with an independent read of the tracker", not bad, f"{len(bad)} problems {bad[:2]}")
    names = {p["name"].strip() for p in capacity.PROJECTS}
    clash = [n for n in capacity.EXCLUDED if n in names]
    check("4 no excluded line is on the list", not clash, str(clash))


def _words(text):
    w = re.findall(r"[a-z0-9]+", text.lower())
    return w + [a + " " + b for a, b in zip(w, w[1:])]


def employer_check():
    files = []
    for dirpath, dirnames, filenames in os.walk(HERE):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "raw")]
        files += [os.path.join(dirpath, f) for f in filenames
                  if f.endswith((".py", ".html", ".js", ".json", ".md", ".txt"))]
    texts = [(f, open(f, encoding="utf-8", errors="replace").read()) for f in files]
    if os.path.exists(PAGE):
        texts.append((PAGE, open(PAGE, encoding="utf-8").read()))
    if BREAK == "employer":
        texts.append(("fixture", "operated by " + bytes([84, 97, 114, 103, 97]).decode() + " Resources"))
    hits = [f for f, t in texts if any(hashlib.sha256(w.encode()).hexdigest() == EMPLOYER_SHA256 for w in _words(t))]
    check("4 the employer is named nowhere under takeaway/ or on the page", not hits,
          f"{len(texts)} files scanned" + (f"; found in {[os.path.basename(h) for h in hits]}" if hits else ""))


# ------------------------------------------------------------------ 5
def headroom_check():
    sign = -1.0 if BREAK == "sign" else 1.0

    def H(P, adds, k, t0, months):
        p0 = P[t0]
        return {t: M.capacity_added(adds, t0, t) - sign * k * (P[t] - p0) for t in months}
    run = M.headroom if BREAK != "sign" else H
    months = M.month_range((2024, 1), (2024, 12))
    m, k = (2024, 6), 0.8
    P = {t: 10.0 + (1.0 if t >= m else 0.0) for t in months}
    h = run(P, [], k, (2024, 1), months)
    check("5 production step of +1 at m gives H = -k from m, 0 before",
          all(abs(h[t] - (-k if t >= m else 0.0)) < 1e-12 for t in months), f"H(m) = {h[m]:+.3f}, want {-k:+.3f}")
    P = {t: 10.0 for t in months}
    h = run(P, [(m, 2.5)], k, (2024, 1), months)
    check("5 a pipe of 2.5 at m gives H = +2.5 from m, 0 before",
          all(abs(h[t] - (2.5 if t >= m else 0.0)) < 1e-12 for t in months), f"H(m) = {h[m]:+.3f}")
    pay = json.load(open(PAYLOAD, encoding="utf-8"))
    last, t0 = pay["steo"]["last_historical"], pay["t0"]
    added = sum(e["bcfd"] for e in pay["entries"] if e["status"] == "confirmed" and t0 < e["month"] <= last)
    want = added - pay["k"]["default"] * (pay["steo"]["P"][last] - pay["steo"]["P"][t0])
    got = pay["H"][last] if BREAK != "sign" else added + pay["k"]["default"] * (pay["steo"]["P"][last] - pay["steo"]["P"][t0])
    check(f"5 payload H at {last} equals the hand sum", abs(got - want) < 1e-12, f"{got:+.4f} vs {want:+.4f}")


# ------------------------------------------------------------------ 6
def _page_text():
    t = open(PAGE, encoding="utf-8").read()
    main = t[t.index("<main"):t.index("<h2>Sources") if "<h2>Sources" in t else len(t)]
    main = re.sub(r'<script type="application/json".*?</script>', " ", main, flags=re.S)
    return t, html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", main))).replace("−", "-")


def page_numbers():
    pay = json.load(open(PAYLOAD, encoding="utf-8"))
    S = pay["story"]
    if BREAK == "page":
        S["readings"][0]["H"] += 0.37
    _, text = _page_text()
    Y = {r["year"]: r for r in S["years"]}
    since21 = [r for r in S["years"] if "vf_share" in r and r["year"] >= 2021]
    big = S["lines"]
    months = [l["months_default"] for l in big] + [l["months_low"] for l in big]
    derived = {
        "pace range (takeaway 1)": f"on average, {S['pace']['k_fit']:.1f} to {S['pace']['default']:.1f} billion cubic feet",
        "months range (takeaway 1)": f"holds only {min(months):.0f} to {max(months):.0f} months",
        "flaring 2019 share": f"{100 * Y[2019]['vf_share']:.1f} per cent of their gas in 2019",
        "flaring max since 2021": f"no more than {100 * max(r['vf_share'] for r in since21):.1f} per cent",
        "flaring 2019 volume": f"{Y[2019]['vf_bcfd']:.2f} Bcf/d was vented or flared in 2019",
        "pace default": f"grown by {S['pace']['default']:.2f} Bcf/d a year",
        "Matterhorn recovery": f"Matterhorn Express {big[3]['recovery_months']}.",
        "default reading row": f"Default: k = {pay['k']['default']:.3f}, lines confirmed in service "
                               f"{S['readings'][0]['H']:+.2f} {len(S['readings'][0]['below'])}",
        "headline magnitude": f"carry {abs(S['readings'][0]['H']):.2f} Bcf/d",
        "two-point k": f"as full as August 2024 is {S['k_fit']['list']:.2f}",
        "2019 reference, default": f"gives {S['H_ref_2019']['default']:+.2f} Bcf/d of room that month",
        "EIA Permian k": f"or {S['k_permian']['net']:.3f} less fuel",
        "oil-well share": f"{100 * pay['csgd']['share']:.0f} per cent of the gas",
        "k default": f"({pay['k']['default']:.3f})",
    }
    missing = [n for n, s in derived.items() if s not in text]
    check("6 numbers derived from the payload are the ones the page prints", not missing,
          f"{len(derived)} checked" + (f"; not on the page: {missing}" if missing else ""))


# ------------------------------------------------------------------ 8
def pre_anchor_check():
    """The lines counted before the anchor, read independently from the tracker,
    and the hero's pipe line at its first month built from exactly them."""
    t = _tracker_independently()
    pay = json.load(open(PAYLOAD, encoding="utf-8"))
    S = pay["story"]
    bad = []
    for e in S["pre_anchor"]:
        cap_raw, cd, status = t[e["name"]]
        if not (status == "Completed" and isinstance(cd, dt.datetime) and e["month"] == f"{cd.year}-{cd.month:02d}"
                and abs(e["bcfd"] * 1000 - float(cap_raw)) < 1e-9):
            bad.append(e["name"])
    check("8 pre-anchor lines agree with an independent read of the tracker", S["pre_anchor"] and not bad, str(bad))
    pipe0 = S["hero"]["pipe"][0]
    if BREAK == "preanchor":
        # the fault: a line missing from the list (here Gulf Coast Express)
        pipe0 += next(e["bcfd"] for e in S["pre_anchor"] if e["name"] == "Gulf Coast Express")
    x0, t0 = S["hero"]["x"][0], pay["t0"]
    want = -(sum(e["bcfd"] for e in S["pre_anchor"] if e["month"] > x0)
             + sum(e["bcfd"] for e in pay["entries"] if e["status"] == "confirmed" and e["month"] <= t0))
    check(f"8 the hero's pipe line at {x0} is minus every listed line from then to {t0}", abs(pipe0 - want) < 1e-9,
          f"{pipe0:+.3f} vs {want:+.3f}")


# ------------------------------------------------------------------ 9
def splice_check():
    import story
    lo, hi = story.SPLICE_RANGE
    check("9 the frozen splice ratio lies inside the range it was fitted over", lo <= story.SPLICE <= hi,
          f"{story.SPLICE} in {story.SPLICE_RANGE}")
    steo, dpr = sources.steo_permian(), sources.dpr_permian()
    ov = [t for t in steo if t in dpr]
    if len(ov) >= 12:
        m = sum(steo[t] / dpr[t] for t in ov) / len(ov)
        check("9 the live STEO/DPR overlap still averages inside the frozen range", lo <= m <= hi,
              f"{len(ov)} months, mean {m:.4f}")
    else:
        print(f"       overlap now {len(ov)} months (< 12): the frozen ratio stands alone, as designed")
    # the 2028 case: STEO's window starts after DPR ends; p_long must refuse
    late = {t: v for t, v in steo.items() if t >= (2024, 1)}
    orig = story.p_long
    if BREAK == "gap":
        story.p_long = lambda P, d: {**{t: v * story.SPLICE for t, v in d.items()}, **P}   # the check removed
    try:
        story.p_long(late, dpr)
        raised = False
    except RuntimeError:
        raised = True
    story.p_long = orig
    check("9 a STEO window that no longer meets DPR stops the build", raised)


# ------------------------------------------------------------------ 10
def hero_check():
    """The hero's gap is model.headroom(), month by month, from the raw files."""
    import story
    pay = json.load(open(PAYLOAD, encoding="utf-8"))
    S = pay["story"]
    t0 = tuple(int(x) for x in pay["t0"].split("-"))
    if BREAK == "t0":
        t0 = M.add_months(t0, 1)
    P = story.p_long(sources.steo_permian(), sources.dpr_permian())
    adds = [(tuple(int(x) for x in e["month"].split("-")), e["bcfd"]) for e in S["pre_anchor"]] + \
           [(tuple(int(x) for x in e["month"].split("-")), e["bcfd"]) for e in pay["entries"] if e["status"] == "confirmed"]
    months = [tuple(int(x) for x in k.split("-")) for k in S["hero"]["x"]]
    H = M.headroom(P, adds, pay["k"]["default"], t0, months)
    bad = [m for i, m in enumerate(months) if abs((S["hero"]["pipe"][i] - S["hero"]["gas"][i]) - H[m]) > 1e-9]
    check("10 hero: pipe minus gas = model.headroom() every month", not bad,
          f"{len(months)} months, {len(bad)} differ" + (f", first {bad[0]}" if bad else ""))
    d = next(r for r in S["readings"] if r["name"] == "default")
    check("10 the default reading = the record's own H at the last month (build_takeaway path)",
          abs(d["H"] - pay["H"][pay["steo"]["last_historical"]]) < 1e-9, f"{d['H']:+.4f}")


# ------------------------------------------------------------------ 11
def readings_check():
    pay = json.load(open(PAYLOAD, encoding="utf-8"))
    S = pay["story"]
    rd = {r["name"]: r for r in S["readings"]}
    last = pay["steo"]["last_historical"]
    hb = rd["hb_full"]["H"]
    if BREAK == "tarzan":
        rd["no_tarzan"]["H"] = rd["default"]["H"]
    tz = next(e for e in pay["entries"] if e["name"].startswith("Tarzan"))
    check("11 Hugh Brinson at full = the build's H_with_expected at the last month",
          abs(hb - pay["H_with_expected"][last]) < 1e-9, f"{hb:+.4f}")
    check("11 Tarzan dropped = default less Tarzan's capacity",
          abs(rd["no_tarzan"]["H"] - (rd["default"]["H"] - tz["bcfd"])) < 1e-9, f"{rd['no_tarzan']['H']:+.4f}")
    check("11 the k readings fall in k order (a higher k, less room)",
          rd["k_hi"]["H"] < rd["default"]["H"] < rd["k_lo"]["H"] < rd["k_permian"]["H"] < rd["k_fit"]["H"])


# ------------------------------------------------------------------ 12
def bars_check():
    import cited
    t, _ = _page_text()
    spec = json.loads(re.search(r'<script type="application/json" class="scrolly-spec">(.*?)</script>', t, re.S)
                      .group(1).replace("<\\/", "</"))
    bars = spec["under"][0]["bars"]
    if BREAK == "count":
        bars[0]["value"] += 1
    rc = cited.reuters_counts()
    bad = [b for b in bars if (int(b["at"]) in rc and (b["value"], b["text"]) != (rc[int(b["at"])], str(rc[int(b["at"])])))
           or (int(b["at"]) not in rc and (b["value"], b["text"]) != (0, "–"))]
    check("12 the hero's bars are Reuters's counts, unnamed years a dash", bars and not bad, str(bad[:2]))


# ------------------------------------------------------------------ 13
def page_shape():
    t, _ = _page_text()
    if BREAK == "app":
        t = t.replace("</main>", '<a href="takeaway-app.html">app</a></main>')
    probs = [p for p, bad in (("marginalia", 'class="marginalia' in t), ("app link", "takeaway-app.html" in t),
                              ("old figure", "takeaway_headroom" in t or "takeaway_capacity" in t),
                              ("no stamp", 'class="stamp"' not in t), ("no hero", 'id="takeaway-hero"' not in t)) if bad]
    check("13 page: no rail, no app, no old figures; stamp and hero present", not probs, str(probs))


def main():
    for f in (reconciliation, district_identity, units, capacity_check, employer_check, headroom_check, page_numbers,
              pdq_check, pre_anchor_check, splice_check, hero_check, readings_check, bars_check, page_shape):
        f()
    print(("FAIL: " + ", ".join(fails)) if fails else "all checks pass", "(break run: " + BREAK + ")" if BREAK else "")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
