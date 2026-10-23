"""The insight kit's markup, written by code (R1, 2026-10-23).

Every reworked page builds these pieces through here rather than typing them,
because each carries a rule that is easy to break by hand:

- scrolly()    the scroll section. Its no-JS figures come from the browser's
               own chart code (kit_render.js runs site/assets/charts.js), and
               it refuses a spec whose labels collide at any width from the
               phone to the widest column.
- takeaways()  at most three, each a full sentence (_INSIGHT rule 4). A
               parameter label such as "C shared, ends alike 0.055%" is
               refused.
- stamp()      "Data through <month>", from the payload's last month; or the
               sentence saying the data does not update (_INSIGHT rule 5).
- counter()    a number that links to its source entry.
- clip()       a Manim clip with poster, two encodings and captions, from the
               metadata clips/render_clip.py writes beside the files.

Pages import this; it writes nothing itself.
"""
import html
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


class KitError(ValueError):
    pass


def _render(spec, states):
    job = json.dumps({"spec": spec, "states": states})
    r = subprocess.run(["node", os.path.join(HERE, "kit_render.js")], input=job,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise KitError("kit_render.js exited %d: %s" % (r.returncode, r.stderr.strip()))
    out = json.loads(r.stdout)
    if out["problems"]:
        raise KitError("chart %s does not fit:\n  %s" % (spec.get("id"), "\n  ".join(out["problems"][:12])))
    return out


def scrolly(spec, steps, from_state=None):
    """spec: a charts.js spec with an "id" and a "title".
    steps: [(html_of_the_step_text, state_dict), ...] in reading order."""
    if not steps:
        raise KitError("a scrolly needs at least one step")
    for key in ("id", "title", "type"):
        if not spec.get(key):
            raise KitError("chart spec has no %r" % key)
    states = [st for _, st in steps]
    snaps = _render(spec, states)
    sid = html.escape(spec["id"])
    out = ['<section class="scrolly wide" id="%s"%s>' % (
        sid, (" data-from='%s'" % html.escape(json.dumps(from_state), quote=True)) if from_state else "")]
    # json in a script element: only "</" can end it early
    out.append('<script type="application/json" class="scrolly-spec">%s</script>'
               % json.dumps(spec, separators=(",", ":")).replace("</", "<\\/"))
    out.append('<div class="scrolly-stage" role="img" aria-label="%s"></div>' % html.escape(spec["title"]))
    out.append('<div class="scrolly-steps">')
    for i, (text, st) in enumerate(steps):
        out.append("<div class=\"step\" data-state='%s'>" % html.escape(json.dumps(st), quote=True))
        out.append(text)
        out.append('<figure class="step-fig"><div class="snap-wide">%s</div><div class="snap-phone">%s</div></figure>'
                   % (snaps["wide"][i], snaps["phone"][i]))
        out.append("</div>")
    out.append("</div>\n</section>")
    return "\n".join(out)


_LABEL = re.compile(r"^[^.!?]*\s[-−]?[\d.,]+\s*(%|[A-Za-z/]{1,8})?$")


def takeaways(sentences):
    """At most three plain-English takeaways, each a full sentence."""
    if not 1 <= len(sentences) <= 3:
        raise KitError("takeaways: %d given; at most three, at least one" % len(sentences))
    items = []
    for s in sentences:
        s = s.strip()
        words = s.split()
        if len(words) < 8:
            raise KitError("takeaways: not a sentence (under eight words): %r" % s)
        if not (s[0].isupper() or s[0].isdigit()):
            raise KitError("takeaways: does not start a sentence: %r" % s)
        if s[-1] not in ".!?":
            raise KitError("takeaways: does not end a sentence: %r" % s)
        if _LABEL.match(s.rstrip(".!?")):
            raise KitError("takeaways: reads as a label and a value, not a sentence: %r" % s)
        items.append("<li>%s</li>" % s)
    return '<section class="takeaways" aria-label="Takeaways"><ol>%s</ol></section>' % "".join(items)


def month_name(ym):
    m = re.fullmatch(r"(\d{4})-(\d{2})", ym)
    if not m or not 1 <= int(m.group(2)) <= 12:
        raise KitError("stamp: month must be YYYY-MM, got %r" % ym)
    return "%s %s" % (MONTHS[int(m.group(2)) - 1], m.group(1))


def stamp(through=None, source=None, live=True):
    """through: the last month of data in the payload, YYYY-MM, read from the
    payload by the caller - never typed. live=False for data that does not
    update; then through may be None."""
    if live:
        if not through or not source:
            raise KitError("stamp: a live page needs the payload's last month and its source")
        return ('<p class="stamp">Data through <time datetime="%s">%s</time> &middot; '
                'refreshed monthly from %s</p>' % (through, month_name(through), html.escape(source)))
    tail = " (last month %s)" % month_name(through) if through else ""
    return '<p class="stamp">This data does not update%s.</p>' % tail


def stamp_annual(year, source, as_of, cadence):
    """For data published once a year (R3, 2026-10-23): the newest year in the
    payload, the source and its own as-of date, and when the next year comes.
    All three are read from the payload by the caller, never typed."""
    if not re.fullmatch(r"\d{4}", str(year)) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", as_of or ""):
        raise KitError("stamp_annual: year YYYY and as_of YYYY-MM-DD, got %r, %r" % (year, as_of))
    y, m, d = as_of.split("-")
    return ('<p class="stamp">Reports through <time datetime="%s">%s</time> &middot; %s, data as of '
            '<time datetime="%s">%d %s %s</time> &middot; %s</p>'
            % (year, year, html.escape(source), as_of, int(d), MONTHS[int(m) - 1], y, html.escape(cadence)))


def counter(value, decimals, ref, unit=None):
    """A number tied to its source: the text is the value, the link is the
    reference entry (ref is that entry's id, e.g. "ref3")."""
    from_js = "{:,.{d}f}".format(abs(value), d=decimals)
    text = ("−" if value < 0 and float(from_js.replace(",", "")) != 0 else "") + from_js
    u = " %s" % html.escape(unit) if unit else ""
    return ('<a class="counter" href="#%s" data-value="%r" data-decimals="%d">%s</a>%s'
            % (html.escape(ref), value, decimals, text, u))


def clip(meta_path, caption, src_prefix="assets/clips/"):
    """meta_path: the .json render_clip.py writes beside a clip. The clip
    loops muted only if it is ten seconds or shorter (_INSIGHT rule 2)."""
    with open(meta_path, encoding="utf-8") as fh:
        m = json.load(fh)
    name, loop = m["name"], m["duration_s"] <= 10.0
    p = src_prefix + name
    return ('<figure class="clip wide" data-loop="%d">'
            '<div class="clip-frame">'
            '<video controls playsinline preload="none"%s poster="%s.png" width="%d" height="%d">'
            # MP4 FIRST. With the VP9 WebM listed first, WebKit (Playwright
            # 1.62's, Windows) never fired load on the page: tests/test_chrome.js
            # and test_invariants.js timed out on the kit fixture, 2026-10-23,
            # and loaded in about 0.5 s with the order swapped. H.264 plays in
            # every current browser; the WebM is the fallback for builds
            # without it.
            '<source src="%s.mp4" type="video/mp4">'
            '<source src="%s.webm" type="video/webm; codecs=vp9">'
            '<track kind="captions" src="%s.vtt" srclang="en" label="English" default>'
            '</video>'
            '<button class="clip-play" type="button" hidden aria-label="Play the clip: %s">Play &#9656; %ds</button>'
            '</div><figcaption>%s</figcaption></figure>'
            % (1 if loop else 0, " muted" if loop else "", p, m["width"], m["height"], p, p, p,
               html.escape(m["title"]), round(m["duration_s"]), caption))
