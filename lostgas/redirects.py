"""Write the redirect stubs that replace the meter page and its simulator (R3, 2026-10-23).

meter.html ("What a meter's error is worth") and meter-app.html (the imbalance simulator) were
replaced by lostgas.html, per the R3 packet: the meter work's method moved into lostgas.html's
appendix and its model ships as meter-code.zip. The URLs keep answering, so links and bookmarks
land on the new page: GitHub Pages has no server-side redirects, so each is a small page with a
canonical link, a meta refresh and a plain link, and noindex (build_sitemap.py skips noindex pages).

meter/update_page.py and meter/build_app.py no longer write into site/ (their main() says so);
meter/update_page.values() is still what lostgas/update_page.py prints the appendix from.

Run:  python redirects.py            report only
      python redirects.py --apply
"""
import argparse
import os
import sys

SITE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site")
TARGET = "lostgas.html"
STUBS = {"meter.html": "What a meter's error is worth", "meter-app.html": "Imbalance simulator"}


def stub(title):
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Andrew Silvestri</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="https://andrewsilvestri.com/{TARGET}">
<meta http-equiv="refresh" content="0; url={TARGET}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
</head><body>
<p>This page is now part of <a href="{TARGET}">Lost gas</a>.</p>
</body></html>
"""


def main(apply):
    changed = 0
    for name, title in STUBS.items():
        p = os.path.join(SITE, name)
        new = stub(title).encode("utf-8")
        old = open(p, "rb").read() if os.path.exists(p) else None      # bytes: trap 32
        state = "unchanged" if old == new else ("rewritten" if apply else "would change")
        print(f"  {name}: {state}")
        if apply and old != new:
            with open(p, "wb") as f:
                f.write(new)
            changed += 1
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    sys.exit(main(ap.parse_args().apply))
