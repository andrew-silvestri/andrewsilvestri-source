"""
Write site/aiweb.html from template.html and outputs/payload.json (build_aiweb.py builds the payload from
sources.py).

Every number on the page comes from the payload; the prose is in the template. The parts other scripts own -
the nav (rebuild_nav.py), the citation markers and Sources list (add_citations.py's table, applied here) and
the ?v= stamps (bust_cache.py) - are kept as the shipped page has them, so tests/test_generators.py can run
this on the shipped tree and expect no change. The idiom is armchair/update_page.py's.

The hero is a map drawn twice (900px and 340px): who reads the web across, who writes it up, both from people
(0) to machines (100). The four futures are placed by this page's judgement; today's markers are measured. The
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


def times(r):
    """A ratio in words, for the comparisons the prose makes."""
    if 1.75 <= r < 2.25:
        return "nearly twice" if r < 2 else "about twice"
    if 3.25 <= r < 3.75:
        return "three and a half times"
    if r >= 10:
        return f"about {round(r):,} times"
    return f"about {r:.1f} times"


# ------------------------------------------------------------------- hero ---
def map_svg(P, W, H, pad, cls, fs):
    """The map: x = who reads (people to machines), y = who writes (people to machines)."""
    f = P["fig"]
    x0, x1 = pad["l"], W - pad["r"]
    y0, y1 = pad["t"], H - pad["b"]

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
    # axis words
    out.append(f'<text class="ax" x="{x0}" y="{y1 + fs + 6}">people read</text>'
               f'<text class="ax" x="{x1}" y="{y1 + fs + 6}" text-anchor="end">machines read</text>'
               f'<text class="ax" x="{x0 - 8}" y="{y1}" text-anchor="end">people</text>'
               f'<text class="ax" x="{x0 - 8}" y="{y1 + fs}" text-anchor="end">write</text>'
               f'<text class="ax" x="{x0 - 8}" y="{y0 + fs - 2}" text-anchor="end">machines</text>'
               f'<text class="ax" x="{x0 - 8}" y="{y0 + 2 * fs - 2}" text-anchor="end">write</text>')
    # the corner no one has measured
    out.append(f'<text class="corner" x="{x1 - 6}" y="{y0 + fs + 4}" text-anchor="end">&#8220;dead internet&#8221;</text>')
    # futures (judgement)
    phone = W < 600
    for s in P["scenarios"]:
        cx, cy = X(s["x"]), Y(s["y"])
        if phone and s["x"] > 60:
            # on a phone the right-hand labels sit under their circle, clear of today's line
            lx, ly, anchor = cx, cy + fs + 10, "middle"
        else:
            anchor = "end" if s["x"] > 60 else "start"
            lx, ly = cx + (-12 if anchor == "end" else 12), cy + fs * 0.35
        out.append(f'<g class="fut f-{s["key"]}"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="7"/>'
                   f'<text class="flab" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}">'
                   f'{E(s["name"])}</text></g>')
    # today (measured): one x, two y values joined by a line
    tx = f[P["today"]["x"]]["value"]
    yp = f[P["today"]["y_published"]]["value"]
    ys = f[P["today"]["y_shown"]]["value"]
    out.append(f'<g class="today"><line x1="{X(tx):.1f}" y1="{Y(yp):.1f}" x2="{X(tx):.1f}" y2="{Y(ys):.1f}"/>'
               f'<rect x="{X(tx) - 5:.1f}" y="{Y(yp) - 5:.1f}" width="10" height="10"/>'
               f'<rect x="{X(tx) - 5:.1f}" y="{Y(ys) - 5:.1f}" width="10" height="10"/>'
               f'<text class="tlab" x="{X(tx) - 10:.1f}" y="{Y(yp) + fs * 0.35:.1f}" text-anchor="end">'
               f'{"published" if phone else "today, published"}</text>'
               f'<text class="tlab" x="{X(tx) - 10:.1f}" y="{Y(ys) + fs * 0.35:.1f}" text-anchor="end">'
               f'{"shown" if phone else "today, shown by Google"}</text></g>')
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
    desc = (f"A square map. Across: the share of the web read by machines, from people (left) to machines "
            f"(right). Up: the share written by machines. Four predicted futures are placed by judgement: "
            + "; ".join(f"{s['name']}, {s['line']}" for s in P["scenarios"])
            + f". Two measured markers for today sit at {v['bot_share']} percent across, at {v['graphite_articles']} "
            f"percent up for what is published and {v['graphite_serp']} percent up for what Google shows.")
    sdesc = ("A strip from open to closed. " + "; ".join(f"{num(f[k]['value'])} percent of {label}"
                                                      for k, label in P["strip"]) + ".")
    key = ('<p class="aikey"><i class="ki"><span class="sw fut"></span>a predicted future, placed by this '
           'page</i> <i class="ki"><span class="sw today"></span>today, measured</i></p>')
    return "\n".join([
        '<figure class="wide aimapfig" aria-label="Five futures for the web">',
        f'<p id="aimap-desc" hidden>{E(desc)}</p>',
        map_svg(P, 900, 470, {"l": 96, "r": 24, "t": 12, "b": 36}, "m-wide", 13),
        map_svg(P, 340, 400, {"l": 70, "r": 8, "t": 12, "b": 36}, "m-phone", 12),
        key,
        '<p class="aistrip-h">The fifth future, a closing web: sites that block AI training crawlers</p>',
        f'<p id="aistrip-desc" hidden>{E(sdesc)}</p>',
        strip_svg(P, 900, "s-wide", 13), strip_svg(P, 340, "s-phone", 12),
        "<figcaption>Across: who reads the web. Up: who writes it. The futures are placed by this page; the "
        "squares for today are measured (Imperva 2025; Graphite 2025-2026). The strip shows two measured samples "
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
        'was measured"><thead><tr><th>Forecast</th><th>By</th><th>Measured since</th><th>So far</th></tr></thead>'
        '<tbody>', *rows, "</tbody></table>"])


# ----------------------------------------------------------------- values ---
def values(P):
    f, d = P["fig"], P["derived"]
    v = {k: num(x["value"]) for k, x in f.items()}
    v.update({k: num(x) for k, x in d.items()})
    v["goog_growth"] = f"{d['goog_growth']:.0f}"
    v["g_c_ratio"] = f"{round(d['g_c_ratio']):,}"
    v["pub_shown_words"] = times(d["pub_shown_ratio"])
    v["ng_ratio"] = f"{round(d['ng_ratio']):,}"
    y, m, dd = P["as_of"].split("-")
    v["as_of_words"] = f"{int(dd)} {MONTHS[int(m) - 1]} {y}"
    v["zip_kb"] = f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}"
    v["stamp"] = insight.stamp(live=False)
    v["takeaways"] = insight.takeaways([
        f"The best-known forecast missed: Google's search volume did not fall {v['gartner_drop']} percent by "
        f"2026, and its search revenue grew {v['goog_growth']} percent in a year.",
        f"What is shrinking is the visit after the search: people clicked a result on {v['pew_click_ai']} percent "
        f"of searches with an AI summary against {v['pew_click_no']} percent without one.",
        f"Machines now make about {v['bot_share']} percent of web traffic and write about half of new English "
        f"articles, but only {v['graphite_serp']} percent of what Google shows is AI-written."])
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
    if d["cf_machine_html"] != g["bot_share"]:
        bad.append("Cloudflare 'the same' share as Imperva")
    if not g["agent_checkout"] < 5 < g["agent_browse"]:
        bad.append("agents browse, rarely check out")
    if not g["graphite_traffic"] < g["chartbeat_drop"]:
        bad.append("Graphite 'only' a small fall against Chartbeat")
    if not g["chartbeat_small"] > g["chartbeat_large"]:
        bad.append("small sites lost more than large")
    if not (g["crawl_google"] < g["crawl_openai"] < g["crawl_anthropic"]):
        bad.append("crawl ratios ordered Google < OpenAI < Anthropic")
    if not g["statcounter"] > g["meta_thresh"]:
        bad.append("Metaculus 'as forecast'")
    if not g["europol"] > g["graphite_articles"] + 20:
        bad.append("Europol 'not met'")
    if not g["ri_ai_2026"] > g["ri_ai_2025"]:
        bad.append("weekly AI use rose")
    if not g["elon_mixed"] > max(g["elon_better"], g["elon_worse"]):
        bad.append("forecasters 'mostly' mixed")
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
