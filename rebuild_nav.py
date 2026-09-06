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

import argparse
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")

# (label, href) - a group is (label, [(label, href), ...])
# Regrouped 2026-09-05 from four groups (The atlas / Energy / Others) into
# three. "Others" had grown to seven pages of unrelated work and said nothing
# about any of them.
#
# The atlas lost its own top-level group and folds in here as the first four
# entries. It is still the main project and does not need the nav to say so:
# index.html opens with its hero, tagged "Main project", above every section.
#
# Every label here is the page's own title. A nav that renames a page gives
# the site two names for one thing, and index.html's headings are this same
# taxonomy in a second place - if the two disagree the site has two
# structures. Changing a label means changing the page.
NAV = [
    ("Home", "index.html"),
    ("Energy", [
        ("Open the atlas", "atlas-app.html"),
        ("About the atlas", "atlas.html"),
        ("How the model works", "model.html"),
        ("Figures", "library.html"),
        ("Industrial heat break-even", "heat.html"),
        ("Battery revenue simulator", "storage.html"),
    ]),
    ("Running", [
        ("What a fast shoe is worth", "shoes.html"),
        ("Economy is not time", "economy.html"),
    ]),
    ("Misc", [
        # Was its own one-item "Climate research" group until the 2026-08-30
        # revamp (SITE_REVAMP_2026-08-30.md, "Navigation grouping"); the label
        # here was "Climate cost calculator" until 2026-09-05, which matched
        # neither the page nor its index entry.
        ("The true climate cost", "climate-cost.html"),
        ("Fat, sugar, salt", "food.html"),
        ("Where the ground goes", "continents.html"),
        ("Longevity quotient", "longevity.html"),
        ("Skylines, played", "skyline.html"),
        # Parked here rather than in a "Mind" group of its own. A group holding
        # one page is rendered by nav_for() as a bare link to that page, with
        # the category name dropped entirely, so a one-item Mind would have put
        # "Mind" on index.html and nothing of the kind in the nav. When the
        # beauty project lands, the two of them make Mind and this line moves.
        ("The measured neuron", "neuron.html"),
        # "The bookshelf" (desktop.html) retired to unpublished/ on 2026-09-05
        # (PHASE5); the pages were regenerated from this list the same day.
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


def main(dry_run=False):
    """--dry-run reports what would change and writes nothing.

    Added 2026-09-05, when NAV was regrouped into four categories. Section 8
    item 11 of HANDOFF: this list and the shipped nav disagreed for five weeks
    once, so running the generator would have silently reverted a deliberate
    change. The defence is to read the diff before the write, and that needs a
    mode that does not write."""
    n = 0
    for path in sorted(glob.glob(os.path.join(SITE, "*.html"))):
        page = os.path.basename(path)
        t = open(path, encoding="utf-8").read()
        if '<nav class="top">' not in t:
            continue
        new = re.sub(r'<nav class="top">.*?</nav>', lambda m: nav_for(page),
                     t, count=1, flags=re.S)
        changed = new != t
        if changed and not dry_run:
            open(path, "w", encoding="utf-8").write(new)
        n += changed
        state = ("would change" if dry_run else "updated") if changed else "unchanged"
        print(f"  {page:24s} {state}")
    verb = "would be rewritten" if dry_run else "rewritten"
    print(f"\n  {n} page(s) {verb}")
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change; write nothing")
    main(ap.parse_args().dry_run)
