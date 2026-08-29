"""
Markdown that never became HTML.

Pages on this site are written by hand and by generators, and a run of
markdown pasted into an HTML file renders as literal asterisks and
backticks rather than as emphasis. It is invisible to a link checker, it
looks like a typo to a reader, and it shipped: a summary row reading
"**Total**  **86,622**" sat on the model page.

Scripts and styles are stripped before matching, because ** is
exponentiation in JavaScript and backticks are template literals.

Run:  python3 tests/test_markup.py
"""
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..", "site")

PATTERNS = {
    "bold **":   r"\*\*[^*\n]+\*\*",
    "code ``":   r"`[^`\n]+`",
    "heading #": r"^#{1,6}\s+\S",
    "link []()": r"\[[^\]\n]+\]\([^)\n]+\)",
}


def main():
    hits = []
    for path in sorted(glob.glob(os.path.join(SITE, "*.html"))):
        t = open(path, encoding="utf-8").read()
        t = re.sub(r"<script.*?</script>", "", t, flags=re.S)
        t = re.sub(r"<style.*?</style>", "", t, flags=re.S)
        t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
        for name, pat in PATTERNS.items():
            for m in re.finditer(pat, t, flags=re.M):
                hits.append((os.path.basename(path), name,
                             m.group(0)[:70].replace("\n", " ")))
    for f, kind, text in hits:
        print(f"  FAIL  {f:22s} {kind:10s} {text!r}")
    print(f"\n  {len(hits)} unrendered-markdown hit(s) "
          f"across {len(glob.glob(os.path.join(SITE, '*.html')))} pages")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
