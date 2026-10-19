"""Checks for the takeaway page (03 RESEARCH/takeaway/PLAN.md section 6).

Each check has a --break that injects the fault it exists to catch, and the
broken run must exit 1 (HANDOFF trap 26). Run them all:

    python test_takeaway.py
    python test_takeaway.py --break month|district|days|tracker|employer|sign|page

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
6. Page numbers against the payload: numbers re-derived here from the
   payload (not through update_page.values) must be the ones the shipped
   page prints.
   --break page: one payload number perturbed before deriving. Must fail.

The JavaScript engine is held to model.py by tests/test_parity_takeaway.py.
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
def page_numbers():
    pay = json.load(open(PAYLOAD, encoding="utf-8"))
    if BREAK == "page":
        pay["steo"]["P"][pay["steo"]["last_historical"]] += 0.37
    t = open(PAGE, encoding="utf-8").read()
    main = t[t.index("<main"):t.index("<h2>Sources") if "<h2>Sources" in t else len(t)]
    text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", main))).replace("−", "-")
    last, t0 = pay["steo"]["last_historical"], pay["t0"]
    P = pay["steo"]["P"]
    k = pay["k"]["default"]
    ent = pay["entries"]
    conf = [e for e in ent if e["status"] == "confirmed"]
    exp = [e for e in ent if e["status"] == "expected"]
    dP = P[last] - P[t0]
    added = sum(e["bcfd"] for e in conf if t0 < e["month"] <= last)
    fl = pay["flaring"]
    c = [x for x in fl["clusters"] if "diff" in x]
    derived = {
        "production now": f"{P[last]:.2f} Bcf/d",
        "pipe added since t0": f"{added:.2f} Bcf/d of pipe",
        "production rise": f"risen {dP:.2f} Bcf/d",
        "gas to move": f"of which {k * dP:.2f} has to leave",
        "headroom": f"at {added - k * dP:+.2f} Bcf/d: on this accounting",
        "k": f"k = {k:.3f}",
        "in-service total": f"{len(conf)} additions are in service, {sum(e['bcfd'] for e in conf):.2f} Bcf/d",
        "expected total": f"Another {sum(e['bcfd'] for e in exp):.2f} Bcf/d",
        "pin before": f"grew {pay['pin']['before']:.2f} Bcf/d",
        "pin after": f"and {pay['pin']['after']:.2f} Bcf/d over the three after",
        "flaring 2019": f"averaged {100 * c[0]['before']:.2f} per cent",
        "flaring 2021": f"went from {100 * c[1]['before']:.2f} to {100 * c[1]['after']:.2f} per cent",
        "oil-well share": f"{100 * pay['csgd']['share']:.0f} per cent of the gas",
        "reconciliation": f"(mean {pay['reconcile']['mean']:.2f})",
        "anchor": f"{P[pay['anchor']['month']]:.2f} against",
    }
    missing = [n for n, s in derived.items() if s not in text]
    check("6 numbers derived from the payload are the ones the page prints", not missing,
          f"{len(derived)} checked" + (f"; not on the page: {missing}" if missing else ""))


def main():
    for f in (reconciliation, district_identity, units, capacity_check, employer_check, headroom_check, page_numbers):
        f()
    print(("FAIL: " + ", ".join(fails)) if fails else "all checks pass", "(break run: " + BREAK + ")" if BREAK else "")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
