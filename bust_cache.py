"""
Stamp style.css and the front-page and atlas scripts with a content hash.

A browser that has style.css cached will keep serving the old one after a
deploy, which looks exactly like a change that did not take. The query string
changes whenever the file does, so the browser fetches the new copy and nothing
downstream has to be told about it.

Run after any edit to style.css or the scripts listed below, and before
publishing:

    python3 bust_cache.py
"""

import glob
import hashlib
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
SCRIPTS = ("assets/motion.js",
           "assets/hero.js", "assets/hero-gl.js", "assets/hero-data.js",
           "assets/atlas-app.js", "assets/atlas-data.js")

# Images need this at least as much as the scripts do. A regenerated
# chart keeps the same filename, so a browser holding the old one shows
# figures from a retired model next to text from the current one.
IMAGE_DIRS = ("assets",)


def digest(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()[:8]


def main():
    css = digest(os.path.join(SITE, "style.css"))
    vers = {a: digest(os.path.join(SITE, a)) for a in SCRIPTS
            if os.path.exists(os.path.join(SITE, a))}
    for d in IMAGE_DIRS:
        for img in glob.glob(os.path.join(SITE, d, "*.png")) + \
                   glob.glob(os.path.join(SITE, d, "*.svg")):
            vers[f"{d}/{os.path.basename(img)}"] = digest(img)
    changed = 0
    for p in glob.glob(os.path.join(SITE, "*.html")):
        t = open(p, encoding="utf-8").read()
        o = t
        t = re.sub(r'href="style\.css(\?v=[0-9a-f]+)?"',
                   f'href="style.css?v={css}"', t)
        for a, v in vers.items():
            t = re.sub(r'src="' + re.escape(a) + r'(\?v=[0-9a-f]+)?"',
                       f'src="{a}?v={v}"', t)
        if t != o:
            open(p, "w", encoding="utf-8").write(t)
            changed += 1
    print(f"  stamped {changed} pages (style.css v={css})")


if __name__ == "__main__":
    main()
