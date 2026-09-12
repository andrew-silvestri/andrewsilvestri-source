"""
Keep every <img width=...> honest.

The width and height attributes on an <img> exist so the browser can reserve
the right box before the image arrives, which is what stops the page shifting
under a reader mid-scroll. That only works while the numbers agree with the
file. They drift silently: a figure gets regenerated at a new size, the markup
keeps the old one, and the reserved box is now the wrong shape - which is
worse than no attribute at all, because the layout shifts *and* the image is
scaled to the wrong aspect on the way there.

This happened during the 2026-08-30 design pass: atlas_layers.png,
climate_chain_tomato.png, energy_model_throughlines.png and
storage_fig3_duration_value.png were all regenerated after their attributes
were written, and four pages went out of step within the same session.

Nothing else checks this. bust_cache.py rewrites the ?v= stamp on the same
tags and never looks at the dimensions; sync_assets.py checks which assets are
referenced, not how. So this is its own pass.

A <picture> is checked the same way, and the shape of a multi-size figure is
not a free choice. The rule, fixed before anything uses it:

    <picture>, ONE BARE SINGLE-PATH srcset per <source> - no descriptor, no
    comma list - plus width and height on the <source> itself.

Both halves were measured into throw-away copies on 2026-09-11 rather than
reasoned about, and both have a separate reason.

A DESCRIPTOR SRCSET LOSES ITS FILES. sync_assets.py's referenced() finds a
srcset only through the second alternative of its pattern, which matches a
quoted path beginning "assets/" and nothing else. Given

    srcset="assets/x-350.png 350w, assets/x-714.png 714w"

the report listed BOTH files as orphans and --apply said "copied 0, removed 3":
it deleted two live figures. bust_cache.py's rewrite wants srcset="<one exact
path>" as well, and against the same markup printed "stamped 0 pages" - the
figure ships unstamped and trap 3 comes back silently. continents/
update_page.py:207 stamps the same shape and has the same limit.

That is sync_assets.py's font lesson with a different noun. There, --apply
deleted a live font because referenced() could not see an @font-face url();
here it deletes a live figure because referenced() cannot see a descriptor.
Same instrument, same blind spot, same fix: do not write markup the pruner
cannot read.

WIDTH AND HEIGHT ON THE <source>, OR THE PAGE JUMPS. The <img> attributes are
what reserves the box, and they describe the DESKTOP file. On continents.html
at 390 the browser serves a 700x1750 phone render behind an <img> claiming
1428x1020, reserves 350x250 and then reflows to 350x872: a 621.4px shift in
Chromium and 622.0px in Firefox, measured by holding the PNG on the wire and
reading the box either side of release. With width and height on the <source>
the same probe reports 0.0px and -3.0px.

WHAT THIS DOES NOT ASSERT. It says nothing about a descriptor srcset beyond
refusing it: it does not resolve one, does not measure the files in one, and
cannot say which a browser would pick. It does not check that a <source>'s
media query matches the width its figure was authored for, does not read
`sizes`, and measures nothing at render time - correct attributes here are a
correct RESERVATION, not a promise that nothing on the page moves. The 621px
shift above sat on a published page through a full defect sweep because
nothing on this site measures what moves AFTER paint; this script does not
measure it either. That is its own class of defect and its own check.

Report by default, --apply to rewrite:

    python3 sync_img_dims.py
    python3 sync_img_dims.py --apply
    python3 sync_img_dims.py --break dims        # 0 caught, non-zero blind
    python3 sync_img_dims.py --break descriptor  # 0 caught, non-zero blind

--break runs the checks against tests/fixtures/imgdims.html instead of site/
and exits non-zero if the fault it names goes unreported. A check nobody has
seen fail is a claim (trap 17); a --break that prints its verdict instead of
asserting on it is decoration (trap 26); and the exit status is the thing to
read, not the output (trap 34). Both modes have been run against a
deliberately blinded checker and both came back non-zero - see the commit.
"""
import glob
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")

IMG = re.compile(r"<img\b[^>]*>", re.I)
SOURCE = re.compile(r"<source\b[^>]*>", re.I)
SRC = re.compile(r'src="([^"]+)"', re.I)
SRCSET = re.compile(r'srcset="([^"]+)"', re.I)
# A bare single path: no comma and no whitespace, so a descriptor or a comma
# list cannot pass. The docstring says what breaks when one does.
BARE = re.compile(r"^[^\s,]+$")
W = re.compile(r'\bwidth="(\d+)"', re.I)
H = re.compile(r'\bheight="(\d+)"', re.I)


def real_size(page_dir, src):
    """Resolve one src against the page and measure the file itself."""
    path = os.path.normpath(os.path.join(page_dir, src.split("?", 1)[0]))
    if not os.path.exists(path):
        return None
    with Image.open(path) as im:      # Pillow, so webp and png alike
        return im.size


def check(pages, apply):
    """Walk the given pages. Returns (checked, wrong, fixed, refused).

    `refused` counts <source> tags whose srcset is not a bare single path.
    Those are never resolved and never rewritten - the docstring says what
    sync_assets.py --apply and bust_cache.py do with one - so they are
    reported and they fail the run whether or not --apply was passed. A shape
    this script refuses is not something --apply can repair.
    """
    checked = wrong = fixed = refused = 0
    for page in pages:
        text = open(page, encoding="utf-8", newline="").read()
        out, last = [], 0
        name = os.path.basename(page)

        # One pass over both tag kinds, in document order, so the rewrite
        # below can splice by offset without two passes disagreeing about
        # what is where.
        tags = sorted([(m, "img") for m in IMG.finditer(text)]
                      + [(m, "source") for m in SOURCE.finditer(text)],
                      key=lambda p: p[0].start())

        for m, kind in tags:
            tag = m.group(0)
            w, h = W.search(tag), H.search(tag)
            if kind == "img":
                s = SRC.search(tag)
                ref = s.group(1) if s else None
            else:
                s = SRCSET.search(tag)
                if not s:
                    continue                 # a <source type=> with no srcset
                ref = s.group(1)
                if not BARE.match(ref):
                    refused += 1
                    print(f"  {name}: <source> srcset is not a bare single "
                          f"path: {ref[:60]!r} - sync_assets.py --apply deletes "
                          f"what it cannot resolve and bust_cache.py cannot "
                          f"stamp it")
                    continue
            if not (ref and w and h):
                continue                     # nothing claimed, nothing to check
            size = real_size(os.path.dirname(page), ref)
            if size is None:
                print(f"  missing file: {ref} in {name}")
                continue
            checked += 1
            if size == (int(w.group(1)), int(h.group(1))):
                continue
            wrong += 1
            print(f"  {name}: <{kind}> {ref.split('?')[0]} "
                  f"says {w.group(1)}x{h.group(1)}, file is "
                  f"{size[0]}x{size[1]}")
            if apply:
                new = W.sub(f'width="{size[0]}"', tag)
                new = H.sub(f'height="{size[1]}"', new)
                out.append(text[last:m.start()])
                out.append(new)
                last = m.end()
                fixed += 1

        if apply and out:
            out.append(text[last:])
            # newline="\n", not "". Both leave today's bytes alone, but ""
            # preserves whatever the tree happens to hold - so when bust_cache.py
            # flipped the pages to CRLF, this followed it and agreed, which is the
            # masking that hides the bug rather than the bug itself.
            open(page, "w", encoding="utf-8", newline="\n").write("".join(out))
    return checked, wrong, fixed, refused


def broken(mode):
    """Run the checks against the fixture and fail if the fault goes unseen.

    The fixture is never in site/: a control page that shipped would be a
    published page nobody meant to publish (tests/test_layout.js says the same
    thing about its own).

    THE EXIT STATUS IS THE VERDICT, and it points the way beauty/break_model.py
    points it: 0 when the fixture's fault was reported, non-zero when it was
    not. The first version of this returned 1 either way, on a reading of trap
    26 that "the break run has to FAIL" meant this process must exit non-zero.
    It does not: what has to fail is the check when the thing it guards is
    broken. A break mode that exits 1 whatever it saw is the same defect trap
    26 names - a status nobody can read a result out of - with the constant
    moved from 0 to 1.
    """
    fx = os.path.join(HERE, "tests", "fixtures", "imgdims.html")
    if not os.path.exists(fx):
        print(f"  --break: fixture missing: {fx}")
        return 1
    checked, wrong, fixed, refused = check([fx], apply=False)
    seen = {"dims": wrong, "descriptor": refused}[mode]
    want = {"dims": "a <source> whose width/height disagree with its file",
            "descriptor": "a <source> carrying a comma/descriptor srcset"}[mode]
    print(f"  --break {mode}: {want} -> reported {seen} time(s)")
    if seen == 0:
        print(f"  --break {mode} BLIND: the fixture carries the fault and "
              f"nothing reported it")
        return 1
    print(f"  --break {mode}: caught; the check sees it")
    return 0


def main():
    if "--break" in sys.argv:
        i = sys.argv.index("--break")
        mode = sys.argv[i + 1] if i + 1 < len(sys.argv) else ""
        if mode not in ("dims", "descriptor"):
            print("  --break takes: dims | descriptor")
            return 1
        return broken(mode)

    apply = "--apply" in sys.argv
    pages = sorted(glob.glob(os.path.join(SITE, "*.html")))
    checked, wrong, fixed, refused = check(pages, apply)
    print(f"{checked} sized <img>/<source> checked, {wrong} disagreed with "
          f"the file" + (f", {fixed} rewritten" if apply else "")
          + (f"; {refused} <source> refused for srcset shape" if refused else ""))
    return 1 if (refused or (wrong and not apply)) else 0


if __name__ == "__main__":
    sys.exit(main())
