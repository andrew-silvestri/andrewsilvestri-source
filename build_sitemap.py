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

lastmod is the date of the last commit that touched the page
(`git log -1 --format=%cs -- site/<page>`), or today if the page in the tree
differs from HEAD - the ordering rule runs this before the commit, so an
edited page gets the day it is committed. Because it reads page bytes it runs
AFTER bust_cache.py, the last step that rewrites a page; run with the page
generators, sync_code_rows.py rewrote code.html behind it and the drift check
reported `DRIFT sitemap` (2026-10-18, HANDOFF trap 33). Until 2026-10-17 lastmod was
carried over from the shipped sitemap and never moved once set: seven of ten
pages were 33 days behind their last commit (AUDIT_2026-10 A4), and nothing
could see it, because a carried-over date always agrees with itself.

The history is read from SITEMAP_GIT_DIR if set, else this tree's .git.
tests/test_generators.py runs generators in a copy with no .git and sets
SITEMAP_GIT_DIR to the real one, so the drift check compares against history
rather than against the shipped file. With no history reachable this exits
non-zero rather than falling back to the shipped dates, which would make the
drift check agree by construction (trap 27). A page committed on an earlier
day than the ordering rule ran shows up there as drift.

Run:  python3 build_sitemap.py             report only
      python3 build_sitemap.py --apply
"""

import argparse
import datetime
import glob
import os
import re
import subprocess

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


def git(*args):
    gd = os.environ.get("SITEMAP_GIT_DIR") or os.path.join(HERE, ".git")
    r = subprocess.run(["git", "--git-dir", gd] + list(args),
                       capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"build_sitemap: git {' '.join(args)} failed in {gd}: "
                         + r.stderr.decode("utf-8", "replace").strip())
    return r.stdout


def lastmod(name, today):
    rel = "site/" + name
    on_disk = open(os.path.join(SITE, name), "rb").read()
    try:
        head = git("show", "HEAD:" + rel)
    except SystemExit:
        head = None                      # not committed yet
    if head != on_disk:
        return today
    return git("log", "-1", "--format=%cs", "--", rel).decode().strip()


def render():
    today = datetime.date.today().isoformat()
    # First, and on its own: with no reachable history every `git show` below
    # fails, every page reads as uncommitted, and every lastmod silently
    # becomes today. That is how the first version of this behaved when run
    # with SITEMAP_GIT_DIR pointing nowhere - exit 0, a plausible file.
    git("rev-parse", "--verify", "HEAD")
    rows = []
    for name in pages():
        loc = BASE if name == "index.html" else BASE + name
        rows.append((loc, lastmod(name, today),
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
    # newline="" on the read and "\n" on the write, both on purpose. Text mode
    # on Windows wrote CRLF, and a universal-newline read made "unchanged" true
    # of a file that differed on every line - tests/test_generators.py saw 53
    # CRLF on 53 lines and nothing here could (HANDOFF section 8, trap 32).
    old = open(OUT, encoding="utf-8", newline="").read() if os.path.exists(OUT) else None
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
        open(OUT, "w", encoding="utf-8", newline="\n").write(new)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
