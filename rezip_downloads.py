"""
Rebuild heat-code.zip, storage-code.zip and bookshelf-code.zip from the
tracked heat/, storage/ and bookshelf/ folders.

figstyle.py and both projects' model.py used to exist only inside
site/downloads/heat-code.zip and storage-code.zip - the sibling source
folders sync_assets.py expected were never created, so a change to either
generator meant editing inside a zip. heat/ and storage/ (unpacked from those
same zips, see SITE_REVAMP_2026-08-30.md) are the source of truth now; the
zips are a build artifact of them, not the other way around. This is what
keeps the two in sync: run it after editing anything under heat/ or
storage/, before publishing, so the file someone downloads from the site
matches the code that actually produced its figures.

Entry order is preserved from whatever the zip already contains - appending
new files at the end, dropping ones that no longer exist in the source
folder - specifically so that re-running this against an unmodified source
folder reproduces the original zip's namelist() exactly. That is also the
verification this script runs on itself: see verify().

Run:
    python3 rezip_downloads.py            # rebuild both zips
    python3 rezip_downloads.py --verify   # rebuild and diff namelist() against
                                           # a backup of what was there before
"""

import argparse
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS = os.path.join(HERE, "site", "downloads")

TARGETS = [
    ("heat", os.path.join(DOWNLOADS, "heat-code.zip")),
    ("storage", os.path.join(DOWNLOADS, "storage-code.zip")),
    # bookshelf/ holds the README and the wallpaper setter; the application
    # itself is the shipped file, pulled in by name so the download can never
    # drift from what the site runs (2026-09-04: it had, by one line).
    ("bookshelf", os.path.join(DOWNLOADS, "bookshelf-code.zip"),
     {"bookshelf-app.html": os.path.join(HERE, "site", "bookshelf-app.html")}),
]


def _all_paths(src_dir):
    """Every path under src_dir, files and directories, as archive-style
    forward-slash relative names - directories carrying the trailing slash
    a zip uses to mark a directory entry."""
    dirs, files = [], []
    for root, ds, fs in os.walk(src_dir):
        ds.sort()
        rel_root = os.path.relpath(root, src_dir)
        if rel_root != ".":
            dirs.append(rel_root.replace(os.sep, "/") + "/")
        for f in sorted(fs):
            rel = os.path.join(rel_root, f) if rel_root != "." else f
            files.append(rel.replace(os.sep, "/"))
    return dirs, files


def rezip(src_dir, zip_path, extras=None):
    """Rebuild zip_path from src_dir. If zip_path already exists, its current
    entry order is kept for every name still present in src_dir - anything
    new in src_dir is appended (directories first, then files, each sorted),
    and anything the zip had that no longer exists in src_dir is dropped with
    a warning, since silently losing a file out of a shipped download is
    exactly the kind of drift this script exists to prevent.

    extras maps an archive name to a path outside src_dir - for a download
    whose main file is the shipped file itself.
    """
    extras = extras or {}
    dirs, files = _all_paths(src_dir)
    all_names = set(dirs) | set(files) | set(extras)

    order = []
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path) as old:
            for name in old.namelist():
                if name in all_names:
                    order.append(name)
                else:
                    print(f"  ! dropping {name!r} from {os.path.basename(zip_path)} "
                          f"- no longer in {os.path.basename(src_dir)}/")
    seen = set(order)
    new_entries = sorted(n for n in all_names if n not in seen)
    order += new_entries

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in order:
            if name.endswith("/"):
                zi = zipfile.ZipInfo(name)
                z.writestr(zi, "")
            else:
                z.write(extras.get(name, os.path.join(src_dir, name)), name)
    return order


def verify(src_dir, zip_path, extras=None):
    """Copy the current zip aside, rebuild it, and confirm the rebuilt
    namelist() matches the original's exactly - the round-trip check this
    module exists to make possible."""
    if not os.path.exists(zip_path):
        print(f"  no existing {zip_path} to verify against")
        return True
    with tempfile.TemporaryDirectory() as tmp:
        backup = os.path.join(tmp, os.path.basename(zip_path))
        shutil.copy2(zip_path, backup)
        with zipfile.ZipFile(backup) as z:
            before = z.namelist()
        rezip(src_dir, zip_path, extras)
        with zipfile.ZipFile(zip_path) as z:
            after = z.namelist()
        ok = before == after
        status = "identical" if ok else "DIFFERS"
        print(f"  {os.path.basename(zip_path)}: namelist() {status} "
              f"({len(before)} -> {len(after)} entries)")
        if not ok:
            print(f"    before: {before}")
            print(f"    after:  {after}")
        return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="rebuild and confirm namelist() is unchanged, "
                         "rather than just rebuilding")
    args = ap.parse_args()

    ok = True
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
