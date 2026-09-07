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

Report by default, --apply to rewrite:

    python3 sync_img_dims.py
    python3 sync_img_dims.py --apply
"""
import glob
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")

IMG = re.compile(r"<img\b[^>]*>", re.I)
SRC = re.compile(r'src="([^"]+)"', re.I)
W = re.compile(r'\bwidth="(\d+)"', re.I)
H = re.compile(r'\bheight="(\d+)"', re.I)


def real_size(page_dir, src):
    """Resolve one src against the page and measure the file itself."""
    path = os.path.normpath(os.path.join(page_dir, src.split("?", 1)[0]))
    if not os.path.exists(path):
        return None
    with Image.open(path) as im:      # Pillow, so webp and png alike
        return im.size


def main():
    apply = "--apply" in sys.argv
    wrong = fixed = checked = 0

    for page in sorted(glob.glob(os.path.join(SITE, "*.html"))):
        text = open(page, encoding="utf-8", newline="").read()
        out, last = [], 0

        for m in IMG.finditer(text):
            tag = m.group(0)
            s, w, h = SRC.search(tag), W.search(tag), H.search(tag)
            if not (s and w and h):
                continue                     # nothing claimed, nothing to check
            size = real_size(os.path.dirname(page), s.group(1))
            if size is None:
                print(f"  missing file: {s.group(1)} in {os.path.basename(page)}")
                continue
            checked += 1
            if size == (int(w.group(1)), int(h.group(1))):
                continue
            wrong += 1
            print(f"  {os.path.basename(page)}: {s.group(1).split('?')[0]} "
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

    print(f"{checked} sized <img> checked, {wrong} disagreed with the file"
          + (f", {fixed} rewritten" if apply else ""))
    return 1 if (wrong and not apply) else 0


if __name__ == "__main__":
    sys.exit(main())
