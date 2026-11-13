"""
Write site/nightshift.html from template.html and outputs/payload.json.

Every number from the time diaries comes from the payload (build_nightshift.py); numbers from published studies
are in the template's prose, each with its citation in add_citations.PAGES["nightshift.html"], which this script
applies itself (oxygen's idiom). The parts other scripts own - the nav (rebuild_nav.py) and the ?v= stamps
(bust_cache.py) - are kept as the shipped page has them, so tests/test_generators.py can run this on the shipped
tree and expect no change.

The hero is a 24-hour clock drawn here as two SVGs (600px wide, 340px for a phone). Three rings, outside in:
everyone aged 15 and over, usual day workers on days they worked, usual night workers on days they worked. In
each ring, at each 10-minute step, a dark wedge is the share asleep and a blue wedge, stacked on it, the share at
work. An arc outside the clock marks the body clock of day-active adults (published averages, not this data), and
a dashed sector marks the evening, 18:00 to 22:00. Elements carry data-o, the step they belong to;
site/assets/nightclock.js shows them one step at a time as the reader scrolls. Without the script every layer
shows.

claims() asserts every direction and word the template commits to ("about two in three", "about the same",
"nearly two hours"). If a rebuild moves one, the generator stops rather than ship prose the payload contradicts.

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import html
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "nightshift.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "nightshift-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
E = html.escape

# Body clock of day-active adults: published means, drawn as an arc (not from the diaries).
# Burgess & Fogg 2008 (n=170): salivary melatonin onset 20:50, offset 08:21.
# Baehr, Revelle & Eastman 2000 (n=172): core body temperature minimum 05:09.
MEL_ON, MEL_OFF, CBT_MIN = 20 * 60 + 50, 8 * 60 + 21, 5 * 60 + 9
EVENING = (18 * 60, 22 * 60)


def hm(m):
    m = int(round(m)) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def hours(mins, k=1):
    return f"{mins / 60:.{k}f}"


# ------------------------------------------------------------------- clock ---
def pt(cx, cy, r, minute):
    a = 2 * math.pi * (minute % 1440) / 1440
    return cx + r * math.sin(a), cy - r * math.cos(a)


def sector(cx, cy, r0, r1, m0, m1):
    """Annular sector from radius r0 to r1, clock minutes m0 to m1 (clockwise, m1 > m0)."""
    large = 1 if (m1 - m0) > 720 else 0
    x0, y0 = pt(cx, cy, r0, m0)
    x1, y1 = pt(cx, cy, r1, m0)
    x2, y2 = pt(cx, cy, r1, m1)
    x3, y3 = pt(cx, cy, r0, m1)
    return (f"M{x0:.1f} {y0:.1f}L{x1:.1f} {y1:.1f}A{r1:.1f} {r1:.1f} 0 {large} 1 {x2:.1f} {y2:.1f}"
            f"L{x3:.1f} {y3:.1f}A{r0:.1f} {r0:.1f} 0 {large} 0 {x0:.1f} {y0:.1f}Z")


def arc(cx, cy, r, m0, m1):
    span = (m1 - m0) % 1440
    x0, y0 = pt(cx, cy, r, m0)
    x1, y1 = pt(cx, cy, r, m0 + span)
    return f"M{x0:.1f} {y0:.1f}A{r:.1f} {r:.1f} 0 {1 if span > 720 else 0} 1 {x1:.1f} {y1:.1f}"


def ring(cx, cy, r0, h, sleep, work, step, start):
    """Two paths: the share asleep from r0 outward, the share at work stacked on it."""
    ds, dw = [], []
    for i, (s, w) in enumerate(zip(sleep, work)):
        m0 = start + i * step
        rs = r0 + h * s / 100
        rw = rs + h * w / 100
        if s > 0.05:
            ds.append(sector(cx, cy, r0, rs, m0, m0 + step))
        if w > 0.05:
            dw.append(sector(cx, cy, rs, rw, m0, m0 + step))
    return "".join(ds), "".join(dw)


def clock(P, wide):
    if wide:
        W, hole, h, gap, lab_r, arc_r = 600, 70, 54, 8, 284, 266
    else:
        W, hole, h, gap, lab_r, arc_r = 340, 34, 31, 4, 160, 148
    cx = cy = W / 2
    step = P["slot_min"]
    start = int(P["clock_start"][:2]) * 60
    G = P["groups"]
    bands = [("night", G["night_work"]["clock"], 2), ("day", G["day_work"]["clock"], 1),
             ("all", P["pop"], 0)]
    out = [f'<svg class="nclock {"nclock-wide" if wide else "nclock-phone"}" viewBox="0 0 {W} {W}" width="{W}" '
           f'height="{W}" role="img" aria-labelledby="nclock-desc">']
    # ring outlines first, so an empty ring still reads as a ring
    for k, (key, c, o) in enumerate(bands):
        r0 = hole + k * (h + gap)
        out.append(f'<g class="band band-{key}" data-o="{o}">')
        out.append(f'<circle class="rim" cx="{cx}" cy="{cy}" r="{r0:.1f}"/>'
                   f'<circle class="rim" cx="{cx}" cy="{cy}" r="{r0 + h:.1f}"/>')
        ds, dw = ring(cx, cy, r0, h, c["sleep"], c["work"], step, start)
        out.append(f'<path class="sl" d="{ds}"/><path class="wk" d="{dw}"/></g>')
    outer = hole + 3 * h + 2 * gap
    # hour ticks and labels
    out.append('<g class="ticks" data-o="0">')
    labels = {0: "midnight", 6 * 60: "06:00", 12 * 60: "noon", 18 * 60: "18:00"}
    if wide:
        labels.update({3 * 60: "03:00", 9 * 60: "09:00", 15 * 60: "15:00", 21 * 60: "21:00"})
    for m in range(0, 1440, 180):
        x0, y0 = pt(cx, cy, outer + 2, m)
        x1, y1 = pt(cx, cy, outer + (8 if m % 360 == 0 else 5), m)
        out.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}"/>')
        if m in labels:
            x, y = pt(cx, cy, lab_r, m)
            anchor = "middle" if m in (0, 720) else ("start" if m < 720 else "end")
            dy = 4 if m not in (0, 720) else (0 if m == 0 else 9)
            if m == 0:
                y = y + 4
            out.append(f'<text x="{x:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}">{labels[m]}</text>')
    out.append("</g>")
    # body clock (step 3): melatonin arc and the temperature low
    out.append('<g class="bclock" data-o="3">')
    out.append(f'<path class="mel" d="{arc(cx, cy, arc_r, MEL_ON, MEL_OFF)}"/>')
    x, y = pt(cx, cy, arc_r, CBT_MIN)
    out.append(f'<circle class="cbt" cx="{x:.1f}" cy="{y:.1f}" r="{5 if wide else 4}"/>')
    out.append("</g>")
    # the evening (step 4)
    out.append('<g class="eve" data-o="4">')
    out.append(f'<path d="{sector(cx, cy, hole, outer, EVENING[0], EVENING[1])}"/>')
    out.append("</g>")
    out.append(f'<text class="mid" x="{cx}" y="{cy + 4}" text-anchor="middle">24 h</text>')
    out.append("</svg>")
    return "".join(out)


def hero(P, v):
    steps = [
        (0, "Everyone aged 15 and over &middot; outer ring",
         f"At 3 a.m. in 2025, {v['a3_03']} percent of Americans aged 15 and over were asleep; at noon, about "
         f"{v['pop_noon']} percent. The outer ring shows the share asleep (dark) and at work (blue) at every ten "
         "minutes of the day. The country keeps one clock, and it is easy to see."),
        (1, "Usual day workers, on days they worked &middot; middle ring",
         f"Day workers sleep inside the country's night and work inside its day. On workdays they report "
         f"{v['day_sleep_h']} hours asleep, and only {v['day_two']} percent split that sleep into two or more "
         f"blocks. While they sleep, {v['day_awake_pct']} percent of everyone else is awake."),
        (2, "Usual night workers, on days they worked &middot; inner ring",
         f"Night workers report {v['night_sleep_h']} hours asleep, about the same as day workers. The hours "
         f"come in pieces: {v['night_two']} percent sleep in two or more blocks, and the longest block averages "
         f"{v['night_long_h']} hours against {v['day_long_h']}. While they sleep, {v['night_awake_pct']} percent of "
         "everyone else is awake, about two in three. Their shifts start at different hours, so no single "
         "time sees them all at work."),
        (3, "The body clock &middot; published averages, not diaries",
         "The arc marks when melatonin, the hormone of the biological night, is high in day-active adults: from "
         "about 20:50 to 08:20. The dot is the low point of body temperature, near 05:00, when people are "
         "sleepiest. A night shift works through that low point and sleeps through the hours the body treats as "
         "day. Few permanent night workers move this clock to fit the shift."),
        (4, "The evening, 18:00 to 22:00 &middot; dashed sector",
         f"These are the hours when most people are awake and off work. On workdays, night workers are asleep or "
         f"at work for {v['night_eve']} percent of them; day workers, {v['day_eve']} percent. Days off do not "
         f"repay it: night workers spend {v['off_gap']} fewer minutes with family and friends than day workers "
         "do on theirs."),
    ]
    desc = (f"A 24-hour clock with midnight at the top and three rings. Outer ring: everyone aged 15 and over, "
            f"mostly asleep from about 23:00 to 06:00. Middle ring: usual day workers on workdays, asleep at night "
            f"and at work in the day. Inner ring: usual night workers on workdays, asleep for parts of the morning "
            f"and early afternoon and at work across the night. An arc marks the melatonin night of day-active "
            f"adults, about 20:50 to 08:20, with a dot at the body-temperature low near 05:00. A dashed sector "
            f"marks 18:00 to 22:00, when night workers are asleep or at work {v['night_eve']} percent of the time "
            f"and day workers {v['day_eve']} percent.")
    out = ['<figure class="nclock-fig wide" aria-label="Three 24-hour clocks">',
           '<div class="nc-fig">', f'<p id="nclock-desc" hidden>{E(desc)}</p>',
           clock(P, True), clock(P, False),
           '<p class="nc-key">Rings, outside in: everyone aged 15 and over; usual day workers on days they '
           'worked; usual night workers on days they worked. Dark: share asleep. Blue: share at work. '
           'Midnight at the top, ten-minute steps. Arc and dot: body clock of day-active adults.</p>',
           '</div>', '<div class="nc-steps">']
    for k, head, text in steps:
        out.append(f'<div class="step" data-step="{k}"><p class="ev">{head}</p><p>{text}</p></div>')
    out.append("</div>\n</figure>")
    return "\n".join(out)


# ------------------------------------------------------------------ tables ---
def table_day(P):
    G = P["groups"]
    n, d = G["night_work"], G["day_work"]
    rows = [
        ("Time reported asleep, hours", hours(n["sleep_min"]), hours(n["sleep_se"]), hours(d["sleep_min"]),
         hours(d["sleep_se"])),
        ("Longest single sleep, hours", hours(n["longest_sleep_min"]), hours(n["longest_sleep_se"]),
         hours(d["longest_sleep_min"]), hours(d["longest_sleep_se"])),
        ("Sleep in two or more blocks of 30 minutes or more, percent", f"{n['two_sleeps_pct']:.0f}",
         f"{n['two_sleeps_se']:.0f}", f"{d['two_sleeps_pct']:.0f}", f"{d['two_sleeps_se']:.0f}"),
        ("Time at work, hours", hours(n["work_min"]), hours(n["work_se"]), hours(d["work_min"]),
         hours(d["work_se"])),
        ("Time with family or friends, hours", hours(n["family_min"] + n["friends_min"]), "",
         hours(d["family_min"] + d["friends_min"]), ""),
        ("18:00 to 22:00 spent asleep or at work, percent", f"{n['evening_busy_pct']:.0f}", "",
         f"{d['evening_busy_pct']:.0f}", ""),
        ("Others awake while they sleep, percent of everyone 15 and over", f"{n['pop_awake_while_asleep']:.0f}", "",
         f"{d['pop_awake_while_asleep']:.0f}", ""),
    ]
    out = ['<table class="nc-table">',
           f'<caption>One workday in the diaries, 2024 and 2025: usual night workers ({n["n"]} diaries) and usual '
           f'day workers ({d["n"]:,} diaries). SE is the standard error.</caption>',
           '<thead><tr><th></th><th class="n">Night</th><th class="n">SE</th><th class="n">Day</th>'
           '<th class="n">SE</th></tr></thead><tbody>']
    for r in rows:
        out.append("<tr><td>%s</td>%s</tr>" % (r[0], "".join(f'<td class="n">{c}</td>' for c in r[1:])))
    out.append("</tbody></table>")
    return "\n".join(out)


def table_reasons(P):
    M = P["module"]
    R, S, X = M["reasons"], M["reasons_se"], M["reasons_by_sex"]
    lab = [("preference", "Personal preference"), ("nature", "Nature of the job"), ("pay", "Better pay"),
           ("family", "Better arrangements for family or child care"), ("no_other", "Could not get another shift"),
           ("school", "Allows time for school or another job"), ("other", "Other")]
    out = ['<table class="nc-table">',
           f'<caption>Main reason for working a night shift, percent of usual night workers, 2024 and 2025 '
           f'({M["n_night"]} respondents; {X["men"]["n"]} men, {X["women"]["n"]} women).</caption>',
           '<thead><tr><th></th><th class="n">All</th><th class="n">SE</th><th class="n">Men</th>'
           '<th class="n">Women</th></tr></thead><tbody>']
    for k, t in lab:
        out.append(f'<tr><td>{t}</td><td class="n">{R[k]:.1f}</td><td class="n">{S[k]:.1f}</td>'
                   f'<td class="n">{X["men"][k]:.1f}</td><td class="n">{X["women"][k]:.1f}</td></tr>')
    out.append("</tbody></table>")
    return "\n".join(out)


# ------------------------------------------------------------------ claims ---
def claims(P):
    G, M = P["groups"], P["module"]
    n, d = G["night_work"], G["day_work"]
    c = [
        ("'about the same' workday sleep: difference within two standard errors",
         abs(P["diff_sleep_min"]) < 2 * P["diff_sleep_se"]),
        ("'about two in three' awake while night workers sleep: 60-70%", 60 <= n["pop_awake_while_asleep"] <= 70),
        ("'one in five' awake while day workers sleep: 17-24%", 17 <= d["pop_awake_while_asleep"] <= 24),
        ("'in pieces': night workers split sleep more often, gap over 3 SE",
         n["two_sleeps_pct"] - d["two_sleeps_pct"] > 3 * math.hypot(n["two_sleeps_se"], d["two_sleeps_se"])),
        ("'about an hour shorter' longest block: 45-80 min",
         45 <= d["longest_sleep_min"] - n["longest_sleep_min"] <= 80),
        ("'nearly two hours' fewer on days off: 90-120 min and over 2 SE",
         90 <= -P["diff_company_off_min"] <= 120 and -P["diff_company_off_min"] > 2 * P["diff_company_off_se"]),
        ("'about half' the evening busy for night workers: 40-55%", 40 <= n["evening_busy_pct"] <= 55),
        ("'the largest group' prefer it: preference is the top reason",
         max(M["reasons"], key=M["reasons"].get) == "preference"),
        ("'nearly half of women' prefer: 40-50%", 40 <= M["reasons_by_sex"]["women"]["preference"] < 50),
        ("'about one in five men'", 17 <= M["reasons_by_sex"]["men"]["preference"] <= 23),
        ("'about three in five' night workers are men: 55-65%", 55 <= M["men_share_night"] <= 65),
        ("'a little over half of all wage and salary workers' are men: 50-56%", 50 < M["men_share_all"] <= 56),
        ("'about four times as likely' to sleep in 2+ blocks: ratio 3.5-5",
         3.5 <= n["two_sleeps_pct"] / d["two_sleeps_pct"] <= 5),
        ("'more' reported sleep on days off than day workers",
         G["night_off"]["sleep_min"] > G["day_off"]["sleep_min"]),
        ("'5.1 million' night workers", round(M["night_thousands"] / 1000, 1) == 5.1),
        ("'no single time sees them all at work': peak work share under 70%", max(n["clock"]["work"]) < 70),
        ("family time on workdays about the same: difference within two SE",
         abs(P["diff_company_min"]) < 2 * P["diff_company_se"]),
    ]
    bad = [k for k, ok in c if not ok]
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    G, M = P["groups"], P["module"]
    n, d = G["night_work"], G["day_work"]
    noon = (12 * 60 - int(P["clock_start"][:2]) * 60) // P["slot_min"]
    v = {
        "night_pct": f"{M['night_pct']:.1f}", "night_m": f"{M['night_thousands'] / 1000:.1f}",
        "n_night": str(M["n_night"]), "n_mod": f"{M['n']:,}", "n_work": str(n["n"]), "n_off": str(G["night_off"]["n"]),
        "n_dwork": f"{d['n']:,}",
        "pref": f"{M['reasons']['preference']:.1f}", "pref_w": f"{M['reasons_by_sex']['women']['preference']:.1f}",
        "pref_m": f"{M['reasons_by_sex']['men']['preference']:.1f}",
        "pay": f"{M['reasons']['pay']:.1f}", "pay_m": f"{M['reasons_by_sex']['men']['pay']:.1f}",
        "pay_w": f"{M['reasons_by_sex']['women']['pay']:.1f}", "fam": f"{M['reasons']['family']:.1f}",
        "nature": f"{M['reasons']['nature']:.1f}",
        "a3_03": f"{P['checks']['a3_2025']['sleep_03']:.0f}", "pop_noon": f"{P['pop']['sleep'][noon]:.0f}",
        "day_sleep_h": hours(d["sleep_min"]), "night_sleep_h": hours(n["sleep_min"]),
        "diff_sleep": f"{P['diff_sleep_min']:.0f}", "diff_sleep_se": f"{P['diff_sleep_se']:.0f}",
        "day_two": f"{d['two_sleeps_pct']:.0f}", "night_two": f"{n['two_sleeps_pct']:.0f}",
        "night_long_h": hours(n["longest_sleep_min"]), "day_long_h": hours(d["longest_sleep_min"]),
        "night_awake_pct": f"{n['pop_awake_while_asleep']:.0f}", "day_awake_pct": f"{d['pop_awake_while_asleep']:.0f}",
        "night_eve": f"{n['evening_busy_pct']:.0f}", "day_eve": f"{d['evening_busy_pct']:.0f}",
        "off_gap": f"{-P['diff_company_off_min']:.0f}", "off_gap_se": f"{P['diff_company_off_se']:.0f}",
        "off_sleep_h": hours(G["night_off"]["sleep_min"]), "doff_sleep_h": hours(G["day_off"]["sleep_min"]),
        "men_share": f"{M['men_share_night']:.0f}",
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    claims(P)
    v["stamp"] = insight.stamp(through=P["through"], live=False)
    v["takeaways"] = insight.takeaways([
        f"About {v['night_m']} million American wage and salary workers, {v['night_pct']} percent, usually work a "
        "night shift, and the most common reason they give is that they prefer it.",
        f"In the government's time diaries, night workers on workdays report about as much sleep as day workers, "
        f"but more often in pieces and at hours when about two in three people are awake.",
        "Years of night work are associated with more heart disease and diabetes, the cancer evidence is "
        "contested, and how much of the risk the shift itself causes is not settled."])
    v["hero"] = hero(P, v)
    v["table_day"] = table_day(P)
    v["table_reasons"] = table_reasons(P)
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "oxygen.html"), encoding="utf-8").read()
        stamps = {}
    else:
        stamps = dict(re.findall(r'(?:href|src|srcset)="([^"?]+)\?v=([0-9a-f]+)"', shipped))
    nav = re.search(r'<nav class="top">.*?</nav>', shipped, flags=re.S).group(0)
    nav = nav.replace(' class="on"', "").replace('<a href="nightshift.html">', '<a href="nightshift.html" class="on">')
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
    hero_only = {"day_awake_pct", "day_long_h", "day_sleep_h", "day_two", "night_awake_pct", "night_long_h",
                 "night_sleep_h", "night_two", "pop_noon"}      # read by hero(), not by the template
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)) - hero_only)
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("nightshift.html")
    if not refs:
        return text, ["nightshift.html has no entry in add_citations.PAGES"]
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
        print("  nightshift.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  nightshift.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
