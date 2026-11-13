"""
Write site/messaging.html from template.html and outputs/payload.json.

Every number on the page that a chart shows comes from the payload; the prose is in the template. The parts
other scripts own - the nav (rebuild_nav.py), the citation markers and Sources list (add_citations.py's
table, applied here) and the ?v= stamps (bust_cache.py) - are kept as the shipped page has them, so
tests/test_generators.py can run this on the shipped tree and expect no change. The idiom is
oxygen/update_page.py's.

The hero is a dot chart drawn here as two SVGs (900px and 320px): one row a field trial, a hollow dot for
the share choosing the low-carbon option without the change and a filled dot with it. Rows carry data-o,
the step they belong to; site/assets/messaging.js shows them group by group as the reader scrolls. The two
supporting charts are drawn here the same way, static, at 720px and 320px.

claims() asserts every range and direction the template's words commit to ("under two points", "tens of
points", "none raised it"). If a rebuild moves one, the generator stops rather than ship prose the payload
contradicts. fits() checks every label against the width it is drawn in.

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
PAGE = os.path.join(SITE, "messaging.html")
TEMPLATE = os.path.join(HERE, "template.html")
PAYLOAD = os.path.join(HERE, "outputs", "payload.json")
ZIP = os.path.join(SITE, "downloads", "messaging-code.zip")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

E = html.escape
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
GROUPS = [("words", "Words: labels, signs, names", "Words"), ("menus", "Menus: more low-carbon dishes", "Menus"),
          ("food_default", "Defaults: food", "Defaults, food"),
          ("energy_default", "Defaults: electricity", "Defaults, power")]
# Perfidy Text at 13px and Perfidy Mono at 12px, measured for oxygen's tree (2026-11-08): 0.450 em and
# 0.56 em a character. 0.47 em is used for the proportional face to leave room.
EM_SANS, EM_MONO = 0.47, 0.56


def f1(x):
    return f"{x:.1f}"


def pp(x):
    return f"{x:+.1f}".replace("-", "&minus;") if abs(x) >= 0.05 else "0.0"


# ------------------------------------------------------------------ hero ---
def hero_svg(P, wide):
    """Wide: the full label left of the axis. Phone: a short label in a 112px column, the axis in the rest, so
    the sticky chart stays under half a phone screen and the step cards stay readable below it."""
    fx = P["effects"]
    if wide:
        W, x0, x1, top, rh, hh = 900, 330, 860, 28, 23, 24
    else:
        W, x0, x1, top, rh, hh = 320, 116, 300, 26, 21, 21
    X = lambda v: x0 + (x1 - x0) * v / 100   # noqa: E731
    rows, y = [], top
    for g, head, short in GROUPS:
        members = [r for r in fx if r["group"] == g]
        rows.append(("h", head if wide else short, y + hh - 7, members[0]["o"]))
        y += hh
        for r in members:
            rows.append(("r", r, y, r["o"]))
            y += rh
    H = y + 6
    cls = "msg-wide" if wide else "msg-phone"
    out = [f'<svg class="dots {cls}" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-labelledby="msg-desc">']
    for t in (0, 25, 50, 75, 100) if wide else (0, 50, 100):
        out.append(f'<line class="grid" x1="{X(t):.1f}" y1="{top - 6}" x2="{X(t):.1f}" y2="{H - 4}"/>')
        anchor = "end" if (t == 100 and not wide) else "middle"
        out.append(f'<text class="ax" x="{X(t):.1f}" y="14" text-anchor="{anchor}">{t}%</text>')
    for kind, r, yy, o in rows:
        if kind == "h":
            out.append(f'<text class="gh" x="0" y="{yy}" data-o="{o}">{E(r)}</text>')
            continue
        c = "w" if r["group"] == "words" else "d"
        dy = yy + rh / 2 + 1
        out.append(f'<g class="row {c}" data-o="{o}">')
        out.append(f'<text class="lab" x="{0 if wide else 8}" y="{dy + 4.5:.1f}">{E(r["label"] if wide else r["short"])}</text>')
        b, t = X(r["baseline"]), X(r["treated"])
        out.append(f'<line class="link" x1="{b:.1f}" y1="{dy:.1f}" x2="{t:.1f}" y2="{dy:.1f}"/>')
        out.append(f'<circle class="b" cx="{b:.1f}" cy="{dy:.1f}" r="4.5"/>')
        out.append(f'<circle class="t" cx="{t:.1f}" cy="{dy:.1f}" r="5"/>')
        txt = pp(r["effect"])
        tw = len(re.sub("&[a-z]+;", "-", txt)) * 12 * EM_MONO
        hi, lo = max(b, t), min(b, t)
        if hi + 9 + tw <= W:
            out.append(f'<text class="eff" x="{hi + 9:.1f}" y="{dy + 4:.1f}">{txt}</text>')
        else:
            out.append(f'<text class="eff" x="{lo - 9:.1f}" y="{dy + 4:.1f}" text-anchor="end">{txt}</text>')
        out.append("</g>")
    out.append("</svg>")
    return "".join(out)


def hero(P, v):
    steps = [
        (0, "Words &middot; field trials, real purchases",
         f"Carbon labels in university and workplace cafeterias, screens telling diners that more and more "
         f"customers choose the veggie options, and the best of three new names for a meat-free breakfast. Each "
         f"was tested on what people bought. The largest moved the share choosing the low-carbon meal by "
         f"{v['w_hi']} percentage points; the preregistered screens in 22 restaurants moved it by nothing the "
         f"trial could detect."),
        (1, "Menus &middot; more of the low-carbon dish",
         f"Doubling the vegetarian dishes on offer, and leaving the meat dishes on the menu, raised the vegetarian "
         f"share by {v['menu_lo']} points in a Cambridge experiment and {v['menu_hi']} points in a Dijon "
         f"cafeteria."),
        (2, "Defaults &middot; food",
         f"Serving the plant-based dish unless diners asked for meat, making a restaurant's chef's menu vegetarian "
         f"unless diners asked otherwise, or checking the plant-based meal on an event form in advance, moved the "
         f"share by {v['food_lo']} to {v['food_hi']} points."),
        (3, "Defaults &middot; electricity",
         f"Pre-selecting a green tariff in a German supplier's online shop took green contracts from "
         f"{v['eb_b']} to {v['eb_t']} percent of sales. "
         '<a href="#unit">How the rows compare</a>'),
        (4, "What the long bars measure",
         "One choice, at one counter, form or shop, at one time. Whether people ate less meat that day, or "
         "whether green contracts added clean power, are separate questions, and the evidence on them is "
         'thinner. <a href="#limits-default">What a default does not do</a>'),
    ]
    rows = "; ".join(f"{r['label']}, {f1(r['baseline'])} to {f1(r['treated'])} percent" for r in P["effects"])
    desc = (f"A dot chart of {len(P['effects'])} field trials. Each row shows the share of people choosing the low-carbon "
            "option without and with a change, on a scale of 0 to 100 percent. " + rows + ".")
    out = ['<figure class="msg wide" aria-label="Field trials: the share choosing the low-carbon option, without '
           'and with each change">',
           '<div class="msg-fig">', f'<p id="msg-desc" hidden>{E(desc)}</p>',
           hero_svg(P, True), hero_svg(P, False),
           '<p class="msg-key">Hollow dot: without the change. Filled dot: with it. Number: the difference in '
           'percentage points. Brown: words. Blue: the choice itself.</p>',
           '</div>', '<div class="msg-steps">']
    for k, head, text in steps:
        out.append(f'<div class="step" data-step="{k}"><p class="ev">{head}</p><p>{text}</p></div>')
    out.append("</div>\n</figure>")
    return "\n".join(out)


# ---------------------------------------------------------------- charts ---
def figure(svg_wide, svg_phone, title, caption, label):
    return ('<figure class="step-fig wide" role="img" aria-label="%s"><div class="snap-wide">%s</div>'
            '<div class="snap-phone">%s</div><figcaption class="dim"><b>%s.</b> %s</figcaption></figure>'
            % (E(label), svg_wide, svg_phone, E(title), caption))


def fmt_unit(x, unit):
    if unit == "Cohen's d":
        return f"d {x:.2f}"
    if unit == "percentage points":
        return f"{x:g} pp"
    return f"{x:.2f}%"


def shrink_svg(P, wide):
    S = P["shrink"]
    if wide:
        W, x0, x1, rh, top = 720, 300, 660, 46, 26
    else:
        W, x0, x1, rh, top = 320, 0, 250, 62, 26
    X = lambda v: x0 + (x1 - x0) * v   # noqa: E731
    H = top + rh * len(S) + 4
    out = [f'<svg class="bars" viewBox="0 0 {W} {H}" width="{W}" height="{H}" aria-hidden="true">']
    for t in (0, 0.5, 1):
        out.append(f'<line class="grid" x1="{X(t):.1f}" y1="{top - 8}" x2="{X(t):.1f}" y2="{H - 2}"/>')
        a = "start" if t == 0 else "end" if (t == 1 and not wide) else "middle"
        out.append(f'<text class="ax" x="{X(t):.1f}" y="13" text-anchor="{a}">{int(100 * t)}%</text>')
    for i, r in enumerate(S):
        y = top + i * rh
        k = max(r["kept"], 0)
        later = f"{fmt_unit(r['later'], r['unit'])} {r['later_label']}"
        first = f"{fmt_unit(r['first'], r['unit'])} {r['first_label']}"
        if wide:
            out.append(f'<text class="lab" x="0" y="{y + 13}">{E(r["label"])}</text>')
            out.append(f'<text class="sub" x="0" y="{y + 30}">{E(first)}</text>')
            by = y + 4
        else:
            out.append(f'<text class="lab" x="0" y="{y + 12}">{E(r["label"])}</text>')
            out.append(f'<text class="sub" x="0" y="{y + 27}">{E(first)}</text>')
            by = y + 34
        out.append(f'<rect class="full" x="{x0}" y="{by}" width="{x1 - x0}" height="12"/>')
        out.append(f'<rect class="kept" x="{x0}" y="{by}" width="{max(X(k) - x0, 1.5):.1f}" height="12"/>')
        out.append(f'<text class="sub" x="{x0}" y="{by + 27}">{E(later)}</text>')
        out.append(f'<text class="eff" x="{x1 + 8}" y="{by + 11}">{100 * k:.0f}%</text>')
    out.append("</svg>")
    return "".join(out)


def chart_shrink(P, v):
    cap = (f"Each bar is the later or larger-sample estimate as a share of the first. Nudge trials run by "
           f"government units kept about a sixth of the effect reported in journals, {v['nudge_later']} against "
           f"{v['nudge_first']} percentage points. Among nudge types, those that change the choice itself fell "
           f"from d {v['struct_first']} to {v['struct_later']} after correction for publication bias, and those "
           f"that add information fell to {v['info_later']}; d is Cohen's d, a difference in standard deviations. "
           f"Data: DellaVigna and Linos 2022; Allcott 2015; Nisa et al. 2019; Bergquist et al. 2023; Maier et al. "
           f"2022, each as printed in the table or page the build file names.")
    return figure(shrink_svg(P, True), shrink_svg(P, False),
                  "What is left of an effect when the sample grows or the bias is removed", cap,
                  "Bar chart: six effects, each later estimate as a percentage of the first")


def tour_svg(P, wide):
    T = P["tournament"]["wept"]
    arms = sorted(T["arms"].values(), key=lambda a: a["est"])
    lo, hi = -0.8, 0.4
    if wide:
        W, x0, x1, rh, top = 720, 300, 700, 26, 28
    else:
        W, x0, x1, rh, top = 320, 10, 306, 40, 28
    X = lambda v: x0 + (x1 - x0) * (v - lo) / (hi - lo)   # noqa: E731
    H = top + rh * len(arms) + 6
    out = [f'<svg class="ci" viewBox="0 0 {W} {H}" width="{W}" height="{H}" aria-hidden="true">']
    for t in (-0.8, -0.4, 0, 0.4):
        c = "zero" if t == 0 else "grid"
        out.append(f'<line class="{c}" x1="{X(t):.1f}" y1="{top - 8}" x2="{X(t):.1f}" y2="{H - 2}"/>')
        a = "start" if (t == lo and not wide) else "end" if (t == hi and not wide) else "middle"
        lab = f"{t:+.1f}".replace("+0.0", "0").replace("-", "−") + (" pages" if t == hi else "")
        out.append(f'<text class="ax" x="{X(t):.1f}" y="13" text-anchor="{a}">{lab}</text>')
    for i, a in enumerate(arms):
        y = top + i * rh
        dy = y + (13 if wide else 28)
        out.append(f'<text class="lab" x="{0 if wide else x0}" y="{y + (17 if wide else 12)}">{E(a["name"])}</text>')
        down = a["hi"] < 0
        out.append(f'<line class="whisk{" dn" if down else ""}" x1="{X(a["lo"]):.1f}" y1="{dy}" '
                   f'x2="{X(a["hi"]):.1f}" y2="{dy}"/>')
        out.append(f'<circle class="pt{" dn" if down else ""}" cx="{X(a["est"]):.1f}" cy="{dy}" r="4.5"/>')
    out.append("</svg>")
    return "".join(out)


def chart_tournament(P, v):
    cap = (f"Pages of the tree-planting task completed, each message against the control group, with 95 percent "
           f"intervals. The control group averaged {v['wept_ctrl']} of 8 pages. Filled dark dots: intervals "
           f"entirely below zero. Data: Vlasceanu et al. 2024, participant data on Zenodo (record 10345806), {v['n_tour']} "
           f"participants in {v['n_countries']} countries; this page's estimate, with country fixed effects and "
           f"errors clustered by country.")
    return figure(tour_svg(P, True), tour_svg(P, False),
                  "Effect of 11 climate messages on an effortful task, in pages", cap,
                  "Dot chart: 11 messages, none above zero, six below")


def kit_table(P):
    out = ['<table class="n kit" tabindex="0">',
           "<thead><tr><th>What was tested</th><th>What it moved</th><th>Evidence</th><th>Where it fails</th></tr></thead>"
           "<tbody>"]
    for r in P["kit"]:
        out.append(f'<tr><td data-label="Tested"><b>{E(r["item"])}.</b> <i>{E(r["example"])}</i></td>'
                   f'<td data-label="Moved">{E(r["effect"])}</td>'
                   f'<td data-label="Evidence"><b>{E(r["grade"])}</b> &middot; {E(r["evidence"])}</td>'
                   f'<td data-label="Fails">{E(r["fails"])}</td></tr>')
    out.append("</tbody></table>")
    return "\n".join(out)


# ---------------------------------------------------------------- checks ---
def fits(P):
    bad = []
    for r in P["effects"]:
        if len(r["label"]) * 13 * EM_SANS > 318:
            bad.append(("hero wide", r["label"]))
        if len(r["short"]) * 12 * EM_SANS > 100:
            bad.append(("hero phone", r["short"]))
    for r in P["shrink"]:
        for s, w in ((r["label"], 290), (f"d 0.00 {r['first_label']}", 290), (f"d 0.00 {r['later_label']}", 290)):
            if len(s) * 12 * EM_SANS > w:
                bad.append(("shrink", s))
    for a in P["tournament"]["wept"]["arms"].values():
        if len(a["name"]) * 12 * EM_SANS > 290:
            bad.append(("tournament", a["name"]))
    if bad:
        raise SystemExit(f"labels too long for the width they are drawn at: {bad}")


def claims(P, v):
    fx = P["effects"]
    words = [r["effect"] for r in fx if r["group"] == "words"]
    design = [r["effect"] for r in fx if r["group"] != "words"]
    W = P["tournament"]["wept"]["arms"]
    four = sorted(a["est"] for a in W.values())[:4]
    by = {r["id"]: r for r in P["shrink"]}
    c = [
        ("h1 'by under {w_cap}': every words row below w_cap", all(w < int(v["w_cap"]) for w in words)),
        ("'tens of points' for defaults: every default row at least 20", all(r["effect"] >= 20 for r in fx
                                                                            if r["group"].endswith("default"))),
        ("menus and defaults all above the largest words row", min(design) > max(words)),
        ("'nothing the trial could detect': the norm sign within 0.5 points of zero",
         abs([r for r in fx if r["id"] == "coker"][0]["effect"]) < 0.5),
        ("'about a tenfold rise' for the green default: ratio 8-12",
         8 <= [r for r in fx if r["id"] == "ebeling"][0]["treated"] / [r for r in fx if r["id"] == "ebeling"][0]["baseline"] <= 12),
        ("'none raised it': no tree-task interval entirely above zero", not any(a["lo"] > 0 for a in W.values())),
        ("'six lowered it'", sum(a["hi"] < 0 for a in W.values()) == 6),
        ("'the four largest drops 0.4 to 0.5 pages'", all(-0.55 < x < -0.35 for x in four)),
        ("'about a tenth of the control average': largest drop 8-12% of it",
         0.08 < -four[0] / P["tournament"]["wept"]["control_mean"] < 0.12),
        ("'the negative-emotion message that did most for sharing did most harm to effort'",
         max(P["tournament"]["share"]["arms"], key=lambda a: P["tournament"]["share"]["arms"][a]["est"])
         == min(W, key=lambda a: W[a]["est"]) == "NegativeEmotions"),
        ("'a near tie' for policy support: letter within 0.2 points of the top",
         max(a["est"] for a in P["tournament"]["policy"]["arms"].values())
         - P["tournament"]["policy"]["arms"]["LetterFutureGen"]["est"] < 0.2),
        ("'about a sixth' for nudge units", 0.12 < by["nudge"]["kept"] < 0.2),
        ("'the one category that kept something': structure above 0.1, information at 0",
         by["structure"]["later"] > 0.1 and by["info"]["later"] == 0),
        ("'about four in five did at least one page' in control", 0.78 < P["tournament"]["wept_ctrl_any"] < 0.86),
        ("'three quarters of the first effect' for home energy reports", 0.7 < by["opower"]["kept"] < 0.8),
    ]
    bad = [n for n, ok in c if not ok]
    if bad:
        raise SystemExit("payload contradicts the template's words:\n  " + "\n  ".join(bad))


def values(P):
    import insight
    fx = {r["id"]: r for r in P["effects"]}
    words = [r["effect"] for r in P["effects"] if r["group"] == "words"]
    menus = [r["effect"] for r in P["effects"] if r["group"] == "menus"]
    food = [r["effect"] for r in P["effects"] if r["group"] == "food_default"]
    T = P["tournament"]
    sh = {r["id"]: r for r in P["shrink"]}

    def top(y):
        a = max(T[y]["arms"].values(), key=lambda a: a["est"])
        return f"{a['est']:.1f}", a["name"].lower() if a["name"] != "Negative emotion" else "negative emotion"
    W = T["wept"]["arms"]
    four = sorted(a["est"] for a in W.values())[:4]
    v = {
        "w_hi": f1(max(words)), "w_cap": str(math.ceil(max(words))),
        "menu_lo": f1(min(menus)), "menu_hi": f"{max(menus):.0f}",
        "food_lo": f"{min(food):.0f}", "food_hi": f"{max(food):.0f}",
        "eb_b": f1(fx["ebeling"]["baseline"]), "eb_t": f1(fx["ebeling"]["treated"]),
        "eb_pp": f1(fx["ebeling"]["effect"]), "eb_n": f"{fx['ebeling']['n']:,}",
        "d_hi": f"{max(r['effect'] for r in P['effects']):.0f}",
        "n_tour": f"{T['n']:,}", "n_countries": str(T["countries"]),
        "belief_top": top("belief")[0], "belief_name": top("belief")[1],
        "policy_top": top("policy")[0], "policy_name": top("policy")[1],
        "share_top": top("share")[0], "share_name": top("share")[1],
        "share_ctrl": f"{T['share']['control_mean']:.0f}",
        "wept_ctrl": f"{T['wept']['control_mean']:.1f}", "wept_any": f"{100 * T['wept_ctrl_any']:.0f}",
        "wept_lo": f"{-four[-1]:.2f}", "wept_hi": f"{-four[0]:.2f}",
        "nudge_first": f"{sh['nudge']['first']:g}", "nudge_later": f"{sh['nudge']['later']:g}",
        "opower_first": f"{sh['opower']['first']:.2f}", "opower_later": f"{sh['opower']['later']:.2f}",
        "struct_first": f"{sh['structure']['first']:.2f}", "struct_later": f"{sh['structure']['later']:.2f}",
        "info_later": f"{sh['info']['later']:.2f}",
        "berg_first": f"{sh['bergquist']['first']:.2f}", "berg_later": f"{sh['bergquist']['later']:.2f}",
        "lit_through": "%s %s" % (MONTHS[int(P["literature_through"][5:]) - 1], P["literature_through"][:4]),
        "zip_kb": f"{round(os.path.getsize(ZIP) / 1024) if os.path.exists(ZIP) else 0:,}",
    }
    v["stamp"] = insight.stamp(live=False)
    v["takeaways"] = insight.takeaways([
        f"In field trials that counted real purchases, carbon labels, a social-norm sign and a renamed dish changed "
        f"the share of people choosing the low-carbon option by {v['w_hi']} percentage points or less.",
        f"Making the low-carbon option the default, or putting more of it on the menu, changed the same share by "
        f"{v['menu_lo']} to {v['d_hi']} points, for lunches and for electricity tariffs alike.",
        "Those large shifts are in one choice at one counter or form; whether people eat or emit less over a "
        "whole day is mostly unmeasured, and the kit below is graded with that in mind."])
    claims(P, v)
    fits(P)
    v["hero"] = hero(P, v)
    v["chart_shrink"] = chart_shrink(P, v)
    v["chart_tournament"] = chart_tournament(P, v)
    v["kit_table"] = kit_table(P)
    return v


def keep_from_shipped(text, shipped):
    """The parts other scripts own, carried over from the page that ships."""
    if shipped is None:
        shipped = open(os.path.join(SITE, "longevity.html"), encoding="utf-8").read()
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
    unused = sorted(set(v) - set(re.findall(r"{{(\w+)}}", t)) - {"w_cap", "eb_n", "food_lo", "food_hi",
                                                                  "nudge_first", "nudge_later",
                                                                  "struct_first", "struct_later", "info_later",
                                                                  "menu_hi", "n_countries", "share_name"})
    if unused:
        raise SystemExit(f"values the template no longer uses: {unused}")
    for k, val in v.items():
        t = t.replace("{{" + k + "}}", str(val))
    shipped = open(PAGE, encoding="utf-8").read() if os.path.exists(PAGE) else None
    return keep_from_shipped(t, shipped)


def cite(text):
    import add_citations
    refs = add_citations.PAGES.get("messaging.html")
    if not refs:
        return text, ["messaging.html has no entry in add_citations.PAGES"]
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
        print("  messaging.html: " + ("unchanged" if old == t else "would change" if not apply else "rewritten"))
    else:
        print("  messaging.html: new page" + ("" if apply else " (not written)"))
    if apply:
        open(PAGE, "w", encoding="utf-8", newline="\n").write(t)
    return 1 if probs else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
