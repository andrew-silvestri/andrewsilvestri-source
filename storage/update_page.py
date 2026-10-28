"""
Write site/storage.html from template.html, outputs/payload.json (build_storage.py) and
data/imm.json (the market monitor's quotes and the values read off its Figure 17).

Every number on the page comes from the payload, from imm.json, from model.py (the ATB cost
reference, the AC hours) or from a file this script measures (the archive's size); the prose is in
the template. The parts other scripts own - the nav (rebuild_nav.py), the citation markers and
Sources (add_citations.py's table, applied here) and the ?v= stamps (bust_cache.py) - are kept as
the shipped page has them, so tests/test_generators.py can run this on the shipped tree and expect
no change. The idiom is lostgas/update_page.py's.

Which years the page talks about is decided here from the payload, never typed: the hero's two
years are the full year with the highest ceiling and the latest full year; a "scarcity year" is a
full year whose ceiling took SCARCE_DAYS days or fewer to reach half. claims() asserts every
comparison the template's words make; if a refresh moves one, the generator stops rather than ship
prose the payload contradicts.

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "storage.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
IMM = os.path.join(HERE, "data", "imm.json")
ZIP = os.path.join(SITE, "downloads", "storage-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]
SCARCE_DAYS = 15        # a full year that earned half its ceiling in this many days or fewer
# Events named on the page, each only in the market monitor's own words (data/imm.json "spikes":
# "Events such as Winter Storm Uri in 2021 ..."), and only if the year's half-days fall in the month.
EVENTS = {"2021": ("Winter Storm Uri", 2)}


def usd(x):
    return f"{x:,.0f}"


def usd2(x):
    return f"{x:,.2f}"


def day_of(year, i):
    return dt.date(int(year), 1, 1) + dt.timedelta(i)


def facts(P, I):
    """Everything the prose is about, derived once. Full years only, except where named."""
    R = P["rtm"]
    full = {y: r for y, r in R.items() if r["complete"]}
    part = {y: r for y, r in R.items() if not r["complete"]}
    c4 = {y: r["dur"]["4"]["net_per_kw"] for y, r in full.items()}
    dh = {y: r["dur"]["4"]["days_for_half"] for y, r in full.items()}
    scar = sorted(y for y in full if dh[y] <= SCARCE_DAYS)
    ordy = sorted(y for y in full if dh[y] > SCARCE_DAYS)
    top = max(full, key=lambda y: c4[y])
    last = max(full)
    fast = min(full, key=lambda y: (dh[y], y))
    f17 = I["figure17_read_by_eye"]
    fl = max(f17["total_musd"])
    energy_kw = f17["energy_musd"][fl] / (f17["total_musd"][fl] / f17["normalized_total_usd_kw_yr"][fl])
    return dict(R=R, full=full, part=part, c4=c4, dh=dh, scar=scar, ordy=ordy, top=top, last=last, fast=fast,
                med=statistics.median(c4.values()), fleet_last=fl, fleet_energy=energy_kw,
                fleet_hours=I["capacity_mwh"] / I["capacity_mw"])


def best_day(year, r):
    d = r["dur"]["4"]["daily_per_kw"]
    i = max(range(len(d)), key=lambda k: d[k])
    return day_of(year, i), d[i]


def half_months(year, r):
    """The months the year's half-days fall in, most first."""
    cnt = {}
    for i in r["dur"]["4"]["half_days"]:
        m = day_of(year, i).month
        cnt[m] = cnt.get(m, 0) + 1
    return [MONTHS[m - 1] for m, _ in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))]


def claims(F, P, I):
    """Each comparison the template's words make, asserted on the payload."""
    bad = []
    c4, dh = F["c4"], F["dh"]
    lo_s, hi_o = min(c4[y] for y in F["scar"]), max(c4[y] for y in F["ordy"])
    if not F["scar"] or not F["ordy"]:
        bad.append("need both scarcity and ordinary years")
    best_n = sorted(F["full"], key=lambda y: -c4[y])[:len(F["scar"])]
    if sorted(best_n) != F["scar"]:
        bad.append(f"the {len(F['scar'])} best years by ceiling {sorted(best_n)} are not the scarcity years {F['scar']}")
    if lo_s <= hi_o:
        bad.append(f"a scarcity year ({lo_s:.0f}) does not out-earn every ordinary year ({hi_o:.0f})")
    if min(dh[y] for y in F["ordy"]) <= SCARCE_DAYS:
        bad.append("an ordinary year is within the scarcity threshold")
    if dh[F["last"]] <= SCARCE_DAYS:
        bad.append("the latest full year is a scarcity year; the standfirst's contrast does not hold")
    r = c4[F["top"]] / F["med"]
    if not 2.5 <= r <= 4.5:
        bad.append(f"the top year is {r:.1f}x a typical year, not 'three to four' as the hero says")
    # "Each extra hour adds less than the one before": per hour of storage added
    for y, row in F["full"].items():
        v = {h: row["dur"][str(h)]["net_per_kw"] for h in (1, 2, 4, 8)}
        steps = [v[1], (v[2] - v[1]) / 1, (v[4] - v[2]) / 2, (v[8] - v[4]) / 4]
        if not all(a > b for a, b in zip(steps, steps[1:])):
            bad.append(f"{y}: an extra hour of storage does not add less than the one before {steps}")
    z = P["zones"]
    for y, zz in z.items():
        if not min(zz.values()) <= zz[P["point"]] <= max(zz.values()):
            bad.append(f"{y}: the hub average is outside the zone range")
    if F["fleet_energy"] >= P["rtm"][F["fleet_last"]]["dur"]["2"]["net_per_kw"]:
        bad.append("the fleet's energy income is not below the two-hour ceiling")
    if dh[F["last"]] != max(dh.values()):
        bad.append("the latest full year is not the most spread-out year, as the hero and standfirst say")
    if max(c4.values()) >= min(M_atb(), atb_over(15)):
        bad.append("a ceiling reaches the ownership cost; 'more than the ceiling in any year' fails")
    dam5 = sorted(sorted(F["full"], key=lambda y: -P["dam"][y]["dur"]["4"]["net_per_kw"])[:len(F["scar"])])
    if dam5 != F["scar"]:
        bad.append(f"the day-ahead five best years {dam5} are not the real-time five {F['scar']}")
    ice = P["ice"]
    if not (ice["annual_pct"] < 3 and ice["month_pct_max"] < 8 and ice["r"] >= 0.95):
        bad.append(f"the ICE cross-check is outside its tolerance: {ice}")
    if bad:
        raise SystemExit("storage/update_page.py: the payload contradicts the page's words:\n  " + "\n  ".join(bad))


def atb_over(years):
    """The same ATB capital and fixed O&M, the capital spread over `years` at model.py's rate."""
    import model as M
    r = M.ATB_DISCOUNT_RATE
    crf = r * (1 + r) ** years / ((1 + r) ** years - 1)
    return crf * M.ATB_CAPEX_USD_PER_KW_2024 + M.ATB_FOM_USD_PER_KW_YR_2024


def M_atb():
    import model as M
    return M.annualized_storage_cost_per_kw_yr()


def hero_spec(F):
    A, B = F["fast"], F["last"]

    def year(y):
        d = F["R"][y]["dur"]["4"]
        return {"label": y, "start": f"{y}-01-01", "values": [round(v, 3) for v in d["daily_per_kw"]],
                "half": d["half_days"], "halfText": f"half of {y}'s profit on {d['days_for_half']} days"}
    return {"id": "storage-hero", "type": "days",
            "title": f"A four-hour battery's profit each day of {A} and of {B}, per kilowatt, at ERCOT's hub average, "
                     f"with perfect hindsight",
            "a": year(A), "b": year(B), "y": {"label": "$ per kW each day"},
            "counter": {"prefix": "$", "unit": " per kW so far", "unitDone": " per kW for the year", "decimals": 0}}


def hero(F):
    import insight
    A, B = F["fast"], F["last"]
    ra, rb = F["R"][A]["dur"]["4"], F["R"][B]["dur"]["4"]
    (da, va), (db, vb) = best_day(A, F["R"][A]), best_day(B, F["R"][B])
    ma = half_months(A, F["R"][A])
    steps = [
        (f"<p><b>{A}: ${usd(F['c4'][A])} per kilowatt.</b> This is the year in which half the money came fastest, "
         f"shown one day at a time. On most days the battery made a little; on a few it made a great deal. Its best "
         f"day, {da.day} {MONTHS[da.month - 1]}, earned ${usd2(va)} per kilowatt by itself.</p>", {"t": 1}),
        (f"<p><b>Half of it on {ra['days_for_half']} days.</b> Sort the days that made money from best to worst. "
         f"The first {ra['days_for_half']} give half the year's total, and {'all' if len(ma) == 1 else 'most'} of them "
         f"are in {ma[0]}.</p>", {"t": 1, "lit": 1}),
        (f"<p><b>{B}: ${usd(F['c4'][B])}.</b> This is the same battery on the same scale, in {B}. The tall days are "
         f"gone: the best one, {db.day} {MONTHS[db.month - 1]}, made ${usd2(vb)}. The market monitor credits the growth "
         f"of storage with much of the fall in price spikes during the evening ramp, as the sun sets.</p>", {"t": 1, "mix": 1}),
        (f"<p><b>Half on {rb['days_for_half']} days.</b> No single day stands out. The money came in small amounts, "
         f"and it took {rb['days_for_half']} days to reach half, more than in any year since 2011.</p>",
         {"t": 1, "mix": 1, "lit": 1}),
    ]
    return insight.scrolly(hero_spec(F), steps, from_state={"t": 0})


def fast_event(F, q):
    """The event the market monitor names for the fastest year, if it names one and the
    year's half-days all fall in that month."""
    y = F["fast"]
    if y not in EVENTS:
        return ""
    name, month = EVENTS[y]
    days = [day_of(y, i) for i in F["R"][y]["dur"]["4"]["half_days"]]
    if name not in q["spikes"] or not all(d.month == month for d in days):
        raise SystemExit(f"storage/update_page.py: {name} is named for {y}, but the monitor's quote or the dates do not bear it out")
    return f", the month of {name}"


FRACTIONS = {"quarter": 0.25, "third": 1 / 3, "half": 0.5}


def fraction_word(x):
    w = min(FRACTIONS, key=lambda k: abs(FRACTIONS[k] - x))
    if abs(FRACTIONS[w] - x) > 0.05:
        raise SystemExit(f"storage/update_page.py: the fleet's share of the ceiling, {x:.2f}, is no plain fraction")
    return w


def year_rows(F):
    rows = []
    for y in sorted(F["R"]):
        r = F["R"][y]
        d = r["dur"]["4"]
        bd, bv = best_day(y, r)
        star = "" if r["complete"] else "*"
        cls = ' class="lit"' if y in F["scar"] else ""
        rows.append(f'<tr{cls}><td>{y}{star}</td><td class="n">{usd(d["net_per_kw"])}</td>'
                    f'<td class="n">{d["days_for_half"]}</td><td class="n">{100 * d["best10_days_share"]:.0f}%</td>'
                    f'<td>{bd.day} {MONTHS[bd.month - 1][:3]}, ${usd2(bv)}</td></tr>')
    return "\n".join(rows)


def dur_rows(F):
    rows = []
    for y in sorted(F["full"]):
        v = {h: F["full"][y]["dur"][str(h)]["net_per_kw"] for h in (1, 2, 4, 8)}
        rows.append(f'<tr><td>{y}</td>' + "".join(f'<td class="n">{usd(v[h])}</td>' for h in (1, 2, 4, 8)) + "</tr>")
    return "\n".join(rows)


def values(P, I):
    import insight
    import model as M
    F = facts(P, I)
    claims(F, P, I)
    q = {k: v["text"] for k, v in I["quotes"].items()}
    last_b = best_day(F["last"], F["R"][F["last"]])[1]
    fast_d = F["R"][F["fast"]]["dur"]["4"]
    last_c = F["c4"][F["last"]]
    last_earned = f"the median ${usd(last_c)}" if abs(last_c - F["med"]) < 1e-9 else f"${usd(last_c)}"
    frac = fraction_word(F["fleet_energy"] / P["rtm"][F["fleet_last"]]["dur"]["2"]["net_per_kw"])
    dam_loose = [y for y in F["scar"] if P["dam"][y]["dur"]["4"]["days_for_half"] > SCARCE_DAYS]
    fm = half_months(F["fast"], F["R"][F["fast"]])
    part_note = ""
    for y, r in sorted(F["part"].items()):
        t = dt.date.fromisoformat(r["through"])
        part_note = (f"* {y} to {t.day} {MONTHS[t.month - 1]}, the last day in ERCOT's file. This is the profit to that "
                     f"date, not the profit for a full year. "
                     f"Highlighted rows show the years in which the ceiling took {SCARCE_DAYS} days or fewer to reach half.")
    if not part_note:
        part_note = f"Highlighted rows show the years in which the ceiling took {SCARCE_DAYS} days or fewer to reach half."
    z = P["zones"]
    zy = sorted(z)
    zlo = lambda y: min(z[y], key=z[y].get)
    zhi = lambda y: max(z[y], key=z[y].get)
    dam = [P["dam"][y]["dur"]["4"]["net_per_kw"] for y in F["full"]]
    th = dt.date.fromisoformat(P["through"])
    ord_c = [F["c4"][y] for y in F["ordy"]]
    sc_c = [F["c4"][y] for y in F["scar"]]
    fl = F["fleet_last"]
    eta = (P["rte"]) ** 0.5
    v = {
        "stamp": insight.stamp(P["through"][:7], "ERCOT's settlement point prices"),
        "takeaways": insight.takeaways([
            f"The {len(F['scar'])} best years since 2011 were all years when half the money came in "
            f"{max(F['dh'][y] for y in F['scar'])} days or fewer. In {F['fast']}, half came in only "
            f"{fast_d['days_for_half']} days of {fm[0]}.",
            f"{F['last']} earned {last_earned}, but its money was the most spread out. No day made more than "
            f"${usd2(last_b)} per kilowatt, and half its money took {F['dh'][F['last']]} days to arrive.",
            f"Real batteries earned roughly a {frac} of the ceiling. Read from the market monitor's chart, the fleet's "
            f"income from energy was about ${usd(F['fleet_energy'])} per kilowatt in {fl}. The ceiling for a "
            f"two-hour battery with perfect foresight was ${usd(P['rtm'][fl]['dur']['2']['net_per_kw'])}."]),
        "hero": hero(F),
        "fast_year": F["fast"], "fast_days": str(fast_d["days_for_half"]), "fast_event": fast_event(F, q),
        "top_year": F["top"], "top_val": usd(F["c4"][F["top"]]), "med_val": usd(F["med"]),
        "last_year": F["last"], "last_days": str(F["dh"][F["last"]]),
        "last_earned": last_earned, "fast_month": fm[0], "fleet_frac": frac, "cdeg_leg": f"{P['c_deg'] / 2:.0f}",
        "q_as": html.escape(q["as_before"]),
        "dam_note": ("" if not dam_loose else ", though " + ", ".join(
            f"{y}'s took {P['dam'][y]['dur']['4']['days_for_half']} days to reach half" for y in dam_loose)),
        "last_best": usd2(last_b), "mw": "one",
        "n_ord": str(len(F["ordy"])), "n_scar": str(len(F["scar"])),
        "ord_lo": usd(min(ord_c)), "ord_hi": usd(max(ord_c)),
        "ord_days_lo": str(min(F["dh"][y] for y in F["ordy"])),
        "scar_lo": usd(min(sc_c)), "scar_hi": usd(max(sc_c)),
        "scar_days_hi": str(max(F["dh"][y] for y in F["scar"])),
        "year_rows": year_rows(F), "part_year_note": part_note,
        "q_spikes": html.escape(q["spikes"]), "q_fleet": html.escape(q["fleet"]), "q_ramp": html.escape(q["ramp"]),
        "f_energy_last": usd(F["fleet_energy"]), "fleet_last": fl,
        "ceil2_last": usd(P["rtm"][fl]["dur"]["2"]["net_per_kw"]), "fleet_hours": f"{F['fleet_hours']:.1f}",
        "through_long": f"{th.day} {MONTHS[th.month - 1]} {th.year}",
        "ice_pct": f"{P['ice']['annual_pct']:.1f}",
        "rte": f"{100 * P['rte']:.0f}",
        "dam_lo": usd(min(dam)), "dam_hi": usd(max(dam)),
        "dur_rows": dur_rows(F),
        "z_hi_year": zy[0], "z_lo_year": zy[-1],
        "z1_lo": usd(z[zy[0]][zlo(zy[0])]), "z1_lo_name": zlo(zy[0]), "z1_hi": usd(z[zy[0]][zhi(zy[0])]), "z1_hi_name": zhi(zy[0]),
        "z2_lo": usd(z[zy[-1]][zlo(zy[-1])]), "z2_lo_name": zlo(zy[-1]), "z2_hi": usd(z[zy[-1]][zhi(zy[-1])]), "z2_hi_name": zhi(zy[-1]),
        "ac_hours": f"{4 * eta:.2f}", "atb": usd(M.annualized_storage_cost_per_kw_yr()), "atb15": usd(atb_over(15)),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    stamps = dict(re.findall(r'(?:href|src|srcset)="([^"?]+)\?v=([0-9a-f]+)"', shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    text = text.replace("{{nav}}", nav)

    def stamp(m):
        path = m.group(2)
        return f'{m.group(1)}="{path}?v={stamps[path]}"' if path in stamps else m.group(0)
    return re.sub(r'(href|src|srcset)="([^"?]+\.(?:css|js|png))"', stamp, text)


def render(P, I):
    t = open(TEMPLATE, encoding="utf-8").read()
    v = values(P, I)
    missing = sorted(set(re.findall(r"{{(\w+)}}", t)) - set(v) - {"nav"})
    if missing:
        raise SystemExit(f"template placeholders without a value: {missing}")
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)))
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else open(os.path.join(SITE, "lostgas.html"), encoding="utf-8").read()
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("storage.html")
    if not refs:
        return text, ["storage.html has no entry in add_citations.PAGES"]
    tmp = PAGE + ".render.tmp"
    open(tmp, "w", encoding="utf-8", newline="\n").write(text)   # LF: trap 32
    try:
        out, probs = add_citations.build(os.path.basename(tmp), refs)
    finally:
        os.remove(tmp)
    return (out if out is not None else text), probs


def main(apply=False):
    P = json.load(open(PAYLOAD, encoding="utf-8"))
    I = json.load(open(IMM, encoding="utf-8"))
    t = render(P, I)
    t, probs = cite(t)
    for p in probs:
        print("  " + p)
    old = open(PAGE, "rb").read().decode("utf-8") if os.path.exists(PAGE) else None   # bytes: trap 32
    print("  storage.html: " + ("new page" if old is None else "unchanged" if old == t else
                               "would change" if not apply else "rewritten"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
