"""
Write site/sitemap.xml from the pages that actually exist.

It was a hand-kept list, and on 2026-09-05 it was four pages behind: it had
never gained continents, economy, food or neuron. A typed list of the site's
pages drifts for the same reason a typed nav does, and the fix is the same
one - generate it, and let the drift check compare the generated file against
the shipped one every run.

What goes in: every page in site/ except the full-screen apps, which are
reached from the page that introduces them and are not separate destinations.
index.html is listed as the bare domain at priority 1.0; everything else at
0.7, which is what the hand-kept file used.

lastmod is carried over from the shipped sitemap where a page already has one,
so re-running this does not churn every date on every build; a page appearing
for the first time gets today. That also makes the script idempotent, which is
what lets tests/test_generators.py check it.

Run:  python3 build_sitemap.py             report only
      python3 build_sitemap.py --apply
"""

import argparse
import datetime
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
OUT = os.path.join(SITE, "sitemap.xml")
BASE = "https://andrewsilvestri.com/"


def pages():
    out = []
    for path in sorted(glob.glob(os.path.join(SITE, "*.html"))):
        name = os.path.basename(path)
        if name.endswith("-app.html"):
            continue
        out.append(name)
    return out


def existing_lastmod():
    if not os.path.exists(OUT):
        return {}
    t = open(OUT, encoding="utf-8").read()
    found = {}
    for m in re.finditer(r"<loc>([^<]*)</loc>\s*<lastmod>([^<]*)</lastmod>", t):
        loc = m.group(1)
        name = "index.html" if loc == BASE else loc[len(BASE):]
        found[name] = m.group(2)
    return found


def render():
    known = existing_lastmod()
    today = datetime.date.today().isoformat()
    rows = []
    for name in pages():
        loc = BASE if name == "index.html" else BASE + name
        rows.append((loc, known.get(name, today),
                     "1.0" if name == "index.html" else "0.7"))
    rows.sort(key=lambda r: r[0])
    body = "".join(
        f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{mod}</lastmod>\n"
        f"    <priority>{pri}</priority>\n  </url>\n"
        for loc, mod, pri in rows)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + body + "</urlset>\n")


def main(apply=False):
    new = render()
    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
    n = len(re.findall(r"<loc>", new))
    if old is None:
        print(f"  sitemap.xml: new file, {n} urls" + ("" if apply else " (not written)"))
    else:
        state = "unchanged" if old == new else ("rewritten" if apply else "would change")
        print(f"  sitemap.xml: {state}, {n} urls")
        if old != new and not apply:
            was = {m for m in re.findall(r"<loc>([^<]*)</loc>", old)}
            now = {m for m in re.findall(r"<loc>([^<]*)</loc>", new)}
            for u in sorted(now - was):
                print(f"    + {u}")
            for u in sorted(was - now):
                print(f"    - {u}")
    if apply:
        open(OUT, "w", encoding="utf-8").write(new)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
