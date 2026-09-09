"""
Rebuild the top navigation on every page.

The navigation lives in one place here rather than in the sixteen pages that
carry it, so adding a page is one line and cannot drift between pages. (It said
"seventeen files" until 2026-09-08; --dry-run reports sixteen. atlas-app.html
and the other four full-screen apps have no nav.top and are not rewritten.)

THE BAR'S SHAPE HAS BEEN ARGUED BOTH WAYS AND BOTH ARGUMENTS BELONG HERE.
This docstring used to open by saying the old bar "put Figures, How it works and
the atlas beside Home as three loose links, which read as three unrelated
destinations", that they are instead "three views of the same world energy model
- the thing itself, its method, and its output", and that grouping them
"shortens the bar from six items to four". The grouping argument was right about
what those pages ARE and wrong about what the bar SAYS; it was reversed on
2026-09-08 and the reason is above NAV. The count had been false for longer than
that: the bar was five items plus About before this change and is six plus About
after it.

THE COUNT MOVED AGAIN ON 2026-09-09 AND THE SENTENCE ABOVE IS KEPT RATHER THAN
SWAPPED OUT. "Six plus About" was true from 2026-09-08 until then. The bar is
now EIGHT plus About - Home / Atlas / Energy / Climate / Running / Mind / Misc /
Code, and About pinned right, nine flex children. Climate and Mind were added as
one-item groups, which was impossible until the length-1 collapse came out of
nav_for() the same day; the reversal is recorded there.
"""

import argparse
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")

# (label, href) - a group is (label, [(label, href), ...])
#
# THE ATLAS HAS ITS OWN TOP-LEVEL GROUP AGAIN, AND ANDREW'S REASON IS THE PART
# THAT WILL OTHERWISE BE TIDIED AWAY. In his words: carved out EVEN THOUGH it is
# about energy - that is the point. It is not a peer of heat and storage, it is
# the main project, and grouping it with them made it look like one of several.
#
# WHAT THIS REPLACES, STATED RATHER THAN DELETED (trap 15). The list was
# regrouped on 2026-09-05 from four groups (The atlas / Energy / Others) into
# three: "Others" had grown to seven pages of unrelated work and said nothing
# about any of them, and the atlas lost the group it had held until then and
# folded into Energy as its first four entries. The justification written here
# for that was, word for word:
#
#     "It is still the main project and does not need the nav to say so:
#      index.html opens with its hero, tagged 'Main project', above every
#      section."
#
# THAT CARD WAS DELETED ON 2026-09-06, when the home page became the hero and
# the index. The justification outlived it by two publishes, sitting here
# describing a page that no longer existed - which is trap 11 in the one file
# trap 11 was first written about. So the nav became the only thing on the site
# saying where the atlas belonged, and what it said was "one of six energy
# pages". The fix is not a better sentence in this comment; it is the carve-out.
#
# Energy keeps heat and storage, and stays a dropdown: nav_for() collapses a
# group to a bare link only at length 1.
#
# Atlas sits directly after Home because index.html's h2s are this same taxonomy
# in a second place, and its Atlas section is first there too.
#
# Every LEAF label here is the page's own title. A nav that renames a page gives
# the site two names for one thing, and if index.html's headings and this list
# disagree the site has two structures. Changing a leaf label means changing the
# page.
#
# GROUP LABELS ARE NOT PAGES, so that rule does not bind them. "Atlas",
# "Energy", "Climate", "Running", "Mind" and "Misc" name no page and are free.
# ("Climate" and "Mind" joined this list on 2026-09-09; it named four labels
# until then.) Nobody needed the distinction until a group label existed that
# was one word off a page title, and the rule above reads as though it covers
# every string in this list.
#
# ONE DELIBERATE INCONSISTENCY, RECORDED SO IT IS NOT CORRECTED BACK:
# index.html's entry for the atlas is titled "The atlas", not this list's leaf
# label "About the atlas". Every other index h3 copies its leaf label exactly.
# Under an <h2>Atlas</h2> the word "About" is noise, and "The atlas" is
# atlas.html's own <title> stem. The leaf label is NOT changed to match, because
# that would change the page title - one of the eighteen strings the rename
# cancelled on 2026-09-08 was not going to touch.
NAV = [
    ("Home", "index.html"),
    ("Atlas", [
        ("Open the atlas", "atlas-app.html"),
        ("About the atlas", "atlas.html"),
        ("How the model works", "model.html"),
        ("Figures", "library.html"),
    ]),
    ("Energy", [
        ("Industrial heat break-even", "heat.html"),
        ("Battery revenue simulator", "storage.html"),
    ]),
    # CLIMATE IS ONE PAGE AND RENDERS AS A DROPDOWN. That is the point of the
    # 2026-09-09 change, not an oversight - do not "simplify" it back to a bare
    # link, which is what nav_for() used to do and why the branch below it is
    # gone. Andrew's decision, and the part worth keeping: Climate is the
    # ARTICLE, climate-cost.html, not the calculator app.
    #
    # This is the second time climate-cost has had a group of its own. This
    # comment sat on the line in Misc until today and is moved with it rather
    # than dropped: it was its own one-item "Climate research" group until the
    # 2026-08-30 revamp (SITE_REVAMP_2026-08-30.md, "Navigation grouping"); the
    # label here was "Climate cost calculator" until 2026-09-05, which matched
    # neither the page nor its index entry.
    #
    # Between Energy and Running because Andrew placed it there.
    ("Climate", [
        ("The true climate cost", "climate-cost.html"),
    ]),
    ("Running", [
        ("What a fast shoe is worth", "shoes.html"),
        ("Economy is not time", "economy.html"),
    ]),
    # MIND EXISTS AS OF 2026-09-09, WITH ONE PAGE, AND ONLY BECAUSE THE LENGTH-1
    # COLLAPSE CAME OUT OF nav_for() THE SAME DAY. What stood on the neuron line
    # in Misc until today, word for word, because it was a promise and it is
    # being departed from rather than found wrong (trap 15):
    #
    #     "Parked here rather than in a "Mind" group of its own. A group holding
    #      one page is rendered by nav_for() as a bare link to that page, with
    #      the category name dropped entirely, so a one-item Mind would have put
    #      "Mind" on index.html and nothing of the kind in the nav. When the
    #      beauty project lands, the two of them make Mind and this line moves."
    #
    # The condition it waited for was the collapse, and the collapse is gone, so
    # Mind is created now with neuron alone. BEAUTY JOINS IT AS A SECOND LEAF
    # when it lands, and costs the bar nothing: it goes inside a menu that
    # already exists.
    #
    # Placed between Running and Misc. Andrew specified only that Climate sits
    # between Energy and Running; this position was proposed and kept, and it is
    # one line to move. It reads in the right direction as the site grows - Mind
    # is the group that gains a page, Misc only loses them.
    ("Mind", [
        # Beauty landed 2026-09-09. The leaf label is the page's own title,
        # not the folder name and not the old thesis: the project was built
        # to show "studied, not endangered" and the fits reversed it.
        ("Endangered, and studied", "beauty.html"),
        # WHY MIND EXISTS AND WHAT NOW HOLDS IT ARE NO LONGER THE SAME PAGE.
        # Historically true: this group was created earlier on 2026-09-09
        # (cdc7535) to take neuron.html out of Misc, and the line it replaced
        # had promised since 2026-09-06 that "when the beauty project lands,
        # the two of them make Mind". Both halves happened, in that order,
        # within one day.
        #
        # Presently true: neuron.html was unpublished 2026-09-09 at Andrew's
        # request, for now (unpublished/RETIRED.md), so Mind holds beauty
        # alone. The group is kept rather than collapsed back into Misc,
        # because it was not created for neuron's sake and the reason it was
        # created has not gone away.
        #
        # A one-item group renders as a DROPDOWN and that is deliberate: the
        # length-1 collapse came out of nav_for() the same day (cdc7535), and
        # Climate has rendered this way since. Do not "simplify" it to a bare
        # link - that branch was removed on purpose and its argument is quoted
        # where it stood.
    ]),
    ("Misc", [
        ("Where the ground goes", "continents.html"),
        ("Longevity quotient", "longevity.html"),
        ("Skylines, played", "skyline.html"),
        # "The bookshelf" (desktop.html) retired to unpublished/ on 2026-09-05
        # (PHASE5); the pages were regenerated from this list the same day.
        #
        # THREE, and this group lost pages twice on 2026-09-09. It held six
        # that morning. First climate-cost went to Climate and neuron to Mind
        # (cdc7535), leaving four - which is what the comment here said, and
        # it was true for a few hours. Then food.html was unpublished at
        # Andrew's request, for now (unpublished/RETIRED.md), leaving three.
        # The count is recorded twice on purpose: a number in a comment is a
        # claim about the list beside it, and this one was overtaken the same
        # day it was written.
        #
        # Still a dropdown, and still a group that says nothing about any of
        # its members - the sort that question belongs to has not been done,
        # and neither of today's changes did it.
    ]),
    ("Code", "code.html"),
    # LAST, AND IT HAS TO STAY LAST. style.css pins this one right with
    # margin-left:auto on a flex item, which eats the free space BEFORE it -
    # so anything appended after this line would sit right of About and the
    # bar would read as having two right-hand items. Add new entries above
    # "Code", not below this.
    ("About", "about.html"),
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
        # THE LENGTH-1 COLLAPSE WAS REMOVED ON 2026-09-09, AND ITS REASON WAS
        # OVERRULED RATHER THAN FOUND WRONG. What stood here, word for word:
        #
        #     "A dropdown holding one page is a menu with nothing to choose, so
        #      the group becomes a direct link to its only child. This keeps the
        #      bar short, and on a phone it removes a tap."
        #
        #     if len(target) == 1:
        #         only_l, only_h = target[0]
        #         on = ' class="on"' if only_h == page else ""
        #         # the child's own name, not the category: the link goes to one
        #         # page and should say which
        #         out.append(f'<a href="{only_h}"{on}>{only_l}</a>')
        #         continue
        #
        # Both sentences are still true. Andrew's decision is that a one-item
        # group renders as a dropdown anyway, because the bar has to say
        # "Climate" and "Mind". With this branch in place a one-item Climate put
        # "Climate" on index.html and NOTHING of the kind in the nav - the bar
        # read "The true climate cost", the leaf's name, and the category the
        # taxonomy exists to state was the one thing missing from it.
        #
        # WHAT IT COSTS, AND IT IS THE SENTENCE BEING OVERRULED: below 620px the
        # dropdowns open on tap through .dd:focus-within (style.css:800), so a
        # one-item group is now TWO TAPS TO REACH ONE PAGE where a bare link was
        # one. Accepted as the price, not overlooked.
        #
        # Removing it was inert for every group that existed that day - Atlas 4,
        # Energy 2, Running 2, Misc 6, with Home, Code and About bare strings
        # taking the isinstance(target, str) branch above. Counted before the
        # removal, not assumed.
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
            # newline="\n" IS LOAD-BEARING AND THIS FILE WAS MISSED IN THE 2026-09-06
            # SWEEP. Python's text mode on Windows translates "\n" to "\r\n", so
            # this line rewrote all sixteen pages to CRLF against a tree
            # .gitattributes declares as LF. Every page generator that writes
            # LF then differs from the shipped file on every line, and
            # tests/test_generators.py reports EIGHT drifts that are pure line
            # endings - the identical failure .gitattributes records for
            # 2026-09-06, and the one it records for bust_cache.py on
            # 2026-09-07. Found 2026-09-09, the same way: by running the check
            # after a nav change and reading the diff instead of the count.
            open(path, "w", encoding="utf-8", newline="\n").write(new)
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
