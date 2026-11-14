"""
Write site/aiweb.html from template.html and outputs/payload.json (build_aiweb.py builds the payload from
sources.py).

Every number on the page comes from the payload; the prose is in the template. The parts other scripts own -
the nav (rebuild_nav.py), the citation markers and Sources list (add_citations.py's table, applied here) and
the ?v= stamps (bust_cache.py) - are kept as the shipped page has them, so tests/test_generators.py can run
this on the shipped tree and expect no change. The idiom is armchair/update_page.py's.

The hero is a map drawn twice (900px and 340px): the share of web requests made by software across, the share
of what readers are shown that machines wrote up, both 0 to 100 percent. The four futures are placed by this page's judgement; today's markers are measured. The
fifth future, the closing web, is a strip under the map with two measured points.

claims() asserts every comparison the template's words commit to ("only", "about as many", "lower", "fastest");
if a rebuild moves one, the generator stops.

Run:  python update_page.py            report only
      python update_page.py --apply
"""
import argparse
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
PAGE = os.path.join(SITE, "aiweb.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "aiweb-code.zip")
sys.path.insert(0, ROOT)
import insight  # noqa: E402

E = html.escape
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]


def num(v):
    """As published: thousands separators, no trailing .0, decimals kept as given."""
    if isinstance(v, int) or float(v).is_integer():
        return f"{int(v):,}"
    return f"{v:,}"


WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}


def half_up(r):
    """Round half up, as a reader would (Python's round() sends 76.5 to 76)."""
    return int(r + 0.5)


def times(r):
    """A ratio in words, for the comparisons the prose makes."""
    if 1.75 <= r < 2.25:
        return "nearly twice" if r < 2 else "about twice"
    if 3.25 <= r < 3.75:
        return "three and a half times"
    if r >= 10:
        return f"about {half_up(r):,} times"
    return f"about {r:.1f} times"


# ------------------------------------------------------------------- hero ---
def map_svg(P, W, H, pad, cls, fs):
    """The map: x = share of requests made by software, y = share of what readers are shown that machines wrote."""
    f = P["fig"]
    x0, x1 = pad["l"], W - pad["r"]
    y0, y1 = pad["t"], H - pad["b"]
    phone = W < 600

    def X(v):
        return x0 + (x1 - x0) * v / 100

    def Y(v):
        return y1 - (y1 - y0) * v / 100
    out = [f'<svg class="aimap {cls}" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-labelledby="aimap-desc">']
    out.append(f'<rect class="frame" x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}"/>')
    for v in (25, 50, 75):
        out.append(f'<line class="grid" x1="{X(v):.1f}" y1="{y0}" x2="{X(v):.1f}" y2="{y1}"/>'
                   f'<line class="grid" x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}"/>')
    # ticks at 0, 50 and 100 percent, and the two axis titles
    for v, a in ((0, "start"), (50, "middle"), (100, "end")):
        out.append(f'<text class="ax" x="{X(v):.1f}" y="{y1 + fs + 4}" text-anchor="{a}">{v}</text>')
        out.append(f'<text class="ax" x="{x0 - 6}" y="{Y(v) + fs * 0.35 + (fs * 0.4 if v == 0 else 0):.1f}" '
                   f'text-anchor="end">{v}</text>')
    xt = "percent of requests made by software" if phone else "across: percent of web requests made by software"
    out.append(f'<text class="ax" x="{(x0 + x1) / 2:.1f}" y="{y1 + 2 * fs + 12}" text-anchor="middle">{xt}</text>')
    yt = ("percent of what readers are shown, machine-written" if not phone
          else "percent shown, machine-written")
    yc = (y0 + y1) / 2
    out.append(f'<text class="ax" x="{x0 - 30}" y="{yc:.1f}" text-anchor="middle" '
               f'transform="rotate(-90 {x0 - 30} {yc:.1f})">{yt}</text>')
    # futures (judgement)
    for s in P["scenarios"]:
        cx, cy = X(s["x"]), Y(s["y"])
        if phone and s["x"] > 60:
            # on a phone the right-hand labels sit under their circle, kept inside the frame
            lx, ly, anchor = min(cx, x1 - 4), cy + fs + 10, "middle" if cx < x1 - 40 else "end"
        else:
            anchor = "end" if s["x"] > 60 else "start"
            lx, ly = cx + (-12 if anchor == "end" else 12), cy + fs * 0.35
        out.append(f'<g class="fut f-{s["key"]}"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="7"/>'
                   f'<text class="flab" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}">'
                   f'{E(s["name"])}</text></g>')
    # today (measured): one x, and two y values from two different samples, not joined
    tx = f[P["today"]["x"]]["value"]
    yp = f[P["today"]["y_published"]]["value"]
    ys = f[P["today"]["y_shown"]]["value"]
    out.append(f'<g class="today">'
               f'<rect x="{X(tx) - 5:.1f}" y="{Y(ys) - 5:.1f}" width="10" height="10"/>'
               f'<rect class="alt" x="{X(tx) - 4:.1f}" y="{Y(yp) - 4:.1f}" width="8" height="8"/>'
               f'<text class="tlab" x="{X(tx) - 10:.1f}" y="{Y(ys) + fs * 0.35:.1f}" text-anchor="end">'
               f'{"today" if phone else "today, shown by Google"}</text>'
               f'<text class="tlab" x="{X(tx) - 10:.1f}" y="{Y(yp) + fs * 0.35:.1f}" text-anchor="end">'
               f'{"published" if phone else "today, new articles"}</text></g>')
    out.append("</svg>")
    return "".join(out)


def strip_svg(P, W, cls, fs):
    f = P["fig"]
    l, r = 8, W - 8
    y = 30

    def X(v):
        return l + (r - l) * v / 100
    out = [f'<svg class="aistrip {cls}" viewBox="0 0 {W} 92" width="{W}" height="92" role="img" '
           f'aria-labelledby="aistrip-desc">',
           f'<text class="ax" x="{l}" y="14">open</text><text class="ax" x="{r}" y="14" text-anchor="end">closed</text>',
           f'<line class="bar" x1="{l}" y1="{y}" x2="{r}" y2="{y}"/>']
    short = {"top1m_block": "of the top million sites", "news_block": "of top news sites"}
    for i, (k, label) in enumerate(P["strip"]):
        v = f[k]["value"]
        anchor = "start" if v < 50 else "end"
        text = f"{num(v)} percent {short[k]}" if W < 600 else f"{num(v)} percent: {label}"
        out.append(f'<g class="gate"><rect x="{X(v) - 5:.1f}" y="{y - 5}" width="10" height="10"/>'
                   f'<text class="tlab" x="{X(v):.1f}" y="{y + 22 + i * (fs + 6)}" text-anchor="{anchor}">'
                   f'{E(text)}</text></g>')
    out.append("</svg>")
    return "".join(out)


def hero(P, v):
    f = P["fig"]
    desc = (f"A square map. Across: the percent of web requests made by software, from 0 to 100. Up: the percent "
            f"of what readers are shown that machines wrote. Four predicted futures are placed by judgment: "
            + "; ".join(f"{s['name']}, {s['line']}" for s in P["scenarios"])
            + f". Today is measured at {v['bot_share']} percent across and {v['graphite_serp']} percent up (what "
            f"Google shows); a second marker at {v['graphite_articles']} percent up is the share of new articles.")
    sdesc = ("A strip from open to closed, with two different measures. "
             + "; ".join(f"{num(f[k]['value'])} percent of {label}" for k, label in P["strip"]) + ".")
    key = ('<p class="aikey"><i class="ki"><span class="sw fut"></span>a predicted future, placed by this '
           'page</i> <i class="ki"><span class="sw today"></span>today, measured</i></p>')
    return "\n".join([
        '<figure class="wide aimapfig" aria-label="Five futures for the web">',
        f'<p id="aimap-desc" hidden>{E(desc)}</p>',
        map_svg(P, 900, 490, {"l": 104, "r": 24, "t": 12, "b": 56}, "m-wide", 13),
        map_svg(P, 340, 420, {"l": 64, "r": 8, "t": 12, "b": 52}, "m-phone", 12),
        key,
        '<p class="aistrip-h">The fifth future, a closing web: sites that block AI training crawlers</p>',
        f'<p id="aistrip-desc" hidden>{E(sdesc)}</p>',
        strip_svg(P, 900, "s-wide", 13), strip_svg(P, 340, "s-phone", 12),
        "<figcaption>Across: the share of web requests made by software (Imperva, 2025). Up: the share of what "
        "readers are shown that machines wrote; today's large square is Google's results (Graphite, mid-2025), "
        "the small one new English articles (Graphite, early 2026), two samples from different dates. The futures "
        "are placed by this page; the squares are measured. The strip's two samples measure different things "
        "(Bouchaud and Ramaciotti, September 2025; BuzzStream, late 2025).</figcaption>",
        "</figure>"])


def scorecard(P, v):
    rows = []
    for r in P["scorecard"]:
        rows.append(f'<tr><td>{E(r["forecast"].format(**v))}</td><td>{E(r["by"].format(**v))}</td>'
                    f'<td>{E(r["measured"].format(**v))}</td><td>{E(r["verdict"])}</td></tr>')
    return "\n".join([
        '<p class="small dim" id="score-cue">On a narrow screen the table scrolls sideways.</p>',
        '<table class="n" tabindex="0" data-scroll-affordance="#score-cue" aria-label="Forecasts against what '
        'was measured"><thead><tr><th>Forecast</th><th>By</th><th>Measured</th><th>So far</th></tr></thead>'
        '<tbody>', *rows, "</tbody></table>"])


# ----------------------------------------------------------------- values ---
def values(P):
    f, d = P["fig"], P["derived"]
    v = {k: num(x["value"]) for k, x in f.items()}
    v.update({k: num(x) for k, x in d.items()})
    v["goog_growth"] = f"{d['goog_growth']:.0f}"
    v["g_c_ratio"] = f"{half_up(d['g_c_ratio']):,}"
    v["pub_shown_words"] = times(d["pub_shown_ratio"])
    v["ng_ratio"] = f"{half_up(d['ng_ratio']):,}"
    v["graphite_flat_words"] = WORDS[f["graphite_flat"]["value"]]
    y, m, dd = P["as_of"].split("-")
    v["as_of_words"] = f"{int(dd)} {MONTHS[int(m) - 1]} {y}"
    v["zip_kb"] = f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}"
    v["stamp"] = insight.stamp(live=False)
    v["takeaways"] = insight.takeaways([
        f"The best-known forecast missed: Google's search volume did not fall {v['gartner_drop']} percent by "
        f"2026, and its search revenue grew {v['goog_growth']} percent in a year.",
        f"What is shrinking is the share of searches that end on a website: people clicked a result on "
        f"{v['pew_click_ai']} percent of searches with an AI summary against {v['pew_click_no']} percent without one.",
        f"Bots make about {v['bot_share']} percent of web traffic, most of it old-fashioned automation; AI writes "
        f"about half of new English articles but only {v['graphite_serp']} percent of what Google shows."])
    claims(P, v)
    v["hero"] = hero(P, v)
    v["scorecard"] = scorecard(P, v)
    return v


def claims(P, v):
    f, d = P["fig"], P["derived"]
    g = {k: x["value"] for k, x in f.items()}
    bad = []
    if d["goog_growth"] <= 0:
        bad.append("search revenue grew")
    if not g["pew_click_ai"] < g["pew_click_no"]:
        bad.append("fewer clicks with an AI summary")
    if not g["zero_2026"] > g["zero_2024"]:
        bad.append("zero-click share up")
    if not g["graphite_serp"] < g["graphite_articles"]:
        bad.append("'only' a smaller share of what Google shows")
    if abs(g["cf_ai_bots"] - g["cf_googlebot"]) > 1:
        bad.append("AI crawlers 'about as many' as Googlebot")
    if abs(d["cf_machine_html"] - g["bot_share"]) > 2:
        bad.append("Cloudflare 'a similar' share to Imperva")
    if not g["agent_checkout"] < 5 < g["agent_browse"]:
        bad.append("agents browse, rarely check out")
    if not g["graphite_traffic"] < g["chartbeat_drop"]:
        bad.append("Graphite 'only' a small fall against Chartbeat")
    if not g["chartbeat_small"] > g["chartbeat_large"]:
        bad.append("small sites lost more than large")
    if not (g["crawl_google"] < g["crawl_openai"] < g["crawl_anthropic"]):
        bad.append("crawl ratios ordered Google < OpenAI < Anthropic")
    if not g["graphite_top10"] > 0:
        bad.append("the ten largest sites 'up'")
    if not g["zero_datos"] < 30 < 60 < g["zero_2026"]:
        bad.append("zero-click range 'about a quarter to about two-thirds'")
    for sc in P["scenarios"]:
        if sc["x"] < g["bot_share"] or sc["y"] < g["graphite_serp"]:
            bad.append(f"future {sc['key']} placed left of or below today")
    if not g["europol"] > g["graphite_articles"] + 20:
        bad.append("Europol 'not met'")
    if not g["ri_ai_2026"] > g["ri_ai_2025"]:
        bad.append("weekly AI use rose")
    if not g["elon_mixed"] > max(g["elon_better"], g["elon_worse"]):
        bad.append("'equal measure' the largest answer")
    if not g["pew_exp"] > 50 > g["pew_pub"]:
        bad.append("experts and public 'divided'")
    if g["ai_ref_share"] > 1:
        bad.append("AI referrals 'under 1 percent'")
    if bad:
        raise SystemExit("prose contradicted by payload: " + "; ".join(bad))


# --------------------------------------------------------------- assembly ---
def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        # A new page takes oxygen's nav with nothing marked current; rebuild_nav.py marks it when it runs.
        shipped = open(os.path.join(SITE, "oxygen.html"), encoding="utf-8").read()
        shipped = shipped.replace(' class="on"', "").replace('class="ddbtn on"', 'class="ddbtn"')
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
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("aiweb.html")
    if not refs:
        return text, ["aiweb.html has no entry in add_citations.PAGES"]
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
        print("  aiweb.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  aiweb.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
