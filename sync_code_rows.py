"""Keep code.html's file counts and archive sizes honest.

    python3 sync_code_rows.py            # report what disagrees
    python3 sync_code_rows.py --apply    # patch the rows

Every row of code.html's archive table states a file count and a download size.
Both were typed, and both drift the moment an archive is rebuilt - which
happens whenever any project's sources change, by a person who is thinking
about that project and not about this table. HANDOFF section 11 has listed
these rows under "typed, and therefore able to go stale" since it was written,
and on 2026-09-07 nine of sixteen rows disagreed with the zips on disk:

    longevity-code.zip   said 11 files,  96 KB   actually 21 files, 811 KB
    neuron-code.zip      said 19 files            actually 26 files
    heat, storage, skyline, continents, food, economy, atlas   all short

The longevity row was out by 8.5x on a number a reader uses to decide whether
to download. That is a section 4 problem - every number on the site traces to
something - not a cosmetic one.

WHAT THIS READS, AND WHY THAT MATTERS. It reads `site/downloads/*.zip` from
the working tree. Those archives are GITIGNORED: they are build output, not
source, so they exist only where someone has run rezip_downloads.py. code.html
itself IS tracked. So this generator's output depends on local build state in a
way most of the others do not, and tests/test_generators.py compares what it
writes against the shipped page - which means the check is only meaningful on a
tree whose archives are current. On a fresh clone with no archives it reports
every row as missing rather than silently rewriting them to nothing; that is
deliberate, and it is why `missing` is a hard error rather than a skip.
(HANDOFF section 8, trap 24: a measurement inherits every default you did not
set. "Which machine built the zips" is one of those defaults.)

Sizes are formatted the way the rows already format them: whole KB below a
megabyte, one decimal above.
"""
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "site", "code.html")
DOWNLOADS = os.path.join(HERE, "site", "downloads")

ROW = re.compile(r"<tr>(?:(?!</tr>).)*?</tr>", re.S)
ZIP = re.compile(r'href="downloads/([\w.\-]+\.zip)"')
FILES = re.compile(r"(<td>)(\d+)(\s*files?</td>)")
SIZE = re.compile(r'(<a href="downloads/[\w.\-]+\.zip">)([^<]*)(</a>)')


def human(nbytes):
    """The rows' own convention: whole KB under a megabyte, one decimal over."""
    kb = nbytes / 1024.0
    return "%.0f KB" % kb if kb < 1024 else "%.1f MB" % (kb / 1024.0)


def main(apply=False):
    text = open(PAGE, encoding="utf-8").read()
    out, changed, missing = [], [], []
    pos = 0

    for m in ROW.finditer(text):
        row = m.group(0)
        z = ZIP.search(row)
        if not z:
            continue
        path = os.path.join(DOWNLOADS, z.group(1))
        if not os.path.exists(path):
            missing.append(z.group(1))
            continue

        with zipfile.ZipFile(path) as zf:
            n = len(zf.namelist())
        size = human(os.path.getsize(path))

        new = FILES.sub(lambda k: k.group(1) + str(n) + k.group(3), row, count=1)
        new = SIZE.sub(lambda k: k.group(1) + size + k.group(3), new, count=1)

        if new != row:
            said_n = FILES.search(row)
            said_s = SIZE.search(row)
            changed.append((z.group(1),
                            said_n.group(2) if said_n else "?", n,
                            said_s.group(2) if said_s else "?", size))
            out.append(text[pos:m.start()])
            out.append(new)
            pos = m.end()

    out.append(text[pos:])
    new_text = "".join(out)

    for name, on, nn, os_, ns in changed:
        print("  %-24s %s -> %s files, %s -> %s" % (name, on, nn, os_, ns))
    if missing:
        # Loud, not silent: an absent archive means the tree has not been built,
        # and rewriting the rows from nothing would be worse than saying so.
        print("\n  %d archive(s) named by code.html are not on disk: %s"
              % (len(missing), ", ".join(missing)))
        print("  run rezip_downloads.py first; nothing written.")
        return 1

    if not changed:
        print("  code.html: %d archive rows, all agree with the zips" % len(ROW.findall(text)))
        return 0

    if apply:
        # newline="\n": site/.gitattributes declares eol=lf and Python's text
        # mode on Windows writes CRLF (HANDOFF section 8, trap 24's neighbours).
        with open(PAGE, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new_text)
        print("\n  %d row(s) rewritten" % len(changed))
    else:
        print("\n  %d row(s) would change. Re-run with --apply." % len(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
