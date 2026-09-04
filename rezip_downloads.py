"""
Rebuild heat-code.zip, storage-code.zip, bookshelf-code.zip and
skyline-code.zip from the tracked heat/, storage/, bookshelf/ and skyline/
folders.

figstyle.py and both projects' model.py used to exist only inside
site/downloads/heat-code.zip and storage-code.zip - the sibling source
folders sync_assets.py expected were never created, so a change to either
generator meant editing inside a zip. heat/ and storage/ (unpacked from those
same zips, see SITE_REVAMP_2026-08-30.md) are the source of truth now; the
zips are a build artifact of them, not the other way around. This is what
keeps the two in sync: run it after editing anything under a source folder,
before publishing, so the file someone downloads from the site matches the
code that actually produced its figures.

Entry order is preserved from whatever the zip already contains - appending
new files at the end, dropping ones that no longer exist in the source
folder - specifically so that re-running this against an unmodified source
folder reproduces the original zip's namelist() exactly.

What is never shipped: bytecode caches, node_modules, a folder's outputs/
(the figures and CSVs a model writes when it runs - they are the site's
assets, not its source), package-manager files, and a built page. On
2026-09-04 storage-code.zip shipped __pycache__/ and outputs/ (ten files,
443 KB) because a builder had just been run in storage/ and this script
walked the folder as it stood. The skip list below is now checked against
every archive on every run, and an archive that fails it is not written.

Two sessions running this at once corrupted an archive the same day. A lock
file in site/downloads/ now makes the second run wait its turn or give up,
and each archive is written beside itself and moved into place, so a run
that dies half-way leaves the shipped zip as it was.

Run:
    python3 rezip_downloads.py            # rebuild every archive
    python3 rezip_downloads.py --verify   # rebuild into a temp file and diff
                                          # names and content against what is
                                          # shipped; the shipped zip is not
                                          # touched. Exit 1 on any difference
                                          # or any polluted entry.
"""

import argparse
import os
import sys
import tempfile
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS = os.path.join(HERE, "site", "downloads")
LOCK = os.path.join(DOWNLOADS, ".rezip.lock")
LOCK_WAIT_S = 60          # how long a second run waits for the first
LOCK_STALE_S = 15 * 60    # a lock older than this belongs to a dead run

TARGETS = [
    ("heat", os.path.join(DOWNLOADS, "heat-code.zip")),
    ("storage", os.path.join(DOWNLOADS, "storage-code.zip")),
    # bookshelf/ holds the README and the wallpaper setter; the application
    # itself is the shipped file, pulled in by name so the download can never
    # drift from what the site runs (2026-09-04: it had, by one line).
    ("bookshelf", os.path.join(DOWNLOADS, "bookshelf-code.zip"),
     {"bookshelf-app.html": os.path.join(HERE, "site", "bookshelf-app.html")}),
    # skyline/ was unpacked from its own zip on 2026-09-04 (FIX_SKYLINE): the
    # zip had been the only copy of the generator, and its template had
    # drifted three lines behind site/skyline-app.html.
    ("skyline", os.path.join(DOWNLOADS, "skyline-code.zip")),
]

# Never shipped in a download: package-manager state, bytecode caches, a
# model's own outputs/, and a built page (skyline-app.html is built by
# skyline/build_app.py next to it; the shipped copy is site/skyline-app.html).
SKIP_DIRS = {"node_modules", "__pycache__", "outputs", ".ipynb_checkpoints"}
SKIP_FILES = {"package.json", "package-lock.json", "skyline-app.html",
              ".DS_Store", "Thumbs.db"}
SKIP_SUFFIXES = (".pyc", ".pyo")


def polluted(names):
    """The entries in names that the skip rules say must never ship."""
    bad = []
    for n in names:
        parts = n.rstrip("/").split("/")
        if any(p in SKIP_DIRS for p in parts) or parts[-1] in SKIP_FILES \
                or parts[-1].endswith(SKIP_SUFFIXES):
            bad.append(n)
    return bad


def _all_paths(src_dir):
    """Every path under src_dir, files and directories, as archive-style
    forward-slash relative names - directories carrying the trailing slash
    a zip uses to mark a directory entry."""
    dirs, files = [], []
    for root, ds, fs in os.walk(src_dir):
        ds[:] = sorted(d for d in ds if d not in SKIP_DIRS)
        fs = [f for f in fs if f not in SKIP_FILES and not f.endswith(SKIP_SUFFIXES)]
        rel_root = os.path.relpath(root, src_dir)
        if rel_root != ".":
            dirs.append(rel_root.replace(os.sep, "/") + "/")
        for f in sorted(fs):
            rel = os.path.join(rel_root, f) if rel_root != "." else f
            files.append(rel.replace(os.sep, "/"))
    return dirs, files


def _order(src_dir, zip_path, extras, quiet=False):
    """The entry order for a rebuilt archive: the existing zip's order for
    every name still present, then anything new (directories first, then
    files, each sorted). Names the zip had that the source no longer has are
    dropped with a warning, since silently losing a file out of a shipped
    download is exactly the kind of drift this script exists to prevent -
    unless they are pollution, which is dropped without regret."""
    dirs, files = _all_paths(src_dir)
    all_names = set(dirs) | set(files) | set(extras)
    order = []
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path) as old:
            for name in old.namelist():
                if name in all_names:
                    order.append(name)
                elif not quiet:
                    why = "never shipped" if polluted([name]) else \
                        f"no longer in {os.path.basename(src_dir)}/"
                    print(f"  ! dropping {name!r} from {os.path.basename(zip_path)} - {why}")
    seen = set(order)
    return order + sorted(n for n in all_names if n not in seen)


def _write(order, src_dir, extras, out_path):
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in order:
            if name.endswith("/"):
                z.writestr(zipfile.ZipInfo(name), "")
            else:
                z.write(extras.get(name, os.path.join(src_dir, name)), name)


def rezip(src_dir, zip_path, extras=None):
    """Rebuild zip_path from src_dir (plus extras, mapping an archive name to
    a path outside src_dir - for a download whose main file is the shipped
    file itself). Written beside the target and moved into place, so a
    failure leaves the shipped archive untouched."""
    extras = extras or {}
    order = _order(src_dir, zip_path, extras)
    bad = polluted(order)
    if bad:
        raise SystemExit(f"refusing to write {os.path.basename(zip_path)}: "
                         f"{len(bad)} entries the skip rules forbid: {bad[:4]}")
    tmp = zip_path + ".tmp"
    try:
        _write(order, src_dir, extras, tmp)
        os.replace(tmp, zip_path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return order


def _members(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        return [(i.filename, i.CRC) for i in z.infolist()]


def verify(src_dir, zip_path, extras=None):
    """Build what rezip() would write into a temporary file and compare its
    entry names and content (CRCs) against the shipped archive. The shipped
    archive is read and never written. Returns True when they agree and the
    shipped archive carries nothing the skip rules forbid."""
    extras = extras or {}
    name = os.path.basename(zip_path)
    if not os.path.exists(zip_path):
        print(f"  {name}: MISSING (nothing shipped to verify)")
        return False
    shipped = _members(zip_path)
    bad = polluted([n for n, _ in shipped])
    order = _order(src_dir, zip_path, extras, quiet=True)
    with tempfile.TemporaryDirectory() as tmp:
        fresh = os.path.join(tmp, name)
        _write(order, src_dir, extras, fresh)
        built = _members(fresh)
    ok = shipped == built and not bad
    print(f"  {name}: {'agrees with source' if ok else 'DIFFERS'} "
          f"({len(shipped)} shipped, {len(built)} from source)")
    if bad:
        print(f"    shipped archive carries {len(bad)} forbidden entries: {bad[:6]}")
    if shipped != built:
        s, b = dict(shipped), dict(built)
        for n in sorted(set(s) | set(b)):
            if n not in b:
                print(f"    - {n}  (shipped, not in source)")
            elif n not in s:
                print(f"    + {n}  (in source, not shipped)")
            elif s[n] != b[n]:
                print(f"    ~ {n}  (content differs)")
        if [n for n, _ in shipped] != [n for n, _ in built] and set(s) == set(b):
            print("    (same names, different order)")
    return ok


class Lock:
    """One rezip at a time per downloads folder. Created with O_EXCL so two
    runs cannot both think they hold it; waits LOCK_WAIT_S for a holder to
    finish; removes a lock older than LOCK_STALE_S as left by a dead run."""

    def __enter__(self):
        os.makedirs(DOWNLOADS, exist_ok=True)
        deadline = time.time() + LOCK_WAIT_S
        while True:
            try:
                fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, f"{os.getpid()} {time.time():.0f}\n".encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    age = time.time() - os.path.getmtime(LOCK)
                except OSError:
                    continue
                if age > LOCK_STALE_S:
                    print(f"  removing stale lock ({age / 60:.0f} min old)")
                    try:
                        os.remove(LOCK)
                    except OSError:
                        pass
                    continue
                if time.time() > deadline:
                    raise SystemExit(f"another rezip_downloads.py holds {LOCK} "
                                     f"({age:.0f} s old); giving up after {LOCK_WAIT_S} s")
                time.sleep(0.5)

    def __exit__(self, *exc):
        try:
            os.remove(LOCK)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="compare a fresh build against the shipped archives "
                         "without writing them")
    args = ap.parse_args()

    ok = True
    with Lock():
        for target in TARGETS:
            folder, zip_path = target[0], target[1]
            extras = target[2] if len(target) > 2 else None
            src = os.path.join(HERE, folder)
            if args.verify:
                ok = verify(src, zip_path, extras) and ok
            else:
                names = rezip(src, zip_path, extras)
                print(f"  wrote {os.path.relpath(zip_path, HERE)}  "
                      f"({len(names)} entries)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
