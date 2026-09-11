"""Development history on a published page.

HANDOFF section 4: the page states what the thing IS. What it used to be goes
into a comment beside the code, where a maintainer sees it and a reader does
not.

Section 7 carried this as an ad-hoc grep with five phrases:

    (an earlier version|used to be|this used to|had been|what this replaced)

Measured against the site on 2026-09-11, that list caught ONE of the five
passages actually present - longevity's "an earlier version of this page". It
missed climate-cost's "This figure replaced an earlier animation", both of
skyline's ("Until 4 September 2026 this section described a different
rendering", "until 4 September 2026 it was the wrong one ... is now voiced")
and longevity's "Until 4 September 2026 every one of those was labeled wild
... They are now carried". A gate that sees one instance in five is green
because the rule is broken (section 8, trap 31), so the vocabulary below is
the union of what those five passages actually say, and
tests/fixtures/retro.html pins every one of them.

Scripts, styles and HTML comments are stripped first: the app pages inline
megabytes of JSON, and a comment explaining a rule is history beside the code,
which is where it belongs.

Run:  python3 tests/test_retro.py
      python3 tests/test_retro.py --break   # plants a passage; must exit 1
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..", "site")
FIXTURE = os.path.join(HERE, "fixtures", "retro.html")

PATTERNS = {
    "an earlier version": r"\ban earlier (version|animation|rendering|build|draft)\b",
    "used to be":         r"\b(used to be|this used to|what this replaced|had been)\b",
    "until <date>":       r"\buntil \d{1,2} \w+ 20\d\d\b",
    "was replaced":       r"\breplaced an earlier\b|\bthat rendering was retired\b|\bwas retired before\b",
    "was wrong":          r"\bit was the wrong one\b",
    "now X instead":      r"\b(is|are) now (carried|voiced|drawn|counted|pinned|labelled|labeled)\b",
}


def strip(t):
    t = re.sub(r"<script.*?</script>", "", t, flags=re.S | re.I)
    t = re.sub(r"<style.*?</style>", "", t, flags=re.S | re.I)
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    return t


def hits(text):
    out = []
    for name, pat in PATTERNS.items():
        for m in re.finditer(pat, text, flags=re.I):
            out.append((name, m.group(0),
                        text[max(0, m.start() - 60):m.end() + 60].replace("\n", " ")))
    return out


def main(argv):
    broke = "--break" in argv
    fx = hits(strip(open(FIXTURE, encoding="utf-8").read()))
    fired = {k for k, _, _ in fx}
    missing = sorted(set(PATTERNS) - fired)
    if missing:
        print("  FAIL  fixture: %d of %d patterns fired; silent: %s"
              % (len(fired), len(PATTERNS), ", ".join(missing)))
        return 1
    print("  ok    fixture: all %d patterns fire on tests/fixtures/retro.html "
          "(%d hits, comments and scripts stripped)" % (len(PATTERNS), len(fx)))

    pages = sorted(glob.glob(os.path.join(SITE, "*.html")))
    found = []
    for p in pages:
        t = strip(open(p, encoding="utf-8").read())
        if broke:
            t += "\n<p>An earlier version of this page said something else.</p>\n"
        for name, text, ctx in hits(t):
            found.append((os.path.basename(p), name, text, ctx))
    for f, name, text, ctx in found:
        print("  FAIL  %-22s %-18s %r" % (f, name, text))
        print("        ...%s..." % re.sub(r"<[^>]+>", "", ctx).strip())
    # Matches, not passages: one passage can trip several patterns, which is
    # what "until 4 September 2026 it was the wrong one" does.
    print("\n  %d match(es) on %d page(s), across %d pages searched%s"
          % (len(found), len({f for f, _, _, _ in found}), len(pages),
             "   [--break planted one on every page]" if broke else ""))
    if broke and len(found) < len(pages):
        print("  FAIL  the planted passage was not caught on every page")
        return 1
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
