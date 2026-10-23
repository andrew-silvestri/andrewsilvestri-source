"""Build tests/fixtures/kit.html, the insight kit's fixture page (R1).

Every piece of the kit on one page, built through insight.py exactly as a
reworked page will build it, so the site's gates (layout, contrast, chrome,
invariants) and tests/test_kit.js measure the kit as it ships. The data is
SYNTHETIC and the page says so; it lives in tests/, never in site/, so it is
never published (test_layout.js's server comment says why).

    python tests/fixtures/build_kit_fixture.py          # writes kit.html
    python tests/fixtures/build_kit_fixture.py --check  # exit 1 if kit.html is stale
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import insight  # noqa: E402

OUT = os.path.join(HERE, "kit.html")


def months(y0, m0, n):
    out = []
    for i in range(n):
        k = (m0 - 1) + i
        out.append("%04d-%02d" % (y0 + k // 12, k % 12 + 1))
    return out


def synthetic():
    """Two made-up monthly series: a smooth rise and a staircase that steps
    over it, crossing several times, so the band has both signs."""
    x = months(2018, 1, 105)   # Jan 2018 .. Sep 2026
    prod = [round(9 + 0.19 * i + 0.6 * math.sin(i / 7.0), 2) for i in range(len(x))]
    steps = {0: 10.0, 22: 13.5, 40: 16.0, 62: 21.0, 80: 25.5, 96: 27.0}
    cap, c = [], None
    for i in range(len(x)):
        c = steps.get(i, c)
        cap.append(c)
    return x, prod, cap


def build():
    x, prod, cap = synthetic()
    series = {
        "type": "series", "id": "kit-series",
        "title": "Synthetic test data: a rising series against a stepped one, January 2018 to September 2026",
        "x": x,
        "series": [{"key": "a", "label": "Rising (synthetic)", "color": "moss", "values": prod},
                   {"key": "b", "label": "Stepped (synthetic)", "color": "acc", "values": cap}],
        "band": {"a": "a", "b": "b",
                 "pos": {"color": "moss", "label": "Rising above"},
                 "neg": {"color": "acc", "label": "Room to spare"}},
        # five labels ~50px apart do not fit a 320px chart with full words
        # (charts.js refuses it), so each carries a short form for phones
        "annotations": [{"at": x[22], "text": "Step one", "short": "S1"},
                        {"at": x[40], "text": "Step two", "short": "S2"},
                        {"at": x[62], "text": "Step three, a longer label", "short": "S3"},
                        {"at": x[80], "text": "Step four", "short": "S4"},
                        {"at": x[96], "text": "Step five", "short": "S5"}],
        "y": {"label": "units/d"},
    }
    steps1 = [
        ("<p>This is the insight kit's fixture page. Every number on it is synthetic. "
         "The first step shows the series at its start.</p>", {"t": 0.05}),
        ("<p>As the reader scrolls, the line draws forward and the gap between the two "
         "series fills in, in one colour where the rising series is above and another where it is below.</p>",
         {"t": 0.45}),
        ("<p>Each annotation appears when the line reaches its date.</p>", {"t": 0.8}),
        ("<p>The last step shows the whole record.</p>", {"t": 1.0}),
    ]
    split = {
        "type": "split", "id": "kit-split",
        "title": "Synthetic test data: one total split into four parts",
        "unit": "units", "decimals": 1,
        "total": {"label": "All of it,", "value": 100.0},
        "parts": [{"label": "Part one", "value": 52.0, "color": "acc"},
                  {"label": "Part two", "value": 27.5, "color": "moss"},
                  {"label": "Part three", "value": 15.0, "color": "ink"},
                  {"label": "Part four", "value": 5.5, "color": "rule"}],
    }
    steps2 = [
        ("<p>A total, before it is split.</p>", {"s": 0}),
        ("<p>The same total, split into where it goes.</p>", {"s": 1}),
    ]
    clip_meta = os.path.join(HERE, "clips", "kit-test.json")
    clip = (insight.clip(clip_meta, "A synthetic eight-second test clip: a line drawn on axes, "
                         "with captions. It proves the clip pipeline and says nothing about any data.",
                         src_prefix="clips/")
            if os.path.exists(clip_meta) else "")

    nav = re.search(r'<nav class="top">.*?</nav>', open(os.path.join(ROOT, "site", "heat.html"), encoding="utf-8").read(), re.S).group(0)
    body = "\n".join([
        "<h1>Insight kit fixture</h1>",
        '<p class="dim">A test page for the scroll scaffold, the charts, the clip, the takeaways and the stamp. '
        "Every number on it is synthetic.</p>",
        insight.stamp("2026-09", "a synthetic source"),
        insight.takeaways([
            "This page exists so the site's tests can measure the kit as it ships.",
            "Every number on this page is made up and none of it describes the world.",
        ]),
        "<h2>A series that draws as you scroll</h2>",
        insight.scrolly(series, steps1, from_state={"t": 0}),
        "<p>A number tied to its source: " + insight.counter(1234.5, 1, "ref1", "units") +
        ", which links to the first entry under Sources.</p>",
        "<h2>Where it goes</h2>",
        insight.scrolly(split, steps2, from_state={"s": 0}),
        "<h2>A clip</h2>" if clip else "",
        clip,
        "<h2>Sources</h2>",
        '<ol class="refs"><li id="ref1"><span class="src">Synthetic. Generated by tests/fixtures/build_kit_fixture.py.</span></li></ol>',
    ])
    return """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Insight kit fixture</title>
<meta name="robots" content="noindex">
<script>try{document.documentElement.dataset.motion=matchMedia('(prefers-reduced-motion: reduce)').matches?'off':'on';}catch(e){document.documentElement.dataset.motion='on';}</script>
<link rel="stylesheet" href="../style.css">
<link rel="stylesheet" href="../assets/scrolly.css">
</head><body>
%s
<main>
%s
<footer>
<p>Insight kit fixture (tests only)</p>
</footer>
</main>
<script src="../assets/motion.js"></script>
<script src="../assets/nav.js"></script>
<script src="../assets/charts.js"></script>
<script src="../assets/scrolly.js"></script>
</body></html>
""" % (nav, body)


if __name__ == "__main__":
    html = build()
    if "--check" in sys.argv:
        cur = open(OUT, "rb").read() if os.path.exists(OUT) else b""
        if cur != html.encode("utf-8"):
            print("kit.html is stale: run python tests/fixtures/build_kit_fixture.py")
            sys.exit(1)
        print("kit.html current")
        sys.exit(0)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    print("wrote", OUT, len(html.encode("utf-8")), "bytes")
