"""
Write site/sub3.html from template.html and outputs/payload.json.

Every number on the page comes from the payload (build_sub3.py), from a constant below that names its
source, or from a file this script measures (the archive's size). The prose is in the template. The parts
other scripts own - the nav (rebuild_nav.py), the citation markers and Sources list (add_citations.py's table,
applied here) and the ?v= stamps (bust_cache.py) - are kept as the shipped page has them, so
tests/test_generators.py can run this on the shipped tree and expect no change. The idiom is
lead/update_page.py's.

The hero is a kit "strip" chart in a scrolly: one bar per minute of finishing time for the runners who passed
halfway in 1:28:30 to 1:29:59. The two supporting charts are static kit strips.

claims() asserts every direction and range the template's words commit to ("half of them made it", "fewer
than one in five", "most near misses were on schedule", "about a coin flip", "little better than the rest").
If a rebuild moves one, the generator stops rather than ship prose the payload contradicts.

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
PAGE = os.path.join(SITE, "sub3.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "sub3-code.zip")
sys.path.insert(0, ROOT)
E = html.escape

# Constants the payload does not compute, each with its source (the page's Sources list carries them too).
WR = 7170                   # Sabastian Sawe, London Marathon, 26 April 2026 (World Athletics, ratified)
HERO_ONLY = {"band_k", "band_med", "miss5", "over15"}   # values only the hero's step text uses
HOT = 18.0                  # race mornings at or above this mean temperature are drawn in the accent colour


def hms(s, h=True):
    s = int(round(s))
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if h else f"{s // 60}:{s % 60:02d}"


def pace(sec_per_km, k=0):
    m, s = divmod(sec_per_km, 60)
    return f"{int(m)}:{s:0{3 + k if k else 2}.{k}f}"


def mins(sec):
    """A whole number of minutes in words, refused unless the value is within 5 s of it."""
    m = round(sec / 60)
    if abs(sec - 60 * m) > 5:
        raise SystemExit(f"{sec} s is not a whole number of minutes")
    return {4: "four minutes", 5: "five minutes", 6: "six minutes"}.get(m, f"{m} minutes")


def p0(x):
    return f"{x:.0f}"


# ------------------------------------------------------------------ hero ---
def hero_spec(P):
    B = P["band"]
    bins = [{"a": None, "b": B["under_from"], "n": B["under"], "s": B["under"], "near": 0, "far": 0}]
    for b in B["bins"]:
        a = b["a"]
        bins.append({"a": a, "b": b["b"], "n": b["n"], "s": b["n"] if a < 180 else 0,
                     "near": b["n"] if 180 <= a < 185 else 0, "far": b["n"] if a >= 195 else 0})
    bins.append({"a": B["tail_from"], "b": None, "n": B["tail"], "s": 0, "near": 0, "far": B["tail"]})
    return {"id": "sub3-hero", "type": "strip",
            "title": "Finishing times of the %s Berlin Marathon runners who passed halfway in 1:28:30 to 1:29:59, "
                     "%d to %d, one bar per minute" % (f"{B['n']:,}", P["source"]["first"], P["source"]["last"]),
            "bins": bins, "y": {"label": "runners"}, "x": {"label": "finishing time, minutes (180 = 3:00:00)"},
            "lights": [{"key": "s", "color": "acc", "state": "s"},
                       {"key": "near", "color": "moss", "state": "n"},
                       {"key": "far", "color": "ink", "state": "f"}],
            "marks": [{"at": 180, "label": "3:00:00", "state": "k"}]}


def hero(P, v):
    import insight
    B = P["band"]
    mid = f"{100 * sum(b['n'] for b in B['bins'] if 185 <= b['a'] < 195) / B['n']:.0f}"
    steps = [
        (f"<p><b>{v['band_n']} runners, one plan.</b> Each passed halfway between 1:28:30 and 1:29:59: on schedule "
         f"for a finish between 2:57 and 3:00 if the second half matched the first. Each bar counts the runners who "
         f"finished in one minute. The bar on the left holds the {B['under']:,} who finished faster than 2:57.</p>",
         {"t": 1, "k": 1}),
        (f"<p><b>Under 3:00: {v['band_k']}, or {v['band_pct']} percent.</b> These runners slowed little or "
         f"not at all in the second half.</p>", {"t": 1, "k": 1, "s": 1}),
        (f"<p><b>3:00:00 to 3:04:59: {v['miss5']} percent.</b> More than a quarter of the group missed by under "
         f"five minutes: under {math.ceil(300 / 21.0975)} seconds a kilometre slower than 3:00 pace over the second half.</p>", {"t": 1, "k": 1, "s": 1, "n": 1}),
        (f"<p><b>3:15 or slower: {v['over15']} percent.</b> About one runner in nine lost a quarter of an hour or "
         f"more, and another {mid} percent finished between 3:05 and 3:14. The median runner in the group finished in {v['band_med']}.</p>",
         {"t": 1, "k": 1, "s": 1, "n": 1, "f": 1}),
    ]
    return insight.scrolly(hero_spec(P), steps, from_state={"t": 0})


# ---------------------------------------------------------------- charts ---
def static_chart(spec, caption):
    import insight
    snaps = insight._render(spec, [{k: 1 for k in ("t", "s", "h", "c", "k")}])
    return ('<figure class="step-fig wide" role="img" aria-label="%s"><div class="snap-wide">%s</div>'
            '<div class="snap-phone">%s</div><figcaption class="dim"><b>%s.</b> %s</figcaption></figure>'
            % (E(spec["title"]), snaps["wide"][0], snaps["phone"][0], E(spec["title"]), caption))


def chart_curve(P):
    C = P["curve"]
    bins = [{"a": c["a"], "b": c["b"], "n": round(c["share"], 1), "c": round(c["share"], 1) if c["a"] == 88 else 0}
            for c in C]
    spec = {"id": "sub3-curve", "type": "strip",
            "title": "Share of Berlin finishers who ran under 3:00, by minute of halfway split",
            "bins": bins, "y": {"label": "percent under 3:00"}, "x": {"label": "halfway split, minutes (90 = 1:30:00)"},
            "lights": [{"key": "c", "color": "acc", "state": "c"}],
            "marks": [{"at": 90, "label": "1:30:00", "state": "k"}]}
    n = sum(c["n"] for c in C)
    return static_chart(spec, "The share falls steeply in the last few minutes before 1:30: the bar for 1:28 (highlighted) "
                              "is close to a coin flip. Each bar is one minute of halfway split, from 1:%02d to 1:%02d; "
                              "%s finishers in all. Data: Berlin Marathon results %d to %d."
                        % (C[0]["a"] - 60, C[-1]["b"] - 60, f"{n:,}", P["source"]["first"], P["source"]["last"]))


def chart_weather(P):
    W = {w["year"]: w for w in P["weather"]["years"]}
    first, last = P["source"]["first"], P["source"]["last"]
    bins = []
    for y in range(first, last + 1):
        w = W.get(y)
        sh = round(w["share"], 1) if w else 0
        bins.append({"a": y, "b": y + 1, "n": sh, "h": sh if w and w["temp"] >= HOT else 0})
    hot = sorted((w for w in W.values() if w["temp"] >= HOT), key=lambda w: w["year"])
    spec = {"id": "sub3-weather", "type": "strip",
            "title": "Share of the halfway group who finished under 3:00, by year, Berlin Marathon",
            "bins": bins, "y": {"label": "percent under 3:00"}, "x": {"label": "year", "years": True},
            "lights": [{"key": "h", "color": "acc", "state": "h"}]}
    names = "; ".join(f"{w['year']}, {w['temp']:.1f} °C" for w in hot)
    return static_chart(spec, "Highlighted: the race mornings with a mean air temperature of %g °C or more (%s). "
                              "No race was held in 2020. Data: Berlin Marathon results; DWD hourly air temperature, "
                              "Berlin-Tempelhof, 09:00 to 13:00." % (HOT, names))


# ---------------------------------------------------------------- tables ---
def seg_rows(P):
    made, missed = (next(s for s in P["segments"] if s["group"] == g) for g in ("made", "missed"))
    rows = []
    for a, b in zip(made["segments"], missed["segments"]):
        lab = f"{a['from']:g} to {a['to']:g} km".replace("42.195", "42.2")
        rows.append(f"<tr><td>{lab}</td><td>{pace(a['pace_median'])}</td><td>{pace(b['pace_median'])}</td></tr>")
    return "\n".join(rows)


def ladder_rows(P):
    rows = []
    for L in P["ladder"]:
        n = f"{L['n']:,} ({L['share']:.2f} percent)" if L["n"] else "none"
        if L["sec"] == WR:
            n = "none"
        rows.append(f"<tr><td>{hms(L['sec'])}</td><td>{pace(L['pace_km'])}</td><td>{hms(L['half_eq'])}</td>"
                    f"<td>{n}</td></tr>")
    return "\n".join(rows)


# ---------------------------------------------------------------- claims ---
def claims(P, v):
    B, Y = P["band"], {x["year"]: x for x in P["band"]["by_year"]}
    W = {w["year"]: w for w in P["weather"]["years"]}
    C = {c["a"]: c["share"] for c in P["curve"]}
    made, missed = (next(s for s in P["segments"] if s["group"] == g) for g in ("made", "missed"))
    seg = lambda s, k: next(x for x in s["segments"] if x["from"] == k)["pace_median"]  # noqa: E731
    c = [
        ("standfirst: 2024 'half of them made it'", round(Y[2024]["share"]) == 50),
        ("standfirst: 2025 'fewer than one in five'", Y[2025]["share"] < 20),
        ("standfirst: 2025 was warmer than 2024", W[2025]["temp"] > W[2024]["temp"]),
        ("'most ... slower than 3:00' in all races but 2024, an even split",
         [x["year"] for x in B["by_year"] if x["share"] >= 50] == [2024] and round(Y[2024]["share"]) == 50),
        ("'about one in three' carried it out", 30 <= B["share"] < 36),
        ("'most near misses were on schedule at halfway'", P["near"]["half_under_90"] > 50),
        ("'about three minutes faster' than 1:28:30-1:29:59", 150 <= 5355 - P["ladder"][0]["half_eq"] <= 230),
        ("'first 15 km the two groups are the same'",
         all(abs(seg(made, k) - seg(missed, k)) <= 1.0 for k in (0.0, 5, 10))),
        ("'a few seconds a kilometre faster than 3:00 pace' early",
         all(seg(g, k) < P["ladder"][0]["pace_km"] for g in (made, missed) for k in (0.0, 5, 10))),
        ("'fast after 25 km': missed loses more after 25 than before",
         missed["behind_at"]["40km"] - missed["behind_at"]["25km"] > 3 * (missed["behind_at"]["25km"] - missed["behind_at"]["half"])),
        ("'nearly all of the deficit came after 25 km'; 'still ahead at 25 km'",
         missed["behind_at"]["25km"] < 0 and missed["behind_at"]["final"] - missed["behind_at"]["25km"] >
         0.9 * (missed["behind_at"]["final"] - missed["behind_at"]["half"])),
        ("'the lowest rate ... came on a morning that was not hot'",
         W[min(B["by_year"], key=lambda x: x["share"])["year"]]["temp"] < HOT),
        ("'heat': the warmest race morning is 2025", P["weather"]["hottest"] == 2025),
        ("'the warmer, the fewer' (negative slope and correlation)", P["weather"]["pearson"] < -0.3 and P["weather"]["slope_pts_per_c"] < 0),
        ("1:28 'about a coin flip'", 40 <= C[88] <= 55),
        ("curve falls with every minute", all(C[a] >= C[a + 1] for a in range(80, 91))),
        ("'little better than the rest'", 0 <= P["repeat"]["had"]["share"] - P["repeat"]["not"]["share"] < 5),
        ("'more than a quarter missed by under five minutes'", 25 < B["miss5"] < 33),
        ("'about one runner in nine' 15 min or more", 9 <= B["over15"] <= 12.5),
        ("'Slower finishers faded more'", P["slowdown"][0]["median_pct"] < P["slowdown"][1]["median_pct"] < P["slowdown"][-1]["median_pct"]),
        ("2025 is in the HOT set and 2024 is not", W[2025]["temp"] >= HOT > W[2024]["temp"]),
    ]
    bad = [name for name, ok in c if not ok]
    if bad:
        raise SystemExit("the payload contradicts the template:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    A, B, S = P["all"], P["band"], P["source"]
    Y = {x["year"]: x for x in B["by_year"]}
    W = {w["year"]: w for w in P["weather"]["years"]}
    lo = min(B["by_year"], key=lambda x: x["share"])
    hi = max(B["by_year"], key=lambda x: x["share"])
    made, missed = (next(s for s in P["segments"] if s["group"] == g) for g in ("made", "missed"))
    seg = lambda s, k: next(x for x in s["segments"] if x["from"] == k)["pace_median"]  # noqa: E731
    C = {c["a"]: c["share"] for c in P["curve"]}
    sl = {s["label"]: s for s in P["slowdown"]}
    L3 = P["ladder"][0]
    v = {
        "band_n": f"{B['n']:,}", "band_k": f"{B['sub3']:,}", "band_pct": p0(B["share"]),
        "miss5": p0(B["miss5"]), "over15": p0(B["over15"]), "band_med": hms(B["median_final"]),
        "y24_n": f"{Y[2024]['n']:,}", "y25_n": f"{Y[2025]['n']:,}", "y24_pct": p0(Y[2024]["share"]),
        "y25_pct": p0(Y[2025]["share"]), "t24": f"{W[2024]['temp']:.1f}", "t25": f"{W[2025]['temp']:.1f}",
        "dt": f"{W[2025]['temp'] - W[2024]['temp']:.0f}",  # 12.6 -> "about 13"
        "years_n": str(len(S["years"])), "years_less1": str(len(S["years"]) - 1), "first": str(S["first"]), "last": str(S["last"]), "rows": f"{S['rows']:,}",
        "all_n": f"{A['n']:,}", "all_pct": f"{A['share']:.1f}", "m_pct": f"{A['m_share']:.1f}", "w_pct": f"{A['w_share']:.1f}",
        "yr_lo": p0(lo["share"]), "yr_lo_y": str(lo["year"]), "yr_hi": p0(hi["share"]), "yr_hi_y": str(hi["year"]),
        "recent_pct": p0(B["recent"]["share"]),
        "near_n": f"{P['near']['n']:,}", "near_pct": p0(P["near"]["half_under_90"]),
        "pace3": pace(L3["pace_km"]), "mile3": pace(L3["pace_km"] * 1.609344), "split5": pace(L3["pace_km"] * 5),
        "half3": hms(L3["half_eq"]),
        "miss_3540": pace(seg(missed, 35)), "made_3540": pace(seg(made, 35)),
        "made_n": f"{made['n']:,}", "missed_n": f"{missed['n']:,}",
        "ahead_half": p0(-missed["behind_at"]["half"]), "behind30": p0(missed["behind_at"]["30km"]),
        "behind40": mins(missed["behind_at"]["40km"]),
        "ahead25": p0(-missed["behind_at"]["25km"]),
        "c89": p0(C[89]), "c88": p0(C[88]), "c87": p0(C[87]), "c85": p0(C[85]),
        "slow_s3": f"{sl['under 3:00']['median_pct']:.1f}", "slow_330": f"{sl['3:00 to 3:29']['median_pct']:.1f}",
        "slow_5h": p0(sl["5:00 or more"]["median_pct"]),
        "slope": f"{-P['weather']['slope_pts_per_c']:.1f}", "r_temp": f"{P['weather']['pearson']:.2f}".replace("-", "−"),
        "rep_pct": p0(P["repeat"]["had"]["share"]), "rep_n": f"{P['repeat']['had']['n']:,}",
        "wr_pace": pace(WR / 42.195),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    # the fade arithmetic in the margin section: a 1:29:30 half slowed by the sub-3 median
    fade = 5370 * (2 + round(sl["under 3:00"]["median_pct"], 1) / 100)
    v["fade_finish"] = hms(fade)
    v["stamp"] = insight.stamp(live=False)
    v["takeaways"] = insight.takeaways([
        f"Of the {v['band_n']} Berlin Marathon runners who passed halfway between 1:28:30 and 1:29:59, on schedule "
        f"for a sub-3, {v['band_pct']} percent finished under three hours.",
        "The runners who missed ran the first 15 km at the same pace as those who made it; nearly all of the time "
        "they lost came after 25 km, not in the first half.",
        f"Heat makes it worse: {v['y24_pct']} percent of the group made it on an {v['t24']} °C morning in 2024 and "
        f"{v['y25_pct']} percent on a {v['t25']} °C morning in 2025, and over all the races warmer mornings went with "
        f"lower rates."])
    claims(P, v)
    v["hero"] = hero(P, v)
    v["chart_curve"] = chart_curve(P)
    v["chart_weather"] = chart_weather(P)
    v["seg_rows"] = seg_rows(P)
    v["ladder_rows"] = ladder_rows(P)
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "lead.html"), encoding="utf-8").read()
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
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)) - HERO_ONLY)
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("sub3.html")
    if not refs:
        return text, ["sub3.html has no entry in add_citations.PAGES"]
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
        print("  sub3.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  sub3.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
