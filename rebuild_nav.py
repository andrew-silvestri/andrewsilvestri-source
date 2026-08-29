"""
Rebuild the top navigation on every page.

The old bar put Figures, How it works and the atlas beside Home as three loose
links, which read as three unrelated destinations. They are not: they are three
views of the same world energy model - the thing itself, its method, and its
output. Grouping them under one heading says so, and shortens the bar from six
items to four.

The navigation lives in one place here rather than in seventeen files, so
adding a page is one line and cannot drift between pages.
"""

import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")

# (label, href) - a group is (label, [(label, href), ...])
NAV = [
    ("Home", "index.html"),
    ("The atlas", [
        ("Open the atlas", "atlas-app.html"),
        ("About the atlas", "atlas.html"),
        ("How the model works", "model.html"),
        ("Figures", "library.html"),
    ]),
    ("Energy", [
        ("Industrial heat break-even", "heat.html"),
        ("Battery revenue simulator", "storage.html"),
    ]),
    ("Climate research", [
        ("Climate cost calculator", "climate-cost.html"),
    ]),
    ("Others", [
        ("Longevity quotient", "longevity.html"),
        ("Skylines, played", "skyline.html"),
        ("The bookshelf", "desktop.html"),
    ]),
    ("Code", "code.html"),
]

BACK = '<a href="#" class="back" id="backlink">&larr; back</a>'


def nav_for(page):
    """The bar as seen from `page`, with the current location marked. A page
    inside a group marks the group heading too, so you can see where you are
    without opening the menu."""
    # No back link. The browser already has one, it was the only nav item
    # whose destination depended on how you arrived, and on a phone it took
    # a row of its own at the top of every page.
    out = []
    for label, target in NAV:
        if isinstance(target, str):
            on = ' class="on"' if target == page else ""
            out.append(f'<a href="{target}"{on}>{label}</a>')
            continue
        # A dropdown holding one page is a menu with nothing to choose, so
        # the group becomes a direct link to its only child. This keeps the
        # bar short, and on a phone it removes a tap.
        if len(target) == 1:
            only_l, only_h = target[0]
            on = ' class="on"' if only_h == page else ""
            # the child's own name, not the category: the link goes to one
            # page and should say which
            out.append(f'<a href="{only_h}"{on}>{only_l}</a>')
            continue
        here = any(h == page for _, h in target)
        cls = "ddbtn on" if here else "ddbtn"
        # full-screen apps open in their own tab, per the house convention
        items = "".join(
            f'<a href="{h}"' + (' class="on"' if h == page else "")
            + (' target="_blank" rel="noopener"' if h.endswith("-app.html")
               else "")
            + f'>{l}</a>'
            for l, h in target)
        out.append(
            f'<span class="dd"><a href="#" class="{cls}" aria-haspopup="true">'
            f'{label} <span class="caret">&#9662;</span></a>'
            f'<span class="ddmenu">{items}</span></span>')
    return '<nav class="top">' + "".join(out) + "</nav>"


def main():
    n = 0
    for path in sorted(glob.glob(os.path.join(SITE, "*.html"))):
        page = os.path.basename(path)
        t = open(path, encoding="utf-8").read()
        if '<nav class="top">' not in t:
            continue
        new = re.sub(r'<nav class="top">.*?</nav>', lambda m: nav_for(page),
                     t, count=1, flags=re.S)
        if new != t:
            open(path, "w", encoding="utf-8").write(new)
            n += 1
        print(f"  {page:24s} {'updated' if new != t else 'unchanged'}")
    print(f"\n  {n} page(s) rewritten")


if __name__ == "__main__":
    main()
