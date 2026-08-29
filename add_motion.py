"""
Add the data-motion contract to every shared-chrome page.

The footer toggle is the contract every other item in the revamp is written
against (see REVAMP_BRIEF.md sec2): a blocking <head> snippet sets
document.documentElement.dataset.motion before the stylesheet loads,
prefers-reduced-motion supplies its default, and a footer control overrides
that default without a reload.

This touches the 11 pages that share style.css and <footer> - the app pages
(atlas-app.html, climate-cost-app.html, longevity-app.html, skyline-app.html,
bookshelf-app.html) have their own inline CSS, no shared nav, and never load
style.css, so they are excluded by the absence of <footer> rather than by a
hard-coded list.

Idempotent: a page that already carries the marker (dataset.motion) is left
alone, so re-running after a partial apply is safe.

Run the report first, then apply:

    python add_motion.py
    python add_motion.py --apply
"""

import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")

HEAD_SNIPPET = (
    '<script>/* the motion contract — set before first paint */\n'
    "try{var m=localStorage.getItem('motion');"
    "if(m!=='on'&&m!=='off')"
    "m=matchMedia('(prefers-reduced-motion: reduce)').matches?'off':'on';"
    "document.documentElement.dataset.motion=m;}"
    "catch(e){document.documentElement.dataset.motion='on';}</script>\n"
)

FOOTER_CONTROL = (
    ' &middot;\n'
    '<button type="button" class="motion-toggle" hidden>Motion: '
    '<span class="motion-state">on</span></button>'
)

BODY_SCRIPT = '<script src="assets/motion.js"></script>\n'

STYLESHEET_RE = re.compile(r'<link rel="stylesheet" href="style\.css[^"]*">')
FOOTER_CLOSE_RE = re.compile(r'</footer>')
BODY_CLOSE_RE = re.compile(r'</body>')


def process(original):
    """Return (new_text, count_inserted). Each insertion point is applied at
    most once, and skipped if its marker is already present. Presence is
    checked against the ORIGINAL text, not the text as it is progressively
    rewritten - inserting the head snippet must never be able to mask a
    later check just because its own markup happens to mention a later
    marker."""
    text = original
    inserted = 0

    if 'dataset.motion' not in original:
        text, n = STYLESHEET_RE.subn(
            lambda m: HEAD_SNIPPET + m.group(0), text, count=1)
        inserted += n

    if 'motion-toggle' not in original:
        text, n = FOOTER_CLOSE_RE.subn(
            lambda m: FOOTER_CONTROL + m.group(0), text, count=1)
        inserted += n

    if 'assets/motion.js' not in original:
        text, n = BODY_CLOSE_RE.subn(
            lambda m: BODY_SCRIPT + m.group(0), text, count=1)
        inserted += n

    return text, inserted


def main():
    apply = '--apply' in sys.argv
    total = 0
    for path in sorted(glob.glob(os.path.join(SITE, "*.html"))):
        page = os.path.basename(path)
        text = open(path, encoding="utf-8").read()
        if '<footer>' not in text:
            continue  # an app page: no shared chrome, out of scope
        new_text, n = process(text)
        if n == 0:
            print(f"  {page:20s} already done")
            continue
        total += n
        verb = "inserted" if apply else "would insert"
        print(f"  {page:20s} {verb} {n}")
        if apply and new_text != text:
            open(path, "w", encoding="utf-8").write(new_text)
    print(f"\n  {total} insertion(s) {'made' if apply else 'pending'} "
          f"across shared-chrome pages")
    if not apply and total:
        print("  run again with --apply to write changes")


if __name__ == "__main__":
    main()
